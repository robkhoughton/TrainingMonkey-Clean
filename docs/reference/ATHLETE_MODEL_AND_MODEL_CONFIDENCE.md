# Athlete Model & Model Confidence
## Reference Document for Guide and FAQ Generation

This document is intended to be used by an LLM to generate user-facing guide content and FAQ sections explaining the Athlete Model, Model Confidence, and Journal Power features in Your Training Monkey.

---

## What Is the Athlete Model?

The Athlete Model is YTM's persistent, personalized representation of how you specifically respond to training stress. It is not a generic endurance model — it is built from your actual workout data, your journal entries, and your feedback over time.

The model drives three things:
1. **Personalized thresholds** — your ACWR productive window and breakdown threshold, calibrated from your own history rather than population defaults
2. **Coaching quality** — the more the model knows about you, the more precise the daily recommendation
3. **Prescription accuracy** — the model confidence % is cited in every recommendation so you know how much to trust it

The Athlete Model is visible on the **Coach → Season** tab under "What Your Coach Has Learned."

---

## What Is Model Confidence?

Model Confidence is a composite score (0–100%) that measures how well-equipped your coach is to give you accurate, personalized prescriptions. It is not a measure of fitness — it is a measure of how much your coach knows about you.

A low confidence score means the prescription is based on population defaults. A high score means it is based on your personal physiology, schedule, goals, and training history.

Model Confidence updates every time you save a journal entry, update your settings, or complete a new assessment.

---

## The 8 Components of Model Confidence

Model Confidence is calculated from 8 input dimensions. Journal Power counts double (2× weight), giving it the most influence of any single component.

### 1. Athlete Profile
**What it measures:** Whether your age, gender, primary sport, and training experience are on file.

**Why it matters:** These four fields determine which physiological norms and training ranges apply to you. Without them, the coach uses generic defaults.

**How to improve:** Complete your profile in Settings.

**Full credit when:** All four fields (age, gender, sport, experience) are populated.

---

### 2. HR Calibration
**What it measures:** Whether your max heart rate and resting heart rate are on file.

**Why it matters:** HR zones, training load calculations, and effort targets all derive from max HR and resting HR. Default values produce zones that may be 10–15 bpm off from your actual physiology.

**How to improve:** Enter your max HR and resting HR in Settings → HR Zones.

**Full credit when:** Both max HR and resting HR are set.

---

### 3. Coaching Preferences
**What it measures:** Whether your coaching tone, recommendation style, and coaching spectrum are configured.

**Why it matters:** These settings shape how the coach communicates and how aggressively it manages load. A user who prefers direct, technical feedback gets a different experience than one who prefers supportive guidance.

**How to improve:** Set your coaching preferences on the Coach → Season tab.

**Full credit when:** All three preference fields are explicitly set.

---

### 4. Season Plan
**What it measures:** Whether you have an A-priority race goal with a name, date, and distance on file.

**Why it matters:** Without a race goal, the coach cannot plan a periodized buildup, assess race readiness, or flag timeline risk. Target time is not required — the coach does not use it for prescription logic.

**How to improve:** Add an A-goal race on the Coach → Season tab. Include race name, date, and distance (miles).

**Full credit when:** An A-priority goal has name + date + distance set. Partial credit (50%) for name + date without distance.

---

### 5. Weekly Schedule
**What it measures:** Whether your available training days are configured.

**Why it matters:** The weekly training plan is built around your actual availability. Without it, the coach distributes workouts without knowing which days you can train.

**How to improve:** Configure your available days on the Coach → Week tab (training schedule section).

**Full credit when:** At least one available day is set in your training schedule.

---

### 6. Activity History
**What it measures:** Whether you have training data spanning at least 28 days in the last 60 days.

**Why it matters:** ACWR (the primary load management metric) requires a minimum of 28 days of training history to calculate the chronic load baseline. Without that window, load ratios cannot be reliably computed.

**How to improve:** This resolves automatically as you continue logging activities via Strava. No action needed beyond consistent use.

**Full credit when:** At least one activity exists in the 28–60 day window (confirming the chronic load window is populated).

---

### 7. Journal Power (2× weight)
**What it measures:** The quality and consistency of your journal entries over the last 30 days, scored against both coverage (did you journal?) and richness (what did you capture?).

**Why it matters:** Journaling is the highest-value input into the Athlete Model. Each entry teaches the coach things that your watch couldn't: how your body responds to specific workouts under specific conditions. Without journal data, the coach cannot learn your personal load-response relationship or calibrate your recommendations over time.

