"""Regression tests for daily saved-error trends."""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import database as db


class TrendTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "trend.db"
        db.initialize(self.path)

    def create(self, status):
        return db.create_error({"title": "sample", "language": "python",
                                "error_type": "TypeError", "status": status}, self.path)

    def test_created_today_grouped(self):
        self.create("미해결")
        self.create("해결")
        trend = db.error_trend(7, self.path)
        self.assertEqual(len(trend), 1)
        self.assertEqual(trend[0]["total"], 2)
        self.assertEqual(trend[0]["resolved"], 1)

    def test_old_records_excluded(self):
        record_id = self.create("해결")
        with db.connect(self.path) as conn:
            conn.execute(
                "UPDATE error_records SET created_at=datetime('now','localtime','-100 days') WHERE id=?",
                (record_id,),
            )
        self.assertEqual(db.error_trend(90, self.path), [])

    def test_empty_records(self):
        self.assertEqual(db.error_trend(30, self.path), [])

    def test_invalid_days_rejected(self):
        for value in (0, -1, 31, 365, "30"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                db.error_trend(value, self.path)

    def test_ui_stats_screen_loads_without_records(self):
        from streamlit.testing.v1 import AppTest
        app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
        app.sidebar.radio[0].set_value("오류 통계").run()
        self.assertEqual(len(app.exception), 0, [str(e) for e in app.exception])


if __name__ == "__main__":
    unittest.main()
