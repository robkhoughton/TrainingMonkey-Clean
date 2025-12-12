# User Flow: Contact to Authorized User
## Complete Journey with Transition Optimization

---

## 🎯 **User Flow Overview**

**Entry Points:** Landing Page, Direct Dashboard Access, Onboarding Page
**Exit Points:** Full Dashboard Access, Help Resources, Tutorial System
**Key Decision Points:** Explore vs Commit, Help vs Continue, Tutorial vs Skip

---

## 📊 **Detailed User Flow Diagram**

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           USER FLOW: CONTACT TO AUTHORIZED USER                 │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   ANONYMOUS     │    │   NEW USER      │    │  EXISTING USER  │
│   VISITOR       │    │   (First Time)  │    │  (Returning)    │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          │                      │                      │
          ▼                      ▼                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              LANDING PAGE                                      │
│  • Interactive Demo (Divergence Chart)                                         │
│  • Value Proposition                                                           │
│  • Patent-pending Technology Showcase                                         │
└─────────────────┬───────────────────────────────────────────────────────────────┘
                  │
                  │ User Actions:
                  │ • "See How It Works" (NEW)
                  │ • "Connect with Strava" (Primary CTA)
                  │ • "Sign In" (Existing Users)
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        DECISION POINT: EXPLORE vs COMMIT                       │
└─────────────────┬───────────────────────────────────────────────────────────────┘
                  │
                  │ Path A: Explore First
                  │ Path B: Commit Directly
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    PATH A: GETTING STARTED RESOURCES PAGE                      │
│  • "What You'll Get" (4 Benefits)                                             │
│  • Interactive Demo (Same as Landing)                                          │
│  • 3-Step Setup Process                                                        │
│  • FAQ Section                                                                 │
│  • Sample AI Recommendations                                                   │
└─────────────────┬───────────────────────────────────────────────────────────────┘
                  │
                  │ User Actions:
                  │ • "Start Free Trial" → Strava Setup
                  │ • "Learn More" → FAQ/Help
                  │ • "View Demo" → Interactive Demo
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           STRAVA SETUP PAGE                                    │
│  • "What happens next?" Section                                                │
│  • Sample Divergence Analysis Preview                                          │
│  • FAQ Section (Setup Concerns)                                                │
│  • Progress Indicator (Step 1 of 6)                                            │
│  • Strava App Creation Instructions                                            │
└─────────────────┬───────────────────────────────────────────────────────────────┘
                  │
                  │ User Actions:
                  │ • Enter Client ID & Secret
                  │ • Click "Connect with Strava"
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        SYSTEM OPERATION: STRAVA OAUTH                          │
│  • Redirect to Strava Authorization                                            │
│  • User Authorizes on Strava                                                   │
│  • Strava Redirects to /oauth-callback                                         │
│  • System Creates User Account                                                 │
│  • Store Strava Tokens                                                         │
└─────────────────┬───────────────────────────────────────────────────────────────┘
                  │
                  │ DATABASE OPERATIONS:
                  │ • INSERT INTO user_settings (email, password_hash, strava_athlete_id, 
                  │   strava_access_token, strava_refresh_token, onboarding_step, 
                  │   features_unlocked, created_at)
                  │ • Set onboarding_step = 'welcome'
                  │ • Initialize features_unlocked = []
                  │ • Set session['new_user_onboarding'] = True
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        POST-STRAVA WELCOME PAGE                                │
│  • "Welcome! Here's what happens next"                                         │
│  • Progress Indicator (Step 2 of 6)                                            │
│  • Next Steps Preview                                                          │
└─────────────────┬───────────────────────────────────────────────────────────────┘
                  │
                  │ User Actions:
                  │ • "Continue" → Data Analysis
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        SYSTEM OPERATION: DATA SYNC                             │
│  • Fetch Activities from Strava API                                            │
│  • Process Training Load Calculations                                          │
│  • Store Activities in Database                                                │
│  • Calculate Initial Metrics                                                   │
└─────────────────┬───────────────────────────────────────────────────────────────┘
                  │
                  │ DATABASE OPERATIONS:
                  │ • INSERT INTO activities (user_id, strava_id, name, date, 
                  │   distance, moving_time, total_elevation_gain, average_heartrate, 
                  │   trimp_score, training_load)
                  │ • UPDATE user_settings SET onboarding_step = 'data_sync'
                  │ • Call /sync-with-auto-refresh
                  │ • Process activities for user
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        DATA ANALYSIS PROGRESS PAGE                             │
│  • "We're analyzing your data"                                                 │
│  • Progress Bar with Estimated Time                                            │
│  • Sample Analysis Preview                                                     │
└─────────────────┬───────────────────────────────────────────────────────────────┘
                  │
                  │ System Operations:
                  │ • Check if 28+ days of data available
                  │ • If yes: → Full Dashboard
                  │ • If no: → Onboarding Page
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        DECISION POINT: ENOUGH DATA?                            │
└─────────────────┬───────────────────────────────────────────────────────────────┘
                  │
                  │ Path A: 28+ Days Available
                  │ Path B: < 28 Days Available
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    PATH A: FIRST-TIME DASHBOARD (28+ Days)                     │
│  • New User Dashboard with Guided Experience                                   │
│  • Highlight Divergence Analysis                                               │
│  • Quick Actions and Next Steps                                                │
│  • Tutorial System Integration                                                 │
└─────────────────┬───────────────────────────────────────────────────────────────┘
                  │
                  │ User Actions:
                  │ • Explore Dashboard
                  │ • Complete Tutorials
                  │ • Set Goals (Optional)
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        SYSTEM OPERATION: ONBOARDING COMPLETE                   │
│  • Set onboarding_step = 'completed'                                           │
│  • Unlock all features                                                         │
│  • Remove new_user_onboarding session flag                                     │
└─────────────────┬───────────────────────────────────────────────────────────────┘
                  │
                  │ DATABASE OPERATIONS:
                  │ • UPDATE user_settings SET onboarding_step = 'completed'
                  │ • UPDATE user_settings SET onboarding_completed_at = NOW()
                  │ • UPDATE user_settings SET features_unlocked = 
                  │   '["dashboard_basic", "dashboard_advanced", "recommendations", 
                  │   "journal", "custom_goals", "advanced_analytics"]'
                  │ • Remove session['new_user_onboarding'] flag
                  │
                  ▼
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              FULL DASHBOARD                                    │
│  • Complete Training Load Dashboard                                            │
│  • All Features Unlocked                                                       │
│  • AI Recommendations Available                                                │
│  • Journal and Activities Access                                               │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                    PATH B: ONBOARDING PAGE (< 28 Days)                         │
│  • "Need help getting started?" Link (NEW)                                     │
│  • Days Needed Counter                                                         │
│  • Activity Count Display                                                      │
│  • Progress Tracking                                                           │
└─────────────────┬───────────────────────────────────────────────────────────────┘
                  │
                  │ User Actions:
                  │ • "Need help getting started?" → Getting Started Resources
                  │ • Wait for more data
                  │ • Manual sync activities
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        ALMOST THERE TRANSITION PAGE                            │
│  • "Almost there!" Motivation                                                  │
│  • Progress Indicator (Step 5 of 6)                                            │
│  • Goals Setup Preview                                                         │
└─────────────────┬───────────────────────────────────────────────────────────────┘
                  │
                  │ User Actions:
                  │ • "Set Goals" → Goals Setup
                  │ • "Skip for Now" → Dashboard
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              GOALS SETUP PAGE                                  │
│  • "Set Your Training Goal"                                                    │
│  • Goal Type Selection (Distance, Frequency, Improvement)                      │
│  • Progress Indicator (Step 6 of 6)                                            │
│  • Connection to Divergence Analysis Benefits                                  │
└─────────────────┬───────────────────────────────────────────────────────────────┘
                  │
                  │ User Actions:
                  │ • Select Goal Type
                  │ • Enter Target Values
                  │ • "Set Goal & Continue"
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        SYSTEM OPERATION: GOALS STORAGE                         │
│  • Store User Goals in Database                                                │
│  • Update onboarding_step = 'goals_setup'                                      │
│  • Unlock Custom Goals Feature                                                 │
└─────────────────┬───────────────────────────────────────────────────────────────┘
                  │
                  │ DATABASE OPERATIONS:
                  │ • INSERT INTO user_goals (user_id, goal_type, target_value, 
                  │   timeframe, created_at, status)
                  │ • UPDATE user_settings SET onboarding_step = 'goals_setup'
                  │ • UPDATE user_settings SET features_unlocked = 
                  │   features_unlocked || '["custom_goals"]'
                  │
                  ▼
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        YOU'RE ALL SET CELEBRATION PAGE                         │
│  • "You're all set!" Achievement                                               │
│  • Onboarding Complete                                                         │
│  • Next Steps and Feature Access                                               │
└─────────────────┬───────────────────────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              FULL DASHBOARD                                    │
│  • Complete Training Load Dashboard                                            │
│  • All Features Unlocked                                                       │
│  • AI Recommendations Available                                                │
│  • Journal and Activities Access                                               │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                    EXISTING USER FLOW (RETURNING USERS)                        │
└─────────────────┬───────────────────────────────────────────────────────────────┘
                  │
                  │ User Actions:
                  │ • "Sign In" from Landing Page
                  │ • Direct Dashboard Access
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        SYSTEM OPERATION: AUTHENTICATION                        │
│  • Verify User Credentials                                                     │
│  • Check Strava Token Validity                                                 │
│  • Refresh Tokens if Needed                                                    │
└─────────────────┬───────────────────────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              FULL DASHBOARD                                    │
│  • Complete Training Load Dashboard                                            │
│  • "New to TrainingMonkey? Get started here" Link (NEW)                        │
│  • Help Overlay/Modal Access                                                   │
│  • Tutorial System Integration                                                 │
└─────────────────┬───────────────────────────────────────────────────────────────┘
                  │
                  │ User Actions:
                  │ • "New to TrainingMonkey? Get started here" → Getting Started Resources
                  │ • Access Help/Tutorials
                  │ • Use Full Dashboard Features
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    GETTING STARTED RESOURCES (EXISTING USERS)                  │
│  • Contextual Content for Existing Users                                       │
│  • Tutorial System Access                                                      │
│  • Feature Discovery and Help                                                  │
│  • Advanced Usage Guides                                                       │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                              HELP & SUPPORT FLOW                               │
└─────────────────┬───────────────────────────────────────────────────────────────┘
                  │
                  │ Access Points:
                  │ • Landing Page → Getting Started Resources
                  │ • Onboarding Page → "Need help getting started?"
                  │ • Dashboard → "New to TrainingMonkey? Get started here"
                  │ • Dashboard → Help Overlay/Modal
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        GETTING STARTED RESOURCES PAGE                          │
│  • Interactive Demo (Divergence Chart)                                         │
│  • "What You'll Get" (4 Benefits)                                             │
│  • 3-Step Setup Process                                                        │
│  • FAQ Section                                                                 │
│  • Sample AI Recommendations                                                   │
│  • Tutorial System Integration                                                 │
│  • Contextual Content Based on User's Current Step                             │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 **Key System Operations & Database Changes**

