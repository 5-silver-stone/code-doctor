"""Tests use fake API responses; they do not require an Internet connection or a real key."""
import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import checker
import database as db
import pypi_api
import stack_api
import translate_api

class FakeResponse:
    def __init__(self, data=None, status=200):
        self.data = data or {}
        self.status_code = status
    def raise_for_status(self):
        import requests
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")
    def json(self):
        return self.data

class CheckerTests(unittest.TestCase):
    def test_syntax_valid(self):
        self.assertTrue(checker.check_python("x = 1\nprint(x)")["passed"])
    def test_syntax_invalid(self):
        item = checker.check_python("if True\n print('x')")
        self.assertFalse(item["passed"])
        self.assertEqual(item["line"], 1)
    def test_runtime_error_not_caught_by_syntax(self):
        self.assertTrue(checker.check_python("print(1 / 0)")["passed"])
    def test_classification(self):
        result = checker.classify_error("NameError: name 'foo' is not defined")
        self.assertEqual(result[0], "NameError")
    def test_no_secret_or_source_in_query(self):
        msg = 'NameError: name "API_KEY_ABC123" is not defined'
        self.assertNotIn("API_KEY_ABC123", checker.suggest_query(msg))
    def test_module_extraction(self):
        self.assertEqual(checker.extract_missing_module("ModuleNotFoundError: No module named 'pandas'"), "pandas")

class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "test.db"
        db.initialize(self.path)
    def tearDown(self):
        self.temp.cleanup()
    def create(self):
        return db.create_error({"title": "KeyError 테스트", "language": "python", "status": "미해결",
                                "error_type": "KeyError", "error_message": "KeyError: 'x'"}, self.path)
    def test_crud_persistence(self):
        rid = self.create()
        self.assertEqual(db.get_error(rid, self.path)["title"], "KeyError 테스트")
        self.assertEqual(len(db.list_errors("KeyError", path=self.path)), 1)
        self.assertTrue(db.update_error(rid, {"status": "해결", "solution": "get 사용"}, self.path))
        self.assertEqual(db.get_error(rid, self.path)["status"], "해결")
        self.assertTrue(db.delete_error(rid, self.path))
        self.assertEqual(db.list_errors(path=self.path), [])
    def test_missing_title(self):
        with self.assertRaises(ValueError):
            db.create_error({"title": " "}, self.path)
    def test_translation_cache(self):
        db.save_translation("Hello", "KO", "안녕하세요", self.path)
        self.assertEqual(db.get_translation("Hello", "KO", self.path), "안녕하세요")
    def test_bookmark_dedup(self):
        rid = self.create()
        q = {"question_id": 101, "title": "test", "link": "https://stackoverflow.com/questions/101"}
        self.assertTrue(db.add_bookmark(rid, q, {"answer_id": 303}, self.path))
        self.assertFalse(db.add_bookmark(rid, q, {"answer_id": 303}, self.path))
        self.assertEqual(len(db.list_bookmarks(rid, self.path)), 1)
        db.delete_error(rid, self.path)
        self.assertEqual(len(db.list_bookmarks(rid, self.path)), 0)

class APITests(unittest.TestCase):
    @patch("stack_api.requests.get", return_value=FakeResponse({"items": [{"question_id": 1}], "quota_remaining": 100}))
    def test_stack_search(self, get_mock):
        r = stack_api.search_questions("NameError", "python")
        self.assertEqual(r["items"][0]["question_id"], 1)
        self.assertEqual(get_mock.call_args.kwargs["params"]["tagged"], "python")
    @patch("stack_api.requests.get", return_value=FakeResponse({"items": [{"answer_id": 3}]}))
    def test_stack_answers(self, _):
        self.assertEqual(stack_api.fetch_answers(1)["items"][0]["answer_id"], 3)
    @patch("pypi_api.requests.get", return_value=FakeResponse({"info": {"name": "pandas", "version": "X.Y"}}))
    def test_pypi_lookup(self, _):
        self.assertEqual(pypi_api.lookup_package("pandas")["version"], "X.Y")
    def test_pypi_invalid(self):
        with self.assertRaises(ValueError):
            pypi_api.lookup_package("../private")
    def test_deepl_hosts(self):
        self.assertIn("api-free.deepl.com", translate_api.get_deepl_endpoint("123:fx"))
        self.assertIn("api.deepl.com", translate_api.get_deepl_endpoint("123456"))
    def test_html_code_is_preserved_and_not_sent(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "translations.db"
            db.initialize(path)
            with patch("translate_api.get_translation", return_value=None), \
                 patch("translate_api.save_translation") as save, \
                 patch("translate_api.requests.post", return_value=FakeResponse({
                     "translations": [{"text": "문제를 해결해 보세요."}, {"text": " 더 읽어보세요."}]
                 })) as post:
                # Parser may emit 1 or 2 prose pieces; use dynamic fake translation if needed.
                source = "<p>Try this <code>print(secret_key)</code> next.</p>"
                def fake_post(*args, **kwargs):
                    self.assertNotIn("secret_key", str(kwargs["json"]["text"]))
                    return FakeResponse({"translations": [{"text": "예시 안내"} for _ in kwargs["json"]["text"]]})
                post.side_effect = fake_post
                result = translate_api.translate_answer_html(source, "KO", "sample:fx")
                self.assertIn("print(secret_key)", result)
                save.assert_called_once()

if __name__ == "__main__":
    unittest.main()
