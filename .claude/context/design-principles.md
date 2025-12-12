# Your Training Monkey Design Principles

This document summarizes the key design principles for YTM. For complete details, see:
- `docs/branding/YOUR_TRAINING_MONKEY_BRAND_FRAMEWORK.md`
- `docs/branding/QUICK_REFERENCE_STYLE_GUIDE.md`

---

## Core Brand Rules

### Color Usage

| Color | Hex | Usage |
|-------|-----|-------|
| Trail Sky | `#E6F0FF` | Light backgrounds |
| Mountain Ridge | `#7D9CB8` | Gradient mid-tone |
| Night Summit | `#1B2E4B` | Dark headers |
| Action Orange | `#FF5722` | **ONE CTA per page MAX** |
| Success Green | `#16A34A` | Positive feedback |
| Purple Gradient | `#667EEA → #764BA2` | Interactive elements |
| Sage Green (YTM) | `#6B8F7F` | Y, T, M letter emphasis |

**Standard Banner Gradient:**
```css
background: linear-gradient(90deg,
  rgba(230, 240, 255, 0.92) 0%,
  rgba(125, 156, 184, 0.92) 50%,
  rgba(27, 46, 75, 0.92) 100%);
```

### Typography

| Element | Size | Weight |
|---------|------|--------|
| Display | 40px | 700 |
| H1 | 32px | 600 |
| H2 | 24px | 600 |
| H3 | 20px | 600 |
| Body | 16px | 400 |

**Critical Rules:**
- All body text **LEFT-ALIGNED** (never center or justify)
- Max line width: **75 characters**
- Line height: **1.6** for body text

### Brand Name Styling

The letters Y, T, M should be emphasized:
- Color: Sage Green `#6B8F7F`
- Size: 1.17em (slightly larger)
- Weight: 900 (extra bold)

### Forbidden Patterns

1. **NO emoji icons** in user-facing UI (use text labels)
2. **NO center-aligned paragraphs**
3. **NO more than ONE orange button per page**
4. **NO hard-coded hex colors** (use CSS variables)

---

## Component Standards

### Buttons

**Primary (Purple Gradient):**
```css
background: linear-gradient(135deg, #667eea, #764ba2);
border-radius: 12px;
padding: 1rem 2rem;
```

**CTA (Orange - Use Sparingly):**
```css
background: #FF5722;
border-radius: 50px; /* Pill shape */
```

**Success (Green):**
```css
background: linear-gradient(135deg, #16a34a, #15803d);
```

### Cards

```css
.ytm-card {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 4px 15px rgba(0,0,0,0.05);
  border: 1px solid #e2e8f0;
}
```

### Form Inputs

```css
.ytm-input {
  padding: 0.875rem 1rem;
  border: 2px solid #e5e7eb;
  border-radius: 10px;
}

.ytm-input:focus {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}
```

---

## Accessibility Requirements

- **Color contrast:** 4.5:1 minimum for text
- **Focus states:** Visible on all interactive elements
- **Keyboard navigation:** Tab order must be logical
- **Form labels:** All inputs must have associated labels

---

## Quick Checklist

Before any UI change:

- [ ] Colors use CSS variables (not hard-coded hex)
- [ ] Text left-aligned, max-width: 75ch
- [ ] Y, T, M emphasized in sage green
- [ ] No emoji icons in UI
- [ ] Max 1 orange CTA per page
- [ ] Contrast meets 4.5:1
- [ ] Focus states visible
- [ ] Loading/empty/error states designed
