# Example: questions to the operator

Rendered example for [operator-writing §Questions to the operator](../SKILL.md#questions-to-the-operator).

## Warden

### 1\. What should Warden do with a review request in an unmanaged repository?
`fact` Five repositories are unmanaged. `fact` Today Warden ignores the request and nobody
sees why. `assessment` A silent skip looks like an outage.\
Either option also applies to repositories added later.

1. One comment saying the repository is not managed by House Rules (recommended).
2. A silent skip, visible only in Warden's host log.

### 2\. Send the error text from the failed App install?
`fact` GitHub opened the organization settings page instead of the install page. `fact`
Warden's host log has no entry from that time. `assessment` The error is probably visible
only in the browser.\
Without the text, the cause stays a guess between a missing permission and a wrong link.

## House Rules

### 3\. Merge [#52](https://github.com/jak-pan/house-rules/pull/52), the writing-rules PR?
`fact` An earlier cleanup removed several writing rules without an operator decision; #52
puts them back. `fact` It changes only the operator-writing skill and the rules changelog.\
Agents on this machine use the rules from their next session; Warden and the lanes get them
only after their House Rules pins move.

**Answer with one numbered line per question, like so:**

1. 1
2. not available
3. ok
