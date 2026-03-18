# Your Training Monkey Design Principles

Single source of truth for all brand and UI standards:
`docs/branding/YOUR_TRAINING_MONKEY_BRAND_FRAMEWORK.md`

---

## Critical Rules (Memorize These)

- **No emoji** in user-facing UI
- **One orange CTA max** per page (`#FF5722`) — marketing/landing pages only
- **Body text left-aligned**, max-width 75ch
- **Y, T, M letters** emphasized in sage green (`#6B8F7F`) in brand name only
- **Contrast** must meet WCAG 4.5:1 for body text

## In-App UI Quick Reference

| Element | Style |
|---------|-------|
| Primary button | `background: #3b82f6`, `border-radius: 4px`, `padding: 6px 16px`, `font-size: 0.8rem`, `font-weight: 600` |
| Secondary button | `background: white`, `border: 1px solid #dee2e6`, same radius/padding/font |
| Card | `background: white`, `border-radius: 8px`, `padding: 20px`, `box-shadow: 0 2px 4px rgba(0,0,0,0.1)` |
| Section divider | `border-bottom: 2px solid #dee2e6` |
| Input / select | `border: 1px solid #dee2e6`, `border-radius: 4px`, `padding: 5px 8px`, `font-size: 0.875rem` |
| Form label | `font-size: 0.8rem`, `color: #6b7280` |

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

**Standard Banner Gradient:**
```css
background: linear-gradient(90deg,
  rgba(230, 240, 255, 0.92) 0%,
  rgba(125, 156, 184, 0.92) 50%,
  rgba(27, 46, 75, 0.92) 100%);
```
Used on: Coach, Guide, Settings pages
