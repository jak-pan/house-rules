---
name: operator-writing
description: Write every operator-facing text — chat replies, status, briefs, reports, PR text, issue comments — in controlled English with an explanation-first structure, so a reader who knows nothing else understands it. Use for all operator communication; decisions additionally follow skill decision-brief.
license: MIT
---

# Operator Writing

The reader must understand the text without any other document. They should know what
happened, why it matters and what to do, in that order. This skill combines a controlled
language (ASD-STE100, applied at about 80 %) with an explanation-first structure and a
reader test.

## Communication rules

- Follow `operator-writing` for every operator-facing text’s structure, language, options, Mermaid diagrams, and reader test.
- Use `decision-brief` for decisions and explanations.
- Support claims with evidence.
- Distinguish observed causes from hypotheses.
- Distinguish completed fixes from plans and deployments awaiting verification.
- Do not invent operator homework.
- Do not ask permission to continue authorized work.

## Language

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
- Size work per [rules/core.md prime rule 13](../../rules/core.md#prime-rules).

## Format

- Operator documents (briefs, status, ledgers, reports) are Markdown files. Do not author
  them as HTML; an HTML rendering, if ever needed, is generated from the Markdown.
- Never put long text in a table cell. Use a table only when every cell is a few words;
  give each option or item its own short section instead.
- Diagrams are Mermaid in files and chat, never ASCII art or indented text trees.
  Orient them vertically, with groups and comparisons stacked rather than side by side.
  Draw unconnected groups as separate diagrams, with text between them; one diagram would
  place them side by side.
- Give every file the reader must open as an absolute path. If the client cannot open that
  path, also send the file with the client's file-sending tool, when it has one.

- Prefer lists of five or fewer items.
- Group longer lists only when helpful.
- Preserve sequence, identifiers, and coverage when grouping.

## Structure

Lead with the result or the action the reader must take. Then explain in this order, using
only the parts the message needs:

1. **What this is:** the project, module or situation, in one or two sentences.
2. **Terms:** every term the rest uses, defined in plain words.
3. **Example:** one concrete, real example, step by step.
4. **Facts:** what exists or happened, each with its evidence link.
5. **Problem:** what breaks or is missing, shown in the example.
6. **Change or options:** what changed, or the options, numbered 1, 2, 3.
7. **Recommendation and next step:** one prominent recommendation, with its trade-offs when it
   has any, and who acts next. Keep any order the operator asked for.

Rules:

- Never mention a decision, sub-decision, option or label before the text has explained
  it. A summary line at the top may state a result; it never introduces an unexplained
  label.
- Number options with one scheme only (Option 1, 2, 3), with no gaps, and define every
  option where options are listed.
- One diagram at most per topic. Never place two diagrams without text between them.
  Diagram format follows §Format.
- Short chat replies use the same order in compressed form: result → why → what is next.
  Omit empty parts; do not add parts the message does not need.
- Put commands, paths and snippets before optional explanation.
- Order explanations by consequence, not by the order the work happened. Omit empty template
  sections, long activity logs and repeated caveats.
- Number steps that must happen in order. Keep each step small. Use only the steps needed.
  This order is for the reader. It does not limit authorized parallel work.
- Answer numbered questions in the same order, with the same numbers.
- Stay on the requested topic. Keep optional findings separate. Report blockers and material
  risks at once.
- When work closes or is replaced, state what was delivered, what was already done and what
  replaced it. Link the remaining work.
- Keep old evidence below a labeled current summary. Old "unresolved" notes must not
  contradict the current status.

- Keep the requested outcome and material blockers visible.
- State the next action and its owner in messages.
- Highlight operator-owned actions with bold text or a heading.

## GitHub text

Issues, PR bodies, review comments, replies to review and commit messages use the forms in
[references/github-text.md](references/github-text.md).

## Questions to the operator

Questions the operator must answer come after the explanation. Each topic is a level-2
heading; each question is a level-3 heading with its number typed in. See the rendered
[example](references/question-example.md).

- Topic headings are level 2 and question headings level 3, so on GitHub only topics get a
  divider line. The question number is typed and escaped (`1\.`), so no renderer
  renumbers it; numbering continues across topics (1, 2, 3), never 1a, 1b.
- Below the heading come one to three context sentences, each starting with the
  inline-code flag `fact` or `assessment`, with no label in front.
- The next line says what happens after the answer, only when the reader could not infer it.
- A choice lists its options as a normal numbered list (not nested), each with what changes
  and its side effect. Exactly one option is marked "(recommended)". Option text never
  repeats the word "Option".
- The message ends with the bold line "Answer with one numbered line per question, like
  so:" and a three-line numbered example showing an option number, a text answer and `ok`.
  No reply line inside the questions, no answer box, no quotes and no tables.
- Reference a PR or issue as a Markdown link (`[#52](https://github.com/…/pull/52)`). A bare
  `#52` links only in GitHub comments, not in chat or in repository files.
- Each line inside the context ends with a backslash, so GitHub files show it as a separate
  line.
- Work the agent's own team must do (tests, replays, verification) is never a question to
  the operator. List it as an internal task.

## Checks before sending

- **Reader test:** read only this text as if no other document exists. The reader can tell
  why it matters, what to choose or do, and what happens next.
- **Language test:** no unexplained acronym or label; every sentence states one fact; no
  option or decision appears before its explanation.
- **Detail test:** every fact the decision or action depends on is present.
  For each limit, stop, failure or change, state what it means for the reader.
  Use the same or the next sentence.
  Include what is changed or unchanged, who acts, and what happens next.
  Example: not "Fix rounds are capped at three." but "A pull request gets at most three fix rounds.
  After that, the lead simplifies or splits the change within approved authority.
  Routine work continues. Changes outside approved authority require your decision."
  Cut only what the reader does not need.

Decisions use skill `decision-brief` for their full content; this skill sets how all of it
is written.
