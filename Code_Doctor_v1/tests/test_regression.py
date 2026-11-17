"""Regression tests for Code Doctor's existing public features.

Run: python -m unittest discover -s Code_Doctor_v1/tests -v
No live API calls or user data are required.
"""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

APP_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_DIR))

import checker
import database as db
import pypi_api
import stack_api
import translate_api


class CheckerTests(unittest.TestCase):
    def test_known_error_type_and_explanation(self):
        name, explanation = checker.classify_error("NameError: name 'foo' is not defined")
        self.assertEqual(name, "NameError")
        self.assertTrue(explanation)

    def test_unknown_error_fallback(self):
        name, explanation = checker.classify_error("WidgetMagicException: failed")
        self.assertEqual(name, "WidgetMagicException")
        self.assertTrue(explanation)

    def test_valid_code(self):
        result = checker.check_python("x = 3\nprint(x)")
        self.assertTrue(result["passed"])

    def test_syntax_error_has_line_and_column(self):
        result = checker.check_python("x = 1\nif True print(x)")
        self.assertFalse(result["passed"])
        self.assertEqual(result["line"], 2)
        self.assertGreater(result["column"], 0)

    def test_empty_code_is_not_checked(self):
        self.assertFalse(checker.check_python("  ")["checked"])

    def test_query_removes_quoted_values_and_paths(self):
        query = checker.suggest_query(
            "File C:/work/project.py\nNameError: name 'SECRET' is not defined", "python"
        )
        self.assertIn("NameError", query)
        self.assertNotIn("SECRET", query)
        self.assertNotIn("C:/work", query)

    def test_unknown_message_never_auto_sends_full_traceback(self):
        self.assertEqual(checker.suggest_query("secret_token=abc123"), "")

    def test_missing_module_extract(self):
        msg = "ModuleNotFoundError: No module named 'pandas.core'"
        self.assertEqual(checker.extract_missing_module(msg), "pandas")


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "test.db"
        db.initialize(self.path)

    def make_record(self, title="문법 오류", status="미해결"):
        return db.create_error({
            "title": title, "language": "python", "environment": "VS Code",
            "error_type": "SyntaxError", "error_message": "invalid syntax",
            "source_code": "", "description": "test", "expected": "",
            "actual": "", "cause": "", "solution": "", "status": status,
        }, self.path)

    def test_create_read_search_update_and_delete(self):
        record_id = self.make_record()
        self.assertEqual(db.get_error(record_id, self.path)["title"], "문법 오류")
        self.assertEqual(len(db.list_errors("문법", "전체", self.path)), 1)
        self.assertTrue(db.update_error(
            record_id, {"status": "해결", "solution": "콜론 추가"}, self.path
        ))
        self.assertEqual(db.get_error(record_id, self.path)["status"], "해결")
        self.assertEqual(len(db.list_errors("", "미해결", self.path)), 0)
        self.assertTrue(db.delete_error(record_id, self.path))
        self.assertIsNone(db.get_error(record_id, self.path))

    def test_title_is_required(self):
        with self.assertRaises(ValueError):
            db.create_error({"title": "  "}, self.path)

    def test_bookmark_deduplication_and_cascade_delete(self):
        record_id = self.make_record()
        question = {"question_id": 42, "title": "test", "link": "https://stackoverflow.com/q/42"}
        answer = {"answer_id": 123}
        self.assertTrue(db.add_bookmark(record_id, question, answer, self.path))
        self.assertFalse(db.add_bookmark(record_id, question, answer, self.path))
        self.assertEqual(len(db.list_bookmarks(record_id, self.path)), 1)
        db.delete_error(record_id, self.path)
        self.assertEqual(db.list_bookmarks(record_id, self.path), [])

    def test_statistics(self):
        self.make_record("첫 번째")
        self.make_record("두 번째", "해결")
        statuses, categories = db.statistics(self.path)
        self.assertEqual(sum(x["count"] for x in statuses), 2)
        self.assertEqual(categories[0]["error_type"], "SyntaxError")

    def test_translation_cache(self):
        self.assertIsNone(db.get_translation("hello", "KO", self.path))
        db.save_translation("hello", "KO", "안녕", self.path)
        self.assertEqual(db.get_translation("hello", "KO", self.path), "안녕")


