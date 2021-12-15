from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from ..models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):

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
            text='Текст проверки'
        )
        cls.id = cls.post.id

    def setUp(self):
        self.guest_client = self.client
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_urls_exists(self):
        '''Общедоступные страницы.'''
        code_url = {
            '/': HTTPStatus.OK,
            '/group/test-slug/': HTTPStatus.OK,
            '/profile/auth/': HTTPStatus.OK,
            f'/posts/{self.id}/': HTTPStatus.OK,
            '/unexiscting_page/': HTTPStatus.NOT_FOUND,
        }
        for url, code in code_url.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, code)

    def test_urls_exists_at_author(self):
        '''Доступность постов для авториз. польз.'''
        code_url = {
            '/create/': HTTPStatus.OK,
            f'/posts/{self.id}/edit/': HTTPStatus.OK,
        }
        for url, code in code_url.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, code)

    def test_redirect_anonymous_on_admin_login(self):
        '''Редирект неавторизованного пользователя.'''
        url_redirect = {
            '/create/': '/auth/login/?next=/create/',
            f'/posts/{self.id}/edit/':
                f'/auth/login/?next=/posts/{self.id}/edit/',
        }
        for url, redirect in url_redirect.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url, follow=True)
                self.assertRedirects(
                    response, redirect)

    def test_urls_uses_correct_template(self):
        '''Шаблоны для всех сраниц.'''
        templates_url_names = {
            '/': 'posts/index.html',
            '/group/test-slug/': 'posts/group_list.html',
            '/profile/auth/': 'posts/profile.html',
            f'/posts/{self.id}/': 'posts/post_detail.html',
            f'/posts/{self.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
            '/follow/': 'posts/follow.html',
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)
