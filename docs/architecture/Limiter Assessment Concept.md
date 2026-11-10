---
ContentType: Concept
status: Draft
title: Limiter Assessment Concept
authors:
  - Rob Houghton
created_at: 2026-11-10
tags:
  - type/note
links:
  - "[[YTM Roadmap]]"
  - "[[Durability Onset Concept]]"
  - "[[COACHING_FRAMEWORK_GAPS]]"
  - "[[ML100_Journal]]"
---

# Limiter Assessment

## Problem

A training block for an A race should spend most of its effort on whatever is most likely to keep the athlete from reaching the race goal. That is the athlete's **limiter**. YTM has no limiter concept. It plans from training stage and load, and it compares demand with capacity on only one axis: the Race Readiness Score turns the A race into a single load-miles number (distance + vert/750) and projects whether chronic load can reach it before taper. A volume shortfall is the only limiter it can see.

The raw material for a broader assessment already exists in pieces: AeT/AnT gap, gait-mode aggregates, elevation load, HR and altitude streams, race history, the journal, autopsy `deviation_reason`, and the [[Durability Onset Concept]]. Nothing pulls these together into a ranked, persisted answer to "what is most likely to limit this athlete in this race?", and nothing feeds such an answer into the weekly program.

## Concept

A limiter is a gap between what the race **demands** and what the athlete can currently **supply**, on one specific dimension, confirmed where possible by **evidence of failure** in past races and long runs.

1. **Race demand profile.** Computed in code from race goal fields and, where available, the course GPX: distance, total gain, total descent, longest sustained climb and descent, expected duration (from `target_time`), altitude, expected temperature, cutoffs.
2. **Capacity per dimension.** Computed in code from data YTM already holds or can capture cheaply (table below).
3. **Failure evidence.** Where earlier races and long runs actually came apart: race history, autopsies, and athlete input after races and long runs (see Athlete input below).

The deterministic layer produces a demand-vs-capacity ratio per dimension, each with its evidence and a confidence level. The LLM ranks and weighs these against the athlete's history (category 3). The result is stored, recomputed weekly, shown on the Coach page, and open to the athlete to confirm or override.

## Limiter dimensions

| Dimension | Race demand | Capacity signal | In YTM today | Missing |
|---|---|---|---|---|
| Volume | Race load-miles | Chronic load, Race Readiness projection | Yes | — |
| Aerobic base | Near-all race time below AeT | AeT/AnT gap (`aerobic_assessment_engine`) | Only if the athlete tests | Prompt to test when the gap is unknown |
| Duration durability | Expected duration | Longest recent run duration; durability onset | Run duration; onset is a concept only | Onset validation and storage |
| Climbing | Total gain, longest climb | Weekly vert; running vs hiking fraction on climbs; HR-referenced vertical speed on sustained climbs | Elevation load, `gait_classifier` | A climbing-capacity metric |
| Descending (eccentric) | Total descent, longest descent | Weekly descent; late-run descent speed relative to early | Altitude stream only | Descent load and any descent metric |
| Fueling intake | Carbohydrate g/h × duration | g/h achieved on long training runs | No | Long-run fueling log |
| GI tolerance | Intake rate, format and heat the race requires | GI events at a given rate, format, heat and NSAID use | Free-text notes only | Structured GI event capture |
| Heat / altitude | Forecast temperature, course elevation | Training exposure (`avg_temp_f`) | Temperature only | Altitude exposure |
| Pacing discipline | Plan splits | Split vs plan in past races | No (done by hand for ML100) | Race split analysis |
| Musculoskeletal | Duration and terrain loading | `pain_percentage`, pain location, injury history | Pain % only | Location, history (HIGH in [[COACHING_FRAMEWORK_GAPS]]) |
| Race-specific | Pack weight, night hours, technical ground | Loaded-vest training, night running, balance at walking pace | No | Free-text capture is enough at first |

Fueling intake and GI tolerance are separate dimensions on purpose. Intake rate is what the athlete plans; GI tolerance decides whether the athlete can execute that plan, and a GI failure also costs time directly through stops. Collapsing them into one "fueling" signal hides which one to train.

Load management stays where it is. Climbing and descending capacity are measured to compare with race demand, never to manage load; internal load stays HR-based.

## Athlete input

