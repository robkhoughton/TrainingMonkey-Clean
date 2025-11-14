# Product Requirements Document: YTM Coach Page

## Executive Summary

**Core Value Proposition**: Leverage TrainingMonkey's unique divergence-based training load analysis to provide **intelligent, personalized weekly training programming** that optimizes ACWR while respecting the user's real-world schedule constraints.

**Strategic Focus**: V1 focuses exclusively on **divergence-based training programming** - our core competency and competitive differentiator. Nutrition, race strategy, and mental preparation are deferred to future phases.

**Key Innovation**: First training platform to combine:
1. Sophisticated divergence/ACWR prediction and optimization
2. User's actual schedule availability (work, family, life constraints)
3. Race periodization (A/B/C goal hierarchy)
4. LLM-powered weekly training programs that balance load management with real-world feasibility

## Introduction/Overview

The **YTM Coach** page addresses a critical gap in the TrainingMonkey application: while the Dashboard shows current training status and the Journal provides daily workout decisions, users lack visibility into their long-term training horizon and **practical week-ahead planning**.

**Problem**: Users know what to do today, but don't know how to structure their upcoming week to optimize divergence while fitting training into their busy lives. They lose sight of the bigger picture when focused on daily workouts, leading to uncertainty about whether their training approach aligns with their race goals.

**Solution**: A divergence-focused coaching page that:
- Displays training goals (A/B/C race hierarchy) and periodized timeline
- Collects user's weekly schedule availability and constraints
- Generates intelligent 7-day training programs optimized for ACWR/divergence management
- Predicts end-of-week metrics based on planned training
- Adapts to user's real-world schedule (work, family, sleep, etc.)
- Includes supplemental training (strength, mobility, cross-training) within total weekly hours

## Goals

1. **Deliver Divergence-Optimized Weekly Training Programs**: Generate intelligent 7-day training schedules that optimize ACWR and divergence while respecting user's real-world availability
2. **Enable Practical Schedule Integration**: Collect and incorporate user's training availability, time blocks, and life constraints (work, family, sleep) into training recommendations
3. **Provide Training Horizon Visibility**: Give users confidence that their current training trajectory aligns with their race goals through periodized timeline visualization
4. **Enable Race Goal Management**: Support the A/B/C race hierarchy typical of trail runners (A race as season focus, B races for evaluation, C races as training volume)
5. **Identify Training Stages**: Use LLM analysis to determine and communicate current training stage (base, build, specificity, taper, recovery)
6. **Consolidate Training Intelligence**: Move existing Dashboard LLM recommendations (daily/weekly/pattern) to Coach page alongside new weekly programming feature
7. **Include Supplemental Training**: Account for strength, mobility, and cross-training within total weekly training hours and divergence calculations

## Functional Requirements

### Race/Goal Management
1. The system must allow users to create multiple race goals with the following attributes:
   - Race name
   - Race date
   - Race type/distance (e.g., "50K Trail", "100 Mile Ultra")
   - Priority classification: A (season focus), B (evaluation), or C (training volume)
   - Target goal time (optional)
   - Race location/notes (optional)

2. The system must display all upcoming races sorted by date
3. The system must allow users to edit and delete race goals
4. The system must identify the primary "A race" as the anchor for periodization
5. The system must store race goals in the database with user_id isolation

### Timeline Visualization
6. The system must display a horizontal timeline marked in weeks
7. The timeline must show distinct training stage zones (base, build, specificity, taper, recovery) with visual differentiation
8. The timeline must indicate the user's current position on the timeline with a clear marker ("You Are Here")
9. The timeline must span from the current date to the A race date (minimum 4 weeks, maximum 52 weeks displayed)
10. The timeline must show B and C races as markers on the timeline within their respective stages

### Countdown & Status
11. The system must display days remaining until the A race prominently at the top of the page
12. The system must display the current training stage name (e.g., "Week 8 of 16 - Build Phase")
13. The system must show weeks remaining in the current stage and weeks remaining until race day

### Training Stage Determination
14. The system must use LLM analysis of recent workouts, ACWR, TRIMP trends, and time-to-race to recommend the current training stage
15. The system must allow users to manually override the LLM-recommended stage if needed
16. The system must update training stage recommendations when journal entries are saved or when significant training data changes
17. Valid training stages must include: Base, Build, Specificity (Race Prep), Taper, Peak Week, Recovery

