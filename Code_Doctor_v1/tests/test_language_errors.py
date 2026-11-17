"""Safe non-Python traceback recognition regression checks."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import language_errors

class NonPythonDiagnosticsTests(unittest.TestCase):
    def test_javascript_reference_error(self):
        kind, explanation, group = language_errors.classify_log(
            "ReferenceError: foo is not defined", "javascript")
        self.assertEqual(kind, "ReferenceError")
        self.assertEqual(group, "변수·참조")
        self.assertTrue(explanation)

    def test_javascript_node_module_error(self):
        kind, _, group = language_errors.classify_log(
            "Error [ERR_MODULE_NOT_FOUND]: cannot find package", "javascript")
        self.assertEqual((kind, group), ("ERR_MODULE_NOT_FOUND", "모듈"))

    def test_java_null_pointer(self):
        kind, _, _ = language_errors.classify_log(
            "Exception in thread \"main\" java.lang.NullPointerException: null", "java")
        self.assertEqual(kind, "NullPointerException")

    def test_java_classpath_problem(self):
        self.assertEqual(
            language_errors.classify_log("java.lang.NoClassDefFoundError", "java")[0],
            "NoClassDefFoundError")

    def test_csharp_compiler_error(self):
        self.assertEqual(
            language_errors.classify_log("Program.cs(2,3): error CS1002: ; expected", "c#")[0],
            "CS1002")

    def test_csharp_exception(self):
        self.assertEqual(
            language_errors.classify_log("System.NullReferenceException: test", "c#")[0],
            "NullReferenceException")

    def test_unknown_input_safe(self):
        self.assertEqual(language_errors.classify_log("no error yet", "java")[0], "")
        self.assertEqual(language_errors.classify_log("", "javascript")[0], "")
        self.assertEqual(language_errors.classify_log("ReferenceError", "nonesuch")[0], "")

    def test_last_error_selected(self):
        self.assertEqual(language_errors.classify_log(
            "ReferenceError: first\nTypeError: second", "javascript")[0], "TypeError")

    def test_non_python_diagnostic_ui(self):
        from streamlit.testing.v1 import AppTest
        app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
        lang = next(x for x in app.selectbox if x.label == "프로그래밍 언어")
        lang.set_value("javascript").run()
        error = next(x for x in app.text_area if x.label == "오류 메시지 (선택)")
        error.set_value("ReferenceError: foo is not defined").run()
        self.assertEqual(len(app.exception), 0, [str(x) for x in app.exception])
        self.assertIn("ReferenceError", "\n".join(str(x.body) for x in app.info))


if __name__ == "__main__":
    unittest.main()
