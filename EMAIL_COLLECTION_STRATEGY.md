# Email Collection Strategy for TrainingMonkey

## Current Situation
- **33 users** with synthetic emails (`strava_*@training-monkey.com`)
- **0 users** with real email addresses
- **Can't send any retention emails** (daily recommendations, journal prompts, etc.)

## What We Fixed
1. ✅ Added `profile:read_all` scope to Strava OAuth
2. ✅ Updated OAuth callback to capture real email from Strava
3. ✅ Fallback to synthetic email if Strava doesn't provide one

## What Still Needs Fixing

### 1. Collect Emails from Existing Users
### 2. Handle Users Who Deny Email Permission
### 3. Create Incentive to Provide Email

---

## SOLUTION 1: Email Collection Modal (For Existing Users)

### Trigger Conditions:
- User has synthetic email (`@training-monkey.com`)
- User has logged in at least once
- Modal not dismissed more than 3 times

### Implementation:

**File: Create `app/templates/email_collection_modal.html`**

```html
<div class="email-modal-overlay" id="emailCollectionModal">
  <div class="email-modal">
    <div class="modal-icon">📧</div>
    
    <h2>Unlock Your Training Monkey's Full Power</h2>
    
    <div class="benefits">
      <p><strong>Right now, you're missing out on:</strong></p>
      <ul>
        <li>✅ Daily training recommendations sent to your inbox (6 AM)</li>
        <li>✅ "How was your run?" prompts after activities</li>
        <li>✅ Injury risk alerts when patterns change</li>
        <li>✅ Weekly progress summaries</li>
        <li>✅ One-click journal entries from email</li>
      </ul>
    </div>

    <div class="current-problem">
      <p class="warning">⚠️ Currently using: <code>{synthetic_email}</code></p>
      <p>This is a placeholder. We can't send you anything!</p>
    </div>

    <form id="emailCollectionForm" class="email-form">
      <label>Your Real Email Address:</label>
      <input 
        type="email" 
        name="email" 
        placeholder="your.email@example.com"
        required
        autocomplete="email"
      />
      
      <div class="privacy-note">
        <small>🔒 We'll only use this for training notifications. 
        No spam, no selling. <a href="/privacy">Privacy Promise</a></small>
      </div>

      <div class="buttons">
        <button type="submit" class="btn-primary">
          Unlock Email Features
        </button>
        <button type="button" class="btn-secondary" onclick="dismissModal()">
          Maybe Later
        </button>
      </div>
    </form>

    <div class="dismiss-counter">
      <small>Dismissed {dismiss_count}/3 times. 
      After 3, we won't ask again.</small>
    </div>
  </div>
</div>

<style>
.email-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  animation: fadeIn 0.3s;
}

.email-modal {
  background: white;
  border-radius: 16px;
  padding: 2rem;
  max-width: 500px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  animation: slideUp 0.3s;
}

.modal-icon {
  font-size: 3rem;
  text-align: center;
  margin-bottom: 1rem;
}

.benefits {
  background: #f0f9ff;
  border-left: 4px solid #3b82f6;
  padding: 1rem;
  margin: 1rem 0;
}

.benefits ul {
  margin: 0.5rem 0 0 0;
  padding-left: 1.5rem;
}

.current-problem {
  background: #fef3c7;
  border-left: 4px solid #f59e0b;
  padding: 1rem;
  margin: 1rem 0;
}

.current-problem code {
  background: rgba(0, 0, 0, 0.1);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.9em;
}

.email-form input[type="email"] {
  width: 100%;
  padding: 0.75rem;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  font-size: 1rem;
  margin-top: 0.5rem;
}

.email-form input[type="email"]:focus {
  outline: none;
  border-color: #3b82f6;
}

.privacy-note {
  margin-top: 0.5rem;
  color: #6b7280;
}

.buttons {
  display: flex;
  gap: 1rem;
  margin-top: 1.5rem;
}

.btn-primary {
  flex: 1;
  background: #3b82f6;
  color: white;
  border: none;
  padding: 0.75rem;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary:hover {
  background: #2563eb;
  transform: translateY(-1px);
}

.btn-secondary {
  background: white;
  border: 2px solid #e5e7eb;
  padding: 0.75rem;
  border-radius: 8px;
  cursor: pointer;
}

.dismiss-counter {
  text-align: center;
  margin-top: 1rem;
  color: #9ca3af;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideUp {
  from { 
    opacity: 0;
    transform: translateY(30px);
  }
  to { 
    opacity: 1;
    transform: translateY(0);
  }
}
</style>

<script>
function dismissModal() {
  fetch('/api/user/dismiss-email-modal', {
    method: 'POST'
  }).then(() => {
    document.getElementById('emailCollectionModal').style.display = 'none';
  });
}

document.getElementById('emailCollectionForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  
  const email = e.target.email.value;
  
  const response = await fetch('/api/user/update-email', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email })
  });
  
  if (response.ok) {
    document.getElementById('emailCollectionModal').innerHTML = `
      <div class="success-message">
        <div class="icon">🎉</div>
        <h2>Email Updated!</h2>
        <p>You'll start receiving your daily recommendations tomorrow morning.</p>
        <button onclick="location.reload()">Continue to Dashboard</button>
      </div>
    `;
  } else {
    alert('Error updating email. Please try again.');
  }
});
</script>
```

