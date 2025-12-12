# Design Review Agent - User Guide
**Your Training Monkey Design Review System**

---

## Quick Start

### Prerequisites

1. **Mock server running:**
   ```bash
   scripts\start_mock_server.bat
   ```
   Server should be accessible at: `http://localhost:5001`

2. **Playwright MCP configured** (one-time setup - see [MCP Setup](#mcp-setup) below)

3. **Changes to review** (uncommitted changes or compare branches)

### Run a Design Review

**Option 1: Slash Command (Recommended)**
```
/design-review
```

**Option 2: Agent Invocation**
```
@agent-design-review Review the dashboard for brand compliance
```

**Option 3: Manual with Playwright**
```
Navigate to http://localhost:5001/dashboard
Take a full page screenshot at 1440px width
Check the console for errors
```

---

## When to Use Design Review

### ✅ Always Review

- **Before committing** UI/UX changes
- **After implementing** brand updates (colors, typography, buttons)
- **When adding** new pages or major features
- **Before deployment** of visual changes

### ⚠️ Consider Reviewing

- Layout or spacing adjustments
- New form elements
- Card or component styling changes
- Text content updates (voice/tone check)

### ❌ Skip Review

- Backend-only changes (no visual impact)
- Database migrations
- Configuration updates
- Documentation changes

---

## How It Works

### The Review Process

The design review agent follows a **7-phase methodology**:

```
Phase 0: Preparation
  ├─ Analyze git diff
  ├─ Set up Playwright browser
  └─ Navigate to localhost:5001

Phase 1: Interaction & User Flow
  ├─ Test primary workflows
  ├─ Verify interactive states (hover, active, disabled)
  └─ Check performance and responsiveness

Phase 2: Responsiveness Testing
  ├─ Desktop (1440px) - screenshot
  ├─ Tablet (768px) - layout check
  └─ Mobile (375px) - touch optimization

Phase 3: Visual Polish (Brand Compliance)
  ├─ Color palette verification
  ├─ Typography hierarchy
  ├─ Y, T, M sage green emphasis
  └─ Max 1 orange CTA per page

Phase 4: Accessibility (WCAG 2.1 AA)
  ├─ Keyboard navigation
  ├─ Focus states
  ├─ Color contrast (4.5:1)
  └─ Semantic HTML

Phase 5: Robustness Testing
  ├─ Form validation
  ├─ Error states
  ├─ Empty states
  └─ Content overflow

Phase 6: Code Health
  ├─ Component reuse
  ├─ CSS variable usage
  └─ Pattern consistency

Phase 7: Content & Console
  ├─ Text clarity and grammar
  ├─ Voice/tone match
  └─ Browser console errors
```

### Output Format

The agent provides a **categorized report**:

```markdown
### Design Review Summary
[Overall assessment with positives first]

### Brand Compliance
- Colors: PASS ✓ / ISSUES ⚠️
- Typography: PASS ✓ / ISSUES ⚠️
- Voice: PASS ✓ / ISSUES ⚠️

### Findings

#### [Blocker] - Fix Before Merging
- Critical accessibility failure
- Complete brand violation
- Broken functionality

#### [High-Priority] - Should Fix
- Significant visual inconsistency
- Accessibility issues
- Missing responsive breakpoints

#### [Medium-Priority] - Improvements
- Polish opportunities
- UX enhancements
- Future considerations

#### [Nitpick] - Optional
- Nit: Minor spacing inconsistency
- Nit: Could improve hover state

### Screenshots
[Desktop / Tablet / Mobile screenshots]
```

---

## Brand Compliance Checklist

The agent automatically checks these **Your Training Monkey** brand rules:

### Colors

| Element | Required Color | Violation Level |
|---------|---------------|-----------------|
| Navigation gradient | `#E6F0FF → #7D9CB8 → #1B2E4B` | High |
| Max 1 orange CTA | `#FF5722` (ONE per page) | **Blocker** |
| Success states | `#16A34A` green | Medium |
| Interactive elements | `#667EEA → #764BA2` purple | Medium |
| Y, T, M emphasis | `#6B8F7F` sage green | High |

### Typography

| Rule | Requirement | Violation Level |
|------|-------------|-----------------|
| Body text alignment | LEFT-ALIGNED | High |
| Max text width | 75 characters | Medium |
| Line height | 1.6 for body text | Low |
| Font sizes | Follow scale (16px body, 32px H1) | Medium |

### UI Elements

| Rule | Requirement | Violation Level |
|------|-------------|-----------------|
| Emoji icons | NO emoji in UI | **High** |
| Center-aligned paragraphs | NO centered body text | High |
| Hard-coded colors | Use CSS variables | Medium |
| Focus states | Visible on all interactive | **Blocker** |

### Accessibility

| Rule | Standard | Violation Level |
|------|----------|-----------------|
| Color contrast | 4.5:1 minimum | **Blocker** |
| Keyboard navigation | Full tab support | **Blocker** |
| Form labels | All inputs labeled | High |
| Alt text | All images | High |

---

## Understanding the Triage Matrix

### [Blocker] - Must Fix Immediately

**Criteria:**
- Accessibility failures (WCAG violations)
- Critical brand violations (2+ orange CTAs)
- Broken functionality
- Security issues

**Action:** Fix before committing/merging

**Examples:**
- Color contrast below 4.5:1
- No keyboard focus visible
- Multiple orange CTA buttons on same page
- Console errors preventing functionality

### [High-Priority] - Fix Before Merge

**Criteria:**
- Significant brand inconsistencies
- Major UX issues
- Important accessibility gaps
- Responsive layout broken

**Action:** Address in current PR/branch

**Examples:**
- Body text centered instead of left-aligned
- Missing Y, T, M sage green emphasis
- Mobile layout broken at 375px
- Form missing error states

### [Medium-Priority] - Improvements

**Criteria:**
- Polish opportunities
- Minor brand inconsistencies
- UX enhancements
- Code quality improvements

**Action:** Can address in follow-up PR

**Examples:**
- Spacing could be more consistent
- Consider adding loading state animation
- Could improve empty state messaging
- Opportunity to extract reusable component

### [Nitpick] - Optional

**Criteria:**
- Very minor aesthetic details
- Personal preferences
- "Would be nice" improvements

**Action:** Optional, at your discretion

**Examples:**
- Nit: Button padding could be 1px smaller
- Nit: Consider slightly darker hover state
- Nit: Wording could be more concise

---

## Common Issues and Fixes

### Issue: Multiple Orange CTAs

**Detected:** Multiple buttons with `#FF5722` on same page

**Fix:**
```css
/* Change secondary CTA to purple gradient */
background: linear-gradient(135deg, #667eea, #764ba2);
```

**Why:** Brand rule allows max 1 orange CTA per page for visual hierarchy

---

### Issue: Center-Aligned Paragraphs

**Detected:** `text-align: center` on body text

**Fix:**
```css
p, .body-text {
  text-align: left;
  max-width: 75ch;
}
```

**Why:** Left alignment improves readability per brand guidelines

---

### Issue: Missing Y, T, M Emphasis

**Detected:** Brand name without sage green emphasis

**Fix:**
```html
<span style="
  font-weight: 900;
  letter-spacing: 0.15em;
  text-transform: uppercase;
">
  <span style="font-size: 1.17em; color: #6B8F7F;">Y</span>our
  <span style="font-size: 1.17em; color: #6B8F7F;">T</span>raining
  <span style="font-size: 1.17em; color: #6B8F7F;">M</span>onkey
</span>
```

**Why:** Brand identity requires Y, T, M letter emphasis

---

### Issue: Emoji Icons in UI

**Detected:** ✅ ⚠️ 🎉 emoji in user-facing text

**Fix:**
```html
<!-- Before -->
<button>✅ Success</button>

<!-- After -->
<button class="ytm-badge ytm-badge-success">Success</button>
```

**Why:** Brand guidelines prohibit emoji in UI (text labels only)

---

### Issue: Hard-Coded Colors

**Detected:** `color: #FF5722` instead of CSS variable

**Fix:**
```css
/* Before */
.button {
  background: #FF5722;
}

/* After */
.button {
  background: var(--ytm-action-orange);
}
```

**Why:** CSS variables ensure consistency and easier updates

---

### Issue: Low Color Contrast

**Detected:** Text contrast below 4.5:1

**Fix:**
```css
/* Before: #64748B on #F8FAFC (2.8:1) */
.help-text {
  color: #64748B;
}

/* After: Use darker text */
.help-text {
  color: #475569; /* Meets 4.5:1 */
}
```

**Why:** WCAG AA requires 4.5:1 for accessibility

---

## MCP Setup

### One-Time Installation

**Windows:**
```bash
claude mcp add --transport stdio playwright -- cmd /c npx -y @playwright/mcp@latest
```

**Mac/Linux:**
```bash
claude mcp add --transport stdio playwright -- npx -y @playwright/mcp@latest
```

### Verify Installation

```
/mcp
```

Should show:
```
playwright: connected
Tools: 20+ browser automation tools
```

### Troubleshooting MCP

**Issue: "No MCP servers configured"**

Solution:
```bash
# Remove and re-add
claude mcp remove playwright
claude mcp add --transport stdio playwright -- cmd /c npx -y @playwright/mcp@latest

# Then restart Claude Code
```

**Issue: Connection closed on startup**

Solution:
- Ensure Node.js is installed: `node --version`
- Check npm is in PATH: `npm --version`
- Try with explicit path to npx

---

## Example Workflows

### Workflow 1: Before Committing UI Changes

```bash
# 1. Start mock server
scripts\start_mock_server.bat

# 2. In Claude Code, run review
/design-review

# 3. Review findings
# - Fix any [Blocker] issues immediately
# - Address [High-Priority] in current commit
# - Create tickets for [Medium-Priority]

# 4. Commit changes
git add .
git commit -m "Update dashboard layout

- Fixed color contrast on help text
- Removed emoji icons from success states
- Left-aligned body paragraphs
- Limited to 1 orange CTA per page"
```

### Workflow 2: Quick Visual Check During Development

```bash
# 1. Mock server running in background
scripts\start_mock_server.bat

# 2. Ask Claude directly
Navigate to http://localhost:5001/dashboard
Take a screenshot
Check console for errors

# 3. Quick visual inspection (no full report)
```

### Workflow 3: Comprehensive Pre-Deployment Review

```bash
# 1. Full design review across all pages
/design-review

# 2. Manual testing
npm run test:screenshots

# 3. Review generated screenshots
ls frontend/tests/screenshots/output/

# 4. Address all findings before deployment
```

---

## Tips for Better Reviews

### Before Running Review

✅ **DO:**
- Start mock server first
- Commit unrelated changes (isolate UI changes)
- Test the page manually once
- Read brand guidelines if unsure

❌ **DON'T:**
- Run review on large mixed commits
- Skip testing locally first
- Ignore previous review findings
- Rush through fixes

### Interpreting Results

**Trust the Agent, But Verify:**
- Screenshots show actual rendering
- Console errors are real issues
- Contrast ratios are measured
- But context matters - ask if unsure

**Prioritize Systematically:**
1. Fix all [Blocker] first
2. Address [High-Priority] before merge
3. Track [Medium-Priority] for later
4. Consider [Nitpick] if quick

**Ask for Clarification:**
```
Why is this a blocker?
Can you show me the contrast ratio calculation?
What's the brand guideline for this?
```

---

## Reference Documents

### Brand Guidelines
- **Complete framework:** `docs/branding/YOUR_TRAINING_MONKEY_BRAND_FRAMEWORK.md`
- **Quick reference:** `docs/branding/QUICK_REFERENCE_STYLE_GUIDE.md`
- **Design principles:** `.claude/context/design-principles.md`

### Design Review System
- **Agent config:** `.claude/agents/design-review.md`
- **Slash command:** `.claude/commands/design-review.md`
- **Methodology:** `frontend/DesignReview/design-review-agent.md`

### Project Guidelines
- **Main guidelines:** `.claude/CLAUDE.md`
- **Visual development:** See "Visual Development" section in CLAUDE.md

---

## FAQ

### Q: Do I need to run `/design-review` for every change?

**A:** No. Use it for:
- Significant UI changes
- New pages/features
- Before deployment
- When unsure about brand compliance

Skip for backend-only changes or minor text edits.

---

### Q: What if I disagree with a finding?

**A:** The agent enforces documented brand rules, but context matters:
1. Check the brand guidelines to verify
2. If guidelines are wrong, update them first
3. If special case, document why in commit message
4. Ask for clarification if unclear

---

### Q: Can I use this without the mock server?

**A:** No. The agent needs to:
- Navigate actual pages
- Take screenshots
- Test interactions
- Check console errors

The mock server provides consistent, fast test data.

---

### Q: How long does a review take?

**A:** Typical timing:
- Quick check: 30 seconds
- Single page review: 1-2 minutes
- Full `/design-review`: 3-5 minutes

Depends on number of pages changed.

---

### Q: What if MCP Playwright isn't working?

**A:** Fallback options:
1. Use standalone Playwright tests: `npm run test:screenshots`
2. Manual review with brand checklist
3. Ask team member to review
4. Fix MCP setup (see [MCP Setup](#mcp-setup))

---

## Support

### Getting Help

1. **Check this guide** - Most common issues covered
2. **Read brand guidelines** - For specific brand questions
3. **Review examples** - See `frontend/DesignReview/` folder
4. **Ask in Claude Code** - Clarify any findings

### Reporting Issues

If the design review agent has bugs or improvements:
1. Document the issue with screenshots
2. Note what was expected vs actual
3. Share with team or file GitHub issue

---

**Last Updated:** December 11, 2025
**Version:** 1.0
**Maintained By:** Your Training Monkey Development Team
