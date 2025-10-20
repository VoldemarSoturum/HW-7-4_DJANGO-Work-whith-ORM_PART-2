# articles/tests_runner.py
import sys
import unittest
from django.test.runner import DiscoverRunner

BAR_WIDTH = 30  # длина полоски прогресса


class ProgressTextTestResult(unittest.TextTestResult):
    """
    Результат с прогресс-баром в консоли.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.total_tests = 0
        self._seen = 0
        # Может быть назначен раннером:
        # self.verbosity = 1

    def startTest(self, test):
        super().startTest(test)
        self._seen += 1

        # полоса прогресса
        if self.total_tests:
            pct = self._seen / self.total_tests
            filled = int(BAR_WIDTH * pct)
            try:
                bar = "█" * filled + "░" * (BAR_WIDTH - filled)
            except Exception:
                bar = "#" * filled + "-" * (BAR_WIDTH - filled)
            self.stream.write(f"\r[{bar}] {self._seen}/{self.total_tests} ({int(pct*100)}%)")
            self.stream.flush()

        # подробный вывод имени теста при -v 2
        if getattr(self, "verbosity", 1) >= 2:
            name = self.getDescription(test)
            self.stream.write(f"\n→ {name}\n")
            self.stream.flush()

    def addError(self, test, err):
        super().addError(test, err)
        if getattr(self, "verbosity", 1) >= 2:
            self.stream.write("   ✖ ERROR\n")

    def addFailure(self, test, err):
        super().addFailure(test, err)
        if getattr(self, "verbosity", 1) >= 2:
            self.stream.write("   ✖ FAIL\n")

    def addSuccess(self, test):
        super().addSuccess(test)
        if getattr(self, "verbosity", 1) >= 2:
            self.stream.write("   ✓ OK\n")

    def stopTestRun(self):
        # финальный перевод строки, чтобы строка прогресса не залипла
        try:
            self.stream.write("\n")
            self.stream.flush()
        except Exception:
            pass
        super().stopTestRun()


class ProgressTextTestRunner(unittest.TextTestRunner):
    """
    TextTestRunner, который знает об общем количестве тестов
    и прокидывает verbosity в результат.
    """
    resultclass = ProgressTextTestResult

    def run(self, test):
        self._total = test.countTestCases()
        return super().run(test)

    def _makeResult(self):
        result = super()._makeResult()
        if isinstance(result, ProgressTextTestResult):
            result.total_tests = getattr(self, "_total", 0)
            # <-- ключевая строка: передаём уровень подробности
            result.verbosity = getattr(self, "verbosity", 1)
        return result


class ProgressTestRunner(DiscoverRunner):
    """
    Django Test Runner, использующий наш ProgressTextTestRunner.
    Совместим с Django 5.x: не пробрасываем несуществующие атрибуты.
    """
    def run_suite(self, suite, **kwargs):
        runner = ProgressTextTestRunner(
            verbosity=getattr(self, "verbosity", 1),
            failfast=getattr(self, "failfast", False),
            buffer=getattr(self, "buffer", False),
            descriptions=True,
            stream=sys.stderr,
        )
        return runner.run(suite)