### **1. User Account Creation (New User)**
```sql
-- Database Operations during Strava OAuth
INSERT INTO user_settings (
    email, 
    password_hash, 
    strava_athlete_id, 
    strava_access_token, 
    strava_refresh_token, 
    strava_token_expires_at,
    onboarding_step, 
    features_unlocked, 
    created_at,
    account_status
) VALUES (
    'strava_{athlete_id}@training-monkey.com',
    '{generated_password_hash}',
    {athlete_id},
    '{access_token}',
    '{refresh_token}',
    {expires_at},
    'welcome',
    '[]',
    NOW(),
    'active'
);
```

### **2. Data Processing (Activity Sync)**
```sql
-- Database Operations during Data Sync
INSERT INTO activities (
    user_id, 
    strava_id, 
    name, 
    date, 
    distance, 
    moving_time, 
    total_elevation_gain, 
    average_heartrate, 
    trimp_score, 
    training_load,
    created_at
) VALUES (
    {user_id},
    {strava_activity_id},
    '{activity_name}',
    '{activity_date}',
    {distance},
    {moving_time},
    {elevation_gain},
    {avg_heartrate},
    {trimp_score},
    {training_load},
    NOW()
);

-- Update user onboarding progress
UPDATE user_settings 
SET onboarding_step = 'data_sync',
    last_onboarding_activity = NOW()
WHERE user_id = {user_id};
```

