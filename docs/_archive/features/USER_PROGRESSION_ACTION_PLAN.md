# TrainingMonkey User Progression - Action Plan

## TL;DR - The Critical Path

```
🎯 GOAL: Get 80% of new users to "Active" status within 7 days

📊 CURRENT STATE:
- 100% connect Strava (✅ Great!)
- 15% use journal (🔴 Problem!)
- 55% active at 30 days (⚠️ Below target)

🎪 THE MAGIC SEQUENCE:
Minutes 0-10:   Landing → "Aha Moment" → Strava Connect
Minutes 10-30:  Sync Progress → Education → Email sent
Minutes 30-60:  First Dashboard → Hero Insight → Clear Action
Day 1:          Morning Email → Training → Evening Log
Days 2-7:       Daily Loop Repeat → Build Habit
Days 7-21:      "Told You So" Moment → Emotional Hook
Days 21-90:     Advanced Features → Mastery Path
```

---

## PHASE 1: THE FIRST 10 MINUTES
**Objective:** Create "I've never seen this before" moment

### Current Flow:
```
Landing Page → Connect Strava → Wait → Dashboard
```

### Problems Identified:
1. Demo is good but doesn't emphasize DIVERGENCE enough
2. No emotional priming before connect
3. No expectation setting for what happens next

### Quick Wins (Implement This Week):

#### 1. Enhance Landing Page Demo
**File:** `app/templates/landing.html`

Add before Strava button:
```html
<div class="divergence-highlight">
  <h3>The Metric Your Garmin Doesn't Show You</h3>
  <div class="demo-divergence">
    <div class="divergence-bad">
      -15.2% ⚠️
      <p>Overtraining Territory</p>
    </div>
    <div class="divergence-good">
      -3.1% ✅
      <p>Optimal Training Zone</p>
    </div>
  </div>
  <p><strong>Training Divergence</strong> predicts injuries weeks before they happen.
     Your Garmin can't calculate this. We can.</p>
</div>
```

#### 2. Add Pre-Connect Assessment (Optional Enhancement)
3-question quiz before Strava connect to increase commitment:
- "How often do you worry about training too much?"
- "Have you been injured in the last year?"
- "Do you have a coach?"

This primes them for the solution.

---

## PHASE 2: THE WAITING PERIOD (10-30 Minutes)
**Objective:** Keep engagement during sync, set expectations

### Current Flow:
```
Connect Strava → ??? → Hope they come back
```

### Problems Identified:
- **3 users (9%) never came back** after connecting Strava
- No indication of how long sync takes
- No engagement during wait
- No email notification when ready

### Critical Fixes (URGENT):

#### 1. Add Sync Progress Page
**File:** `app/templates/strava_setup.html` or create new

```html
<div class="sync-progress">
  <h2>Your Training Monkey is Analyzing Your Data</h2>
  
  <div class="progress-tracker">
    <div class="step completed">
      ✅ Connected to Strava
    </div>
    <div class="step in-progress">
      🔄 Importing activities (47 found)
    </div>
    <div class="step pending">
      ⏳ Calculating heart rate metrics
    </div>
    <div class="step pending">
      ⏳ Analyzing training patterns
    </div>
  </div>

  <div class="wait-education">
    <h3>While You Wait... What is Training Divergence?</h3>
    <video><!-- 90-second explainer --></video>
    
    <h3>How We Caught This Runner's Overtraining 3 Weeks Early</h3>
    <div class="case-study"><!-- Success story --></div>
  </div>

  <div class="email-signup">
    <p>⏱️ This usually takes 5-10 minutes</p>
    <p>We'll email you at <strong>{user_email}</strong> when your insights are ready.</p>
    <button>Notify me when ready</button>
    <p><small>Or stick around and watch the magic happen! ✨</small></p>
  </div>
</div>
```

#### 2. Send Email When Sync Complete
**File:** `app/strava_app.py` - Add after successful sync

