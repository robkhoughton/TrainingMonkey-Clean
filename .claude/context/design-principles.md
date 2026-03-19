# Your Training Monkey Design Principles

Single source of truth for all brand and UI standards:
`docs/branding/YOUR_TRAINING_MONKEY_BRAND_FRAMEWORK.md`

---

## Critical Rules (Memorize These)

- **No emoji** in user-facing UI
- **One orange CTA max** per page (`#FF5722`) — marketing/landing pages only
- **Body text left-aligned**, max-width 75ch — never let prose span a wide monitor
- **Forms and input groups**: max-width 560px (≈ `repeat(2, minmax(0, 280px))` for two-column grids). Single-column forms: max-width 480px. Never `width: 100%` on a form container without a max-width cap.
- **Cards and content containers**: max-width 1200px, centered — already standard across the app
- **Y, T, M letters** emphasized in sage green (`#6B8F7F`) in brand name only
- **Contrast** must meet WCAG 4.5:1 for body text

> **Why this matters:** On a 24" monitor at 1920px, an unconstrained input stretches to ~1400px of usable width. WCAG 1.4.8 caps text lines at 80 characters. The `ch` unit enforces this at any font size. Forms follow the same logic — a 560px form is comfortable at any viewport above mobile.

## In-App UI Quick Reference

| Element | Style |
|---------|-------|
| Primary button | `background: #3b82f6`, `border-radius: 4px`, `padding: 6px 16px`, `font-size: 0.8rem`, `font-weight: 600` |
| Secondary button | `background: white`, `border: 1px solid #dee2e6`, same radius/padding/font |
| Card | `background: white`, `border-radius: 8px`, `padding: 20px`, `box-shadow: 0 2px 4px rgba(0,0,0,0.1)` |
| Section divider | `border-bottom: 2px solid #dee2e6` |
| Input / select | `border: 1px solid #dee2e6`, `border-radius: 4px`, `padding: 5px 8px`, `font-size: 0.875rem` |
| Form label | `font-size: 0.8rem`, `color: #6b7280` |
| Form grid (2-col) | `display: grid`, `grid-template-columns: repeat(2, minmax(0, 280px))`, `gap: 15px` |
| Form container | always add `max-width: 560px` — never unconstrained |

## Key Colors

| Name | Hex | Use |
|------|-----|-----|
| Night Summit | `#1B2E4B` | Dark headers |
| Mountain Ridge | `#7D9CB8` | Gradient mid-tone |
| Trail Sky | `#E6F0FF` | Light backgrounds |
| Action Orange | `#FF5722` | One CTA per page, marketing only |
| Success Green | `#16A34A` | Positive feedback |
| Sage Green | `#6B8F7F` | Y, T, M letter emphasis only |
| Primary Text | `#1F2937` | Body copy |
| Secondary Text | `#6b7280` | Labels, help text |
| App Blue | `#3b82f6` | In-app primary buttons, links |

## Tactical Form Aesthetic

All user input forms use a **dark tactical container** — distinct from content cards. This signals mode shift: you are now acting, not reading.

| Element | Style |
|---------|-------|
| Form container | `background: #1B2E4B` + carbon fiber texture (see below), `border: 1px solid rgba(255,87,34,0.7)`, `border-radius: 8px` |
| Header strip | Standard banner gradient (`#E6F0FF → #7D9CB8 → #1B2E4B`), label uppercase 0.7rem `#1B2E4B` |
| Form label | `font-size: 0.75rem`, `font-weight: 700`, `color: #7D9CB8`, `text-transform: uppercase`, `letter-spacing: 0.08em` |
| Input / textarea | `background: #162440` (solid), `border: 1px solid #7D9CB8`, `color: #E6F0FF`, `border-radius: 4px` |
| Number input | add `-webkit-appearance: none; -moz-appearance: textfield` — suppress spinner arrows |
| Primary CTA | `background: #FF5722`, white text, `font-weight: 700`, `letter-spacing: 0.06em` |
| Cancel | `background: rgba(230,240,255,0.07)`, `color: #E6F0FF`, Mountain Ridge border |
| Required marker | `color: rgba(255,87,34,0.8)` — `*` only, no prose |

**Carbon fiber texture** (copy exactly — wrong values look like diamond plate):
```css
background-image:
  linear-gradient(135deg, rgba(255,255,255,0.04) 25%, transparent 25%),
  linear-gradient(225deg, rgba(255,255,255,0.04) 25%, transparent 25%),
  linear-gradient(315deg, rgba(255,255,255,0.04) 25%, transparent 25%),
  linear-gradient(45deg,  rgba(255,255,255,0.04) 25%, transparent 25%);
background-size: 4px 4px;   /* must be 4px — 8px reads as diamond plate regardless of opacity */
```

**CTA verbs** — never use "Save":

| Context | CTA |
|---------|-----|
| Add new goal/target | SET TARGET |
| Edit existing | COMMIT CHANGES |
| Log a result | LOG RESULT |
| Settings / preferences | APPLY |
| First-time setup | INITIALIZE |

**Reference implementations:** `RaceGoalsManager.tsx` (modal), `TrainingScheduleConfig.tsx` (inline panel), `SeasonPage.tsx` GoalModal

---

## Modal Behavior Rules (Locked)

All data-entry modals follow this pattern exactly. No exceptions.

**Structure:**
- Fixed-position overlay: `position: fixed; inset: 0; z-index: 1000; background: rgba(0,0,0,0.65)`
- Overlay is flex-centered: `display: flex; align-items: center; justify-content: center; padding: 20px`
- Clicking the overlay backdrop (not the modal itself) closes the modal
- Modal container: tactical dark form (`#1B2E4B` + carbon fiber), `border: 1px solid rgba(255,87,34,0.7)`, `border-radius: 8px`

**Sizing — hard limits:**
- `width: 100%` on the modal container (fills to max-width on narrow viewports)
- `max-width: 560px` — **non-negotiable**, applies to all modals
- `max-height: 90vh` with `overflow-y: auto` — never let a modal exceed viewport height

**Header strip:** always present, standard banner gradient, uppercase label `0.7rem #1B2E4B`

**Footer / button row:** `display: flex; justify-content: flex-end; gap: 12px` — Cancel left of primary CTA

**Inline panels** (e.g. TrainingScheduleConfig): same tactical style, same `max-width: 560px`. No overlay.

---

## Card Header Semantic Convention

Card header color signals **editability** — a subtle but meaningful distinction:

| Header style | Gradient | Text | Meaning |
|---|---|---|---|
| **Configurable** | `#E6F0FF → #7D9CB8 → #1B2E4B` (light→dark) | `#1B2E4B` dark | User sets this — Race Season, Coaching Preferences, training schedule |
| **Data-driven** | `#1B2E4B → #2d4a6e` (dark→darker) | `#7D9CB8` label / `#ffffff` title | System computes this — Race Readiness, Athlete Model |

Never mix these. A card that is read-only gets the dark header. A card the user can edit gets the standard gradient.

---

**Standard Banner Gradient (configurable cards):**
```css
background: linear-gradient(90deg, #E6F0FF 0%, #7D9CB8 50%, #1B2E4B 100%);
```

**Data-driven card gradient:**
```css
background: linear-gradient(90deg, #1B2E4B 0%, #2d4a6e 100%);
```
Used on: Race Readiness, Athlete Model
