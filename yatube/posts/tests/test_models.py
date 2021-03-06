from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post, Comment

User = get_user_model()


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
            text='Тестовый текст',
        )

    def test_models_have_correct_object_names_post(self):
        """Корректность post __str__."""
        post = self.post
        expected_object_name = post.text[:15]
        self.assertEqual(expected_object_name, str(post))

    def test_models_have_correct_object_names_group(self):
        """Корректность group __str__."""
        group = self.group
        expected_object_name = group.title
        self.assertEqual(expected_object_name, str(group))


class CommentModelTest(TestCase):

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
            text='Тестовый текст',
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Тестовый текст',
        )

    def test_models_have_correct_object_names_post(self):
        """Корректность comment __str__."""
        comment = self.comment
        expected_object_name = comment.text[:15]
        self.assertEqual(expected_object_name, str(comment))