```python
def send_sync_complete_email(user_id, user_email):
    """Send email when data sync is complete"""
    subject = "🐵 Your Training Monkey Found Something Interesting"
    
    body = f"""
    Hi there!
    
    Your Training Monkey just finished analyzing {activity_count} activities.
    
    Here's what we found:
    
    📊 Your Training Status: {status_color}
    🎯 Today's Recommendation: {short_recommendation}
    
    Click here to see your full analysis:
    {dashboard_link}
    
    - Your Training Monkey
    
    P.S. We spotted some patterns in your training that you'll want to know about.
    """
    
    send_email(user_email, subject, body)
```

---

## PHASE 3: THE "AHA MOMENT" (30-60 Minutes)
**Objective:** Show them something that changes their training TODAY

### Current Flow:
```
Dashboard loads → All charts shown → Information overload
```

### Problems Identified:
- Too much data at once
- No clear hierarchy of importance
- User doesn't know what to look at first
- Recommendation buried in UI

### Critical Redesign (HIGH PRIORITY):

#### 1. Add Hero Banner to Dashboard
**File:** `frontend/src/TrainingLoadDashboard.tsx`

At top of dashboard, before all charts:

```typescript
const HeroBanner = ({ divergence, status, recommendation }: HeroProps) => {
  const statusConfig = {
    green: {
      color: '#10b981',
      icon: '✅',
      title: 'Your Training is Dialed In',
      description: 'Low injury risk, good balance'
    },
    yellow: {
      color: '#f59e0b',
      icon: '⚠️',
      title: 'Yellow Alert - Manage Carefully',
      description: 'Training load accumulating'
    },
    red: {
      color: '#ef4444',
      icon: '🚨',
      title: 'High Risk Territory',
      description: 'Overtraining indicators present'
    }
  };

  return (
    <div className="hero-banner" style={{ borderLeft: `8px solid ${statusConfig[status].color}` }}>
      <div className="hero-icon">{statusConfig[status].icon}</div>
      <div className="hero-content">
        <h2>{statusConfig[status].title}</h2>
        <p className="hero-description">{statusConfig[status].description}</p>
        
        <div className="divergence-callout">
          <span className="label">Training Divergence:</span>
          <span className="value">{divergence}%</span>
          <span className="explanation">
            {divergence < -10 ? 
              "Your body is working much harder than your external effort shows" :
              divergence < -5 ?
              "Slight mismatch between effort and output" :
              "External work and internal effort are aligned"
            }
          </span>
        </div>

        <div className="todays-recommendation">
          <h3>🐵 Today's Recommendation</h3>
          <p className="recommendation-text">{recommendation}</p>
          <button className="cta-button">I'll do this</button>
          <button className="secondary-button">I did something different</button>
        </div>
      </div>
    </div>
  );
};
```

#### 2. Simplify Initial Dashboard View
Hide advanced features until after first week:

```typescript
const DashboardView = ({ userDaysActive }: Props) => {
  // Progressive feature reveal
  const showAdvancedCharts = userDaysActive >= 7;
  const showACWRDetails = userDaysActive >= 14;
  const showAutopsy = userDaysActive >= 21;

  return (
    <div>
      <HeroBanner {...heroData} />
      
      {/* Always visible */}
      <BasicTrainingLoadChart />
      
      {showAdvancedCharts && (
        <>
          <HeartRateZoneBreakdown />
          <SportBreakdown />
        </>
      )}
      
      {showACWRDetails && <ACWRDeepDive />}
      {showAutopsy && <AIAutopsySection />}
    </div>
  );
};
```

---

## PHASE 4: THE DAILY LOOP (Days 1-7)
**Objective:** Build habit through friction-free daily engagement

### Current Flow:
```
User remembers to check dashboard → Maybe logs journal → Maybe checks recommendation
```

### Problems Identified:
- **Only 15% use journal** (massive problem!)
- No daily prompts/reminders
- Too much friction to log
- No reinforcement loop

