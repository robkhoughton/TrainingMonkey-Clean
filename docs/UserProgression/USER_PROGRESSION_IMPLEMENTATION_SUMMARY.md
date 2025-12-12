# User Progression Implementation Summary

**Status:** Ready for Implementation
**Last Updated:** 2025-01-04

---

## CRITICAL DECISIONS (FINALIZED)

### 1. Product Positioning
✅ **YTM is for SERIOUS TRAIL RUNNERS**
- Not a beginner app (Garmin/Coros handle that)
- Technical, deep analysis for athletes who want MORE
- Landing page emphasizes trail running focus upfront
- Filters out casual users early = less database clutter

### 2. Minimal Data for Value
✅ **Calculate Max HR from Age**
- Stage 0 requires: Age + Gender only
- Max HR = 220 - age (sufficient for initial recommendations)
- 75% accuracy with calculated max HR → 95% with resting HR
- Users see value immediately, THEN motivated to improve

### 3. Journal Prompting Strategy
✅ **Prompt ONLY after YTM recommendations**
- Track which activities had a YTM daily recommendation
- Next day: "I recommended X. You did Y. How did it go?"
- Don't prompt for random workouts without prior recommendation
- Closes the prescribed → actual → autopsy loop

### 4. Autopsy Depth
✅ **Deep, Technical, Sophisticated**
- Target audience: Serious athletes with Garmin/Coros
- Use technical terminology: TRIMP, Zone 3, lactate threshold
- Include exact numbers: "TRIMP 124 vs 98 expected (+27% overage)"
- Show pattern detection: "3rd consecutive time..."
- Predict future: "If you rest tomorrow, ACWR drops to 1.18"
- **Do NOT dumb it down**

---

## REVISED USER PROGRESSION

```
STAGE 0: Daily Recommendation (immediate value)
         Prerequisites: Age + Gender → Calculate Max HR → Show recommendation
         ↓
STAGE 1: Add Resting HR (improve accuracy 75% → 95%)
         15 seconds, optional
         ↓
STAGE 2: Log Workout → AI Autopsy (AHA MOMENT)
         30 seconds, only for workouts with prior recommendation
         ↓
STAGE 3: Personalize AI Style (after seeing it work)
         30 seconds, coaching tone + risk tolerance
         ↓
STAGE 4: Add Race Goal (training purpose)
         1 minute, unlocks periodization
         ↓
STAGE 5: Configure Schedule (commitment)
         2 minutes, unlocks weekly programs
         ↓
STAGE 6: Generate Weekly Program (full experience)
         90 seconds generation time
         ↓
STAGE 7: Power User (ongoing engagement)
```

---

## IMPLEMENTATION PHASES

### Phase 1: Age/Gender Collection + Daily Rec Prominence (Week 1)

**Goal:** Every user sees daily recommendation on first dashboard visit

**Tasks:**
1. **Age/Gender Collection Flow:**
   - After Strava OAuth, redirect to quick form: "Two quick questions to personalize your experience"
   - Fields: Age (___), Gender (M/F/Other)
   - Takes 10 seconds
   - Store in user_settings table

2. **Calculate Max HR:**
   - Backend function: `calculate_max_hr(age, gender)`
   - Formula: 220 - age (or Tanaka: 208 - 0.7 * age for more accuracy)
   - Store as `calculated_max_hr` in user_settings
   - Flag: `max_hr_is_calculated = True`

3. **Daily Recommendation Prominence:**
   - Move daily recommendation to TOP of dashboard (above charts)
   - Large banner style (impossible to miss)
   - Show note: "Using calculated max HR (220 - age = X bpm)"
   - Two CTAs: [Tell Me How It Went] [Improve Accuracy]

**Success Metrics:**
- 100% users provide age/gender before seeing dashboard
- 100% users see daily recommendation on first visit
- Baseline accuracy shown: 75%

---

### Phase 2: Resting HR Motivation (Week 1)

**Goal:** Convert "Improve Accuracy" clicks to resting HR additions

**Tasks:**
1. **"Improve Accuracy" Modal/Page:**
   - Current: 75% (calculated max HR)
   - Potential: 95% (with resting HR)
   - Form: 2 fields (Resting HR required, Actual Max HR optional)
   - Takes 15 seconds
   - Show before/after example with user's actual data