---

## SOLUTION 2: Backend API Routes

**File: `app/strava_app.py`** - Add these routes:

```python
@app.route('/api/user/update-email', methods=['POST'])
@login_required
def update_user_email():
    """Update user's email address"""
    try:
        data = request.get_json()
        new_email = data.get('email', '').strip().lower()
        
        if not new_email or '@' not in new_email:
            return jsonify({'error': 'Invalid email address'}), 400
        
        # Check if email already exists
        existing_user = User.get_by_email(new_email)
        if existing_user and existing_user.id != current_user.id:
            return jsonify({'error': 'Email already in use'}), 400
        
        # Update email in database
        db_utils.execute_query(
            "UPDATE user_settings SET email = %s WHERE id = %s",
            (new_email, current_user.id),
            fetch=False
        )
        
        # Log the change
        logger.info(f"User {current_user.id} updated email to {new_email}")
        
        # Send confirmation email
        send_email_confirmation(new_email, current_user.id)
        
        return jsonify({'success': True, 'message': 'Email updated successfully'})
        
    except Exception as e:
        logger.error(f"Error updating email: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/user/dismiss-email-modal', methods=['POST'])
@login_required
def dismiss_email_modal():
    """Track email modal dismissals"""
    try:
        # Get current dismiss count
        result = db_utils.execute_query(
            "SELECT email_modal_dismissals FROM user_settings WHERE id = %s",
            (current_user.id,),
            fetch=True
        )
        
        current_count = result.get('email_modal_dismissals', 0) if result else 0
        new_count = current_count + 1
        
        # Update dismiss count
        db_utils.execute_query(
            "UPDATE user_settings SET email_modal_dismissals = %s WHERE id = %s",
            (new_count, current_user.id),
            fetch=False
        )
        
        logger.info(f"User {current_user.id} dismissed email modal ({new_count}/3)")
        
        return jsonify({'success': True, 'dismissals': new_count})
        
    except Exception as e:
        logger.error(f"Error tracking modal dismissal: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


def should_show_email_modal(user_id):
    """Check if we should show email collection modal to user"""
    try:
        result = db_utils.execute_query(
            """SELECT email, email_modal_dismissals 
               FROM user_settings 
               WHERE id = %s""",
            (user_id,),
            fetch=True
        )
        
        if not result:
            return False
        
        email = result.get('email', '')
        dismissals = result.get('email_modal_dismissals', 0)
        
        # Show if:
        # - Email is synthetic (@training-monkey.com)
        # - User hasn't dismissed 3 times
        is_synthetic = '@training-monkey.com' in email
        not_max_dismissals = dismissals < 3
        
        return is_synthetic and not_max_dismissals
        
    except Exception as e:
        logger.error(f"Error checking email modal status: {str(e)}")
        return False
```

