"""Regression checks for beginner/expert AI explanation controls."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import ai_doctor

class LevelTests(unittest.TestCase):
    def test_beginner_instructions_are_clear(self):
        text = ai_doctor.level_instructions("초보자", "explain")
        self.assertIn("쉬운 예시", text)
        self.assertIn("확인 단계", text)

    def test_expert_instructions_include_verification(self):
        text = ai_doctor.level_instructions("전문가", "explain")
        self.assertIn("재현 조건", text)
        self.assertIn("검증", text)

    def test_suggestion_prompts_do_not_automatically_apply_code(self):
        text = ai_doctor.level_instructions("전문가", "suggest")
        self.assertIn("자동 변경하지 마", text)

    def test_invalid_level_and_task_rejected(self):
        with self.assertRaises(ValueError):
            ai_doctor.level_instructions("최고", "explain")
        with self.assertRaises(ValueError):
            ai_doctor.level_instructions("초보자", "hack")

    def test_level_radio_renders_and_switches(self):
        from streamlit.testing.v1 import AppTest
        app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
        level = next(x for x in app.radio if x.label == "설명 수준")
        level.set_value("전문가").run()
        self.assertEqual(len(app.exception), 0, [str(x) for x in app.exception])
        self.assertEqual(app.session_state["ai_explain_level"], "전문가")


if __name__ == "__main__":
    unittest.main()
