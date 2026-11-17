"""UI regression tests for the prominently placed upload panel."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

APP_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_DIR))


class FakeUploadedPython:
    name = "example.py"

    def __init__(self, source):
        self.data = source.encode("utf-8")
        self.size = len(self.data)

    def getvalue(self):
        return self.data


class UploadPanelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from streamlit.testing.v1 import AppTest
        cls.AppTest = AppTest

    def test_upload_section_is_prominent_and_descriptive(self):
        app = self.AppTest.from_file(str(APP_DIR / "app.py"), default_timeout=30).run()
        self.assertEqual(len(app.exception), 0, [str(item) for item in app.exception])
        page_text = "\n".join(str(m.value) for m in app.markdown)
        self.assertIn("Python 파일 업로드", page_text)
        self.assertIn("드래그", page_text)
        source = (APP_DIR / "app.py").read_text(encoding="utf-8")
        self.assertIn('st.file_uploader(', source)
        self.assertIn('key="python_upload"', source)

    def test_uploaded_file_populates_existing_editor(self):
        source = "x = 2\nprint(x)\n"
        with patch("streamlit.file_uploader", return_value=FakeUploadedPython(source)):
            app = self.AppTest.from_file(str(APP_DIR / "app.py"), default_timeout=30).run()
        self.assertEqual(len(app.exception), 0, [str(item) for item in app.exception])
        self.assertEqual(app.session_state["code_input"], source)

    def test_uploaded_code_is_not_executed(self):
        source = "raise RuntimeError('do not run this code')\n"
        with patch("streamlit.file_uploader", return_value=FakeUploadedPython(source)):
            app = self.AppTest.from_file(str(APP_DIR / "app.py"), default_timeout=30).run()
        self.assertEqual(len(app.exception), 0, [str(item) for item in app.exception])
        self.assertEqual(app.session_state["code_input"], source)


if __name__ == "__main__":
    unittest.main()
