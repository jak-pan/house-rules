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

## Language

- One fact per sentence. Instructions: at most 20 words. Descriptions: at most 25 words.
- Active voice, simple tense. Name who does what.
- One term per concept. Define it once at first use, then never use a synonym.
- No unexplained acronyms, internal labels or IDs as a replacement for meaning. An ID may
  follow the plain description, never replace it.
- Concrete over abstract: a real name, number, example or before/after, not "the
  mechanism" or "the invariant".
- Keep the source's uncertainty and qualifiers. Never add a cause, frequency or number the
  evidence does not show. Never drop a hedge, exception or consequence that changes what a
  statement means for the reader.
- No filler, no marketing adjectives, no ceremonial openings or closings.
- Size work per [AGENTS.md prime rule 13](../../AGENTS.md#prime-rules).

## Format

- Operator documents (briefs, status, ledgers, reports) are Markdown files. Do not author
  them as HTML; an HTML rendering, if ever needed, is generated from the Markdown.
- Never put long text in a table cell. Use a table only when every cell is a few words;
  give each option or item its own short section instead.
- Diagrams are Mermaid in files and chat, never ASCII art or indented text trees.
  Orient them vertically, with groups and comparisons stacked rather than side by side.
  Unconnected subgraphs render side by side, so use separate diagrams with text between
  them. When the client shows Mermaid as source, render it with the client's visual tool.

## Structure

Lead with the result or the action the reader must take. Then explain in this order, using
only the parts the message needs:

1. **What this is:** the project, module or situation, in one or two sentences.
2. **Terms:** every term the rest uses, defined in plain words.
3. **Example:** one concrete, real example, step by step.
4. **Facts:** what exists or happened, each with its evidence link.
5. **Problem:** what breaks or is missing, shown in the example.
6. **Change or options:** what changed, or the options, numbered 1, 2, 3.
7. **Recommendation and next step:** one recommendation, and who acts next.

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

## GitHub text

Issues, PR bodies, review comments, replies to review and commit messages use the forms in
[references/github-text.md](references/github-text.md). In short:

- Lead with the observable behavior and its effect; history comes last or not at all.
- Every claim names the commit or version it was seen on, with a full-SHA permalink, a
  command, a count or a verbatim log line. Untested claims say "From code reading".
- Show each regression test as failing on the base and passing on the head.
- State limits: what was not run, not built or not covered.
- Titles name the behavior in plain words, never an internal label or code, and never stop
  mid-phrase. Automatically filed issues follow the issue form too.
- Commit messages state the old behavior, its consequence, then the change. No gate logs,
  no internal round labels, no references to files outside the repository.

Operator direction: 2026-10-04, after issue and PR bodies relied on internal labels and
omitted reproduction and test evidence; an upstream contribution in this form was chosen
as the model.

## Questions to the operator

A question the operator must answer is a card, placed after the explanation:

| Row | Content |
|---|---|
| Type | Decision (choose, approve, accept a risk), design request (define intended behavior) or evidence request (provide a record). |
| Why we ask | One or two sentences, each labelled as fact or assessment. |
| The request | One direct question naming the concrete choices. |
| How to answer | The exact answer format, plus how to answer "not decided", "need more information about X" or "not applicable because …". |
| Done when | What changes after the answer. |

Work the agent's own team must do (tests, replays, verification) is never a question to
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
  Example: not "Fix rounds are capped at three." but "A PR gets at most three fix rounds.
  After that, the lead simplifies or splits the change within approved authority.
  Routine work continues. Changes outside approved authority require your decision."
  Cut only what the reader does not need.

Decisions use skill `decision-brief` for their full content; this skill sets how all of it
is written.
