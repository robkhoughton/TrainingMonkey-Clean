# Your Training Monkey - Quick Reference Style Guide
**Visual Examples & Code Snippets**

---

## Color Palette with Examples

### Primary Colors (Blues/Grays)

```css
/* Navigation Blue Gradient */
--ytm-trail-sky: #E6F0FF;        /* Light backgrounds */
--ytm-mountain-ridge: #7D9CB8;   /* Mid-tone accents */
--ytm-night-summit: #1B2E4B;     /* Dark headers */
```

**Standard Banner Gradient:**
```css
background: linear-gradient(90deg,
  rgba(230, 240, 255, 0.92) 0%,
  rgba(125, 156, 184, 0.92) 50%,
  rgba(27, 46, 75, 0.92) 100%);
```

Used on: Coach, Guide, Settings pages

### Functional Colors

```css
/* Action Colors */
--ytm-action-orange: #FF5722;      /* CTAs ONLY */
--ytm-success-green: #16A34A;      /* Positive feedback */
--ytm-purple-start: #667EEA;       /* Interactive elements */
--ytm-purple-end: #764BA2;         /* Gradients */
--ytm-sage-green: #6B8F7F;         /* Y, T, M emphasis */

/* Alert/Warning */
--ytm-alert-bg: #FEF3C7;           /* Warning background */
--ytm-alert-border: #F59E0B;       /* Warning border */
--ytm-alert-text: #92400E;         /* Warning text */
```

**Critical Rule:** Only ONE orange button per page!

---

## Typography Examples

### Heading Hierarchy

```html
<!-- Display (Hero Headlines) -->
<h1 class="ytm-display">Your Training Monkey</h1>
<!-- Size: 40px | Weight: 700 | Line-height: 1.2 -->

<!-- H1 (Page Titles) -->
<h1 class="ytm-h1">Training Dashboard</h1>
<!-- Size: 32px | Weight: 600 | Line-height: 1.3 -->

<!-- H2 (Section Headers) -->
<h2 class="ytm-h2">Today's Recommendation</h2>
<!-- Size: 24px | Weight: 600 | Line-height: 1.4 -->

<!-- H3 (Subsections) -->
<h3 class="ytm-h3">Recent Activities</h3>
<!-- Size: 20px | Weight: 600 | Line-height: 1.4 -->

<!-- Body Text -->
<p>Your divergence analysis shows...</p>
<!-- Size: 16px | Weight: 400 | Line-height: 1.6 -->
<!-- Max-width: 75ch for readability -->
```

### Brand Name Styling

**Full Name with Y, T, M Emphasis:**
```html
<span style="
  font-weight: 900;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  font-variant: small-caps;
  font-family: 'Arial Black', 'Arial Bold', sans-serif;
">
  <span style="font-size: 1.17em; color: #6B8F7F; font-variant: normal; font-weight: 900; text-shadow: 1px 1px 2px rgba(107,143,127,0.3);">Y</span>our
  <span style="font-size: 1.17em; color: #6B8F7F; font-variant: normal; font-weight: 900; text-shadow: 1px 1px 2px rgba(107,143,127,0.3);">T</span>raining
  <span style="font-size: 1.17em; color: #6B8F7F; font-variant: normal; font-weight: 900; text-shadow: 1px 1px 2px rgba(107,143,127,0.3);">M</span>onkey
</span>
```

**Renders as:** <span style="font-size: 1.2em;">**<span style="font-size: 1.17em; color: #6B8F7F; font-weight: 900;">Y</span>OUR <span style="font-size: 1.17em; color: #6B8F7F; font-weight: 900;">T</span>RAINING <span style="font-size: 1.17em; color: #6B8F7F; font-weight: 900;">M</span>ONKEY**</span>

**Acceptable Variations:**
- Full name with emphasis: "Your Training Monkey" (preferred)
- Abbreviation: "YTM" (acceptable in code, comments, internal use)

**Sage Green Color:** `#6B8F7F` - Stronger, darker shade for Y, T, M letters
**Styling:** Slightly larger (1.17em), bold weight (900), subtle text-shadow for emphasis

---

## Readability Guidelines

