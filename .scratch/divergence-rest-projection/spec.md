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
  - **Identity check:** scaling every acute-window session's load and TRIMP by the same factor
    leaves the projected divergence unchanged.
  - **Ordering check:** rest worsens divergence when the oldest acute sessions are the cheapest
    per load-mile, and improves it when they are the most expensive.
- **Canonical calculation:** a unit test that both-zero ACWRs give undefined, for both the
  Banister and dynamic-AeT divergence functions.
- **Prior art:**
  - the metric-verdict tests (fixture `metrics()` builder + thresholds dict)
  - the safety-floor tests (numeric repair against `metrics_snapshot`)
  - the daily-context tests (shared-seam consumption guard)

## Out of Scope

- **Changing the `overtraining_risk` safety floor.** Today the floor allows only `rest`, while
  the mandate text says "REST or very-light recovery only (Zone 1)". The projection shows that
  Zone 1 easy sessions are what clear a mix-driven breach. Widening the floor to allow `reduce`
  is a category-2 safety decision and needs Rob's explicit call. This spec only surfaces the
  projection as fact.
- **Telling a mix-driven breach apart from a fatigue-driven one** (e.g. discounting a planned test
  session). That would change what the metric means, and the glossary warns against changing the
  metric's definition on a single event.
- **The enhanced path's per-row chronic average.** Queued separately in
  `.scratch/enhanced-acwr-chronic-per-day/`.
- Any frontend redesign beyond rendering a gap for undefined divergence.

## Further Notes

- The identity holds for any acute/chronic averaging, as long as external and internal load use
  the same windows and weights. This is why divergence ignores volume and rest days can't change
  it directly.
- Today's journal for user 1 also reported bilateral lower-leg edema and calf tightness. These are
  independent signals that may justify rest on their own; the problem here is only that rest
  was justified *by divergence*, with a reassessment divergence couldn't meet.
- Open question for Rob (not blocking this spec): once the projection is in the prompt, should
  `overtraining_risk` with a mix-driven breach mandate Zone 1 easy sessions instead of full
  rest? See Out of Scope.
