from django.test import TestCase
from django.contrib.auth import get_user_model

from ..models import Post, Group

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Шерлок',
            slug='sherlock',
            description='Группа фанатов Шерлока',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Пост',
            group=cls.group
        )

    def test_str_method(self):
        """Проверяем, что у моделей корректно работает __str__."""
        group = PostModelTest.group
        post = PostModelTest.post
        self.assertEqual(str(group), group.title)
        self.assertEqual(str(post), post.text[:15])

    def test_verbose_name_post(self):
        """Проверяем наличие verbose_name группы"""
        task = PostModelTest.post
        verbose = task._meta.get_field('group').verbose_name
        self.assertEqual(verbose, 'Группа')

    def test_help_text_group(self):
        """Проверяем наличие help_text при выборе группы"""
        task = PostModelTest.post
        help_texts = task._meta.get_field('group').help_text
        self.assertEqual(help_texts, 'Выберите группу')

    def test_help_text_post(self):
        """Проверяем наличие help_text при вводе текста"""
        task = PostModelTest.post
        help_texts = task._meta.get_field('text').help_text
        self.assertEqual(help_texts, 'Введите текст поста')

    def test_verbose_name_author_post(self):
        """Проверяем наличие verbose_name автора"""
        task = PostModelTest.post
        verbose = task._meta.get_field('author').verbose_name
        self.assertEqual(verbose, 'Автор')
