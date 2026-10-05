## Test discipline

Single tests finish in seconds and never run long. Remove a known looping or hanging
test at once, keep its defect tracked, and replace it with a small, explicitly bounded
test. Stop a command holding the shared build queue after a few minutes without CPU
progress and after a fixed overall hold limit; configure those limits in the build runner.

Test logging and pruning follow [Guard upkeep](../../references/guards.md#guard-upkeep).
Scale tests move, never vanish: record the replacement test and where it runs,
preserving the scale and behavior it proves.
