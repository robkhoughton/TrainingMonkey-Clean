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
- Derive `deviation_reason` from journal note text instead of asking the athlete. Alignment queries currently ask "is something going on I should know about?" when the notes already answered it in prose ("abandoned today's workout due to right QL pain") — an LLM classification pass over the note could populate `deviation_reason` directly, removing the dependency on the athlete answering a query at all. (Distinct from the starvation bullet below, which is the bug; this is a proposed capability.)
- RESOLVED 2026-08-24 (commit `09a2e2d`) — `deviation_reason` NULL-on-all-autopsies was NOT caused by the gates this bullet originally suspected (`classify_deviation()`'s early returns); it was four separate defects (a schema typo silently aborting every write, write ordering, a NULL-vs-'unknown' predicate matching 0 of 31 rows, ungrouped calibration queries duplicating multi-activity days) — all fixed. Scope was 524 rows/35 users, not 256. **Still open**: `classify_deviation()` reads `extraction_result`, absent on all 172 of user 1's alignment<7 autopsies, so `deviation_reason` still writes `'unknown'` until a real signal populates `extraction_result` — that's the live blocker now, not the four fixed defects. Open sub-question, still unresolved: whether same-day divergence is the right readout for a breakdown threshold at all, or whether it should read a preceding window — do NOT decide this on single injury events. (Corrected 2026-09-06 after this bullet's stale wording was re-propagated as current fact into a fresh Open Brain capture during the model-confidence-redesign session — check git log against a roadmap claim before trusting it.)
- Ingest journal for 100-mile race guidance. (via `/process-inbox`)
- Is weekly synthesis used anywhere besides next week's plan? (via `/process-inbox`; likely related to the 2026-08-03 bug note above about the coach not ingesting weekly-plan input — worth checking together)
- Use `avg_temp_f` (activities.avg_temp_f, added 2026-08-05) to flag/adjust for heat-affected sessions — TRIMP conflates heat-driven HR elevation with training load; wrist-optical temp readings need validation before trusting them for this
- Model a minimum-effective-stimulus floor (anabolic resistance) — the generic `ACWR < 0.8` flag isn't age-calibrated, so an athlete holding constant volume can drop below their own rising effective-dose threshold and lose ground undetected; see `project_coaching_framework_gaps` Layer 5 and `VAULT/Research/TSB_ACWR_vs_YTM_Adaptive_Envelope_Memo.md`
- Personal case study candidate: Rob's own before/after (peak condition at RTR/Broken Arrow/ML camp, training feels easier) attributed to 4 YTM mechanisms — journaling self-awareness, easy/hard intensity discipline, workout diversification, normalized-divergence-driven readiness restraint; potential marketing/product-narrative testimonial (2026-08-07)
- Prompt the user for missing coaching-tone/style preference directly inside the autopsy and/or Rx flow when it's unset, rather than only in Settings — it's pure tone/phrasing (not session content), so it's low-risk to ask for in the moment it's actually missing (from the model-confidence reliability review, 2026-09-05)
- Autopsies and Rx should address the athlete by first name or nickname, not generically — this models the self-distancing self-talk pattern (Kross: naming yourself/"you" instead of ruminating in first-person reduces anxiety, improves performance under duress) so the athlete can eventually reproduce the YTM voice as their own internal self-talk mid-effort, not just receive it as app copy. Depends on `coaching_tone`/`coaching_style_spectrum` staying consistent over time — see `BeyondAge/CoAuthor/00_META/Idea_Log.md` 2026-09-05 entry for the book-side framing (2026-09-05)
- Ingest and use `vo2max` — already synced from intervals.icu into `journal_entries` (`intervals_icu_sync.py`), stored, but never read anywhere in Rx/autopsy generation. Objective fitness-trend signal, distinct from daily readiness (from the model-confidence reliability review, 2026-09-05)
- Ingest `has_heartrate` from the Strava activity summary and use it to distinguish "no HR sensor paired" from "true zero effort" — today `average_heartrate or 0` in `strava_training_load.py` treats both the same, silently feeding a false zero into TRIMP/internal ACWR for HR-less activities (2026-09-05)
- Ingest Strava's own `perceived_exertion` field (RPE the athlete logs directly in the Strava app) as a free, zero-additional-friction RPE signal when present, with the existing YTM journal RPE entry as the athlete-facing override — needs an explicit precedence rule (which wins when both exist), not a silent default (2026-09-05)
- Ingest `suffer_score` (Strava's own Relative Effort estimate) as an independent cross-check against YTM's computed TRIMP — large divergence between the two is itself a data-quality flag worth surfacing, not just a redundant number (2026-09-05)
- Ingest per-mile/lap splits — the existing `get_activity_streams()` call in `strava_training_load.py` already fetches full per-second stream data (`time, distance, heartrate, altitude, velocity_smooth, cadence, watts, temp, moving, grade_smooth`) but only ever consumes `heartrate`; splits/laps would let autopsy compare prescribed pacing/effort distribution against actual within-run pattern (fade, negative split, blow-up) instead of one averaged number (2026-09-05)
- Add a structured illness/injury toggle to the journal ("I'm sick / injured today") instead of relying on keyword-matching free-text notes (`_EXO_KEYWORDS` in `strava_app.py`) to infer it — safety-relevant enough that it shouldn't depend on NLP inference from prose (2026-09-05)
- Add a structured life/non-training stress rating (1-5, alongside energy/RPE) instead of inferring it from note keywords ("stress," "work," "travel," "busy") — relates to the existing open Landing Strip question about daily weight as a broad status indicator (2026-09-05)
- Open question, not a decision: should menstrual cycle phase be a tracked input? Common in comparable training platforms (shifts HRV/RHR baselines and load tolerance) — depends on the user base, worth a deliberate yes/no rather than defaulting to "not now" by omission (2026-09-05)
- Grade-bucketed cadence as a trail-appropriate coachable metric — average cadence over a trail run blends running gait with power-hiking gait (a different biomechanical activity), which is why it reads as noise. `get_activity_streams()` in `strava_training_load.py` already fetches `cadence` and `grade_smooth` per-second on every sync (only `heartrate` is currently consumed) — no new Strava API surface needed, just processing. Likely shares grade-bucketing machinery with the planned `trail_aerobic_decoupling`/`segment_efficiency_trend` metrics (see Trail Metrics Plan, `.claude/plans/transient-squishing-pike.md`) — design together, not twice. Pending decisions before this is buildable: (1) runnable-grade band boundaries (e.g. -10% to +8%, tunable — needs real data to set), (2) store raw per-second streams vs. only the derived grade-bucketed aggregates per activity (storage-volume tradeoff, depends on current DB retention practice) (2026-09-05)
- `hr_streams` grows unbounded with no purge path — 14,593 rows / 90MB (81MB in TOAST) as of 2026-09-05, one year of history, `ON DELETE CASCADE` exists on both FKs but nothing in the app ever deletes a real activity or a real (onboarded) user, so it's dead-letter capacity, not an active retention mechanism. Not just a TRIMP write-once artifact — raw streams are re-read on demand for HR charts, aerobic-assessment/AeT drift tests, and `rebucket_zone_times()` inside autopsy generation (zone-time is a function of the raw stream + the day's effective AeT, which recalibrates over time, so re-deriving on read is the *correct* pattern here, not a shortcut — caching would need its own invalidation job). Nothing to fix now — cost is currently trivial (~6.5KB avg row) — but worth revisiting if per-user activity/autopsy volume grows a lot (2026-09-05)
- DB retention is asymmetric and partly dead code, found while scoping the cadence-streams storage decision above: `cleanup_old_recommendations(user_id, keep_days=14)` (`db_utils.py:672`) actively deletes `llm_recommendations` older than 14 days on every Rx generation — meaning no Rx survives long enough for any longitudinal Rx-quality analysis. Meanwhile `cleanup_api_logs(days_to_keep=90)` and `cleanup_analytics_events(days_to_keep=90)` (`db_utils.py:704`, `731`) are defined but have zero callers anywhere in the app — those tables have grown unbounded since inception despite an evident intent to cap them at 90 days. `activities`/`journal_entries`/`ai_autopsies` have no cleanup at all (presumably intentional, but never confirmed as a decision). (1) RESOLVED 2026-09-05 — `keep_days` bumped 14→28 in both the default and the `llm_recommendations_module.py:1437` call site, in conjunction with the model-confidence redesign below (not yet committed/deployed). Still open: (2) wire up or remove the two dead cleanup functions, (3) confirm the no-cleanup policy on core training tables is a decision, not an oversight (2026-09-05)
- **Model-confidence redesign — decided shape, not yet built** (supersedes treating `model_confidence_pct` as a single gamified composite; full reasoning chain from a 2026-09-05 session). Replace the one blended 8-component number with two separately-scored, separately-purposed signals:
  - **Data Reliability** (recency/decay-weighted — load coverage+recency, `has_heartrate`-aware HR density, HRV/RHR baseline reliability+recency reusing `compute_readiness_state`'s own math, journal recency+density, aerobic-assessment staleness decay, autopsy count/recency folded in) — gates whether Rx generation proceeds at all. Below threshold: no LLM call, user sees what's specifically thin and how to fix it. Threshold value TBD — needs redoing against this component set, not the earlier draft numbers (those used binary presence, not decay).
  - **Specification Clarity** (athlete profile, season goal, weekly schedule — doesn't decay, answers "do we know who this athlete is and what they're training for," not "is today's data good"). Season goal specifically is now a **second, independent hard gate**: no season goal → Rx modal blocks with a "can't do this without a season goal" message and a link/redirect to the season-goal input screen, rather than silently falling back to a generic plan.
  - **Dependency, decided 2026-09-05**: the season-goal gate cannot ship until season goals support non-race types (fitness maintenance, weight loss, general — see the existing "allow user to define Goal other than A race" backlog item below). Shipping the gate against race-only goals today would permanently lock out every non-racing user. Build the non-race goal types alongside or before the gate, not after.
  - Coaching preferences / voice-consistency-for-internalization stay **out** of both scores — a separate settings-completion nudge, not a reliability input (see the name/nickname bullet above).
  - Rx prompt consequence: Element 5 ("CONFIDENCE") stops citing the old blended "model confidence %" and autopsy count as two bolted-together facts. Specification Clarity drops out of daily Rx narration entirely (it's a precondition resolved before generation starts, nothing left to report per-day once passed). Element 5 becomes: state Data Reliability alone, in plain language tied to what it measures (e.g. "78% — HR, activity history, and journaling are solid, trust this fully" vs. "45% — light on recent journaling, treat today's call as an estimate").
  - `[planned]` → `.scratch/model-confidence-redesign/issues/` — 7 tickets in dependency order: 01 non-race season goals, 02 Data Reliability score, 03 Specification Clarity score, 04 Data Reliability gates Rx, 05 season-goal hard gate, 06 athlete-model panel two-score display, 07 Rx prompt Data-Reliability-only. Open sub-decisions (exact decay functions, gating threshold, HR-density interim definition) are flagged in the relevant tickets, not pre-decided (2026-09-05)

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
