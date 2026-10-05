import importlib.util
from pathlib import Path
import subprocess
import sys
import unittest


SCRIPT = Path(__file__).with_name("worker-pack.py")
spec = importlib.util.spec_from_file_location("worker_pack", SCRIPT)
worker_pack = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker_pack)


class WorkerPackTest(unittest.TestCase):
    def run_pack(self, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args], capture_output=True, text=True, timeout=5
        )

    def test_default_is_worker_pack(self):
        result = self.run_pack()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, worker_pack.pack() + "\n")
        self.assertNotIn("{{CANON}}", result.stdout)

    def test_reviewers_mode_prints_reviewer_pack(self):
        result = self.run_pack("reviewers")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, worker_pack.pack("reviewers") + "\n")
        self.assertNotIn("{{CANON}}", result.stdout)

    def test_explicit_workers_mode_matches_default(self):
        result = self.run_pack("workers")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, self.run_pack().stdout)

    def test_unknown_mode_fails_without_printing_a_pack(self):
        result = self.run_pack("reviewer")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertIn("invalid choice", result.stderr)


if __name__ == "__main__":
    unittest.main()