Race demand and capacity come from race goal fields, the course GPX and synced activity data, with no athlete input. Failure evidence is the one input that needs the athlete: Strava cannot show when fuel stopped going down, when GI distress began, or what the athlete believes limited them.

Three channels, in priority order. All three feed one extraction step that writes the same structured record: which dimensions limited, when each began (mile and elapsed hour), carbohydrate g/h, GI events with timing, candidate causes, and the athlete's own read. The athlete reviews the extracted record before it is saved.

1. **Interview.** The default. Triggered when an activity matching a race goal syncs, and run through the coach chat (`app/chat/`). It follows up on timing and cause, which is where most of the value lies: "when did the fuel stop going down?" is the question that produces a mile-63 timestamp.
2. **Form.** The fallback when the athlete declines or abandons the interview. A multi-select across the limiter dimensions, carbohydrate g/h, and GI events with the mile they began. It captures what limited the athlete but loses most of when and why.
3. **Race report.** For athletes who already write race reports: paste or upload, then the same extraction. Third because few athletes write them.

## Worked case — [[ML100_Journal|Mountain Lakes 100]], 2026-09-19

Rob finished in 24:37, 37 minutes over the sub-24 buckle and outside his 22 ± 2 h bracket. The limiters were identified by hand from the race journal, GPS splits and the matched-speed HR analysis. This is the analysis Limiter Assessment would automate.

**GI distress, fueling breakdown and output collapse happened together.** GI issues were a limiter in this race, concurrent with the fueling breakdown and the output collapse:

| Mile | Event |
|---|---|
| ~63 (hour ~13) | [[GOAT Fuel]] rejection and palate fatigue begin |
| 64–72 | Output onset: time running falls from 69% to 44%, then to 31% and below |
| 72 | GI distress first appears; 18-minute stop; all 5 loose doses issued here go unused |
| 93.5 | GI distress and nausea peak; about 10 minutes off the trail |

Carbohydrate ran about 17–25 g/h all day against an ISSN racing recommendation of 30–50 g/h (Tiller et al. 2019), so intake was low before the GI distress began, and the GI distress then made the intake worse. Candidate GI causes on record: fructose in the fuel, heat, ibuprofen (taken at miles 40 and 72, the second dose as the distress began) and the low carbohydrate rate. One race cannot separate cause from effect among intake, GI and output; the three are recorded as concurrent limiters. YTM's autopsy read the late collapse as a fueling and hydration execution signal from RPE and pain, but had no structured way to record GI as its own factor.

**Other limiters on record.** A fast start (43 minutes ahead of a 22-hour plan by mile 30, at an effort that felt easy and stayed under VT1), a training block short on vert, weak daylight climbing relative to the field, loaded-vest training that never simulated the race-day hardware floor, wasted quads (a failed half-squat at mile 93.5), and a balance problem at walking pace from about mile 70 (see [[ML_Vertigo]]).

**Not a limiter.** The aerobic engine. HR was 99% below VT1 and fell on every leg, and hydration and sodium were within ISSN recommendations.

**What this case shows for the design.**

- Several limiters can act at once and arrive close together. The assessment has to rank them and keep concurrent ones, not pick a single winner.
- Most of the evidence is subjective and time-stamped by the athlete (when fuel was rejected, when GI began). A post-race interview would have recorded these timings without a journal write-up; a form alone would have recorded that GI and fueling limited, but not when.
- The training levers follow directly from the limiters: gut training at race rate on every long run over 3 hours, glucose-only fuel, a planned late-race fuel switch, added vert, progressively longer lead-up races to calibrate all-day pace, and a redesigned loaded-vest protocol.

## Grade-adjusted pace

Grade-adjusted pace (GAP) converts speed on a slope into an equivalent flat-ground pace using a model of how running cost changes with grade. It corrects for grade only. It does not correct for footing or technical terrain, surface, altitude, heat, or fatigue. It models running gait, so it breaks down on climbs steep enough that the athlete power-hikes, and on steep descents, where speed is set by braking, skill and eccentric tolerance rather than metabolic cost.

YTM already uses grade adjustment in one place: `gait_classifier` lowers its running-speed threshold with grade to decide running vs hiking. It deliberately reports raw speed everywhere else, because stride length and real distance need real ground speed. YTM requests `grade_smooth` and `velocity_smooth` streams but no grade-adjusted stream; computing GAP would need a published cost-of-gradient model (e.g. Minetti et al. 2002, not yet in Zotero) or a population-fit model like Strava's.

