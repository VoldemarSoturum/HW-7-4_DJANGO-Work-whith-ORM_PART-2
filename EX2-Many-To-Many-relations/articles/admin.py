from django.contrib import admin
from django.core.exceptions import ValidationError
from django.forms import BaseInlineFormSet

from .models import Article, Tag, Scope


class ScopeInlineFormSet(BaseInlineFormSet):
    """
    Проверяем, что у статьи выбран ровно один основной раздел (is_main=True).
    """
    def clean(self):
        super().clean()
        mains = 0
        for form in self.forms:
            # форма может быть пустой/удалённой – пропускаем
            if not getattr(form, "cleaned_data", None):
                continue
            if form.cleaned_data.get("DELETE"):
                continue
            if form.cleaned_data.get("is_main"):
                mains += 1
        if mains != 1:
            raise ValidationError("Должен быть выбран ровно один основной раздел.")
        return self.cleaned_data


class ScopeInline(admin.TabularInline):
    model = Scope
    formset = ScopeInlineFormSet
    extra = 1
    autocomplete_fields = ["tag"]  # удобно, если тегов много
    fields = ("tag", "is_main")


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ("title", "published_at")
    search_fields = ("title", "text")
    date_hierarchy = "published_at"
    inlines = [ScopeInline]


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)