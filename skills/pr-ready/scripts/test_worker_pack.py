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


class RuleOwnershipTest(unittest.TestCase):
    root = SCRIPT.parents[3]

    def text(self, path):
        return " ".join((self.root / path).read_text().split())

    def test_two_fix_rounds_require_simplify_or_split(self):
        rules = self.text("skills/pr-ready/SKILL.md")
        reassessment = rules.split("**Review reassessment.**", 1)[1].split(
            "**Repeat defects.**", 1
        )[0]
        self.assertIn("After two fix rounds", reassessment)
        self.assertRegex(reassessment, r"stop.*lead.*simplify.*split")
        self.assertNotIn("or continue", reassessment)
        self.assertNotIn("not a hardcoded stop", reassessment)

    def test_design_disposition_has_one_owner(self):
        common = self.text("skills/pr-ready/reviewers/common.md")
        bar, remainder = common.split("{{CANON}}", 1)
        self.assertRegex(bar, r"design finding.*stops for a lead decision")
        self.assertIn("never becomes a follow-up or starts another fix round", bar)
        self.assertNotRegex(remainder, r"design finding (?:stays|stops)")
        self.assertIn("§Review bar", remainder)
        for path in (
            "skills/pr-ready/reviewers/design.md",
            "skills/pr-ready/SKILL.md",
            "skills/pr-ready/references/review-lenses.md",
            "skills/design-flow/SKILL.md",
        ):
            with self.subTest(path=path):
                text = self.text(path)
                self.assertNotRegex(text, r"design finding stops|design findings cannot")
                self.assertIn("common.md#review-bar", text)

    def test_feature_implementation_uses_worker_choice_boundaries(self):
        rules = self.text("skills/design-flow/SKILL.md")
        implementation = rules.split("## 5. Implement", 1)[1].split(
            "## Design changes", 1
        )[0]
        self.assertIn("design-spec reviewer checks its spec sections", implementation)
        self.assertIn("workers/common.md", implementation)
        self.assertNotIn("choose the simplest option", implementation)
        self.assertNotIn("Stop and report options", implementation)
        self.assertNotIn("never settle them by editing the spec", implementation)

    def test_test_logging_and_pruning_belong_to_guard_upkeep(self):
        canon = self.text("skills/pr-ready/canon.md")
        self.assertIn("references/guards.md#guard-upkeep", canon)
        self.assertNotIn("log runtime", canon)
        self.assertNotRegex(canon, r"prune or bound slow")
        self.assertIn("Scale tests move, never vanish", canon)
        guards = self.text("skills/pr-ready/references/guards.md")
        self.assertIn("Every guard and every test logs", guards)
        self.assertIn("pruning or narrowing guards and tests", guards)

    def test_lane_cache_policy_references_worker_owner(self):
        lanes = self.text("skills/agent-lanes/SKILL.md")
        self.assertIn("workers/common.md", lanes)
        self.assertNotRegex(lanes, r"target directory must never bypass")
        self.assertIn("Build output lives inside the lane's own worktree", lanes)
        self.assertIn(".tmp/cargo-target/<lane>", lanes)
        worker = self.text("skills/pr-ready/workers/common.md")
        self.assertIn("configured compiler cache; never disable it", worker)

    def test_decision_ids_keep_option_formatting_in_operator_writing(self):
        brief = self.text("skills/decision-brief/SKILL.md")
        self.assertIn("Stable decision IDs", brief)
        self.assertIn("Decision 1 = Option 2, Decision 2 = Option 1", brief)
        self.assertIn("operator-writing/SKILL.md#structure", brief)
        self.assertNotIn("options numbered", brief)
        self.assertNotIn("Options use only", brief)
        self.assertNotIn("no letters or mixed schemes", brief)

    def test_review_template_does_not_copy_reviewer_instructions(self):
        template = self.text("skills/pr-ready/references/review-prompt.md")
        review = template.split("## Fix prompt template", 1)[0]
        self.assertIn("shared reviewer pack", review)
        self.assertIn("Scope:", review)
        self.assertIn("Under <N> lines", review)
        for copied in ("Challenge the spec", "VERDICT:", "Do not edit files"):
            with self.subTest(copied=copied):
                self.assertNotIn(copied, review)

    def test_fix_dispatch_references_worker_procedure(self):
        for path in (
            "skills/pr-ready/SKILL.md",
            "skills/pr-ready/references/review-prompt.md",
        ):
            with self.subTest(path=path):
                text = self.text(path)
                self.assertRegex(text, r"worker pack|workers/common\.md")
                for copied in (
                    "with the smallest fix",
                    "reviewer's smallest fix",
                    "regression test",
                    "pattern so every instance",
                    "Commit once",
                    "Do not push",
                ):
                    self.assertNotIn(copied, text)
        self.assertIn(
            "next review names that commit", self.text("skills/pr-ready/SKILL.md")
        )

    def test_worker_full_suite_prohibition_preserves_no_pr_ci_exception(self):
        worker = self.text("skills/pr-ready/workers/common.md")
        gate = worker.split("- Local gate only:", 1)[1].split(
            "- Use the machine's", 1
        )[0]
        self.assertIn("targeted tests", gate)
        self.assertIn("Never run the full test suite or workspace-wide tests", gate)
        self.assertRegex(gate, r"except.*no-PR-CI")
        self.assertIn("SKILL.md#4-merge-and-cleanup", gate)

    def test_test_discipline_heading_and_references_do_not_collide(self):
        canon = (self.root / "skills/pr-ready/canon.md").read_text()
        self.assertIn("## Test discipline\n", canon)
        self.assertNotIn("## Tests\n", canon)
        self.assertIn("§Test discipline", self.text("AGENTS.md"))
        guards = self.text("skills/pr-ready/references/guards.md")
        self.assertIn("canon.md#test-discipline", guards)
        self.assertNotIn("canon.md#tests", guards)


if __name__ == "__main__":
    unittest.main()
