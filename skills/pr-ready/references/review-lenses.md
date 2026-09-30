# Review lenses

A review round can be a panel: several short reviewers in parallel, each with one lens,
spread across at least two model families, plus one generalist per family. Each lens
reviewer gets the base review prompt ([review-prompt.md](review-prompt.md)) with its lens
line appended, and reports only findings in its lens.

| Lens | Append to the review prompt |
|---|---|
| Generalist | Review the whole change against the review bar. |
| Security and confidentiality | Only: authorization on every path, confidentiality including indirect disclosure (errors, counts, tokens, cursors, timing, work), input handling, secrets. |
| Concurrency and durability | Only: races, ordering, crash and replay, fences and barriers, retries, idempotency, resource ownership and cleanup. |
| Performance and memory | Only: request-path cost against declared bounds, proportional scans, unbounded memory or retained state, measured numbers against claims. |
| Spec conformance | Only: build a traceability pass over the referenced spec sections — for each requirement and acceptance test, cite where the code implements it and which test proves it, and report every requirement that is missing, partial, contradicted, or claimed without a test. Name the section for every finding. |
| Code quality and waste | Only: the waste class of the review bar, duplication, dead code, speculative abstractions, style mismatches. |

**Challenge the spec too.** Every reviewer, whatever its lens, also reports spec issues in a
separate section: requirements that contradict each other or the code's real constraints,
are infeasible or unmeasurable as written, leave a case undefined, or look like a worse
design than an evident alternative. A spec issue blocks only when the code faithfully
implements a wrong spec. The lead triages each one: a clarification goes into the spec
in the same PR; a genuine design choice goes to the operator as a decision.

Loop: panel round → fixer confirms each finding (rejecting false ones with a reason) and
fixes the real ones → each flagging lens checks its own findings and one generalist reviews
the fix diff → next full panel round. Stop when a full panel round finds no blockers; the
project may require two clean rounds for security-critical changes. Track, per lens and
model, how many findings were confirmed, and drop pairings that mostly produce noise.
