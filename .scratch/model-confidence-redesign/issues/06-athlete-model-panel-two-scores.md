# 06 — Athlete-model panel shows two scores, not one composite

**What to build:** The existing "what YTM knows about you" panel, which today shows a single blended model-confidence percentage, is replaced with Data Reliability (02) and Specification Clarity (03) shown as two distinct scores, each with its own component breakdown and "what's missing" guidance — a full replacement, not a third number added alongside the old one.

This is the engagement mechanic now: showing users the real reliability signals directly, so improving them is the same action as improving Rx quality, rather than climbing a gamified number that was only loosely related to it.

**Blocked by:** 02, 03 (both scores must exist)

**Status:** ready-for-agent

**Component copy — reuse ticket 04's mapping, don't invent separate wording (decided 2026-09-05):**
ticket 04 defines the label/message/deep-link mapping for every Data Reliability component (`load_coverage` → "Training history", etc.), each with an action-oriented message and a real link to the fix (e.g. `/settings/hrzones`, `/settings/integrations`). This panel must use that exact same mapping for its breakdown, not raw internal component names and not independently-drafted copy — two different phrasings of the same "why is my score low" answer in two different places is its own confusion.

- [ ] Panel displays Data Reliability and Specification Clarity as two separate scores with separate breakdowns
- [ ] The old single blended model-confidence percentage is fully removed from this panel, not left displayed alongside the new two scores
- [ ] Each score's breakdown gives the user a concrete, specific next action with a working deep link where one exists (not generic advice) — using ticket 04's label/message/link mapping for Data Reliability components
