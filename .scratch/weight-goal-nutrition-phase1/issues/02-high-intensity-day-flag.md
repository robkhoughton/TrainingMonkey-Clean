# 02 — High-intensity-day flag (computed, non-gating)

**What to build:** A per-day boolean, computed from the athlete's existing
zone-time data, indicating whether a given day contained high-intensity work.
Stored/exposed for future use; nothing in the daily recommendation, safety
floor, or any UI consumes it yet — this is prefactoring for a later phase.

**Blocked by:** None — can start immediately.

**Status:** ready-for-agent

- [ ] Flag computes correctly across representative zone-time distributions (all-easy day, day with any high-intensity time, rest day/no activity).
- [ ] Flag is available to be read by future code but is not wired into any current-gating logic, prompt, or UI element.
- [ ] Covered by unit tests at the same function-level seam as the rest of this feature's computed values.
