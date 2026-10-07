Status: ready-for-agent

# Weight Goal + Energy Estimate (Nutrition Module, Phase 1/2)

## Problem Statement

YTM already collects and charts body weight, and already has a safety check (the
`underfueling_risk` branch of Assessment Category) that reacts *after* a user has
lost weight unsafely. But the app gives the user no way to say what weight they're
working toward, no sense of what daily energy that goal actually costs given their
real training load, and no way to catch an unsafe goal *before* they start executing
it. Today's safety check is purely retrospective — it can only notice a problem 28
days after it starts.

This gap is sharpest for YTM's actual population: recreational/masters trail
runners, heavily 60+, mixed-sex, largely postmenopausal. Standard consumer
nutrition/goal features (calorie-counting apps, generic BMR calculators) are built
for a younger population where the dominant risk is overweight; for this cohort the
more common risk is under-fueling, sarcopenia, and bone injury, and a goal-setting
feature that doesn't know that can do real harm.

## Solution

Give the user a single active target-weight goal (mirroring how race goals already
work), anchored to either a target date or a linked race/event. Alongside it, show
an estimate of the athlete's actual daily energy expenditure — computed from their
real logged training history, not a generic activity-factor multiplier — and what
the goal implies they need to eat to hit it safely. Validate the goal at save time
against a rate-of-loss cap and an age-aware absolute floor, so an unsafe goal is
caught at configuration time rather than a month into executing it.

Extend the existing Assessment Category safety check with a new, purely
corroborating signal derived from the goal's own numbers — it can sharpen the
existing weight-trend-based finding, but it can never fire the safety floor on its
own, and it must never misread a deliberate low-carbohydrate/fat-adapted training
strategy as underfueling. The whole goal/energy surface is opt-in and off by
default; the existing safety check keeps protecting every user regardless of
opt-in status.

This is Phase 1 (the goal + the energy estimate, informational) and Phase 2 (the
new safety signal) of a longer-running nutrition module. Full intake logging,
macro targets, and true energy-availability calculation are explicitly out of scope
here — see Out of Scope.

## User Stories

