---
allowed-tools: Grep, Read, Edit, Write, TodoWrite, mcp__playwright__browser_close, mcp__playwright__browser_resize, mcp__playwright__browser_console_messages, mcp__playwright__browser_handle_dialog, mcp__playwright__browser_evaluate, mcp__playwright__browser_press_key, mcp__playwright__browser_type, mcp__playwright__browser_navigate, mcp__playwright__browser_navigate_back, mcp__playwright__browser_navigate_forward, mcp__playwright__browser_network_requests, mcp__playwright__browser_take_screenshot, mcp__playwright__browser_snapshot, mcp__playwright__browser_click, mcp__playwright__browser_drag, mcp__playwright__browser_hover, mcp__playwright__browser_select_option, mcp__playwright__browser_tab_list, mcp__playwright__browser_tab_new, mcp__playwright__browser_tab_select, mcp__playwright__browser_tab_close, mcp__playwright__browser_wait_for, Bash, Glob
description: Run a comprehensive design review on current branch changes
---

You are an elite design review specialist for **Your Training Monkey**. Conduct a comprehensive design review of the pending changes.

## Prerequisites Check

**IMPORTANT:** Before starting, verify the mock server is running:
- URL: `http://localhost:5001`
- Start command: `scripts\start_mock_server.bat`

If the server is not accessible, inform the user and stop.

## Current Branch Status

```
$!git status
```

## Files Modified (Frontend Focus)

```
$!git diff --name-only HEAD -- "*.tsx" "*.ts" "*.css" "*.html" "frontend/*" "app/templates/*" "app/static/*"
```

## Recent Commits

```
$!git log -5 --oneline
```

## Diff Content (Frontend Changes)

```
$!git diff HEAD -- "*.tsx" "*.ts" "*.css" "frontend/*"
```

---

## Your Task

Using the `@agent-design-review` agent, conduct a comprehensive design review:

1. **Navigate** to `http://localhost:5001/dashboard` using Playwright
2. **Test** all pages affected by the changes (Dashboard, Activities, Journal, Coach, Settings)
3. **Capture** screenshots at desktop (1440px), tablet (768px), and mobile (375px)
4. **Verify** brand compliance against `docs/branding/QUICK_REFERENCE_STYLE_GUIDE.md`
5. **Check** for console errors
6. **Report** findings using the triage matrix (Blocker/High/Medium/Nitpick)

## Brand Compliance Checklist

**Colors:**
- [ ] Navigation gradient: `#E6F0FF → #7D9CB8 → #1B2E4B`
- [ ] Max 1 orange CTA (`#FF5722`) per page
- [ ] Success states use green (`#16A34A`)
- [ ] Interactive elements use purple gradient

**Typography:**
- [ ] Body text left-aligned, max-width: 75ch
- [ ] Y, T, M letters emphasized in sage green (`#6B8F7F`)
- [ ] No center-aligned paragraphs

**UI Elements:**
- [ ] No emoji icons in user-facing UI
- [ ] Consistent card styling (12px border-radius)
- [ ] Form inputs have focus states

**Accessibility:**
- [ ] Color contrast meets 4.5:1
- [ ] Focus states visible
- [ ] Keyboard navigation works

---

## Output Format

Provide a complete markdown design review report including:
1. Summary with overall assessment
2. Brand compliance status
3. Categorized findings (Blocker → Nitpick)
4. Screenshots for each viewport
5. Recommendations
