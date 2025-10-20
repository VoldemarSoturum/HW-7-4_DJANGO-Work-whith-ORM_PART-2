# Инструкция по запуску и тестам

## Требования
- Python 3.11+
- PostgreSQL (локально)
- pip (рекомендуется `venv`)
- Зависимости из `requirements.txt` (включая Pillow)

## Установка зависимостей
```bash
pip install -r requirements.txt
```

## Настройка базы данных (PostgreSQL)
Открой `website/settings.py` и проверь блок:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'netology_m2m_relations',
        'USER': 'netology',
        'PASSWORD': 'netology13',
        'HOST': '127.0.0.1',
        'PORT': '5432',
        # опционально для тестов (см. ниже):
        # 'TEST': {'NAME': 'test_netology_m2m_relations'},
    }
}
```

### Полезные настройки для dev
```python
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```
И внизу `website/urls.py` (при `DEBUG=True`):
```python
from django.conf import settings
from django.conf.urls.static import static

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

## Применение миграций
```bash
python manage.py migrate
```

## (Необязательно) Загрузка тестовых данных
Если есть фикстура `articles.json`:
```bash
# если лежит в корне проекта
python manage.py loaddata articles.json

# если лежит в articles/fixtures/articles.json
python manage.py loaddata articles
```

## Создание суперпользователя
```bash
python manage.py createsuperuser
```

## Запуск сервера
```bash
python manage.py runserver
```
- Главная: http://127.0.0.1:8000/
- Админка: http://127.0.0.1:8000/admin/

### Работа в админке
1) Создайте теги (раздел **Tags**).  
2) Откройте статью (раздел **Articles**) → внизу инлайн-таблица **Scope**.  
3) Добавьте строки (выберите теги). **Ровно одна** строка должна иметь `is_main=True`.  
4) Сохраните.

## Прогон тестов

### Вариант 1 — стандартный раннер Django
```bash
python manage.py test articles -v 2
```

#### Возможная ошибка: «нет прав для создания базы данных»
Если при тестах видите ошибку прав, сделайте ОДНО из:
- Выдать пользователю право создавать БД:
  ```sql
  -- войдите как суперпользователь postgres
  ALTER ROLE netology CREATEDB;
  ```
- Либо создать тестовую БД вручную и выдать права:
  ```sql
  CREATE DATABASE test_netology_m2m_relations ENCODING 'UTF8';
  GRANT ALL PRIVILEGES ON DATABASE test_netology_m2m_relations TO netology;

  \c test_netology_m2m_relations
  ALTER SCHEMA public OWNER TO netology;
  GRANT USAGE, CREATE ON SCHEMA public TO netology;
  ```
  И добавить в `settings.py`:
  ```python
  DATABASES['default']['TEST'] = {'NAME': 'test_netology_m2m_relations'}
  ```
  Теперь можно запускать, не пересоздавая БД:
  ```bash
  python manage.py test articles -v 2 --keepdb
  ```

### Вариант 2 — с прогресс-баром (кастомный тест-раннер)
При наличии `articles/tests_runner.py`:
- Постоянно (через настройки):
  ```python
  # website/settings.py
  TEST_RUNNER = 'articles.tests_runner.ProgressTestRunner'
  ```
  Запуск:
  ```bash
  python manage.py test articles -v 2
  ```

- Разово (без изменения настроек):
  ```bash
  python manage.py test articles -v 2 --testrunner=articles.tests_runner.ProgressTestRunner
  ```

## Что проверяют тесты
- **Порядок тегов** в списке статей: сначала основной (`is_main=True`), затем остальные по алфавиту.  
- **Ограничения БД**: нельзя прикрепить к статье один и тот же тег дважды; не более одного «основного» тега.  
- **Валидация админки**: инлайн-формсет не даёт сохранить без **ровно одного** основного тега.

## Частые проблемы
- **Пустая главная**: нет данных — загрузите фикстуру или создайте статьи/теги через админку.  
- **Теги не отображаются**: проверьте, что в моделях у `Scope.article` стоит `related_name='scopes'`, а в шаблоне используется `article.scopes.all`.  
- **Картинки не видны**: проверьте `MEDIA_URL`, `MEDIA_ROOT` и выдачу медиа в `urls.py`.  
- **Импорт тест-раннера**: убедитесь, что путь указан верно, файл лежит в `articles/tests_runner.py`, а в `articles/` есть `__init__.py`.

## Итоговый вид

- **Контент**
![КОНТЕН](https://github.com/VoldemarSoturum/HW-7-4_DJANGO-Work-whith-ORM_PART-2/blob/main/EX2-Many-To-Many-relations/For_Readme/ScreenShot.png)
- **Админка**
![АДМИНКА](https://github.com/VoldemarSoturum/HW-7-4_DJANGO-Work-whith-ORM_PART-2/blob/main/EX2-Many-To-Many-relations/For_Readme/ADMINKA_ORM-2.gif)
- **Диаграмма БД (DBeaver)**
![ДИАГРАММА_БД](https://github.com/VoldemarSoturum/HW-7-4_DJANGO-Work-whith-ORM_PART-2/blob/main/EX2-Many-To-Many-relations/For_Readme/netology_m2m_relations%20-%20public.png)
