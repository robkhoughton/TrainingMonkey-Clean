# 06 — Weight goal validation

**What to build:** Saving a weight goal (03) is checked against a maximum safe
rate-of-loss and an absolute floor (a height-based minimum-weight floor, and
independently a percent-below-current-weight ceiling, whichever is more
conservative), tightened further when a non-stale DEXA result shows low bone
density. A goal anchored to a fixed date/event that fails the rate cap saves
with an annotation explaining the tradeoff; a rate-anchored goal with no fixed
date is auto-corrected to the nearest safe date and the correction is shown.
The absolute floor is a hard reject regardless of anchor type.

**Blocked by:** 03, 04

**Status:** ready-for-agent

- [ ] Rate-of-loss cap is checked at save time for both anchor types (date/event vs. rate).
- [ ] A date/event-anchored goal that fails the rate cap saves successfully but with a visible annotation naming the tradeoff.
- [ ] A rate-anchored goal that fails the rate cap is auto-corrected to the nearest compliant date, and the user is shown the correction.
- [ ] Absolute floor combines a height-based minimum (when height is on file) and a percent-below-current-weight ceiling (always available), taking whichever is more conservative; a violation is rejected outright, no annotation path.
- [ ] A non-stale DEXA result showing low bone density produces a tighter rate cap and floor than the age-adjusted default; absence of a DEXA result leaves the age-adjusted default unmodified.
- [ ] Covered by function-level unit tests per the spec's Testing Decisions, including both anchor types and the DEXA-personalization case.
