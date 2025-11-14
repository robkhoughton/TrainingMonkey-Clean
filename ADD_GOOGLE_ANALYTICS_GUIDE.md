# How to Add Google Analytics to TrainingMonkey

## Why Google Analytics?
- **Free** and industry-standard
- Tracks **where users come from** (Google, Facebook, direct, etc.)
- Shows **user behavior**, page views, conversions
- **Real-time** data dashboard
- Works with your existing analytics infrastructure

## Setup Steps

### 1. Create Google Analytics Account (5 minutes)

1. Go to https://analytics.google.com
2. Sign in with your Google account
3. Click **"Start measuring"**
4. Fill in:
   - Account name: "TrainingMonkey"
   - Property name: "TrainingMonkey Web App"
   - Time zone: Your timezone
   - Currency: USD
5. Choose **"Web"** platform
6. Enter your website URL: `https://yourtrainingmonkey.com`
7. Accept terms and create

### 2. Get Your Tracking Code

After creating the property, Google will show you a **Measurement ID** like:
```
G-XXXXXXXXXX
```

Copy this ID.

### 3. Add to Your Landing Page

Open `app/templates/landing.html` and replace this section (around line 58):

```html
<!-- Analytics/Tracking (add your tracking codes here) -->
<!-- Google Analytics, Facebook Pixel, etc. -->
```

With this code (replace `G-XXXXXXXXXX` with YOUR actual Measurement ID):

```html
<!-- Google Analytics 4 -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-XXXXXXXXXX', {
    'cookie_flags': 'SameSite=None;Secure'
  });
</script>
```

### 4. Add to Other Pages

Also add the same code to these files:
- `app/templates/signup.html`
- `app/templates/onboarding.html`
- `frontend/public/index.html` (for React app)

For the React app (`frontend/public/index.html`), add it in the `<head>` section.

### 5. Track Custom Events (Optional but Recommended)

You can send custom events to GA4 from your existing code. For example, when a user clicks "Connect with Strava":

```javascript
// Add this to your existing trackCTAClick() function in landing.html
gtag('event', 'cta_click', {
  'button_name': 'strava_connect',
  'page': 'landing'
});
```

### 6. Deploy and Verify

1. Deploy your changes (rebuild frontend if needed)
2. Visit your live site
3. In Google Analytics, go to **Reports > Realtime**
4. You should see yourself as an active user!

---

## What You'll See in Google Analytics

### Acquisition Reports (Where Users Come From):
- **Direct traffic**: Typed your URL directly
- **Organic Search**: Found you on Google/Bing
- **Social**: Facebook, Twitter, Reddit, etc.
- **Referral**: Other websites linking to you
- **Paid Search**: If you run Google Ads

### User Behavior:
- Which pages they visit
- How long they stay
- Where they drop off
- Conversion paths (visitor → signup → active user)

### Real-Time:
- See current visitors
- What they're doing right now
- Where they came from

---

## Option 2: Squarespace Analytics (If Hosting Landing Page There)

If you're using Squarespace for your landing page:

1. Log into Squarespace
2. Go to **Analytics** in left sidebar
3. Click **Traffic Sources**
4. You'll see:
   - Search engines (with keywords)
   - Social media
   - Referral sites
   - Direct traffic

**Built-in, no setup required!**

---

## Option 3: UTM Tracking Parameters

When sharing links on social media or in marketing campaigns, add UTM parameters:

### Format:
```
https://yourtrainingmonkey.com?utm_source=SOURCE&utm_medium=MEDIUM&utm_campaign=CAMPAIGN
```

### Examples:

**Facebook post:**
```
https://yourtrainingmonkey.com?utm_source=facebook&utm_medium=social&utm_campaign=launch_week
```

**Reddit comment:**
```
https://yourtrainingmonkey.com?utm_source=reddit&utm_medium=social&utm_campaign=trailrunning_community
```

**Email newsletter:**
```
https://yourtrainingmonkey.com?utm_source=newsletter&utm_medium=email&utm_campaign=weekly_update
```

**Paid Google Ad:**
```
https://yourtrainingmonkey.com?utm_source=google&utm_medium=cpc&utm_campaign=runners_keyword
```

### How to Track UTM Parameters

Your existing analytics already captures the referrer, but to track UTM parameters specifically, add this to your landing page:

```javascript
// Add to landing.html after GA code
<script>
  // Extract UTM parameters and send to your analytics
  const urlParams = new URLSearchParams(window.location.search);
  const utmData = {
    utm_source: urlParams.get('utm_source'),
    utm_medium: urlParams.get('utm_medium'),
    utm_campaign: urlParams.get('utm_campaign'),
    utm_content: urlParams.get('utm_content'),
    utm_term: urlParams.get('utm_term')
  };
  
  if (utmData.utm_source) {
    // Send to your existing analytics endpoint
    fetch('/api/landing/analytics', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        event_type: 'page_view',
        event_data: {
          page: 'landing',
          utm_params: utmData,
          timestamp: new Date().toISOString()
        }
      })
    });
    
    // Also send to Google Analytics if you added it
    if (typeof gtag !== 'undefined') {
      gtag('event', 'page_view', utmData);
    }
  }
</script>
```

---

## Tracking User Signups by Source

To know which traffic source led to actual signups, add this to your signup completion code:

### In `app/strava_app.py` (or wherever signup completes):

```python
# When a new user signs up successfully
from analytics_tracker import track_analytics_event, EventType

# Get the referrer from session or request
referrer = request.headers.get('Referer', 'direct')

# Track signup with source
track_analytics_event(
    event_type=EventType.USER_SIGNUP,  # You may need to add this EventType
    event_data={
        'signup_method': 'strava',
        'referrer': referrer,
        'timestamp': datetime.now().isoformat()
    },
    user_id=new_user_id,
    request=request
)
```

---

## Quick Win: Check Your Current Database

You mentioned you have 33 users. Let's see where they came from! Run this query:

```python
# Run this to see signup sources for existing users
python -c "
import psycopg2
conn = psycopg2.connect('postgresql://appuser:trainmonk25@35.223.144.85:5432/train-d')
cur = conn.cursor()

# Get first event for each user (proxy for signup source)
cur.execute('''
    SELECT 
        user_id,
        MIN(timestamp) as first_seen,
        (SELECT referrer FROM analytics_events WHERE user_id = ae.user_id ORDER BY timestamp ASC LIMIT 1) as first_referrer
    FROM analytics_events ae
    WHERE user_id IS NOT NULL
    GROUP BY user_id
    ORDER BY first_seen;
''')

for row in cur.fetchall():
    print(f'User {row[0]}: First seen {row[1]}, came from: {row[2]}')

cur.close()
conn.close()
"
```

---

## Summary Recommendations

**Do This NOW:**
1. ✅ Add Google Analytics 4 to your landing page (10 minutes)
2. ✅ Deploy and verify it's working in GA Realtime

**Do This SOON:**
3. ✅ Add UTM parameters to all your social media links
4. ✅ Track signup events with referrer data
5. ✅ Check Squarespace analytics if you use it for landing page

**Nice to Have:**
6. Set up conversion goals in GA4
7. Create custom dashboards
8. Set up alerts for traffic spikes

---

## Need Help?

If you want me to:
- Add the GA4 code to your templates
- Set up UTM tracking
- Create queries to analyze your existing user referrer data

Just let me know!