2. **Store HR Data:**
   - `resting_hr` in user_settings
   - `max_hr` in user_settings (if provided)
   - If max_hr provided, set `max_hr_is_calculated = False`
   - Recalculate HR zones immediately

3. **Update Daily Recommendation:**
   - Remove "Using calculated max HR" note
   - Show "Accuracy: 95%" badge
   - More confident language in recommendations

**Success Metrics:**
- 60%+ add resting HR within 48 hours
- Accuracy improvement visible in dashboard

---

### Phase 3: Autopsy Enhancement (Week 2)

**Goal:** Make Stage 2 autopsy incredibly impressive and technical

**Tasks:**
1. **Track Recommendation → Activity Link:**
   - New table: `recommendation_activity_links`
   - Columns: recommendation_id, activity_id, recommendation_date, activity_date
   - Links daily recommendations to actual Strava activities

2. **Prompt Only for Tracked Activities:**
   - Next day after activity: Check if YTM gave recommendation
   - If yes: Show journal prompt with specific comparison
   - If no: Don't prompt (user can manually add journal entry)

3. **Enhanced Autopsy Prompt:**
   ```
   You are analyzing a trail runner's workout performance. This athlete is
   SERIOUS - they use Garmin/Coros already and want DEEP analysis.

   Prescribed workout: {recommendation}
   Actual workout: {activity data + journal entry}

   Provide technical analysis including:
   - Exact TRIMP comparison (expected vs actual with delta and %)
   - Precise ACWR impact (before/after with change)
   - HR zone breakdown (% time in each zone vs prescribed)
   - Elevation gain impact on load (for trail runs)
   - Pattern detection with historical context
   - Specific predictions for next workout

   Use technical terminology. Be specific. Show your work.
   ```

4. **Autopsy Display Format:**
   - Alignment Score: X/10
   - Pattern Detection (from day 1)
   - Training Load Impact (TRIMP, ACWR with exact numbers)
   - Adjustment for Tomorrow (specific changes)
   - Learning Integration (explicit explanation of what AI learned)

**Success Metrics:**
- 50%+ who log one entry log second within 7 days
- Autopsy includes specific patterns by 3rd entry
- Users mention autopsy in feedback/support

---

### Phase 4: Progressive CTAs (Week 3)

**Goal:** Guide users through Stages 3-6 with personalized CTAs

**Tasks:**
1. **Stage Detection Function:**
   ```python
   def get_user_stage(user_id):
       # Check Stage 0: Age/gender provided?
       # Check Stage 1: Resting HR provided?
       # Check Stage 2: Journal entries count
       # Check Stage 3: Coaching style personalized?
       # Check Stage 4: Race goals count
       # Check Stage 5: Training schedule configured?
       # Check Stage 6: Weekly programs generated?
       return stage_number, next_action, cta_data
   ```

2. **CTA Variants (7 total):**
   - Stage 1: Improve Accuracy (resting HR)
   - Stage 2: Log First Workout (journal + autopsy)
   - Stage 3: Personalize AI Style (coaching tone)
   - Stage 4: Add Race Goal (training purpose)
   - Stage 5: Configure Schedule (weekly programs unlock)
   - Stage 6: Generate Weekly Program (first program)
   - Stage 7: Keep Going (power user encouragement)

3. **YTM Progress Meter:**
   - Visual progress indicator (3/7 complete)
   - Checkmarks for completed stages
   - Next stage highlighted
   - Show in dashboard sidebar or settings

**Success Metrics:**
- 40%+ reach Stage 6 within 30 days
- CTR >30% for each stage CTA
- Drop-off analysis by stage

---

### Phase 5: Landing Page Update (Week 4)

**Goal:** Emphasize trail running focus upfront

**Tasks:**
1. **Headline:**
   - "AI-Powered Training Intelligence for Serious Trail Runners"
   - Or: "The AI Coach That Learns Your Trail Running Patterns"

2. **Value Props:**
   - Elevation gain analysis (trail-specific)
   - Technical terrain stress modeling
   - Vertical load optimization
   - Patent-pending divergence analysis

3. **Social Proof:**
   - "Built by trail runners, for trail runners"
   - "Not your average training app - this is for athletes who want MORE"

4. **Filtering:**
   - Clearly state: "Designed for serious trail runners"
   - Note: "Road runners welcome, but trail focus"
   - Sets expectations for technical depth

