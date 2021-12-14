from http import HTTPStatus

from django.test import TestCase


class StaticURLTests(TestCase):

    def setUp(self):
        self.guest_client = self.client

    def test_urls_exists(self):
        '''About страницы'''
        code_url = {
            '/about/author/': HTTPStatus.OK,
            '/about/tech/': HTTPStatus.OK,
        }
        for url, code in code_url.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, code)

    def test_urls_uses_correct_template(self):
        '''Шаблоны для about'''
        templates_url_names = {
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html',
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)
