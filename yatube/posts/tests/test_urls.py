from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from http import HTTPStatus

from ..models import Post, Group

User = get_user_model()


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(slug='group_slug')
        cls.user = User.objects.create(username='USERNAME')
        cls.author = User.objects.create_user(
            username='author_of_Posts')
        cls.post = Post.objects.create(
            author=User.objects.get(username='author_of_Posts'),
            text='Текст',
            group=cls.group,
        )

    def setUp(self) -> None:
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_not_author = Client(self.author)

    def test_not_authorized_pages(self):
        """Главная, группы, профиль, пост доступны ВСЕМ"""
        pages_url = {
            '/': HTTPStatus.OK,
            f'/group/{self.group.slug}/': HTTPStatus.OK,
            f'/profile/{self.user}/': HTTPStatus.OK,
            f'/posts/{self.post.id}/': HTTPStatus.OK,
        }

        for address, http_status in pages_url.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, http_status)

    def test_create_page_for_authorized(self):
        """Создание поста доступно авторизаванному"""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edit_page_for_author(self):
        """Редактирование поста доступно автору"""
        response = self.authorized_client_not_author.\
            get(f'/posts/{self.post.id}/edit/')
        self.assertNotEqual(response.status_code, HTTPStatus.OK)

    def test_404_response(self):
        """Запрос к несуществующей странице вернёт ошибку 404"""
        nonexistent = {
            '/nonexistent_page/': HTTPStatus.NOT_FOUND
        }

        for address, http_status in nonexistent.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, http_status)