Journal Power is the most heavily weighted component because it is the most actionable and the most informative.

**How Journal Power is scored (per entry, 0–100):**

Each entry earns up to 11 points, normalized to 0–100:

| Signal                                                                      | Points       |
| --------------------------------------------------------------------------- | ------------ |
| Energy level filled in                                                      | 1            |
| RPE (effort score) filled in                                                | 1            |
| Pain/discomfort field filled in                                             | 1            |
| Sleep quality filled in                                                     | 1            |
| Morning soreness filled in                                                  | 1            |
| HRV recorded/fetched                                                        | 1            |
| Resting HR recorded/fetched                                                 | 1            |
| Notes: any meaningful text (8+ words, or any physio/context keyword)        | 1            |
| Notes: describes physical sensation AND external context                    | 2            |
| Notes: rich detail (24+ words, multiple physio hits, multiple context hits) | 1 additional |

**Maximum per entry: 11 points → 100%**

The component score is: `avg(journal_power_score) × coverage_rate` — so both quality and consistency matter.

**How to improve:**
- Log post-workout notes on every run, even short ones
- Describe how your body felt physically (legs, breathing, effort)
- Include at least one context factor (sleep, heat, stress, travel, nutrition)
- Fill in morning readiness fields (sleep quality, soreness, HRV if available)
- Even a 2-sentence note with one physio word scores meaningfully

**Full credit when:** High average quality AND consistent coverage over the last 30 days.

---

### 8. Aerobic Assessment
**What it measures:** Whether you have completed at least one aerobic drift test in the last 28 days.

**Why it matters:** The aerobic drift test (HR decoupling analysis) provides a calibrated AeT (aerobic threshold) in bpm for your current fitness state. This is used to set HR training zones based on your actual physiology rather than formulas. Fitness changes over time, so a recent assessment reflects your current state.

**How to improve:** Complete an aerobic assessment on the Coach → Season tab. You need a run of at least 60 minutes with HR data.

**Full credit when:** At least one valid assessment is on file within the last 28 days.

---

## How Model Confidence Affects Your Prescription

The composite confidence score is injected into every coaching recommendation. The coach is instructed to cite the confidence % and explain what it means for how much to trust the prescription.

| Confidence | Prescription basis |
|---|---|
| < 40% (Low) | Population defaults — generic endurance athlete assumptions |
| 40–70% (Building) | Partial personalization — some fields calibrated, others default |
| > 70% (High) | Fully personalized — prescription uses your actual physiology, history, and preferences |

---

## What Are Autopsies?

A workout autopsy is an AI analysis generated after you save a journal entry for a completed workout. The autopsy compares your prescribed workout against what actually happened, scores alignment (1–10), and extracts patterns that feed into the Athlete Model.

Autopsies are triggered automatically when you save a journal entry — they are not a separate action. The best way to improve autopsy quality is to write rich journal notes.

---

## FAQ

**Q: Why is my model confidence low if I've been using YTM for months?**
A: Confidence depends on input quality, not just time. The most common gaps are: missing HR calibration, no A-race goal set, and low Journal Power (low note quality or coverage). Check each component on the Athlete Model panel on Coach → Season.

**Q: Does target time for my race affect the prescription?**
A: No. YTM does not use target time for prescription logic. Race name, date, and distance are what matter.

**Q: Why does Journal Power count double?**
A: Journaling is the only input that teaches the coach how your body responds to training stress. Every other component is static configuration. Journal Power is the only continuously improving signal.

**Q: How often should I do an aerobic assessment?**
A: Every 4 weeks or after a significant fitness change (illness, travel, peak training block). Aerobic threshold shifts as fitness changes, so monthly assessments keep your HR zones calibrated.

**Q: My model confidence shows "Activity History: 0%" but I've been running for years. Why?**
A: Activity History is based on data in the last 60 days, specifically whether any activity exists in the 28–60 day window. This reflects whether your *current* chronic load baseline can be calculated — not your lifetime history.

**Q: Can I improve all 8 components to 100%?**
A: Yes, with the exception of Activity History (which requires 28+ days of logged activities and resolves on its own) and Aerobic Assessment (which requires a recent test). All configuration components can be completed in one session.

**Q: Where do I see the current state of my Athlete Model?**
A: Coach → Season tab → Athlete Model panel (right column). Each component shows its current score and a link to the relevant settings or input screen.
