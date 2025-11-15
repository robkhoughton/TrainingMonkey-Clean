# Task List: YTM Coach Page Implementation

## Relevant Files

### Backend Files
- `app/strava_app.py` - Main Flask application (add new API endpoints)
- `app/db_utils.py` - Database utilities (schema creation, queries)
- `app/llm_recommendations_module.py` - Existing LLM integration (extend for coach)
- `app/coach_recommendations.py` - NEW: Weekly training program generation module
- `app/ultrasignup_parser.py` - NEW: Screenshot parsing with Claude Vision API
- `sql/coach_schema.sql` - NEW: Database migration script for Coach tables (CREATED - race_goals, race_history, weekly_programs tables + user_settings modifications)

### Frontend Files
- `frontend/src/App.tsx` - Main app component (add Coach tab navigation)
- `frontend/src/CoachPage.tsx` - NEW: Main Coach page component
- `frontend/src/RaceGoalsManager.tsx` - NEW: Race goals CRUD component
- `frontend/src/RaceHistoryManager.tsx` - NEW: Race history with screenshot upload
- `frontend/src/TrainingScheduleConfig.tsx` - NEW: Training schedule configuration
- `frontend/src/WeeklyProgramDisplay.tsx` - NEW: 7-day program display
- `frontend/src/TimelineVisualization.tsx` - NEW: Training stage timeline
- `frontend/src/ScreenshotUpload.tsx` - NEW: Screenshot upload component
- `frontend/src/TrainingLoadDashboard.tsx` - MODIFY: Remove LLM section, add link to Coach

### Configuration Files
- Cloud Scheduler job configuration for Sunday/Wednesday program generation

## Parent Tasks Overview

Based on the PRD, implementation is organized into 12 high-level tasks focusing on divergence-based weekly training programming:

**Core Database & Backend (Tasks 1-4):**
- Database tables for race goals, race history, training schedules
- API endpoints for CRUD operations
- Screenshot parsing with Claude Vision API
- Training stage analysis and timeline calculations

**Weekly Training Program Generation (Tasks 5-6):**
- LLM module for divergence-optimized weekly programs
- Performance analysis from race history
- Scheduled generation (Sunday/Wednesday)

**Frontend Implementation (Tasks 7-10):**
- Coach page component and UI
- Race goals & history management (with screenshot upload)
- Training schedule configuration
- Weekly training program display
- Timeline visualization

**Integration & Migration (Tasks 11-12):**
- Navigation updates
- Move LLM recommendations from Dashboard to Coach page

---

## Tasks

### Backend Infrastructure & Data Layer

- [x] **1.0 Database Schema & Backend Infrastructure Setup**
  - [x] 1.1 Create `sql/coach_schema.sql` migration script
  - [x] 1.2 Write `race_goals` table creation SQL:
    - Fields: id (SERIAL PRIMARY KEY), user_id (FK to user_settings), race_name (VARCHAR 200), race_date (DATE), race_type (VARCHAR 100), priority (CHAR 1 with CHECK A/B/C), target_time (VARCHAR 20), notes (TEXT), created_at/updated_at (TIMESTAMP DEFAULT NOW())
    - Index: idx_race_goals_user_date ON (user_id, race_date)
  - [x] 1.3 Write `race_history` table creation SQL:
    - Fields: id (SERIAL PRIMARY KEY), user_id (FK), race_date (DATE), race_name (VARCHAR 200), distance_miles (REAL), finish_time_minutes (INTEGER), created_at/updated_at (TIMESTAMP)
    - Constraint: CHECK (race_date >= CURRENT_DATE - INTERVAL '5 years')
    - Index: idx_race_history_user_date ON (user_id, race_date DESC)
    - Index: idx_race_history_user_distance ON (user_id, distance_miles)
  - [x] 1.4 Write ALTER TABLE user_settings SQL to add fields:
    - training_schedule_json (JSONB)
    - include_strength_training (BOOLEAN DEFAULT FALSE)
    - strength_hours_per_week (REAL DEFAULT 0)
    - include_mobility (BOOLEAN DEFAULT FALSE)
    - mobility_hours_per_week (REAL DEFAULT 0)
    - include_cross_training (BOOLEAN DEFAULT FALSE)
    - cross_training_type (VARCHAR 50)
    - cross_training_hours_per_week (REAL DEFAULT 0)
    - schedule_last_updated (TIMESTAMP)
  - [x] 1.5 Test migration script in SQL editor manually (per project rules)
  - [x] 1.6 Document rollback SQL in script comments

- [x] **2.0 Race Goals & History Management (Backend)**
  - [x] 2.1 In `app/strava_app.py`, create `GET /api/coach/race-goals` endpoint:
    - Query: `SELECT * FROM race_goals WHERE user_id = %s ORDER BY race_date ASC`
    - Return JSON array of goals with user_id filtering
    - Use @login_required decorator
  - [x] 2.2 Create `POST /api/coach/race-goals` endpoint:
    - Validate required fields: race_name, race_date, priority
    - Validate priority is 'A', 'B', or 'C'
    - Enforce only one 'A' race at a time (business rule)
    - INSERT query with parameterized %s placeholders
    - Return created goal with ID
  - [x] 2.3 Create `PUT /api/coach/race-goals/<int:goal_id>` endpoint:
    - Verify goal belongs to current_user.id before update
    - Validate same constraints as POST
    - UPDATE query with WHERE id = %s AND user_id = %s
  - [x] 2.4 Create `DELETE /api/coach/race-goals/<int:goal_id>` endpoint:
    - Verify ownership before delete
    - DELETE query with user_id filter
  - [x] 2.5 Create `GET /api/coach/race-history` endpoint:
    - Query with 5-year filter: `WHERE user_id = %s AND race_date >= CURRENT_DATE - INTERVAL '5 years'`
    - ORDER BY race_date DESC
  - [x] 2.6 Create `POST /api/coach/race-history` endpoint (single race):
    - Validate: race_name, distance_miles (> 0), race_date, finish_time_minutes (> 0)
    - INSERT with user_id
  - [x] 2.7 Create `POST /api/coach/race-history/bulk` endpoint:
    - Accept JSON array of races
    - Validate each race
    - Bulk INSERT using executemany pattern
    - Return count of inserted races
  - [x] 2.8 Create `PUT /api/coach/race-history/<int:history_id>` endpoint
  - [x] 2.9 Create `DELETE /api/coach/race-history/<int:history_id>` endpoint
  - [x] 2.10 Create `GET /api/coach/race-analysis` endpoint:
    - Fetch all user's race history
    - Calculate PRs per distance (group by distance_miles, find MIN finish_time)
    - Calculate trend: compare recent 6 months average pace vs previous 6 months
    - Return: {prs: [{distance, time, race_name, date}], trend: 'improving'|'stable'|'declining', base_fitness: 'analysis text'}
  - [x] 2.11 Add comprehensive error handling and input validation to all endpoints

