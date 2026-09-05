# 02 — Data Reliability score: compute and expose it

**What to build:** A single decay-weighted Data Reliability score (0–100%) per user, replacing the "is this field present" logic of the old model-confidence composite with "is the signal recent, dense, and long-enough-established to trust." Components:

- Load coverage + recency (wire up the load/ACWR-input coverage signal that already exists for visualization but has never fed a reliability score)
- HR calibration density (does recent training actually carry real per-activity HR signal, not just a profile-level HR number) — **PROVISIONAL, see caveat below**
- HRV/RHR baseline reliability + recency — reuse the existing readiness engine's own baseline-sufficiency math (it already requires a minimum number of readings before trusting a baseline) rather than re-deriving new logic
- Journal recency + density — decay-weighted toward the last few days, not a flat 30-day average, so a lapsed journaling habit shows up immediately rather than being smoothed away
- Aerobic-assessment staleness — decays with time since the last test rather than a hard cutoff
- Autopsy count/recency — folded in here rather than kept as a separate gate

Expose the score with a per-component breakdown (what's specifically thin) so later tickets (04, 06, 07) and manual validation can use it. Validate against a handful of real accounts spanning the maturity spectrum (brand-new, established, lapsed) before anything downstream gates on it.

**Why gate on this at all, rather than reuse the old composite (load-bearing context, don't lose this):**
the old blended composite's fatal flaw wasn't just that it mixed presence and decay — it double-weighted journal_power but capped it at roughly a fifth of the total score. A user could clear "good enough to prescribe" purely on HR calibration + activity history, with **zero** recent journaling, and still get a full Rx. That's the actual justification for gating on a score where journal recency decays fast and can't be diluted by unrelated components — not a stylistic preference for decay math.

**HR calibration density — validity-blind, not just coarse (flag prominently, don't undersell this):**
this app doesn't yet ingest whether an activity actually had a heart-rate sensor paired. A dense stream of HR values that are actually silent zeros (`average_heartrate or 0` in strava_training_load.py, no sensor paired) would score as highly reliable under any interim definition built from presence alone — which is exactly backwards, since that's the user whose internal-load numbers (TRIMP, internal ACWR) are most wrong. The profile-level stand-in below is even further from the real signal (it's an onboarding estimate, not training data at all) — treat this whole component as provisional pending `has_heartrate` ingestion, not just "coarser."

**`MIN_AUTOPSIES` (llm_recommendations_module.py:4248) is a separate, unrelated gate — decided, not touched:**
this existing `total_autopsies < 3` check controls only whether `get_athlete_model_context()` emits the full alignment/divergence prompt block or a "LEARNING" placeholder — a lifetime-cumulative calibration-sufficiency question, not a today's-signal-trustworthy question. It stays exactly as-is. Autopsy count is not being "double-gated" by dropping it into Data Reliability — the two thresholds measure different things and were never meant to relate.

**Blocked by:** None — can start immediately

**Status:** implemented, pending real-account number review (2026-09-05)

**Decisions made (2026-09-05, confirmed with user):**
- Autopsy count/recency **dropped** from the component set — confirmed
  `generate_autopsy_for_date()` is only ever called from inside
  `save_journal_entry()` (strava_app.py:5631) for that same date, so an
  autopsy never exists without a same-day journal entry. A standalone
  component would double-count journal_recency.
- HR calibration density: **interim** profile-level `max_hr`/`resting_hr`
  presence (same signal the old composite used), pending `has_heartrate`
  ingestion (separate backlog item). Flagged `interim_definition: True` on
  the component so downstream consumers know it's a stand-in.
- Decay half-lives: journal_recency 5 days, aerobic_staleness 21 days
  (moderate posture). HRV/RHR recency reuses the journal half-life rather
  than a third invented value, since HRV/RHR sync into the same
  journal_entries rows.
- Implementation: `app/data_reliability.py`, `compute_data_reliability(user_id)`.
  Reuses `readiness_engine.get_readiness_metrics()` / `MIN_HRV_CHRONIC` /
  `MIN_RHR_CHRONIC` for the HRV/RHR gate, and `exponential_decay_engine`
  for the half-life math, rather than re-deriving either.
- **Correction to this ticket's original framing:** "the readiness engine's
  own baseline-sufficiency math" is `readiness_engine.py`'s z-score path
  (`get_readiness_metrics()`, `MIN_HRV_CHRONIC`/`MIN_RHR_CHRONIC` = 14/14) —
  **not** a `>=5 HRV / >=3 RHR` check. That number is real but belongs to a
  *different*, superseded path: `llm_recommendations_module.compute_readiness_state()`
  has a legacy ratio-based HRV/RHR fallback (`hrv_baseline_count >= 5`,
  `rhr_baseline_count >= 3`) used only when the z-score path is unavailable,
  embedded inside a larger function that also mixes in unrelated sleep/soreness
  presence scoring. `data_reliability.py` reuses the z-score path's own
  function and constants directly — not a copy-paste of the legacy fallback's
  numbers — which was confirmed as the correct target during a review pass.

**Real-account sanity check (5 accounts spanning the maturity spectrum):**

| Account | Profile | Composite |
|---|---|---|
| user 1 (Rob) | established, active, journaling well | 71 |
| user 80 | established, active, zero journal | 35 |
| user 122 | established, activity stale (~28d) | 20 |
| user 170 | low activity, lapsed (~52d) | 20 |
| user 144 | brand new, zero activities | 20 |

Score differentiates sensibly across the spectrum. One finding worth a look:
`hr_calibration` scored 100 for every account tested, including the two with
zero logged activities — `max_hr`/`resting_hr` are set from an age-based
formula at onboarding, not measured from real training data, so the interim
definition currently can't tell "calibrated" from "never trained." Expected
given the agreed interim definition, but worth knowing going in: this
component won't discriminate at all until `has_heartrate` ingestion lands.

- [x] Score computed per user from the components above, each expressed as a decay/coverage function rather than binary presence
- [x] Component breakdown available (which specific input is dragging the score down)
- [x] Reuses the existing HRV/RHR baseline-reliability logic rather than duplicating it
- [ ] Numbers above still need Rob's sign-off before ticket 04 sets a gating threshold on this score

**Resolved (was open, now decided — see Decisions made above):**
- ~~Exact decay function/half-life per component~~
- ~~HR calibration density's interim definition~~
