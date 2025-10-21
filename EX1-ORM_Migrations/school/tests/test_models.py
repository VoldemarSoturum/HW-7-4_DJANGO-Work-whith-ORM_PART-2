# school/tests/test_models.py
from django.test import TestCase
from school.models import Student, Teacher

class TestModels(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.t1 = Teacher.objects.create(name="Иван Петров", subject="Матем")
        cls.t2 = Teacher.objects.create(name="Анна Смирнова", subject="Физика")
        cls.s1 = Student.objects.create(name="Вася", group="7А")
        cls.s2 = Student.objects.create(name="Маша", group="7Б")
        cls.s1.teachers.set([cls.t1, cls.t2])
        cls.s2.teachers.set([cls.t2])

    def test_student_has_many_teachers(self):
        self.assertEqual(self.s1.teachers.count(), 2)
        self.assertEqual(self.s2.teachers.count(), 1)

    def test_related_name_from_teacher(self):
        actual = list(self.t2.students.values_list('name', flat=True))
        expected = ["Маша", "Вася"]
        # порядок не важен (зависит от collation БД)
        self.assertCountEqual(actual, expected)

    def test_add_remove_m2m(self):
        self.s2.teachers.add(self.t1)
        self.assertEqual(self.s2.teachers.count(), 2)
        self.s2.teachers.remove(self.t1)
        self.assertEqual(self.s2.teachers.count(), 1)

    def test_str_methods(self):
        self.assertEqual(str(self.t1), "Иван Петров")
        self.assertEqual(str(self.t2), "Анна Смирнова")
        self.assertEqual(str(self.s1), "Вася")
        self.assertEqual(str(self.s2), "Маша")
