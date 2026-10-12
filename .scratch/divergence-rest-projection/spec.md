Status: ready-for-agent

# Divergence Under Rest: Projection + Empty-Window Honesty

## Problem Statement

When Normalized Divergence falls past an athlete's personal breakdown threshold, the daily
recommendation mandates rest and tells the athlete to "reassess tomorrow — if divergence
normalizes back above the threshold, the planned session stays on the table." Rest cannot
deliver that. Divergence does not depend on how much load the athlete carries. It depends only
on how much internal cost each unit of external load costs in the acute window compared with the
chronic window:

    External ACWR / Internal ACWR = r_chronic / r_acute,   where r = TRIMP ÷ Total Load Miles
    Normalized Divergence = 2(x − 1) / (x + 1),             where x = r_chronic / r_acute

A rest day adds zero to both TRIMP and Total Load Miles, so it leaves r_acute unchanged.
Divergence only moves when an older session drops out of the 7-day window. If the cheapest
sessions drop out first, divergence gets **worse** during rest.

Real case (user 1, 2026-10-12): divergence was −0.14 against a calibrated breakdown threshold of
−0.11. The Rx mandated rest and promised a reassessment. User 1 is on the enhanced ACWR
configuration (42-day chronic, decay 0.05). Recomputed forward with that configuration and a rest
row on every day:

| Date | Ext ACWR | Int ACWR | Divergence |
|---|---|---|---|
| 10/11 (stored) | 0.61 | 0.70 | −0.143 |
| 10/12 | 0.55 | 0.66 | −0.188 |
| 10/14 | 0.46 | 0.55 | −0.184 |
| 10/15–16 | 0.27–0.29 | 0.36–0.38 | −0.275 |
| 10/17+ | 0 | 0 | 0/0 → reported as **0** |

This creates a loop. A breach mandates rest, rest deepens the breach, and the deeper breach
mandates more rest. The loop ends only when the acute window is empty. At that point the
canonical divergence calculation returns 0 for a 0/0 input, so the metric shows "balanced" with
no data behind it. The athlete sees a fake all-clear after a week of unnecessary rest. The
dashboard shows the same false 0.

The breach in this case came mostly from session mix, not accumulated fatigue. The session that
dominated the acute window was a planned drift test on flat road (TRIMP/load 15.1, against an
acute-window average of 13.1). Sessions that are cheap per load-mile clear divergence: with a
28-day simple chronic, easy days at the athlete's own easy-session TRIMP/load ratio (~9) brought
it to −0.06 within two days and to 0.00 within three. Recompute the easy-scenario fixture under
the 42-day decay configuration when the projection is built.

## Solution

1. **No fake zero.** If the acute window has no load (both ACWRs are 0, or their average is 0),
   Normalized Divergence is *undefined*, not 0. The verdict says "insufficient acute data".
   Divergence-driven categories don't fire, and the dashboard shows a gap instead of a
   "balanced" reading.
2. **Divergence projection as a stated fact.** Every daily verdict carries a deterministic
   projection of divergence over the next several days under two scenarios: all rest, and
   repeated easy sessions at the athlete's own easy profile. The model gets this as computed
   fact (category 1), the same way it gets the metric verdict. It can then describe what rest
   will and won't do, and can't promise that rest will normalize divergence.
3. **Domain glossary correction.** Add "rest clears divergence" to the recorded misreadings of
   Normalized Divergence in the domain glossary, together with the identity above.
4. **Zone 1 recovery is allowed under a divergence breach when the athlete isn't hurting.**
   Under `overtraining_risk`, the safety floor allows Zone 1 easy sessions (not just rest) when
   both of these hold:
   - the worst Pain Score in the last 3 days is below 40%
   - no journal note in the last 3 days, including rest-day notes, signals injury or pain
   
   Otherwise the floor stays rest-only. Zone 1 easy sessions are the action the projection shows
   actually clears a breach caused by session mix, so the Rx can now prescribe the way out
   instead of a rest loop. Decided by Rob 2026-10-12.

## User Stories

