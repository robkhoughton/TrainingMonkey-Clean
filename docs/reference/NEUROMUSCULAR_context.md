# Neuromuscular Training — Hill Sprints, Strides, and Running Economy

**Source:** [Evoke Endurance — Why Even Ultra Runners Need Speed Work](https://evokeendurance.com/resources/why-even-ultra-runners-need-speed-work/)  
**Author:** Scott Johnston  
**Coaching context:** [[neuromuscular]]

---

## Why Neuromuscular Work Matters for Trail Runners

Trail running at sustained effort produces a characteristic shuffle: shortened stride, reduced foot lift, slow turnover. This pattern is adaptive in the short term (energy conservation) but erodes running economy over time and across a training year.

Speed work — specifically hill sprints and strides — counteracts this by recruiting fast-twitch fibers in coordinated, propulsive patterns. The key insight is that the adaptation is **neural, not metabolic**: brief maximal efforts with full recovery develop fiber recruitment and stride mechanics without the fatigue cost of interval or tempo work.

Stride length improvements compound. Even a small increase in stride length per step accumulates to meaningful distance and time advantage over the course of a long run or race.

---

## Hill Sprint Protocol

| Parameter | Value |
|-----------|-------|
| Effort | Near-maximal (95%+) |
| Duration | 8–10 seconds per rep |
| Grade | 20%+ (steep stairs acceptable) |
| Recovery | 2–3 minutes complete rest |
| Starting volume | 6 reps |
| Stop condition | Distance per rep drops from rep 1 baseline |
| Frequency | 1× per week |
| Phase | Year-round |

**Terrain note:** Steep grade exaggerates form errors — a shortened hill sprint at max effort makes it immediately obvious if the athlete is overstriding or not driving knees. This is a feature of the terrain choice.

**Recovery note:** The rest interval must be complete. Shortening recovery to raise cardiovascular demand converts a neuromuscular session into a poorly-designed interval session with neither benefit.

---

## Strides Protocol

Operational detail is maintained in `workout_library.py` (`STRIDE_PROTOCOL`) and injected per-session by the recommendation engine. See that file for canonical count, duration, recovery, terrain, and placement rules.

Summary for reference:

| Parameter | Value |
|-----------|-------|
| Effort | Controlled fast — ~85–90% max speed; not a sprint |
| Duration | 20–25 seconds |
| Recovery | 90 seconds easy walk or jog |
| Volume | 4–6 reps |
| Placement | End of easy run, after main aerobic work |
| Terrain | Flat or gently rolling |

**Phase-aware maximum sessions per week:**

| Phase | Max stride sessions/week |
|-------|--------------------------|
| Base | 3 |
| Build / Specificity | 2 |
| Taper | 2 |
| Peak | 2 |
| Recovery (week 1) | 0 |
| Recovery (week 2+) | 1 (4 strides only, reconnection) |

---

## Running Form — Overstriding

**Correct:** Foot strikes ground directly under the body's center of mass, immediately positioned for propulsive force.

**Overstriding:** Foot reaches forward ahead of the body, heel-strikes first. Creates a braking force on every step. Results in:
- Longer ground contact time
- Reduced stride efficiency
- Higher impact load per step
- Increased injury risk (knee, shin, hip)

**Correction cue:** "Shorten stride, increase turnover — foot under your hip, not in front of it."

Overstriding is common in athletes who came from road running with a heel-strike pattern, and in trail runners who developed a shuffle from sustained climbing. Both populations benefit from strides and hill sprints as a corrective stimulus.

---

## Year-Round Integration

Neither hill sprints nor strides create significant recovery debt. They can be appended to easy aerobic sessions without disrupting training load or requiring additional recovery days. The one exception is the day after a long run — avoid any neuromuscular work then; let that easy run be restorative.
