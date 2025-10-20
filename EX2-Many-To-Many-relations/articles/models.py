from django.db import models

# =================================================Для тегов и тем
from django.db.models import Q
class Tag(models.Model):
    name = models.CharField(max_length=64, unique=True, verbose_name='Тема')
    class Meta:
        ordering = ['name']
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
    def __str__(self): return self.name
# =================================================

class Article(models.Model):

    title = models.CharField(max_length=256, verbose_name='Название')
    text = models.TextField(verbose_name='Текст')
    published_at = models.DateTimeField(verbose_name='Дата публикации')
    image = models.ImageField(null=True, blank=True, verbose_name='Изображение',)
# ==================================================================================
    # Связь многие-ко-многим к Tag через промежуточную модель Scope
    tags = models.ManyToManyField(
        Tag,
        through='Scope',
        related_name='articles',
        verbose_name='Тематики',
        blank=True,
    )
# ====================================================================================
    class Meta:
        ordering = ['-published_at']
        verbose_name = 'Статья'
        verbose_name_plural = 'Статьи'

    def __str__(self): return self.title

# ================================================= Для основания статьи

class Scope(models.Model):
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        related_name='scopes',
        verbose_name='Тег')
    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name='scopes',
        verbose_name='Статья')
    is_main = models.BooleanField(default=False, verbose_name='Основной')

    class Meta:
        verbose_name = 'Тематика статьи'
        verbose_name_plural = 'Тематики статьи'
        # запрет дублирования одного тега у одной статьи
        constraints = [
            models.UniqueConstraint(
                fields=['tag', 'article'],
                name='unique_tag_per_article',
            ),
            # у статьи может быть не более одного основного тега
            models.UniqueConstraint(
                fields=['article'],
                condition=Q(is_main=True),
                name='unique_main_scope_per_article',
            ),
        ]
        indexes = [
            models.Index(fields=['article', 'is_main']),
        ]

    def __str__(self) -> str:
        label = ' (основной)' if self.is_main else ''
        return f'{self.article} — {self.tag}{label}'
# ========================================================