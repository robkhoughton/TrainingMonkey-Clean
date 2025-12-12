# Branding Guidelines Update - December 8, 2025

## Summary of Changes

All branding documents have been updated to reflect the correct
brand guidelines as implemented in the application.

---

## Key Corrections

### 1. Brand Name Styling

**UPDATED:**
- Y, T, M letters are emphasized in stronger sage green (`#6B8F7F`)
- Y, T, M are slightly larger than other letters (1.17em)
- Y, T, M have bold weight (900) and subtle text-shadow
- Full styling:
  ```css
  font-weight: 900;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  font-variant: small-caps;
  font-family: "Arial Black", "Arial Bold", sans-serif;
  ```

**Example:**
```html
<span class="ytm-brand-name">
  <span style="font-size: 1.17em; color: #6B8F7F; font-weight: 900; text-shadow: 1px 1px 2px rgba(107,143,127,0.3);">Y</span>our
  <span style="font-size: 1.17em; color: #6B8F7F; font-weight: 900; text-shadow: 1px 1px 2px rgba(107,143,127,0.3);">T</span>raining
  <span style="font-size: 1.17em; color: #6B8F7F; font-weight: 900; text-shadow: 1px 1px 2px rgba(107,143,127,0.3);">M</span>onkey
</span>
```

### 2. YTM Abbreviation

**PREVIOUS:** "Never use 'YTM' in user-facing content"

**UPDATED:** "YTM abbreviation is acceptable in code, comments,
and internal use. Preferred is full name with Y, T, M emphasis
for user-facing content."

### 3. Banner Gradient

**UPDATED:** Standard banner gradient for Coach/Guide/Settings
pages:
```css
background: linear-gradient(90deg,
  rgba(230, 240, 255, 0.92) 0%,
  rgba(125, 156, 184, 0.92) 50%,
  rgba(27, 46, 75, 0.92) 100%);
```

### 4. Emoji Icons

**UPDATED:** Avoid emoji icons in user-facing interfaces.

**Before:**
- "✅ Sweet Spot"
- "⚠️ Important Notice"
- "🎉 Success!"

**After:**
- "Sweet Spot" (text badge)
- "Important Notice" (text heading)
- "Success!" (text only)

**Exception:** Emoji acceptable in internal documentation only.

### 5. Readability Guidelines

**ADDED:**

**Text Alignment:**
- All body text: Left-aligned (never center or justify)
- Paragraphs: `text-align: left;`
- Max-width: `75ch` (60-75 characters per line)

**Example:**
```css
p, li {
  max-width: 75ch;
  text-align: left;
}
```

**Rationale:** Improves readability and reduces eye strain.

---

## Updated Color Palette

Added sage green for Y, T, M emphasis:

```css
/* Sage Green (for Y, T, M emphasis) */
--ytm-sage-green: #6B8F7F;
```

**Usage:** Exclusively for emphasizing Y, T, M letters in brand
name.

---

## Updated Files

### Primary Documentation
1. **VISUAL_STYLE_EXAMPLES.html** - Live visual examples with
   all corrections
2. **QUICK_REFERENCE_STYLE_GUIDE.md** - Quick reference with
   updated guidelines
3. **BRANDING_README.md** - Overview with all corrections

### What Changed in Each File

**VISUAL_STYLE_EXAMPLES.html:**
- Added sage green color swatch
- Updated banner gradient example
- Updated brand name styling with Y, T, M emphasis
- Removed emoji icons from all examples
- Added max-width: 75ch for text
- Changed text-align to left

**QUICK_REFERENCE_STYLE_GUIDE.md:**
- Added sage green color documentation
- Updated brand name styling section
- Added readability guidelines section
- Removed emoji from all examples
- Updated DO/DON'T comparisons
- Added YTM abbreviation acceptance

**BRANDING_README.md:**
- Updated FAQ about YTM abbreviation
- Added readability guidelines
- Updated visual checklist
- Added sage green to color palette
- Updated version history to v1.1

---

## Quick Reference: Brand Name

### Preferred (User-Facing)
```html
<span style="
  font-weight: 900;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  font-variant: small-caps;
  font-family: 'Arial Black', sans-serif;
">
  <span style="font-size: 1.17em; color: #6B8F7F; font-weight: 900; text-shadow: 1px 1px 2px rgba(107,143,127,0.3);">Y</span>our
  <span style="font-size: 1.17em; color: #6B8F7F; font-weight: 900; text-shadow: 1px 1px 2px rgba(107,143,127,0.3);">T</span>raining
  <span style="font-size: 1.17em; color: #6B8F7F; font-weight: 900; text-shadow: 1px 1px 2px rgba(107,143,127,0.3);">M</span>onkey
</span>
```

### Acceptable (Internal/Space-Limited)
```
YTM
```

---

## Visual Comparison

### Old Style
```
Your Training Monkey (italic, bold, no color emphasis)
```

### New Style
```
YOUR TRAINING MONKEY
^     ^        ^
Slightly larger (1.17em)
Stronger sage green (#6B8F7F), bold weight, subtle shadow
Small-caps for remaining letters
```

---

## Implementation Notes

### Frontend (React/TypeScript)
Already implemented in `frontend/src/App.tsx` (lines 150-180)

### Templates (Jinja/HTML)
Already implemented in:
- `app/templates/base_getting_started.html`
- `app/templates/base_settings.html`

### CSS Variables
Add to your root CSS:
```css
:root {
  --ytm-sage-green: #6B8F7F;
}

.ytm-brand-name .emphasis {
  font-size: 1.17em;
  color: #6B8F7F;
  font-weight: 900;
  text-shadow: 1px 1px 2px rgba(107, 143, 127, 0.3);
}
```

---

## Developer Checklist

When implementing brand name:

- [ ] Use full name with Y, T, M emphasis (preferred)
- [ ] OR use "YTM" abbreviation (acceptable)
- [ ] Apply sage green (#6B8F7F) to Y, T, M
- [ ] Y, T, M slightly larger (1.17em), bold weight 900
- [ ] Add subtle text-shadow to Y, T, M for emphasis
- [ ] Use small-caps for remaining letters
- [ ] Left-align text, max-width: 75ch
- [ ] Avoid emoji icons in UI

---

## Questions?

Refer to:
- **Visual Examples:** `VISUAL_STYLE_EXAMPLES.html`
- **Quick Reference:** `QUICK_REFERENCE_STYLE_GUIDE.md`
- **Complete Guide:** `BRANDING_README.md`

**Updated:** December 8, 2025
**Version:** 1.1
