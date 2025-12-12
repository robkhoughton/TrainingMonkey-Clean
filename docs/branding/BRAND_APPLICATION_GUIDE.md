# Your Training Monkey - Brand Application Guide
### Quick Implementation Reference for Developers & Designers

This guide provides practical, copy-paste ready code snippets and examples for implementing the Your Training Monkey brand framework. For complete brand strategy and philosophy, see `YOUR_TRAINING_MONKEY_BRAND_FRAMEWORK.md`.

---

## Table of Contents
1. [CSS Variables Setup](#css-variables-setup)
2. [Component Library](#component-library)
3. [Common Patterns](#common-patterns)
4. [Copy Templates](#copy-templates)
5. [Code Snippets](#code-snippets)

---

## CSS Variables Setup

### Core Variables (Add to your root CSS)

```css
:root {
  /* Brand Colors - Blues/Grays */
  --ytm-trail-sky: #E6F0FF;
  --ytm-mountain-ridge: #7D9CB8;
  --ytm-night-summit: #1B2E4B;

  /* Brand Colors - Functional */
  --ytm-action-orange: #FF5722;
  --ytm-action-orange-hover: #E64A19;
  --ytm-success-green: #16A34A;
  --ytm-success-green-dark: #15803D;
  --ytm-success-green-light: #DCFCE7;
  --ytm-success-green-bg: #F0FDF4;

  /* Interactive Purple Gradient */
  --ytm-purple-start: #667EEA;
  --ytm-purple-end: #764BA2;

  /* Alert/Warning */
  --ytm-alert-bg: #FEF3C7;
  --ytm-alert-border: #F59E0B;
  --ytm-alert-text: #92400E;

  /* Grays */
  --ytm-text-primary: #1F2937;
  --ytm-text-heading: #1E293B;
  --ytm-text-secondary: #64748B;
  --ytm-bg-light: #F8FAFC;
  --ytm-border-light: #E5E7EB;
  --ytm-border-medium: #E2E8F0;

  /* Sage Green (Y, T, M emphasis) */
  --ytm-sage-green: #6B8F7F;

  /* Strava */
  --strava-orange: #FC5200;

  /* Typography Scale */
  --ytm-font-display: 2.5rem;     /* 40px */
  --ytm-font-h1: 2rem;            /* 32px */
  --ytm-font-h2: 1.5rem;          /* 24px */
  --ytm-font-h3: 1.25rem;         /* 20px */
  --ytm-font-body-lg: 1.1rem;     /* 17.6px */
  --ytm-font-body: 1rem;          /* 16px */
  --ytm-font-small: 0.95rem;      /* 15.2px */
  --ytm-font-caption: 0.85rem;    /* 13.6px */

  /* Font Weights */
  --ytm-weight-regular: 400;
  --ytm-weight-semibold: 600;
  --ytm-weight-bold: 700;

  /* Spacing Scale */
  --ytm-space-xs: 0.25rem;   /* 4px */
  --ytm-space-sm: 0.5rem;    /* 8px */
  --ytm-space-md: 1rem;      /* 16px */
  --ytm-space-lg: 1.5rem;    /* 24px */
  --ytm-space-xl: 2rem;      /* 32px */
  --ytm-space-2xl: 3rem;     /* 48px */

  /* Border Radius */
  --ytm-radius-sm: 8px;
  --ytm-radius-md: 12px;
  --ytm-radius-lg: 20px;
  --ytm-radius-full: 9999px;

  /* Shadows */
  --ytm-shadow-sm: 0 4px 8px rgba(0, 0, 0, 0.05);
  --ytm-shadow-md: 0 4px 15px rgba(0, 0, 0, 0.05);
  --ytm-shadow-lg: 0 6px 14px rgba(2, 6, 23, 0.06);
  --ytm-shadow-xl: 0 10px 30px rgba(0, 0, 0, 0.1);

  /* Transitions */
  --ytm-transition-fast: 0.2s ease;
  --ytm-transition-base: 0.3s ease;
  --ytm-transition-slow: 0.5s ease;
}

/* System Font Stack */
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto,
               Oxygen, Ubuntu, Cantarell, sans-serif;
  font-size: var(--ytm-font-body);
  line-height: 1.6;
  color: var(--ytm-text-primary);
}

/* Readability Guidelines */
p, li {
  max-width: 75ch;  /* 60-75 characters per line */
  text-align: left; /* Always left-align body text */
}
```

---

## Component Library

### Buttons

#### Primary Action Button (Purple Gradient)
```css
.ytm-btn-primary {
  display: inline-block;
  background: linear-gradient(135deg, var(--ytm-purple-start), var(--ytm-purple-end));
  color: white;
  padding: 1rem 2rem;
  border-radius: var(--ytm-radius-md);
  font-size: var(--ytm-font-body-lg);
  font-weight: var(--ytm-weight-semibold);
  text-decoration: none;
  border: none;
  cursor: pointer;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
  transition: all var(--ytm-transition-base);
}

.ytm-btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
}

.ytm-btn-primary:active {
  transform: translateY(0);
}

.ytm-btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  pointer-events: none;
}
```

**HTML Example:**
```html
<button class="ytm-btn-primary">Get Started</button>
<a href="/signup" class="ytm-btn-primary">Start Training</a>
```

#### Success Button (Green)
```css
.ytm-btn-success {
  background: linear-gradient(135deg, var(--ytm-success-green), var(--ytm-success-green-dark));
  color: white;
  padding: 1rem 2rem;
  border-radius: var(--ytm-radius-md);
  font-size: var(--ytm-font-body-lg);
  font-weight: var(--ytm-weight-semibold);
  text-decoration: none;
  border: none;
  cursor: pointer;
  box-shadow: 0 4px 15px rgba(22, 163, 74, 0.3);
  transition: all var(--ytm-transition-base);
}

.ytm-btn-success:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(22, 163, 74, 0.4);
}
```

#### CTA Button (Orange - Use Sparingly!)
```css
.ytm-btn-cta {
  background: var(--ytm-action-orange);
  color: white;
  padding: 1rem 2.5rem;
  border-radius: var(--ytm-radius-full);
  font-size: var(--ytm-font-body-lg);
  font-weight: var(--ytm-weight-semibold);
  text-decoration: none;
  border: none;
  cursor: pointer;
  box-shadow: 0 4px 15px rgba(255, 87, 34, 0.4);
  transition: all var(--ytm-transition-base);
}

.ytm-btn-cta:hover {
  background: var(--ytm-action-orange-hover);
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(255, 87, 34, 0.6);
}
```

**⚠️ Important:** Only use ONE CTA button per page/screen!

#### Secondary/Outline Button
```css
.ytm-btn-secondary {
  background: transparent;
  color: var(--ytm-purple-start);
  padding: 1rem 2rem;
  border: 2px solid var(--ytm-purple-start);
  border-radius: var(--ytm-radius-md);
  font-size: var(--ytm-font-body);
  font-weight: var(--ytm-weight-semibold);
  text-decoration: none;
  cursor: pointer;
  transition: all var(--ytm-transition-base);
}

.ytm-btn-secondary:hover {
  background: var(--ytm-purple-start);
  color: white;
}
```

### Cards

#### Standard Card
```css
.ytm-card {
  background: white;
  border-radius: var(--ytm-radius-md);
  padding: var(--ytm-space-lg);
  box-shadow: var(--ytm-shadow-md);
  border: 1px solid var(--ytm-border-medium);
  margin-bottom: var(--ytm-space-lg);
}
```

**HTML Example:**
```html
<div class="ytm-card">
  <h2>Your Training Status</h2>
  <p>Current divergence analysis...</p>
</div>
```

#### Highlighted Card (with left border)
```css
.ytm-card-highlight {
  background: var(--ytm-bg-light);
  border-left: 4px solid #3b82f6;
  border-radius: var(--ytm-radius-md);
  padding: 1rem 1.25rem;
  margin-bottom: var(--ytm-space-md);
}
```

**HTML Example:**
```html
<div class="ytm-card-highlight">
  <h3>Step 1: Connect Strava</h3>
  <p>Link your account to import training data.</p>
</div>
```

#### Alert Card (Warning)
```css
.ytm-card-alert {
  background: var(--ytm-alert-bg);
  border: 2px solid var(--ytm-alert-border);
  border-radius: var(--ytm-radius-md);
  padding: var(--ytm-space-lg);
  margin-bottom: var(--ytm-space-lg);
}

.ytm-card-alert h3 {
  color: var(--ytm-alert-text);
  margin-top: 0;
}

.ytm-card-alert p {
  color: var(--ytm-alert-text);
  margin-bottom: 0;
}
```

**HTML Example:**
```html
<div class="ytm-card-alert">
  <h3>⚠️ Important Notice</h3>
  <p>This app is optimized specifically for trail runners.</p>
</div>
```

#### Success Card
```css
.ytm-card-success {
  background: rgba(22, 163, 74, 0.1);
  border: 1px solid var(--ytm-success-green);
  border-radius: var(--ytm-radius-md);
  padding: var(--ytm-space-md);
  text-align: center;
  margin-bottom: var(--ytm-space-lg);
}

.ytm-card-success h3 {
  color: var(--ytm-success-green);
  margin-top: 0;
}
```

**HTML Example:**
```html
<div class="ytm-card-success">
  <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">✅</div>
  <h3>Strava Connected Successfully!</h3>
  <p>Your training data is now syncing.</p>
</div>
```

### Form Elements

#### Text Input
```css
.ytm-input {
  width: 100%;
  padding: 0.875rem 1rem;
  border: 2px solid var(--ytm-border-light);
  border-radius: 10px;
  font-size: var(--ytm-font-body);
  background: white;
  transition: all var(--ytm-transition-fast);
}

.ytm-input:focus {
  outline: none;
  border-color: var(--ytm-purple-start);
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.ytm-input:invalid {
  border-color: #ef4444;
}
```

**HTML Example:**
```html
<div class="ytm-form-group">
  <label for="email">Email Address</label>
  <input type="email" id="email" name="email" class="ytm-input" placeholder="your.email@example.com">
  <small class="ytm-help-text">We'll never share your email.</small>
</div>
```

#### Form Group Container
```css
.ytm-form-group {
  margin-bottom: var(--ytm-space-lg);
}

.ytm-form-group label {
  display: block;
  color: #374151;
  font-weight: var(--ytm-weight-semibold);
  margin-bottom: var(--ytm-space-sm);
  font-size: var(--ytm-font-small);
}

.ytm-help-text {
  display: block;
  font-size: var(--ytm-font-caption);
  color: var(--ytm-text-secondary);
  margin-top: var(--ytm-space-xs);
}

.ytm-error-text {
  display: block;
  font-size: var(--ytm-font-caption);
  color: #ef4444;
  margin-top: var(--ytm-space-xs);
}
```

### Typography Components

#### Headings
```css
.ytm-display {
  font-size: var(--ytm-font-display);
  font-weight: var(--ytm-weight-bold);
  line-height: 1.2;
  color: var(--ytm-text-heading);
  margin-bottom: var(--ytm-space-sm);
}

.ytm-h1 {
  font-size: var(--ytm-font-h1);
  font-weight: var(--ytm-weight-semibold);
  line-height: 1.3;
  color: var(--ytm-text-heading);
  margin-bottom: var(--ytm-space-md);
}

.ytm-h2 {
  font-size: var(--ytm-font-h2);
  font-weight: var(--ytm-weight-semibold);
  line-height: 1.4;
  color: var(--ytm-text-heading);
  margin-bottom: var(--ytm-space-md);
}

.ytm-h3 {
  font-size: var(--ytm-font-h3);
  font-weight: var(--ytm-weight-semibold);
  line-height: 1.4;
  color: var(--ytm-text-heading);
  margin-bottom: var(--ytm-space-sm);
}
```

#### Brand Name Styling
```css
.ytm-brand-name {
  font-weight: 900;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  font-variant: small-caps;
  font-family: "Arial Black", "Arial Bold", sans-serif;
}

.ytm-brand-name .emphasis {
  font-size: 1.17em;
  color: #6B8F7F;
  font-variant: normal;
  font-weight: 900;
  text-shadow: 1px 1px 2px rgba(107, 143, 127, 0.3);
}
```

**HTML Example:**
```html
<span class="ytm-brand-name">
  <span class="emphasis">Y</span>our
  <span class="emphasis">T</span>raining
  <span class="emphasis">M</span>onkey
</span>

<!-- Or YTM abbreviation (acceptable): -->
<p>Welcome to YTM!</p>
```

**Note:** Y, T, M are slightly larger (1.17em) in sage green (#6B8F7F) with bold weight for emphasis.

### Badges & Pills

#### Patent Badge
```css
.ytm-badge-patent {
  display: inline-block;
  background: rgba(255, 255, 255, 0.15);
  padding: 0.5rem 1rem;
  border-radius: var(--ytm-radius-full);
  font-weight: var(--ytm-weight-semibold);
  font-size: var(--ytm-font-small);
  backdrop-filter: blur(10px);
}
```

**HTML Example:**
```html
<span class="ytm-badge-patent">Patent-Pending Technology</span>
```

#### Status Badge
```css
.ytm-badge {
  display: inline-block;
  padding: 0.35rem 0.75rem;
  border-radius: var(--ytm-radius-full);
  font-size: var(--ytm-font-caption);
  font-weight: var(--ytm-weight-semibold);
}

.ytm-badge-success {
  background: var(--ytm-success-green-light);
  color: var(--ytm-success-green-dark);
}

.ytm-badge-warning {
  background: var(--ytm-alert-bg);
  color: var(--ytm-alert-text);
}

.ytm-badge-info {
  background: #DBEAFE;
  color: #1e40af;
}
```

**HTML Example:**
```html
<span class="ytm-badge ytm-badge-success">Sweet Spot</span>
<span class="ytm-badge ytm-badge-warning">Caution</span>
<span class="ytm-badge ytm-badge-info">Analyzing</span>
```

---

## Common Patterns

### Hero Section (Landing Page)
```html
<section class="ytm-hero">
  <div class="ytm-hero-logo">
    <img src="/static/images/YTM_Logo_byandfor_300.webp" alt="Your Training Monkey">
  </div>
  <div class="ytm-hero-content">
    <h1 class="ytm-display">Your Training Monkey</h1>
    <p class="ytm-subtitle">Prevent Injuries — Train Smarter</p>
    <p class="ytm-description">
      The only platform with patent-pending <strong>normalized divergence analysis</strong>
      that reveals when your body and training are out of sync.
    </p>
  </div>
</section>
```

```css
.ytm-hero {
  background: linear-gradient(90deg, var(--ytm-trail-sky) 0%,
              var(--ytm-mountain-ridge) 50%, var(--ytm-night-summit) 100%);
  color: white;
  padding: 3rem 2rem;
  text-align: center;
  min-height: 250px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 2rem;
}

.ytm-subtitle {
  font-size: var(--ytm-font-body-lg);
  margin-bottom: var(--ytm-space-md);
  opacity: 0.95;
}

.ytm-description {
  font-size: var(--ytm-font-body);
  max-width: 700px;
  margin: 0 auto;
  opacity: 0.9;
}
```

### Step-by-Step Cards
```html
<div class="ytm-steps">
  <div class="ytm-step-card">
    <div class="ytm-step-number">1</div>
    <h3 class="ytm-step-title">Connect Strava</h3>
    <p class="ytm-step-description">
      Securely link your Strava account to import training history.
    </p>
  </div>

  <div class="ytm-step-card">
    <div class="ytm-step-number">2</div>
    <h3 class="ytm-step-title">Analyze Patterns</h3>
    <p class="ytm-step-description">
      Our algorithm calculates divergence between external work and internal load.
    </p>
  </div>

  <div class="ytm-step-card">
    <div class="ytm-step-number">3</div>
    <h3 class="ytm-step-title">Train Smarter</h3>
    <p class="ytm-step-description">
      Get daily AI recommendations to optimize training and prevent injuries.
    </p>
  </div>
</div>
```

```css
.ytm-steps {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: var(--ytm-space-lg);
  margin: var(--ytm-space-xl) 0;
}

.ytm-step-card {
  background: var(--ytm-bg-light);
  padding: var(--ytm-space-lg);
  border-radius: var(--ytm-radius-md);
  border-left: 4px solid #3b82f6;
}

.ytm-step-number {
  display: inline-block;
  background: #3b82f6;
  color: white;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  text-align: center;
  line-height: 30px;
  font-weight: var(--ytm-weight-semibold);
  margin-bottom: var(--ytm-space-md);
}

.ytm-step-title {
  font-size: var(--ytm-font-body-lg);
  font-weight: var(--ytm-weight-semibold);
  margin-bottom: var(--ytm-space-sm);
  color: var(--ytm-text-heading);
}

.ytm-step-description {
  color: var(--ytm-text-secondary);
  line-height: 1.6;
  margin: 0;
}
```

### Loading Spinner (Branded)
```html
<div class="ytm-spinner">
  <div class="ytm-spinner-ring"></div>
  <div class="ytm-spinner-text">Analyzing your training...</div>
</div>
```

```css
.ytm-spinner {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--ytm-space-2xl);
}

.ytm-spinner-ring {
  width: 48px;
  height: 48px;
  border: 4px solid var(--ytm-bg-light);
  border-top: 4px solid var(--ytm-purple-start);
  border-radius: 50%;
  animation: ytm-spin 1s linear infinite;
}

@keyframes ytm-spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.ytm-spinner-text {
  margin-top: var(--ytm-space-md);
  color: var(--ytm-text-secondary);
  font-size: var(--ytm-font-small);
}
```

### Empty State
```html
<div class="ytm-empty-state">
  <div class="ytm-empty-icon">📊</div>
  <h3 class="ytm-empty-title">No Training Data Yet</h3>
  <p class="ytm-empty-message">
    Connect your Strava account to start analyzing your training load.
  </p>
  <a href="/auth/strava" class="ytm-btn-primary">Connect Strava</a>
</div>
```

```css
.ytm-empty-state {
  text-align: center;
  padding: var(--ytm-space-2xl);
  max-width: 500px;
  margin: 0 auto;
}

.ytm-empty-icon {
  font-size: 4rem;
  margin-bottom: var(--ytm-space-md);
  opacity: 0.5;
}

.ytm-empty-title {
  font-size: var(--ytm-font-h2);
  color: var(--ytm-text-heading);
  margin-bottom: var(--ytm-space-sm);
}

.ytm-empty-message {
  color: var(--ytm-text-secondary);
  margin-bottom: var(--ytm-space-lg);
}
```

---

## Copy Templates

### Welcome Messages

**Post-Signup:**
```
Welcome to Your Training Monkey!

Your account is ready. Here's what happens next:

1. Your Strava data is syncing (this may take a few minutes)
2. We'll analyze your last 28+ days of training
3. You'll receive your first divergence analysis shortly

While you wait, check out our [Getting Started Guide](/guide) to learn how to interpret your training status.

Questions? We're here to help: support@yourtrainingmonkey.com
```

**Dashboard Welcome (First Visit):**
```
Welcome! Let's Get You Started

Your Training Monkey analyzes the relationship between your external training load (distance, elevation) and your internal response (heart rate, perceived effort).

When these diverge significantly, it's an early warning sign of overtraining or injury risk - something your Garmin can't calculate.

Need help understanding your dashboard? [View Tutorial](/tutorials)
```

### Error Messages

**Insufficient Data:**
```
Not Enough Training Data

Your Training Monkey requires at least 28 days of consistent training data to calculate reliable divergence analysis.

Current data: [X] days
Required: 28 days

Keep training and sync with Strava. We'll notify you when analysis is ready!
```

**Strava Connection Error:**
```
Strava Connection Failed

We couldn't connect to your Strava account. This usually happens if:

• Authorization was cancelled
• The connection timed out
• Strava is experiencing issues

[Try Again] [Contact Support]
```

**Generic Error:**
```
Something Went Wrong

We encountered an unexpected error. Our team has been notified and we're looking into it.

In the meantime:
• Try refreshing the page
• Check your internet connection
• Contact support if the issue persists

Error ID: [error_code]
```

### Email Subject Lines

**Daily Recommendation:**
```
Today's Training: [Sweet Spot|Caution|Recovery] - [Date]
```

**Alert:**
```
⚠️ Overtraining Risk Detected - Review Before Training
```

**Welcome:**
```
Welcome to Your Training Monkey - Let's Get Started
```

**Data Sync:**
```
✅ Strava Data Synced - Your Analysis Is Ready
```

### Button Copy

**Primary Actions:**
- "Connect with Strava"
- "Start Training Smarter"
- "View My Dashboard"
- "Analyze My Training"
- "See My Divergence"

**Secondary Actions:**
- "Learn More"
- "How It Works"
- "View Tutorial"
- "Skip for Now"
- "Go to Settings"

**Destructive Actions:**
- "Disconnect Strava"
- "Delete Account"
- "Clear Data"

**Success Confirmation:**
- "Got It"
- "Continue"
- "Sounds Good"

---

## Code Snippets

### React Component: Brand Name
```jsx
// BrandName.jsx
export const BrandName = ({ className = "" }) => {
  return (
    <span className={`ytm-brand-name ${className}`}>
      <em><strong>Your Training Monkey</strong></em>
    </span>
  );
};

// Usage:
<p>Welcome to <BrandName />!</p>
```

### React Component: Status Badge
```jsx
// StatusBadge.jsx
export const StatusBadge = ({ status }) => {
  const statusConfig = {
    'sweet-spot': { label: 'Sweet Spot', variant: 'success' },
    'caution': { label: 'Caution', variant: 'warning' },
    'recovery': { label: 'Recovery', variant: 'info' },
    'risk': { label: 'High Risk', variant: 'warning' }
  };

  const config = statusConfig[status] || statusConfig['sweet-spot'];

  return (
    <span className={`ytm-badge ytm-badge-${config.variant}`}>
      {config.label}
    </span>
  );
};

// Usage:
<StatusBadge status="sweet-spot" />
```

### Python/Jinja Template: Flash Messages
```python
# Flask route
from flask import flash

@app.route('/save-settings', methods=['POST'])
def save_settings():
    # ... save logic ...
    flash('Settings saved successfully!', 'success')
    return redirect(url_for('settings'))
```

```jinja
<!-- Template -->
{% with messages = get_flashed_messages(with_categories=true) %}
  {% if messages %}
    <div class="ytm-flash-messages">
      {% for category, message in messages %}
        <div class="ytm-card-{{ category }}">
          {% if category == 'success' %}✅{% elif category == 'error' %}❌{% endif %}
          {{ message }}
        </div>
      {% endfor %}
    </div>
  {% endif %}
{% endwith %}
```

### Responsive Breakpoints
```css
/* Mobile First Approach */

/* Small phones */
@media (max-width: 480px) {
  .ytm-hero {
    padding: 2rem 1rem;
  }

  .ytm-display {
    font-size: 2rem;
  }

  .ytm-steps {
    grid-template-columns: 1fr;
  }
}

/* Tablets */
@media (max-width: 768px) {
  .ytm-hero {
    flex-direction: column;
  }

  .ytm-h1 {
    font-size: 1.75rem;
  }
}

/* Desktop */
@media (min-width: 1200px) {
  .ytm-container {
    max-width: 1400px;
    margin: 0 auto;
  }
}
```

### Dark Mode Considerations (Future)
```css
/* Prepare for dark mode */
@media (prefers-color-scheme: dark) {
  :root {
    /* Override colors for dark mode */
    --ytm-bg-light: #1F2937;
    --ytm-text-primary: #F9FAFB;
    --ytm-text-heading: #FFFFFF;
    /* ... other overrides ... */
  }
}
```

### Accessibility Helpers
```css
/* Screen reader only */
.ytm-sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border-width: 0;
}

/* Focus visible (keyboard navigation) */
.ytm-btn-primary:focus-visible,
.ytm-input:focus-visible {
  outline: 3px solid var(--ytm-purple-start);
  outline-offset: 2px;
}

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## Quick Checklist for New Components

When creating a new component, ensure:

**Visual:**
- [ ] Uses CSS variables from `:root`
- [ ] Follows spacing scale (sm/md/lg/xl)
- [ ] Uses brand colors appropriately
- [ ] Includes hover/active states
- [ ] Responsive (mobile-first)
- [ ] Meets contrast requirements (4.5:1 min)

**Code:**
- [ ] Semantic HTML (use correct elements)
- [ ] Accessible (ARIA labels where needed)
- [ ] No inline styles (use classes)
- [ ] Consistent naming (`ytm-component-variant`)
- [ ] Documented in this guide (if reusable)

**Content:**
- [ ] Voice matches brand (see framework)
- [ ] No medical claims without disclaimers
- [ ] Brand name with Y, T, M emphasis in sage green (#6B8F7F)
- [ ] Clear, action-oriented copy
- [ ] Error states considered

---

## File Organization

### Recommended Structure
```
/static/
  /css/
    variables.css          (CSS variables from this guide)
    components.css         (Reusable components)
    pages/
      landing.css
      dashboard.css
      settings.css
  /images/
    /brand/
      YTM_Logo_*.webp
    /ui/
      icons/
      illustrations/
  /js/
    components/
      StatusBadge.js
      BrandName.js
```

### Import Order (CSS)
```css
/* 1. Variables */
@import 'variables.css';

/* 2. Base/Reset */
@import 'reset.css';

/* 3. Components */
@import 'components.css';

/* 4. Page-specific */
@import 'pages/landing.css';
```

---

## Resources

**Brand Framework:** `YOUR_TRAINING_MONKEY_BRAND_FRAMEWORK.md`
**Logo Files:** `/app/static/images/YTM_Logo_*`
**Strava Assets:** `/app/Strava_brand/`
**Color Palette Tool:** [Use coolors.co with our hex codes]
**Contrast Checker:** [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)

---

## Common Questions

**Q: Can I use a different shade of green for success messages?**
A: Stick to `--ytm-success-green` for consistency. If you need a lighter version, use `--ytm-success-green-light` or `--ytm-success-green-bg`.

**Q: When should I use the orange CTA button vs. purple button?**
A: Orange is ONLY for the most critical action on a page (typically "Connect with Strava" or "Start Training"). Use purple for all other primary actions.

**Q: Can I abbreviate "Your Training Monkey" to "YTM"?**
A: Yes, YTM is acceptable in code, comments, and internal use. Preferred is full name with Y, T, M emphasized in sage green (#6B8F7F) for user-facing content.

**Q: What if I need a color that's not in the palette?**
A: Check if you can use an existing color first. If absolutely necessary, add it to the variables file and document it in the brand framework.

**Q: How do I handle the brand name in all-caps headings?**
A: Avoid all-caps for brand name. Use regular case: "Your Training Monkey" even in headings that are otherwise capitalized.

---

**Last Updated:** December 6, 2025
**Maintained By:** Development Team
**Questions?** Refer to main brand framework or contact team lead.
