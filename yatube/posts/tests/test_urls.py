from django.test import TestCase, Client
from django.urls import reverse

from posts.models import Post, Group, User
from http import HTTPStatus


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_homepage(self):
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, HTTPStatus.OK)


class PostUrlTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def guest_client_urls(self):
        """Страницы доступны любому пользователю."""
        url_names = (
            '/',
            '/group/test-slug/',
            '/profile/auth/',
            '/posts/1/',
        )

        for address in url_names:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                error_acces = f'address{address}, dont have access'
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK,
                    error_acces
                )

    def test_post_create_url(self):
        """Страница create/ доступна авторизованному пользователю."""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_url(self):
        author = User.objects.create_user(username='test')
        post = Post.objects.create(
            author=author,
            text='abc',
            group=self.group
        )
        self.authorized_client.force_login(author)
        response = self.authorized_client.get(f'/posts/{post.id}/edit/')
        self.assertEquals(response.status_code, HTTPStatus.OK)

    def test_post_edit_url_redirect_anonymous(self):
        """Страница /post_id/edit/ перенаправляет анонимного пользователя."""
        response = self.guest_client.get('/posts/1/edit/', follow=True)
        self.assertRedirects(
            response, ('/auth/login/?next=/posts/1/edit/'))

    def test_post_create_url_redirect_anonymous(self):
        """Страница create/ перенаправляет анонимного пользователя."""
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(
            response, ('/auth/login/?next=/create/'))

    def unexisting_page(self):
        """Несуществующая страница."""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            '/group/test-slug/': 'posts/group_list.html',
            '/profile/auth/': 'posts/profile.html',
            '/posts/1/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            '/posts/1/edit/': 'posts/create_post.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
                error_acces = f'address{address}, dont have access'
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK,
                    error_acces
                )

    def test_urls_return_correct_name(self):
        """URL-адрес возвращвет ожидаемый путь."""
        reverse_url_names = {
            reverse('posts:index'): '/',
            reverse('posts:group_list', kwargs={'slug': self.group.slug}):
            '/group/test-slug/',
            reverse('posts:profile', kwargs={'username': self.post.author}):
            '/profile/auth/',
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}):
            '/posts/1/',
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}):
            '/posts/1/edit/',
            reverse('posts:post_create'): '/create/',
        }
        for name, address in reverse_url_names.items():
            with self.subTest(address=address):
                self.assertEqual(address, name)