- [ ] **3.0 Ultrasignup Screenshot Parsing System**
  - [ ] 3.1 Create `app/ultrasignup_parser.py` module
  - [ ] 3.2 Import required libraries: requests, base64, os (for API key)
  - [ ] 3.3 Create `parse_ultrasignup_screenshot(image_bytes)` function:
    - Encode image to base64
    - Build Claude Vision API request with prompt: "Extract race history from this ultrasignup.com screenshot. For each race return JSON: race_name, distance_miles, race_date (YYYY-MM-DD), finish_time_minutes. Return as JSON array."
    - Set model to "claude-3-7-sonnet-20250219" with vision capability
    - POST to https://api.anthropic.com/v1/messages with image
    - Parse response JSON and extract race array
    - Handle API errors gracefully
  - [ ] 3.4 Add validation function `validate_extracted_race(race_dict)`:
    - Check required fields exist
    - Validate distance_miles > 0
    - Validate date format YYYY-MM-DD
    - Validate finish_time_minutes > 0
    - Return validation errors if any
  - [ ] 3.5 In `app/strava_app.py`, create `POST /api/coach/race-history/screenshot` endpoint:
    - Use @login_required decorator
    - Accept multipart/form-data file upload
    - Validate file type (PNG, JPG, JPEG, WebP)
    - Validate file size < 5MB
    - Read file bytes
    - Call parse_ultrasignup_screenshot()
    - Validate each extracted race
    - Return JSON: {success: true, races: [...]} or {success: false, error: "..."}
  - [ ] 3.6 Add error handling for:
    - Claude API failures (return error message)
    - Invalid image formats
    - Parse errors (malformed JSON response)
    - Empty extractions (no races found)
  - [ ] 3.7 Log all screenshot parsing attempts for debugging
  - [ ] 3.8 Document API cost (~$0.01-0.02 per screenshot) in code comments

- [ ] **4.0 Training Schedule & Availability Management (Backend)**
  - [ ] 4.1 Create `GET /api/coach/training-schedule` endpoint in `app/strava_app.py`:
    - Query user_settings for current_user.id
    - Return training_schedule_json, include_strength_training, strength_hours_per_week, include_mobility, mobility_hours_per_week, include_cross_training, cross_training_type, cross_training_hours_per_week, schedule_last_updated
    - If training_schedule_json is NULL, return default: {available_days: ['monday', 'tuesday', 'wednesday', 'thursday', 'saturday', 'sunday'], time_blocks: {}, constraints: []}
  - [ ] 4.2 Create `POST /api/coach/training-schedule` endpoint:
    - Accept JSON body with: available_days (array), time_blocks (object), constraints (array), include_strength_training, strength_hours_per_week, include_mobility, mobility_hours_per_week, include_cross_training, cross_training_type, cross_training_hours_per_week
    - Validate available_days contains valid day names
    - Validate time_blocks structure
    - Validate hour values are numeric and >= 0
    - UPDATE user_settings SET training_schedule_json = %s, include_strength_training = %s, ... WHERE id = %s
    - Set schedule_last_updated = NOW()
    - Return success message
  - [ ] 4.3 Add helper function `validate_training_schedule(schedule_dict)`:
    - Check available_days is array of valid weekday strings
    - Check time_blocks is properly structured JSON
    - Check constraints is array
    - Return validation errors or None
  - [ ] 4.4 Document training_schedule_json structure in code comments with example

### LLM & Program Generation

- [ ] **5.0 Training Stage Analysis & Timeline Backend**
  - [ ] 5.1 Create helper function `calculate_training_stage(a_race_date, current_date)`:
    - Calculate weeks until race
    - Return stage based on time windows: >16 weeks = 'base', 12-16 = 'build', 4-12 = 'specificity', 2-4 = 'taper', <2 = 'peak'
    - Return stage name, week_number, total_weeks, weeks_remaining_in_stage
  - [ ] 5.2 Create helper function `generate_timeline_data(a_race_date, b_races, c_races)`:
    - Calculate week-by-week timeline from today to race date
    - Assign training stage to each week
    - Mark weeks with B/C races
    - Return array of weeks with: week_date, stage, is_race_week, race_info
  - [ ] 5.3 Create `GET /api/coach/training-stage` endpoint:
    - Get user's A race from race_goals (priority='A')
    - If no A race, return {error: 'No A race configured'}
    - Calculate training stage using helper function
    - Get user's recent ACWR and divergence from activities
    - Generate timeline data
    - Return: {stage, week_number, total_weeks, timeline: [...], current_metrics: {acwr, divergence}}
  - [ ] 5.4 Add caching: store calculated stage in session or database to avoid recalculation on every request
  - [ ] 5.5 Add support for manual stage override (store in user_settings.manual_training_stage)