### Critical Implementations:

#### 1. Daily Morning Email
**New File:** `app/daily_recommendation_emailer.py`

```python
def send_daily_recommendation_email(user_id):
    """Send daily recommendation at 6 AM user's timezone"""
    
    recommendation = get_todays_recommendation(user_id)
    divergence = get_current_divergence(user_id)
    
    subject = f"Today: {recommendation.short_title}"
    
    body = f"""
    Good morning! 🐵

    YOUR TRAINING TODAY:
    {recommendation.detailed_text}
    
    Why: Your divergence is {divergence}% and you've trained 
    {recent_days} days in a row.
    
    [View Full Dashboard →]
    
    Quick question: How did yesterday's training feel?
    [Great] [Ok] [Tough] [Skipped]
    
    - Your Training Monkey
    
    P.S. Reply to this email if you need clarification!
    """
    
    send_email(user.email, subject, body)
```

Schedule with Cloud Scheduler to run daily.

#### 2. One-Click Journal Entry
**File:** `app/strava_app.py` - New route

```python
@app.route('/journal/quick-entry')
def quick_journal_entry():
    """Pre-filled journal entry from email link"""
    
    token = request.args.get('token')  # Secure token
    user_id = verify_token(token)
    
    # Pre-populate with today's activity
    activity = get_todays_activity(user_id)
    
    return render_template('journal_quick_entry.html',
        activity=activity,
        pre_filled={
            'date': datetime.now().date(),
            'activity_name': activity.name if activity else None,
            'auto_detected_rpe': estimate_rpe_from_activity(activity)
        }
    )
```

**File:** `app/templates/journal_quick_entry.html` - Ultra-simple form

```html
<div class="quick-journal">
  <h2>How was today's training?</h2>
  
  <div class="activity-summary">
    <p>You did: <strong>{activity_name}</strong></p>
    <p>{distance} miles, {duration} minutes</p>
  </div>

  <div class="simple-inputs">
    <label>Effort (1-10):</label>
    <div class="rpe-buttons">
      <button class="rpe" data-value="1">1</button>
      <button class="rpe" data-value="2">2</button>
      <!-- ... through 10 -->
    </div>

    <label>Energy level:</label>
    <div class="energy-faces">
      😫 😐 🙂 😊 🎉
    </div>

    <label>Any pain/soreness?</label>
    <textarea placeholder="Optional notes..."></textarea>

    <button class="save-button">Save (takes 5 seconds)</button>
  </div>
</div>
```

#### 3. Evening Check-In Email
**Send after activity auto-syncs from Strava:**

```
Subject: "Quick check-in: How'd it go?"

Body:
We saw you did a [Run/Ride] today!
{activity_details}

Tell us how it felt (takes 10 seconds):
[Fill out quick form →]

Tomorrow's preview:
Based on today, we recommend: {tomorrow_recommendation_preview}

See you tomorrow! 🐵
```

---

## PHASE 5: THE TRUST-BUILDING MOMENT (Days 7-21)
**Objective:** Show prediction accuracy to build emotional connection

### Current Flow:
```
User gets recommendations → Does whatever → No feedback loop
```

### Problems Identified:
- No tracking of adherence vs outcomes
- No "I told you so" moments
- No reinforcement when predictions come true
- Users don't see the AI's accuracy

### New Feature: "Monkey vs You" Dashboard

**File:** Create new component in dashboard

