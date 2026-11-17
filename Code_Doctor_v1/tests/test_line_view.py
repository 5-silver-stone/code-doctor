"""Tests for error-line highlighting with HTML escaping and Streamlit integration."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import line_view


class HighlightedLineTests(unittest.TestCase):
    def test_error_line_highlighted_with_neighboring_lines(self):
        excerpt = line_view.highlighted_excerpt("x = 1\nif True print(x)\ny = 2", 2)
        self.assertIn('class="code-error-line" aria-label="2행 오류 발생"', excerpt)
        self.assertIn('class="code-normal-line" aria-label="1행"', excerpt)
        self.assertIn("if True print(x)", excerpt)

    def test_user_html_escaped_not_executed_or_interpreted(self):
        source = 'print("<script>alert(1)</script>")'
        excerpt = line_view.highlighted_excerpt(source, 1)
        self.assertIn("&lt;script&gt;", excerpt)
        self.assertNotIn("<script>", excerpt)

    def test_context_window_clipped(self):
        excerpt = line_view.highlighted_excerpt("\n".join(f"line {i}" for i in range(50)), 25)
        self.assertIn("line 24", excerpt)
        self.assertNotIn("line 10", excerpt)
        self.assertIn("…", excerpt)

    def test_invalid_location_does_not_render(self):
        self.assertEqual(line_view.highlighted_excerpt("print(1)", 99), "")
        self.assertEqual(line_view.highlighted_excerpt("print(1)", None), "")

    def test_empty_line_is_represented(self):
        self.assertIn('aria-label="2행 오류 발생"',
                      line_view.highlighted_excerpt("x = 1\n\ny = 3", 2))

    def test_ui_detects_syntax_error_without_crash(self):
        from streamlit.testing.v1 import AppTest
        app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
        self.assertGreaterEqual(len(app.text_area), 2)
        app.text_area[1].set_value("x = 1\nif True print(x)").run()
        self.assertEqual(len(app.exception), 0, [str(x) for x in app.exception])
        page = "\n".join(str(markdown.value) for markdown in app.markdown)
        self.assertIn("오류가 발생한 코드 줄", page)
        self.assertIn("code-error-line", page)


if __name__ == "__main__":
    unittest.main()
