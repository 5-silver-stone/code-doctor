"""Tests for the local-only credential warning feature."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import security_guard


class SecurityGuardTests(unittest.TestCase):
    def test_api_key_assignment_is_detected_without_exposing_value(self):
        text = "api_key = 'fictional-value-for-test-only'"
        findings = security_guard.scan_text(text)
        self.assertTrue(findings)
        self.assertEqual(findings[0]["line"], 1)
        self.assertNotIn("fictional-value-for-test-only", str(findings))

    def test_email_detected_with_line_number(self):
        found = security_guard.scan_text("a = 1\ncontact = 'example@example.org'")
        self.assertEqual(found[0]["kind"], "이메일 주소")
        self.assertEqual(found[0]["line"], 2)

    def test_private_key_marker_detected(self):
        result = security_guard.scan_text("-----BEGIN PRIVATE KEY-----")
        self.assertTrue(any(item["kind"] == "개인 키" for item in result))

    def test_regular_traceback_and_source_are_not_blocked(self):
        text = "NameError: name 'x' is not defined\nprint(x)"
        self.assertEqual(security_guard.scan_text(text), [])

    def test_environment_variable_reference_not_treated_as_literal(self):
        text = 'api_key = os.getenv("DEEPL_API_KEY")'
        self.assertEqual(security_guard.scan_text(text), [])

    def test_field_labels_without_raw_secret_values(self):
        found = security_guard.scan_fields({
            "오류 메시지": "NameError: x",
            "코드": 'password="fictional-password"',
        })
        self.assertTrue(found)
        self.assertEqual(found[0]["field"], "코드")
        self.assertNotIn("fictional-password", str(found))

    def test_large_input_limited(self):
        found = security_guard.scan_text("test@example.org\n" * 100, max_findings=3)
        self.assertEqual(len(found), 3)


if __name__ == "__main__":
    unittest.main()
