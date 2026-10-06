## No fortification

A cache, budget, retry, index-like row, indirection or reduced test that works around
cost or complexity elsewhere must name the root cause. Fix that cause or cite a recorded
decision accepting the workaround. First ask whether the mechanism should exist; delete
or narrow it before adding another mechanism. A workaround without that evidence blocks
review.

When the same class of defect has already been fixed once, first ask whether the mechanism
should exist: delete or narrow it when that suffices. Then check whether the spec is unclear.
Only then introduce one shared mechanism that makes the class impossible instead of
patching another call site. When a finding targets a mechanism an earlier fix round added,
apply this repair order.
