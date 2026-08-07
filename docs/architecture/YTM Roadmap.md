---
ContentType: Roadmap
status: Draft
Next Steps:
expert_review:
title: YTM Roadmap
description:
agent:
authors:
  - Rob Houghton
notes:
revision_notes:
manual date created:
created_at: 2026-04-02 18:16
updated_at: 2026-04-02 18:16
tags:
  - type/note
links:
---
## Protocol

This roadmap follows the vault-wide Idea Capture Protocol (`C:\Users\robho\Documents\VAULT\CLAUDE.md`) — two triggers land into the Landing Strip:

1. **Rob-triggered**: Rob says "capture this" (or similar) about a YTM idea, at any time, in any session — append immediately, no confirmation needed.
2. **LLM-reviewed**: at `/wrap` (session close), Claude scans for candidate new YTM feature/direction ideas (not bugs, not tasks), checks them against the full roadmap file, and asks a yes/no per candidate before adding anything — nothing lands without an explicit answer.

Either route lands a one-line bullet in **Landing Strip**, untriaged.

**Triage** happens periodically (ad hoc, or during `/weekly-review`): sweep the Landing Strip, move each item into its matching category below (or create a new category), and tag it with a status:

- `[idea]` — captured, not yet scoped
- `[planned]` — scoped, not started
- `[in progress]` — actively being built
- `[shipped]` — done and deployed
- `[deferred]` — considered, explicitly not now (note why if non-obvious)

Untagged bullets below the Landing Strip are legacy backlog from before this protocol existed — tag them opportunistically when touched, no need for a retroactive sweep.

## Landing Strip

*(new ideas land here — untriaged)*

- Update FAQ & Guide pages to explain model confidence and coaching philosophy, using Training Metrics, Athlete Model, and Model Confidence
- Add hill sprints and LIFTMOR-M as workout types
- Rx should regen the weekly work plan (not just adjust the recommendation) on gross, repeated non-compliance — make this explicit in the autopsy
- Need a symbol/notation for normalized divergence
- Does ML applied to the training database need to know the "right answer"? e.g. ACWR 71.5 with Δ positive but HRV normal — what's the correct read?
- Weekly plan currently generates daily-Rx-level detail per weekday — wrong altitude. Weekly plan should map out intensity/duration/frequency by current training phase; day-level specificity belongs to the daily Rx, generated separately. (via `/process-inbox`; likely related to the 2026-08-03 bug note that the coach isn't ingesting weekly-plan input — worth checking together)
- How could successive weekly synthesis be used to improve the athlete model? Shouldn't the LLM know this and "calibrate" its response accordingly — if I explain why a workout did not align with Rx, how is this info ingested and used? (via `/process-inbox`)
- How does YTM process responses to poor alignment? Are they captured in weekly synthesis? AWR seems relevant to TRIMP — daily weight seems like a broad indicator of user status. (via `/process-inbox`)
- Ingest journal for 100-mile race guidance. (via `/process-inbox`)
- Is weekly synthesis used anywhere besides next week's plan? (via `/process-inbox`; likely related to the 2026-08-03 bug note above about the coach not ingesting weekly-plan input — worth checking together)
- Use `avg_temp_f` (activities.avg_temp_f, added 2026-08-05) to flag/adjust for heat-affected sessions — TRIMP conflates heat-driven HR elevation with training load; wrist-optical temp readings need validation before trusting them for this
- Model a minimum-effective-stimulus floor (anabolic resistance) — the generic `ACWR < 0.8` flag isn't age-calibrated, so an athlete holding constant volume can drop below their own rising effective-dose threshold and lose ground undetected; see `project_coaching_framework_gaps` Layer 5 and `VAULT/Research/TSB_ACWR_vs_YTM_Adaptive_Envelope_Memo.md`

---
- **Loading Page**
- Create new landing page that separates current status from history - move away from spreadsheet model
- provide macro/meso/micro context for current status landing page
- Modify data flow so that loading is not delayed by API calls
- when all activities have been logged, check for date before loading morning survey
- load branding during any waits
- Use Nate's color scheme
- prompt for vert if indoor activity is detected
- tick marks on all sliders that aligned with catch points
- Dive deeper logic carries user to:
- Old dashboard
- Journal page
- **Autopsy**
- actual vs prescribed - left side bar per Coach page
- log times in zones
- carbon fiber
- fitness impact
- **for Coach plan**
- allow user define period, 7-day vs 10-day vs 12-day
- allow user to define Goal other than A race, such as fitness, weight loss, etc.
- is confidence scoring simply an average of autopsies and journal entries
- self-reported HR sensor type (chest strap > armband > wrist optical) as a model confidence input — Strava and intervals.icu only expose the recording device (watch), not the paired HR sensor, so this can't be inferred per-activity; would need a one-time profile field feeding the HR Calibration confidence component; could also surface as a rubric item ("pair a chest strap") for users to improve their own confidence score
- **Dynamic AeT**
- use pace/drift to measure progress
- **intervals.icu marketing**
- highlight the fact that everyone is relying exclusively on HR metrics, while ignoring the most important data from your watch
- **Nutrition**
- Nutrition guidance is flawed generic advice
- Build nutrition module