### LLM Coaching Recommendations
18. The system must move the following LLM recommendations from Dashboard to Coach page:
    - **Daily Training Decision** (currently in "Training Recommendations & Analysis" section on Dashboard)
    - **Weekly Training Recommendation** (pattern analysis)
    - **Pattern Insights** (weekly trends)
19. The system must preserve existing recommendation functionality (auto-generation at 6 AM UTC, autopsy-informed decisions)
20. The system must add new coaching section to Coach page:
    - **Weekly Training Program**: Divergence-based training schedule for the next 7 days, integrating user's available training hours, schedule constraints, and current training stage
21. The Weekly Training Program must:
    - Recommend specific training days based on user's availability schedule
    - Suggest training volume/intensity for each day based on divergence trends
    - Balance training load to optimize ACWR and avoid overtraining
    - Account for race timeline and current training stage
    - Include supplemental work (strength, mobility) within total weekly hours
    - Predict end-of-week divergence based on planned training
22. Each coaching section must be generated by Claude API with context from user's training data, race goals, current stage, and schedule
23. The system must display coaching recommendations in collapsible/expandable sections
24. The system must minimize API calls by caching coaching recommendations appropriately (see Performance Considerations)
25. **Journal Page Unchanged**: Daily training decisions for "tomorrow's workout" remain on Journal page as currently implemented

### Data Integration
26. The system must integrate all existing data sources:
    - User's recent training load and ACWR metrics
    - Historical performance data (PRs, past race results if available)
    - Current fitness trends from Dashboard (7-day/28-day averages, normalized divergence)
    - Journal observations (energy, RPE, pain, notes)
27. The system must accept manual user inputs for race goals (name, date, type, target time)
28. The system must accept user schedule inputs for weekly training programming:
    - Total weekly training hours available (including supplemental work)
    - Training availability by day of week (which days user can train)
    - Time blocks available per day (morning/midday/evening)
    - Fixed schedule constraints (work hours, family commitments, sleep schedule)
29. The system must calculate training stage boundaries based on A race date and LLM recommendations

### Additional User Inputs for Divergence-Based Training Programming

**Currently Collected (Existing):**
- Age, gender (Profile Settings)
- Resting HR, Max HR (HR Zones Settings)
- Primary sport, secondary sport (Training Settings)
- Training experience level (beginner/intermediate/advanced/elite)
- Weekly training hours (basic total)
- Current training phase (base/build/peak/race/recovery)
- Single race goal date
- Coaching style preference (casual to analytical)

**New Inputs Required for Coach Page (Essential - V1):**

1. **Multiple Race Goals**: 
   - Race name, date, type/distance, priority (A/B/C), target time/goal
   - Replaces single `race_goal_date` field

2. **Race History** (Critical for performance trend and base fitness assessment):
   - **Past Race Results** (last 5 years only):
     - Race name
     - Distance (in miles)
     - Race date
     - Finish time (minutes)
   
   **Input Methods:**
   - **Manual Entry**: 4-field form for adding individual races
   - **Screenshot Upload** (V1 Feature): Upload ultrasignup.com race history screenshot
     - User uploads one screenshot from ultrasignup.com
     - Claude Vision API parses race data from screenshot
     - Extracted data displayed in review table for user verification
     - User can edit any extracted fields before saving
     - Bulk save confirmed races to race_history table
     - Error handling: If extraction fails, falls back to manual entry
     - **Note**: Ultrasignup.com does not provide a public API (verified 2025-11-14), so screenshot parsing is the optimal automated solution
   
   **Why Critical:**
   - **Performance Trend**: Are they improving, plateauing, or declining?
   - **Base Fitness Assessment**: What volume/intensity can their body handle?
   - **Training Capacity**: Historical performance reveals sustainable training load
   - **Realistic Goal Setting**: Recent race history validates future race goals
   
   **Simple, focused data** - No fluff, just the facts needed to understand athlete trajectory and capacity

3. **Weekly Training Schedule & Availability**:
   - **Total weekly hours available**: Refined input including supplemental work (strength, mobility, cross-training)
   - **Training day availability**: Which days of the week user can train (Monday-Sunday checkboxes)
   - **Preferred training times per day**: Morning (5am-9am), Midday (9am-5pm), Evening (5pm-9pm), Night (9pm-12am)
   - **Fixed schedule constraints**: 
     - Work/school hours (e.g., "Monday-Friday 9am-5pm")
     - Family commitments (e.g., "Pick up kids 3pm weekdays")
     - Sleep schedule (e.g., "Must sleep by 10pm")
     - Other recurring obligations

