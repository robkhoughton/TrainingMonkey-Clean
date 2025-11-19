# 📧 Email Enforcement Implementation Roadmap

**Current Status:** Phase 1 Deployed (Passive Tracking)  
**Deployment Date:** _________________ (fill this in when you deploy!)

---

## 🗓️ Timeline & Triggers

### ✅ Phase 1: Passive Tracking (CURRENT)
**Duration:** 3-7 days  
**Action Required:** Monitor only  

**Check on:** _________________ (deploy date + 5 days)

**What to Look For:**
- [ ] No errors in logs
- [ ] `[EMAIL_TRACKING]` entries appearing
- [ ] Dashboard loads normally for all users
- [ ] No user complaints

**If Everything Looks Good → Proceed to Phase 2**

---

### ⏳ Phase 2: Soft Prompts (NEXT)
**When:** 5-7 days after Phase 1 deployment  
**Expected Date:** _________________ (calculate: deploy date + 5-7 days)

**Trigger to Deploy:**
- ✅ Phase 1 ran for 3+ days with no issues
- ✅ You reviewed the monitoring query results
- ✅ You're comfortable with the user distribution

**Implementation Time:** 1-2 hours (modal integration)

**Action Items:**
1. [ ] Run the monitoring query (see below)
2. [ ] Review which users are in each urgency level
3. [ ] Enable Phase 2 flags in `email_enforcement.py`
4. [ ] Integrate modal UI into dashboard
5. [ ] Deploy and monitor

**Expected Impact:**
- ~20-40% of users will see dismissible modal (days 4-7)
- ~30-50% will see persistent banner (days 8-14)
- Zero blocking - all prompts are skippable

---

### ⏳ Phase 3: Hard Block (FUTURE)
**When:** 14-21 days after Phase 2 deployment  
**Expected Date:** _________________ (calculate: Phase 2 date + 14-21 days)

**Trigger to Deploy:**
- ✅ Phase 2 ran for 2+ weeks
- ✅ You reviewed email collection rates
- ✅ Modal dismissal rates are acceptable
- ✅ You're ready to enforce email requirement

**Implementation Time:** 2-3 hours (blocking logic + email-required page)

**Action Items:**
1. [ ] Analyze Phase 2 success rates
2. [ ] Create `/email-required` page
3. [ ] Enable Phase 3 blocking flag
4. [ ] Deploy and closely monitor
5. [ ] Watch for user churn

**Expected Impact:**
- Users 15+ days old with synthetic emails will be blocked
- They must provide email to continue
- Some churn expected (10-15%)

---

## 📊 Monitoring Query - Run This Weekly

Copy/paste into your SQL editor:

```sql
-- Email Enforcement Status Report
SELECT 
    CASE 
        WHEN EXTRACT(DAY FROM (NOW() - registration_date)) <= 3 THEN '1_grace_period'
        WHEN EXTRACT(DAY FROM (NOW() - registration_date)) <= 7 THEN '2_soft_prompt'
        WHEN EXTRACT(DAY FROM (NOW() - registration_date)) <= 14 THEN '3_medium_prompt'
        ELSE '4_hard_block'
    END as urgency_level,
    COUNT(*) as user_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) as percentage,
    ARRAY_AGG(id ORDER BY registration_date DESC LIMIT 3) as sample_user_ids
FROM user_settings
WHERE email LIKE '%@training-monkey.com'
GROUP BY urgency_level
ORDER BY urgency_level;
```

**What to Look For:**
- How many users are in each level?
- Are thresholds (3, 7, 14 days) appropriate?
- Should you adjust timelines?

---

## 🔔 Calendar Reminders (Set These Now!)

**Reminder 1: Check Phase 1**
- **Date:** Deploy date + 5 days
- **Action:** Run monitoring query, check logs
- **Decision:** Deploy Phase 2 or wait?

**Reminder 2: Deploy Phase 2**
- **Date:** Deploy date + 7 days
- **Action:** Enable soft prompts, integrate modal
- **File:** `EMAIL_ENFORCEMENT_PHASES.md` has instructions

**Reminder 3: Check Phase 2 Results**
- **Date:** Phase 2 deploy + 14 days
- **Action:** Review email collection rates
- **Decision:** Deploy Phase 3 or adjust?

**Reminder 4: Deploy Phase 3**
- **Date:** Phase 2 deploy + 21 days
- **Action:** Enable hard blocking
- **File:** `EMAIL_ENFORCEMENT_PHASES.md` has instructions

---

## 🚨 Red Flags - Deploy Next Phase If You See These

### From Logs:
```
[EMAIL_TRACKING] User 58 | Level: hard | Days: 45 | Message: Day 45 - would block access
```
→ **User is 45 days old and still has synthetic email - time to be more aggressive**

