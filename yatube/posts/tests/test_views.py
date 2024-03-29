import shutil
import tempfile

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

from posts.models import Post, Group, User, Comment, Follow


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='StasBasov')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая пост',
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostPagesTests.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': self.group.slug}):
            'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': self.post.author}):
            'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}):
            'posts/post_detail.html',
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}):
            'posts/create_post.html',
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}):
            'posts/create_post.html',
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(template)
                self.assertTemplateUsed(response, reverse_name)

    def test_index_show_correct_context(self):
        """Список постов в шаблоне index равен ожидаемому контексту."""
        response = self.guest_client.get(reverse('posts:index'))
        expected = list(Post.objects.all()[:10])
        self.assertEqual(list(response.context['page_obj']), expected)

    def test_group_list_show_correct_context(self):
        """Список постов в шаблоне group_list равен ожидаемому контексту."""
        response = self.guest_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        expected = list(Post.objects.filter(group_id=self.group.id)[:10])
        self.assertEqual(list(response.context['page_obj']), expected)

    def test_profile_show_correct_context(self):
        """Список постов в шаблоне profile равен ожидаемому контексту."""
        response = self.guest_client.get(
            reverse('posts:profile', args=(self.post.author,))
        )
        expected = list(Post.objects.filter(author_id=self.user.id)[:10])
        self.assertEqual(list(response.context['page_obj']), expected)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.assertEqual(response.context.get('post').text, self.post.text)
        self.assertEqual(response.context.get('post').author, self.post.author)
        self.assertEqual(response.context.get('post').group, self.post.group)

    def test_create_edit_show_correct_context(self):
        """Шаблон create_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_create_show_correct_context(self):
        """Шаблон create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse("posts:post_create"))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_check_group_in_pages(self):
        """Проверяем создание поста на страницах с выбранной группой"""
        form_fields = {
            reverse('posts:index'): Post.objects.get(group=self.post.group),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}):
            Post.objects.get(group=self.post.group),
            reverse('posts:profile', kwargs={'username': self.post.author}):
            Post.objects.get(group=self.post.group),
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                form_field = response.context['page_obj']
                self.assertIn(expected, form_field)

    def test_check_group_not_in_mistake_group_list_page(self):
        """Проверяем чтобы созданный Пост с группой не попап в чужую группу."""
        form_fields = {
            reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}
            ): Post.objects.exclude(group=self.post.group),
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                form_field = response.context['page_obj']
                self.assertNotIn(expected, form_field)

    def test_comment_correct_context(self):
        """Валидная форма Комментария создает запись в Post."""
        comments_count = Comment.objects.count()
        form_data = {'text': 'Тестовый коммент'}
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response, reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id})
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertTrue(
            Comment.objects.filter(text='Тестовый коммент').exists()
        )

    def test_check_cache(self):
        """Проверка кеша."""
        response = self.guest_client.get(reverse('posts:index'))
        r_1 = response.content
        Post.objects.get(id=1).delete()
        response2 = self.guest_client.get(reverse('posts:index'))
        r_2 = response2.content
        self.assertEqual(r_1, r_2)


class FollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post_autor = User.objects.create(username='autor')
        cls.post_follower = User.objects.create(username='follower')
        cls.post_not_follower = User.objects.create(username='not_follower')
        cls.post = Post.objects.create(text='Тестовый текст',
                                       author=cls.post_autor,)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.post_follower)
        self.follower_client = Client()
        self.follower_client.force_login(self.post_autor)
        self.not_follower_client = Client()
        self.not_follower_client.force_login(self.post_not_follower)
        cache.clear()

    def test_follow_on_user(self):
        """Проверка подписки на пользователя."""
        count_follow = Follow.objects.count()
        self.follower_client.post(
            reverse('posts:profile_follow',
                    kwargs={'username': self.post_follower}))
        # follow = Follow.objects.all().latest('id')
        self.assertEqual(Follow.objects.count(), count_follow + 1)
        # self.assertEqual(follow.author_id, self.post_follower.id)
        # self.assertEqual(follow.user_id, self.post_autor.id)
        self.assertTrue(Follow.objects.filter(
            user=self.post_autor,
            author=self.post_follower).exists()
        )

    def test_unfollow_on_user(self):
        """Проверка отписки от пользователя."""
        Follow.objects.create(user=self.post_autor,
                              author=self.post_follower)
        count_follow = Follow.objects.count()
        self.follower_client.post(
            reverse('posts:profile_unfollow',
                    kwargs={'username': self.post_follower}))
        self.assertEqual(Follow.objects.count(), count_follow - 1)
        self.assertFalse(Follow.objects.filter(
            user=self.post_autor,
            author=self.post_follower).exists()
        )

    def test_posts_on_followers(self):
        """Проверка записей у тех кто подписан на авторов."""
        Follow.objects.create(user=self.post_follower,
                              author=self.post_autor)
        response = self.authorized_client.get(reverse('posts:follow_index'))
        follow = response.context['page_obj']
        self.assertIn(self.post, follow)

    def test_posts_on_unfollowers(self):
        """Проверка записей у тех кто не подписан на авторов."""
        Follow.objects.create(user=self.post_follower,
                              author=self.post_autor)
        response = self.not_follower_client.get(reverse('posts:follow_index'))
        not_follow = response.context['page_obj']
        self.assertNotIn(self.post, not_follow)

    def test_not_follower_to_yourself(self):
        """Проверяем, что нельзя подписаться на себя."""
        response = self.follower_client.get(reverse('posts:follow_index'))
        self.assertEqual(len(response.context['page_obj']), 0)
        self.assertFalse(Follow.objects.filter(
            user=self.post_autor,
            author=self.post_autor).exists()
        )


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            description='Группа для тестов',
            slug='grouptest',
        )
        cls.user = User.objects.create_user(username='TestUser')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.group = Group.objects.create(
            title='Тестовая группа',
            slug='testgroup'
        )
        post_list = []
        for i in range(12):
            post_list.append(Post(
                text=f'Тестовый текст {i}',
                group=self.group,
                author=self.user)
            )
        Post.objects.bulk_create(post_list)

    def test_first_page_index_contains_ten_records(self):
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_index_contains_three_records(self):
        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_first_page_profile_contains_three_records(self):
        response = self.client.get(reverse(
            'posts:profile', kwargs={'username': 'TestUser'}))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_profile_contains_three_records(self):
        response = self.client.get(reverse(
            'posts:profile', kwargs={'username': 'TestUser'}) + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_first_page_groups_contains_ten_records(self):
        response = self.client.get(reverse(
            'posts:group_list', kwargs={'slug': 'testgroup'}))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_groups_contains_three_records(self):
        response = self.client.get(reverse(
            'posts:group_list', kwargs={'slug': 'testgroup'}) + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 2)


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostMediaTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="HasNoName")
        cls.group = Group.objects.create(
            title="Test group",
            slug="test_group_slug",
            description="Test group description",
        )
        cls.small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )
        cls.uploaded = SimpleUploadedFile(
            name="small.gif", content=cls.small_gif, content_type="image/gif"
        )
        cls.post = Post.objects.create(
            author=cls.user, text="Тестовый текст", group=cls.group,
            image=cls.uploaded
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()

    def test_image_in_group_list_page(self):
        """Картинка передается на страницу group_list."""
        response = self.guest_client.get(
            reverse("posts:group_list", kwargs={"slug": self.group.slug}),
        )
        obj = response.context["page_obj"][0]
        self.assertEqual(obj.image, self.post.image)

    def test_image_in_index_and_profile_page(self):
        """Картинка передается на страницу index_and_profile."""
        templates = (
            reverse("posts:index"),
            reverse("posts:profile", kwargs={"username": self.post.author}),
        )
        for url in templates:
            with self.subTest(url):
                response = self.guest_client.get(url)
                obj = response.context["page_obj"][0]
                self.assertEqual(obj.image, self.post.image)

    def test_image_in_post_detail_page(self):
        """Картинка передается на страницу post_detail."""
        response = self.guest_client.get(
            reverse("posts:post_detail", kwargs={"post_id": self.post.id})
        )
        obj = response.context["post"]
        self.assertEqual(obj.image, self.post.image)

    def test_image_in_page(self):
        """Проверяем что пост с картинкой создается в БД"""
        self.assertTrue(
            Post.objects.filter(
                text="Тестовый текст",
                image="posts/small.gif").exists()
        )
