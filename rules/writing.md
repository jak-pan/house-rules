# Writing rules

The reader must understand the text without any other document. They should know what
happened, why it matters and what to do, in that order.

## Communication rules

- Support claims with evidence.
- Distinguish observed causes from hypotheses.
- Distinguish completed fixes from plans and deployments awaiting verification.

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
- Size work per [rules/core.md prime rule 13](core.md#prime-rules).

## Format

- Operator documents (briefs, status, ledgers, reports) are Markdown files. Do not author
  them as HTML; an HTML rendering, if ever needed, is generated from the Markdown.
- Never put long text in a table cell. Use a table only when every cell is a few words;
  give each option or item its own short section instead.
- Diagrams are Mermaid in files and chat, never ASCII art or indented text trees.
  Orient them vertically, with groups and comparisons stacked rather than side by side.
  Draw unconnected groups as separate diagrams, with text between them; one diagram would
  place them side by side.
- Make every file reference a link that works where the text is read.
- In chat, show a local file's absolute path as the link text.
- In chat, set the link target to the file's path from the session root, so the client can
  open it.
- In chat, also give the web link when the reader may need the reviewed version.
- In a file, link another local file with a path relative to the linking file.
- In other text read on the web (issues, PRs, comments, commits, web pages), link files only
  with web links.
- Pin a web link to a commit when it cites evidence.
- Send a file that no link can open with the client's file-sending tool, when it has one.
- In chat, the client turns every written path into a link counted from the session root.
  Write a path in chat only as an absolute path or as a path from the session root.
- Name a file that does not exist yet in words, not as a path.
- Write a PR or issue reference as a Markdown link: `[#52](https://github.com/owner/repo/pull/52)`.
- Prefer lists of five or fewer items.
- Group longer lists only when helpful.
- Preserve sequence, identifiers, and coverage when grouping.

## Claim labels

- Label claims `FACT`, `ASSUMPTION`, `ESTIMATE`, `ASSESSMENT` or `DECISION`. Quote an
  existing decision; never present a settled operator decision as open, or your own choice
  as settled.
- Label a claim `FACT` only after you verified it yourself, in this session, against its
  primary source: the code at a named commit, a command you ran, or a log or record you read.
- Give that evidence with the `FACT`: a link, the command, or the quoted line.
- A claim you remember, infer, read in a summary, or receive from another agent or an earlier
  session is never a `FACT`. Verify it first, or label it `ASSUMPTION` and name its source.

## Checks before sending

- **Reader test:** read only this text as if no other document exists. The reader can tell
  why it matters, what to choose or do, and what happens next.
- **Language test:** no unexplained acronym or label; every sentence states one fact; no
  option or decision appears before its explanation.
- **Detail test:** every fact the decision or action depends on is present.
  For each limit, stop, failure or change, state what it means for the reader.
  Use the same or the next sentence.
  Include what is changed or unchanged, who acts, and what happens next.
  Cut only what the reader does not need.
