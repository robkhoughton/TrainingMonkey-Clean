---
allowed-tools: Bash, Read, Grep, Glob, mcp__playwright__browser_close, mcp__playwright__browser_resize, mcp__playwright__browser_console_messages, mcp__playwright__browser_handle_dialog, mcp__playwright__browser_evaluate, mcp__playwright__browser_press_key, mcp__playwright__browser_type, mcp__playwright__browser_navigate, mcp__playwright__browser_navigate_back, mcp__playwright__browser_navigate_forward, mcp__playwright__browser_network_requests, mcp__playwright__browser_take_screenshot, mcp__playwright__browser_snapshot, mcp__playwright__browser_click, mcp__playwright__browser_drag, mcp__playwright__browser_hover, mcp__playwright__browser_select_option, mcp__playwright__browser_tab_list, mcp__playwright__browser_tab_new, mcp__playwright__browser_tab_select, mcp__playwright__browser_tab_close, mcp__playwright__browser_wait_for
description: Rebuild, deploy, and verify UI component with Playwright
---

You are a UI verification specialist for **Your Training Monkey**. Automate the rebuild-deploy-screenshot-verify cycle for frontend components.

## Usage

```
/verify-ui <component-id> <checklist-items>
```

**Parameters:**
- `component-id`: CSS selector or element ID (e.g., `#at-a-glance-meters`, `.activity-card`)
- `checklist-items`: Comma-separated verification criteria (e.g., "stroke widths consistent, vertical alignment, tick marks visible")

## Prerequisites Check

**IMPORTANT:** Verify the mock server is running:
- URL: `http://localhost:5001`
- Start command: `scripts\start_mock_server.bat`

If the server is not accessible, inform the user and stop.

## Workflow

Execute the following steps in order:

### 1. Clean Build
```bash
rm -rf frontend/build
```

### 2. Rebuild React App
```bash
cd frontend && npm run build
```

### 3. Deploy to Mock Server
```bash
cp -r frontend/build/* app/build/
cp -r frontend/build/static/* app/static/
```

### 4. Generate Cache-Busting Parameter
Create a unique version parameter for the URL (e.g., `?v=timestamp` or incrementing number).

### 5. Navigate with Playwright
Navigate to `http://localhost:5001/dashboard?v={cache_buster}` using Playwright MCP.

### 6. Take Focused Screenshot
- Use `mcp__playwright__browser_take_screenshot` to capture the specified component
- Save screenshot with descriptive name: `{component_name}_verification_{timestamp}.png`

### 7. Measure & Analyze
Perform programmatic verification:

**Alignment Verification:**
- Measure vertical/horizontal positions of key elements
- Report exact Y/X coordinates
- Verify alignment within ±2px tolerance

**Dimension Verification:**
- Measure stroke widths of SVG paths
- Measure element heights/widths
- Compare against expected values

**Color Verification:**
- Extract color values from elements
- Verify against brand guidelines
- Check opacity values

**Visibility Verification:**
- Confirm elements are visible (not clipped)
- Check z-index layering
- Verify no overlaps

### 8. Check Console Errors
Run `mcp__playwright__browser_console_messages` to detect any JavaScript errors.

### 9. Verification Report
Generate a detailed report with:

#### Visual Consistency
- [ ] Stroke widths: [Measured values]
- [ ] Vertical alignment: [Y coordinates with tolerance check]
- [ ] Horizontal alignment: [X coordinates with tolerance check]
- [ ] Colors: [Extracted hex values vs expected]
- [ ] Typography: [Font sizes, weights, colors]
- [ ] Spacing: [Margins, padding, gaps]

#### Component-Specific Checks
- [ ] Custom criteria from checklist-items parameter

#### Console Status
- [ ] JavaScript errors: [None | List errors]

#### Screenshots
- [Link to saved screenshot]

#### Summary
- ✅ **PASS**: All checks passed
- ⚠️ **ISSUES**: List specific problems found
- ❌ **FAIL**: Critical issues requiring fixes

## Example Usage

### Example 1: Verify Injury Risk Card
```
/verify-ui #at-a-glance-meters "stroke widths 8px, gauges vertically aligned, tick marks light colored, carbon fiber visible"
```

### Example 2: Verify Activity Card
```
/verify-ui .activity-card "proper spacing, colors match brand, no console errors"
```

## Best Practices

**DO:**
- Use cache-busting on every verification
- Request pixel measurements for alignment
- Provide explicit verification criteria
- Take multiple screenshots if needed (full, zoomed)
- Compare before/after when relevant

**DON'T:**
- Skip rebuild/deploy steps
- Assume "verified" without measurements
- Accept vague visual inspection
- Trust screenshots alone for alignment

## Verification Prompt Template

When analyzing the screenshot, use this systematic approach:

```
Navigate to http://localhost:5001/dashboard?v={VERSION}

1. Screenshot element: {COMPONENT_ID}

2. Measure and report:
   - Vertical positions: Y coordinates of [list elements]
   - Horizontal positions: X coordinates of [list elements]
   - Dimensions: Width/height of [list elements]
   - Stroke widths: SVG path stroke-width values
   - Colors: Background, foreground, accent colors (hex codes)

3. Verify alignment:
   - All [elements] should have same Y coordinate (±2px tolerance)
   - All [elements] should have same X coordinate (±2px tolerance)

4. Check visibility:
   - No elements clipped or cut off
   - All text readable
   - No overlapping elements

5. Verify checklist items:
   {CHECKLIST_ITEMS}

6. Console errors:
   - Run browser_console_messages
   - Report any errors/warnings

7. Save screenshot as: {COMPONENT}_verification_{TIMESTAMP}.png
```

## Output Format

Provide a complete verification report including:
1. Build & deploy confirmation
2. Screenshot(s) with measurements overlaid/annotated
3. Measurement data (coordinates, dimensions, colors)
4. Checklist verification results
5. Console error status
6. Pass/Fail/Issues summary
7. Recommendations for fixes (if issues found)

---

**Note**: This command combines the manual steps from the dashboard redesign session into a single automated workflow for faster UI iteration.
