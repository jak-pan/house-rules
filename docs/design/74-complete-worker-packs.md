Status: proposed (design only, awaiting operator approval)

# Complete worker role packs

Design for [#74](https://github.com/jak-pan/house-rules/issues/74). Evidence is from main at
9e18159 unless a line says otherwise.

## 1. Result

Each of the five worker roles (implementer, fixer, reviewer, triager, checker) compiles into
one prompt that contains every rule it cites and says that it is the worker's only House Rules
source. Workers stop reading unpinned House Rules files to fill gaps, and no role asks the
worker to find the repository's rule files; the dispatcher supplies them. The checker stops
calling itself the triager. Five small files are added under `prompts/util/`, nine prompt files
change, and new tests keep the packs complete and the copied rule text identical to its
source.

## 2. Terms

- **Role pack:** the output of `python3 skills/pr-ready/scripts/prompt.py prompts/roles/<role>.md`,
  which expands every `@rule house-rules:<path>` line into the whole file it names.
- **Fragment:** a whole file under `prompts/util/` or `prompts/skills/` that roles include with
  `@rule`. Fragments never include other files
  ([README](../../prompts/README.md#L14)).
- **Citation:** text in a pack that sends the worker to another file or section: a Markdown
  link, a `§` section reference, a `rules/*.md` path, or "skill `name`".
- **Open citation:** a citation whose target is not part of the same pack.
- **Staged paths:** `prompts/` and `skills/pr-ready/`. Warden stages only `prompts/` and `skills/pr-ready/`; staging `rules/` is a separate Warden change.
- **Stay-off line:** the sentence that tells a worker not to load House Rules or skills.
- **"Repository rules" part** and **task part:** two parts of a pack that
  [#77](https://github.com/jak-pan/house-rules/issues/77)'s one-step assembly writes. The
  "Repository rules" part holds the target repository's own rule file, or the single line
  "Repository rules: this repository has no rules of its own." The task part holds the task
  file, into which the dispatcher writes the work item's Decisions and Pre-flight sections.

## 3. Current behavior

### Open citations per role

`FACT` I compiled each role with `prompt.py </dev/null`, listed its files with `--list`, and
scanned those files for links outside the list and for `§`, `rules/*.md`, "skill `…`" and
`pr-ready` pointers. All five roles compile (exit 0). The open citations are:

- **Implementer** (8,128 bytes):
  - [implementer.md:22](../../prompts/roles/implementer.md#L22) "Merge eligibility follows pr-ready §4."
  - [implementer.md:38](../../prompts/roles/implementer.md#L38) "following House Rules rules/delivery.md §Git".
  - [code-canon.md:13](../../prompts/skills/code-canon.md#L13) "(design-canon §Decisions)".
- **Fixer** (8,649 bytes): [fixer.md:1](../../prompts/roles/fixer.md#L1) "follow the commit
  cadence in House Rules rules/delivery.md §Git", plus the implementer's three, because the fixer
  includes the implementer.
- **Reviewer** (10,572 bytes):
  - [cost-and-design.md:10](../../prompts/util/cost-and-design.md#L10) links `triage-classes.md`,
    which the reviewer does not include. That file holds the cost-defect definition the
    reviewer must apply ([triage-classes.md:11](../../prompts/util/triage-classes.md#L11)).
  - [code-canon.md:13](../../prompts/skills/code-canon.md#L13).
- **Triager** (15,248 bytes):
  - [code-canon.md:13](../../prompts/skills/code-canon.md#L13).
  - [issue-form.md:5](../../prompts/util/issue-form.md#L5) "one priority label (`P0`–`P3`,
    skill `work-tracking`)". The meaning of each priority is in
    [design-flow §2](../../skills/design-flow/SKILL.md#L57), which no pack includes.
  - [issue-form.md:44](../../prompts/util/issue-form.md#L44) "Work-item sections (…; skill
    `work-tracking`)".
- **Checker** (13,499 bytes): the same three as the triager.

`FACT` No role includes [rules/writing.md](../../rules/writing.md), and
[core.md:47](../../rules/core.md#L47) says that file governs all text (checked by
`test_general_writing_rules_are_always_loaded`).

### Stay-off line and checker name

- `FACT` The reviewer ([reviewer.md:1](../../prompts/roles/reviewer.md#L1)) and implementer
  ([implementer.md:1](../../prompts/roles/implementer.md#L1)) have a stay-off line. The triager
  and checker have none.
- `FACT` In the 2026-10-07 load test, the lane triager read the unpinned House Rules index, the
  operator-writing and pr-ready skills, and all four rule files, on top of its compiled prompt
  (raw tool log of the lane run). The three lane reviewers read nothing outside their prompt.
- `FACT` [checker.md:1](../../prompts/roles/checker.md#L1) starts "You are the TRIAGER doing
  the check round".
- `FACT` A managed repository's `AGENTS.md` says "Read House Rules `AGENTS.md` first and follow
  it" ([STRUCTURE.md:52](../../STRUCTURE.md#L52)). The implementer tells the worker to follow the
  repository's `AGENTS.md` ([implementer.md:2](../../prompts/roles/implementer.md#L2)). In a
  managed repository the two instructions conflict.
- The STRUCTURE.md managed-repository loader template does not change in this design; #77
  detects it by exact match.
- `FACT` The operator's lane launcher now starts workers in a separate tool home without the
  House Rules block, project instruction files or shared skills. That closes the global loading
  path, but not the repository loader path above.
- `FACT` In the 2026-10-07 re-test with that isolated home, the three lane reviewers read nothing
  outside their compiled prompt, but the triager still loaded House Rules (raw command log of the
  re-test, reported in [a comment on #74](https://github.com/jak-pan/house-rules/issues/74)).
  The path was:
  1. The triager role tells the worker to read "the repository's rule files supplied or named by
     the dispatcher" ([triager.md:2](../../prompts/roles/triager.md#L2)). The dispatcher supplied
     none.
  2. The triager searched the worktree for `AGENTS.md` and rule-like files, and checked each
     parent directory for an `AGENTS.md`.
  3. It read the target repository's `AGENTS.md`. Its loader line says to read House Rules'
     `AGENTS.md` and `STRUCTURE.md` and to "Read and follow them first".
  4. It then read the House Rules index, `STRUCTURE.md`, all four rule files, and the pr-ready
     and operator-writing skills from the unpinned operator checkout.
- `ASSESSMENT` Two parts of this design are therefore load-bearing, not cosmetic. The triager
  and checker need the stay-off line. And no role may ask the worker to find rule files itself,
  because any search for rule files finds the repository loader, which restarts the House Rules
  chain. The implementer has the same instruction
  ([implementer.md:2–4](../../prompts/roles/implementer.md#L2)).

### The staged-paths guard test

`FACT` `test_role_prompts_include_only_files_warden_stages`, added by
[#61](https://github.com/jak-pan/house-rules/pull/61)
([test_prompt.py:260](../../skills/pr-ready/scripts/test_prompt.py#L260)) fails when any role
lists a file outside `prompts/` or `skills/pr-ready/`. It keeps every role buildable from what
Warden stages.

## 4. Design

Two rules decide every change below.

1. **DECISION (proposed):** a role pack has no open citations. Each citation either points to a
   file in the same pack or is removed because the worker does not need it.
2. **DECISION (proposed):** rule text that lives outside the staged paths reaches a pack as a
   verbatim copy under `prompts/util/`. A parity test fails when a copy and its source differ.
   Question 1 asks the operator to confirm this over moving the text.
3. **DECISION (proposed):** no role asks the worker to search for, find or open the repository's
   rule files. The role text names the two pack parts that hold them: the repository's rules
   are in the "Repository rules" part, and the work item's Decisions and Pre-flight sections are
   in the task part. #77's assembly writes both parts.
   - A "Repository rules" part that says the repository has no rules of its own is a complete
     answer. The worker reports nothing about it.
   - A pack with no "Repository rules" part at all (built without a target repository) makes
     the worker say so once and continue.
   - The stay-off line forbids following any House Rules pointer the worker still meets, such as
     an `AGENTS.md` that holds real rules and also says to read House Rules first.

### 4.1 New fragments

Five new files in [prompts/util/](../../prompts/util/). Copies keep their source's line breaks.
Headings are labels, not rule text; the parity test ignores them.

**`worker-git.md`**: copy of [delivery.md §Git](../../rules/delivery.md#L44), lines 46, 47,
48, 49, 51, 57, 58, 59 and 71.

```markdown
## Worker Git

- Stage explicit files.
- Never use `git add -A`.
- Never amend or force-push unless told.
- Default to frequent commits at logical-piece completion.
- Use repository commit tooling and message conventions.
- Keep each commit one logical chunk.
- Never mix unrelated fixes, docs, refactors, or in-flight prototypes in one commit.
- Keep one topic per commit unless one larger task requires them together.
- Commit documentation with the code it describes.
```

`ASSESSMENT` The other §Git lines are lead work or conflict with the worker's
[no-external-writes rule](../../prompts/util/external-writes.md):

- Line 50 joins "Require green gates" with "update tracker state", and tracker updates are external
  writes. The implementer's local-gate bullet already sets the worker's gate.
- Line 52 relies on the undefined term "bible". The implementer already follows the
  repository's own rules, and repository rules override House Rules.
- Lines 53–56 and 66 are about pushing. External writes forbid every push.
- Lines 60–65 and 67–70 are delivery authority and external repositories, which only the lead has.

**`writing-baseline.md`**: copy of [writing.md](../../rules/writing.md) lines 3–4
(introduction), 8–10 (§Communication rules) and 14–34 (§Language).

```markdown
## Writing

The reader must understand the text without any other document. They should know what
happened, why it matters and what to do, in that order.

- Support claims with evidence.
- Distinguish observed causes from hypotheses.
- Distinguish completed fixes from plans and deployments awaiting verification.
- One fact per sentence. Prefer short sentences; split one that carries more than one fact.
  Length is never a reason to drop content.
- Active voice, simple tense. Name who does what.
- One term per concept. Define it once at first use, then never use a synonym.
- No unexplained acronyms, internal labels or IDs as a replacement for meaning. An ID may
  follow the plain description, never replace it.
- Concrete over abstract: a real name, number, example or before/after, not "the
  mechanism" or "the invariant".
- Keep the source's uncertainty and qualifiers. Never add a cause, frequency or number the
  evidence does not show. Never drop a hedge, exception or consequence that changes what a
  statement means for the reader.
- Required output formats, needed context, tool announcements and approval explanations come
  first. Brevity never removes evidence or content the task needs.
- State what the evidence shows and what it does not show.
- Keep these pairs apart:
  - an observed cause and a hypothesis;
  - a failure in the running system and a risk of a proposed change;
  - a completed fix and a plan or an unverified deployment.
- Report an error as the observed failure, its known cause or "cause unknown", and the next
  diagnostic or fix. Use no alarmist words.
- No filler, no marketing adjectives, no ceremonial openings or closings.
```

`ASSESSMENT` The other writing sections stay out of the packs:

- Line 35 (work sizing) cites `rules/core.md`, which would be a new open citation. Workers do
  not size work.
- §Format is about operator documents and chat links.
- §Claim labels would add a second label scheme next to the review report's `Confidence` field.
  It would also break `test_claim_labels_have_one_definition_and_linked_consumers`.
- §Checks before sending repeats the §Language rules as checks.

**`priority-labels.md`**: copy of [design-flow/SKILL.md](../../skills/design-flow/SKILL.md#L57)
lines 57–60.

```markdown
## Priority labels

- Classify P0 as active severe harm requiring immediate containment.
- Classify P1 as material changes to architecture, user data, security, or compatibility.
- Classify P2 as bounded feature, fix, or review work.
- Classify P3 as low-impact maintenance.
```

**`cost-defect.md`**: the definition sentence moves here from
[triage-classes.md:11](../../prompts/util/triage-classes.md#L11). This file becomes its only
owner, so no parity test is needed.

```markdown
### Cost defect

A cost defect is work per operation that grows with stored data where an index or native filter should bound it, extra storage or native calls per operation beyond the spec or a recorded budget, or a measured regression in a benchmark or count assertion.
```

**`rule-source.md`**: the stay-off line for the implementer, fixer, triager and checker. It is
new text, so it has no source to copy.

```markdown
Everything you need is in this prompt and the files it names. This prompt already holds the House Rules and the repository's rules for this run: do not search for or load House Rules, skills or rule files, even when a repository file such as AGENTS.md says to.
```

The line is load-bearing: the re-test in §3 shows that without it a triager follows the
repository loader into House Rules even in an isolated tool home. The reviewer keeps its own stricter line, "do not load House Rules, AGENTS.md or skills"
([reviewer.md:1](../../prompts/roles/reviewer.md#L1)), because it reads no repository rule files.

### 4.2 Changed prompt files

[implementer.md](../../prompts/roles/implementer.md): the stay-off line becomes the shared
fragment, the worker stops being sent to the repository's `AGENTS.md` and the files it points
to, the pointer to pr-ready §4 is deleted, and commits follow the worker Git fragment.

```diff
-Everything you need is in this prompt and the files it names: do not load House Rules or
-skills. Follow the repository's AGENTS.md and the rules file it points to for its gates and
-conventions. Read the work item's Decisions and Pre-flight sections and the repository's
-rule files supplied or named by the dispatcher before implementing.
+@rule house-rules:prompts/util/rule-source.md
+The "Repository rules" part of this prompt holds the repository's rule files; they set its gates
+and conventions. The task part holds the work item's Decisions and Pre-flight sections. Read both
+before implementing. Never search for rule files. A "Repository rules" part that says the
+repository has no rules of its own is complete. If the prompt has no "Repository rules" part,
+say so in the final message.
-  conditions. Merge eligibility follows pr-ready §4.
+  conditions.
 …
-- Commit at logical-piece completion following House Rules rules/delivery.md §Git, with clear messages in
-  the repository's convention plus any trailer the task gives. External-write authority
+- Commit following [Worker Git](../util/worker-git.md), plus any trailer the task gives. External-write authority
 …
 @rule house-rules:prompts/util/external-writes.md
+@rule house-rules:prompts/util/worker-git.md
+@rule house-rules:prompts/util/writing-baseline.md
 @rule house-rules:prompts/skills/code-canon.md
```

`ASSESSMENT` The deleted sentence "Merge eligibility follows pr-ready §4." points in a circle:
[pr-ready §4](../../skills/pr-ready/SKILL.md#L153) says "The no-PR-CI exception follows the
worker pack". A worker never merges, because the lead does all external writes. Approving this
design records the decision that
[triage-classes.md:8](../../prompts/util/triage-classes.md#L8) requires before requirement text
is deleted.

[fixer.md](../../prompts/roles/fixer.md):

```diff
-… finish the fix, and follow the commit cadence in House Rules rules/delivery.md §Git.
+… finish the fix, and follow the commit cadence in [Worker Git](../util/worker-git.md).
```

[reviewer.md](../../prompts/roles/reviewer.md):

```diff
 @rule house-rules:prompts/util/cost-and-design.md
+@rule house-rules:prompts/util/cost-defect.md
 @rule house-rules:prompts/util/review-report.md
 @rule house-rules:prompts/util/external-writes.md
+@rule house-rules:prompts/util/writing-baseline.md
```

[triager.md](../../prompts/roles/triager.md) and [checker.md](../../prompts/roles/checker.md)
get the same four includes. The checker also gets a new name.

```diff
-You are the TRIAGER doing the check round of a code review (current checkout). …
+You are the CHECKER doing the check round of a code review (current checkout). …
+@rule house-rules:prompts/util/rule-source.md
 …
 @rule house-rules:prompts/util/cost-and-design.md
+@rule house-rules:prompts/util/cost-defect.md
 @rule house-rules:prompts/util/external-writes.md
+@rule house-rules:prompts/util/writing-baseline.md
 …
 @rule house-rules:prompts/util/issue-form.md
+@rule house-rules:prompts/util/priority-labels.md
```

In both roles the stay-off include goes on line 2, directly after the identity line.

The triager's line 2 stops asking it to find rule files
([triager.md:2](../../prompts/roles/triager.md#L2), last sentence):

```diff
-Read the work item's Decisions and Pre-flight sections and the repository's rule files supplied or named by the dispatcher before triaging.
+Read the work item's Decisions and Pre-flight sections in the task part and the repository's rule files in the "Repository rules" part of this prompt before triaging. Never search for rule files. A "Repository rules" part that says the repository has no rules of its own is complete. If the prompt has no "Repository rules" part, say so in one line.
```

**DECISION (proposed):** the checker's new self-name is "CHECKER". It matches the file name,
the launcher's `ROLE=checker`, and the upper-case style of "TRIAGER". `FACT` No test, pr-ready file or
lane script matches the string "TRIAGER" in checker output (searched with `grep`).

[cost-and-design.md](../../prompts/util/cost-and-design.md) lines 8–11 point to the new owner
of the definition and drop the open link:

```diff
 … Cost defects and design findings
-cannot be reclassified to escape review reassessment. Cost-defect classification and the
-cost-defect definition follow [Triage classes](triage-classes.md); settled-decision
-disagreements follow [Code canon](../skills/code-canon.md).
+cannot be reclassified to escape review reassessment. A cost defect is defined in [Cost defect](cost-defect.md).
+Settled-decision disagreements follow [Code canon](../skills/code-canon.md).
```

`ASSESSMENT` The reviewer does not classify findings (the lead adjudicates,
[review-bar.md:28](../../prompts/util/review-bar.md#L28)). The triager and checker get
classification from `triage-classes.md`, which they include.

[triage-classes.md](../../prompts/util/triage-classes.md): line 11 loses the definition,
line 4 stops naming a role because the checker includes it too, and line 5 points to the rule
files in the prompt. Line 5 is the checker's only instruction about rule files.

```diff
-… If no list is supplied, the triager says so in one line and files as usual.
+… If no list is supplied, say so in one line and file as usual.
-- Before calling a contract "unresolved", check the work item's Decisions and Pre-flight sections, the repository's rule files and the design; apply …
+- Before calling a contract "unresolved", check the work item's Decisions and Pre-flight sections (task part) and the repository's rule files ("Repository rules" part), and the design; apply …
 …
-… a fix whose lines are reasoned for and necessary is fine. A cost defect is work per operation that grows with stored data where an index or native filter should bound it, extra storage or native calls per operation beyond the spec or a recorded budget, or a measured regression in a benchmark or count assertion. With a concrete operation and its count or measurement, it is FIX-NOW even if the fix adds an index, a native filter or a test.
+… a fix whose lines are reasoned for and necessary is fine. With a concrete operation and its count or measurement, a cost defect ([Cost defect](cost-defect.md)) is FIX-NOW even if the fix adds an index, a native filter or a test.
```

[issue-form.md](../../prompts/util/issue-form.md): this file is also used by interactive
sessions through [github-text.md](../../skills/operator-writing/references/github-text.md#L31).
The relative link works there too.

```diff
-Labels: one priority label (`P0`–`P3`, skill `work-tracking`) and one type label (`bug`,
+Labels: one priority label (`P0`–`P3`, [Priority labels](priority-labels.md)) and one type label (`bug`,
 …
-- Work-item sections (Scope, Decisions, Lane, Design; skill `work-tracking`) follow
+- Work-item sections (Scope, Decisions, Lane, Design) follow
```

`ASSESSMENT` The work-tracking pointer on line 44 serves only a lead who adds work-item
sections. That lead loads work-tracking from the index trigger anyway.

[code-canon.md](../../prompts/skills/code-canon.md) line 13 drops the source note. The sentence
already states the rule the worker needs.

```diff
-…; product schema migrations may be a feature (design-canon §Decisions).
+…; product schema migrations may be a feature.
```

[prompts/README.md](../../prompts/README.md) gets one paragraph after line 16:

```markdown
A role cites only files it includes. Rule text whose owner Warden cannot stage is copied
verbatim into `util/`; `test_prompt.py` lists each copy with its source and fails when
they differ.
```

`CHANGELOG-RULES.md` gets one provenance note: the 2026-10-07 load test, in which the lane
triager loaded unpinned rules.

### 4.3 Which role includes which new fragment

| Fragment | Implementer | Fixer | Reviewer | Triager | Checker |
|---|---|---|---|---|---|
| rule-source | yes | via implementer | no | yes | yes |
| worker-git | yes | via implementer | no | no | no |
| writing-baseline | yes | via implementer | yes | yes | yes |
| cost-defect | no | no | yes | yes | yes |
| priority-labels | no | no | no | yes | yes |

`FACT` I simulated the changes in memory with the same expansion rule as `prompt.py`: no role
includes any file twice, and the open-citation scan finds nothing.

### 4.4 Tests in `skills/pr-ready/scripts/test_prompt.py`

**New: no open citations.** The test covers all five roles, and each lens combined with the
reviewer.

```python
CITATION = re.compile(r"§|\brules/[\w-]+\.md|skill `|SKILL\.md")
LINK = re.compile(r"\]\(([^)\s#]+)(?:#[^)]*)?\)")

def test_compiled_roles_cite_only_files_they_include(self):
    for role in sorted((ROOT / "prompts/roles").glob("*.md")):
        with self.subTest(role=role.name):
            listed = PromptTest().run_prompt("--list", f"prompts/roles/{role.name}").stdout.split()
            for path in set(listed):
                text = (ROOT / path).read_text()
                self.assertNotRegex(text, CITATION, path)
                for target in LINK.findall(text):
                    resolved = os.path.normpath(os.path.join(os.path.dirname(path), target))
                    self.assertIn(resolved, listed, f"{path} -> {target}")
```

**New: copies match their source.** The table below is the only record of where each copy comes
from. The copies themselves hold no source note, because a note would be an open citation.

```python
# Rule text whose owner file is outside the paths Warden stages.
COPIES = {
    "prompts/util/worker-git.md": "rules/delivery.md",
    "prompts/util/writing-baseline.md": "rules/writing.md",
    "prompts/util/priority-labels.md": "skills/design-flow/SKILL.md",
}

def blocks(text):
    """Paragraphs and top-level list items, whitespace-normalized; headings skipped."""
    found, current = [], []
    for line in text.splitlines() + [""]:
        if not line.strip() or line.startswith(("#", "- ")):
            if current:
                found.append(" ".join(" ".join(current).split()))
            current = [line] if line.startswith("- ") else []
        else:
            current.append(line)
    return found

def test_copied_rule_text_matches_its_source(self):
    for copy, source in COPIES.items():
        with self.subTest(copy=copy):
            owner = " ".join((ROOT / source).read_text().split())
            for block in blocks((ROOT / copy).read_text()):
                self.assertIn(block, owner)
```

This keeps the copy and the source identical in both directions:

- A changed source sentence leaves the old block without a match.
- An edited copy no longer matches its source.

A rule change is therefore made in the source and copied in the same PR. The test does not
detect a new source sentence that workers would also need; the PR that adds one decides
whether to copy it.

**New, small:**

- The `rule-source.md` text appears exactly once in the compiled implementer, fixer, triager and
  checker. The compiled reviewer still contains "do not load House Rules, AGENTS.md or skills".
- `writing-baseline.md` appears exactly once in every compiled role.
- `worker-git.md` appears exactly once in the implementer and fixer, and in no other role.
- `checker.md` starts with "You are the CHECKER" and does not contain "TRIAGER".
- No compiled role contains "supplied or named" or "the rules file it points to". The compiled
  implementer, fixer, triager and checker each name the "Repository rules" part. The existing
  `test_workers_and_triager_read_work_item_and_repo_rules` keeps passing, because the new
  sentences still say "work item's Decisions and Pre-flight" and "repository's rule files".

**Changed:**

- `test_worker_git_references_name_house_rules` is replaced by the worker-git test above.
- `test_worker_full_suite_prohibition_preserves_no_pr_ci_exception` asserts that the gate text
  no longer contains `pr-ready`.
- `test_triage_uses_live_cost_definition_and_fix_exception_once`: the definition sentence has
  the one owner `cost-defect.md`, and the FIX-NOW sentence uses its new wording.
- `test_triager_reconciles_before_filing_with_one_prompt_owner` uses the new "say so in one line"
  sentence.

**Kept unchanged:** the staged-paths guard test from [#61](https://github.com/jak-pan/house-rules/pull/61), `test_role_prompts_include_only_files_warden_stages`.
Every new file is under `prompts/util/`, so the test passes without change, and it keeps
enforcing the staged paths. It widens only when Warden stages `rules/`, which is a separate Warden change;
acceptance criteria state.

## 5. Alternatives considered

- **Include `rules/delivery.md` and `rules/writing.md` whole once Warden stages `rules/`.**
  Rejected: it waits on a separate Warden change, and it adds about 13 KB to every pack. It would also give
  workers the lead's push and merge rules (delivery.md lines 53–66), which contradict their
  no-external-writes rule.
- **Move the copied text into `prompts/util/` and have `rules/` link to it.** One owner, no
  copy. Rejected for now: it changes `rules/delivery.md` and `rules/writing.md`, which
  [#73](https://github.com/jak-pan/house-rules/issues/73) is restructuring. It would also make
  the always-loaded writing rules depend on a file outside `rules/`. Question 1 lets the
  operator choose it anyway.
- **Section includes (`@rule house-rules:rules/delivery.md#git`).** Rejected: the compiler
  rejects section references on purpose (`test_section_reference_fails`), and Warden cannot
  stage `rules/` yet.
- **Leave citations open and tell workers to read the cited files.** Rejected: that is the
  current failure. The worker reads unpinned files, or files Warden does not stage.
- **Stay-off line written into each role instead of one fragment.** Rejected: four copies of
  one sentence. [external-writes.md](../../prompts/util/external-writes.md) already sets the
  one-line shared-fragment pattern.

## 6. Size

- New files: five fragments in `prompts/util/`, about 50 lines in total.
- Changed files: five roles, `cost-and-design.md`, `triage-classes.md`, `issue-form.md`,
  `code-canon.md`, `prompts/README.md`, `CHANGELOG-RULES.md` and `test_prompt.py`. The prompt
  files change about 30 lines. The test file gains about 80 lines and changes about 10.
- Compiled pack sizes, before (`FACT`, measured) and after (`ESTIMATE`, from the in-memory
  simulation; tokens with o200k):
  - Implementer: 8,128 B / 1,717 tokens → 10,226 B / 2,172 tokens.
  - Fixer: 8,649 B / 1,824 tokens → 10,747 B / 2,282 tokens.
  - Reviewer: 10,572 B / 2,285 tokens → 12,447 B / 2,683 tokens.
  - Triager: 15,248 B / 3,365 tokens → 17,364 B / 3,824 tokens.
  - Checker: 13,499 B / 2,980 tokens → 15,615 B / 3,439 tokens.
- The writing baseline accounts for most of the growth: 1,673 B and 363 tokens per role.
- The revised rule-file sentences and the longer stay-off line add about 300 B more to the
  implementer, fixer, triager and checker (`ESTIMATE`, not in the figures above).

## 7. Verification

**Text tests:** the full `test_prompt.py` suite passes, including the tests in §4.4.

**Canary lane run** (the issue's acceptance criterion):

- Setup:
  - Pin the lanes to a commit that contains both this change and #77, with the lane runner
    already passing `--target` (see §8). This canary runs in the same round as #77's.
  - Append a unique canary code to every file of the unpinned House Rules checkout: the index,
    the four rule files and every skill. Do not change `prompts/`.
  - Run in a test repository whose `AGENTS.md` holds real rules and also says to read House
    Rules first (#77's case-2 fixture). #77 includes that file in the "Repository rules" part,
    so the pack itself tells the worker to read House Rules. This exercises the "even when a
    repository file such as AGENTS.md says to" clause.
  - Run the triager and checker a second time in a test repository whose `AGENTS.md` is the
    unchanged STRUCTURE.md loader template. #77 never includes a loader, so the pack gets the
    line "Repository rules: this repository has no rules of its own."
- Run one implementer, three reviewers, the triager, one fixer and the checker on a small
  seeded change.
- Pass:
  - For every role, the tool logs show no read of any unpinned House Rules path or skill
    file. The logs are the evidence; self-reports are not.
  - Each output keeps its contract: a `VERDICT:` first line for the reviewer, triager and
    checker, and the final-message sections for the implementer and fixer.
  - The checker's output never calls the checker "triager".
  - In the loader-template run, the triager and checker logs show no search for rule files and
    no read of the repository's `AGENTS.md`, and their output does not report missing rules.
  - In one extra triager run from a pack built with `--no-target`, the log shows no search for
    rule files, and the output says once that the prompt has no "Repository rules" part.
- Fail: any such read or search, in any role.

**Warden:** after Warden moves to a House Rules commit that contains this change, one Warden
review runs every role without a missing-file error.

## 8. Rollout and pins

The merge order for the five designs is #74 → #77 → #73 → #76 → #75. This change merges first.

1. Merge the implementation PR. Do not move the lane House Rules pin at this merge.
2. The lane pin moves once, after #77 merges, to a commit that contains both changes, together
   with the lane runner switch to `--target`. #77's rollout owns that step, and its step zero
   (a short House Rules `.agents/rules.md`) comes before any lane targets a House Rules
   worktree. The §7 canary runs then, in the same round as #77's.
3. `ASSESSMENT` Between this merge and #77's merge, a dispatcher that compiles roles from main
   gets role text that names a "Repository rules" part no tool writes yet. The worker then says
   once that the part is missing and does not search. No lane is affected, because the lane pin
   has not moved.
4. Warden uses the new packs once it moves to a House Rules commit that contains them. Until
   then it keeps the old packs. Nothing breaks, because the guard test keeps every include
   inside the staged paths.
5. The operator checkout needs only a pull. `scripts/sync.py` installs no prompts.
6. When Warden stages `rules/` (a separate Warden change), the guard test widens to `rules/`.
   Whether the copies then go away depends on Question 1 and on #73's split of `rules/`. The
   implementation PR files that follow-up as a House Rules issue.

## 9. Interfaces with the other designs

- **[#73](https://github.com/jak-pan/house-rules/issues/73) (foundation).** `ASSUMPTION` #73 may move or reword the sentences these copies come
  from. The parity test then fails, and the PR that moves them updates the `COPIES` table and
  the copy in the same change. If #73 splits delivery.md line 50 into "Require green gates" and
  "Update tracker state", `worker-git.md` can take the first sentence. If #73 defines its own
  everyday-writing baseline, `writing-baseline.md` should equal it. Packs do not include #73's
  foundation files. `ASSUMPTION` #73's foundation adds one sentence: a compiled prompt that
  states it is the only rule source overrides the foundation's loading and re-read rules for
  that run. `rule-source.md` and the reviewer's line are such statements.
- **[#75](https://github.com/jak-pan/house-rules/issues/75) (subagent profiles).** `ASSUMPTION` Specialist packs are these role packs, plus
  the parts #77 assembles; they carry no foundation. `rule-source.md` is the statement that the
  pack is the only rule source. Question 1 below covers specialist packs too. #77 decides where
  the pack's revision header goes.
- **[#76](https://github.com/jak-pan/house-rules/issues/76) (review entry skill).** `ASSUMPTION` The review skill loads the compiled reviewer pack.
  With this design that pack includes the writing baseline.
- **[#77](https://github.com/jak-pan/house-rules/issues/77) (one-step assembly).** `ASSUMPTION` One-step assembly compiles these roles unchanged.
  `ASSUMPTION` #77's "Repository rules" part holds the target repository's own rules, or the line
  "Repository rules: this repository has no rules of its own.", and is absent with `--no-target`.
  The dispatcher writes the work item's Decisions and Pre-flight sections into the task file, so
  they reach the worker in the task part; #77 adds no work-item part. This design's role text
  names those parts and depends on them. #77 never includes a loader `AGENTS.md`, but it
  includes a case-2 `AGENTS.md` unchanged; the stay-off line handles its House Rules line. The
  STRUCTURE.md managed-repository loader template does not change in this design; #77 detects it
  by exact match.
  No role includes a file twice, so no deduplication is needed for the role part.

## 10. Questions for the operator

### 1\. What House Rules text should worker and specialist packs carry beyond their role fragments?
`FACT` Three fragments copy text from files outside `prompts/`: Git rules from `rules/delivery.md`, the writing baseline from `rules/writing.md`, and priority labels from the design-flow skill. `FACT` Warden stages only `prompts/` and `skills/pr-ready/`; staging `rules/` is a separate Warden change. `ASSESSMENT` The answer applies to #75's specialist packs too, which are built from these role packs. `ASSESSMENT` The repository's tests prefer one owner per rule, but #73 is rewriting the rule files now.\
The answer decides whether the implementation PR touches `rules/` at all.

1. **Verbatim copies under `prompts/util/`, with a parity test that fails when a copy and its source differ; replace them with direct includes after Warden stages `rules/` and #73 lands (recommended).** No `rules/` change and no conflict with #73. Two copies exist until the follow-up.
2. Move the text: the fragment becomes the only owner, and `rules/delivery.md`, `rules/writing.md` and design-flow link to it. One owner at once, but the change edits files #73 is restructuring, and the always-loaded writing rules then depend on a file under `prompts/`.
3. Wait until Warden stages `rules/` and include the whole rule files. No copies, but every pack grows by about 13 KB and gets the lead's push and merge rules.
4. Include #73's whole foundation in every pack instead. One source for sessions and packs, but every pack grows by about 4,200 tokens (#73's measurement); the reviewer pack would grow from about 2,700 to about 7,000 tokens.

**Answer like so:**
```text
 1. 1
```