```typescript
const MonkeyVsYouWidget = ({ user_id }: Props) => {
  const adherenceData = useAdherence(user_id);
  
  return (
    <div className="monkey-vs-you">
      <h3>🐵 Monkey vs You: Last 7 Days</h3>
      
      <div className="adherence-timeline">
        {adherenceData.map(day => (
          <div className="day" key={day.date}>
            <div className="date">{day.date}</div>
            <div className="monkey-said">
              🐵: {day.recommendation_short}
            </div>
            <div className="you-did">
              You: {day.what_you_did}
              {day.followed ? '✅' : '❌'}
            </div>
            {day.outcome && (
              <div className="outcome">
                Result: {day.outcome_description}
                {day.monkey_was_right && (
                  <span className="validation">
                    (Monkey was right! 🎯)
                  </span>
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="adherence-stats">
        <div className="stat">
          <span className="value">{adherenceData.adherence_rate}%</span>
          <span className="label">Followed advice</span>
        </div>
        <div className="stat">
          <span className="value">{adherenceData.prediction_accuracy}%</span>
          <span className="label">Predictions accurate</span>
        </div>
      </div>

      {adherenceData.last_ignored_warning && (
        <div className="warning-callout">
          <h4>🚨 Remember {adherenceData.last_ignored_warning.date}?</h4>
          <p>Monkey said: "{adherenceData.last_ignored_warning.recommendation}"</p>
          <p>You did: "{adherenceData.last_ignored_warning.what_you_did}"</p>
          <p>Result: {adherenceData.last_ignored_warning.what_happened}</p>
          <p><em>No judgment! But patterns don't lie. 🐵</em></p>
        </div>
      )}
    </div>
  );
};
```

### Trigger Email When Prediction Comes True

```python
def check_prediction_validation(user_id):
    """Check if recent predictions were validated by outcomes"""
    
    # Find instances where user ignored advice and had poor outcome
    violations = find_adherence_violations_with_negative_outcomes(user_id)
    
    if violations:
        send_validation_email(user_id, violations)

def send_validation_email(user_id, violations):
    """Send 'told you so' email (lovingly)"""
    
    subject = "🐵 Remember when your monkey said...?"
    
    body = f"""
    Hey there!
    
    Not to say "I told you so" but... your monkey might have been onto something.
    
    {violations[0].date}: Monkey recommended {violations[0].recommendation}
    You did: {violations[0].what_you_did}
    What happened: {violations[0].outcome}
    
    Your divergence spiked from {violations[0].divergence_before}% to 
    {violations[0].divergence_after}% right after.
    
    Again, no judgment! Training is hard and sometimes you gotta go for it.
    But next time you're tempted to ignore a rest day recommendation...
    maybe give it a think? 🙈
    
    Your (slightly smug but loving) Training Monkey
    
    P.S. The data doesn't lie, even when we wish it would.
    """
```

---

## SUCCESS METRICS & TRACKING

### Dashboard Analytics to Add

**File:** `app/analytics_tracker.py`

Track these new events:

```python
class UserProgressionEvent(Enum):
    # Phase 1
    LANDING_PAGE_VIEW = 'landing_page_view'
    STRAVA_CONNECT_CLICKED = 'strava_connect_clicked'
    
    # Phase 2
    SYNC_STARTED = 'sync_started'
    SYNC_PROGRESS_VIEWED = 'sync_progress_viewed'
    SYNC_COMPLETE_EMAIL_SENT = 'sync_complete_email_sent'
    
    # Phase 3
    FIRST_DASHBOARD_VIEW = 'first_dashboard_view'
    HERO_BANNER_VIEWED = 'hero_banner_viewed'
    RECOMMENDATION_CLICKED = 'recommendation_clicked'
    
    # Phase 4
    MORNING_EMAIL_OPENED = 'morning_email_opened'
    JOURNAL_ENTRY_STARTED = 'journal_entry_started'
    JOURNAL_ENTRY_COMPLETED = 'journal_entry_completed'
    QUICK_ENTRY_USED = 'quick_entry_used'
    
    # Phase 5
    MONKEY_VS_YOU_VIEWED = 'monkey_vs_you_viewed'
    ADHERENCE_ACKNOWLEDGED = 'adherence_acknowledged'
    PREDICTION_VALIDATED = 'prediction_validated'
    
    # Success milestones
    SEVEN_DAY_STREAK = 'seven_day_streak'
    THIRTY_DAY_ACTIVE = 'thirty_day_active'
    FEATURE_MASTERY = 'feature_mastery'
```

