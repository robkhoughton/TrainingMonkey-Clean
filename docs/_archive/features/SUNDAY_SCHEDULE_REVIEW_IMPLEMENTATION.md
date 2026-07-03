# Sunday Schedule Review System - Implementation Status

## ✅ COMPLETED

### Database Schema
- **Migration**: `app/add_schedule_review_tracking.py`
- **New columns in `user_settings`**:
  - `schedule_review_week_start DATE` - tracks which week was reviewed
  - `schedule_review_status VARCHAR(20)` - 'pending', 'accepted', 'updated'
  - `schedule_review_timestamp TIMESTAMP` - when review completed

**To deploy**: Run migration SQL on production database (see file for SQL)

### Backend API Endpoints (in `app/strava_app.py`)

1. **GET `/api/coach/schedule-review-status`**
   - Returns: `{ needs_review: bool, week_start: date, current_status: str, is_sunday: bool }`
   - Logic: needs_review = true if Sunday AND (no review OR different week OR status='pending')

2. **POST `/api/coach/schedule-review-accept`**
   - User accepts current schedule for next week
   - Sets status='accepted', records timestamp, saves week_start

3. **POST `/api/coach/training-schedule` (enhanced)**
   - When user saves schedule on Sunday, auto-marks as reviewed
   - Sets status='updated', records timestamp

## 🚧 IN PROGRESS

### Frontend (CoachPage.tsx)
- ✅ Added state: `scheduleReviewStatus`, `showScheduleReviewBanner`
- ⏳ Need to add:
  1. `fetchScheduleReviewStatus()` function
  2. Call it in `useEffect` or `fetchCoachData`
  3. Sunday banner UI (between countdown and timeline)
  4. Handle "Keep Current Schedule" button → calls accept API
  5. Handle "Update Schedule" button → navigates to Training Schedule tab

### Banner UI Design
```tsx
{scheduleReviewStatus?.needs_review && showScheduleReviewBanner && (
  <div className={styles.card} style={{
    marginBottom: '0.75rem',
    padding: '1rem',
    backgroundColor: '#fff3cd',
    border: '2px solid #ffc107',
    borderRadius: '8px'
  }}>
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      <div>
        <h3 style={{ margin: 0, marginBottom: '0.5rem', color: '#856404' }}>
          📅 Review Your Training Schedule for Next Week
        </h3>
        <p style={{ margin: 0, color: '#856404', fontSize: '14px' }}>
          Week of {formatDate(scheduleReviewStatus.week_start)} - Confirm your availability before Sunday 6 PM
        </p>
      </div>
      <div style={{ display: 'flex', gap: '0.5rem' }}>
        <button onClick={handleAcceptSchedule} style={{...}}>
          ✓ Keep Current Schedule
        </button>
        <button onClick={() => setActiveSubTab('schedule')} style={{...}}>
          ✏️ Update Schedule
        </button>
      </div>
    </div>
  </div>
)}
```

## ⏳ TODO

### 1. Complete Frontend Implementation
- Add `fetchScheduleReviewStatus()` to CoachPage
- Add banner component
- Add `handleAcceptSchedule()` function
- Add `handleDismissBanner()` (sets showScheduleReviewBanner=false)

### 2. Update Cron Job
File: `app/strava_app.py` → `/cron/weekly-program`

Add to Sunday 6 PM UTC cron:
```python
# Reset schedule review status for all users on Sunday
logger.info("Resetting schedule review status for new week...")
db_utils.execute_query(
    """
    UPDATE user_settings
    SET schedule_review_status = 'pending'
    WHERE schedule_review_week_start IS NULL 
       OR schedule_review_week_start < CURRENT_DATE
    """
)
```

### 3. Testing Checklist
- [ ] Migration runs successfully on production
- [ ] API endpoints return correct data
- [ ] Banner appears on Sunday
- [ ] Banner disappears after "Keep Current Schedule"
- [ ] Banner disappears after updating schedule
- [ ] Banner doesn't appear Monday-Saturday
- [ ] Cron job resets status on Sunday
- [ ] Weekly program generation uses current schedule if not reviewed

## User Flow

### Sunday Afternoon (User visits Coach page)
1. User sees banner: "Review Your Training Schedule for Next Week"
2. Options:
   - **Keep Current Schedule** → API call → banner disappears → done
   - **Update Schedule** → Navigate to Training Schedule tab → User edits → Save → banner disappears

### Sunday 6 PM UTC (Cron Job)
1. Check each user's `schedule_review_status`
2. If 'accepted' or 'updated' → use current schedule
3. If 'pending' → use current schedule (default)
4. Generate weekly program
5. Reset all users to 'pending' for next week

### Monday-Saturday
- Banner does not appear
- User can update schedule anytime via Training Schedule tab
- No review prompt

## Database Migration SQL

```sql
ALTER TABLE user_settings
ADD COLUMN IF NOT EXISTS schedule_review_week_start DATE,
ADD COLUMN IF NOT EXISTS schedule_review_status VARCHAR(20) DEFAULT 'pending',
ADD COLUMN IF NOT EXISTS schedule_review_timestamp TIMESTAMP;
```

## Files Modified
- ✅ `app/add_schedule_review_tracking.py` (new)
- ✅ `app/strava_app.py` (3 new endpoints, enhanced save endpoint)
- 🚧 `frontend/src/CoachPage.tsx` (state added, banner pending)
- ⏳ `app/strava_app.py` (cron job update pending)

