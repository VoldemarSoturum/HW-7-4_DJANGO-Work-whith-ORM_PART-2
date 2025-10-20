# articles/tests.py
from django.test import TestCase, Client
from django.urls import reverse
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.forms.models import inlineformset_factory

from .models import Article, Tag, Scope


class ArticlesViewOrderingTests(TestCase):
    def setUp(self):
        # Теги так, чтобы алфавитный порядок был: Analytics < Backend < Cloud
        self.tA = Tag.objects.create(name="Analytics")
        self.tB = Tag.objects.create(name="Backend")
        self.tC = Tag.objects.create(name="Cloud")

        self.article = Article.objects.create(
            title="Проверка порядка тегов",
            text="Text",
            published_at=timezone.now(),
        )
        # основной — Backend
        Scope.objects.create(article=self.article, tag=self.tB, is_main=True)
        # остальные: Analytics, Cloud (должны идти по алфавиту)
        Scope.objects.create(article=self.article, tag=self.tA, is_main=False)
        Scope.objects.create(article=self.article, tag=self.tC, is_main=False)

    def test_scopes_order_in_list_view(self):
        """
        На странице списка статей теги идут: основной, затем остальные по алфавиту.
        Проверяем порядок по индексам в HTML.
        """
        client = Client()
        url = reverse("articles")   # <— имя роута из твоего urls.py
        resp = client.get(url)
        self.assertEqual(resp.status_code, 200)

        html = resp.content.decode("utf-8")

        pos_main = html.find("Backend")    # основной
        pos_a = html.find("Analytics")     # далее по алфавиту
        pos_c = html.find("Cloud")

        self.assertNotEqual(pos_main, -1, "Основной тег не найден в HTML")
        self.assertNotEqual(pos_a, -1, "Тег Analytics не найден в HTML")
        self.assertNotEqual(pos_c, -1, "Тег Cloud не найден в HTML")

        self.assertTrue(
            pos_main < pos_a < pos_c,
            f"Ожидался порядок Backend (main) -> Analytics -> Cloud, но индексы: {pos_main}, {pos_a}, {pos_c}"
        )


class ScopeModelConstraintsTests(TestCase):
    def setUp(self):
        self.article = Article.objects.create(
            title="Ограничения Scope",
            text="Text",
            published_at=timezone.now(),
        )
        self.t1 = Tag.objects.create(name="Django")
        self.t2 = Tag.objects.create(name="ORM")

    def test_unique_tag_per_article(self):
        """Нельзя добавить один и тот же тег к одной статье дважды."""
        Scope.objects.create(article=self.article, tag=self.t1, is_main=True)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Scope.objects.create(article=self.article, tag=self.t1, is_main=False)

    def test_at_most_one_main_per_article(self):
        """На уровне БД — не более одного основного тега на статью."""
        Scope.objects.create(article=self.article, tag=self.t1, is_main=True)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Scope.objects.create(article=self.article, tag=self.t2, is_main=True)


class AdminInlineValidationTests(TestCase):
    """
    Проверяем, что админский инлайн-формсет требует РОВНО один is_main=True.
    Используем inlineformset_factory, как делает админка.
    """
    def setUp(self):
        self.article = Article.objects.create(
            title="Admin formset",
            text="Text",
            published_at=timezone.now(),
        )
        self.t1 = Tag.objects.create(name="AI")
        self.t2 = Tag.objects.create(name="ML")

        # Пытаемся взять твой formset из admin.py; если не получится — тест всё равно пройдёт,
        # так как важна логика clean из твоего класса.
        try:
            from .admin import ScopeInlineFormSet
            base_formset = ScopeInlineFormSet
        except Exception:
            from django.forms import BaseInlineFormSet as base_formset  # без спец-валидатора

        # Класс формсета с привязкой к моделям (как делает админка)
        self.FormSetClass = inlineformset_factory(
            parent_model=Article,
            model=Scope,
            formset=base_formset,
            fields=("tag", "is_main"),
            extra=0,
            can_delete=True,
        )

    def _make_formset(self, rows):
        """
        rows — список словарей: {'tag': tag_id, 'is_main': True/False, 'DELETE': False}
        """
        total = len(rows)
        data = {
            "scopes-TOTAL_FORMS": str(total),
            "scopes-INITIAL_FORMS": "0",
            "scopes-MIN_NUM_FORMS": "0",
            "scopes-MAX_NUM_FORMS": "1000",
        }
        for i, row in enumerate(rows):
            data[f"scopes-{i}-id"] = ""
            data[f"scopes-{i}-article"] = str(self.article.pk)
            data[f"scopes-{i}-tag"] = str(row["tag"])
            if row.get("is_main"):
                data[f"scopes-{i}-is_main"] = "on"
            if row.get("DELETE"):
                data[f"scopes-{i}-DELETE"] = "on"

        return self.FormSetClass(data=data, instance=self.article, prefix="scopes")

    def test_admin_formset_requires_exactly_one_main(self):
        # 0 основных — невалидно
        fs = self._make_formset([
            {"tag": self.t1.id, "is_main": False},
            {"tag": self.t2.id, "is_main": False},
        ])
        self.assertFalse(fs.is_valid(), "Ожидалась ошибка валидатора: 0 основных")
        self.assertIn("основн", str(fs.errors).lower() + str(fs.non_form_errors()).lower())

        # 2 основных — невалидно
        fs = self._make_formset([
            {"tag": self.t1.id, "is_main": True},
            {"tag": self.t2.id, "is_main": True},
        ])
        self.assertFalse(fs.is_valid(), "Ожидалась ошибка валидатора: >1 основного")
        self.assertIn("основн", str(fs.errors).lower() + str(fs.non_form_errors()).lower())

        # Ровно 1 основной — валидно
        fs = self._make_formset([
            {"tag": self.t1.id, "is_main": True},
            {"tag": self.t2.id, "is_main": False},
        ])
        self.assertTrue(fs.is_valid(), f"Формсет должен быть валиден, но есть ошибки: {fs.errors} {fs.non_form_errors()}")