3. **Supplemental Training Preferences**:
   - Include strength training (Y/N, hours per week)
   - Include mobility/yoga (Y/N, hours per week)
   - Include cross-training (Y/N, type, hours per week)

**Implementation Approach:**
- **Initial Setup Interview**: When user first visits Coach page, show onboarding flow that collects:
  1. Race goals (future races with A/B/C priority)
  2. Race history (past race results from last 5 years) - Optional but strongly encouraged
     - Option A: Upload ultrasignup.com screenshot (recommended for users with extensive history)
     - Option B: Manual entry (4-field form)
  3. Training schedule (availability, constraints, supplemental training)
- **Editable Profiles**: 
  - "Edit Race Goals" button for managing future races
  - "Add Race Result" button with two options:
    - "Upload Screenshot" for ultrasignup.com parsing
    - "Manual Entry" for 4-field form
  - "Edit Training Schedule" button for availability/constraints
- **Auto-Calculated Insights**: PRs, trends, and base fitness are calculated automatically from race history - no manual entry needed
- **Smart Defaults**: If schedule not provided, use existing `weekly_training_hours` and assume 5 days/week availability
- **Progressive Disclosure**: 
  - Start with essential inputs (race goals, basic schedule)
  - Encourage race history ("Add past races to improve recommendations")
  - Expand to detailed constraints if user wants precise programming

**Data Storage:**
- New fields in `user_settings` table: 
  - `training_schedule_json` (JSONB): Stores availability, time blocks, constraints
  - `include_strength_training` (BOOLEAN)
  - `strength_hours_per_week` (REAL)
  - `include_mobility` (BOOLEAN)
  - `mobility_hours_per_week` (REAL)
  - `include_cross_training` (BOOLEAN)
  - `cross_training_type` (VARCHAR)
  - `cross_training_hours_per_week` (REAL)

**Future Enhancements (V2+):**
- Injury/limitation history for safety constraints
- Terrain access for workout type recommendations  
- Automatic race result import from Strava (V1 uses ultrasignup.com screenshot + manual entry)
- Multiple screenshot uploads in one batch (V1 supports one screenshot at a time)
- Screenshot parsing for other platforms (Athlinks, Strava profile, etc.)
- **Ultrasignup.com API Partnership** (if they develop API or partnership program in future)
- Race performance prediction calculator based on recent training + planned workouts
- Nutrition guidance (deferred)
- Race strategy & pacing plans (deferred)
- Mental preparation & race-day confidence building (deferred)

### User Interaction & Feedback
29. The system must allow users to add/edit/delete race goals (future races) through a form interface
30. The system must allow users to add/edit/delete race history (past races) through:
    - **Manual Entry**: Simple 4-field form (race name, distance, date, finish time)
    - **Screenshot Upload**: Upload ultrasignup.com screenshot workflow:
      1. User clicks "Upload Ultrasignup Screenshot" button
      2. File picker allows PNG, JPG, JPEG, WebP (max 5MB)
      3. Frontend shows loading indicator while processing
      4. Backend sends image to Claude Vision API for parsing
      5. Extracted races displayed in editable review table
      6. User can edit any field or remove races before saving
      7. User clicks "Save All" to bulk insert to race_history table
      8. If extraction fails, show error and offer manual entry
    - Automatically filtered to last 5 years for both methods
31. The system must calculate and display performance metrics from race history:
    - PRs at each distance (auto-calculated, no manual entry needed)
    - Performance trend (improving/stable/declining based on recent race times)
    - Base fitness assessment (volume/intensity capacity from historical performance)
32. The system must provide a feedback mechanism for coaching recommendations (helpful/not helpful thumbs up/down)
33. The system must allow users to manually request fresh coaching recommendations via a "Regenerate Training Program" button
34. The system must display performance insights derived from race history in weekly training program (e.g., "Based on your 50K PR of 5:30, this week's long run pace is calibrated for your 100K goal")
35. The system must include an optional LLM chat interface for asking specific coaching questions (future enhancement - out of scope for v1)

