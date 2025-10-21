from django.test import TestCase
from django.urls import reverse
from school.models import Student, Teacher


class TestStudentsListView(TestCase):
    @classmethod
    def setUpTestData(cls):
        t1 = Teacher.objects.create(name="Иван Петров", subject="Матем")
        t2 = Teacher.objects.create(name="Анна Смирнова", subject="Физика")
        s1 = Student.objects.create(name="Вася", group="7А")
        s2 = Student.objects.create(name="Маша", group="7Б")
        s1.teachers.set([t1, t2])
        s2.teachers.set([t2])

    def test_students_page_status(self):
        url = reverse("students")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_students_page_context(self):
        url = reverse("students")
        resp = self.client.get(url)
        # В view мы кладём students в context['object_list']
        self.assertIn("object_list", resp.context)
        self.assertGreaterEqual(resp.context["object_list"].count(), 2)

    def test_template_renders_teachers(self):
        url = reverse("students")
        resp = self.client.get(url)
        content = resp.content.decode("utf-8")
        # Проверяем, что имена учителей видны на странице
        self.assertIn("Иван Петров", content)
        self.assertIn("Анна Смирнова", content)
        self.assertIn("Матем", content)
        self.assertIn("Физика", content)