1. As an athlete whose divergence is past my breakdown threshold, I want my daily recommendation to tell me honestly what rest will do to divergence, so that I'm not promised a recovery the math can't deliver.
2. As an athlete told to rest because of divergence, I want to see what kind of session would actually bring divergence back, so that I know the way out of the breach.
3. As an athlete, I want the reassessment criteria in my Rx to be reachable, so that I'm not stuck in a loop of rest that deepens the breach that mandated it.
4. As an athlete who has rested for 7+ days, I want the app to tell me divergence can't be computed right now, so that I don't take a 0 as proof I've recovered.
5. As an athlete looking at the dashboard after a layoff, I want the divergence chart to show a gap where there is no acute data, so that a flat "balanced" line doesn't mislead me.
6. As an athlete whose breach came from a planned hard session (e.g. a drift test), I want the Rx to recognise that the breach is about session mix, so that one planned test doesn't push me into days of unnecessary rest.
7. As an athlete, I want the easy-session scenario to use my own easy-session profile, not a population figure, so that the projection describes my body.
8. As an athlete with too few easy sessions on record to build a profile, I want the projection to show only the rest scenario and say why the easy scenario is missing, so that I never see an invented number.
9. As the coaching model, I want the projected divergence path stated as an authoritative fact in the verdict block, so that I don't re-derive (and mis-derive) how rest affects a rolling ratio.
10. As the coaching model, I want to know which day the rest projection becomes undefined, so that I don't present the empty-window state as recovery.
11. As the coaching model, I want "insufficient acute data" stated explicitly in the verdict when divergence is undefined, so that I don't treat a missing value as 0 and reason from it.
12. As the developer (Rob), I want the safety-floor categories to treat an undefined divergence as "no divergence signal", not as 0, so that the classifier's behaviour on missing data is explicit instead of coming from `or 0` coercion.
13. As the developer, I want the injury risk score to give divergence no contribution when divergence is undefined, so that the dashboard risk number and the daily verdict agree.
14. As the developer, I want the projection to be a pure function of daily load/TRIMP series plus a scenario, so that I can test it against real fixtures without a database.
15. As the developer, I want the projection to use the athlete's configured ACWR method (standard 28-day, or enhanced exponential decay with its configured chronic period and decay rate) and the same canonical divergence formula as the production metric, so that the projection's day-0 value matches the stored value.
16. As the developer, I want the projection to respect the dynamic-AeT cutover (if internal ACWR is on the dynamic track, the projection uses the same internal load), so that the projection and today's metric never come from different internal-load sources.
17. As the developer, I want every divergence call site that currently turns undefined into 0 audited and fixed, so that "undefined" survives end to end from calculation to display.
18. As the developer, I want the glossary to record "rest clears divergence" as a known misreading with the identity behind it, so that future sessions (human or model) don't reintroduce it.
19. As the developer, I want the verdict block to stay compact, so that the projection adds one or two lines of facts, not a table that crowds out the rest of the prompt.
20. As a future maintainer, I want the projection horizon and the easy-profile derivation documented with their rationale, so that I can change them deliberately rather than by accident.
21. As an athlete past my divergence breakdown threshold with no pain and no injury, I want the Rx to allow Zone 1 easy sessions, so that I can clear a breach caused by session mix instead of resting into a deeper breach.
22. As an athlete who reported pain of 40% or more in the last 3 days, I want the floor to stay rest-only under a divergence breach, so that a mechanical problem isn't trained through.
23. As an athlete who notes an injury or pain signal in a rest-day journal note, I want that note to be checked too, so that the app doesn't miss a warning just because I didn't run that day.
24. As an athlete with no pain readings in the last 3 days, I want the floor to stay rest-only, so that missing data is never read as "pain-free".
25. As an athlete allowed Zone 1, I want my Zone 1 HR ceiling stated in the Rx, so that "easy" has a number I can hold to.
26. As the developer, I want the guardrail to reject a "reduce" decision that is really a shortened tempo run under the new recovery floor, so that Zone 1 is enforced, not just requested.
27. As the developer, I want the journal-note injury check to be able to tighten the floor but never loosen it, so that LLM fallibility can only err toward rest.
28. As the developer, I want a failure of the journal-note injury check (error, timeout, unparseable output) to leave the floor rest-only, so that the check fails safe.

## Implementation Decisions

- **Canonical divergence calculation returns undefined for an empty acute window.** The
  canonical Normalized Divergence calculation (and its dynamic-AeT twin, which must stay
  formula-identical) returns undefined (`None`) instead of 0 when both ACWRs are 0 or their
  average is 0. That is the only change to the canonical calculation; the formula stays the same.
- **Downstream consumers treat undefined as undefined.** These consumers currently coerce a
  missing divergence to 0:
  - the assessment-category classifier
  - the injury-risk-score computation in the unified metrics service
  - the verdict block formatter
  - the acwr visualization route
  - the stored-value writers in the training-load module
  
  They must handle undefined explicitly: divergence-driven categories (`overtraining_risk`,
  `recovery_needed`) do not fire, and the risk score gets no divergence contribution. Category
  selection then falls through to the ACWR-driven branches, which is correct: an empty acute
  window means ACWR ≈ 0, giving `undertraining_opportunity`.
- **Stored rows.** The activities table may store `NULL` divergence for empty-window days. No
  schema change is needed; the column is already nullable.
