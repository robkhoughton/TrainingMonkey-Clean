# 📧 Email Enforcement - Quick Reference Card

**Print this or pin to desktop!**

---

## ⏰ When to Act

| Days Since Phase 1 | Action | File to Edit |
|-------------------|--------|--------------|
| **5-7 days** | Deploy Phase 2 | `app/email_enforcement.py` |
| **21-28 days** | Deploy Phase 3 | `app/email_enforcement.py` |

---

## 🔍 Weekly Check (Run This SQL)

```sql
SELECT 
    CASE 
        WHEN EXTRACT(DAY FROM (NOW() - registration_date)) <= 3 THEN 'grace'
        WHEN EXTRACT(DAY FROM (NOW() - registration_date)) <= 7 THEN 'soft'
        WHEN EXTRACT(DAY FROM (NOW() - registration_date)) <= 14 THEN 'medium'
        ELSE 'hard'
    END as level,
    COUNT(*) as users
FROM user_settings
WHERE email LIKE '%@training-monkey.com'
GROUP BY level;
```

---

## ⚙️ Enable Phase 2 (3 simple edits)

**File:** `app/email_enforcement.py`

**Line 67 - Change:**
```python
'should_show_modal': False,  # Phase 1: disabled
# TO:
'should_show_modal': True,   # Phase 2: enabled
```

**Line 76 - Change:**
```python
'should_show_modal': False,  # Phase 1: disabled
# TO:
'should_show_modal': True,   # Phase 2: enabled
```

**Then:** Deploy + integrate modal UI

---

## ⚙️ Enable Phase 3 (1 edit + blocking logic)

**File:** `app/email_enforcement.py`

**Line 85 - Change:**
```python
'should_block_access': False,  # Phase 1: disabled - no blocking
# TO:
'should_block_access': True,   # Phase 3: enabled - hard block
```

**Then:** Deploy + add blocking redirect in `strava_app.py`

---

## 🚨 Emergency Disable

**File:** `app/strava_app.py` (line ~1894)

**Comment out the TODO line:**
```python
# TODO: Enable Phase 2 in 5-7 days - see EMAIL_ENFORCEMENT_ROADMAP.md
# ↑ Just add return statement here:
return send_from_directory('build', 'index.html')  # Skip all tracking
```

Or delete: `app/email_enforcement.py`

---

## 📊 Success Metrics

**Current:** 12% real emails (4/33 users)

**After Phase 2:** Target 40-50% real emails  
**After Phase 3:** Target 80%+ real emails

---

## 📁 Full Documentation

- `EMAIL_ENFORCEMENT_ROADMAP.md` - Complete timeline & checklists
- `EMAIL_ENFORCEMENT_PHASES.md` - Technical details
- `PHASE1_DEPLOYMENT_SUMMARY.md` - Current deployment status

---

**Calendar Reminders:** Set these NOW!
- [ ] Deploy date + 5 days
- [ ] Deploy date + 7 days  
- [ ] Phase 2 date + 14 days
- [ ] Phase 2 date + 21 days