class StackApiTests(unittest.TestCase):
    def test_empty_search_rejected(self):
        with self.assertRaises(ValueError):
            stack_api.search_questions("  ")

    @patch.object(stack_api.requests, "get")
    def test_search_sends_keyword_and_language_not_code(self, get):
        response = Mock()
        response.json.return_value = {"items": [], "quota_remaining": 100}
        get.return_value = response
        data = stack_api.search_questions("NameError", "python")
        self.assertEqual(data["quota_remaining"], 100)
        kwargs = get.call_args.kwargs
        self.assertEqual(kwargs["params"]["q"], "NameError")
        self.assertEqual(kwargs["params"]["tagged"], "python")
        self.assertLessEqual(kwargs["timeout"], 15)

    @patch.object(stack_api.requests, "get")
    def test_api_error_converted(self, get):
        response = Mock()
        response.json.return_value = {"error_message": "rate limit"}
        get.return_value = response
        with self.assertRaises(stack_api.APIError):
            stack_api.search_questions("NameError")

    def test_invalid_question_id(self):
        with self.assertRaises(ValueError):
            stack_api.fetch_answers(0)


class PyPiTests(unittest.TestCase):
    def test_invalid_package_rejected(self):
        with self.assertRaises(ValueError):
            pypi_api.lookup_package("../bad")

    @patch.object(pypi_api.requests, "get")
    def test_existing_package_info(self, get):
        response = Mock(status_code=200)
        response.json.return_value = {"info": {
            "name": "requests", "version": "2.1", "summary": "HTTP client",
            "requires_python": ">=3.9",
        }}
        get.return_value = response
        pkg = pypi_api.lookup_package("requests")
        self.assertEqual(pkg["name"], "requests")
        self.assertEqual(pkg["version"], "2.1")

    @patch.object(pypi_api.requests, "get")
    def test_package_not_found(self, get):
        get.return_value = Mock(status_code=404)
        self.assertIsNone(pypi_api.lookup_package("not-a-real-package"))


class TranslationTests(unittest.TestCase):
    def test_html_to_markdown_disallows_script(self):
        text, _ = translate_api.html_to_markdown(
            "<p>Hello</p><script>alert('secret')</script><p>World</p>"
        )
        self.assertIn("Hello", text)
        self.assertIn("World", text)
        self.assertNotIn("alert", text)

    def test_code_preserved_when_reading_original(self):
        html = "<p>Run this:</p><pre><code>print(42)</code></pre>"
        result = translate_api.translate_answer_html(html, "EN", "")
        self.assertIn("print(42)", result)
        self.assertIn("```", result)

    def test_translation_without_key_fails_safely(self):
        with self.assertRaises(translate_api.TranslationError):
            translate_api.translate_answer_html("<p>Hi</p>", "KO", "")

    def test_deepl_endpoint_selection(self):
        self.assertIn("api-free.deepl.com", translate_api.get_deepl_endpoint("abc:fx"))
        self.assertIn("api.deepl.com", translate_api.get_deepl_endpoint("abc"))


class StreamlitSmokeTests(unittest.TestCase):
    """Verify all existing screens render without live APIs being called."""

    @classmethod
    def setUpClass(cls):
        from streamlit.testing.v1 import AppTest
        cls.AppTest = AppTest

    def make_app(self):
        app = self.AppTest.from_file(str(APP_DIR / "app.py"), default_timeout=30)
        return app.run()

    def test_default_screen_and_theme_toggle(self):
        app = self.make_app()
        self.assertEqual(len(app.exception), 0, [str(e) for e in app.exception])
        self.assertGreaterEqual(len(app.sidebar.toggle), 1)
        app.sidebar.toggle[0].set_value(True).run()
        self.assertEqual(len(app.exception), 0, [str(e) for e in app.exception])

    def test_other_main_pages_render(self):
        app = self.make_app()
        for page in ("저장 기록", "오류 통계", "API·사용 안내"):
            app.sidebar.radio[0].set_value(page).run()
            self.assertEqual(len(app.exception), 0, f"{page}: {[str(e) for e in app.exception]}")


if __name__ == "__main__":
    unittest.main()
