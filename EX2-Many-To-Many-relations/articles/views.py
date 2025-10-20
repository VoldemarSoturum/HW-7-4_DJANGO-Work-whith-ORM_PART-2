from django.shortcuts import render

# ==========================
from django.db.models import Prefetch
from articles.models import Article, Scope

def articles_list(request):
    template = 'articles/news.html'
    # используйте этот параметр для упорядочивания результатов
    # https://docs.djangoproject.com/en/3.1/ref/models/querysets/#django.db.models.query.QuerySet.order_by
    ordering = '-published_at'

    scopes_prefetch = Prefetch(
        'scopes',
        queryset=Scope.objects.select_related('tag').order_by('-is_main', 'tag__name')
    )
    articles = (
        Article.objects
        .order_by(ordering)
        .prefetch_related(scopes_prefetch)
    )

    context = {'object_list': articles}

    return render(request, template, context)
