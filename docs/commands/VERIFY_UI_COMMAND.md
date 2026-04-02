# `/verify-ui` Command Documentation

**Command Type**: Slash Command
**Purpose**: Automated UI verification workflow for frontend component testing
**Location**: `.claude/commands/verify-ui.md`
**Status**: Implemented (awaiting CLI registration)

---

## Overview

The `/verify-ui` command automates the complete rebuild-deploy-screenshot-verify cycle for frontend React components. It was designed to eliminate the manual iteration process discovered during the Injury Risk dashboard redesign session (December 2025).

### What It Does

Combines five manual steps into a single automated workflow:

1. **Clean Build** - Removes old build artifacts
2. **Rebuild** - Compiles React application
3. **Deploy** - Copies assets to mock server
4. **Screenshot** - Captures component with Playwright
5. **Verify** - Programmatically checks alignment, dimensions, colors

### Why It Exists

During the dashboard redesign (5 iterations), each cycle required:
- Manual rebuild commands
- Manual file copying
- Manual Playwright navigation
- Visual inspection (prone to missing pixel-level issues)

This command automates the entire process and adds **programmatic measurements** for objective verification.

---

## Usage

### Basic Syntax

```bash
/verify-ui <component-id> <checklist-items>
```

### Parameters

#### `component-id` (required)
CSS selector or element ID of the component to verify.

**Examples**:
- `#at-a-glance-meters` - ID selector
- `.activity-card` - Class selector
- `div[data-testid="profile-header"]` - Attribute selector

#### `checklist-items` (required)
Comma-separated verification criteria specific to your component.

**Examples**:
- `"stroke widths 8px, gauges aligned, tick marks visible"`
- `"proper spacing, colors match brand, no console errors"`
- `"responsive layout, mobile-friendly, no overlaps"`

---

## Examples

### Example 1: Verify Injury Risk Card

```bash
/verify-ui #at-a-glance-meters "stroke widths 8px, gauges vertically aligned, tick marks light colored, carbon fiber visible"
```

