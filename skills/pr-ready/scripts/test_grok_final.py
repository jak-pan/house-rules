import json
import os
import tempfile
import unittest

from grok_final import final_message


class GrokFinalTest(unittest.TestCase):
    def test_last_assistant_message_wins(self):
        with tempfile.TemporaryDirectory() as root:
            session = os.path.join(root, "%2Ftmp%2Fx", "sid-1")
            os.makedirs(session)
            with open(os.path.join(session, "chat_history.jsonl"), "w") as f:
                for entry in [
                    {"type": "assistant", "content": "I'll review the change."},
                    {"type": "tool_result", "content": "file"},
                    {"type": "assistant", "content": "VERDICT: APPROVE\n\nBlocking: none."},
                ]:
                    f.write(json.dumps(entry) + "\n")
            self.assertEqual(final_message({"sessionId": "sid-1"}, root), "VERDICT: APPROVE\n\nBlocking: none.")

    def test_missing_session_returns_none(self):
        with tempfile.TemporaryDirectory() as root:
            self.assertIsNone(final_message({"sessionId": "absent"}, root))
            self.assertIsNone(final_message({}, root))


if __name__ == "__main__":
    unittest.main()