### Navigation & Integration
36. The system must add a "Coach" tab to the main navigation between "Journal" and "Guide"
37. The system must update the Dashboard to remove LLM recommendations section and add a link: "View full coaching analysis on Coach page"

## Non-Goals (Out of Scope)

### V1 Out of Scope (Future Phases)
1. **Nutrition Guidance**: Deferred to V2+ (not core competency)
2. **Race Strategy & Pacing**: Deferred to V2+ (focus on training load management first)
3. **Mental Preparation**: Deferred to V2+ (focus on divergence-based programming first)
4. **Structured Workout Builder**: Not creating specific interval/tempo workout prescriptions (volume/intensity guidance only)
5. **Training Plan Templates**: Not providing pre-built training plans (e.g., "16-week marathon plan")
6. **Social/Sharing Features**: No sharing of goals or comparing with other users
7. **Mobile Native App**: Web-only implementation; mobile app is a future roadmap item
8. **Race Result Importing**: Not automatically pulling race results from external platforms
9. **Multi-User Coaching**: Not supporting coach-athlete relationships or team management
10. **Real-Time Chat**: LLM chat interface is a future enhancement, not included in v1
11. **Calendar Integration**: Not syncing with Google Calendar, Apple Calendar, etc.
12. **Workout Library**: Not providing a searchable database of workouts
13. **Journal Page Changes**: Daily training decisions remain on Journal page unchanged; no modifications to Journal workflow

## Design Considerations

### Layout Priority (Top to Bottom)
1. **Header**: Page title "Your Training Monkey Coach" with tagline "Divergence-Based Training Programming"
2. **Countdown Banner**: Prominent display of days to A race with current training stage
3. **Timeline Visualization**: Horizontal week-by-week timeline with stage zones and position marker
4. **Race Goals & History Card**: 
   - **Upcoming Races**: List of all races (A/B/C) with add/edit buttons
   - **Race History**: Simple table of past races (last 5 years) with "Add Race Result" button
     - Columns: Date, Race Name, Distance, Finish Time
   - **Performance Summary**: Auto-calculated from race history
     - Recent PRs at key distances
     - Performance trend indicator (↗️ improving, → stable, ↘️ declining)
     - Base fitness assessment
5. **Training Schedule Profile**: Current availability, weekly hours, constraints (with "Edit Schedule" button)
6. **Weekly Training Program (Primary Focus)**: Divergence-optimized 7-day training schedule showing:
   - Day-by-day training recommendations
   - Volume/intensity for each day based on current divergence
   - Rest days strategically placed
   - Supplemental work (strength, mobility) scheduled
   - Predicted end-of-week ACWR and divergence
   - Performance context from race history (e.g., "Your 50K PR pace suggests...")
