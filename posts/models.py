from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()
 

class Group(models.Model):
    title = models.CharField(
        max_length=200
    )
    slug = models.SlugField(
        unique=True, 
        max_length=50,
    )
    description= models.TextField()
 
    class Meta:
        verbose_name = ('Група')
        verbose_name_plural = ('Группы')

    def __str__(self):
        return self.title
 
 
class Post(models.Model):
    text = models.TextField(verbose_name='Текст')
    pub_date = models.DateTimeField(
        "Дата и время публикации", 
        auto_now_add=True,
    )

    author = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name="posts",
        verbose_name='Автор',
    )

    group = models.ForeignKey(
        Group, 
        on_delete=models.SET_NULL, 
        related_name="posts", 
        verbose_name='Группа',
        blank=True, 
        null=True,
    )
    image = models.ImageField(
        upload_to='posts/', 
        blank=True, 
        null=True
    ) 

    class Meta:
        verbose_name = ('Пост')
        verbose_name_plural = ('Посты')
        ordering = (
            "-pub_date",
        )

    def __str__(self):
       return f"{self.author}, {self.text[:20]}..."


class Comment(models.Model):
    post = models.ForeignKey(
        Post, 
        on_delete=models.CASCADE, 
        related_name='comments',
        verbose_name='Пост'
    )
    author = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='comments',
        verbose_name='Автор',
    )
    text = models.TextField(verbose_name='Текст коментария')
    created = models.DateTimeField(
        'Дата и время публикации', 
        auto_now_add=True, 
        db_index=True
    )

    class Meta:
        verbose_name = ('Коммент')
        verbose_name_plural = ('Комменты')
        ordering = (
            "-created",
        )

    def __str__(self):
        return self.text[:20]


class Follow(models.Model):
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='follower'
        ) 
    author = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='following'
    )

    class Meta:
        verbose_name = ('Подписка')
        verbose_name_plural = ('Подписки')