### **3. Goals Setup (User Goals)**
```sql
-- Database Operations during Goals Setup
INSERT INTO user_goals (
    user_id, 
    goal_type, 
    target_value, 
    timeframe, 
    created_at, 
    status
) VALUES (
    {user_id},
    '{goal_type}',
    {target_value},
    '{timeframe}',
    NOW(),
    'active'
);

-- Update user features and onboarding
UPDATE user_settings 
SET onboarding_step = 'goals_setup',
    features_unlocked = features_unlocked || '["custom_goals"]',
    last_onboarding_activity = NOW()
WHERE user_id = {user_id};
```

### **4. Onboarding Completion**
```sql
-- Database Operations when Onboarding Complete
UPDATE user_settings 
SET onboarding_step = 'completed',
    onboarding_completed_at = NOW(),
    features_unlocked = '["dashboard_basic", "dashboard_advanced", "recommendations", "journal", "custom_goals", "advanced_analytics"]',
    last_onboarding_activity = NOW()
WHERE user_id = {user_id};
```

### **5. Analytics Tracking**
```python
# System Operations for Analytics (No DB changes needed)
- Track integration point clicks
- Monitor user journey progression  
- Record tutorial completions
- Measure conversion rates
```

---

## 📊 **User Decision Points**

### **1. Landing Page Decision**
- **Explore First:** "See How It Works" → Getting Started Resources
- **Commit Directly:** "Connect with Strava" → Strava Setup
- **Existing User:** "Sign In" → Authentication