- [ ] **6.0 Weekly Training Program Generation (LLM Integration)**
  - [ ] 6.1 Create `app/coach_recommendations.py` module
  - [ ] 6.2 Import existing modules: llm_recommendations_module, db_utils, unified_metrics_service
  - [ ] 6.3 Create `build_weekly_program_prompt(user_id, target_week_start)` function:
    - Fetch last 28 days ACWR, divergence, TRIMP from unified_metrics_service
    - Fetch race goals from race_goals table
    - Fetch race history from race_history table
    - Calculate performance trend from race history
    - Fetch training schedule from user_settings
    - Get current training stage
    - Fetch recent journal observations (last 7 days)
    - Build comprehensive prompt including all context
  - [ ] 6.4 Create prompt template with sections:
    - Current Training Status (ACWR, divergence, days since rest)
    - Race Goals (A/B/C races with dates and target times)
    - Performance History (race results, PRs, trend analysis)
    - Training Schedule (available days, time blocks, constraints)
    - Current Training Stage (base/build/specificity/taper)
    - Supplemental Training (strength/mobility/cross-training hours)
    - Recent Observations (energy, RPE, pain from journal)
    - Request: Generate divergence-optimized 7-day training program
  - [ ] 6.5 Create `generate_weekly_program(user_id, target_week_start=None)` function:
    - If target_week_start is None, use next Monday
    - Build prompt using helper function
    - Call Claude API with structured output request (JSON format)
    - Parse response to extract: weekly_program array, predicted_acwr, predicted_divergence, key_focus
    - Validate response structure
    - Return program data
  - [ ] 6.6 Create database table `weekly_programs` to cache results:
    - Fields: id, user_id, week_start_date, program_json, predicted_acwr, predicted_divergence, generated_at, generation_type ('scheduled'|'manual')
    - Index on (user_id, week_start_date)
  - [ ] 6.7 Create `save_weekly_program(user_id, week_start, program_data)` function
  - [ ] 6.8 Create `get_cached_weekly_program(user_id, week_start)` function:
    - Query weekly_programs table
    - Return cached program if exists and < 3 days old
    - Return None if expired or not found
  - [ ] 6.9 Create `GET /api/coach/weekly-program` endpoint:
    - Get week_start from query param (default to upcoming Monday)
    - Check cache first
    - If not cached or expired, generate new program
    - Save to cache
    - Return program JSON
  - [ ] 6.10 Create `POST /api/coach/weekly-program/generate` endpoint for manual regeneration:
    - Force generation regardless of cache
    - Mark as generation_type='manual'
    - Return new program

### Frontend Implementation

- [ ] **7.0 Frontend Coach Page Foundation & Layout**
  - [ ] 7.1 Create `frontend/src/CoachPage.tsx` React component
  - [ ] 7.2 Add performance monitoring: `usePagePerformanceMonitoring('coach')`
  - [ ] 7.3 Define TypeScript interfaces for all data types:
    - RaceGoal, RaceHistory, TrainingSchedule, WeeklyProgram, TimelineWeek
  - [ ] 7.4 Create state management with useState hooks:
    - raceGoals, raceHistory, trainingSchedule, weeklyProgram, trainingStage, timeline, loading, error
  - [ ] 7.5 Implement `useEffect` to fetch data on mount:
    - Parallel fetch: race-goals, race-history, training-schedule, training-stage, weekly-program
    - Handle loading states
    - Handle errors gracefully
  - [ ] 7.6 Create page layout structure with sections:
    - Header with title and tagline
    - Countdown banner (days to A race)
    - Timeline visualization container
    - Race goals & history card
    - Training schedule profile card
    - Weekly training program card
    - Moved recommendations card (daily/weekly/pattern)
  - [ ] 7.7 Implement initial onboarding flow:
    - Detect if user has no race goals configured
    - Show welcome modal with setup wizard
    - Guide through: Add race goals → Add race history → Configure schedule
    - Skip button with reminder message
  - [ ] 7.8 Add loading spinner while fetching data
  - [ ] 7.9 Add error display with retry button
  - [ ] 7.10 Reuse existing CSS from `TrainingLoadDashboard.module.css` for consistent styling

- [ ] **8.0 Race Goals & History Management UI (with Screenshot Upload)**
  - Race goals form (add/edit/delete with A/B/C priority)
  - Race history table display
  - Manual race entry form (4 fields: name, distance, date, time)
  - **Screenshot upload component:**
    - File picker UI
    - Upload progress indicator
    - Extracted race data review table (editable)
    - Bulk save confirmation
    - Error handling UI
  - Performance summary display (PRs, trends, base fitness)

- [ ] **9.0 Training Schedule Configuration UI**
  - Training availability day selector (Mon-Sun checkboxes)
  - Time block selection per day (morning/midday/evening/night)
  - Weekly hours input (including supplemental work)
  - Fixed constraints input (work, family, sleep)
  - Supplemental training preferences (strength, mobility, cross-training)
  - Save and validation

- [ ] **10.0 Weekly Training Program Display & Timeline Visualization**
  - **Timeline visualization:**
    - Horizontal week-by-week timeline with color-coded training stages
    - "You Are Here" marker
    - Race markers (A/B/C badges)
    - Responsive design for various week counts
  - **Weekly training program display:**
    - 7-day training schedule cards
    - Daily volume/intensity recommendations
    - Rest day indicators
    - Supplemental work scheduling
    - Predicted end-of-week metrics
    - Performance context from race history
  - **Moved Dashboard recommendations:**
    - Daily training decision
    - Weekly recommendation
    - Pattern insights
  - Manual regenerate button

### Integration & Deployment

- [ ] **11.0 Navigation & Dashboard Integration**
  - Add "Coach" tab to main navigation (between Journal and Guide)
  - Remove LLM recommendations section from Dashboard
  - Add link on Dashboard: "View full coaching analysis on Coach page"
  - Ensure consistent styling and navigation flow
  - Update route handling

- [ ] **12.0 Scheduled Jobs for Weekly Program Generation**
  - Create cron endpoint `/cron/weekly-program` 
  - Implement Sunday 6 PM UTC generation (full 7-day program)
  - Implement Wednesday 6 PM UTC generation (adjust remaining 4 days)
  - Cloud Scheduler configuration
  - Error handling and logging
  - Active user detection (exclude inactive users)

---

## Detailed Sub-Tasks

### 1.0 Database Schema & Backend Infrastructure Setup

- [x] 1.1 Create SQL migration script `sql/coach_schema.sql` with PostgreSQL syntax
  - Use `SERIAL PRIMARY KEY` (not AUTOINCREMENT)
  - Use `NOW()` (not CURRENT_TIMESTAMP)
  - Include `CHECK` constraints where appropriate
  - Add proper indexes for performance

- [x] 1.2 Define `race_goals` table structure
  - Fields: id, user_id, race_name, race_date, race_type, priority (A/B/C), target_time, notes, created_at, updated_at
  - Foreign key constraint to `user_settings(id)`
  - Index on `(user_id, race_date)`
  - CHECK constraint for priority IN ('A', 'B', 'C')

