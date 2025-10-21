# Школа — переход с FK на M2M между Student и Teacher

Пошаговый процесс, который мы выполнили: от первоначальной схемы с `ForeignKey` у `Student` к `ManyToManyField`, включая перенос данных, правки шаблона и оптимизацию числа SQL‑запросов.

## Состав проекта (важные файлы)

- `school/models.py` — модели `Teacher` и `Student`.
- `school/views.py` — функция `students_list` с оптимизацией запросов.
- `templates/school/students_list.html` — шаблон с выводом всех учителей ученика.
- `school/migrations/` — миграции, в т.ч. дата‑миграция переноса связей FK → M2M.
- `school.json` — исходные данные (fixtures).

## Требования и запуск окружения

```bash
pip install -r requirements.txt
```

## База: начальные миграции и загрузка данных

> Важно: исходные данные нужно загрузить **до** изменения схемы на M2M (иначе `loaddata` не применится к новой схеме).

```bash
python manage.py makemigrations # создадим первую миграцию
python manage.py migrate        # применяем существующие миграции (например, 0001 и 0002)
python manage.py loaddata school.json # выгружем данные из json
```

---

## Рефакторинг моделей: FK → M2M

Меняем связь у `Student` с одного учителя (`ForeignKey`) на список учителей (`ManyToManyField`).

### Итоговое состояние модели `Student`

```python
# school/models.py
class Student(models.Model):
    name = models.CharField(max_length=30, verbose_name='Имя')
    teachers = models.ManyToManyField('school.Teacher', related_name='students', blank=True)
    group = models.CharField(max_length=10, verbose_name='Класс')
```

---

## Вариант дальнейших действий по **АККУАТНОЙ** миграции (в «3 приёма», некий "пузырьковый" вариант): Add → Copy → Remove

### Шаг 1. Добавляем M2M, FK пока оставляем

Во `Student` временно существуют **оба** поля: старое `teacher` (FK) и новое `teachers` (M2M).

```python
class Student(models.Model):
    name = models.CharField(max_length=30, verbose_name='Имя')
    teacher = models.ForeignKey('school.Teacher', on_delete=models.CASCADE)  # временно оставляем
    teachers = models.ManyToManyField('school.Teacher', related_name='students', blank=True)  # новое поле
    group = models.CharField(max_length=10, verbose_name='Класс')
```

Создаём и применяем миграцию:

```bash
python manage.py makemigrations
python manage.py migrate
```

### Шаг 2. Переносим данные FK → M2M (данные‑миграция)

Создаём пустую миграцию и добавляем перенос:

```bash
python manage.py makemigrations --empty school -n copy_fk_to_m2m
```

В файл "пустой" миграции который был создан добавляем:

```python
from django.db import migrations

def copy_fk_to_m2m(apps, schema_editor):
    Student = apps.get_model('school', 'Student')
    for s in Student.objects.all():
        if getattr(s, 'teacher_id', None):
            s.teachers.add(s.teacher_id)

class Migration(migrations.Migration):
    dependencies = [
        ('school', '0003_student_teachers'),  # подставьте актуальное имя файла предыдущей миграции
    ]
    operations = [
        migrations.RunPython(copy_fk_to_m2m, migrations.RunPython.noop),
    ]
```

Применяем:

```bash
python manage.py migrate
```

### Шаг 3. Удаляем старое поле FK

Убираем поле `teacher` из модели и генерируем миграцию на удаление:

```python
class Student(models.Model):
    name = models.CharField(max_length=30, verbose_name='Имя')
    teachers = models.ManyToManyField('school.Teacher', related_name='students', blank=True)
    group = models.CharField(max_length=10, verbose_name='Класс')
```

```bash
python manage.py makemigrations
python manage.py migrate
```

> Теперь все прежние связи «ученик → учитель» сохранены в новой M2M‑связи, и каждому ученику можно назначать сколько угодно учителей.

---

## Вариант такой же **АККУРАТНОЙ** миграции (компактно в одной миграции)

Если хочется одной миграцией без трёх файлов, порядок операций **внутри** единственного файла должен быть таким:

```python
operations = [
    migrations.AddField(... teachers ...),                                  # 1) создать M2M‑таблицу
    migrations.RunPython(copy_fk_to_m2m, migrations.RunPython.noop),        # 2) перенести данные из FK
    migrations.RemoveField(model_name='student', name='teacher'),           # 3) удалить FK
]
```

Код переноса такой же, как выше.

---

## Правки шаблона

`templates/school/students_list.html` — выводим всех учителей ученика:

```html
{% for student in object_list %}
  <li>
    {{ student.name }} {{ student.group }}<br>
    Преподаватели:
    {% for teacher in student.teachers.all %}
      {{ teacher.name }}: {{ teacher.subject }}{% if not forloop.last %}, {% endif %}
    {% empty %} — {% endfor %}
  </li>
{% endfor %}
```

## Правки view (оптимизация числа SQL‑запросов)

`school/views.py` — используем `prefetch_related` для M2M, чтобы не делать отдельный запрос на каждого ученика:

```python
ordering = 'group'
students = Student.objects.all().order_by(ordering).prefetch_related('teachers')
context['object_list'] = students
```

> Это закрывает доп. задание по анализу запросов: теперь ORM сделает 1 запрос за студентов и 1 запрос за их учителей, вместо N+1.

---

## Проверка и запуск

```bash
python manage.py migrate
python manage.py runserver
```

Открываем главную страницу. Для входа в админку (если нужно):

```bash
python manage.py createsuperuser
```

---

## Частые проблемы и как их решить

- **«field `teacher` doesn’t exist» в дата‑миграции** — удалили FK слишком рано. Убедитесь, что порядок **AddField → RunPython → RemoveField** соблюдается (либо тремя миграциями по очереди, либо в одной миграции — именно таким порядком в `operations`).  
- **У некоторых студентов нет учителя** — код переноса использует `getattr(s, 'teacher_id', None)`, так что пустые значения пропускаются.  
- **Большие данные** — миграции работают в транзакции по умолчанию. Для особо тяжёлых операций можно использовать `atomic = False` у миграции, но сейчас это не требуется.

---

## Необязательные улучшения

- В админке для удобного выбора учителей у ученика можно добавить:
  ```python
  @admin.register(Student)
  class StudentAdmin(admin.ModelAdmin):
      filter_horizontal = ('teachers',)
  ```
- В шаблоне можно стилизовать список учителей бейджиками.

---

Если потребуется, можно «сплющить» миграции позже через `squashmigrations`, когда функционал устоится.

- Итог на скриншотах 

Вид итоговой страницы
![итоговая страница](https://github.com/VoldemarSoturum/HW-7-4_DJANGO-Work-whith-ORM_PART-2/blob/main/EX1-ORM_Migrations/FOR_README/School-after-migrate.png) 

Вид конечной диаграммы взят из DBeaver
![Диаграмма](https://github.com/VoldemarSoturum/HW-7-4_DJANGO-Work-whith-ORM_PART-2/blob/main/EX1-ORM_Migrations/FOR_README/netology_orm_migrations-public.png)

