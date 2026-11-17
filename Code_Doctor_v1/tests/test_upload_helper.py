"""Regression checks for safe Python file upload decoding."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import upload_helper


class PythonUploadTests(unittest.TestCase):
    def test_utf8_file_loads(self):
        content = "def add(x, y):\n    return x + y\n"
        decoded = upload_helper.decode_python_upload("sample.py", content.encode("utf-8"))
        self.assertEqual(decoded, content)

    def test_utf8_bom_file_loads(self):
        self.assertEqual(
            upload_helper.decode_python_upload("hello.py", b"\xef\xbb\xbfprint(123)"),
            "print(123)",
        )

    def test_other_extensions_rejected(self):
        with self.assertRaises(ValueError):
            upload_helper.decode_python_upload("notes.exe", b"print(1)")

    def test_invalid_encoding_rejected(self):
        with self.assertRaises(ValueError):
            upload_helper.decode_python_upload("legacy.py", b"\xff\xfe\xfd")

    def test_large_file_rejected(self):
        with self.assertRaises(ValueError):
            upload_helper.decode_python_upload("big.py", b"x" * 11, max_bytes=10)

    def test_nonbinary_input_rejected(self):
        with self.assertRaises(ValueError):
            upload_helper.decode_python_upload("source.py", "print(1)")


if __name__ == "__main__":
    unittest.main()
