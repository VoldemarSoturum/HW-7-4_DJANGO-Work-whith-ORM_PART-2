from django.test import TestCase
from django.urls import reverse
from django.db import connection
from django.test.utils import CaptureQueriesContext
from school.models import Student, Teacher


class TestQueryCount(TestCase):
    """
    Проверяем, что список учеников не страдает от N+1.
    В students_list используется .prefetch_related('teachers'),
    поэтому ожидаем порядка 3 запросов:
      1) выборка студентов
      2) выборка связей из through-таблицы (m2m)
      3) выборка учителей
    """

    @classmethod
    def setUpTestData(cls):
        teachers = [
            Teacher.objects.create(name=f"Учитель {i}", subject=f"Предм{i}")
            for i in range(5)
        ]
        # Несколько студентов, каждому добавляем всех учителей
        for s in range(10):
            st = Student.objects.create(name=f"Ученик {s}", group="7А")
            st.teachers.set(teachers)

    def test_students_list_query_count(self):
        url = reverse("students")
        with CaptureQueriesContext(connection) as ctx:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200)
        # Немного «с запасом»: в зависимости от версии Django/настроек может быть 3 или 4.
        # Если у тебя стабильно 3 — можно зафиксировать ровно 3.
        self.assertLessEqual(len(ctx.captured_queries), 4, msg=f"Слишком много запросов: {len(ctx.captured_queries)}")
