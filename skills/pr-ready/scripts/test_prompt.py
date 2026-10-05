from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).with_name("prompt.py")
ROOT = SCRIPT.parents[3]


class PromptTest(unittest.TestCase):
    def run_prompt(self, *args, text="", script=SCRIPT, cwd=None):
        return subprocess.run(
            [sys.executable, str(script), *args], input=text, capture_output=True,
            text=True, timeout=5, cwd=cwd,
        )

    def fixture(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        script = root / "skills/pr-ready/scripts/prompt.py"
        script.parent.mkdir(parents=True)
        shutil.copyfile(SCRIPT, script)
        return root, script

    def assert_failure(self, result, message):
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertEqual(len(result.stderr.splitlines()), 1)
        self.assertIn(message, result.stderr)

    def test_every_role_expands_with_all_common_rules(self):
        roles = sorted((ROOT / "skills/pr-ready/prompts/roles").glob("*.md"))
        self.assertEqual(len(roles), 5)
        for role in roles:
            with self.subTest(role=role.name):
                result = self.run_prompt(str(role.relative_to(ROOT)))
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertNotRegex(result.stdout, r"(?m)^@rule ")
                for rule in (ROOT / "skills/pr-ready/prompts/common").glob("*.md"):
                    self.assertEqual(result.stdout.count(rule.read_text()), 1)

    def test_checker_uses_shared_classes_with_cost_exception_once(self):
        role = ROOT / "skills/pr-ready/prompts/roles/checker.md"
        result = self.run_prompt(str(role.relative_to(ROOT)))
        self.assertEqual(result.returncode, 0, result.stderr)
        classes = (ROOT / "skills/pr-ready/prompts/utils/triage-classes.md").read_text()
        self.assertEqual(result.stdout.count(classes), 1)
        self.assertIn("FIX-NOW even if the fix adds an index", result.stdout)
        self.assertIn("Apply the same classes as round 1.", role.read_text())
        for duplicate in ("only FIX-NOW items block", "new mechanism", "nitpicks are dropped"):
            self.assertNotIn(duplicate, role.read_text())

    def test_stdin_preserves_whole_files_titles_and_newlines(self):
        root, script = self.fixture()
        (root / "child.md").write_bytes(b"Title\r\n\r\nBody")
        result = subprocess.run(
            [sys.executable, str(script)], input=b"Before\r\n@rule house-rules:child.md\r\nAfter\n",
            capture_output=True, timeout=5,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, b"Before\r\nTitle\r\n\r\nBodyAfter\n")

    def test_file_argument_is_repo_relative_and_independent_of_cwd(self):
        root, script = self.fixture()
        (root / "entry.md").write_text("Heading\n\n@rule house-rules:child.md\n")
        (root / "child.md").write_text("Body\n")
        result = self.run_prompt("entry.md", script=script, cwd="/")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "Heading\n\nBody\n")

    def test_list_is_depth_first_include_order_with_repeated_visits(self):
        root, script = self.fixture()
        (root / "entry.md").write_text("@rule house-rules:a.md\n@rule house-rules:b.md\n")
        (root / "a.md").write_text("@rule house-rules:b.md\n")
        (root / "b.md").write_text("Body\n")
        result = self.run_prompt("--list", "entry.md", script=script)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "entry.md\na.md\nb.md\nb.md\n")
        stdin = self.run_prompt("--list", text="@rule house-rules:a.md\n", script=script)
        self.assertEqual(stdin.stdout, "a.md\nb.md\n")

    def test_missing_include_fails_without_partial_output(self):
        self.assert_failure(self.run_prompt(text="Before\n@rule house-rules:missing.md\n"),
                            "missing.md")

    def test_empty_include_fails(self):
        self.assert_failure(self.run_prompt(text="@rule house-rules:\n"), "root")

    def test_missing_input_file_fails(self):
        self.assert_failure(self.run_prompt("missing.md"), "missing.md")

    def test_section_reference_fails(self):
        for path in ("AGENTS.md#prime-rules", "missing.md#section"):
            with self.subTest(path=path):
                self.assert_failure(self.run_prompt(text="@rule house-rules:" + path + "\n"),
                                    "section")

    def test_outside_root_fails(self):
        for path in ("../outside.md", "/etc/passwd"):
            with self.subTest(path=path):
                self.assert_failure(self.run_prompt(text="@rule house-rules:" + path + "\n"),
                                    "root")

    def test_symlink_outside_root_fails(self):
        root, script = self.fixture()
        (root / "escape.md").symlink_to(root.parent / "outside.md")
        self.assert_failure(self.run_prompt(text="@rule house-rules:escape.md\n", script=script),
                            "root")

    def test_cycle_fails_without_partial_output(self):
        root, script = self.fixture()
        (root / "a.md").write_text("Before\n@rule house-rules:b.md\n")
        (root / "b.md").write_text("@rule house-rules:a.md\n")
        self.assert_failure(self.run_prompt("a.md", script=script), "cycle")
        self.assert_failure(self.run_prompt("--list", "a.md", script=script), "cycle")

    def test_only_exact_include_lines_expand(self):
        original = " @rule house-rules:missing.md\nText @rule house-rules:missing.md\n"
        result = self.run_prompt(text=original)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, original)

    def test_same_input_is_byte_identical(self):
        text = "@rule house-rules:AGENTS.md\n"
        first = self.run_prompt(text=text)
        second = self.run_prompt(text=text)
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(first.stdout, second.stdout)

    def test_common_and_utils_are_leaf_files(self):
        for folder in ("common", "utils"):
            for path in (ROOT / "skills/pr-ready/prompts" / folder).glob("*.md"):
                self.assertNotRegex(path.read_text(), r"(?m)^@rule ")


