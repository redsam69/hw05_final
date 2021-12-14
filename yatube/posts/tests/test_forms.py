import tempfile
import shutil

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.models import Group, Post, Comment

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TestCreateForm(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Группа',
            slug='test-slug',
            description='Группа наименование',
        )
        cls.post = Post.objects.create(
            group=cls.group,
            text='Текст поста',
            author=cls.user,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = self.client
        self.authorized_client.force_login(self.user)

    def test_form_create(self):
        """Проверка создания нового поста, авторизированным пользователем"""
        post_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'group': self.group.id,
            'text': 'Отправить текст',
            'image': uploaded,
        }
        response = self.authorized_client.post(reverse('posts:post_create'),
                                               data=form_data, follow=True)
        self.assertRedirects(response, reverse('posts:profile',
                             kwargs={'username': self.user}))
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(Post.objects.filter(
            text=form_data['text'],
            group=form_data['group'],
            image=f"posts/{form_data['image'].name}",
            author=self.user).exists())

    def test_form_update(self):
        """
        Проверка редактирования поста через форму
        """
        form_data = {
            'group': self.group.id,
            'text': 'Обновленный текст',
        }
        self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data, follow=True)
        self.post.refresh_from_db()
        self.assertEqual(self.post.text, form_data['text'])
        self.assertEqual(self.post.group.id, form_data['group'])

    def test_form_add_comment(self):
        """Добавление комментария к посту"""
        form_data = {
            'text': 'Комментарий!',
        }
        self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data, follow=True)
        self.assertTrue(Comment.objects.filter(
            text=form_data['text'], ).exists())