- [x] 1.3 Define `race_history` table structure
  - Fields: id, user_id, race_date, race_name, distance_miles, finish_time_minutes, created_at, updated_at
  - Foreign key constraint to `user_settings(id)`
  - CHECK constraint for last 5 years: `race_date >= CURRENT_DATE - INTERVAL '5 years'`
  - Index on `(user_id, race_date DESC)` for chronological queries
  - Index on `(user_id, distance_miles)` for PR calculations

- [x] 1.4 Add training schedule fields to `user_settings` table (ALTER TABLE)
  - `training_schedule_json JSONB` - stores availability, time blocks, constraints
  - `include_strength_training BOOLEAN DEFAULT FALSE`
  - `strength_hours_per_week REAL DEFAULT 0`
  - `include_mobility BOOLEAN DEFAULT FALSE`
  - `mobility_hours_per_week REAL DEFAULT 0`
  - `include_cross_training BOOLEAN DEFAULT FALSE`
  - `cross_training_type VARCHAR(50)`
  - `cross_training_hours_per_week REAL DEFAULT 0`
  - `schedule_last_updated TIMESTAMP`

- [x] 1.5 Test database schema creation
  - Run migration script on development database
  - Verify all tables created successfully
  - Verify indexes exist using `\d table_name` or `SELECT * FROM pg_indexes WHERE tablename = 'race_goals'`
  - Test foreign key constraints
  - Test CHECK constraints (try inserting invalid priority, old race date)

- [x] 1.6 Add schema verification to `db_utils.py`
  - Function to check if Coach tables exist
  - Function to verify required columns
  - Integration with existing `initialize_db()` if needed

### 2.0 Race Goals & History Management (Backend)

- [x] 2.1 Implement race goals API endpoints in `strava_app.py`
  - `GET /api/coach/race-goals` - Fetch all race goals for current user, ordered by race_date
  - `POST /api/coach/race-goals` - Create new race goal with validation
  - `PUT /api/coach/race-goals/<id>` - Update existing race goal
  - `DELETE /api/coach/race-goals/<id>` - Delete race goal
  - All endpoints require `@login_required` decorator
  - All queries filter by `current_user.id`
  - Use parameterized queries with `%s` placeholders

- [x] 2.2 Implement input validation for race goals
  - Validate race_date is future date (with 7-day grace period)
  - Validate priority is 'A', 'B', or 'C'
  - Validate race_name is not empty
  - Enforce only one 'A' race at a time (business rule)
  - Return meaningful error messages (400 status)

- [x] 2.3 Implement race history API endpoints in `strava_app.py`
  - `GET /api/coach/race-history` - Fetch race history (last 5 years), ordered by race_date DESC
  - `POST /api/coach/race-history` - Create new race result with validation
  - `POST /api/coach/race-history/bulk` - Bulk insert multiple races (for screenshot parsing)
  - `PUT /api/coach/race-history/<id>` - Update existing race result
  - `DELETE /api/coach/race-history/<id>` - Delete race result

- [x] 2.4 Implement input validation for race history
  - Validate race_date is within last 5 years
  - Validate distance_miles > 0
  - Validate finish_time_minutes > 0
  - Validate race_name is not empty
  - Return meaningful error messages

- [x] 2.5 Implement race analysis calculations
  - Create `/api/coach/race-analysis` endpoint
  - Calculate PRs at each distance from race_history
  - Calculate performance trend (improving/stable/declining)
    - Compare recent races (last 12 months) vs older races (12-24 months ago)
    - Look for time improvements at similar distances
  - Assess base fitness from race history
    - Maximum distance completed
    - Frequency of racing
    - Consistency of performance
  - Return JSON with PRs, trend indicator, and base fitness summary

- [x] 2.6 Write helper functions in `db_utils.py` or new `coach_utils.py`
  - `_calculate_performance_trend()` - Determine improving/stable/declining
  - `_assess_base_fitness()` - Analyze training capacity
  - Helper functions integrated into strava_app.py

- [x] 2.7 Test all race goals & history endpoints
  - Test CRUD operations for race goals
  - Test A race uniqueness constraint
  - Test race history filtering (5 year limit)
  - Test bulk insert
  - Test race analysis calculations
  - Test user isolation (can't access other user's data)

### 3.0 Ultrasignup Screenshot Parsing System

- [ ] 3.1 Create `app/ultrasignup_parser.py` module
  - Import necessary libraries (requests, base64, json, logging)
  - Set up module constants (API URL, max file size, allowed formats)
  - Import Anthropic API key from environment

- [ ] 3.2 Implement image upload handling function
  - `validate_image_file(file)` - Check file size (<5MB), format (PNG/JPG/JPEG/WebP)
  - `encode_image_base64(file)` - Convert uploaded file to base64 for Claude API
  - Return validation errors if file invalid

- [ ] 3.3 Implement Claude Vision API integration
  - `parse_ultrasignup_screenshot(image_file)` - Main parsing function
  - Construct Claude Vision API request with image and prompt
  - Prompt: "Extract race history from this ultrasignup.com screenshot. For each race, return: race_name (string), distance_miles (float), race_date (YYYY-MM-DD), finish_time_minutes (integer). Return as JSON array."
  - Use Claude model with vision capabilities (claude-3-sonnet or claude-3-opus)
  - Handle API errors gracefully
  - Parse JSON response from Claude

- [ ] 3.4 Implement data extraction and validation
  - Parse Claude's JSON response
  - Validate extracted race data structure
  - Convert distances to miles if needed (handle km/miles)
  - Convert finish times to minutes if in other format
  - Filter out races older than 5 years
  - Return structured array of race objects

- [ ] 3.5 Create screenshot upload API endpoint in `strava_app.py`
  - `POST /api/coach/race-history/screenshot` - Upload endpoint
  - Use `@login_required` decorator
  - Accept multipart/form-data with image file
  - Call `parse_ultrasignup_screenshot()`
  - Return extracted race data as JSON for user review
  - Include confidence/success indicators
  - Handle parsing failures gracefully (return error, allow fallback to manual entry)

