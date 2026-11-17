"""Verify the existing Streamlit Cloud entrypoint loads the maintained app."""
from pathlib import Path
import unittest

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
CLOUD_ENTRY = ROOT / "Code_Doctor_v1" / "app.py"


class CloudEntrypointTests(unittest.TestCase):
    def test_existing_deploy_path_runs_updated_app(self):
        self.assertTrue(CLOUD_ENTRY.is_file())
        app = AppTest.from_file(str(CLOUD_ENTRY), default_timeout=30).run()
        self.assertEqual(len(app.exception), 0, [str(e) for e in app.exception])
        rendered = "\n".join(str(item.value) for item in app.markdown)
        self.assertIn("v1.3.1", rendered)
        self.assertIn("Python 파일 업로드", rendered)
        self.assertGreaterEqual(len(app.sidebar.toggle), 1)

    def test_legacy_path_keeps_dark_mode_working(self):
        app = AppTest.from_file(str(CLOUD_ENTRY), default_timeout=30).run()
        app.sidebar.toggle[0].set_value(True).run()
        self.assertEqual(len(app.exception), 0, [str(e) for e in app.exception])


if __name__ == "__main__":
    unittest.main()
