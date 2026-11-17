"""Additional regression tests for enhanced error classification."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import checker


class EnhancedClassificationTests(unittest.TestCase):
    def test_last_exception_in_chained_traceback_wins(self):
        log = (
            "Traceback (most recent call last):\n"
            "  File \"app.py\", line 3\n"
            "ValueError: initial problem\n"
            "\nDuring handling of the above exception, another exception occurred:\n"
            "Traceback (most recent call last):\n"
            "  File \"app.py\", line 7\n"
            "TypeError: final problem"
        )
        name, explanation = checker.classify_error(log)
        self.assertEqual(name, "TypeError")
        self.assertTrue(explanation)

    def test_unknown_exception_on_final_line(self):
        name, explanation = checker.classify_error(
            "NameError: earlier\nwidgets.custom.WidgetFailureException: later"
        )
        self.assertEqual(name, "WidgetFailureException")
        self.assertIn("실행 환경", explanation)

    def test_namespaced_exception(self):
        name, _ = checker.classify_error("builtins.PermissionError: [Errno 13] Denied")
        self.assertEqual(name, "PermissionError")

    def test_specific_subclass_takes_priority(self):
        name, _ = checker.classify_error("UnboundLocalError: variable referenced before assignment")
        self.assertEqual(name, "UnboundLocalError")
        self.assertEqual(checker.error_category(name), "변수·자료형")

    def test_file_and_permission_error_categories(self):
        for name in ("FileNotFoundError", "FileExistsError", "PermissionError", "OSError"):
            with self.subTest(name=name):
                self.assertEqual(checker.error_category(name), "파일·권한")
                self.assertEqual(checker.classify_error(f"{name}: failed")[0], name)

    def test_data_and_network_categories(self):
        self.assertEqual(checker.error_category("JSONDecodeError"), "자료·값")
        self.assertEqual(checker.error_category("UnicodeDecodeError"), "자료·값")
        self.assertEqual(checker.error_category("TimeoutError"), "실행·자원")
        self.assertEqual(checker.error_category("ConnectionError"), "실행·자원")

    def test_import_and_streamlit_categories(self):
        self.assertEqual(checker.error_category("ModuleNotFoundError"), "모듈·설치")
        self.assertEqual(checker.error_category("StreamlitDuplicateElementId"), "Streamlit")
        self.assertEqual(checker.classify_error("StreamlitDuplicateElementId: collision")[0],
                         "StreamlitDuplicateElementId")

    def test_empty_message_is_not_classified(self):
        self.assertEqual(checker.classify_error("")[0], "")
        self.assertEqual(checker.error_category(""), "기타·추가 확인 필요")

    def test_non_exception_message_keeps_existing_fallback(self):
        name, _ = checker.classify_error("I encountered an IndexError in my list")
        self.assertEqual(name, "IndexError")

    def test_auto_query_uses_last_error_without_source_snippets(self):
        log = 'ValueError: first\nTypeError: expected "PASSWORD_ABC123" but got value'
        query = checker.suggest_query(log, "python")
        self.assertTrue(query.startswith("TypeError"))
        self.assertNotIn("PASSWORD_ABC123", query)

    def test_unknown_error_still_supported(self):
        self.assertEqual(
            checker.classify_error("WidgetMagicException: not documented")[0],
            "WidgetMagicException",
        )


if __name__ == "__main__":
    unittest.main()