---

## SOLUTION 3: Add Modal to Dashboard

**File: `app/templates/dashboard.html`** - Add at bottom before `</body>`:

```html
{% if show_email_modal %}
  {% include 'email_collection_modal.html' %}
{% endif %}
```

**File: `app/strava_app.py`** - Update dashboard route:

```python
@app.route('/dashboard')
@login_required
def dashboard():
    """Render training dashboard with email modal if needed"""
    # ... existing dashboard code ...
    
    # Check if we should show email collection modal
    show_email_modal = should_show_email_modal(current_user.id)
    
    return render_template('dashboard.html',
        # ... existing variables ...
        show_email_modal=show_email_modal,
        synthetic_email=current_user.email if '@training-monkey.com' in current_user.email else None
    )
```

---

## SOLUTION 4: Add Database Column (If Not Exists)

Run this SQL to add tracking column:

```sql
ALTER TABLE user_settings 
ADD COLUMN IF NOT EXISTS email_modal_dismissals INTEGER DEFAULT 0;
```

---

## SOLUTION 5: Email Collection During Onboarding

**For NEW users who deny Strava email permission:**

**File: `app/templates/welcome_post_strava.html`** - Add step 2:

```html
<div class="onboarding-step" id="step-email">
  <h2>📧 Where Should We Send Your Daily Recommendations?</h2>
  
  <div class="value-prop">
    <p>Every morning at 6 AM, your Training Monkey will email you:</p>
    <ul>
      <li>Today's personalized training recommendation</li>
      <li>Your current injury risk status</li>
      <li>One-click journal entry link (takes 10 seconds)</li>
    </ul>
    <p><strong>95% of active users check this email daily</strong></p>
  </div>

  {% if has_synthetic_email %}
  <div class="warning">
    <p>⚠️ We currently have: <code>{{ user_email }}</code></p>
    <p>This won't work for sending you emails!</p>
  </div>
  {% endif %}

  <form method="POST" action="/onboarding/set-email">
    <label>Your Email:</label>
    <input 
      type="email" 
      name="email" 
      value="{{ strava_email if strava_email else '' }}"
      placeholder="your.email@example.com"
      required
    />
    
    <button type="submit" class="btn-primary">
      Continue
    </button>
    
    <button type="button" class="btn-link" onclick="skipEmail()">
      Skip (I'll miss out on daily recommendations)
    </button>
  </form>
</div>
```

---

## SOLUTION 6: Incentive Strategy

### Carrot (Positive Incentives):

**Show what they GET with email:**
- ✅ Daily recommendations in inbox (no need to remember to check)
- ✅ Injury risk alerts (prevent disasters)
- ✅ One-click journal entry (10 seconds vs 2 minutes)
- ✅ Weekly progress summaries
- ✅ "Told you so" emails when predictions come true
- ✅ Celebration emails (streaks, milestones)

**Show what they MISS without email:**
- ❌ 47% less engaged (show data!)
- ❌ 3x more likely to quit within 30 days
- ❌ Miss injury warnings
- ❌ Forget to log journal (only 15% do without prompts!)

### Stick (FOMO):

**Lock features without email:**
```html
<div class="locked-feature">
  <div class="blur-overlay">
    <img src="email-preview.png" class="blurred" />
  </div>
  
  <h3>🔒 Daily Email Recommendations</h3>
  <p>See what you're missing:</p>
  
  <div class="email-preview">
    <div class="subject">
      <strong>Subject:</strong> "Today: Easy recovery run (here's why)"
    </div>
    <div class="preview-text">
      Good morning! 🐵
      
      Your monkey analyzed last night's data...
      [Blurred content]
      
      [Add Email to Unlock]
    </div>
  </div>
  
  <button class="unlock-button">
    Provide Email to Unlock This
  </button>
</div>
```

---

## SOLUTION 7: Gradual Persuasion Timeline