### From Monitoring Query:
```
4_hard_block | 15 users | 51.7%
```
→ **Over half your users would be blocked - Phase 3 is overdue**

### From User Reports:
- "I lost access to my account" → Phase 3 might be too aggressive
- "How do I change my email?" → Phase 2 needs better UX
- "I can't connect Strava" → OAuth scope issue (unrelated)

---

## 📁 Implementation Checklists

### Phase 2 Checklist (Soft Prompts)

**Before You Start:**
- [ ] Phase 1 ran for 3+ days successfully
- [ ] No errors in application logs
- [ ] You ran the monitoring query

**Code Changes:**
- [ ] Edit `app/email_enforcement.py` lines 67 and 76
  - Change `'should_show_modal': False` to `True`
- [ ] Add `email_collection_modal.html` to dashboard template
- [ ] Wire up dismissal tracking API
- [ ] Test locally (if possible) or deploy to staging

**Deployment:**
- [ ] Deploy modified files
- [ ] Test as a user (check dashboard)
- [ ] Monitor logs for first 24 hours
- [ ] Check modal dismissal rates after 3 days

**Success Metrics:**
- [ ] 30%+ of soft-prompted users add email
- [ ] 50%+ of medium-prompted users add email
- [ ] < 5% of users report frustration

---

### Phase 3 Checklist (Hard Block)

**Before You Start:**
- [ ] Phase 2 ran for 14+ days
- [ ] Email collection rates are acceptable
- [ ] You're mentally prepared for potential churn

**Code Changes:**
- [ ] Create `/email-required` page (HTML template)
- [ ] Edit `app/email_enforcement.py` line 85
  - Change `'should_block_access': False` to `True`
- [ ] Add blocking logic to `strava_app.py` dashboard route
- [ ] Test blocking logic thoroughly

**Deployment:**
- [ ] Deploy during low-traffic hours
- [ ] Monitor VERY closely for first 6 hours
- [ ] Be ready to rollback if issues arise
- [ ] Respond to user support requests quickly

**Success Metrics:**
- [ ] 80%+ of blocked users add email
- [ ] < 15% churn rate
- [ ] Support volume is manageable

---

## 🔄 If You Need to Adjust Timeline

**Extend Grace Period:**
Edit `email_enforcement.py` line 60:
```python
# FROM:
if days <= 3:

# TO:
if days <= 7:  # Give users a full week
```

**Make Phase 2 Less Aggressive:**
Extend thresholds:
```python
elif days <= 14:  # Instead of 7
    return {
        'level': 'soft',
        ...
    }
```

**Skip Phase 3 Entirely:**
Just leave blocking disabled forever. Use Phase 2 prompts indefinitely.

---

## 📞 Quick Reference

**Enable Phase 2:**
- File: `app/email_enforcement.py`
- Lines: 67, 76
- Change: `False` → `True` for `should_show_modal`

**Enable Phase 3:**
- File: `app/email_enforcement.py`  
- Line: 85
- Change: `False` → `True` for `should_block_access`

**Check Current Status:**
- Logs: Search for `[EMAIL_TRACKING]`
- SQL: Run monitoring query above
- Code: Check flags in `email_enforcement.py`

**Rollback Any Phase:**
- Revert the `False` → `True` changes
- Or comment out tracking in `strava_app.py`
- Or delete `email_enforcement.py` entirely

---

## 🎯 Success = Getting to 80%+ Real Emails

**Current State:** 12.1% real emails (4 out of 33 users)  
**Target State:** 80%+ real emails  

**Realistic Expectations:**
- Phase 1: No change (just tracking)
- Phase 2: +30-40% adoption (soft prompts)
- Phase 3: +70-80% adoption (hard block)
- Final churn: 10-15% of synthetic email users

**Best Case:** 28+ users with real emails  
**Acceptable:** 24+ users with real emails  
**Need to Reassess:** < 20 users with real emails

---

## 📝 Notes Section (Use This!)

**Phase 1 Observations:**
- Deploy date: _________________
- Issues found: _________________
- User distribution: _________________
- Ready for Phase 2: YES / NO / ADJUST

**Phase 2 Observations:**
- Deploy date: _________________
- Modal shown to: _____ users
- Emails collected: _____ (___%)
- Issues found: _________________
- Ready for Phase 3: YES / NO / NEVER

**Phase 3 Observations:**
- Deploy date: _________________
- Users blocked: _____
- Emails collected: _____ (___%)
- Churn: _____ (___%)
- Final decision: _________________

---

**🔖 BOOKMARK THIS FILE** - It's your roadmap for the next 4-6 weeks.