**Success Metrics:**
- Increased % of trail runner signups
- Decreased % of "not for me" early drop-offs
- Clearer target audience

---

## TECHNICAL IMPLEMENTATION NOTES

### Database Changes Required

```sql
-- Add calculated max HR flag
ALTER TABLE user_settings
ADD COLUMN max_hr_is_calculated BOOLEAN DEFAULT FALSE,
ADD COLUMN calculated_max_hr INTEGER;

-- Track recommendation → activity links
CREATE TABLE recommendation_activity_links (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES user_settings(id),
    recommendation_date DATE NOT NULL,
    activity_id BIGINT REFERENCES activities(id),
    activity_date DATE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index for fast lookups
CREATE INDEX idx_rec_activity_user_date
ON recommendation_activity_links(user_id, activity_date);
```

### Backend Functions

```python
# Calculate max HR from age
def calculate_max_hr(age, gender=None):
    """
    Calculate estimated max HR from age.
    Options:
    - Simple: 220 - age
    - Tanaka: 208 - (0.7 * age) [more accurate]
    - Gender-specific adjustments possible
    """
    return 208 - (0.7 * age)  # Tanaka formula

# Check if should prompt for journal entry
def should_prompt_journal(user_id, activity_id):
    """
    Only prompt if YTM gave recommendation before this activity
    """
    return recommendation_activity_links.exists(
        user_id=user_id,
        activity_id=activity_id
    )

# Get user progression stage
def get_user_stage(user_id):
    """
    Determine which stage user is at and what CTA to show
    """
    # Implementation per Phase 4
    pass
```

### Frontend Components

```typescript
// Progressive CTA component
<ProgressiveCTA
  stage={userStage}
  userData={metrics}
  onCtaClick={handleStageAction}
/>

// YTM Progress Meter
<ProgressMeter
  completedStages={[0,1,2]}
  currentStage={3}
  totalStages={7}
/>

// Daily Recommendation Banner (prominent)
<DailyRecBanner
  recommendation={dailyRec}
  accuracy={75 | 95}
  usingCalculatedMaxHR={true | false}
/>
```

---

## SUCCESS METRICS SUMMARY

### Week 1-2 (Foundation)
- 100% users see daily recommendation on first visit ✓
- 60%+ add resting HR within 48 hours
- Baseline engagement established

### Week 3-4 (Engagement)
- 50%+ log first journal entry within 7 days
- 40%+ personalize settings within 14 days
- 30%+ add race goal within 30 days

### Month 2-3 (Advanced Features)
- 40%+ configure schedule
- 35%+ generate weekly program
- 15%+ become power users (weekly engagement)

### Business Metrics
- 7-day retention: 70%+
- 30-day retention: 50%+
- 90-day retention: 35%+

---

## RISKS & MITIGATIONS

### Risk: Calculated Max HR Too Inaccurate
**Mitigation:**
- Use Tanaka formula (more accurate than 220-age)
- Prompt after hard workouts: "Was that max effort? Detected 175 bpm - update max HR?"
- Show accuracy % so users know it's estimated
- Make resting HR addition very easy

### Risk: Users Skip Journal Entirely
**Mitigation:**
- Make autopsy incredibly impressive (word of mouth)
- Show progress meter with journal as key unlock
- Occasional reminders: "Missing autopsy learning - here's what you're missing"
- Don't nag - respect choice

### Risk: Landing Page Filters Out Too Many Users
**Mitigation:**
- Track signup conversion rate
- A/B test: "For serious trail runners" vs "For trail and road runners"
- Note: "Road runners welcome" to soften
- Focus is a FEATURE - attracts right users

---

## NEXT ACTIONS

**This Week:**
1. Review and approve this implementation plan
2. Prioritize phases (recommend: 1 → 2 → 3 → 4)
3. Set up tracking/analytics for metrics
4. Begin Phase 1 implementation

**Questions Answered:**
1. ✅ Age/gender collection: Already part of onboarding process after OAuth
2. ✅ Calculated max HR formula: **Tanaka (208 - 0.7 * age)** - more accurate
3. ✅ Landing page update: No urgency, backlog item to remember
4. ✅ Analytics setup: **Google Analytics**

---

**END OF SUMMARY - Ready to Build**