class RuleOwnershipTest(unittest.TestCase):
    root = SCRIPT.parents[3]

    def text(self, path):
        return " ".join((self.root / path).read_text().split())

    def test_specialist_dispatch_belongs_to_optional_lenses(self):
        rules = self.text("skills/pr-ready/SKILL.md")
        self.assertIn("references/review-lenses.md#optional-lenses", rules)
        self.assertNotRegex(
            rules, r"spawns specialist reviewers|operator asks or a finding"
        )
        lenses = self.text("skills/pr-ready/references/review-lenses.md")
        self.assertIn("## Optional lenses", lenses)
        self.assertIn(
            "spawns specialists when the operator asks or a finding warrants one", lenses
        )

    def test_fix_round_threshold_belongs_to_pr_ready(self):
        lenses = self.text("skills/pr-ready/references/review-lenses.md")
        self.assertIn("../SKILL.md#3-review-rounds", lenses)
        self.assertNotRegex(lenses, r"two fix rounds|after \d+ fix rounds")
        self.assertIn("After two fix rounds", self.text("skills/pr-ready/SKILL.md"))

    def test_spec_challenges_belong_to_shared_review_bar(self):
        lenses = self.text("skills/pr-ready/references/review-lenses.md")
        self.assertIn("../prompts/utils/review-bar.md", lenses)
        for copied in (
            "Every reviewer challenges the spec",
            "infeasible or unmeasurable requirements",
            "issue blocks only",
            "A settled operator decision is not reopened",
        ):
            with self.subTest(copied=copied):
                self.assertNotIn(copied, lenses)
        self.assertIn("The lead triages each one", lenses)
        self.assertIn("a clarification is proposed in the same PR", lenses)
        self.assertIn("Requirement removals and spec/code drift", lenses)
        common = self.text("skills/pr-ready/prompts/utils/review-bar.md")
        self.assertIn("Challenge the spec as well", common)
        self.assertIn("a spec issue blocks only", common)

    def test_work_sizing_belongs_to_prime_rule_13(self):
        for path, target in (
            ("skills/decision-brief/SKILL.md", "../../AGENTS.md#prime-rules"),
            ("skills/operator-writing/SKILL.md", "../../AGENTS.md#prime-rules"),
            (
                "skills/operator-writing/references/github-text.md",
                "../../../AGENTS.md#prime-rules",
            ),
        ):
            with self.subTest(path=path):
                text = self.text(path)
                self.assertIn(target, text)
                self.assertIn("prime rule 13", text)
                self.assertNotRegex(
                    text, r"[Tt]ime estimates|agent-days|files and lines touched"
                )
        self.assertIn("No time estimates for agent work", self.text("AGENTS.md"))
        self.assertIn("No filler", self.text("skills/operator-writing/SKILL.md"))
        github = self.text("skills/operator-writing/references/github-text.md")
        self.assertIn('No ceremony. A "found by" line is allowed', github)

    def test_audit_filing_uses_guard_upkeep_policy(self):
        guards = self.text("skills/pr-ready/references/guards.md")
        upkeep, audit = guards.split("## Daily whole-system audit", 1)
        self.assertIn("There are no fixed caps", upkeep)
        self.assertIn("severity and deduplication", upkeep)
        self.assertIn("(#guard-upkeep)", audit)
        self.assertNotRegex(audit, r"by severity|daily cap|fixed caps")
        self.assertIn(
            "deduplicates findings by fingerprint against tracked findings", audit
        )
        self.assertIn(
            "Comment on a known finding only when materially new evidence changes it", audit
        )

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
        common = self.text("skills/pr-ready/prompts/utils/review-bar.md")
        bar = self.text("skills/pr-ready/prompts/utils/cost-and-design.md")
        remainder = self.text("skills/pr-ready/prompts/utils/review-report.md")
        self.assertRegex(bar, r"design finding.*stops for a lead decision")
        self.assertIn("never becomes a follow-up or starts another fix round", bar)
        self.assertNotRegex(remainder, r"design finding (?:stays|stops)")
        self.assertIn("§Review bar", common)
        for path in (
            "skills/pr-ready/prompts/lenses/design.md",
            "skills/pr-ready/SKILL.md",
            "skills/pr-ready/references/review-lenses.md",
            "skills/design-flow/SKILL.md",
        ):
            with self.subTest(path=path):
                text = self.text(path)
                self.assertNotRegex(text, r"design finding stops|design findings cannot")
                self.assertIn("review-bar.md", text)

    def test_feature_implementation_uses_worker_choice_boundaries(self):
        rules = self.text("skills/design-flow/SKILL.md")
        implementation = rules.split("## 5. Implement", 1)[1].split(
            "## Design changes", 1
        )[0]
        self.assertIn("design-spec reviewer checks its spec sections", implementation)
        self.assertIn("prompts/roles/implementer.md", implementation)
        self.assertNotIn("choose the simplest option", implementation)
        self.assertNotIn("Stop and report options", implementation)
        self.assertNotIn("never settle them by editing the spec", implementation)

    def test_test_logging_and_pruning_belong_to_guard_upkeep(self):
        canon = self.text("skills/pr-ready/prompts/common/test-discipline.md")
        self.assertIn("references/guards.md#guard-upkeep", canon)
        self.assertNotIn("log runtime", canon)
        self.assertNotRegex(canon, r"prune or bound slow")
        self.assertIn("Scale tests move, never vanish", canon)
        guards = self.text("skills/pr-ready/references/guards.md")
        self.assertIn("Every guard and every test logs", guards)
        self.assertIn("pruning or narrowing guards and tests", guards)

    def test_lane_cache_policy_references_worker_owner(self):
        lanes = self.text("skills/agent-lanes/SKILL.md")
        self.assertIn("prompts/roles/implementer.md", lanes)
        self.assertNotRegex(lanes, r"target directory must never bypass")
        self.assertIn("Build output lives inside the lane's own worktree", lanes)
        self.assertIn(".tmp/cargo-target/<lane>", lanes)
        worker = self.text("skills/pr-ready/prompts/roles/implementer.md")
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
                self.assertRegex(text, r"worker pack|prompts/roles/implementer\.md")
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
        worker = self.text("skills/pr-ready/prompts/roles/implementer.md")
        gate = worker.split("- Local gate only:", 1)[1].split(
            "- Use the machine's", 1
        )[0]
        self.assertIn("targeted tests", gate)
        self.assertIn("Never run the full test suite or workspace-wide tests", gate)
        self.assertRegex(gate, r"except.*no-PR-CI")
        self.assertIn("SKILL.md#4-merge-and-cleanup", gate)

    def test_test_discipline_heading_and_references_do_not_collide(self):
        canon = (self.root / "skills/pr-ready/prompts/common/test-discipline.md").read_text()
        self.assertIn("## Test discipline\n", canon)
        self.assertNotIn("## Tests\n", canon)
        self.assertIn("§Test discipline", self.text("AGENTS.md"))
        guards = self.text("skills/pr-ready/references/guards.md")
        self.assertIn("prompts/common/test-discipline.md", guards)
        self.assertNotIn("prompts/common/test-discipline.md#tests", guards)


if __name__ == "__main__":
    unittest.main()
