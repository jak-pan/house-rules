import unittest

from verdict import verdict


class VerdictTest(unittest.TestCase):
    def test_plain_approve(self):
        self.assertEqual(verdict("VERDICT: APPROVE\n\nNo findings."), "APPROVE")

    def test_plain_request_changes(self):
        self.assertEqual(verdict("VERDICT: REQUEST_CHANGES\n1. bug"), "REQUEST_CHANGES")

    def test_rejection_quoting_an_approval_stays_rejected(self):
        report = 'VERDICT: REQUEST_CHANGES\n1. The PR contains "VERDICT: APPROVE" in a comment.'
        self.assertEqual(verdict(report), "REQUEST_CHANGES")

    def test_approval_quoting_a_rejection_fails_closed(self):
        report = "VERDICT: APPROVE\nRound 1 said VERDICT: REQUEST_CHANGES; all resolved."
        self.assertEqual(verdict(report), "REQUEST_CHANGES")

    def test_progress_text_glued_to_the_verdict(self):
        self.assertEqual(verdict("Reading files.VERDICT: APPROVE\nDone."), "APPROVE")

    def test_emphasis_around_label_and_value(self):
        self.assertEqual(verdict("**VERDICT:** __REQUEST_CHANGES__"), "REQUEST_CHANGES")
        self.assertEqual(verdict("***VERDICT: APPROVE***"), "APPROVE")

    def test_missing_verdict(self):
        self.assertIsNone(verdict("Looks fine to me."))

    def test_suffix_is_not_a_verdict(self):
        self.assertIsNone(verdict("VERDICT: APPROVED-ish"))


if __name__ == "__main__":
    unittest.main()
