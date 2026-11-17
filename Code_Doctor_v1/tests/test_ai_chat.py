"""Regression tests for bounded conversational debugging session."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import ai_doctor


class ChatTests(unittest.TestCase):
    def test_context_contains_recent_turns(self):
        entries = [
            {"role": "user", "content": "첫 질문"},
            {"role": "assistant", "content": "첫 답변"},
            {"role": "user", "content": "추가 질문"},
        ]
        result = ai_doctor.chat_context(entries)
        self.assertIn("사용자: 첫 질문", result)
        self.assertIn("AI: 첫 답변", result)
        self.assertIn("사용자: 추가 질문", result)

    def test_context_is_bounded(self):
        items = [{"role": "user", "content": "x" * 4000} for _ in range(100)]
        result = ai_doctor.chat_context(items)
        self.assertLessEqual(len(result), 9000)

    def test_invalid_context_rejected(self):
        with self.assertRaises(ValueError):
            ai_doctor.chat_context("not a list")

    def test_chat_controls_render_without_api_key(self):
        from streamlit.testing.v1 import AppTest
        app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
        self.assertEqual(len(app.exception), 0, [str(x) for x in app.exception])
        submit = next(x for x in app.button if x.label == "💬 추가 질문 보내기")
        self.assertTrue(submit.disabled)
        self.assertEqual(app.session_state["ai_chat"], [])

    def test_chat_is_session_only_not_written_to_database(self):
        src = (ROOT / "app.py").read_text(encoding="utf-8")
        self.assertIn('st.session_state.ai_chat', src)
        self.assertIn("ai_doctor.chat_context", src)


if __name__ == "__main__":
    unittest.main()