- [ ] 3.6 Implement error handling and logging
  - Log API calls to Claude Vision (for cost tracking)
  - Log parsing successes and failures
  - Provide meaningful error messages to frontend
  - Handle network errors, API rate limits, invalid images
  - Cost tracking: Log estimated cost per screenshot (~$0.01-0.02)

- [ ] 3.7 Test screenshot parsing functionality
  - Test with sample ultrasignup.com screenshots
  - Test with various image formats
  - Test with oversized files (should reject)
  - Test with non-race images (should fail gracefully)
  - Test with empty/corrupted images
  - Verify extracted data accuracy
  - Test Claude API error handling

### 4.0 Training Schedule & Availability Management (Backend)

- [ ] 4.1 Define training schedule JSON structure
  - Document JSONB schema in comments
  - Structure: `{ available_days: [], time_blocks: {}, constraints: [] }`
  - Example documented in PRD (lines 256-273 of prd-ytm-coach-page.md)

- [ ] 4.2 Implement training schedule API endpoints in `strava_app.py`
  - `GET /api/coach/training-schedule` - Fetch user's training schedule from user_settings
  - `POST /api/coach/training-schedule` - Update training schedule (full replace)
  - Include supplemental training preferences in response

- [ ] 4.3 Implement training schedule validation
  - Validate `available_days` array contains valid day names
  - Validate `time_blocks` for each day are valid (morning/midday/evening/night)
  - Validate `constraints` array has proper structure
  - Validate weekly hours are reasonable (1-40 hours)
  - Validate supplemental hours don't exceed total weekly hours

- [ ] 4.4 Implement default schedule generation
  - If user hasn't configured schedule, generate smart defaults
  - Use existing `weekly_training_hours` from user_settings
  - Assume 5 days/week availability (Mon, Tue, Wed, Thu, Sat)
  - Distribute training across morning and evening time blocks
  - Return default schedule with flag indicating it's default (not user-configured)

- [ ] 4.5 Create helper functions for schedule operations
  - `get_training_schedule(user_id)` - Returns schedule or defaults
  - `save_training_schedule(user_id, schedule_data)` - Saves to user_settings
  - `calculate_total_available_hours(schedule)` - Sum up available time blocks
  - `validate_schedule_data(schedule_json)` - Comprehensive validation

- [ ] 4.6 Test training schedule endpoints
  - Test GET with no schedule (returns defaults)
  - Test POST with valid schedule
  - Test validation errors
  - Test supplemental training preferences
  - Test JSONB storage and retrieval

### 5.0 Training Stage Analysis & Timeline Backend

- [ ] 5.1 Create training stage calculation logic
  - Function `calculate_training_stage(a_race_date, current_date)` in new `coach_utils.py`
  - Stage logic based on weeks until race:
    - 12+ weeks: Base Building
    - 8-12 weeks: Build Phase
    - 4-8 weeks: Specificity (Race Prep)
    - 2-4 weeks: Taper
    - 0-2 weeks: Peak Week
    - Post-race: Recovery
  - Return stage name, week number, total weeks

- [ ] 5.2 Implement timeline generation logic
  - Function `generate_training_timeline(a_race, current_date)` 
  - Calculate week-by-week breakdown from now to race date
  - Assign training stage to each week
  - Include B/C races as markers on timeline
  - Return array of week objects with: week_number, start_date, end_date, stage, races_this_week

- [ ] 5.3 Create LLM-enhanced stage analysis (optional refinement)
  - Function `get_llm_stage_recommendation(user_id, calculated_stage)`
  - Send recent training data (ACWR, TRIMP trends) to Claude
  - Ask LLM if calculated stage is appropriate or should be adjusted
  - Consider recent injuries, overtraining signals, etc.
  - Return recommended stage with rationale
  - Cache result for 48 hours

- [ ] 5.4 Implement stage override functionality
  - Allow user to manually override calculated stage
  - Store override in database (new field `manual_training_stage` in user_settings)
  - If override exists, use it instead of calculated stage
  - Display override indicator in UI ("Manual override active")

- [ ] 5.5 Create training stage API endpoint
  - `GET /api/coach/training-stage` in `strava_app.py`
  - Calculate or retrieve current training stage
  - Generate timeline data
  - Include A/B/C race positions on timeline
  - Return JSON with: current_stage, week_number, total_weeks, timeline_array, races

- [ ] 5.6 Test training stage calculations
  - Test with various race dates (4 weeks, 12 weeks, 24 weeks out)
  - Test with no A race (return null or base building)
  - Test timeline generation
  - Test with multiple B/C races
  - Test manual override functionality

### 6.0 Weekly Training Program Generation (LLM Integration)

- [ ] 6.1 Create `app/coach_recommendations.py` module
  - Import existing LLM utilities from `llm_recommendations_module.py`
  - Import Claude API functionality
  - Import database utilities
  - Set up logging

- [ ] 6.2 Implement data collection for LLM context
  - Function `gather_weekly_program_context(user_id)`
  - Collect ACWR, divergence, TRIMP trends (last 28 days)
  - Collect race goals and race history
  - Calculate performance metrics from race history
  - Collect training schedule and availability
  - Get current training stage
  - Collect journal observations (recent patterns)
  - Return comprehensive context dictionary

- [ ] 6.3 Build LLM prompt for weekly program generation
  - Function `create_weekly_program_prompt(context)`
  - Structure prompt with clear sections:
    - Current training state (ACWR, divergence, days since rest)
    - Race goals and timeline (A/B/C races, weeks until A race)
    - Performance history (PRs, trend, base fitness)
    - Training schedule (available days, time blocks, constraints)
    - Current training stage and periodization
    - Supplemental training preferences
  - Request structured JSON output with 7-day program
  - Specify output format (see PRD lines 404-417)
  - Include coaching style from user preferences

- [ ] 6.4 Implement Claude API call for program generation
  - Function `generate_weekly_training_program(user_id, target_week_start=None)`
  - Call Claude API with constructed prompt
  - Parse JSON response
  - Extract 7-day program, predicted metrics, key focus
  - Handle API errors gracefully
  - Log API call for cost tracking

