"""Regression tests for optional AI error explanation and explicit API safeguards."""
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import ai_doctor


class AIExplanationTests(unittest.TestCase):
    def test_missing_api_key_never_calls_network(self):
        with patch.object(ai_doctor.requests, "post") as post:
            with self.assertRaisesRegex(ai_doctor.AIServiceError, "API 키"):
                ai_doctor.request_response({"오류": "NameError: x"}, api_key="")
            post.assert_not_called()

    def test_secrets_never_leave_local_guard(self):
        with patch.object(ai_doctor.requests, "post") as post:
            with self.assertRaisesRegex(ai_doctor.AIServiceError, "민감정보"):
                ai_doctor.request_response({"코드": 'api_key="fictional-secret123"'}, api_key="test-key")
            post.assert_not_called()

    def test_message_size_limit(self):
        with self.assertRaisesRegex(ai_doctor.AIServiceError, "12,000"):
            ai_doctor.validate_payload({"오류": "x" * 13000})

    def test_empty_fields_rejected(self):
        with self.assertRaises(ai_doctor.AIServiceError):
            ai_doctor.validate_payload({})

    @patch.object(ai_doctor.requests, "post")
    def test_request_disables_api_storage(self, post):
        response = Mock(status_code=200)
        response.json.return_value = {"output": [{
            "type": "message", "content": [{"type": "output_text", "text": "원인은 변수 누락입니다."}]
        }]}
        post.return_value = response
        result = ai_doctor.request_response({"오류": "NameError: x"}, api_key="local-secret")
        self.assertIn("변수", result)
        self.assertEqual(post.call_args.kwargs["json"]["store"], False)
        self.assertEqual(post.call_args.kwargs["json"]["model"], ai_doctor.DEFAULT_MODEL)
        self.assertNotIn("local-secret", str(post.call_args.kwargs["json"]))

    @patch.object(ai_doctor.requests, "post")
    def test_authentication_error_is_generic(self, post):
        post.return_value = Mock(status_code=401)
        with self.assertRaisesRegex(ai_doctor.AIServiceError, "인증"):
            ai_doctor.request_response({"오류": "NameError: x"}, api_key="secret-value")

    @patch.object(ai_doctor.requests, "post")
    def test_throttled_request_is_generic(self, post):
        post.return_value = Mock(status_code=429)
        with self.assertRaisesRegex(ai_doctor.AIServiceError, "한도"):
            ai_doctor.request_response({"오류": "NameError: x"}, api_key="secret-value")

    @patch.object(ai_doctor.requests, "post")
    def test_empty_response_rejected(self, post):
        response = Mock(status_code=200)
        response.json.return_value = {"output": []}
        post.return_value = response
        with self.assertRaisesRegex(ai_doctor.AIServiceError, "비어"):
            ai_doctor.request_response({"오류": "NameError: x"}, api_key="secret-value")

    def test_streamlit_panel_safe_without_key(self):
        from streamlit.testing.v1 import AppTest
        with patch.dict("os.environ", {"OPENAI_API_KEY": ""}):
            app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
        self.assertEqual(len(app.exception), 0, [str(x) for x in app.exception])
        self.assertTrue(any("AI 오류 원인 설명" in ex.label for ex in app.get("expander")))


if __name__ == "__main__":
    unittest.main()