### Weekly Cohort Report

```python
def generate_weekly_cohort_report():
    """Generate report on new user progression"""
    
    cohort = get_users_signed_up_this_week()
    
    metrics = {
        'total_signups': len(cohort),
        'completed_sync': count_event(cohort, 'SYNC_COMPLETE'),
        'viewed_dashboard': count_event(cohort, 'FIRST_DASHBOARD_VIEW'),
        'first_journal': count_event(cohort, 'JOURNAL_ENTRY_COMPLETED'),
        'seven_day_streak': count_event(cohort, 'SEVEN_DAY_STREAK'),
        'still_active': count_active_last_7_days(cohort)
    }
    
    return {
        'cohort_week': get_week(),
        'conversion_funnel': calculate_funnel(metrics),
        'drop_off_points': identify_drop_offs(metrics),
        'recommendations': generate_recommendations(metrics)
    }
```

---

## IMPLEMENTATION PRIORITY

### 🔴 WEEK 1 (Critical for retention):
1. ✅ Post-sync email notification
2. ✅ Hero banner on dashboard
3. ✅ One-click journal entry
4. ✅ Daily morning recommendation email

**Impact:** Should improve 7-day retention from 55% → 75%

### 🟡 WEEK 2 (Build the loop):
5. ✅ Evening check-in email
6. ✅ Sync progress page with education
7. ✅ Simplified first-time dashboard
8. ✅ "Monkey vs You" widget

**Impact:** Should improve journal adoption from 15% → 60%

### 🟢 WEEK 3 (Advanced engagement):
9. ✅ Prediction validation emails
10. ✅ Progressive feature unlock
11. ✅ Weekly summary email
12. ✅ Celebration moments

**Impact:** Should improve 30-day retention from 55% → 80%

---

## QUICK REFERENCE: Email Schedule

```
USER TIMELINE          EMAIL/NOTIFICATION
─────────────────────  ────────────────────────────────────
Minute 0               (User signs up)
Minute 10              "Your monkey is analyzing your data..."
Minute 15              "Your insights are ready! 🐵"
Day 1, 6:00 AM         "Today's recommendation: Easy run"
Day 1, 8:00 PM         "How was your run? Quick check-in"
Day 2, 6:00 AM         "Today's recommendation: Rest day"
Day 7                  "One week milestone! Here's what we learned"
Day 14                 "Two weeks in - you're building something special"
Day 21                 "Three weeks! The data shows..."
Day 30                 "One month anniversary 🎉"
Day 90                 "You've evolved. Here's your transformation"
```

---

## TESTING PLAN

### Before Implementing Changes:
1. ✅ Review current user progression data
2. ✅ Identify biggest drop-off points
3. ✅ Interview 3-5 users who churned
4. ✅ Interview 3-5 power users

### After Implementing Week 1 Changes:
1. Track next 10 new users through progression
2. Measure time to first journal entry
3. Measure 7-day active rate
4. Collect feedback from users

### Success Criteria:
- 80%+ open rate on morning emails
- 70%+ first journal entry within 24 hours
- 75%+ 7-day retention
- 60%+ journal adoption rate
- User feedback score >4.5/5

---

## BOTTOM LINE

**The Goal:** Transform new users from "curious about data" to "can't live without this" in 7 days.

**The Method:** Remove ALL friction between the user and the "aha moment", then build the daily habit loop with intelligent automation.

**The Metric:** 80% of users who connect Strava should still be daily active at Day 30.

**Current vs Target:**
```
                    CURRENT   TARGET   GAP
────────────────────────────────────────────
Connect Strava        100%     100%    ✅
First Dashboard View   91%      95%    +4%
First Journal Entry    15%      70%   +55% 🔴
7-Day Active           ?        85%    ?
30-Day Active          55%      80%   +25%
```

**The work:** Week 1 fixes above should close that 55% gap significantly.

Let's get to work! 🐵


