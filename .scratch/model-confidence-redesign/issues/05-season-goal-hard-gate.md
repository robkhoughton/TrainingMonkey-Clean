# 05 — Season-goal hard gate on Rx

**What to build:** A user with no season goal at all (race or non-race) hitting the Rx flow sees a dedicated blocking modal — "can't do this without a season goal" framing — with a direct link/redirect to the season-goal input screen, instead of silently receiving a generic, un-targeted Rx. Setting any goal type (thanks to ticket 01) immediately unblocks the next Rx request.

This is independent of the Data Reliability gate (ticket 04) — a user can have excellent recent data and still be blocked here for having no stated training objective, and vice versa.

**Double-gate precedence with ticket 04 — DECIDED (2026-09-05, with Rob):**
"independent" describes the gating *logic*, not what the user *sees*. **Data Reliability (04) leads when both fail.** Rationale: this gate (season goal) is a 30-second form — the easy fix. Ticket 04's gate is protracted (weeks of training/journaling history). Sequencing the easy one first only to reveal the hard one behind it is a bait-and-switch: the user clears what feels like the whole task, then discovers the real work was still ahead. Leading with the harder requirement sets expectations correctly.

Concretely, for **this** ticket: this gate's dedicated blocking modal (with the redirect) is the user's **only** blocker when Data Reliability already passes — same behavior as originally scoped. But when Data Reliability is *also* failing, this ticket's full modal does not take over the screen; instead, ticket 04's Data Reliability message is primary, with a secondary, non-blocking line surfaced there ("You'll also need a season goal before your first Rx" → this ticket's input screen) rather than this modal displacing it. See ticket 04 for the exact secondary-line copy and the message/link table.

**Blocked by:** 01 (non-race goal types must exist — shipping this gate against race-only goals would permanently lock out every non-racing user)

**Status:** ready-for-agent

- [ ] A user with zero season goals (no race, no non-race goal) AND passing Data Reliability is blocked from Rx generation with the dedicated modal, not a silent fallback
- [ ] The modal links/redirects directly to the season-goal input screen
- [ ] A user with any goal type — race or non-race — passes through this gate
- [ ] Setting a goal via the redirect immediately unblocks the next Rx request without further action
- [ ] A user failing both this gate and ticket 04's Data Reliability gate sees ticket 04's message as primary (with this gate's secondary non-blocking line) — this ticket's own full modal does not independently fire in that case
