"""Regression checks for session-only Stack Overflow search history."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import search_history


class SearchHistoryTests(unittest.TestCase):
    def test_newest_first(self):
        entries = search_history.add_search([], "SyntaxError", "python", 5)
        entries = search_history.add_search(entries, "NameError", "python", 2)
        self.assertEqual([e["query"] for e in entries], ["NameError", "SyntaxError"])

    def test_repeated_query_refreshes_entry(self):
        entries = search_history.add_search([], "SyntaxError", "python", 5)
        entries = search_history.add_search(entries, "SyntaxError", "python", 1)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["count"], 1)

    def test_different_languages_separate(self):
        entries = search_history.add_search([], "fetch", "python", 5)
        entries = search_history.add_search(entries, "fetch", "javascript", 3)
        self.assertEqual(len(entries), 2)

    def test_bounded_and_clean(self):
        entries = []
        for i in range(30):
            entries = search_history.add_search(entries, " q" + str(i) + " ", "python", i)
        self.assertEqual(len(entries), 15)
        self.assertEqual(entries[0]["query"], "q29")
        self.assertEqual(entries[-1]["query"], "q15")

    def test_empty_query_ignored(self):
        self.assertEqual(search_history.add_search([], "   ", "python", 0), [])

    def test_search_history_present_in_ui(self):
        from streamlit.testing.v1 import AppTest
        app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
        self.assertEqual(len(app.exception), 0, [str(e) for e in app.exception])
        expander_labels = [x.label for x in app.get("expander")]
        self.assertTrue(any("최근 검색 기록" in label for label in expander_labels))


if __name__ == "__main__":
    unittest.main()
