from django.contrib.auth import get_user_model
from django import forms
from django.test import Client, TestCase
from django.urls import reverse
from django.conf import settings
import tempfile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
import shutil
import tempfile

from ..models import Group, Post, Comment, Follow


User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

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


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='testuser')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_group',
            description='Тестовое описание',
        )
        cls.group2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test_group2',
            description='Тестовое описание 2',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Текст',
            group=cls.group,
        )
        cls.group_post = Post.objects.create(
            author=cls.user,
            text='Текст',
            group=cls.group,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self) -> None:
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostPagesTests.user)

    def test_paginator(self):
        """Тест паджинатора"""
        cache.clear()
        post_list = []
        for i in range(1, 12):
            post_list.append(Post(
                text='text' + str(i),
                author=self.user,
                group=self.group,
            ))
        Post.objects.bulk_create(post_list)

        templates_pages_names = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', args={self.user}),
        ]
        for reverse_name in templates_pages_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(len(response.context['page_obj']), 10)
                response = self.authorized_client.get(reverse_name + '?page=2')
                self.assertEqual(len(response.context['page_obj']), 3)

    def test_post_detail_page_show_correct_context(self):
        """post_detail имеет правильный context."""
        postdetail = reverse('posts:post_detail',
                             kwargs={'post_id': self.post.id})
        response = self.authorized_client.get(postdetail)
        test_post = response.context['post']
        self.check_post_detail(test_post)

    def check_post_detail(self, post):
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.author.username, self.user.username)
        self.assertEqual(post.group, self.post.group)
        self.assertEqual(post.image, self.post.image)

    def test_post_create_page_show_correct_context(self):
        """post_create имеет правильный context."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        is_edit = True
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        self.assertNotEqual(response.context["is_edit"], is_edit)

    def test_main_pages_show_correct_context(self):
        """Контекст index / group_list / profile"""
        cache.clear()
        context = {reverse('posts:index'): self.post,
                   reverse('posts:group_list',
                           kwargs={'slug': self.group.slug,
                                   }): self.post,
                   reverse('posts:profile',
                           kwargs={'username': self.user.username,
                                   }): self.post,
                   }
        for reverse_page, object in context.items():
            with self.subTest(reverse_page=reverse_page):
                response = self.guest_client.get(reverse_page)
                self.check_post_detail(
                    response.context['page_obj'][0])

    def test_post_edit_page_show_correct_context(self):
        """post_edit имеет правильный context."""
        post = PostPagesTests.post
        url = reverse('posts:post_edit', kwargs={'post_id': f'{post.id}'})
        response = self.authorized_client.get(url)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        is_edit = True
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        self.assertEqual(response.context["is_edit"], is_edit)

    def test_post_showing_on_page(self):
        """
        Попадает ли пост на Главную страницу, в страницу Групп,
        в страницу Профиля
        """
        cache.clear()
        group_post_pages = {
            reverse('posts:index') + '?page=2': 2,
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}) + '?page=2': 2,
            reverse('posts:profile',
                    kwargs={'username': self.user.username}) + '?page=2': 2,
        }
        for value, expected in group_post_pages.items():
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                self.assertEqual(len(response.context["page_obj"]), expected)

    def test_add_comment(self):
        """Проверка добавления комментария"""
        comment1 = Comment.objects.create(
            text='тест',
            author=self.user,
            post=self.post
        )
        self.assertEqual(comment1.text, 'тест')
        self.assertEqual(comment1.author, self.user)
        self.assertEqual(comment1.post, self.post)


class FollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(
            username='user',
        )
        cls.other_user = User.objects.create(
            username='other_user'
        )
        cls.group = Group.objects.create(
            title='Тестовое название группы',
            slug='test_slug',
            description='Тестовое описание группы',
        )
        cls.post = Post.objects.create(
            text='тестовый текст',
            author=cls.user,
            group=cls.group,
        )

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.other_user)

    def test_follow_for_auth(self):
        """Проверка profile_follow"""
        follow_count = Follow.objects.count()
        new_follower = Follow.objects.create(
            user=self.other_user,
            author=self.user
        )
        self.authorized_client.post(reverse(
            'posts:profile_follow', kwargs={'username': self.user}))
        self.assertTrue(Follow.objects.filter(
            user=self.other_user, author=self.user).exists()
        )
        self.assertEqual(Follow.objects.count(), follow_count + 1)
        self.assertEqual(new_follower.user, self.other_user)
        self.assertEqual(new_follower.author, self.user)

    def test_unfollow_for_auth(self):
        """Проверка profile_follow"""
        Follow.objects.create(
            user=self.other_user,
            author=self.user
        )
        follow_count = Follow.objects.count()
        self.authorized_client.post(reverse(
            'posts:profile_unfollow', kwargs={'username': self.user}))
        self.assertFalse(Follow.objects.filter(
            user=self.other_user, author=self.user).exists()
        )
        self.assertEqual(Follow.objects.count(), follow_count - 1)

    def test_follow_page_context(self):
        """ Тестируем вывод поста после подписки
        и пустой список после отписки"""
        response = self.authorized_client.get(reverse('posts:follow_index'))
        page_object = response.context.get('page_obj').object_list
        self.assertEqual((len(page_object)), 0)
        new_follower = Follow.objects.create(
            user=self.other_user,
            author=self.user
        )
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertEqual((len(response.context['page_obj'])), 1)
        page_object = response.context.get('page_obj').object_list[0]
        self.assertIn(
            self.post, response.context['page_obj'])
        new_follower.delete()
        response = self.authorized_client.get(reverse('posts:follow_index'))
        page_object = response.context.get('page_obj').object_list
        self.assertEqual((len(page_object)), 0)