7. **Current Training Analysis**: Moved from Dashboard:
   - Daily Training Decision (today's guidance)
   - Weekly Training Recommendation (existing pattern analysis)
   - Pattern Insights (existing trends analysis)

### Visual Design
- Timeline uses distinct color zones for each training stage (e.g., base = blue, build = green, specificity = orange, taper = yellow)
- "You Are Here" marker is a prominent vertical line or icon
- Countdown timer uses large, bold typography
- Race markers on timeline show race name, date, and priority badge (A/B/C)
- Coaching recommendation cards have consistent styling with expand/collapse icons

### UI Components to Reuse
- Use existing `TrainingLoadDashboard.module.css` for consistent styling
- Reuse chart container styles for timeline visualization
- Reuse recommendation card styles from Dashboard
- Reuse form components from Settings page for race goal input

## Technical Considerations

### Frontend Implementation
- **New Component**: Create `CoachPage.tsx` in `frontend/src/`
- **Navigation**: Update `App.tsx` to add "Coach" tab and route to `CoachPage`
- **State Management**: Use React hooks for race goals, timeline data, coaching recommendations
- **API Calls**: Fetch race goals, training stage, and coaching recommendations from backend

### Backend Implementation
- **New API Endpoints**:
  
  **Race Goals Management (Future Races):**
  - `GET /api/coach/race-goals` - Fetch user's race goals
  - `POST /api/coach/race-goals` - Create new race goal
  - `PUT /api/coach/race-goals/<id>` - Update race goal
  - `DELETE /api/coach/race-goals/<id>` - Delete race goal
  
  **Race History Management (Past Races):**
  - `GET /api/coach/race-history` - Fetch user's race history (last 5 years)
  - `POST /api/coach/race-history` - Add past race result (name, distance, date, finish time)
  - `POST /api/coach/race-history/screenshot` - Upload ultrasignup.com screenshot for parsing
    - Request: multipart/form-data with image file
    - Response: Extracted race data in JSON format for user review
  - `POST /api/coach/race-history/bulk` - Bulk save multiple races from screenshot extraction
  - `PUT /api/coach/race-history/<id>` - Update race result
  - `DELETE /api/coach/race-history/<id>` - Delete race result
  - `GET /api/coach/race-analysis` - Get calculated trends and PRs from race history
  
  **Training Schedule Management:**
  - `GET /api/coach/training-schedule` - Fetch user's training schedule and availability
  - `POST /api/coach/training-schedule` - Update user's training schedule and constraints
  
  **Training Stage & Timeline:**
  - `GET /api/coach/training-stage` - Get current training stage and timeline data
  
  **Weekly Training Program:**
  - `GET /api/coach/weekly-program` - Fetch current weekly training program (cached)
  - `POST /api/coach/weekly-program/generate` - Manually trigger weekly program regeneration
  
  **Legacy Recommendations (moved from Dashboard):**
  - `GET /api/coach/recommendations` - Fetch daily/weekly/pattern recommendations
  - `POST /api/coach/recommendations/generate` - Manually trigger recommendation generation (existing)
  
  **Feedback & Analytics:**
  - `POST /api/coach/feedback` - Submit feedback on recommendations
  - `POST /api/coach/program-adherence` - Log adherence to weekly program (for future learning)

- **Database Schema**: 

New table `race_goals` (future races):
  ```sql
  CREATE TABLE race_goals (
      id SERIAL PRIMARY KEY,
      user_id INTEGER NOT NULL REFERENCES user_settings(id),
      race_name VARCHAR(200) NOT NULL,
      race_date DATE NOT NULL,
      race_type VARCHAR(100),
      priority CHAR(1) CHECK (priority IN ('A', 'B', 'C')),
      target_time VARCHAR(20),
      notes TEXT,
      created_at TIMESTAMP DEFAULT NOW(),
      updated_at TIMESTAMP DEFAULT NOW()
  );
  CREATE INDEX idx_race_goals_user_date ON race_goals(user_id, race_date);
  ```

New table `race_history` (past race results - simple and focused):
  ```sql
  CREATE TABLE race_history (
      id SERIAL PRIMARY KEY,
      user_id INTEGER NOT NULL REFERENCES user_settings(id),
      race_date DATE NOT NULL,
      race_name VARCHAR(200) NOT NULL,
      distance_miles REAL NOT NULL,
      finish_time_minutes INTEGER NOT NULL,
      created_at TIMESTAMP DEFAULT NOW(),
      updated_at TIMESTAMP DEFAULT NOW(),
      CONSTRAINT check_last_5_years CHECK (race_date >= CURRENT_DATE - INTERVAL '5 years')
  );
  CREATE INDEX idx_race_history_user_date ON race_history(user_id, race_date DESC);
  CREATE INDEX idx_race_history_user_distance ON race_history(user_id, distance_miles);
  ```
  
  **Note**: PRs and trends are calculated dynamically from this simple dataset by the LLM/backend, not stored separately.

New fields in `user_settings` table:
  ```sql
  ALTER TABLE user_settings ADD COLUMN training_schedule_json JSONB;
  ALTER TABLE user_settings ADD COLUMN include_strength_training BOOLEAN DEFAULT FALSE;
  ALTER TABLE user_settings ADD COLUMN strength_hours_per_week REAL DEFAULT 0;
  ALTER TABLE user_settings ADD COLUMN include_mobility BOOLEAN DEFAULT FALSE;
  ALTER TABLE user_settings ADD COLUMN mobility_hours_per_week REAL DEFAULT 0;
  ALTER TABLE user_settings ADD COLUMN include_cross_training BOOLEAN DEFAULT FALSE;
  ALTER TABLE user_settings ADD COLUMN cross_training_type VARCHAR(50);
  ALTER TABLE user_settings ADD COLUMN cross_training_hours_per_week REAL DEFAULT 0;
  ALTER TABLE user_settings ADD COLUMN schedule_last_updated TIMESTAMP;
  ```

Example `training_schedule_json` structure:
  ```json
  {
    "available_days": ["monday", "tuesday", "wednesday", "thursday", "saturday", "sunday"],
    "time_blocks": {
      "monday": ["morning", "evening"],
      "tuesday": ["evening"],
      "wednesday": ["morning"],
      "thursday": ["evening"],
      "saturday": ["morning"],
      "sunday": ["morning"]
    },
    "constraints": [
      {"type": "work", "description": "Monday-Friday 9am-5pm"},
      {"type": "family", "description": "Pick up kids 3pm weekdays"},
      {"type": "sleep", "description": "In bed by 10pm"}
    ]
  }
  ```

- **Screenshot Parsing Integration**:
  - Create new module `ultrasignup_parser.py` for screenshot processing
  - Use Claude Vision API to extract race data from ultrasignup.com screenshots
  - Vision API prompt: "Extract race history from this ultrasignup.com screenshot. For each race, return: race_name (string), distance_miles (float), race_date (YYYY-MM-DD), finish_time_minutes (integer). Return as JSON array."
  - Handle image formats: PNG, JPG, JPEG, WebP (max 5MB)
  - Return structured JSON for user review/editing before database save
  - Error handling: If extraction fails or confidence low, return error message and fallback to manual entry
  - Cost per screenshot: ~$0.01-0.02 (vision API pricing)

- **LLM Integration**:
  - Create new module `coach_recommendations.py` extending existing `llm_recommendations_module.py`
  - New LLM prompt for **Weekly Training Program** generation with:
    - Current ACWR, divergence, and TRIMP trends (28-day history)
    - User's training schedule availability and constraints
    - Race goals (A/B/C priority) and timeline
    - Current training stage
    - **Race history and performance analysis:**
      - Past race results (last 5 years: name, distance, date, finish time)
      - Calculated performance trend: improving, plateauing, or declining
      - Best times (PRs) at relevant distances derived from race history
      - Base fitness assessment: what volume/intensity has athlete successfully completed?
      - Training capacity indicators from historical race performance
    - Supplemental training preferences (strength, mobility, cross-training)
    - Historical adherence patterns from journal
  - LLM output format for Weekly Training Program:
    ```json
    {
      "weekly_program": [
        {
          "day": "Monday",
          "training_type": "Easy Run",
          "duration_hours": 1.0,
          "intensity_guidance": "Zone 2, conversational pace",
          "rationale": "Recovery from weekend long run, maintaining base"
        },
        // ... 7 days
      ],
      "predicted_end_week_acwr": 1.15,
      "predicted_divergence": -0.03,
      "training_stage": "Build Phase - Week 8 of 16",
      "key_focus": "Maintain consistency while managing divergence"
    }
    ```
  - Context enrichment with race goals, training stage, schedule constraints, and divergence trends

### Performance Considerations: API Call Management

**Challenge**: Minimize Claude API costs while maintaining fresh, relevant coaching content.

**Optimized Caching Strategy for Divergence-Based Programming**:

1. **Weekly Training Program**: Generate twice per week (Sunday 6 PM UTC, Wednesday 6 PM UTC)
   - Sunday generation: Full 7-day program for upcoming week
   - Wednesday mid-week check: Adjust remaining 4 days based on actual adherence and divergence changes
   - Cached until next scheduled generation
   - Manual regenerate button available anytime
   - Cost: ~2 API calls per user per week

2. **Training Stage Analysis**: Generate when significant changes occur
   - Triggered by: race goal changes, training schedule updates, major divergence shifts (>0.15)
   - Cached for 48 hours
   - Cost: ~0.5-1 API call per user per week (average)

3. **Daily/Weekly/Pattern Insights**: Moved from Dashboard (existing)
   - Continue existing generation schedule (daily at 6 AM UTC)
   - Cost: ~7 API calls per user per week (unchanged)

**Total Estimated API Cost**: ~$0.18-0.22 per user per week (9.5-10 LLM calls)
- Existing daily recommendations: ~$0.14 per user per week (7 calls)
- New weekly program: ~$0.04-0.06 per user per week (2-2.5 calls)
- Training stage analysis: ~$0.01-0.02 per user per week (0.5-1 calls)
- Screenshot parsing: ~$0.01-0.02 per screenshot (one-time cost during initial setup or when adding races)

**Page Load Strategy**:
- On page visit: Fetch cached weekly program and recommendations from database (no LLM call)
- Display last generated content with timestamp (e.g., "Generated Sunday 6:00 PM - Next update Wednesday 6:00 PM")
- "Regenerate Training Program" button triggers fresh LLM generation and saves to cache
- Scheduled job (Cloud Scheduler) handles automatic regeneration (Sunday/Wednesday 6 PM UTC)

**Why Twice-Weekly Generation?**
- Sunday evening: User plans upcoming week
- Wednesday mid-week: Adjust for actual adherence, unexpected rest days, or divergence changes
- Balances freshness with cost efficiency
- User can manually regenerate anytime if schedule changes

### Integration with Existing Features
- **Dashboard**: Remove "Training Recommendations & Analysis" section, add link to Coach page
- **Journal**: NO CHANGES - daily training decisions remain on Journal page unchanged
- **Settings**: Potentially add coaching preferences (coaching detail level, frequency)
- **Strava Sync**: No changes required

### Data Flow
1. User navigates to Coach page
2. Frontend fetches race goals, training stage, and coaching recommendations in parallel (from database cache)
3. Training stage calculation:
   - Backend checks if cached stage is <24 hours old; if yes, return cached
   - If expired: LLM analyzes recent training data (ACWR, TRIMP, journal notes)
   - Returns recommended stage, week number, and timeline boundaries
4. Coaching recommendations:
   - Backend checks cache timestamps for each section
   - Returns cached content if within validity period
   - User can manually trigger regeneration via button
5. Scheduled generation (Monday 6 AM UTC):
   - Weekly strategy, nutrition, and mental preparation regenerate
   - Race strategy regenerates if race <4 weeks away

## Success Metrics

1. **User Engagement**: >60% of active users visit Coach page at least once per week
2. **Goal Configuration**: >80% of users configure at least one race goal within first 2 weeks
3. **Recommendation Usefulness**: >4.0/5.0 average rating on coaching recommendation feedback
4. **Page Performance**: <2 seconds load time for Coach page with full data
5. **API Performance**: <500ms response time for all Coach API endpoints (cached responses)
6. **Feature Adoption**: >50% of users interact with weekly strategy or nutrition guidance
7. **Timeline Engagement**: >70% of users expand/view timeline visualization
8. **Cost Efficiency**: Maintain <$0.25 per user per week for all LLM coaching features combined

## Open Questions & Decisions

### ✅ Resolved (Per User Input)

1. **Training Stage Transition Logic**: Should LLM automatically transition between stages, or require user confirmation?
   - **DECISION**: Auto-transition with notification + manual override option

2. **Recommendation Generation Frequency**: Should new coaching sections generate daily (6 AM) or less frequently (weekly for strategy/nutrition)?
   - **DECISION**: Weekly strategy/nutrition/mindset generate weekly (Mondays); race strategy generates 2 weeks before race

3. **Historical Race Results**: Should we allow users to log past race results for LLM context?
   - **DECISION**: Yes, but as a future enhancement (v2); for v1, LLM uses only Strava training data

4. **Multiple A Races**: Can users have multiple A races, or only one per period?
   - **DECISION**: Only one A race at a time; to change A race, user must re-prioritize existing goals

5. **Timeline Customization**: Should users be able to manually adjust training stage boundaries?
   - **DECISION**: Not in v1; accept LLM recommendations only

6. **Notification System**: Should users receive notifications when training stage changes?
   - **DECISION**: Future enhancement; v1 shows stage change on Coach page only

7. **API Call Frequency**: How often should LLM be triggered to balance freshness and cost?
   - **DECISION**: Hybrid caching with weekly generation (Mondays 6 AM UTC) + manual regenerate option

### ⏳ Remaining Questions

1. **Training Stage Override UI**: Should manual override be a dropdown selector or require confirmation?
   - **Recommendation**: Dropdown with confirmation dialog showing impact

2. **Race Priority Validation**: Should system enforce only one A race, or just warn user?
   - **Recommendation**: Enforce as requirement; show error if trying to create second A race

3. **Timeline Scroll Behavior**: For timelines >12 weeks, should it scroll horizontally or compress?
   - **Recommendation**: Horizontal scroll with "scroll to today" button

4. **Empty State**: What should users see if no race goals configured?
   - **Recommendation**: Welcome card with "Add Your First Race Goal" CTA and explanation of A/B/C system

