---
ContentType: Concept
status: Draft
title: Durability Onset Concept
authors:
  - Rob Houghton
created_at: 2026-10-29
tags:
  - type/note
links:
  - "[[YTM Roadmap]]"
  - "[[Central Governor Fatigue]]"
---
# Durability Onset

## Problem

Late in a long run or ultra, the athlete's output falls. Two things can happen to heart rate when it does, and each calls for a different coaching response:

- **Drift up.** HR rises at the same or lower output. This is cardiovascular drift from heat, dehydration or rising aerobic cost. The usual coaching move is to slow down, cool down and drink.
- **Drift down.** HR falls and will not rise even though effort feels high. This is fatigue-driven suppression. The cause can be glycogen depletion, reduced sympathetic drive or neuromuscular fatigue. When it happens, HR is no longer a usable pacing signal. The coaching move is to pace by RPE, fueling cadence and mechanics.

YTM collapses every activity into one averaged number, so the autopsy cannot tell these two patterns apart. It also cannot tell when in the run either one began. The point where it began is the **durability onset**. It may be one of the more informative long-run signals for an ultra athlete; one race so far has been checked (see the worked case below).

## Concept

For each qualifying long run, compute post-sync from streams YTM already fetches. There are **two onsets, tracked separately** — they need not coincide, and in the worked case they were about 40 miles apart:

1. **HR-response onset.** The elapsed time at which HR at matched running speed on flat runnable ground departs from the athlete's *training* baseline at that speed — up (`drift_up`) or down (`suppression`).
2. **Output onset.** The elapsed time at which running-mode output fades: running fraction on runnable grade, running speed, or both, drop and stay down. Classify the HR state at this point as `drift_up`, `suppression` or `coupled_fade` (output and HR fall together).
3. **Gait drift.** Cadence and stride length before vs after each onset, reusing the [[autopsy-gait-drift]] work.

Report each onset as elapsed time, distance and percentage of moving time.

Design rules:

- **Running-mode samples only.** Use `gait_classifier.classify_gait_modes()` to separate running from hiking. Do not use a fixed grade window, because power-hiking a climb is not a fade. A rising hiking fraction is reported as its own observable.
- **Time-based windows, time-weighted samples.** Strava streams are not reliably 1 Hz — a 21-hour race stream arrived at a median of one sample per 6 s — and the filtered samples are not contiguous. Weight each sample by its time delta (capping gaps as pauses) and bin by moving time. Never count samples as seconds. The gait classifier's dwell is in samples, so its effective dwell lengthens on downsampled streams; record the sample interval alongside the result.
- **Baseline from training, not from the run's opening hour.** Race-start arousal inflates HR at a given speed (about 15 bpm in the worked case), so a run's own early baseline makes the return to normal look like a decline. The matched-speed HR baseline comes from the athlete's recent long training runs. The run's own early window is a fallback only when no training baseline exists, and must then be flagged.
- **No absolute bpm thresholds.** Any HR reference is relative to the athlete's training baseline or effective AeT (Dynamic AeT). In the worked case, a fixed "HR < 125 and pace down" rule would have fired around mile 35–40, while the athlete was still running 80–88% of the time and racing well.
- **Handle truncated streams.** Device battery death ends the stream before the finish. Analyze to the end of the stream and record the coverage (stream distance vs activity or race distance); never extrapolate the missing segment.
- **Store at sync, not at autopsy time.** Same constraint as the gait-drift map. Columns go alongside the gait aggregates and carry a `classifier_version`.

## Uses, in order of evidence required

| Use | Category (`llm-determinism.md`) | Gate |
|---|---|---|
| Coaching-context file on late-race pacing: HR stops being reliable late in long efforts, so switch to RPE, fueling cadence and stride frequency | 3 / `[DOMAIN]` | None. This is established coaching practice, it is independent of the metric, and it can ship now |
| Inject both onsets, the HR state at each, and gait drift into the autopsy as bare numbers, with no interpretive framing | 1 (numbers) + 3 (reading them) | Offline validation shows a stable onset |
| Durability trend: onset over months, compared only between similar long runs (duration and vert bands) | 1 | Enough qualifying runs per athlete. Counts as an objective fitness-trend signal, like the `vo2max` bullet |
| Feed into long-run prescription or recovery decisions | 2 if it is ever a floor | **Deferred.** Readiness (HRV/RHR) and normalized divergence already own recovery. Revisit only after the trend proves predictive |

## Worked case — [[ML100_Journal|Mountain Lakes 100]], 2026-09-19

Rob, age 70, finished in 24:37. The Garmin Forerunner 955 battery died around hour 21, so the stream covers 89 of 100 miles, ending near 5:19 AM. GPS mileage is accurate. Wrist HR has a reliable history for this athlete. Stream: median one sample per 6 s, analyzed time-weighted in 60-minute moving-time bins on running-mode samples.