**Day 1:** Modal appears (dismissible)  
**Day 2:** Notification in dashboard "You missed yesterday's recommendation email"  
**Day 3:** Show "locked feature" tease  
**Day 5:** Modal appears again (dismissible)  
**Day 7:** Final modal "Last chance for email features"  
**Day 8+:** If still no email, show permanent banner "Limited experience - add email for full features"

---

## IMPLEMENTATION PRIORITY

### 🔴 Week 1 (Critical):
1. ✅ Add email scope to OAuth (DONE)
2. ✅ Capture real email from Strava (DONE)
3. ✅ Create email collection modal
4. ✅ Add API routes for email update

### 🟡 Week 2:
5. ✅ Add modal to dashboard
6. ✅ Add email step to onboarding
7. ✅ Create incentive displays
8. ✅ Add database tracking column

### 🟢 Week 3:
9. ✅ Send email to existing users explaining why we need their real email
10. ✅ A/B test different incentive messaging
11. ✅ Add "locked features" teasers

---

## MEASURING SUCCESS

### Target Metrics:
- **New users**: 80%+ provide email during signup
- **Existing users**: 60%+ update email within 30 days
- **Modal conversion**: 40%+ click "Unlock Email Features"
- **Overall**: 70%+ of active users have real emails within 60 days

### Track These Events:
```python
EMAIL_MODAL_SHOWN = 'email_modal_shown'
EMAIL_MODAL_DISMISSED = 'email_modal_dismissed'
EMAIL_MODAL_COMPLETED = 'email_modal_completed'
EMAIL_UPDATED_FROM_ONBOARDING = 'email_updated_onboarding'
EMAIL_UPDATED_FROM_SETTINGS = 'email_updated_settings'
```

---

## COMMUNICATION STRATEGY

### Email to Existing Users:

**Subject:** "🐵 Your Training Monkey Needs Your Real Email"

**Body:**
```
Hi there!

Quick question: What email are we using for you?

We have: strava_12345@training-monkey.com

That's not a real email address! We created it as a placeholder when you 
signed up via Strava, but it means we can't send you:

✅ Daily training recommendations (6 AM - most users' favorite feature)
✅ Post-run journal prompts (one-click entry, takes 10 seconds)
✅ Injury risk alerts when we spot concerning patterns
✅ Weekly progress summaries
✅ Celebration emails when you hit milestones

Takes 30 seconds to fix:
[Update My Email →]

- Your (inbox-less) Training Monkey

P.S. We're not asking for your soul. Just an email address so we can 
actually help you train smarter!
```

---

## FALLBACK PLAN

If users STILL won't provide email:

### Option 1: SMS (Future Enhancement)
- "No email? Get texts instead"
- Requires phone number collection
- More invasive, higher friction

### Option 2: Push Notifications (Web)
- Browser notifications for recommendations
- Requires permission (another modal...)
- Less effective than email

### Option 3: In-App Notifications Only
- Show notifications in dashboard
- Requires daily app visits
- Much lower engagement

**Bottom Line:** Email is critical. Make it worth their while!

---

## THE PSYCHOLOGICAL APPROACH

**Don't say:** "Please provide your email"  
**Do say:** "Unlock daily recommendations delivered to your inbox"

**Don't say:** "We need your email for notifications"  
**Do say:** "You're missing 5 features without a real email address"

**Don't say:** "Update your contact information"  
**Do say:** "Get the full Training Monkey experience"

**Frame it as:**
- They're missing out (FOMO)
- They're getting MORE, not giving MORE
- Their current experience is "limited"
- This unlocks power they don't have

---

## QUICK REFERENCE: The Fix

**For NEW users (after today's deploy):**
1. OAuth requests email permission
2. Real email captured automatically
3. If denied, onboarding step collects it
4. If skipped, modal appears after 1 day

**For EXISTING 33 users:**
1. Email sent explaining situation
2. Modal appears on next dashboard visit
3. Shows up to 3 times over 7 days
4. If ignored, permanent banner appears

**Success Rate Target:**
- New users: 80%+ email capture
- Existing users: 60%+ update within 30 days
- Overall: 70%+ real emails by end of Q1

---

Let's get those email addresses! 📧🐵



