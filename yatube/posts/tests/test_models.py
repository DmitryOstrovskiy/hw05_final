from django.test import TestCase

from ..models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        def test_models_have_correct_object_names(self):
            group = PostModelTest.group
            expected_object_name = group.title
            self.assertEqual(expected_object_name, str(group))

        def test_models_len_post(self):
            post = PostModelTest.post
            expected_object_name = post.text[:15]
            self.assertEqual(expected_object_name, str(post))