**What it checks**:
- All gauge stroke widths are 8px
- ACWR and Divergence gauges at same Y coordinate
- Tick marks use light color (#e0e0e0)
- Carbon fiber background texture is visible

### Example 2: Verify Activity Card

```bash
/verify-ui .activity-card "proper spacing, colors match brand, no console errors"
```

**What it checks**:
- Consistent margin/padding values
- Colors match brand guidelines
- No JavaScript errors in console

### Example 3: Verify Navigation Header

```bash
/verify-ui header.main-nav "gradient correct, logo positioned, responsive breakpoints"
```

**What it checks**:
- Navigation gradient matches specification
- Logo alignment and spacing
- Layout adapts at mobile breakpoints

---

## Workflow Details

### Step-by-Step Process

#### 1. Prerequisites Check
```bash
curl http://localhost:5001
```
Verifies mock server is running. If not, command stops and instructs user to start it:
```bash
scripts\start_mock_server.bat
```

#### 2. Clean Build
```bash
rm -rf frontend/build
```
Removes old build directory to ensure fresh compilation.

#### 3. Rebuild React App
```bash
cd frontend && npm run build
```
Compiles optimized production build of React application.

#### 4. Deploy to Mock Server
```bash
cp -r frontend/build/* app/build/
cp -r frontend/build/static/* app/static/
```
Copies build artifacts to both locations for mock server access.

#### 5. Generate Cache-Busting Parameter
Creates unique version parameter (timestamp or incrementing number):
```
?v=1734123456
```
Ensures browser doesn't use cached version.

#### 6. Navigate with Playwright
```
http://localhost:5001/dashboard?v={cache_buster}
```
Opens dashboard in Playwright-controlled browser.

#### 7. Capture Screenshot
Uses `mcp__playwright__browser_take_screenshot` to capture:
- Focused element screenshot (not full page)
- Saved with descriptive name: `{component}_verification_{timestamp}.png`

#### 8. Programmatic Measurements

**Alignment Verification**:
```javascript
// Measure Y coordinates of gauge tops
const gaugeY = element.getBoundingClientRect().top;
// Verify within ±2px tolerance
```

**Dimension Verification**:
```javascript
// Extract SVG stroke widths
const strokeWidth = path.getAttribute('stroke-width');
```

**Color Verification**:
```javascript
// Get computed colors
const color = window.getComputedStyle(element).color;
```

**Visibility Verification**:
```javascript
// Check if element is clipped
const isClipped = element.scrollHeight > element.clientHeight;
```

#### 9. Console Error Check
```javascript
mcp__playwright__browser_console_messages
```
Captures any JavaScript errors or warnings.

#### 10. Generate Report
Produces detailed verification report (see Output Format below).

---

## Output Format

### Verification Report Structure

```markdown
## UI Verification Report

**Component**: #at-a-glance-meters
**Timestamp**: 2025-12-13 18:29:41
**Build**: Fresh rebuild from source
**URL**: http://localhost:5001/dashboard?v=1765679381

---

### ✅ Build & Deploy Status
- Clean build: ✓ Completed
- React build: ✓ Successful (205.65 kB)
- Deployment: ✓ Copied successfully
- Server status: ✓ Running (HTTP 200)

---

### 📸 Visual Verification

#### Checklist Verification Results

| Criteria | Status | Observation |
|----------|--------|-------------|
| Stroke widths 8px | ✅ PASS | Measured: 8px on all paths |
| Gauges aligned | ✅ PASS | Y coords: 156px (tolerance: ±2px) |
| Tick marks light | ✅ PASS | Color: #e0e0e0 (expected) |
| Carbon fiber | ✅ PASS | Background pattern visible |

---

### 🎨 Design Consistency

**Measured Values**:
- Stroke widths: [8, 8, 8] px
- Gauge positions: Y=156px, Y=156px (aligned ✓)
- Tick mark colors: #e0e0e0, #e0e0e0
- Background: repeating-linear-gradient(...)

---

### 🖥️ Console Status

✅ No JavaScript errors
✅ No console warnings

---

### 📊 Summary

**Overall Status**: ✅ PASS - All criteria met

Components verified: 3 (ACWR, Divergence, Risk Level)
Issues found: 0
Warnings: 0

---

### 📷 Screenshots

- Full dashboard: injury_risk_verification_1765679381.png
- Focused component: injury_risk_card_focused_1765679381.png
```

---

## Best Practices

### ✅ DO

**Use Cache-Busting Every Time**
```bash
# Good - forces fresh page load
/verify-ui #component "criteria"
# (Command automatically adds ?v=timestamp)
```

**Request Pixel Measurements for Alignment**
```bash
# Good - specific, measurable
/verify-ui #nav "links aligned within 2px, logo centered"
```

**Provide Explicit Verification Criteria**
```bash
# Good - clear expectations
/verify-ui #card "stroke 8px, colors #2ecc71, spacing 1rem"

# Bad - vague
/verify-ui #card "looks good"
```

**Take Multiple Screenshots if Needed**
```bash
# Full page context
/verify-ui body "overall layout"
# Focused component
/verify-ui #specific-card "detailed measurements"
```

**Compare Before/After When Relevant**
```bash
# Before changes
/verify-ui #component "baseline measurements"
# Make changes
# After changes
/verify-ui #component "same criteria as baseline"
```

### ❌ DON'T

**Don't Skip Rebuild/Deploy Steps**
```bash
# Bad - using old cached build
# (Command always rebuilds, but don't manually skip steps)
```

**Don't Assume "Verified" Without Measurements**
```bash
# Bad
/verify-ui #gauge "looks aligned"

# Good
/verify-ui #gauge "Y coordinates within ±2px tolerance"
```

**Don't Accept Vague Screenshot Descriptions**
```bash
# Bad checklist
"everything looks fine"

# Good checklist
"stroke widths consistent, vertical alignment, proper colors"
```

**Don't Trust Screenshots Alone for Alignment**
```bash
# Bad - visual inspection only
"gauges look aligned"

# Good - programmatic verification
"gauges Y=156px ±2px, measured programmatically"
```

---

## Comparison: Manual vs Automated

### Manual Iteration Process (Before)

```bash
# 1. Clean
rm -rf frontend/build

# 2. Build
cd frontend && npm run build

# 3. Deploy
cp -r frontend/build/* app/build/
cp -r frontend/build/static/* app/static/

# 4. Navigate
# Open browser manually or use Playwright
npx playwright screenshot http://localhost:5001/dashboard?v=1

# 5. Verify
# Visual inspection - prone to errors
# No measurements - subjective
```

**Time**: ~3-5 minutes per iteration
**Iterations needed**: 5 (for dashboard redesign)
**Total time**: 15-25 minutes
**Accuracy**: Subjective, missed vertical alignment issues

### Automated Process (With /verify-ui)

```bash
/verify-ui #at-a-glance-meters "stroke 8px, aligned, ticks light, carbon fiber"
```

**Time**: ~2 minutes (automated)
**Iterations needed**: Fewer (objective measurements catch issues)
**Accuracy**: Programmatic measurements, ±2px tolerance
**Benefits**: Reproducible, documented, consistent

---

## Troubleshooting

### Issue: "Mock server not running"

**Error**:
```
Mock server not accessible at http://localhost:5001
```

**Solution**:
```bash
scripts\start_mock_server.bat
```

**Verification**:
```bash
curl http://localhost:5001
# Should return HTTP 200
```

---

### Issue: "Component not found"

**Error**:
```
Element #at-a-glance-meters not found
```

**Solution**:
1. Verify component ID exists in rendered HTML
2. Check if component is conditionally rendered
3. Wait for component to load (add delay if needed)

**Debug**:
```bash
# Navigate to page manually
# Open browser inspector
# Verify element ID in DOM
```

---

### Issue: "Screenshot shows old design"

**Error**:
Captured screenshot doesn't reflect recent code changes.

**Solution**:
1. Verify build completed successfully
2. Check deployment copied latest files
3. Ensure cache-busting parameter is unique
4. Clear browser cache if needed

**Manual verification**:
```bash
# Check file timestamps
ls -la app/static/js/main.*.js

# Verify latest build hash in index.html
cat app/build/index.html | grep "main.*js"
```

---

### Issue: "Build warnings"

**Warning**:
```
[eslint]
src\Component.tsx
  Line 42:9: 'unusedVar' is assigned a value but never used
```

**Impact**: Non-blocking - build completes successfully

**Solution** (optional):
- Remove unused variables
- Add `// eslint-disable-next-line` if intentional
- Fix linting issues before final deployment

---

### Issue: "Console errors detected"

**Error**:
```
Console errors found:
- TypeError: Cannot read property 'x' of undefined
```

**Solution**:
1. Review error message and stack trace
2. Fix underlying JavaScript issue
3. Rebuild and re-verify
4. Ensure component loads without errors

---

## Advanced Usage

### Custom Verification Scripts

Create specialized verification scripts for complex measurements:

**File**: `scripts/verify_gauge_alignment.js`
```javascript
const { chromium } = require('playwright');

async function verifyGaugeAlignment() {
  const browser = await chromium.launch();
  const page = await browser.newPage();

  await page.goto('http://localhost:5001/dashboard?v=' + Date.now());

  const measurements = await page.evaluate(() => {
    const gauges = document.querySelectorAll('#at-a-glance-meters svg');
    return Array.from(gauges).map(g => ({
      y: g.getBoundingClientRect().top,
      height: g.getBoundingClientRect().height
    }));
  });

  // Verify alignment within tolerance
  const tolerance = 2; // pixels
  const allAligned = measurements.every((m, i) =>
    i === 0 || Math.abs(m.y - measurements[0].y) <= tolerance
  );

  console.log('Alignment:', allAligned ? 'PASS' : 'FAIL');
  console.log('Measurements:', measurements);

  await browser.close();
}

verifyGaugeAlignment();
```

**Usage**:
```bash
node scripts/verify_gauge_alignment.js
```

---

### Integration with CI/CD

Add UI verification to automated testing pipeline:

**File**: `.github/workflows/ui-verify.yml`
```yaml
name: UI Verification

on: [pull_request]

jobs:
  verify-ui:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Start mock server
        run: npm run start:mock &
      - name: Run UI verification
        run: |
          claude /verify-ui #at-a-glance-meters "stroke 8px, aligned"
      - name: Upload screenshots
        uses: actions/upload-artifact@v2
        with:
          name: ui-verification-screenshots
          path: "*.png"
```

---

## Related Documentation

- **Session Summary**: `docs/session_summaries/2025-12-13_injury_risk_dashboard_redesign_with_playwright.md`
- **Design Review**: `.claude/commands/design-review.md`
- **Mock Server Guide**: `docs/LOCAL_MOCK_DEVELOPMENT.md`
- **Brand Guidelines**: `docs/branding/YOUR_TRAINING_MONKEY_BRAND_FRAMEWORK.md`

---

## Command Evolution

### Version History

**v1.0** (2025-12-13)
- Initial implementation
- Basic rebuild-deploy-screenshot workflow
- Programmatic measurement verification
- Console error checking
- Comprehensive reporting

### Planned Enhancements

**Future Features**:
1. **Diff Comparison** - Compare before/after screenshots with image diff
2. **Responsive Testing** - Auto-verify at multiple viewport sizes (desktop/tablet/mobile)
3. **Accessibility Checks** - Verify WCAG contrast ratios, keyboard navigation
4. **Performance Metrics** - Measure component render time, bundle size impact
5. **Visual Regression** - Baseline comparison to detect unintended changes

---

## Credits

**Created**: 2025-12-13
**Origin**: Dashboard redesign session learnings
**Contributors**: Claude Code assistant, User feedback
**Inspired by**: Playwright MCP integration, Iterative UI development best practices

---

## Support

**Questions or Issues?**
- Check troubleshooting section above
- Review session summary for context
- Consult `.claude/commands/verify-ui.md` for implementation details
- Reference Playwright MCP documentation

**Feature Requests?**
- Document use case and expected behavior
- Suggest enhancement in project issues
- Provide examples of desired workflow
