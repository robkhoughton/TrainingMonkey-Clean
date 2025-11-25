# Email Enforcement Implementation - Phased Rollout

## Current Status: Phase 1 - Passive Tracking ✅

**Deployed:** Phase 1 only  
**User Impact:** None (100% silent tracking)  
**Purpose:** Monitor and validate the logic before enabling user-facing changes

---

## Phase 1: Passive Tracking (ACTIVE)

### What It Does
- Tracks days since registration for all users
- Calculates email "urgency level" (none/soft/medium/hard)
- Logs tracking data to application logs
- **Does NOT show any modals or block access**

### Implementation
- `app/email_enforcement.py` - Core logic module
- `app/strava_app.py` (line ~1893) - Dashboard tracking call
- Database: Uses existing `registration_date` and `email_modal_dismissals` columns

### Urgency Levels (Calculated but Not Enforced)
```
Days 1-3:   Level 'none'   - Grace period
Days 4-7:   Level 'soft'   - Would show dismissible modal
Days 8-14:  Level 'medium' - Would show persistent banner  
Days 15+:   Level 'hard'   - Would block access
```

### Monitoring
Check application logs for entries like:
```
[EMAIL_TRACKING] User 58 | Level: medium | Days: 10 | Message: Day 10 - would show persistent banner (disabled in Phase 1)
```

### Safety Features
- ✅ Automatic bypass for users with real emails
- ✅ Automatic bypass for admin accounts
- ✅ Fails silently if any error occurs (no user disruption)
- ✅ All enforcement flags set to `False`

---

## Phase 2: Soft Prompts (NOT YET DEPLOYED)

### What It Will Do
- Days 4-7: Show dismissible modal (once per session)
- Days 8-14: Show persistent top banner
- Still no blocking - purely educational

### To Enable Phase 2
In `app/email_enforcement.py`, modify the `get_email_urgency_level()` function:

**Change Line 67:**
```python
# FROM:
'should_show_modal': False,  # Phase 1: disabled

# TO:
'should_show_modal': True,  # Phase 2: enabled
```

**Change Line 76:**
```python
# FROM:
'should_show_modal': False,  # Phase 1: disabled

# TO:
'should_show_modal': True,  # Phase 2: enabled
```

**Then integrate modal UI:**
- Add `app/templates/email_collection_modal.html` to dashboard
- Wire up `/api/user/dismiss-email-modal` endpoint
- Style persistent banner for medium urgency

---

## Phase 3: Hard Block (NOT YET DEPLOYED)

### What It Will Do
- Day 15+: Redirect to "Email Required" page
- User must provide email to continue using app
- Can still add email and get full access back

### To Enable Phase 3
In `app/email_enforcement.py`, modify line 85:

**Change:**
```python
# FROM:
'should_block_access': False,  # Phase 1: disabled - no blocking

# TO:
'should_block_access': True,  # Phase 3: enabled - hard block
```

**Then implement blocking logic:**
In `app/strava_app.py`, modify the dashboard route (~line 1904):

```python
urgency = get_email_urgency_level(user_data)

# Add this check:
if urgency['should_block_access']:
    return redirect('/email-required')

log_email_enforcement_status(current_user.id, urgency)
```

**Create `/email-required` page:**
- Simple form to collect email
- POST to `/api/user/update-email`
- Redirect back to dashboard on success

---

## Rollback Instructions

### Emergency Disable (If Issues Arise)
In `app/strava_app.py`, comment out the tracking block (~lines 1893-1909):

```python
@app.route('/dashboard')
@login_required
def dashboard():
    """Serve React dashboard"""
    # # Phase 1: Track email enforcement status (passive monitoring only)
    # try:
    #     from email_enforcement import get_email_urgency_level, log_email_enforcement_status
    #     ...
    # except Exception as e:
    #     logger.error(...)
    
    response = send_from_directory('build', 'index.html')
    ...
```

### Complete Removal
Delete these files:
- `app/email_enforcement.py`
- `EMAIL_ENFORCEMENT_PHASES.md` (this file)

---

## Testing Phase 1

### Test Scenarios

**Scenario 1: User with Real Email**
- Expected Log: "User has real email" (level: none)
- Expected Behavior: No tracking logged

**Scenario 2: New User (Day 1-3)**
- Expected Log: "Day X - grace period" (level: none)
- Expected Behavior: Silent

**Scenario 3: User on Day 8**
- Expected Log: "Day 8 - would show persistent banner (disabled in Phase 1)"
- Expected Behavior: No modal/banner shown, just logged

**Scenario 4: User on Day 20**
- Expected Log: "Day 20 - would block access (disabled in Phase 1)"
- Expected Behavior: No blocking, just logged

### Validation Query
Run this to see current state of all users:

```sql
SELECT 
    id,
    email,
    registration_date,
    EXTRACT(DAY FROM (NOW() - registration_date)) as days_registered,
    CASE 
        WHEN email NOT LIKE '%@training-monkey.com' THEN 'real'
        ELSE 'synthetic'
    END as email_type,
    CASE 
        WHEN EXTRACT(DAY FROM (NOW() - registration_date)) <= 3 THEN 'grace'
        WHEN EXTRACT(DAY FROM (NOW() - registration_date)) <= 7 THEN 'soft'
        WHEN EXTRACT(DAY FROM (NOW() - registration_date)) <= 14 THEN 'medium'
        ELSE 'hard'
    END as would_be_level
FROM user_settings
WHERE email LIKE '%@training-monkey.com'
ORDER BY days_registered DESC;
```

---

## Next Steps

1. **Monitor Phase 1** for 3-5 days
   - Check logs for any errors
   - Verify logic is correct
   - Review user distribution across urgency levels

2. **Deploy Phase 2** when confident
   - Enable modal display flags
   - Integrate UI components
   - Monitor dismissal rates

3. **Deploy Phase 3** after 1-2 weeks
   - Enable hard block flag
   - Create email-required page
   - Monitor conversion rates

---

## Success Metrics

**Phase 1:**
- ✅ Zero user complaints
- ✅ Zero errors in logs
- ✅ Accurate urgency calculations

**Phase 2:**
- Target: 30% of soft-prompted users add email
- Target: 50% of medium-prompted users add email

**Phase 3:**
- Target: 80% of hard-blocked users add email
- Acceptable: 10% churn rate for persistent non-compliers

---

## Support

If users report issues or you need to adjust timelines:
- Modify day thresholds in `get_email_urgency_level()` function
- Adjust grace period (currently 3 days)
- Extend soft/medium periods as needed






