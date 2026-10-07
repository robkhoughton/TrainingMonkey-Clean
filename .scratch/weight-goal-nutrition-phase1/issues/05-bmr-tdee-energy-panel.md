# 05 — BMR/TDEE energy panel

**What to build:** A panel showing the athlete's estimated BMR and TDEE (as a
rolling multi-day average), computed via the full precedence — a fresh
lab-measured BMR first, then a fat-free-mass-based formula using a DEXA or
wellness-sync body-fat figure, then the general-population formula as
fallback — with staleness rules for lab/DEXA inputs, and a tiered,
HR-zone-first / distance-elevation-fallback / duration-last-resort estimate of
exercise energy expenditure feeding the TDEE side. The method/tier actually
used is always shown alongside the number. A user with no height on file sees
the panel locked with a clear reason instead of a number.

**Blocked by:** 01, 04

**Status:** ready-for-agent

- [ ] BMR uses a fresh lab-measured value when present; otherwise the FFM-based formula when a non-stale DEXA or wellness-sync body-fat figure exists; otherwise the general formula — and the panel states which was used.
- [ ] A lab-measured or DEXA result past its staleness window (age-based or weight-divergence-based) is not used, and the panel falls back down the precedence instead.
- [ ] TDEE is reported as a rolling multi-day average aligned to the same window the existing weight-trend signal already uses.
- [ ] Exercise-energy estimate uses the HR-zone-based method when zone-time data is available, grade-adjusted distance/elevation when it isn't, and duration/activity-type as a last resort — and states which tier was used.
- [ ] Exercise-energy calculation nets out the BMR the same time block would have cost anyway (no double-counting).
- [ ] A user with no height on file sees the panel locked with an explanation, while goal-setting (03) and the existing safety check remain fully functional.
- [ ] Covered by function-level unit tests with DB calls mocked, per the spec's Testing Decisions.
