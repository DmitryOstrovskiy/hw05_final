from http import HTTPStatus
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Post, Group, User


class PostFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="NoName")
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.post = Post.objects.create(
            author=self.user,
            text="Тестовый текст",
        )
        self.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-slug",
            description="Тестовое описание",
        )

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        form_data = {"text": "Изменяем текст", "group": self.group.id}
        response = self.authorized_client.post(
            reverse("posts:post_create"), data=form_data, follow=True)
        self.assertRedirects(response, reverse("posts:profile",
                             kwargs={"username": self.user.username}))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        text = Post.objects.first().text
        group = Post.objects.first().group.id
        self.assertEqual(text, form_data['text'])
        self.assertEqual(group, form_data['group'])
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit(self):
        """Валидная форма изменяет запись в Post."""
        posts_count = Post.objects.count()
        form_data = {"text": "Изменяем текст", "group": self.group.id}
        response = self.authorized_client.post(
            reverse("posts:post_edit", args=({self.post.id})),
            data=form_data,
            follow=True,)
        self.assertRedirects(response, reverse("posts:post_detail",
                             kwargs={"post_id": self.post.id}))
        self.assertEqual(Post.objects.count(), posts_count)
        post = Post.objects.get(id=self.post.id)
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group.id, form_data['group'])
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_not_create_guest_client(self):
        """Валидная форма не изменит запись в Post если неавторизован."""
        posts_count = Post.objects.count()
        form_data = {"text": "Изменяем текст", "group": self.group.id}
        response = self.guest_client.post(
            reverse("posts:post_edit", args=({self.post.id})),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response,
                             f"/auth/login/?next=/posts/{self.post.id}/edit/")
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertFalse(Post.objects.filter(text="Изменяем текст").exists())
        self.assertEqual(response.status_code, HTTPStatus.OK)
