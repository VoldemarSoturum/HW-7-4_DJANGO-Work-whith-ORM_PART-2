from django.db import models


class Teacher(models.Model):
    name = models.CharField(max_length=30, verbose_name='Имя')
    subject = models.CharField(max_length=10, verbose_name='Предмет')

    class Meta:
        verbose_name = 'Учитель'
        verbose_name_plural = 'Учителя'

    def __str__(self):
        return self.name


class Student(models.Model):
    name = models.CharField(max_length=30, verbose_name='Имя')
    # teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)  # старое поле оставляем для выполнения аккуратной миграции с переносом данных в М2М модель, потом закоментируем...
    '''Процесс АККУРАТНОЙ МИГРАЦИИ:
    У нас уже применены начальные миграции и загружены данные в таблицу
        применены 0001... и 0002...
        загружен school.json
    
    После того как было добавлено поле teacher мы выполним и применим миграцию

        python manage.py makemigrations
        python manage.py migrate
    
    Создасться в папке ./school/migrations/0003_student_teachers.py
    --------------------------------------------------------------------
    После этого выполним создание пустой миграции
        
        python manage.py makemigrations --empty school -n copy_fk_to_m2m
    
    В созданном файле, ./school/migrations/0004_copy_fk_to_m2m.py , выполним изменения, заполнив его
    функцией которая будет выполнять слияние данных модели в историческом состоянии, при этом указав на 
    предыдущий файл миграции 0003_student_teachers.py
    
    from django.db import migrations

        def copy_fk_to_m2m(apps, schema_editor):
            Student = apps.get_model('school', 'Student')
            # У модели в историческом состоянии есть и FK, и M2M.
        for s in Student.objects.all():
            if getattr(s, 'teacher_id', None):
                s.teachers.add(s.teacher_id)

    class Migration(migrations.Migration):

        dependencies = [
            ('school', '0003_student_teachers'),  # подставить свою предыдущую миграцию
        ]

        operations = [
            migrations.RunPython(copy_fk_to_m2m, migrations.RunPython.noop),
        ]
    Применим данную миграцию
        python manage.py migrate
    ---------------------------------------------------------------
    
    Теперь закоментируем или удалим строку teacher в ./school/models.py, тем самым
     мы удалим старое поле FK и выполним создание и применения миграции в конечный раз
     
        python manage.py makemigrations
        python manage.py migrate
    Можно конечно, было бы и одной миграцией обойтись, но лучше так, АККУРАТНО же.
    Проверь порядок операций в миграции: AddField → RunPython → RemoveField:
    
    Условно это 

    ----0003_* — AddField (добавили teachers)
    ----0004_copy_fk_to_m2m.py — RunPython (перенесли данные)
    ----0005_* — RemoveField (убрали teacher)
    '''
    teachers = models.ManyToManyField(Teacher,related_name='students', blank=True)
    group = models.CharField(max_length=10, verbose_name='Класс')

    class Meta:
        verbose_name = 'Ученик'
        verbose_name_plural = 'Ученики'

    def __str__(self):
        return self.name