- [ ] 6.5 Implement program caching and storage
  - Create new table `weekly_programs` to store generated programs
    - Fields: id, user_id, week_start_date, program_json, predicted_acwr, predicted_divergence, generated_at
  - Save generated program to database
  - Check cache before generating (don't regenerate if recent)
  - Return cached program if <24 hours old (unless manual regenerate requested)

- [ ] 6.6 Create weekly program API endpoints
  - `GET /api/coach/weekly-program` - Fetch current week's program (from cache)
  - `POST /api/coach/weekly-program/generate` - Manually trigger generation
  - Include metadata: generation timestamp, next scheduled update, cache status

- [ ] 6.7 Implement program validation and quality checks
  - Validate JSON structure from LLM
  - Check that 7 days are present
  - Verify predicted metrics are reasonable
  - Log warnings if program seems inappropriate (e.g., too much volume during taper)
  - Fall back to rule-based defaults if LLM output invalid

- [ ] 6.8 Test weekly program generation
  - Test with various user profiles (beginner, advanced, high volume)
  - Test with different training stages (base, build, taper)
  - Test with constrained schedules (3 days/week vs 6 days/week)
  - Test with race history (improving vs declining trend)
  - Verify program respects user's availability
  - Verify divergence optimization (programs should improve ACWR)
  - Test caching behavior
  - Test manual regeneration

### 7.0 Frontend Coach Page Foundation & Layout

- [ ] 7.1 Create `frontend/src/CoachPage.tsx` component
  - Set up basic React functional component with TypeScript
  - Import performance monitoring hooks
  - Import CSS module (reuse `TrainingLoadDashboard.module.css`)
  - Add page title and subtitle

- [ ] 7.2 Define TypeScript interfaces for Coach page data
  - `RaceGoal` interface (id, name, date, type, priority, target_time, notes)
  - `RaceHistory` interface (id, name, distance, date, finish_time)
  - `TrainingSchedule` interface (available_days, time_blocks, constraints)
  - `WeeklyProgram` interface (weekly_program array, predicted_acwr, predicted_divergence)
  - `TimelineData` interface (current_stage, week_number, timeline_array)

- [ ] 7.3 Implement page state management
  - `useState` for race goals, race history, training schedule
  - `useState` for weekly program, timeline data
  - `useState` for loading states (isLoadingGoals, isLoadingProgram, etc.)
  - `useState` for error states
  - `useState` for onboarding flow state

- [ ] 7.4 Implement data fetching on component mount
  - `useEffect` hook to fetch initial data
  - Parallel API calls: race goals, race history, training schedule, weekly program, training stage
  - Use Promise.all() for parallel fetching
  - Handle loading states
  - Handle errors gracefully
  - Update component state with fetched data

- [ ] 7.5 Create page layout structure (placeholder sections)
  - Header section with title and tagline
  - Countdown banner section (placeholder)
  - Timeline visualization section (placeholder)
  - Race goals & history card (placeholder)
  - Training schedule profile section (placeholder)
  - Weekly training program section (placeholder)
  - Moved recommendations section (placeholder)
  - Use CSS Grid or Flexbox for responsive layout

- [ ] 7.6 Implement loading and error states
  - Loading spinner while fetching data
  - Error message display if API calls fail
  - Retry button on error
  - Skeleton loaders for each section
  - Graceful degradation (show what data is available even if some calls fail)

- [ ] 7.7 Implement initial onboarding flow
  - Detect if user has no race goals (first visit)
  - Show onboarding wizard modal/overlay
  - Multi-step wizard: 1) Add race goals, 2) Add race history (optional), 3) Configure schedule
  - "Skip for now" option for each step
  - Save onboarding progress
  - Don't show onboarding on subsequent visits

- [ ] 7.8 Add navigation to Coach page in `App.tsx`
  - Add "Coach" tab to navigation array (between Journal and Guide)
  - Add route case in `renderTabContent()` for 'coach' tab
  - Test navigation works correctly

- [ ] 7.9 Implement performance monitoring
  - Use `usePagePerformanceMonitoring('coach')` hook
  - Track page load time
  - Track API fetch durations
  - Log performance metrics

- [ ] 7.10 Test Coach page foundation
  - Navigate to Coach page from other tabs
  - Verify data loads correctly
  - Test loading states
  - Test error states
  - Test onboarding flow for new user
  - Test responsive layout on different screen sizes

### 8.0 Race Goals & History Management UI (with Screenshot Upload)

- [ ] 8.1 Create `RaceGoalsManager.tsx` component
  - Display list of race goals sorted by date
  - Show A/B/C priority badges
  - Show countdown to each race
  - Highlight A race prominently
  - "Add Race Goal" button
  - Edit/Delete buttons for each race

- [ ] 8.2 Implement race goal form
  - Modal or inline form for add/edit
  - Fields: race name, race date (date picker), race type/distance, priority (A/B/C selector), target time (optional), notes (optional)
  - Validation: required fields, future date, only one A race
  - Submit handler calls POST or PUT API
  - Update local state on success
  - Show success/error feedback

- [ ] 8.3 Implement race goal delete confirmation
  - Confirmation dialog before delete
  - "Are you sure?" with race name
  - Call DELETE API
  - Update local state on success

- [ ] 8.4 Create `RaceHistoryManager.tsx` component
  - Display race history table (columns: Date, Race Name, Distance, Finish Time)
  - Sort by date descending (most recent first)
  - "Add Race Result" button with dropdown: "Manual Entry" or "Upload Screenshot"
  - Edit/Delete buttons for each race
  - Show PR indicator next to fastest time at each distance

- [ ] 8.5 Implement manual race entry form
  - Modal form for adding race manually
  - Fields: race name, distance (miles), race date (date picker), finish time (hours:minutes)
  - Validation: required fields, reasonable values, last 5 years
  - Submit handler calls POST API
  - Update local state on success

- [ ] 8.6 Create screenshot upload component
  - `ScreenshotUploadModal.tsx` component
  - File input with drag-and-drop support
  - Accept PNG, JPG, JPEG, WebP only
  - Show file preview after selection
  - "Upload & Parse" button
  - Progress indicator during upload/parsing
  - Display "Processing with AI..." message

- [ ] 8.7 Implement screenshot parsing flow
  - On upload button click, send file to `/api/coach/race-history/screenshot`
  - Show loading state during API call
  - On success, receive array of extracted races
  - Display extracted data in editable review table
  - User can edit any field (race name, distance, date, time)
  - User can remove races from the list
  - "Save All Races" button to bulk insert

