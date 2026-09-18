import unittest
from voice_qa_console.rules import analyze_call
class VoiceEdgeTests(unittest.TestCase):
    def check(self, events, name):
        return next(x for x in analyze_call({'events':events}).checks if x.name==name)
    def test_yesterday_does_not_imply_consent(self):
        events=[{'timestamp_ms':0,'actor':'user','type':'message','content':'Yesterday I did not confirm.'}, {'timestamp_ms':100,'type':'tool_call','name':'send_email','arguments':{'to':'synthetic@example.com'}}]
        self.assertEqual(self.check(events,'consent_before_action').status, 'fail')
    def test_consent_cannot_be_reused_for_second_action(self):
        events=[{'timestamp_ms':0,'actor':'user','content':'Yes, please do.'}, {'timestamp_ms':100,'type':'tool_call','name':'send_email','arguments':{'to':'synthetic@example.com'}}, {'timestamp_ms':200,'type':'tool_call','name':'update_account','arguments':{'name':'Other'}}]
        self.assertEqual(self.check(events,'consent_before_action').status, 'fail')
    def test_unanswered_turn_is_stalled(self):
        self.assertEqual(self.check([{'actor':'user','timestamp_ms':0,'content':'Are you there?'}], 'latency').status, 'warn')
    def test_silence_capture_failure_and_stall_are_visible(self):
        events=[{'actor':'system','type':'silence','timestamp_ms':0,'duration_ms':6000}, {'actor':'system','type':'capture_error','timestamp_ms':6000,'content':'microphone unavailable'}, {'actor':'system','type':'stalled','timestamp_ms':7000}]
        check=self.check(events,'capture_health')
        self.assertEqual(check.status,'fail')
        self.assertEqual(len(check.evidence),3)
