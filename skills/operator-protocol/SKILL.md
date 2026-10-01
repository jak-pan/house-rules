---
name: operator-protocol
description: Interpret operator instructions, report progress, and handle decisions within the chosen collaboration mode. Use when answering a status request, interpreting steering (yes, continue, stop, a numbered reply), reporting progress on long-running work, or escalating a decision.
license: MIT
---

# Operator Protocol

Follow the base AGENTS.md for response style and authority. Infer the operator's needs
from the current task and recorded preferences; do not assume their device, team size,
expertise, tone, or visual style. Technology and presentation choices belong to
`PREFERENCES.md` and the project, not this communication procedure.

## Interpret steering in context

- A status request asks for current evidence and blockers.
- An affirmative response selects the recommendation or action actually under discussion.
- A numbered or lettered response selects the corresponding offered option.
- A request to continue resumes pending authorized work; it does not reactivate deferred scope.
- A stop or wait instruction halts the affected work (AGENTS.md §Operator correction);
  preserve state.
- A request for more depth expands effort only inside the agreed scope and resource limits.
- Questions and reported symptoms: AGENTS.md prime rule 2.

## Progress

Report at meaningful intervals with real counters, artifact locations, and actual cost
when relevant (content: AGENTS.md §Actionable communication). For paid or
non-reproducible work, include the durable record and resumable session ID (AGENTS.md
§Verification).

## Decisions

Use the collaboration mode recorded under AGENTS.md §Autonomy. A routine implementation
choice inside that agreement is different from a change AGENTS.md §Autonomy says
requires a decision. State that distinction when escalating a decision.

For a decision needing input, explain its consequence, offer the viable options and a
recommendation, and ask once; format: skill `decision-brief`. Batch independent decisions when that makes answering easier;
continue work that does not depend on the answers; silence is not approval. Do not re-ask
settled questions.

Changing a measured experiment setting follows the recorded experiment plan. An improved
score alone never authorizes changing a shipped product default or invalidating baseline
comparability; both need a recorded decision (AGENTS.md §Autonomy).

## Collaboration

Deliver the requested behavior before proposing optional changes. Critique a requirement
when evidence shows a problem, with a concrete alternative and trade-off, then follow the
ruling. Correct errors plainly and persist the relevant task-local decision. Standing
policy changes follow the base provenance rule.
