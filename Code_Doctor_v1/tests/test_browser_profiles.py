"""Regression tests for optional device-local convenience profiles."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import browser_profiles as profile


class BrowserProfileTests(unittest.TestCase):
    def test_signup_login_and_pin_not_stored_in_plaintext(self):
        initial = profile.load_bundle(None)
        changed = profile.signup(initial, "학생1", "1234")
        self.assertTrue(profile.authenticate(changed, "학생1", "1234"))
        self.assertFalse(profile.authenticate(changed, "학생1", "9999"))
        self.assertNotIn("1234", str(changed))
        self.assertEqual(initial["accounts"], {})

    def test_duplicate_signup_on_same_device_rejected(self):
        changed = profile.signup(profile.load_bundle(None), "Example", "1234")
        with self.assertRaisesRegex(ValueError, "이미"):
            profile.signup(changed, "example", "2345")

    def test_invalid_pin_rejected(self):
        for pin in ("123", "abcd", "12345", ""):
            with self.subTest(pin=pin), self.assertRaises(ValueError):
                profile.signup(profile.load_bundle(None), "test-account", pin)

    def test_per_profile_notes_not_mixed(self):
        bundle = profile.signup(profile.load_bundle(None), "alice", "1234")
        bundle = profile.signup(bundle, "bob", "5678")
        bundle = profile.add_note(bundle, "alice", "에러 A", "코드의 콜론 수정")
        self.assertEqual(len(bundle["accounts"]["alice"]["notes"]), 1)
        self.assertEqual(len(bundle["accounts"]["bob"]["notes"]), 0)

    def test_secrets_rejected_from_local_notes(self):
        bundle = profile.signup(profile.load_bundle(None), "alice", "1234")
        with self.assertRaisesRegex(ValueError, "민정보|비밀키|개인정보"):
            profile.add_note(bundle, "alice", "키", 'password="fictional-secret"')

    def test_broken_browser_state_rejected(self):
        with self.assertRaises(ValueError):
            profile.load_bundle("{broken")
        with self.assertRaises(ValueError):
            profile.load_bundle([])

    def test_profile_page_renders_with_browser_storage_mock(self):
        from streamlit.testing.v1 import AppTest
        with patch("streamlit_local_storage.LocalStorage") as local:
            local.return_value.getItem.return_value = '{"version": 1, "accounts": {}}'
            app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
            app.sidebar.radio[0].set_value("기기별 프로필").run()
        self.assertEqual(len(app.exception), 0, [str(e) for e in app.exception])
        self.assertEqual(app.sidebar.radio[0].value, "기기별 프로필")
        self.assertIn("📱 이 브라우저의 간편 프로필", (ROOT / "app.py").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
