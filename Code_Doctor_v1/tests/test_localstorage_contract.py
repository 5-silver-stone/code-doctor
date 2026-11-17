"""Guard against incompatible streamlit-local-storage getItem calls.

The pinned 0.0.25 library accepts getItem(itemKey), not getItem(itemKey, key=...).
"""
import inspect
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import browser_profiles


class StrictBrowserStorage:
    """A fake with the actual package's narrow API (no **kwargs on getItem)."""
    current_value = None
    read_keys = []

    def __init__(self):
        pass

    def getItem(self, itemKey):
        type(self).read_keys.append(itemKey)
        return type(self).current_value

    def setItem(self, itemKey, itemValue, key="set"):
        type(self).current_value = itemValue


class LocalStorageContractTests(unittest.TestCase):
    def setUp(self):
        StrictBrowserStorage.read_keys = []
        StrictBrowserStorage.current_value = None

    def test_pinned_package_getitem_signature(self):
        from streamlit_local_storage import LocalStorage
        signature = inspect.signature(LocalStorage.getItem)
        self.assertIn("itemKey", signature.parameters)
        self.assertNotIn("key", signature.parameters)

    def test_profile_page_loads_saved_profiles_via_actual_getitem_contract(self):
        from streamlit.testing.v1 import AppTest
        existing = browser_profiles.signup(
            browser_profiles.load_bundle(None), "Test Account", "1234"
        )
        StrictBrowserStorage.current_value = json.dumps(existing)
        with patch("streamlit_local_storage.LocalStorage", StrictBrowserStorage):
            app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
            app.sidebar.radio[0].set_value("기기별 프로필").run()

        self.assertEqual(len(app.exception), 0, [str(e) for e in app.exception])
        self.assertEqual(
            StrictBrowserStorage.read_keys[-1], browser_profiles.STORAGE_KEY
        )
        self.assertIn("test account", app.session_state["browser_profile_bundle"]["accounts"])

    def test_missing_device_data_opens_empty_profile_screen(self):
        from streamlit.testing.v1 import AppTest
        with patch("streamlit_local_storage.LocalStorage", StrictBrowserStorage):
            app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
            app.sidebar.radio[0].set_value("기기별 프로필").run()

        self.assertEqual(len(app.exception), 0, [str(e) for e in app.exception])
        self.assertFalse(app.session_state.get("browser_profile_bundle"))

    def test_component_typeerror_has_informative_fallback_not_crash(self):
        from streamlit.testing.v1 import AppTest
        class BrokenStorage:
            def __init__(self):
                pass
            def getItem(self, itemKey):
                raise TypeError("unavailable storage component")

        with patch("streamlit_local_storage.LocalStorage", BrokenStorage):
            app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
            app.sidebar.radio[0].set_value("기기별 프로필").run()

        self.assertEqual(len(app.exception), 0, [str(e) for e in app.exception])
        self.assertTrue(any("브라우저 저장소" in str(e.message) for e in app.error))


if __name__ == "__main__":
    unittest.main()
