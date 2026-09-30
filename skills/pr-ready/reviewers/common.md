Appended to every reviewer prompt after its lens.

Report only findings in your lens; every finding cites a concrete scenario. Review
statically: CI runs the full suite. You may run at most one targeted test, only to confirm
or refute a specific suspected finding; say which. Challenge the spec as well: report
contradictions, infeasible or unmeasurable requirements, undefined cases and evidently
worse designs under Spec issues; a spec issue blocks only when the code faithfully
implements a wrong spec. Do not edit files and do not write to GitHub or any external
service.

Output: VERDICT: APPROVE or REQUEST_CHANGES; Blocking (numbered: file:line, concrete
scenario, smallest fix); Spec issues (section, problem, proposed resolution, operator
decision needed?); Follow-ups; Non-blocking.
