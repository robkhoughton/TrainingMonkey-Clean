# 03 — Weight goal CRUD (basic)

**What to build:** A user opted into the nutrition module can create, edit, and
retire a single active target-weight goal, anchored to either a target date or
a linked race/event, with notes. No rate-cap/floor validation yet — this ticket
is plain persistence plus the single-active-goal rule.

**Blocked by:** 01

**Status:** ready-for-agent

- [ ] Goal form (sibling of the existing race-goal manager's card/form idiom) supports create/edit/retire.
- [ ] Exactly one of target-date or target-rate is required at save; the other is derived; a linked race/event is an alternative anchor to a bare date.
- [ ] At most one active goal per user is enforced, the same way the existing race-goal table enforces a single "A" priority.
- [ ] Retiring/achieving a goal preserves its history rather than deleting the row.
- [ ] Goal management surfaces are hidden unless the user has opted into the nutrition module.
