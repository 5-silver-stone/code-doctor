"""Test safe multi-file upload validation and selection."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import upload_helper


class DummyUpload:
    def __init__(self, name, source):
        self.name = name
        self.data = source.encode("utf-8")
        self.size = len(self.data)

    def getvalue(self):
        return self.data


class MultiFileUploadTests(unittest.TestCase):
    def test_two_files_within_limits(self):
        self.assertEqual(
            upload_helper.validate_file_selection([
                DummyUpload("a.py", "print(1)"),
                DummyUpload("b.py", "print(2)"),
            ]), 16
        )

    def test_too_many_files_rejected(self):
        with self.assertRaisesRegex(ValueError, "최대 10개"):
            upload_helper.validate_file_selection(
                [DummyUpload(f"{n}.py", "x") for n in range(11)]
            )

    def test_one_file_over_limit_rejected(self):
        with self.assertRaisesRegex(ValueError, "512KB"):
            upload_helper.validate_file_selection(
                [DummyUpload("big.py", "x" * (512 * 1024 + 1))]
            )

    def test_total_over_limit_rejected(self):
        big = [DummyUpload(f"{n}.py", "x" * (450 * 1024)) for n in range(5)]
        with self.assertRaisesRegex(ValueError, "전체"):
            upload_helper.validate_file_selection(big)

    def test_invalid_file_metadata_rejected(self):
        with self.assertRaises(ValueError):
            upload_helper.validate_file_selection([object()])

    def test_multiple_uploads_default_to_first_file(self):
        from streamlit.testing.v1 import AppTest
        first = DummyUpload("first.py", "x = 1\nprint(x)")
        second = DummyUpload("second.py", "y = 2\nprint(y)")
        with patch("streamlit.file_uploader", return_value=[first, second]):
            app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
        self.assertEqual(len(app.exception), 0, [str(x) for x in app.exception])
        self.assertEqual(app.session_state["code_input"], first.data.decode())
        self.assertTrue(any("분석할 파일 선택" in item.label for item in app.selectbox))

    def test_switching_selected_file_changes_editor(self):
        from streamlit.testing.v1 import AppTest
        first = DummyUpload("first.py", "print('first')")
        second = DummyUpload("second.py", "print('second')")
        with patch("streamlit.file_uploader", return_value=[first, second]):
            app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
            picker = next(x for x in app.selectbox if "분석할 파일 선택" in x.label)
            picker.set_value(1).run()
        self.assertEqual(len(app.exception), 0, [str(x) for x in app.exception])
        self.assertEqual(app.session_state["code_input"], "print('second')")


if __name__ == "__main__":
    unittest.main()
