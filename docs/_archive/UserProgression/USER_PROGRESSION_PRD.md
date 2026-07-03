# YTM User Progression & Feature Adoption PRD

**Document Status:** Draft v2 - Value-First Approach
**Created:** 2025-01-04
**Last Revised:** 2025-01-04
**Purpose:** Define optimal user progression based on IMMEDIATE VALUE first, then progressive data collection

---

## 1. EXECUTIVE SUMMARY

### Product Positioning (CRITICAL)

**YTM is for SERIOUS TRAIL RUNNERS.**

This is not a beginner app. Garmin and Coros are fine for newbies. YTM is for athletes who:
- Already use Garmin/Coros but want MORE
- Understand ACWR, TRIMP, periodization
- Want deep, technical, AI-powered analysis
- Are training for races, not just "staying in shape"

**Competitive Positioning:**
- **Garmin/Coros:** Hardware + basic metrics → Good for tracking
- **TrainingPeaks:** Structured plans + TSS → Good for following plans
- **YTM:** AI coach that LEARNS your patterns → Good for adaptive, intelligent training

**Landing Page Strategy:**
Emphasize "for serious trail runners" upfront. This is a FEATURE:
- ✅ Attracts right users (serious trail runners who need this)
- ✅ Filters out wrong users (casual joggers who won't engage)
- ✅ No wasted database clutter from non-target users
- ✅ Sets expectations for technical depth

---

### Core Problem Identified

New users see the dashboard and think: *"Lots of data... but what am I supposed to DO with this?"*

**Root Cause:**
We're asking users to invest time (profile setup) BEFORE showing them the core value proposition (daily recommendations). Users have no reference point for "more accurate" until they've seen the baseline.

**Solution:**
**Show daily recommendation IMMEDIATELY** (with whatever data is available), THEN use that experience to motivate progressive data collection.

**Core Flow:**
```
See Daily Recommendation → Log Workout → Get AI Autopsy → See Better Recommendations → Generate Weekly Plan
```

**Success Metrics:**
- 100% of users see a daily recommendation on first dashboard visit (up from current unclear state)
- Journal adoption: 5% → 50%+
- Weekly plan generation: ~10% → 35%+

---

## 2. CRITICAL DATA PRIORITIES

### 2.1 Rigorous Data Collection Philosophy

YTM's competitive advantage is **patent-pending divergence analysis** and **autopsy-informed learning**. This requires rigorous, complete data:

**Mission-Critical Data (Cannot Compromise):**
1. **Primary Sport** - Trail running focus (different load models than road/cycling)
2. **Age** - Required for max HR calculation (220-age formula or age-adjusted)
3. **Gender** - Required for physiological modeling
4. **Training Experience** - Required for recovery/adaptation rates

**High-Value Data (Major Accuracy Improvement):**
5. **Resting HR** - Improves TRIMP accuracy significantly
6. **Max HR** - Can be calculated from age (220-age), but actual max HR is better
7. **HR Zone Preferences** - Method (percentage vs reserve)

**Strategic Data (Unlocks Learning):**
8. **Journal Entries** - Required for autopsy learning loop
9. **Perceived Effort (RPE)** - Required for divergence validation
10. **Feeling Scores** - Required for pattern detection

**Key Insight:**
With just **Age + Gender**, we can provide a daily recommendation using calculated max HR.
- Calculated Max HR = 220 - age (or more sophisticated age-adjusted formulas)
- This enables HR zone analysis immediately
- Users can later provide actual max HR for improved accuracy

**The Tension:**
- We NEED complete, rigorous data for accurate analysis
- We CAN'T ask for it upfront without showing value first

**Resolution:**
- Show value with minimal data (age → calculated max HR)
- Use that experience to motivate better data collection
- Make data quality visible ("Your TRIMP accuracy: 75% → Improve to 95% with resting HR")

---

## 3. PRIMARY SPORT: CRITICAL SCREENING

**Why This Matters More Than Other Fields:**

You specifically screen for **trail runners** because:
- Different elevation gain patterns than road runners
- Different pacing strategies (uneven terrain)
- Different injury risk profiles (technical descents)
- Different training load models (vertical gain emphasis)

**Current Implementation:**
- `primary_sport` field exists in database
- Used in: Activity type filtering, load conversion factors
- **Problem:** Not emphasized enough in onboarding

**Recommendation:**
- Make primary sport a REQUIRED field before showing dashboard
- Use it to customize the entire first experience
- Show sport-specific value prop on landing page

**Example:**
```
Landing Page Variant A (Trail Runners):
"Stop guessing when to back off. YTM analyzes your vertical gain patterns
and technical terrain stress to prevent trail runner burnout."

Landing Page Variant B (Road Runners):
"Stop guessing when to back off. YTM analyzes your volume and intensity
to optimize your road racing performance."
```

---

## 4. VALUE DELIVERY ANALYSIS

### 4.1 The Immediate Value Question

**User's First Dashboard Visit:**
```
┌─────────────────────────────────────────────────────────┐
│ Training Load Dashboard                                  │
│                                                          │
│ [Chart: ACWR over time]                                  │
│ Current ACWR: 1.18                                       │
│                                                          │
│ [Chart: Divergence Analysis]                             │
│ Current Divergence: +0.03                                │
│                                                          │
│ [Chart: Training Load Trends]                            │
│ 7-day avg: 42.3 miles                                    │
│ 28-day avg: 38.7 miles                                   │
└─────────────────────────────────────────────────────────┘

User's Thought: "Cool charts... but what do I DO with this?"
```

**Missing:** The answer to "what should I do TODAY?"

### 4.2 Core Value Hierarchy

**TIER 1 - IMMEDIATE VALUE (Day 1):**
1. **Daily Recommendation** - "What should I do today?"
   - **User Need:** Actionable guidance
   - **Delivery:** Automatic, requires no user input
   - **Stickiness:** Daily habit formation

**Why This Must Be First:**
- Answers the immediate question users have
- Shows AI capability instantly
- Creates daily touchpoint
- No setup barrier
- Makes all other features make sense in context

---

**TIER 2 - LEARNING VALUE (Day 2-7):**
2. **Journal + Autopsy** - "How did my workout compare to the plan?"
   - **User Need:** Validation, learning, personalization
   - **Delivery:** 30 seconds per workout
   - **Stickiness:** Very high (immediate feedback loop)

**Why This Must Be Second:**
- Low commitment (30 seconds)
- Shows AI learning capability
- Creates "aha moment"
- Improves next daily recommendation
- Demonstrates value of data rigor

---

**TIER 3 - OPTIMIZATION VALUE (Week 2):**
3. **Weekly Training Plan** - "What's my complete training strategy?"
   - **User Need:** Structure, periodization, race prep
   - **Delivery:** One-time generation, weekly updates
   - **Stickiness:** High (weekly ritual)

**Why This Must Be Third:**
- Requires setup (schedule, goals)
- Makes sense after seeing daily recommendations work
- Natural progression from daily → weekly
- Users now trust AI enough to commit time

---

## 5. REVISED OPTIMAL PROGRESSION

### STAGE 0: First Dashboard Visit (VALUE DELIVERY)

**User State:**
- Just connected Strava
- Provided age/gender (required for calculated max HR)
- Sees dashboard with charts
- Thinking: "What do I DO with this data?"

**Prerequisites:**
- Age + Gender collected (via quick form immediately after Strava OAuth)
- Max HR calculated: 220 - age (or age-adjusted formula)
- HR zones calculated from max HR
- Ready to generate daily recommendation

**What Happens:**
User sees **daily recommendation** in prominent banner at top of dashboard:

```
┌─────────────────────────────────────────────────────────┐
│ 🎯 TODAY'S TRAINING RECOMMENDATION                       │
│                                                          │
│ Today (January 4, 2025):                                 │
│ Rest Day or Very Easy 3-4 Miles                          │
│                                                          │
│ Why: Your ACWR is at 1.32 (elevated). You've trained    │
│ 5 consecutive days with yesterday's 8-mile tempo run.    │
│ Taking a rest day brings your ACWR down to ~1.25 by     │
│ Monday, setting you up for a productive week ahead.      │
│                                                          │
│ Alternative: If you must run today, keep it under       │
│ 4 miles and stay in Zone 1-2 (conversational pace).     │
│                                                          │
│ ⚠️ Note: Using calculated max HR (220 - age = 180 bpm). │
│ Add your resting HR for more accurate TRIMP scoring.     │
│                                                          │
│ [Tell Me How It Went →] [Improve Accuracy →]            │
└─────────────────────────────────────────────────────────┘
```

**Key Elements:**
- ✅ ACTIONABLE: Clear guidance for today
- ✅ SPECIFIC: Uses actual user data (ACWR 1.32, 5 consecutive days)
- ✅ RATIONALE: Explains the "why"
- ✅ SHOWS CURRENT STATE: "Using calculated max HR" shows we're working with what we have
- ✅ MOTIVATION: Clear path to improvement (add resting HR)
- ✅ CTA: Two paths - immediate engagement (log workout) or improve accuracy

**User Thought:** "Oh! This is actually useful. And I can make it better."

**Success Metric:** 100% of users see daily recommendation on first visit

---

### STAGE 1: Enhance Recommendation Accuracy (DATA MOTIVATION)

**User State:**
- Saw first daily recommendation with calculated max HR
- Understands the value
- Now motivated to improve accuracy

**What Happens:**
After user clicks "Improve Accuracy" or sees recommendation for 2nd time:

```
┌─────────────────────────────────────────────────────────┐
│ 📊 Your Daily Recommendations Are Good - Let's Make Them│
│    Great                                                 │
│                                                          │
│ Current Accuracy: 75% (Using calculated max HR)          │
│ Potential Accuracy: 95% (With resting HR)               │
│                                                          │
│ Add these 2 fields (takes 15 seconds):                   │
│ • Resting Heart Rate: ___ bpm (measure first thing AM)  │
│ • Actual Max Heart Rate: ___ bpm (optional - we'll     │
│   calculate from your hard workouts if not provided)     │
│                                                          │
│ What This Unlocks:                                       │
│ ✓ Precise TRIMP calculations based on YOUR recovery     │
│ ✓ More accurate internal vs external divergence         │
│ ✓ Better recovery recommendations tailored to you       │
│                                                          │
│ Example: Yesterday's 8-mile tempo                        │
│ Current analysis: "8 miles, ~72% time in Zone 3"        │
│ With resting HR: "8 miles, TRIMP 145, 68% TRIMP         │
│   efficiency, suggests good cardiac fitness"             │
│                                                          │
│ [Add My Resting HR →] [I'll Do This Later]             │
└─────────────────────────────────────────────────────────┘
```

**Key Elements:**
- ✅ SHOWS GAP: 75% → 95% accuracy improvement (not as dramatic as 65%, but honest)
- ✅ SPECIFIC BENEFIT: Shows exact example with technical detail
- ✅ LOW COMMITMENT: 15 seconds, 1-2 fields (not 45 seconds, 4 fields)
- ✅ OPTIONAL: Can skip and still use daily recommendations
- ✅ SMART: Offers to calculate actual max HR from workouts if not provided
- ✅ TECHNICAL LANGUAGE: "TRIMP efficiency", "cardiac fitness" - speaks to serious athletes

**Data Collected:**
- Resting HR (critical for TRIMP accuracy)
- Actual Max HR (optional - can calculate from hard efforts)
- [Already have: Age, Gender, Primary Sport from Stage 0]
- Training Experience (can ask here or later - less critical)

**Success Metric:** 60%+ of users add resting HR within 48 hours

---

### STAGE 2: Activate Learning Loop (AHA MOMENT)

**User State:**
- Receiving daily recommendations (with or without HR data)
- Seeing 2-3 days of recommendations
- Ready to engage

**What Happens:**
Morning after a workout, prominent banner:

```
┌─────────────────────────────────────────────────────────┐
│ 📝 How Did Yesterday Go?                                 │
│                                                          │
│ January 3rd - I recommended:                             │
│ "6 miles easy, conversational pace, Zone 1-2"           │
│                                                          │
│ Did you follow the plan? Go rogue? Skip it?             │
│                                                          │
│ Log it in 30 seconds and I'll:                           │
│ • Compare what I prescribed vs what you actually did     │
│ • Analyze how it affected your training load            │
│ • Detect patterns in your training behavior             │
│ • Adjust today's recommendation based on what happened   │
│                                                          │
│ This is the AI Autopsy system - how I learn YOUR        │
│ specific patterns and become a better coach for you.     │
│                                                          │
│ [Log Yesterday's Workout →]                              │
└─────────────────────────────────────────────────────────┘
```

**Journal Entry Form (Simple):**
```
┌─────────────────────────────────────────────────────────┐
│ Journal Entry - January 3, 2025                          │
│                                                          │
│ Activity: [Auto-populated from Strava]                   │
│ • 6.2 miles, 52 minutes, 750 ft gain                     │
│                                                          │
│ How did you feel?                                        │
│ Energy Level: ●●●●○ (4/5)                                │
│ Perceived Effort: ●●●●●●○○○○ (6/10 - Moderate)          │
│ Any pain/soreness? 20% (Minor)                           │
│                                                          │
│ Notes (optional):                                        │
│ [Felt good but legs were heavy on climbs]               │
│                                                          │
│ [Get AI Autopsy →]                                       │
└─────────────────────────────────────────────────────────┘
```

**Autopsy Response (MUST BE IMPRESSIVE):**
```
┌─────────────────────────────────────────────────────────┐
│ 🔬 AI WORKOUT AUTOPSY - January 3, 2025                 │
│                                                          │
│ Prescribed: 6 miles easy, conversational pace, Zone 1-2  │
│ Actual: 6.2 miles, moderate effort, 750 ft gain         │
│                                                          │
│ ALIGNMENT ANALYSIS:                                      │
│ • Distance: 103% of target (6.2 vs 6.0) ✓               │
│ • Intensity: Moderate effort vs Easy prescribed ⚠️       │
│ • Heart Rate: 68% in Zone 2, 25% in Zone 3 (should      │
│   have been 80%+ Zone 1-2) ⚠️                            │
│ • Elevation: 750 ft gain not in prescription            │
│                                                          │
│ Alignment Score: 6/10                                    │
│                                                          │
│ PATTERN DETECTION:                                       │
│ This is the 3rd consecutive workout where you exceeded   │
│ prescribed intensity. Pattern: You tend to run 15-20%    │
│ harder than recommended, especially on trail runs with   │
│ elevation gain.                                          │
│                                                          │
│ TRAINING LOAD IMPACT:                                    │
│ • Expected TRIMP: 98                                     │
│ • Actual TRIMP: 124 (+27% overage)                       │
│ • ACWR before: 1.28                                      │
│ • ACWR after: 1.32 (+0.04)                               │
│ • Status: Moved from "Monitor" to "Elevated Risk"       │
│                                                          │
│ ADJUSTMENT FOR TOMORROW:                                 │
│ Because you went harder yesterday, I'm adjusting today's │
│ recommendation from "5 miles moderate" to "4 miles easy  │
│ OR rest day" to prevent ACWR from climbing further.     │
│                                                          │
│ LEARNING INTEGRATION:                                    │
│ I now know you're a "runner who goes rogue" type. In     │
│ future recommendations, I'll:                            │
│ 1. Account for typical 15-20% intensity overage         │
│ 2. Pre-emptively suggest shorter distances on easy days │
│ 3. Add explicit "don't go hard" warnings on recovery runs│
│                                                          │
│ This is how I become YOUR coach, not just A coach.      │
│                                                          │
│ [See Today's Updated Recommendation →]                   │
└─────────────────────────────────────────────────────────┘
```

**Key Elements:**
- ✅ SPECIFIC NUMBERS: Uses exact data (6.2 vs 6.0, TRIMP 124 vs 98)
- ✅ PATTERN DETECTION: "3rd consecutive workout" shows AI is watching
- ✅ CONCRETE IMPACT: Shows ACWR change (1.28 → 1.32)
- ✅ IMMEDIATE ADJUSTMENT: Changes today's recommendation
- ✅ LEARNING EXPLICIT: Explains exactly how AI will adapt
- ✅ PERSONALITY: "Runner who goes rogue" makes it memorable

**Success Metric:** 50%+ of users who log one entry log a second within 7 days

---

### STAGE 3: Personalize AI Behavior (CUSTOMIZATION)

**User State:**
- Seen multiple daily recommendations
- Logged 1-2 workouts, received autopsy
- Understands how AI works
- Ready to customize

**What Happens:**
After 2-3 autopsy cycles, CTA appears:

```
┌─────────────────────────────────────────────────────────┐
│ 🎨 Your AI Coach Has a Question                         │
│                                                          │
│ I've analyzed 3 of your workouts now. I notice you      │
│ consistently go 15-20% harder than I recommend.         │
│                                                          │
│ Should I adjust my coaching style?                       │
│                                                          │
│ Option 1: 🛡️ More Conservative                          │
│ "Give me softer recommendations since I tend to overshoot│
│ anyway. Help me avoid injury."                           │
│ → I'll recommend shorter/easier workouts, knowing you'll │
│    naturally push harder.                                │
│                                                          │
│ Option 2: ⚖️ Balanced (Current)                          │
│ "Keep recommending what's optimal. I'll work on following│
│ the plan better."                                        │
│ → I'll continue current recommendations and note when    │
│    you deviate.                                          │
│                                                          │
│ Option 3: 🔥 More Aggressive                             │
│ "I can handle more than you think. Push me harder."     │
│ → I'll recommend harder workouts, testing your limits   │
│    more frequently.                                      │
│                                                          │
│ You can change this anytime in Settings.                │
│                                                          │
│ [Choose My Style →]                                      │
└─────────────────────────────────────────────────────────┘
```

**Key Elements:**
- ✅ CONTEXTUAL: References their actual behavior
- ✅ CONCRETE OPTIONS: Shows exactly what each choice means
- ✅ PERSONAL: "Your AI Coach" not "the AI"
- ✅ CHANGEABLE: Reduces commitment anxiety
- ✅ SMART TIMING: After they've seen autopsy work

**Data Collected:**
- Coaching style / risk tolerance
- (Can also ask coaching tone: casual/supportive/analytical)

**Success Metric:** 40%+ users personalize settings within 14 days

---

### STAGE 4: Add Training Purpose (RACE GOALS)

**User State:**
- Using daily recommendations regularly
- Logging some workouts (autopsy loop active)
- Personalized settings
- Building fitness but... for what?

**What Happens:**
After 1-2 weeks of engagement:

```
┌─────────────────────────────────────────────────────────┐
│ 🏁 What Are You Training For?                           │
│                                                          │
│ You've been training consistently:                       │
│ • 14 days of recommendations followed                    │
│ • 9 workouts logged                                      │
│ • Averaging 38 miles/week                                │
│                                                          │
│ But I don't know what you're building TOWARD.            │
│                                                          │
│ Add a race goal to unlock:                              │
│ ✓ Race-specific periodization (Base→Build→Peak→Taper)   │
│ ✓ Countdown timeline (weeks to race)                    │
│ ✓ Target pace workouts for your goal time               │
│ ✓ Weekly training programs aligned to your race date    │
│                                                          │
│ Examples:                                                │
│ • Trail marathon: Moab Red Hot 55k (March 15)          │
│ • Road half: Big Sur Half Marathon (April 27)          │
│ • Ultra: Western States 100 (June 28)                   │
│                                                          │
│ Without a goal: You're training in circles.             │
│ With a goal: Every workout has a purpose.                │
│                                                          │
│ [Add My Race Goal →] [Skip - Just Maintaining Fitness]  │
└─────────────────────────────────────────────────────────┘
```

**Key Elements:**
- ✅ EARNED: Shows their engagement metrics
- ✅ SPECIFIC BENEFITS: Clear unlocks
- ✅ EXAMPLES: Shows realistic race goals
- ✅ OPTIONAL: Can skip if just maintaining fitness
- ✅ PURPOSE: Frames as "training with purpose"

**Data Collected:**
- Race name, date, type
- Priority (A/B/C)
- Target time (optional)

**Success Metric:** 30%+ users add race goal within 30 days

---

### STAGE 5: Structure Training Time (TRAINING SCHEDULE)

**User State:**
- Has race goal (or skipped - training for fitness)
- Ready for structured programs
- Trusts AI enough to commit 2 minutes

**What Happens:**
After race goal added:

```
┌─────────────────────────────────────────────────────────┐
│ 📅 Let's Build Your Training Program                    │
│                                                          │
│ Race Goal: Moab Red Hot 55k - March 15, 2025           │
│ Time Until Race: 70 days (10 weeks)                     │
│                                                          │
│ I can give you daily recommendations (current) OR        │
│ complete weekly training programs with:                  │
│ • 7-day structured plans                                 │
│ • Day-by-day workout prescriptions                       │
│ • Strategic context (why each workout matters)          │
│ • Weekly ACWR/divergence predictions                     │
│                                                          │
│ To build weekly programs, I need to know WHEN you can   │
│ train:                                                   │
│                                                          │
│ Which days are you available?                            │
│ ☑ Monday    ☑ Tuesday   ☑ Wednesday                      │
│ ☐ Thursday  ☑ Friday    ☑ Saturday   ☑ Sunday           │
│                                                          │
│ Long run day (90+ minutes):                              │
│ ○ Saturday  ● Sunday                                     │
│                                                          │
│ Hours per week available: [8-10] hours                   │
│                                                          │
│ Any constraints?                                         │
│ [Can't run before 6am, need Wed < 60min]               │
│                                                          │
│ [Generate My First Weekly Program →]                     │
│ [Skip - Keep Daily Recommendations Only]                │
└─────────────────────────────────────────────────────────┘
```

**Key Elements:**
- ✅ CONTEXT: Shows their race goal
- ✅ COMPARISON: Daily vs Weekly programs
- ✅ SIMPLE FORM: Quick checkboxes, not complex time blocks
- ✅ OPTIONAL: Can stick with daily recommendations
- ✅ IMMEDIATE PAYOFF: Generate program right away

**Data Collected:**
- Available days
- Long run day
- Weekly hours
- Constraints (optional)
- (Can add strength/mobility preferences here or later)

**Success Metric:** 40%+ of users with race goals configure schedule within 14 days

---

### STAGE 6: Weekly Training Programs (FULL EXPERIENCE)

**User State:**
- Has schedule configured
- Has race goal (or not - can still generate)
- Ready for structured 7-day plans

**What Happens:**
Immediately after schedule configuration:

```
┌─────────────────────────────────────────────────────────┐
│ 🎓 Generating Your First Weekly Training Program...     │
│                                                          │
│ [Loading Animation]                                      │
│                                                          │
│ Analyzing your training history...                       ✓│
│ Calculating optimal periodization for Moab 55k...       ✓│
│ Accounting for your "goes harder than prescribed"       ✓│
│ pattern...                                               │
│ Building 7-day program for week of Jan 6-12...          ⏳│
│                                                          │
│ This takes 30-60 seconds.                                │
└─────────────────────────────────────────────────────────┘
```

**Then:**
User sees full 7-day program with:
- Daily workout cards (type, distance, duration, intensity, rationale)
- Weekly strategic context (periodization, load management)
- Predicted ACWR for the week
- Key workout highlights

**Success Metric:** 35%+ of users with schedule generate weekly program

---

### STAGE 7: Power User (ONGOING ENGAGEMENT)

**Behaviors:**
- Weekly program generation (or daily recommendations)
- Regular journal entries (2-3+ per week)
- Occasional settings adjustments
- Active race goal management

**Retention Mechanics:**
- Sunday evening: "Review this week's performance, generate next week"
- Daily: Updated recommendation based on autopsy learning
- Weekly: ACWR/divergence trend alerts
- Monthly: Progress report toward race goal

**Success Metric:** 15%+ users are "power users" (weekly engagement) at 90 days

---

## 6. IMPLEMENTATION PRIORITY

### Phase 1: Daily Recommendation Prominence (Week 1)
**Goal:** Make daily recommendation the FIRST thing users see

**Tasks:**
1. Move daily recommendation to top of dashboard (above charts)
2. Make it visually prominent (large banner)
3. Add "Improve Accuracy" CTA that links to profile form
4. Show accuracy percentage (65% → 95% with HR data)

**Success Metric:** 100% of dashboard visits see daily recommendation first

---

### Phase 2: Motivational Profile Completion (Week 1)
**Goal:** Convert "Improve Accuracy" clicks to completed profiles

**Tasks:**
1. Create "Improve Your Recommendations" modal/page
2. Show before/after examples with user's actual data
3. Make form dead simple (4 fields, 45 seconds)
4. Show real-time accuracy improvement as they type

**Success Metric:** 75%+ complete profile within 48 hours

---

### Phase 3: Autopsy Enhancement (Week 2)
**Goal:** Make Stage 2 autopsy incredibly compelling

**Tasks:**
1. Enhance autopsy prompt to be more specific
2. Add pattern detection from day 1
3. Show exact ACWR impact with predictions
4. Explain learning integration explicitly
5. Update tomorrow's recommendation based on autopsy

**Success Metric:** 50%+ who log one entry log second within 7 days

---

### Phase 4: Progressive CTAs (Week 3)
**Goal:** Guide users through stages 3-6

**Tasks:**
1. Implement stage detection logic
2. Create 7 CTA variants
3. Use actual user data in CTAs
4. Add YTM Progress Meter (Stage 2 of 7)

**Success Metric:** 40%+ reach Stage 6 within 30 days

---

## 7. YTM PROGRESS METER

Visual progress indicator showing feature adoption:

```
┌─────────────────────────────────────────────────────────┐
│ Your YTM Progress                                        │
│                                                          │
│ ✅ Connected Strava                                      │
│ ✅ Receiving daily recommendations                       │
│ ✅ Logged first workout (autopsy activated!)            │
│ ⏳ Personalize AI coaching style                         │
│ ⏹️ Add race goal                                         │
│ ⏹️ Configure training schedule                           │
│ ⏹️ Generate weekly training program                      │
│                                                          │
│ Progress: ███████░░░░░░ 3/7 Complete                     │
│                                                          │
│ Next: Personalize your AI coach →                        │
└─────────────────────────────────────────────────────────┘
```

**Placement:** Collapsible section in dashboard sidebar or settings page

**Gamification:**
- Show percentage complete
- Celebrate completions
- Show benefits unlocked at each stage
- Optional: Hide after Stage 7 completion (can show "Power User" badge)

---

## 8. SUCCESS METRICS

### 8.1 Immediate Metrics (Week 1-2)

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| Daily recommendation visibility | Unknown | 100% | % dashboard views with recommendation shown |
| Profile completion rate | ~60% | 75%+ | % users with HR/age/gender filled within 48h |
| Time to first journal entry | Unknown | <3 days | Median days from signup to first entry |

### 8.2 Engagement Metrics (Week 3-8)

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| Journal adoption | ~5% | 50%+ | % users with 1+ journal entries |
| Repeat journal usage | Unknown | 50%+ | % who log 2nd entry within 7 days of first |
| Settings personalization | ~10% | 40%+ | % users who change coaching style |
| Race goal adoption | ~5% | 30%+ | % users with 1+ race goals |

### 8.3 Advanced Feature Adoption (Month 2-3)

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| Schedule configuration | ~20% | 40%+ | % users with training schedule configured |
| Weekly program generation | ~10% | 35%+ | % users who generate 1+ weekly program |
| Power user status | ~2% | 15%+ | % users with weekly engagement at 90 days |

### 8.4 Business Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| 7-day retention | 70%+ | % users active on day 7 |
| 30-day retention | 50%+ | % users active on day 30 |
| 90-day retention | 35%+ | % users active on day 90 |

---

## 9. DESIGN DECISIONS (RESOLVED)

### 9.1 Primary Sport Screening
**Decision:** Emphasize on landing page BEFORE Strava connection

**Rationale:**
- Attracts serious trail runners (target audience)
- Filters out casual runners early (reduces database clutter)
- Sets expectations for technical depth
- No wasted user investment if they're not target audience

**Implementation:**
- Landing page headline: "AI-Powered Training Intelligence for Serious Trail Runners"
- Value prop focused on trail-specific features (elevation gain, technical terrain, vertical load)
- Can still support road runners, but messaging is clear about focus

---

### 9.2 Daily Recommendations with Minimal Data
**Decision:** Show recommendations immediately using calculated max HR from age

**Rationale:**
- Max HR can be calculated: 220 - age (or more sophisticated formulas)
- With age + calculated max HR, we can provide HR zone analysis
- Accuracy: ~75% (good enough to show value)
- Motivates users to add resting HR for 95% accuracy

**Implementation:**
- Stage 0: Require age/gender during Strava OAuth or immediately after
- Calculate max HR automatically
- Show daily recommendation with note: "Using calculated max HR. Add resting HR for better accuracy."
- Stage 1 becomes: "Improve from 75% to 95% accuracy by adding resting HR"

---

### 9.3 Journal Entry Prompting Strategy
**Decision:** Prompt ONLY after workouts where YTM gave a recommendation

**Rationale:**
- We want to close the loop on OUR recommendations (prescribed vs actual)
- Don't need to track random workouts YTM didn't recommend
- Keeps autopsy focused and relevant
- Reduces prompt fatigue

**Implementation:**
- Track which activities had a YTM daily recommendation
- Next morning after that workout: "You did X yesterday. I recommended Y. How did it go?"
- Don't prompt for activities without prior recommendation (user can manually add journal entry if desired)

---

### 9.4 Autopsy Depth and Technical Detail
**Decision:** Deep, technical, sophisticated analysis - do NOT dumb it down

**Rationale:**
- Target audience: Serious trail runners who already use Garmin/Coros
- They WANT deep analysis - that's why they're here
- Competitors (Garmin/Coros) are for beginners
- YTM differentiates on depth, not simplicity

**Autopsy Must Include:**
- Exact TRIMP scores (expected vs actual, with delta)
- Precise ACWR calculations (before/after with change)
- HR zone breakdown (% time in each zone vs prescribed)
- Elevation gain impact on load
- Pattern detection with historical context ("3rd consecutive time...")
- Specific predictions ("If you rest tomorrow, ACWR drops to 1.18 by Sunday")
- Technical terminology (don't say "effort level", say "TRIMP", "Zone 3", "lactate threshold")

**Example Language:**
❌ Beginner: "You went a bit harder than suggested"
✅ Technical: "HR averaged 162 bpm (78% max) - this is Zone 3. Prescribed was Zone 2 (68-74% max). This increased your TRIMP from expected 98 to actual 124 (+27% overage)."

---

### 9.5 Stage Progression Timing
**Decision:** Context-driven, not time-driven

**Timing:**
- Stage 0 → 1: Immediately (show limitation in first recommendation)
- Stage 1 → 2: After 2-3 days of seeing recommendations
- Stage 2 → 3: After 2-3 autopsy cycles
- Stage 3 → 4: After 1-2 weeks of engagement
- Stage 4 → 5: Immediately after race goal added
- Stage 5 → 6: Immediately after schedule configured

**No arbitrary time gates** - progression is based on engagement, not days elapsed

---

### 9.6 Skip Behavior
**Decision:** Allow skips for non-blocking stages, show benefits at each stage

**Strategy:**
- Blocking stages (Stage 0: age/gender): Cannot skip - required for recommendations
- Enhancement stages (Stage 2: journal): Can skip - show what they're missing
- Structure stages (Stage 4-5: goals/schedule): Can skip - daily recommendations still work

**Re-prompting:**
- If skipped: Show in YTM Progress Meter as "○ Skipped: Journal entry"
- Occasional reminder CTAs (weekly): "You're missing autopsy learning - here's what others get from it"
- No nagging - respect user choice

---

## 10. OPEN QUESTIONS (REMAINING)

1. **Age/Gender Collection Timing:**
   - Immediately after Strava OAuth (redirect to quick form)?
   - During OAuth flow (custom page)?
   - First dashboard visit (modal)?

2. **Calculated vs Actual Max HR:**
   - Should we test actual max HR in field (prompt after hard workout: "Was that your max effort? This could be your max HR")?
   - Or rely on user to provide it manually?

3. **Trail vs Road Runner Accommodation:**
   - Landing page emphasizes trail runners
   - But road runners can still use it
   - Should we have separate landing pages? Or single page with "Primarily for trail runners, but road runners welcome"?

4. **Autopsy Learning Display:**
   - Should we show a "learning history" of all patterns detected?
   - Or keep it ephemeral (only in each autopsy)?
   - Risk: History could be powerful social proof, but also overwhelming

---

## 10. NEXT STEPS

**Immediate (This Session):**
1. ✅ Review revised PRD
2. ⏳ Validate stage order
3. ⏳ Confirm primary sport screening strategy
4. ⏳ Approve for implementation

**Week 1 (Foundation):**
1. Implement daily recommendation prominence
2. Create "Improve Accuracy" motivation flow
3. Simplify profile completion form

**Week 2 (Autopsy):**
1. Enhance autopsy analysis prompts
2. Add pattern detection from day 1
3. Show learning integration explicitly

**Week 3 (Progressive CTAs):**
1. Implement stage detection
2. Create 7 CTA variants
3. Add YTM Progress Meter

**Week 4 (Optimization):**
1. A/B test CTA copy
2. Analyze funnel drop-off
3. Iterate based on data

---

**END OF PRD - Ready for Review**