- **New deterministic module: divergence projection.** A pure function. Its inputs are:
  - daily Total Load Miles and TRIMP series covering at least the athlete's chronic period
  - an as-of date
  - the athlete's ACWR method: standard (7-day/28-day sums) or enhanced (7-day acute ÷ 7,
    exponentially decayed chronic with the configured period and decay rate). The default
    enhanced configuration is 42 days, decay 0.05.
  - a scenario (`rest` or `easy` with a per-day load and TRIMP/load ratio)
  - a horizon in days
  
  For each projected day it returns external ACWR, internal ACWR, and Normalized Divergence
  (undefined when the acute window is empty). It uses the athlete's production ACWR method and
  the canonical divergence calculation. Divergence depends only on the acute vs. chronic
  TRIMP/load ratio, so it ignores the chronic denominator. ACWR does not, so the projection
  should use the per-day chronic definition from `.scratch/enhanced-acwr-chronic-per-day/` once
  that fix lands.
- **Projection horizon: 7 days.** That is enough for every current acute session to drop out of
  the window, so it always shows the full outcome of rest, including the day it becomes undefined.
- **Easy-session profile is athlete-specific and deterministic.** The per-day load is the median
  Total Load Miles of the athlete's recent sessions classified `Easy/Recovery` by the Workout
  Classification. The TRIMP/load ratio is the median TRIMP ÷ Total Load Miles across those same
  sessions. If too few such sessions exist in the lookback, the easy scenario is omitted, and the
  verdict says so instead of using a population default. The lookback length and the
  minimum-sample count are new constants; document their rationale beside them.
- **Verdict block additions** (one or two compact lines, stated as authoritative fact):
  - the divergence path under rest, compressed to the key points (next day, the worst point, the
    day it becomes undefined)
  - the divergence path under easy sessions, compressed to the first day it rises back above the
    calibrated breakdown threshold
  - when today's divergence is undefined, an explicit "insufficient acute data — no sessions in
    the 7-day window" line in place of the numeric comparison
- **Prompt tagging.** The projection lines are category-1 facts (computed, injected, never
  re-derived), so they need no `[COMP]` tag. Any accompanying prose instruction (e.g. "do not
  promise that rest will normalize divergence; use the projection") is `[COMP]`.
- **Shared context seam.** The projection is computed alongside the metric verdict. It reaches all
  three daily prompt builders through the shared daily context assembly by construction; no
  per-builder wiring.
- **Domain glossary.** Add a fourth entry to the Normalized Divergence *Avoid (semantics)* block:
  "Treating rest as a way to clear divergence". Include the identity, note that rest only moves
  divergence through window turnover, and explain that the empty-window state is undefined, not 0.
- **Safety floor for `overtraining_risk` becomes conditional** (category 2, decided by Rob
  2026-10-12). The floor is computed server-side from two deterministic-first gates:
  - **Pain gate.** The maximum Pain Score (`pain_percentage`) across journal entries dated within
    the last 3 days must be below 40%. At least one non-null reading must exist in that window.
    With no readings, the gate fails and the floor stays `rest`. The 40% line is the guide's
    "Tolerable — consider modifying" step on the Pain Score scale, where Zone 1 counts as a
    modification. It's also the point where the fallback alignment note already fires.
  - **Journal-note injury veto.** An LLM classification reads the free-text journal notes from
    the last 3 days, rest days included, and answers whether any note signals injury or pain.
    A positive answer fails the gate. Tightness, soreness and swelling/edema are *not* injury
    signals unless the note also reports pain (decided by Rob 2026-10-12). The classifier prompt
    states this rule explicitly, as `[DOMAIN]`. The veto can only tighten the floor, never loosen it. An
    error, timeout or unparseable answer counts as positive (fail safe). The existing
    autopsy-extracted `injury_or_pain_notes` is not the source here, because autopsies run only
    on session days and miss rest-day notes.
  - Both gates pass → floor `recovery`. Either fails → floor `rest`. `mandatory_rest` (days
    since rest over the maximum) is unchanged and still rest-only. It is checked first, so the
    recovery floor can never override it.
- **New floor tier `recovery`.** Allowed: `decision.action` of `rest`, or `reduce` with
  `intensity_target` at the easy/recovery end, `polarized_session_intent` easy, and no
  `hard_session_type`. A `reduce` decision carrying a hard session or moderate-or-above intensity
  violates the floor and goes through the existing regenerate-once-then-fallback path. Checking
  the prose itself is still the separate Landing Strip item (the safety-floor prose check) and
  is not part of this spec.
- **Zone 1 ceiling stated as fact.** When the floor is `recovery`, the verdict block states the
  athlete's Zone 1 HR ceiling (from the athlete's computed HR zones, never re-derived by the
  model) and which gate result allowed it. When the floor is `rest`, the verdict names the gate
  that failed (pain value, journal-note veto, or no pain readings). The `overtraining_risk`
  mandate text splits into two variants matching the two floors.

