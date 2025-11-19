# "Mark as Rest Day" Button Implementation
**Date**: November 1, 2025  
**Feature**: Explicit rest day declaration for recommendation generation

## Problem Statement

User scenario:
- Planning a rest day today (no workout)
- Wants to see tomorrow's prescribed workout now
- System doesn't distinguish between:
  - **Planned rest day** (wants recommendation)
  - **Activity not synced yet** (Strava pending)
  - **Day in progress** (might workout later)

Dashboard "Generate" button doesn't help because:
- It doesn't create a new recommendation if one already exists
- System doesn't know today is intentionally a rest day
- No trigger for auto-generation workflow

---

## Solution: Explicit Rest Day Declaration

### User Flow
```
Today is planned rest day
    ↓
Open Journal page → See today's row
    ↓
Notice "Actual Activity: Rest Day"
    ↓
Click [🛌 Mark as Rest Day] button
    ↓
System saves journal entry with rest flag
    ↓
Auto-generates tomorrow's recommendation
    ↓
Tomorrow's row updates immediately with recommendation
    ↓
Success message: "🛌 Rest day marked! Tomorrow's workout recommendation generated"
```

---

## Implementation Details

### Backend Changes

#### File: `app/strava_app.py` - `save_journal_entry()`

**Added rest day flag**:
```python
is_rest_day = data.get('is_rest_day', False)  # NEW: Rest day flag
```

**Modified generation trigger**:
```python
# Generate recommendation if:
# 1. Autopsy was generated (normal flow with workout)
# 2. Rest day explicitly marked (no workout, but user wants tomorrow's plan)
if autopsy_generated or is_rest_day:
    try:
        if is_rest_day:
            logger.info(f"Rest day marked for {date_str} - generating tomorrow's recommendation without autopsy")
        else:
            logger.info(f"Auto-generating autopsy-informed recommendation after journal save for {date_str}")
            
        from llm_recommendations_module import generate_recommendations
        
        recommendation = generate_recommendations(force=True, user_id=current_user.id)
        if recommendation:
            recommendation_generated = True
```

**Key Logic**:
- Rest day bypasses autopsy (no workout to analyze)
- Still triggers tomorrow's recommendation generation
- Uses `force=True` to regenerate even if old recommendation exists
- Based on current metrics and training history

**Enhanced Response Messages**:
```python
if is_rest_day and recommendation_generated:
    response_data['user_message'] = (
        "🛌 Rest day marked! Tomorrow's workout recommendation generated based on your current metrics."
    )
    response_data['is_rest_day'] = True
    response_data['recommendation_generated'] = True
```

---

### Frontend Changes

#### File: `frontend/src/JournalPage.tsx`

**Added button in Actions column** (lines 684-700):
```typescript
// NEW: State 0 - Today with no activity, show "Mark as Rest Day" button
if (isToday && isRestDay && !isSaved) {
  return (
    <button
      onClick={() => handleMarkRestDay(entry.date)}
      disabled={isCurrentlySaving}
      className={`${styles.journalButton} ${isCurrentlySaving ? styles.buttonSaving : styles.buttonSave}`}
      style={{
        backgroundColor: '#9333ea',  // Purple color for rest days
        color: 'white',
        border: 'none'
      }}
    >
      {isCurrentlySaving ? '🛌 Marking...' : '🛌 Mark as Rest Day'}
    </button>
  );
}
```

**When Button Appears**:
- `isToday` - Only on today's row
- `isRestDay` - No activity or activity type is 'rest'
- `!isSaved` - Not already marked as rest

**Added handler function** (lines 228-272):
```typescript
const handleMarkRestDay = async (date: string) => {
  try {
    setIsSaving(date);

    const response = await fetch('/api/journal', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        date: date,
        is_rest_day: true,  // Flag for backend
        notes: 'Rest Day'    // Optional note
      }),
    });

    if (!response.ok) {
      throw new Error('Failed to mark rest day');
    }

    const result = await response.json();
    
    if (result.user_message) {
      alert(result.user_message);  // Show success message
    }

    // Mark as saved
    setSavedEntries(prev => new Set(prev).add(date));

    // Refresh journal data to get tomorrow's updated recommendation
    await fetchJournalData(centerDate);

  } catch (error) {
    console.error('Error marking rest day:', error);
    alert(`Failed to mark rest day: ${error.message}`);
  } finally {
    setIsSaving(null);
  }
};
```

**Handler Features**:
- Shows loading state while processing
- Sends `is_rest_day: true` flag to backend
- Displays success message from backend
- Refreshes page to show updated tomorrow's recommendation
- Handles errors gracefully

---

## Visual Design

### Today's Row with No Activity
```
┌────────────────────────────────────────────────────────────┐
│ Sat, Nov 1 (TODAY)                                         │
│ Actual Activity: Rest Day                                  │
│ Energy: __ RPE: __ Pain: __ Notes: ________________        │
│                                                             │
│ Alignment: -    Actions: [🛌 Mark as Rest Day]           │
└────────────────────────────────────────────────────────────┘
```

**Button Styling**:
- **Color**: Purple (`#9333ea`) - distinct from Save (blue) and Analysis (green)
- **Icon**: 🛌 (bed emoji) - clear visual indicator
- **Label**: "Mark as Rest Day" - explicit intent
- **Loading**: "🛌 Marking..." - shows progress