1. As a user, I want to set a single target body weight, so that I have something concrete to work toward instead of just watching a chart.
2. As a user, I want to anchor my weight goal to either a specific date or a linked race, so that the pace implied by my goal is grounded in a real timeline instead of an arbitrary rate.
3. As a user with a goal already tied to a race, I want the pace to be computed from that race's date automatically, so that I don't have to keep two dates in sync.
4. As a user, I want at most one active weight goal at a time, so that the app's guidance about my goal is never ambiguous.
5. As a user, I want to edit or retire my goal, so that I can change my mind or mark it achieved without losing its history.
6. As a user who sets a goal implying an unsafely fast rate of loss, I want the app to tell me at save time, not a week later, so that I don't unknowingly commit to something unsafe.
7. As a user whose goal is anchored to a fixed date/event, I want an unsafe-rate warning to explain that the *date* is the problem (with a suggested later date), so that I understand the tradeoff instead of just being blocked.
8. As a user whose goal is open-ended (rate-based, no fixed date), I want the app to offer a revised, safe target date rather than just rejecting my input, so that I can still move forward with a corrected goal.
9. As a user, I want the app to refuse a target weight below a safe absolute floor regardless of timeline, so that no date/rate combination can talk me into an unsafe destination weight.
10. As a 60+ user, I want that absolute floor to reflect the elevated risk of being underweight at my age, not a generic population BMI cutoff, so that the guardrail actually protects me rather than a younger population.
11. As a user without a height on file, I want to be prompted for it the first time I visit anything nutrition-related, so that the app can compute my energy needs without a separate onboarding step blocking me.
12. As a user who declines to enter my height, I want the goal-setting and energy-estimate features to stay usable in a degraded form (weight-trend safety checks still fully active), so that I'm not locked out of the app's core safety behavior over one optional field.
13. As a user, I want to see my estimated Basal Metabolic Rate and Total Daily Energy Expenditure, computed from my actual logged activities rather than a generic activity-level multiplier, so that the number reflects my real training instead of a guess.
14. As a user, I want the energy estimate to say which estimation method it used (e.g., HR-zone-based vs. distance/elevation-based vs. duration-only) and to flag itself as an estimate, so that I don't mistake a rough number for a precise one.
15. As a user with a weight goal active, I want to see what my goal implies I should eat, and how that compares to my estimated TDEE, so that I understand the practical size of the gap I'm being asked to close.
16. As a user who declares I'm following a fat-adapted/low-carbohydrate training strategy, I want the app to not flag my intentionally low carbohydrate intake as underfueling, so that a deliberate, working strategy isn't treated as a problem.
17. As any user (regardless of fueling strategy), I want the app to still flag a real, load-linked weight-loss trend as underfueling, so that the fat-adapted exception doesn't become a loophole that hides a genuine problem.
18. As a user whose goal-implied energy gap is large enough to suggest low energy availability, but who isn't showing the existing weight-trend-based signal, I want the app to surface this as an advisory (not a training-day gate), so that I get visibility without an unearned change to today's workout.
19. As a user who IS showing the existing load-linked weight-trend signal (today's safety floor is already REDUCE) AND whose goal-implied numbers corroborate it, I want the daily explanation to say so, so that the two pieces of evidence read as one coherent finding instead of two unrelated flags.
20. As a user with an active weight goal, if the load-linked underfueling signal fires, I want my goal to be automatically paused (not silently ignored) with a clear reason, so that the app never keeps coaching me toward a deficit on a day it has itself flagged as unsafe.
21. As a user, I want my weight-goal chart to show a target line and a projected trajectory at my current trend, so that I can see at a glance whether I'm on track without doing the math myself.
22. As a user, I want the goal/energy features fully off until I opt in, with no calorie-tracking gamification anywhere in the daily flow, so that a feature I never asked for doesn't become a source of anxiety.
23. As a user, I want the existing underfueling safety check to keep working exactly as it does today even if I never opt into the goal/energy features, so that opting out of a nutrition feature never means opting out of a safety feature.
24. As a user, I want my declared sex-for-formula-purposes to be captured separately from my gender identity field, so that a biological input to a formula and my personal identity aren't conflated.
25. As a user, I want the weekly plan's existing nutrition mention to draw on this same computed context instead of being an ungrounded aside, so that I'm not getting two disconnected nutrition messages from the same app.
26. As a user who has had my metabolic rate directly measured in a lab (e.g. indirect calorimetry / a metabolic cart test), I want to enter that result and have it used instead of the formula-based estimate, so that the app uses my actual measured number rather than a population prediction whenever I have something better.
27. As a user who has had a DEXA scan, I want to enter its body-fat-percentage and lean-mass results, so that the energy calculation uses my real body composition instead of an estimate from a bioimpedance scale.
28. As a user with an old lab-measured BMR or DEXA result on file, I want the app to tell me when it's treating that result as too stale to trust (e.g. after a long time, or after a large weight change since the test), and fall back to the formula-based estimate in that case, so that a years-old measurement doesn't quietly outrank a better current estimate.
29. As a 60+ user with a DEXA-confirmed low bone density result on file, I want that specific, measured fact — not just my age — to inform how conservative my goal's rate cap and absolute floor are, so that a real, confirmed risk factor is weighted more heavily than a generic age-based assumption.

## Implementation Decisions

**Single seam, by design.** All new decision logic (BMR/TDEE calculation, rate-cap
and floor validation, the new corroborating safety sub-signal, the auto-suspend
interaction) lives as deterministic functions in the metrics/classifier layer,
alongside the existing weight-trend calculation and Assessment Category classifier.
The goal CRUD endpoint and the new UI component are thin wiring with no independent
business logic — they call into this layer and persist/display its output. This
matches the project's existing pattern for this exact kind of decision (the
load-linked/load-independent underfueling split lives entirely in the classifier,
not in the route or the UI) and keeps the feature's real logic testable in one
place instead of scattered across a route handler and a form component.

