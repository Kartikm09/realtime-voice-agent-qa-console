import json
import unittest
from pathlib import Path

from voice_qa_console.rules import analyze_call


ROOT = Path(__file__).resolve().parents[1]


class VoiceQATests(unittest.TestCase):
    def test_example_scores_as_pass(self):
        payload = json.loads((ROOT / "examples" / "call_events.json").read_text())
        report = analyze_call(payload)
        self.assertGreaterEqual(report.score, 80)
        self.assertEqual(report.status, "pass")

    def test_action_before_consent_fails(self):
        payload = {
            "call_id": "bad-consent",
            "events": [
                {"timestamp_ms": 0, "actor": "user", "type": "message", "content": "I need a demo."},
                {
                    "timestamp_ms": 100,
                    "actor": "tool",
                    "type": "tool_call",
                    "name": "schedule_demo",
                    "arguments": {"time": "today"},
                },
            ],
        }
        report = analyze_call(payload)
        consent = next(check for check in report.checks if check.name == "consent_before_action")
        self.assertEqual(consent.status, "fail")

    def test_sensitive_information_request_fails_safety(self):
        payload = {
            "call_id": "bad-safety",
            "events": [
                {"timestamp_ms": 0, "actor": "assistant", "type": "message", "content": "Please share your password."}
            ],
        }
        report = analyze_call(payload)
        safety = next(check for check in report.checks if check.name == "safety")
        self.assertEqual(safety.status, "fail")


if __name__ == "__main__":
    unittest.main()