- [ ] 8.8 Implement review table for extracted races
  - Editable table with parsed race data
  - Inline editing for all fields
  - Validation as user edits
  - Checkbox to include/exclude each race
  - Indicate if date is outside 5-year window (auto-exclude)
  - "Save Selected Races" button calls bulk insert API

- [ ] 8.9 Implement error handling for screenshot upload
  - If parsing fails, show error message
  - Offer "Try Again" or "Manual Entry Instead" options
  - Handle network errors gracefully
  - Show specific error if file too large or wrong format
  - Fallback to manual entry always available

- [ ] 8.10 Create performance summary display
  - `PerformanceSummary.tsx` component
  - Call `/api/coach/race-analysis` to get calculated metrics
  - Display PRs at key distances (5K, 10K, half, marathon, 50K, 50M, 100K, 100M)
  - Display performance trend indicator (↗️ improving, → stable, ↘️ declining) with text explanation
  - Display base fitness assessment summary
  - Update when race history changes

- [ ] 8.11 Style race goals & history components
  - Use existing CSS module styles
  - Card layout for goals and history sections
  - Table styling for race history
  - Badge styling for A/B/C priority
  - Modal styling for forms
  - Responsive design for mobile

- [ ] 8.12 Test race goals & history UI
  - Test adding/editing/deleting race goals
  - Test A race uniqueness enforcement
  - Test manual race entry
  - Test screenshot upload with sample ultrasignup image
  - Test editing parsed race data
  - Test bulk save
  - Test error scenarios
  - Test performance summary calculations
  - Test responsive layout

### 9.0 Training Schedule Configuration UI

- [ ] 9.1 Create `TrainingScheduleConfig.tsx` component
  - Modal or dedicated section for schedule configuration
  - "Edit Training Schedule" button to open
  - Display current schedule if configured, or prompt to configure

- [ ] 9.2 Implement day availability selector
  - Checkbox group for days of week (Mon-Sun)
  - All days selected by default
  - Visual indication of selected days
  - Minimum 1 day required validation

- [ ] 9.3 Implement time block selection per day
  - For each selected day, show time block checkboxes
  - Options: Morning (5am-9am), Midday (9am-5pm), Evening (5pm-9pm), Night (9pm-12am)
  - Multiple selections allowed per day
  - Store in nested object: `{ monday: ['morning', 'evening'], ... }`

- [ ] 9.4 Implement weekly hours input
  - Number input for total weekly training hours
  - Include helper text: "Include all training: running, strength, mobility, etc."
  - Validation: 1-40 hours
  - Show calculation of available time blocks vs requested hours (warn if mismatch)

- [ ] 9.5 Implement fixed constraints input
  - Text area or list builder for constraints
  - Examples shown: "Monday-Friday 9am-5pm", "Pick up kids 3pm weekdays"
  - Each constraint is free text
  - Add/remove constraint buttons
  - Store as array of constraint objects: `[{ type: 'work', description: '...' }]`

- [ ] 9.6 Implement supplemental training preferences
  - Checkbox: "Include strength training" → shows hours per week input
  - Checkbox: "Include mobility/yoga" → shows hours per week input
  - Checkbox: "Include cross-training" → shows type selector and hours per week
  - Cross-training types: Cycling, Swimming, Hiking, Other
  - Validate that supplemental hours don't exceed total weekly hours

- [ ] 9.7 Implement form validation
  - At least 1 day selected
  - At least 1 time block selected per selected day
  - Total weekly hours reasonable (1-40)
  - Supplemental hours ≤ total hours
  - Show validation errors inline
  - Disable save button until valid

- [ ] 9.8 Implement save functionality
  - "Save Schedule" button
  - Call POST `/api/coach/training-schedule`
  - Show loading state during save
  - Show success message on save
  - Update local state
  - Close modal/form
  - Trigger weekly program regeneration (schedule change should update program)

- [ ] 9.9 Display current schedule summary
  - When schedule configured, show summary view
  - "Training {X} days per week, {Y} hours total"
  - List available days and time blocks
  - Show constraints if any
  - Show supplemental training if configured
  - "Edit" button to reopen configuration

- [ ] 9.10 Style training schedule component
  - Card layout
  - Checkbox and input styling
  - Clear visual hierarchy
  - Responsive design
  - Modal styling if using modal

- [ ] 9.11 Test training schedule UI
  - Test day/time block selection
  - Test weekly hours input
  - Test constraints input
  - Test supplemental training
  - Test validation
  - Test save functionality
  - Test edit existing schedule
  - Test responsive layout

### 10.0 Weekly Training Program Display & Timeline Visualization

- [ ] 10.1 Create `TimelineVisualization.tsx` component
  - Horizontal timeline with SVG or CSS
  - Display weeks from now to A race date
  - Color-coded zones for training stages (base=blue, build=green, specificity=orange, taper=yellow)
  - "You Are Here" marker at current week
  - Race markers at appropriate weeks (A/B/C badges)

- [ ] 10.2 Implement timeline rendering logic
  - Calculate timeline width based on number of weeks
  - Position "You Are Here" marker correctly
  - Position race markers at correct week positions
  - Show stage boundaries and labels
  - Handle timelines of various lengths (4 weeks to 52 weeks)

- [ ] 10.3 Make timeline interactive
  - Hover over week shows tooltip with week number and dates
  - Click on race marker shows race details
  - Scroll horizontally if timeline exceeds container width
  - "Scroll to Today" button if timeline is scrolled

- [ ] 10.4 Create `WeeklyProgramDisplay.tsx` component
  - Display 7-day training program
  - Card layout for each day
  - Show day name, date, training type, duration, intensity guidance
  - Show rationale for each day's training
  - Highlight rest days differently
  - Show supplemental work (strength, mobility) on appropriate days

- [ ] 10.5 Display predicted end-of-week metrics
  - Show predicted ACWR and divergence
  - Visual indicators (good/caution/warning colors)
  - Comparison to current metrics ("ACWR will improve from 1.2 to 1.15")
  - Explanation of predictions