### Text Width
All wrapping text should be left-justified with maximum width:
- **Paragraphs:** max-width: 75ch (approx 60-75 characters)
- **Headlines:** Can exceed for impact
- **Buttons/Labels:** As needed

```css
p, li {
  max-width: 75ch;
  text-align: left;
}
```

### Alignment
- **Body text:** Left-aligned (never center or justify)
- **Headlines:** Left-aligned (can center for hero sections)
- **Forms:** Left-aligned labels above fields

---

## Button Styles

### Primary Action Button (Purple Gradient)

```css
.ytm-btn-primary {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  padding: 1rem 2rem;
  border-radius: 12px;
  font-size: 1.1rem;
  font-weight: 600;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
}
```

```html
<button class="ytm-btn-primary">Get Started</button>
```

### Success Button (Green)

```css
.ytm-btn-success {
  background: linear-gradient(135deg, #16a34a, #15803d);
  color: white;
  padding: 1rem 2rem;
  border-radius: 12px;
}
```

### CTA Button (Orange - Use Sparingly!)

```css
.ytm-btn-cta {
  background: #FF5722;
  color: white;
  padding: 1rem 2.5rem;
  border-radius: 50px;  /* Pill shape */
  font-weight: 600;
}
```

**IMPORTANT:** Maximum ONE orange CTA per page!

### Secondary/Outline Button

```css
.ytm-btn-secondary {
  background: transparent;
  color: #667EEA;
  border: 2px solid #667EEA;
  padding: 1rem 2rem;
  border-radius: 12px;
}
```

---

## Card Styles

### Standard Card

```css
.ytm-card {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 4px 15px rgba(0,0,0,0.05);
  border: 1px solid #e2e8f0;
}
```

### Highlighted Card (Important Info)

```css
.ytm-card-highlight {
  background: #f8fafc;
  border-left: 4px solid #3b82f6;
  border-radius: 12px;
  padding: 1rem 1.25rem;
}
```

### Alert Card (Warning)

```css
.ytm-card-alert {
  background: #fef3c7;
  border: 2px solid #f59e0b;
  border-radius: 12px;
  padding: 1.25rem;
}
```

### Success Card

```css
.ytm-card-success {
  background: rgba(22, 163, 74, 0.1);
  border: 1px solid #16a34a;
  border-radius: 12px;
  padding: 1rem;
  text-align: center;
}
```

---

## Voice & Messaging Examples

### DO's vs DON'Ts

**Headlines:**

✅ DO:
- "The Training Status Your Garmin Can't Show You"
- "See Your Divergence - Prevent Injuries"
- "Trail Running Intelligence for Smart Athletes"

❌ DON'T:
- "Revolutionary AI-Powered Training Optimization" (buzzwordy)
- "Never Get Injured Again!" (over-promise)

**Call-to-Action Copy:**

✅ DO:
- "Connect with Strava" (specific action)
- "Start Training Smarter" (benefit-focused)
- "See My Divergence" (curiosity-driven)

❌ DON'T:
- "Sign Up Now!" (generic)
- "Click Here" (no context)

**Error Messages:**

✅ DO:
```
Not Enough Training Data

Your Training Monkey requires at least 28 days of
consistent training data to calculate reliable divergence
analysis.

Current data: 12 days
Required: 28 days

Keep training and sync with Strava. We'll notify you when
analysis is ready!
```

❌ DON'T:
```
Error: Insufficient data

You need more data.

[OK]
```

---

## Icon Usage

**Avoid Emoji Icons**
- Do NOT use emoji in user-facing interfaces
- Use text labels instead
- Exception: Internal documentation is acceptable

✅ DO:
- "Sweet Spot" (text badge)
- "Caution" (text badge)
- "Important Notice" (text heading)

❌ DON'T:
- "✅ Sweet Spot"
- "⚠️ Caution"
- "🎉 Success!"

---

## Form Elements

### Text Input

```css
.ytm-input {
  width: 100%;
  padding: 0.875rem 1rem;
  border: 2px solid #e5e7eb;
  border-radius: 10px;
  font-size: 1rem;
}

.ytm-input:focus {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}
```