### **2. Data Sufficiency Decision**
- **28+ Days:** → First-Time Dashboard (Guided)
- **< 28 Days:** → Onboarding Page (Wait for Data)

### **3. Goals Setup Decision**
- **Set Goals:** → Goals Setup Page → Celebration
- **Skip Goals:** → Direct to Dashboard

### **4. Help Access Decision**
- **Need Help:** → Getting Started Resources
- **Continue:** → Next Step in Journey

---

## 🎯 **Success Metrics by Stage**

### **Landing Page Metrics**
- Click-through rate: "See How It Works" vs "Connect with Strava"
- Time spent on interactive demo
- Bounce rate and engagement

### **Onboarding Metrics**
- Strava connection success rate
- Data sync completion rate
- Onboarding step completion rates
- Time to complete onboarding

### **Dashboard Metrics**
- Feature discovery rates
- Tutorial completion rates
- Help resource usage
- User retention post-onboarding

### **Overall Journey Metrics**
- End-to-end conversion rate
- Time from landing to first value
- User satisfaction scores
- Support ticket reduction

---

## 🚀 **Optimization Opportunities**

### **A/B Testing Points**
1. **Landing Page CTAs:** "See How It Works" vs "Connect with Strava"
2. **Getting Started Content:** Different layouts and messaging
3. **Onboarding Flow:** Different step orders and requirements
4. **Help Integration:** Different placement and wording

### **Performance Optimization**
1. **Page Load Times:** Optimize getting started resources page
2. **Demo Performance:** Smooth interactive demo animations
3. **Mobile Experience:** Responsive design across all pages
4. **Analytics Efficiency:** Lightweight tracking implementation

---

This comprehensive user flow shows the complete journey from first contact to authorized user, including all the transition optimization features and system operations that make the experience smooth and contextual.