- [ ] 10.6 Display performance context from race history
  - Show relevant PRs in context ("Your 50K PR suggests...")
  - Show how current training aligns with goals
  - Display base fitness insights
  - Performance trend indicators

- [ ] 10.7 Move Dashboard recommendations to Coach page
  - Create section for "Current Training Analysis"
  - Fetch existing recommendations from `/api/coach/recommendations`
  - Display daily training decision (today's guidance)
  - Display weekly recommendation (pattern analysis)
  - Display pattern insights (trends)
  - Use existing styling from Dashboard

- [ ] 10.8 Implement manual regenerate button
  - "Regenerate Training Program" button
  - Confirmation dialog: "This will create a new program based on current data"
  - Call POST `/api/coach/weekly-program/generate`
  - Show loading state
  - Update display with new program
  - Show success message with generation timestamp

- [ ] 10.9 Display generation metadata
  - Show when program was generated: "Generated Sunday 6:00 PM"
  - Show next scheduled update: "Next update Wednesday 6:00 PM"
  - Show if using cached program
  - "Program age: 2 days old" indicator

- [ ] 10.10 Style weekly program and timeline components
  - Card layout for program days
  - Timeline styling with stage colors
  - Responsive design (stack vertically on mobile)
  - Clear visual hierarchy
  - Icons for training types (running, strength, rest)

- [ ] 10.11 Test weekly program display
  - Test with various program lengths (3 days/week vs 6 days/week)
  - Test with different training stages
  - Test timeline visualization with different race distances
  - Test manual regeneration
  - Test with race history context
  - Test moved Dashboard recommendations display
  - Test responsive layout

### 11.0 Navigation & Dashboard Integration

- [ ] 11.1 Update navigation in `App.tsx`
  - Add "Coach" tab between "Journal" and "Guide"
  - Verify tab order: Dashboard, Activities, Journal, **Coach**, Guide, Settings
  - Update tab rendering logic
  - Test navigation to/from Coach page

- [ ] 11.2 Update Dashboard to remove LLM recommendations section
  - Locate "Training Recommendations & Analysis" section in `TrainingLoadDashboard.tsx`
  - Remove or comment out the entire recommendations section
  - Keep daily/weekly/pattern recommendations display for Journal page (don't break Journal)
  - Test Dashboard still works without recommendations section

- [ ] 11.3 Add link to Coach page on Dashboard
  - Add prominent card/banner on Dashboard
  - Text: "View your full coaching analysis and weekly training program"
  - Button: "Go to Coach Page"
  - Link to Coach tab
  - Style to match Dashboard aesthetic

- [ ] 11.4 Ensure consistent styling across pages
  - Verify Coach page uses same CSS module as Dashboard
  - Check font sizes, colors, spacing match
  - Test dark mode if applicable
  - Ensure "Powered by Strava" branding present

- [ ] 11.5 Update route handling if needed
  - Verify URL parameter handling for Coach tab (?tab=coach)
  - Test direct navigation to Coach page via URL
  - Test browser back/forward buttons

- [ ] 11.6 Test navigation flow
  - Navigate from Dashboard to Coach
  - Navigate from Coach to other pages
  - Test URL updates correctly
  - Test active tab highlighting
  - Test on mobile (tab navigation)

### 12.0 Scheduled Jobs for Weekly Program Generation

- [ ] 12.1 Create cron endpoint `/cron/weekly-program` in `strava_app.py`
  - Add route with POST method
  - Verify `X-Cloudscheduler` header for security (prevent unauthorized calls)
  - Return 401 if not from Cloud Scheduler
  - Log start of cron job

- [ ] 12.2 Implement active user detection
  - Query for users with activity in last 14 days
  - Exclude users without race goals configured
  - Exclude users without training schedule configured
  - Return list of user IDs to process

- [ ] 12.3 Implement Sunday 6 PM UTC generation logic
  - Determine if current day is Sunday
  - Calculate week_start_date (Monday of current week)
  - For each active user:
    - Call `generate_weekly_training_program(user_id, week_start_date)`
    - Handle errors per user (don't fail entire job if one user fails)
    - Log success/failure per user
  - Track counts: successful, failed, skipped

- [ ] 12.4 Implement Wednesday 6 PM UTC generation logic
  - Determine if current day is Wednesday
  - Calculate remaining days of week (Thu, Fri, Sat, Sun)
  - For each active user:
    - Check actual adherence vs planned program (Mon-Wed)
    - Call `generate_weekly_training_program()` with context about adherence
    - Adjust remaining 4 days based on actual divergence changes
  - Same error handling and logging as Sunday

- [ ] 12.5 Implement error handling and logging
  - Try/except per user to isolate failures
  - Log errors with user_id and stack trace
  - Send error notifications if critical failure
  - Log success metrics (generation time, costs)
  - Return summary JSON: `{ processed: 50, successful: 48, failed: 2, day: 'Sunday' }`

- [ ] 12.6 Add cost tracking
  - Log number of LLM API calls
  - Estimate cost per generation (~$0.02-0.03 per user)
  - Track total monthly costs
  - Alert if costs exceed threshold

- [ ] 12.7 Create Cloud Scheduler configuration
  - Create or document Cloud Scheduler job for Sunday 6 PM UTC
  - Create or document Cloud Scheduler job for Wednesday 6 PM UTC
  - Target: `/cron/weekly-program` endpoint
  - Method: POST
  - Add `X-Cloudscheduler` header
  - Set retry policy (3 retries with exponential backoff)

- [ ] 12.8 Test cron endpoint locally
  - Manually trigger endpoint with test header
  - Verify user selection logic
  - Test Sunday generation for sample users
  - Test Wednesday adjustment logic
  - Verify error handling (simulate API failures)
  - Check logging output

- [ ] 12.9 Test in staging/production
  - Deploy to staging environment
  - Manually trigger Cloud Scheduler jobs
  - Verify generations complete successfully
  - Check database for new weekly_programs entries
  - Verify users see updated programs on Coach page
  - Monitor logs for errors

- [ ] 12.10 Document cron jobs
  - Document schedule (Sunday/Wednesday 6 PM UTC)
  - Document expected behavior
  - Document error handling
  - Document how to manually trigger
  - Document cost estimates
  - Add to operations runbook







