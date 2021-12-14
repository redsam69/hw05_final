import tempfile
import shutil

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

from ..models import Group, Post, Comment, Follow
from ..forms import PostForm

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user_2 = User.objects.create_user(username='auth1')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
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
        cls.post = Post.objects.create(
            author=cls.user,
            text='Текст проверки',
            group=cls.group,
            image=uploaded
        )

    def setUp(self):
        self.authorized_client = self.client
        self.authorized_client.force_login(self.user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_pages_uses_correct_template(self):
        """Проверка шаблонов"""
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            (reverse('posts:posts_group', kwargs={'slug':
                     self.group.slug})
             ): 'posts/group_list.html',
            (reverse('posts:profile', kwargs={'username': self.user})
             ): 'posts/profile.html',
            (reverse('posts:post_detail',
             kwargs={'post_id': self.post.id})
             ): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            (reverse('posts:post_edit', kwargs={'post_id': self.post.id})
             ): 'posts/create_post.html',
            reverse('posts:follow_index'): 'posts/follow.html',
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_show_correct_context_form(self):
        """Проверка сontext форм"""
        page_names = (
            reverse('posts:post_create'),
            reverse('posts:post_edit',
                    kwargs={'post_id': self.post.id})
        )
        for value in page_names:
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                context = response.context
                self.assertIn('form', context)
                self.assertIsInstance(context['form'], PostForm)

    def test_post_edit_context(self):
        """Проверка context post edit"""
        response = self.authorized_client.get(
            reverse('posts:post_edit',
                    kwargs={'post_id': self.post.id})
        )
        context = response.context
        self.assertIn('post', context)
        self.assertEqual(context['is_edit'], True)
        self.assertIsInstance(context['post'], Post)

    def test_task_detail_pages_show_correct_context(self):
        """Один пост"""
        response = self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}))
        self.assertEqual(response.context['post'].text,
                         self.post.text)

    def test_pages_uses_correct_pages(self):
        """Отображение на страницах"""
        url_page_names = (
            reverse('posts:index'),
            reverse('posts:posts_group',
                    kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user})
        )
        for value in url_page_names:
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                first_object = response.context['page_obj'][0]
                post_text_0 = first_object.text
                post_author_0 = first_object.author.username
                post_image_0 = first_object.image
                self.assertEqual(post_text_0, self.post.text)
                self.assertEqual(post_author_0, self.user.username)
                self.assertEqual(post_image_0, self.post.image)

    def test_pages_uses_correct_group(self):
        """Отображение на страниц с переданной группой"""
        url_page_names = (
            reverse('posts:index'),
            reverse('posts:posts_group',
                    kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user})
        )
        for value in url_page_names:
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                first_object = response.context['page_obj'][0]
                post_group_0 = first_object.group.title
                self.assertEqual(post_group_0, self.group.title)

    def test_task_detail_comment_show_correct_context(self):
        """Вывод комментария"""
        comment = Comment.objects.create(
            post=self.post,
            author=self.user,
            text='Комментарий'
        )
        response = self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}))
        self.assertEqual(response.context['comments'][0].text,
                         comment.text)

    def test_login_user_follow(self):
        """
        Авторизованный пользователь подписывается
        на других пользователей
        """
        count_before = len(Follow.objects.filter(author=self.user_2))
        self.authorized_client.get(reverse(
            'posts:profile_follow', kwargs={'username': self.user_2}))
        count_after = len(Follow.objects.filter(author=self.user_2))
        self.assertEqual(count_after, count_before + 1)

    def test_login_user_unfollow(self):
        """
        Авторизованный пользователь отписывается от других
        пользователей
        """
        count_before = len(Follow.objects.filter(author=self.user_2))
        self.authorized_client.get(reverse(
            'posts:profile_follow', kwargs={'username': self.user_2}))
        self.authorized_client.get(reverse(
            'posts:profile_unfollow', kwargs={'username': self.user_2}))
        count_after = len(Follow.objects.filter(author=self.user_2))
        self.assertEqual(count_after, count_before)

    def test_follow_index(self):
        """
        Новая запись пользователя появляется в ленте тех,
        кто на него подписан
        """
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.authorized_client.get(
            reverse('posts:profile_follow', kwargs={'username': self.user_2}))
        response_after_follow = self.authorized_client.get(
            reverse('posts:follow_index'))
        self.assertEqual(response.content, response_after_follow.content)

    def test_cach_in_index_page(self):
        """Проверка работы cach"""
        response = self.authorized_client.get(reverse('posts:index'))
        before_clearing_the_cache = response.content
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        after_clearing_the_cache = response.content
        self.assertNotEqual(before_clearing_the_cache,
                            after_clearing_the_cache)


class PostPaginatorTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        post_ = (Post(text=f'Текст проверки {i}',
                 group=cls.group,
                 author=cls.user) for i in range(1, 14))
        Post.objects.bulk_create(post_)

    def setUp(self):
        self.authorized_client = self.client
        self.authorized_client.force_login(self.user)

    def test_first_page_contains_ten_records(self):
        """Проверка пагинатора на 1-й странице"""
        url_page_names = (
            reverse('posts:index'),
            reverse('posts:posts_group',
                    kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user})
        )
        for value in url_page_names:
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                self.assertEqual(len(response.context['page_obj']),
                                 settings.PAGE_COUNT)

    def test_second_page_contains_three_records(self):
        """Проверка пагинатора на 2-й странице"""
        url_page_names = (
            reverse('posts:index'),
            reverse('posts:posts_group',
                    kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user})
        )
        for value in url_page_names:
            with self.subTest(value=value):
                response = self.authorized_client.get(value + '?page=2')
                page_count_this = Post.objects.count() - settings.PAGE_COUNT
                self.assertEqual(len(response.context['page_obj']),
                                 page_count_this)