## Testing Decisions

- **Good tests check external behaviour.** Assert on the verdict block text, the assessment
  category, and the projected divergence values. Don't assert on internal helpers or
  intermediate sums.
- **Seam 1 (existing): the metric verdict path.** Extend the metric-verdict test suite:
  - undefined divergence with ACWR ≈ 0 → category `undertraining_opportunity`, never
    `overtraining_risk` / `recovery_needed`; the verdict block says "insufficient acute data"
    and has no numeric divergence comparison
  - undefined divergence never gets coerced to 0 by the injury risk score
  - when given a projection, the verdict block states the rest path and the easy path with the
    calibrated threshold, using the exact projected values
  - when the easy profile is missing, the verdict block says so and contains no easy-scenario
    number
- **Seam 2 (new): the divergence projection pure function.** A new test module with no DB:
  - **User-1 fixture** covering the 42 days to 2026-10-11 (real daily load/TRIMP, enhanced
    configuration). Day 0 matches the stored 0.61 / 0.70 / −0.143. The rest scenario gives
    −0.188 next day, −0.275 at the worst point, and undefined from 10/17. The easy scenario at
    the athlete's easy profile crosses back above −0.11 within the horizon (exact values
    recomputed under the 42-day configuration when the fixture is built).
  - **Standard-method fixture** for a user on the 28-day path, so both ACWR methods are covered.
  - **Identity check:** a history with constant TRIMP-per-load-mile gives divergence exactly 0
    however volume varies, including an acute spike that moves ACWR well above 1. (Scaling only
    the acute sessions is *not* invariant, because those days also sit inside the chronic
    window.)
  - **Ordering check:** rest worsens divergence when the oldest acute sessions are the cheapest
    per load-mile, and improves it when they are the most expensive.
- **Canonical calculation:** a unit test that both-zero ACWRs give undefined, for both the
  Banister and dynamic-AeT divergence functions.
- **Safety floor (extend the safety-floor tests):**
  - `overtraining_risk` with max pain 0–39% and a negative veto → floor `recovery`; `reduce` +
    easy intensity + no hard session passes; `reduce` + tempo/hard session is a violation; `train`
    is a violation
  - pain exactly 40% → floor `rest` (boundary uses `<`)
  - no pain readings in the 3-day window → floor `rest`
  - veto positive, or veto errors → floor `rest`
  - `mandatory_rest` stays `rest` whatever the gates say
- **Journal-note veto:** tested at its boundary with the LLM call stubbed. The fail-safe paths
  (exception, unparseable output) must give "positive". The classifier's own judgement on real
  notes is checked with a small labelled fixture of journal notes, kept separate from the
  deterministic suite.
- **Prior art:**
  - the metric-verdict tests (fixture `metrics()` builder + thresholds dict)
  - the safety-floor tests (numeric repair against `metrics_snapshot`)
  - the daily-context tests (shared-seam consumption guard)

## Out of Scope

- **A structured "active injury" journal field.** Considered and not chosen. The pain gate plus
  the journal-note veto cover it without a schema or UI change.
- **Checking the prose against the floor.** Tracked separately on the Landing Strip.
- **Telling a mix-driven breach apart from a fatigue-driven one** (e.g. discounting a planned test
  session). That would change what the metric means, and the glossary warns against changing the
  metric's definition on a single event.
- **The enhanced path's per-row chronic average.** Fixed and shipped separately (commit
  `9e5687a`, see `.scratch/enhanced-acwr-chronic-per-day/`).
- Any frontend redesign beyond rendering a gap for undefined divergence.

## Further Notes

- The identity holds for any acute/chronic averaging, as long as external and internal load use
  the same windows and weights. This is why divergence ignores volume and rest days can't change
  it directly.
- Today's journal for user 1 also reported bilateral lower-leg edema and calf tightness. These are
  independent signals that may justify rest on their own; the problem here is only that rest
  was justified *by divergence*, with a reassessment divergence couldn't meet.
- Veto calibration reference case: user 1's 2026-10-11 note ("Mild tightness in right calf.
  Minor bilateral lower leg edema.") is labelled **negative** (no injury signal: tightness and
  edema without pain). With pain 0% on 10/10, 2026-10-12 would have been floor `recovery` (Zone 1
  allowed). The labelled fixture also needs positive cases that mention pain explicitly (e.g.
  "sharp pain in left Achilles on the climbs").
