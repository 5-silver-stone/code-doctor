"""Optional AI code-suggestion UI regression checks."""
import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


class SuggestionTests(unittest.TestCase):
    def test_suggestion_control_present_without_api_key(self):
        app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
        self.assertEqual(len(app.exception), 0, [str(x) for x in app.exception])
        button = next(button for button in app.button if button.label == "🛠️ AI 수정 코드 생성")
        self.assertTrue(button.disabled)
        self.assertEqual(app.session_state["ai_suggestion"], "")

    def test_ai_never_overwrites_source_automatically(self):
        code = (ROOT / "app.py").read_text(encoding="utf-8")
        self.assertIn("수정 코드 제안 결과 (자동 반영되지 않음)", code)
        self.assertIn("st.session_state.ai_suggestion", code)
        self.assertNotIn('st.session_state["code_input"] = st.session_state.ai_suggestion', code)


if __name__ == "__main__":
    unittest.main()
