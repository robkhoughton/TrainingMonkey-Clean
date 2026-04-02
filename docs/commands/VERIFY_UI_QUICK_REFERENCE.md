# `/verify-ui` Quick Reference

> One-command UI verification workflow: rebuild → deploy → screenshot → verify

---

## Basic Usage

```bash
/verify-ui <component-id> <checklist>
```

**Example**:
```bash
/verify-ui #at-a-glance-meters "stroke 8px, aligned, ticks light, carbon fiber"
```

---

## What It Does

| Step | Action | Time |
|------|--------|------|
| 1️⃣ | Clean old build | 1s |
| 2️⃣ | Rebuild React app | 30s |
| 3️⃣ | Deploy to mock server | 5s |
| 4️⃣ | Screenshot component | 10s |
| 5️⃣ | Verify measurements | 5s |
| 6️⃣ | Generate report | 5s |
| **Total** | **~2 minutes** | |

---

## Common Patterns

### Verify Gauge Component
```bash
/verify-ui #gauge-card "stroke 8px, needles crisp, colors consistent"
```

### Verify Card Layout
```bash
/verify-ui .dashboard-card "spacing 1rem, rounded corners, shadow visible"
```

### Verify Alignment
```bash
/verify-ui #navigation "items aligned, Y coords ±2px, even spacing"
```

### Verify Colors
```bash
/verify-ui #brand-header "green #6B8F7F, orange #FF5722, contrast 4.5:1"
```

---

## Prerequisites

✅ **Mock server must be running**:
```bash
scripts\start_mock_server.bat
```

✅ **Verify server**:
```bash
curl http://localhost:5001
# Should return HTTP 200
```

---

## Output

### ✅ PASS Example
```
✅ PASS - All criteria met

Stroke widths: 8px, 8px, 8px ✓
Vertical alignment: Y=156px ±2px ✓
Tick marks: #e0e0e0 (light) ✓
Carbon fiber: Pattern visible ✓

Console errors: None
```

### ⚠️ ISSUES Example
```
⚠️ ISSUES - 2 problems found

Stroke widths: 8px, 3px, 8px ✗
  → ACWR gauge stroke is 3px (expected 8px)

Vertical alignment: Y=156px, Y=162px ✗
  → Divergence gauge 6px lower than ACWR

Console errors: 1 warning
```

---

## Checklist Items Cheat Sheet

### Measurements
- `"stroke 8px"` - SVG stroke width
- `"width 150px"` - Element width
- `"height 100px"` - Element height
- `"radius 50px"` - Circular gauge radius

### Alignment
- `"aligned ±2px"` - Vertical/horizontal alignment
- `"centered"` - Center alignment
- `"Y coords match"` - Same vertical position
- `"evenly spaced"` - Consistent gaps

### Colors
- `"green #2ecc71"` - Specific hex color
- `"colors consistent"` - Same color across elements
- `"contrast 4.5:1"` - WCAG compliance
- `"ticks light"` - Light-colored tick marks

### Visibility
- `"no clipping"` - Elements not cut off
- `"texture visible"` - Background patterns show
- `"no overlaps"` - Elements don't overlap
- `"labels readable"` - Text fully visible

### Effects
- `"no blur"` - Crisp rendering
- `"no glow"` - No shadow effects
- `"sharp edges"` - Clean lines
- `"carbon fiber"` - Specific texture

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Server not running | `scripts\start_mock_server.bat` |
| Component not found | Check element ID in browser inspector |
| Old design showing | Clear cache, rebuild ensures fresh files |
| Build warnings | Non-blocking, fix optional |
| Console errors | Fix JavaScript issues, rebuild |

---

## Before/After Comparison

### ❌ Manual Process (Before)
```bash
rm -rf frontend/build
cd frontend && npm run build
cp -r frontend/build/* app/build/
cp -r frontend/build/static/* app/static/
npx playwright screenshot http://localhost:5001/dashboard?v=1
# Visual inspection (subjective, error-prone)
```
⏱️ **Time**: 3-5 minutes per iteration
🎯 **Accuracy**: Subjective, missed alignment issues

### ✅ Automated Process (Now)
```bash
/verify-ui #component "criteria"
```
⏱️ **Time**: ~2 minutes (automated)
🎯 **Accuracy**: Programmatic measurements, ±2px tolerance

---

## Pro Tips

💡 **Use specific measurements**: `"stroke 8px"` > `"looks thick"`

💡 **Test alignment objectively**: `"Y ±2px"` > `"looks aligned"`

💡 **Check multiple criteria**: Combine measurements, colors, visibility

💡 **Screenshot naming**: Auto-saved with timestamp for comparison

💡 **Console monitoring**: Automatically checks for JS errors

---

## Related Commands

- `/design-review` - Full brand compliance review
- `/summarize-chat` - Document session learnings
- `/troubleshoot` - Debug issues

---

## Quick Links

📖 **Full Documentation**: `docs/commands/VERIFY_UI_COMMAND.md`
📝 **Session Summary**: `docs/session_summaries/2025-12-13_injury_risk_dashboard_redesign_with_playwright.md`
⚙️ **Command File**: `.claude/commands/verify-ui.md`

---

**Created**: 2025-12-13
**Purpose**: Eliminate manual UI verification iterations
**Origin**: Dashboard redesign session learnings
