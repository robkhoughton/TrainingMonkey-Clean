# 08 — Extended Assessment Category signal (R3) + auto-suspend

**What to build:** The existing daily Assessment Category classifier gains a
third, goal-derived condition — an active goal whose implied deficit (from
05/06's numbers) would put total-energy-only availability below the
low-availability line. This condition never gates today's training action by
itself; when it co-occurs with the existing load-linked underfueling finding,
it becomes supporting evidence in that finding's explanation without creating
a second flag or changing the floor beyond what the existing case already
does; and whenever the existing load-linked finding is live, any active goal
is automatically suspended, visibly and reversibly, regardless of whether the
new condition agrees. A user's declared fueling strategy prevents a
deliberate low-carbohydrate, adequate-total-energy pattern from being
misread as this condition.

**Blocked by:** 05, 06

**Status:** ready-for-agent

- [ ] The goal-derived condition alone produces only an advisory (visible on the goal, not the daily training explanation) and never changes today's safety floor.
- [ ] The goal-derived condition co-occurring with the existing load-linked finding is folded into that finding's explanation as corroborating evidence, without introducing a second category or altering the existing floor logic beyond what the load-linked finding already does.
- [ ] Category priority is unchanged relative to the existing higher-priority categories (e.g. mandatory rest, overtraining).
- [ ] The active goal is automatically suspended the moment the existing load-linked finding is live, independent of the new condition's own state; the suspension is visible to the user and reversible once the underlying finding clears.
- [ ] A fixture representing a declared fat-adapted strategy with adequate total energy does not trigger the goal-derived condition; the same total-energy shortfall without that declared strategy does.
- [ ] Covered by function-level unit tests per the spec's Testing Decisions.