### After Clicking Button
```
┌────────────────────────────────────────────────────────────┐
│ Sat, Nov 1 (TODAY)                                         │
│ Actual Activity: Rest Day                                  │
│ Energy: __ RPE: __ Pain: __ Notes: Rest Day                │
│                                                             │
│ Alignment: -    Actions: [✅ Saved!]                       │
└────────────────────────────────────────────────────────────┘

Alert: "🛌 Rest day marked! Tomorrow's workout recommendation 
        generated based on your current metrics."

┌────────────────────────────────────────────────────────────┐
│ Sun, Nov 2 (TOMORROW) NEXT WORKOUT                         │
│ ╔════════════════════════════════════════════════════════╗ │
│ ║ 🤖 AI Training Decision for Tomorrow                  ║ │
│ ║                                                        ║ │
│ ║ ASSESSMENT: 6 days since rest complete. External     ║ │
│ ║ ACWR 1.05, internal 1.06 positioned optimally...     ║ │
│ ║                                                        ║ │
│ ║ TODAY: Execute quality moderate workout, Zone 2-3... ║ │
│ ╚════════════════════════════════════════════════════════╝ │
└────────────────────────────────────────────────────────────┘
```

**Note**: Tomorrow's recommendation appears WITHOUT the "🧠 Autopsy-Informed" badge (no workout to analyze)

---

## User Scenarios

### Scenario 1: Planned Rest Day (Your Case)
```
1. Wake up, decide to take rest day
2. Open Journal page
3. See today's row shows "Rest Day" in Activity
4. Click [🛌 Mark as Rest Day]
5. Get success message
6. Tomorrow's row populates with recommendation
7. Can plan tomorrow's workout now
```

### Scenario 2: Rest Day After Workout Recorded
```
1. Complete workout, syncs to Strava
2. Later decide it's actually a rest day (misclick?)
3. Journal shows actual activity
4. Button hidden (activity exists)
5. User can still enter observations normally
```

### Scenario 3: Workout Coming Later Today
```
1. Morning: No activity yet
2. See [🛌 Mark as Rest Day] button
3. DON'T click it (planning to workout later)
4. Afternoon: Complete workout, syncs
5. Journal refreshes, shows activity
6. Button disappears, normal Save button appears
```

---

## Technical Notes

### Why `force=True` in Generation?
```python
recommendation = generate_recommendations(force=True, user_id=current_user.id)
```

Without `force=True`:
- System checks if recommendation already exists
- Sees old recommendation → skips generation
- User gets stale recommendation

With `force=True`:
- Always generates new recommendation
- Overrides existing recommendation
- Uses current metrics and latest training data

### Why No Autopsy for Rest Days?
```python
if has_prescribed_action and has_actual_activity:
    generate_autopsy_for_date(date_str, current_user.id)
    autopsy_generated = True
```

Autopsy requires:
- Prescribed action (what AI recommended)
- Actual activity (what you did)

Rest day has no actual activity → no autopsy possible

But recommendation still generates using:
- Current ACWR values
- Days since rest
- Recent training patterns
- Normalized divergence

---

## Benefits

### 1. **Explicit User Intent**
- System knows rest day is intentional
- Not waiting for activity that never comes
- Clear distinction from "activity pending"

### 2. **Immediate Recommendation**
- Don't need to wait for Dashboard workarounds
- One click in Journal generates tomorrow's plan
- Natural workflow: mark rest → see tomorrow

### 3. **Preserves Workflow Consistency**
- Same auto-generation behavior as workout days
- Tomorrow's row updates automatically
- No manual "Generate" button needed

### 4. **Clean UX**
- Button only appears when relevant (today + no activity)
- Purple color distinguishes from other actions
- Clear loading and success feedback

---

## Testing Checklist

### Before Deployment
- [ ] Backend accepts `is_rest_day` flag
- [ ] Backend generates recommendation without autopsy
- [ ] Backend returns appropriate success message
- [ ] Frontend button appears on today's row with no activity
- [ ] Frontend button calls API with correct payload
- [ ] Frontend refreshes to show tomorrow's recommendation
- [ ] Success message displays properly

### After Deployment
- [ ] Navigate to Journal
- [ ] Verify today (rest day) shows button
- [ ] Click [🛌 Mark as Rest Day]
- [ ] Verify success message appears
- [ ] Verify tomorrow's row shows recommendation
- [ ] Verify recommendation does NOT have autopsy badge
- [ ] Check Dashboard shows same recommendation

---

## Files Modified

**Backend**:
- `app/strava_app.py` - Added `is_rest_day` flag handling and generation logic

**Frontend**:
- `frontend/src/JournalPage.tsx` - Added button and handler

**No Schema Changes**: Uses existing journal_entries table

---

## Deployment

```bash
cd frontend
npm run build

scripts\build_and_copy.bat
scripts\deploy_strava_simple.bat
```

---

## Expected Behavior After Deployment

**Your Current Situation**:
1. Today is rest day (no activity)
2. Open Journal page
3. See today's row: [🛌 Mark as Rest Day]
4. Click button
5. Alert: "🛌 Rest day marked! Tomorrow's workout recommendation generated..."
6. Tomorrow's row updates with recommendation
7. You can now see Sunday's prescribed workout!

**Recommendation Will**:
- Use your current External ACWR, Internal ACWR
- Consider 6+ days since rest
- Factor in normalized divergence
- Provide scientifically sound guidance
- NOT have autopsy badge (no workout to analyze)

---

## Success Criteria

✅ Button only appears on today's row with no activity  
✅ Clicking button generates tomorrow's recommendation  
✅ Tomorrow's row updates immediately after click  
✅ Success message clearly explains what happened  
✅ Button disappears after marking (shows "Saved!")  
✅ Recommendation appears in both Journal and Dashboard  
✅ Works for genuine rest days without confusion  

**Rest days now have first-class support in the workflow!** 🛌➡️🏃









