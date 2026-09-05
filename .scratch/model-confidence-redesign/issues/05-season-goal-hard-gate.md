# 05 — Season-goal hard gate on Rx

**What to build:** A user with no season goal at all (race or non-race) hitting the Rx flow sees a dedicated blocking modal — "can't do this without a season goal" framing — with a direct link/redirect to the season-goal input screen, instead of silently receiving a generic, un-targeted Rx. Setting any goal type (thanks to ticket 01) immediately unblocks the next Rx request.

This is independent of the Data Reliability gate (ticket 04) — a user can have excellent recent data and still be blocked here for having no stated training objective, and vice versa.

**Double-gate precedence with ticket 04 — decide before building either (2026-09-05 review finding):**
"independent" describes the gating *logic*, not what the user *sees*. Neither this ticket nor ticket 04 originally said what happens when both fail at once — which is the default state for a brand-new user (no season goal AND no activity/journal/HRV history, all on day one), not an edge case. Resolve this here and in ticket 04 with one explicit precedence rule before implementing either gate, so a brand-new user gets one coherent blocking message. Candidate: this gate (05) takes priority, since setting a season goal is a one-time setup action independent of daily data quality — the Data Reliability message (04) would then only ever surface once a goal exists but recent data is still thin. Confirm with the user before building.

**Blocked by:** 01 (non-race goal types must exist — shipping this gate against race-only goals would permanently lock out every non-racing user)

**Status:** ready-for-agent

- [ ] A user with zero season goals (no race, no non-race goal) is blocked from Rx generation with the dedicated modal, not a silent fallback
- [ ] The modal links/redirects directly to the season-goal input screen
- [ ] A user with any goal type — race or non-race — passes through this gate
- [ ] Setting a goal via the redirect immediately unblocks the next Rx request without further action
- [ ] A user failing both this gate and ticket 04's Data Reliability gate simultaneously sees the single, precedence-resolved message decided above — not both, not neither