### Validation Messages

```css
/* Error */
.ytm-error-text {
  color: #ef4444;
  font-size: 0.85rem;
  margin-top: 0.25rem;
}

/* Success */
.ytm-success-text {
  color: #16a34a;
  font-size: 0.85rem;
}
```

**No emoji - text only:**
- "Please enter a valid email" (not "❌ Invalid!")
- "Email saved successfully" (not "✅ Saved!")

---

## Status Badges

```css
.ytm-badge {
  padding: 0.35rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.85rem;
  font-weight: 600;
}

.ytm-badge-success {
  background: #dcfce7;
  color: #15803d;
}

.ytm-badge-warning {
  background: #fef3c7;
  color: #92400e;
}

.ytm-badge-info {
  background: #dbeafe;
  color: #1e40af;
}
```

**Text-only labels:**
- `<span class="ytm-badge ytm-badge-success">Sweet Spot</span>`
- `<span class="ytm-badge ytm-badge-warning">Caution</span>`
- `<span class="ytm-badge ytm-badge-info">Analyzing</span>`

---

## Hero Section

```html
<section class="ytm-hero">
  <h1 class="ytm-display">
    <span class="ytm-brand-name">
      <span class="emphasis">Y</span>our
      <span class="emphasis">T</span>raining
      <span class="emphasis">M</span>onkey
    </span>
  </h1>
  <p class="ytm-subtitle">Prevent Injuries — Train Smarter</p>
  <p class="ytm-description">
    The only platform with patent-pending normalized
    divergence analysis that reveals when your body and
    training are out of sync.
  </p>
</section>
```

```css
.ytm-hero {
  background: linear-gradient(90deg,
    rgba(230, 240, 255, 0.92) 0%,
    rgba(125, 156, 184, 0.92) 50%,
    rgba(27, 46, 75, 0.92) 100%);
  color: white;
  padding: 3rem 2rem;
  text-align: left;
}

.ytm-description {
  max-width: 60ch;
}
```

---

## Common Mistakes to Avoid

### Visual Mistakes

❌ Using emoji icons in UI
❌ Center-aligning body text
❌ Paragraphs wider than 75 characters
❌ Multiple orange CTA buttons per page
❌ Missing Y, T, M sage green emphasis

✅ Text-only labels
✅ Left-aligned body text
✅ Max-width: 75ch for readability
✅ One orange CTA per page maximum
✅ Always emphasize Y, T, M in sage green

### Content Mistakes

❌ "Welcome to Your Training Monkey!" (missing emphasis)
❌ Center-justified paragraphs
❌ Long lines without max-width

✅ "Welcome to **<span style="color: #6B8F7F;">Y</span>OUR <span style="color: #6B8F7F;">T</span>RAINING <span style="color: #6B8F7F;">M</span>ONKEY**!"
✅ Left-aligned, max 75ch width
✅ "YTM" abbreviation is acceptable

---

## Quick Checklist

Before launching any new component:

**Visual:**
- [ ] Uses CSS variables (not hard-coded hex)
- [ ] Text left-aligned, max-width: 75ch
- [ ] Y, T, M slightly larger with sage green (#6B8F7F)
- [ ] No emoji icons in UI
- [ ] Follows spacing scale
- [ ] Meets contrast requirements (4.5:1)

**Content:**
- [ ] Voice matches brand personality
- [ ] Brand name has Y, T, M emphasis
- [ ] Clear, action-oriented copy
- [ ] No emoji in user-facing text
- [ ] Trail-running focus maintained

**Functionality:**
- [ ] Loading states designed
- [ ] Empty states designed
- [ ] Error states designed (no emoji)
- [ ] Keyboard navigation works

---

## Resources

**Complete Framework:** `YOUR_TRAINING_MONKEY_BRAND_FRAMEWORK.md`
**Code Library:** `BRAND_APPLICATION_GUIDE.md`
**Visual Examples:** `VISUAL_STYLE_EXAMPLES.html`
**This Guide:** `QUICK_REFERENCE_STYLE_GUIDE.md`

**Last Updated:** December 8, 2025
**Version:** 1.1
