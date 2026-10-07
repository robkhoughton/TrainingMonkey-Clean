# 07 — Weight chart target line + trajectory projection

**What to build:** The existing weight chart shows the active goal's
(validated/annotated/corrected) target as a line, plus a projected trajectory
based on the athlete's current weight trend, so the user can see at a glance
whether they're on track.

**Blocked by:** 06

**Status:** ready-for-agent

- [ ] Target line reflects the goal's final, validated state (post-annotation/auto-correction from 06), not raw user input.
- [ ] Trajectory projection uses the same weight-trend calculation the existing safety check already relies on.
- [ ] No new page — this extends the existing chart.
- [ ] Chart with no active goal renders exactly as it does today (no regression for opted-out or goal-less users).