**Data model.**
- `user_settings` gains: a height field (store metric, display in the user's
  preferred unit — same pattern as the existing weight kg→lbs conversion); a
  separate biological-sex-for-formula field, defaulted from the existing gender
  field but editable independently (the existing gender field may hold an
  identity value that isn't the biological term the BMR formula needs); a
  fueling-strategy field (`fat_adapted` / `conventional`, unset until the user
  opts in — see below); a nutrition-module opt-in timestamp, following the same
  pattern as the app's existing consent/opt-in timestamp fields, defaulting to
  not-set (off).
- A new goal table, structured as a sibling of the existing race-goal table
  rather than columns on `user_settings`: goal type (lose/maintain/gain), target
  weight, and *either* a target date *or* a target rate (exactly one required,
  the other derived) — plus an optional link to a specific race/event as an
  alternative anchor to a bare date, status (active/achieved/paused/suspended/
  abandoned), notes, and timestamps. History matters here: an auto-suspended goal
  must leave a record rather than silently disappearing, both for user trust and
  because goal-vs-outcome history is exactly the data a future calibration step
  would need. Enforce at most one active goal per user, the same way the existing
  race-goal table enforces a single "A" priority.
- The existing journal/wellness table gains an optional body-fat-percentage
  field, sourced the same way weight already is (daily sync from the wellness
  provider, for users on the hardware that reports it). This is what unlocks a
  fat-free-mass-based BMR formula and, later, a real energy-availability
  calculation, for the subset of users who have it.
- No new table for the computed energy values in Phase 1 — compute on demand
  next to the existing weight-trend calculation. A cache table is deferred until
  latency actually requires it; materializing now invites a cache-invalidation
  bug the moment an activity is re-synced or a weight entry corrected.
- A new table for occasional, manually-entered lab/clinical body-composition
  tests — distinct from the daily wellness-sync data because these come from a
  clinical provider (a metabolic-cart RMR test, a DEXA scan), arrive rarely, and
  are entered by hand rather than synced: test date, test type, measured BMR
  (when the test provides one), body-fat percentage and/or fat-free mass (when
  the test provides them — DEXA), and bone-mineral-density result (T-score/
  Z-score, when the test provides one — DEXA also serves this clinical purpose,
  and it's directly relevant given how central bone-health risk is to this
  cohort). One row per test; a user may have several over time, and history is
  kept rather than overwritten, the same reasoning as the goal-history table
  above.

**BMR formula, and where a lab result outranks it.** A measured value always beats
a predicted one, so the precedence is:
1. **Measured** — a lab-measured BMR/RMR result (e.g. from an indirect-
   calorimetry/metabolic-cart test) on file and not stale (see below) is used
   directly, with no formula involved at all.
2. **Fat-free-mass-based formula** — used when a body-fat percentage or lean-mass
   figure is available from *either* a DEXA test on file or the daily wellness
   sync's own body-fat field (a DEXA result, being clinically measured rather
   than a bioimpedance estimate, takes precedence over the sync's figure when
   both exist and the DEXA result isn't stale).
3. **General-population formula** — the fallback, needing only weight, height,
   age, and sex-for-formula.

Which of the three produced the displayed number is part of the output, not
hidden — this is the same "state the tier" principle already applied to the
exercise-energy estimator below.

**Staleness.** A lab result is a snapshot; body composition and metabolic rate
drift over time, especially across a large weight change. Treat a lab-measured
BMR or DEXA result as stale — and fall back down the precedence list above — past
a fixed age (a research-backed value TBD, on the order of 12 months, subject to
the same citation-verification requirement as every other threshold here) *or*
sooner, if current weight has diverged from the weight recorded at test time by
more than a set percentage, since a body-composition or RMR result measured at a
meaningfully different bodyweight no longer describes the athlete's current
state. The specific percentage is likewise a threshold needing verification
before it ships, not a number to invent here.

**TDEE — computed from real training history, not a population multiplier.**
Reject the standard `BMR × activity factor` approach: it's a population average
that ignores the training log YTM already has, and it's also the source of a
classic double-counting error (people apply an "active" multiplier *and* separately
add workout calories). Instead:

- Total daily energy = BMR scaled by a *non-exercise* activity multiplier
  (covering daily-life activity only, never training) + the day's *net* exercise
  energy expenditure (gross expenditure during exercise minus the BMR that same
  time block would have cost anyway — omitting this subtraction is the
  double-count) + a fixed thermic-effect-of-food allowance (an estimate, clearly
  labeled as one, until actual intake data exists in a later phase).
- Report this as a rolling multi-day average, on the same window the existing
  weight-trend signal already uses, so the two numbers are comparable and a
  single rest day doesn't misleadingly read as a deficit.
- The exercise-energy estimate itself is tiered by whatever data a given activity
  has, and the tier used is part of the output, not hidden:
  - Best: heart-rate-zone-based estimate, using the athlete's existing zone-time
    breakdown and personal HR bands — most accurate for interval/threshold work,
    where average-HR-based methods understate cost.
  - Fallback: grade-adjusted mechanical-cost estimate from distance and elevation
    gain, for activities with unreliable HR data — better suited to long trail
    efforts where HR data has gaps.
  - Last resort: duration- and activity-type-based estimate when neither of the
    above is available.
- Calibrating the population-default coefficients above against an individual's
  actual observed weight trajectory (the same "population default, then
  athlete-specific override as evidence accumulates" pattern the app's learned
  athlete model already uses elsewhere) is explicitly deferred — Phase 1 ships the
  tiered estimator; calibration needs a track record of goal-vs-outcome data this
  phase starts collecting but doesn't yet use.

**Rate-of-loss cap and absolute floor (validation, at goal save time).**
- Rate cap: a maximum safe percent-of-bodyweight-per-week loss rate, applied
  regardless of whether the goal is date-anchored or rate-anchored.
- Absolute floor: rather than a single population BMI cutoff (rejected as a poor
  fit — a low BMI carries elevated risk *specifically* for this app's 60+
  population, the opposite direction a general-population cutoff assumes), apply
  two independent floors and take whichever is more conservative: (a) a
  height-based minimum-weight floor set higher than the general-population
  convention, reflecting the elevated frailty/sarcopenia risk of a low BMI in an
  older athlete, usable whenever height is on file; and (b) a
  percent-below-current-weight ceiling on total goal size, independent of height,
  as a second guardrail that still applies for users who decline to enter height.
  Both numbers need the same source-citation treatment as every other threshold
  in the reference guide before they ship — see Further Notes.
- **DEXA-confirmed low bone density personalizes both numbers tighter.** When a
  non-stale DEXA result on file shows a low-bone-density finding, treat that as a
  confirmed, individual risk fact and apply a more conservative rate cap and
  absolute floor than the generic age-adjusted default — the same "population
  default, then override with real individual evidence when it exists" pattern
  the app already applies to its learned athlete model elsewhere. Absent a DEXA
  result, the age-adjusted default applies with no assumption either way about
  the user's actual bone density.
- **Violation handling is accept-and-annotate, tied to the goal's own anchor, not
  a hard reject:** if the goal is anchored to a fixed date or a linked event, the
  save succeeds but is annotated that the implied rate exceeds the safe cap for
  that timeline (explaining the tradeoff, not silently changing the user's date);
  if the goal is rate-anchored with no fixed date, the save is auto-corrected to
  the nearest date that keeps the rate within the safe cap, and that correction is
  shown, not hidden. The absolute floor is the one thing that IS a hard reject —
  no date or rate makes an unsafe destination weight acceptable.

**No height on file:** prompt for it the first time the user reaches any
nutrition-related surface (goal setting or the energy panel), rather than
gatekeeping either behind a separate onboarding step. Declining leaves the energy
estimate unavailable (clearly stated why) while the goal feature and, critically,
the existing weight-trend safety check keep working at full strength — height is
required only for the energy-estimate half of this feature, never for safety
coverage.

**Fueling-strategy field:** captured once, at the point the user opts into the
nutrition module (not inferred later), because the failure mode it exists to
prevent — a caloric-deficit-style check misreading a deliberate low-carbohydrate
strategy as underfueling — can happen from the very first day the module is on,
before any future intake-logging phase could infer it from data. Default
`conventional`; the user changes it explicitly.

**New safety signal — corroborating only, never standalone.** The existing
Assessment Category classifier keeps its current two cases (load-linked weight
drop with elevated training-load ratio → today's safety floor reduces; the
same weight drop without elevated load → surfaced in the narrative, not gating).
Add a third, goal-derived condition: an active goal whose implied daily deficit
would put estimated energy availability below the low-availability line computed
from total energy alone (not a carbohydrate-specific measure — see the design
constraint below). This third condition:
- Never gates today's training action by itself.
- When it co-occurs with the existing load-linked condition, it becomes part of
  that same finding's supporting evidence in the explanation shown to the user —
  it does not create a second, separate flag or change the floor beyond what the
  existing load-linked case already does.
- On its own, it produces only an advisory shown alongside the goal (not in the
  daily training explanation) and — this is the one new automatic action —
  **auto-suspends the active goal** the moment the existing load-linked signal is
  live, regardless of whether the goal-derived condition agrees. The app must
  never keep coaching toward an active deficit goal on a day it has already
  flagged unsafe. The suspension is visible and reversible by the user once the
  underlying signal clears, not a silent state change.

**Design constraint — total-energy adequacy is not the same question as
carbohydrate availability, and this signal must not conflate them.** A user
following a deliberate low-carbohydrate, fat-adapted strategy on long aerobic
efforts is not underfueled by that pattern alone — that is a legitimate, working
strategy for some athletes, and a naive caloric-or-carb check would misfire on
exactly that pattern. The new signal above is scoped to *total* energy balance
only, for exactly this reason, and both the reference-guide entry and the new
coaching-context file must say explicitly that a low-carbohydrate, adequate-total-
energy pattern is not itself a finding. A separate, genuinely session-intensity-
aware question — whether high-intensity work specifically was carbohydrate-fed,
which matters regardless of an athlete's general strategy because glycogen-
depleted high-intensity work carries its own bone-health mechanism — is a real
and already-partially-encoded piece of guidance (today, as unenforced prompt
text), but building a *computed, enforced* version of it is Phase 3-scoped and
depends on intake data this phase doesn't yet collect. This phase's only
in-scope piece of that: compute (not gate on) a per-day flag for whether the day
contained high-intensity work, using the athlete's existing zone-time data, and
expose it as a non-gating value the future phase can build on — nothing consumes
it yet.

**Coaching context integration.** Add a new, opt-in-and-signal-gated context file
to the existing coaching-context library, following that library's own rules
(imperative, no citations inline, and explicit that it does not override the
existing readiness context file's top priority). It should restate the fat-
adaptation/total-vs-carbohydrate-energy distinction inline rather than relying on
a cross-file reference, since the library's own contract has no cross-file
reference mechanism and the two files aren't always injected together. The
existing weekly-plan nutrition mention (currently an ungrounded, unsourced aside)
should be rewired to draw on this same computed context rather than continuing to
exist as a second, disconnected nutrition surface.

**UI.** A goal-management component as a direct sibling of the existing race-goal
manager — same card/form idiom, same inline validation feel. The existing weight
chart gains a target line and trend-projection, not a new page. A new energy
panel (BMR / TDEE / estimated exercise energy, each labeled with its estimation
tier and stated as an estimate) sits in a two-column layout matching the sibling
component's existing pattern — not full-bleed. The daily page gains at most one
line when relevant; no calorie widget or gamification anywhere in the daily flow.
Settings gains the height, sex-for-formula, fueling-strategy, and opt-in fields.

## Testing Decisions

A good test here exercises the computed output (BMR/TDEE numbers, the validation
outcome for a given goal, the classifier's category and floor for a given input
combination) against realistic input fixtures, with all database calls mocked —
never the internal steps of how a number was derived. This is the same shape
already used for the existing weight-trend/underfueling classifier tests and for
the race-context builder tests elsewhere in this suite: direct calls into the
metrics/classifier functions, not full HTTP-level tests through the Flask app.

Modules to test, all at that same function-level seam:
- The BMR/TDEE calculation functions: formula selection (with/without body-fat
  data), the tiered exercise-energy estimator (each tier, and correct fallback
  when higher-tier data is missing), and the double-count guard (net vs. gross
  exercise energy).
- Goal validation: rate-cap and floor checks, both anchor types (date vs. rate,
  and the event-linked variant), the annotate-vs-auto-correct branch for each
  anchor type, and the hard-reject floor case.
- The extended Assessment Category classifier: the new goal-derived condition in
  isolation (advisory-only, never gates alone), in combination with the existing
  load-linked condition (corroboration, still one floor decision, category
  priority unchanged relative to the higher-priority existing categories), and
  the auto-suspend action firing exactly when the load-linked condition is live
  regardless of the goal-derived condition's own state.
- The fat-adaptation exception: a fixture representing a deliberate low-
  carbohydrate/fat-adapted pattern with adequate total energy must not trigger
  the new signal; the same total-energy shortfall without that declared strategy
  must.
- The measured-vs-formula precedence: a fixture with a fresh lab-measured BMR
  must produce that exact value untouched by any formula; a fixture with a
  stale one (past the age cutoff, or past the weight-divergence cutoff) must
  fall back to the formula tier and say so; the same precedence and staleness
  logic, separately, for a DEXA body-fat/lean-mass result feeding the
  fat-free-mass-based formula.
- The DEXA-BMD personalization: a fixture with a confirmed low-bone-density
  result must produce a tighter rate cap/floor than the age-adjusted default
  alone; a fixture with no DEXA result must produce exactly the unmodified
  age-adjusted default.

Out of automated-test scope: the new goal-management UI component and energy
panel. These follow the project's existing manual verification convention
(local mock server + a visual check against the design system, done before any
deploy) rather than new automated frontend tests, matching how the sibling race-
goal UI is verified today.

## Out of Scope

- Actual intake/food logging, and any macro-level (protein/carb/fat) targets —
  Phase 3.
- A true, fat-free-mass-denominated energy-availability calculation — needs
  intake data this phase doesn't collect; Phase 1/2 compute and label an
  explicit *proxy* using total energy only.
- Any *enforced* or *gating* use of session-intensity-aware carbohydrate timing.
  This phase computes the underlying high-intensity-day flag but does not act on
  it — Phase 3.
- Calibrating the TDEE estimator's coefficients against an individual's observed
  outcomes. This phase's design allows for it later; it isn't built now.
- Menstrual-cycle-based or other female-triad-specific screening tools (e.g.
  LEAF-Q-style questionnaires) — deliberately excluded as a poor fit for this
  app's largely postmenopausal population, not deferred.
- Any male-specific hormonal marker (e.g. testosterone) — unmeasurable in this
  app and out of scope regardless of phase.
- Any new elite-athlete-sourced threshold beyond the one rate-of-loss number
  already explicitly approved for use.
- Redesigning the existing bone-health coaching-context file's own gating logic
  to consume a DEXA T-score directly in prose. This phase makes the T-score
  available as a stored, queryable fact and uses it to personalize the
  rate-cap/floor numbers (see Implementation Decisions); wiring it into that
  file's own prompt text is a follow-up for whoever owns that file, not this
  spec.
- A general-purpose lab-results feature (e.g. bloodwork, hormone panels). This
  table is scoped specifically to body-composition/metabolic tests relevant to
  the BMR/energy-availability calculation above, not a general clinical-data
  store.

## Further Notes

**Blocking, pre-merge:** every new numeric threshold introduced here (the BMR
formula's constants, the exercise-energy estimator's per-method coefficients, the
rate-of-loss cap, the age-adjusted absolute-floor numbers, and the low-energy-
availability line used by the new proxy signal) must be checked against its
actual primary source before it is written into the reference guide — none of
them should be treated as settled by this spec. This is a documentation/citation
task, not an implementation blocker for the code itself, but the reference-guide
entry and the code must land together, per the project's existing rule against
undocumented thresholds.

**Still open, deliberately defaulted rather than blocked on:** whether to expose
the high-intensity-day flag anywhere user-visible in this phase (defaulted to:
compute it, don't surface or gate on it yet) — revisit once Phase 3 scoping
starts.

**Not this phase's problem, but worth flagging for whoever schedules the next
one:** this spec covers a backend computation/classifier layer, a new database
table and two new user-settings fields, and a new frontend component — a
genuinely multi-layer build. It was scoped as a single spec because the
underlying logic is narrow enough to converge on one seam (see Implementation
Decisions), but if the resulting work turns out to need independently-demoable
vertical slices, breaking it into tickets afterward is a reasonable next step
rather than a sign this spec was wrong to combine.
