from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from ..forms import PostForm
from http import HTTPStatus

from ..models import Group, Post


User = get_user_model()


class PostFormsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='username')
        cls.group = Group.objects.create(
            title='test group',
            slug='test_group',
            description='description',
        )
        cls.group2 = Group.objects.create(
            title='test group 2',
            slug='test_group2',
            description='description2',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='text',
            group=cls.group
        )
        cls.form = PostForm()

    def setUp(self) -> None:
        self.authorized_client = Client()
        self.authorized_client.force_login(PostFormsTests.user)

    def test_new_data_create_post(self):
        """
        При отправке валидной формы со страницы
        создания поста reverse('posts:post_create')
        создаётся новая запись в базе данных
        """
        posts_count = Post.objects.count()
        form_data = {
            'text': 'text',
            'group': self.group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(
            response, reverse('posts:profile', args={self.user})
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        last_post = Post.objects.latest('pub_date')
        self.assertEqual(last_post.text, form_data['text'])
        self.assertEqual(last_post.group, self.group)

    def test_edit_post(self):
        """
        При отправке валидной формы со страницы редактирования поста
        происходит изменение поста с post_id в базе данных
        """
        posts_count = Post.objects.count()
        groupnew = PostFormsTests.group2.id
        form_data = {
            'text': 'text',
            'group': groupnew,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        post = Post.objects.get(id=self.post.id)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(form_data['text'], post.text)
        self.assertEqual(form_data['group'], post.group.id)
