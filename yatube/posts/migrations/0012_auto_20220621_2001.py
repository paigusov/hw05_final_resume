# Generated by Django 2.2.16 on 2022-06-21 17:01

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0011_auto_20220621_1407'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='follow',
            name='Пара уникальных значений',
        ),
        migrations.AlterField(
            model_name='follow',
            name='author',
            field=models.ForeignKey(help_text='На Вас подписаны', on_delete=django.db.models.deletion.CASCADE, related_name='following', to=settings.AUTH_USER_MODEL, verbose_name='Блогер'),
        ),
        migrations.AlterField(
            model_name='follow',
            name='user',
            field=models.ForeignKey(help_text='Подписчик', on_delete=django.db.models.deletion.CASCADE, related_name='follower', to=settings.AUTH_USER_MODEL, verbose_name='Подписчик'),
        ),
        migrations.AddConstraint(
            model_name='follow',
            constraint=models.UniqueConstraint(fields=('user', 'author'), name='unique_pair'),
        ),
    ]