**Training baseline.** HR at 2.2–2.6 m/s on flat (±3%) running ground held at roughly 120–130 bpm for the whole of three long training runs (2026-07-23, 2026-07-25 at 5.4 h, 2026-08-27). The exception was 2026-07-23, where it rose late (drift up). The longest training run was 5.4 h.

| Moving hours | Miles | Time running | HR at matched flat speed | Running cadence |
|---|---|---|---|---|
| 0–4 | 0–27 | 74–93% | 147 → 136 | 153–167 |
| 5–6 | 27–36 | 46–85% | 123–126 | 164–167 |
| 7–9 | 36–50 | 51–88% | 117–121 | 164–167 |
| 10–13 | 50–68 | 44–69% | 105–116 | 163–164 |
| 14–16 | 68–80 | 26–31% | 101–107 | 159–162 |
| 17–19 | 80–89 | 5–14% | 87–98 | 158–163 |

Dips in time running at hours 6, 9 and 10 line up with sustained climbs (+4–5% average grade) and are terrain, not fade.

**Reading.**

- **Hours 0–4: arousal, not fatigue.** HR at matched speed started about 15 bpm above the training baseline and returned to it by mile ~30. That stretch was also a fast start: 43 minutes ahead of a 22-hour plan by mile 30, at a conversational effort that felt easy. Neither the HR cap (HR stayed under VT1, 148) nor perceived effort flagged it.
- **HR-response onset: about hour 7, mile ~36–40, `suppression`.** HR at matched speed fell below the training baseline and kept falling, to about 90 bpm by mile 89. This began in daylight warmth, several hours before sunset, so night cooling cannot explain the onset; it may add to the decline after about hour 11. It started past the longest training run (5.4 h), in territory with no baseline for comparison. Running cadence held at 158–167 spm throughout. The athlete raced well for 25+ miles after this onset.
- **Output onset: miles 64–72, `suppression`.** Time running fell from 69% to 44%, then to 31% and below. This lines up with the fuel plan breaking down (GI rejection and palate fatigue from about hour 13, mile ~63), GI distress by mile 72, and a balance problem at walking pace from about mile 70 (see [[ML_Vertigo]]). The fuel breakdown is the earliest of these in time. Fuel plan: [[GOAT Fuel]] at about 17–25 g/h of carbohydrate plus aid-station food, against an ISSN racing recommendation of 30–50 g/h (Tiller et al. 2019). Hydration followed the plan, and both fluid (500–750 mL/h) and sodium (about 940 mg/L) sat within the ISSN recommendations.

**What this case changes in the design.**

- Two onsets, not one; in this race they were about 40 miles apart, and the first carried no performance cost.
- The matched-speed baseline has to come from training runs. Measured against the race's own first hours, the arousal decay looks like an early fatigue onset at mile ~27.
- A fixed bpm threshold misfires.
- Coaching value lies mostly at the output onset, where fueling and the other causes act. The HR-response onset mainly says HR has stopped being a usable pacing signal.

## Open questions

1. **Does a stable onset exist across races and long runs?** One race shows both onsets clearly. Validate offline on more long runs and races, using the same method as the gait classifier: negative controls (flat/road runs, short runs), a grid sweep over the fade fraction and the matched-speed band, and judging by signal stability. Training runs up to 5.4 h show no HR-response onset at all, so the test set needs efforts past about 7 h (lead-up races) to test the duration hypothesis.
2. **Sensor artifact vs physiology.** Late-run wrist-optical HR dropout and cadence-lock both look like suppression. For Rob, wrist HR has a reliable history, and the race decline was smooth and independent of cadence. For other athletes, check whether the activity record shows which sensor was used, and whether a chest strap should be required for a qualifying run.
3. **Confounds.** Planned slowing, aid-station stops, night sections (cooler air lowers HR at a given speed), heat (`avg_temp_f`), early-race arousal and course profile. Which of these can be excluded deterministically, and which are left for the autopsy LLM to weigh?
4. **RPE can't confirm the onset.** Strava `perceived_exertion` and journal RPE are one number per activity, so they cannot place an onset in time. They can only sit alongside the onset as activity-level context.
5. **Qualifying run.** Is the qualifying definition a minimum moving time, a fraction of the athlete's longest recent run, or both?
6. **Overlap with deprioritized work.** `trail_aerobic_decoupling` was deprioritized on 2026-07-02 because a decoupling chart is a commodity (HRV4Training ships one). This concept differs in three ways: it is late-onset rather than a half-split, it classifies fade type, and its numbers go into the autopsy rather than a chart. Whether that is enough to revive the shared machinery is Rob's call.

## Out of scope

- Real-time in-run alerts. YTM works on synced activities after the fact.
- Prescribing long-run distance as "onset + N miles". No source supports a fixed overload margin.
- An automatic override of the weekly plan on a single run's signal.