Where GAP could help limiter assessment:

- **Widening the matched-speed window for durability onset.** The ML100 analysis used only flat running samples (±3% grade). Grade-adjusting running-mode samples on moderate grades would make more of a hilly course usable. This needs offline validation first: on training runs, does GAP-matched HR on moderate grades agree with the flat-only baseline? The usable grade band comes out of that validation, not out of a fixed number.
- **Leg-by-leg fade within one race.** GAP per leg can show where output fell on mixed terrain. Split vs plan already does this better when a plan exists, because the plan encodes the terrain.

Where it does not help:

- **GAP:HR as a general fitness or efficiency signal.** This is still invalid on trail, for the same reasons pace:HR is: footing and technicality remain uncorrected.
- **Descending capacity.** GAP is weakest on descents, which is exactly where the eccentric limiter shows.
- **Race demand.** Demand is distance, gain, descent and duration; GAP adds nothing.
- **Internal load.** Load stays HR-based.

## How it feeds coaching

| Layer | Change | Category (`llm-determinism.md`) |
|---|---|---|
| Race demand profile and capacity ratios | Computed in code, injected as facts | 1 |
| Limiter ranking | LLM weighs ratios, evidence and athlete history; athlete can confirm or override | 3 |
| Weekly program | Ranked limiters injected into `build_weekly_program_prompt()`. Within each stage, key sessions target the top limiter: aerobic gap or muscular endurance in base; specific climbing and descending in build; race-duration long runs with fueling and GI rehearsal in specificity | 3 |
| Coaching context gating | `muscular_endurance.md` and fueling guidance gated on the limiter, not only on days-to-race | 1 (gate) |
| Daily recommendation | Assessment Category and the safety floor unchanged. A limiter only influences session choice inside the floor; it never lifts it | 2 unchanged |
| Autopsy and Weekly Synthesis | Track whether limiter-targeted work happened and whether the limiter is shrinking | 3 |
| Race Readiness | Becomes multi-axis: volume plus each demand-vs-capacity ratio | 1 |

## Uses, in order of evidence required

| Step | Gate |
|---|---|
| Athlete input after races and long runs: interview first, form as the fallback, race report third, all writing one structured record (see Athlete input) | None. Low friction because it appears only after races and long runs |
| Race demand profile from race goal fields and course GPX | None |
| Duration and vert ratios (longest recent run vs expected duration; peak weekly gain and descent vs race totals) | A sourcing decision for each ratio, or an explicit product-judgment label |
| Climbing, descending and durability-onset capacity metrics | Offline validation on Rob's long runs and races before anything is stored |
| Stored limiter assessment, weekly recompute, Coach page panel | Demand profile and at least two validated capacity dimensions |
| Weekly program injection and limiter-based context gating | A stored assessment the athlete has confirmed |

## Open questions

1. **Sourcing.** Which demand-vs-capacity ratios have a literature basis (e.g. longest training run as a fraction of race duration, training vert as a fraction of race gain) and which are product judgment? Each needs a source or an explicit label.
2. **Measurement validity.** Can climbing capacity be measured from Strava data without the terrain confounds that make pace:HR invalid on trail? Can descent load be computed reliably from barometric vs GPS altitude streams?
3. **Ranking.** How much of the ranking is deterministic (largest gap first) and how much is LLM judgment over evidence? How are concurrent limiters, like GI, fueling and output at ML100, represented without forcing a single cause?
4. **Evidence base.** How many races or long runs are enough to call something a limiter rather than a one-off? How does the assessment behave for an athlete with no race history?
5. **Long runs.** Does every qualifying long run get the interview, or only the form, with the interview reserved for races?
6. **Athlete override.** When the athlete disagrees with the ranking, does the override persist until the next race, or until new evidence contradicts it?
7. **Weekly plan altitude.** The Landing Strip notes the weekly plan generates daily-level detail. Limiter allocation belongs at the weekly altitude (which dimension gets the key sessions), so the two should be designed together.
8. **Next A race.** Western States 2027 is the first prospective case: course demand is well documented, and ML100 supplies the failure evidence.

## Out of scope

- Real-time in-race limiter detection. YTM works on synced activities after the fact.
- Using climbing or descending capacity to manage load. Load stays HR-based.
- Elite performance data as a capacity benchmark. Capacity is compared with this race's demand and this athlete's history, not with other athletes.
