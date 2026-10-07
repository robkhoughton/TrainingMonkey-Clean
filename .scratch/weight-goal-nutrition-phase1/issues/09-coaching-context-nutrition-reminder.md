# 09 — Coaching context file + fold in nutrition_reminder

**What to build:** A new context file, gated on nutrition opt-in and on an
active goal or any underfueling-related signal (08) being present, added to
the existing coaching-context library — stating the BMR/TDEE facts (05) and
explicitly that a low-carbohydrate, adequate-total-energy pattern is not
itself a finding. The existing weekly-plan nutrition mention is rewired to
draw on this same computed context instead of standing as an ungrounded
aside.

**Blocked by:** 05, 08

**Status:** ready-for-agent

- [ ] New context file follows the existing library's own writing rules (imperative, no inline citations) and states inline (not by cross-file reference) that low-carbohydrate-with-adequate-total-energy is not underfueling.
- [ ] File is gated on nutrition opt-in AND (active goal OR any of the underfueling-related conditions from 08) — never injected for an opted-out user or one with neither condition present.
- [ ] File does not override the existing readiness context file's stated top priority when both are injected.
- [ ] The weekly plan's nutrition mention is grounded in the same computed BMR/TDEE/goal facts instead of its current ungrounded text, for opted-in users; unchanged for opted-out users.
- [ ] Verified end-to-end that the file is actually injected under the stated gating conditions for a fixture user (matching this project's context-seam test convention).
