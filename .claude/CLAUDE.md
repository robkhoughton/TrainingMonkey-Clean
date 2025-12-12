# TrainingMonkey Project Guidelines

## Project Overview

TrainingMonkey is a training analytics platform for endurance athletes. It integrates with Strava to provide:
- Training load monitoring (ACWR/TRIMP metrics)
- AI-powered coaching recommendations
- Activity journaling and analysis
- Race goal planning

## Deployment Model

**Local Deployment** - This project is deployed from the local machine, not from GitHub/CI/CD.
- User runs deployment commands manually (e.g., `app/deploy_strava_simple.bat`)
- Assistant prepares code changes but NEVER runs deployment commands
- All testing happens locally before user initiates deployment
- Git is used for version control only, not deployment triggers

## Git Commit/Push Practices

**Commit Strategically** - Do not commit every minor edit.
- **Prompt before significant changes**: Ask user before starting major refactors or multi-file changes
- **Prompt after significant completions**: Suggest commit when a feature, fix, or logical unit of work is complete
- **Group related changes**: Multiple related edits should be one commit with a descriptive message
- **Skip trivial changes**: Minor formatting, typo fixes, or exploratory changes don't need immediate commits
- **User controls timing**: Never auto-commit; always ask or suggest

## Architecture

```
TrainingMonkey/
├── app/                    # Flask backend (Python)
│   ├── strava_app.py       # Main Flask application
│   ├── db_utils.py         # Database operations
│   ├── db_credentials_loader.py  # Secure credential loading
│   ├── templates/          # Jinja2 templates
│   └── static/             # Built React assets (copied from frontend)
├── frontend/               # React frontend (TypeScript)
│   └── src/                # React components
├── scripts/                # Utility scripts
│   └── migrations/         # Database migration scripts
└── .claude/rules/          # Modular coding standards
```

## Critical Rules (Read First)

1. **PostgreSQL ONLY** - Use `%s` placeholders, `SERIAL PRIMARY KEY`, `NOW()` - never SQLite syntax
2. **Secure Credentials** - Always use `db_credentials_loader.py`, never hardcode DATABASE_URL
3. **Dockerfile Updates** - New Python files MUST be added to `app/Dockerfile.strava`
4. **Frontend Deployment** - After React changes, rebuild and copy to `app/static/`
5. **No Deployment Commands** - Assistant prepares code; user handles all deployment
6. **Root Cause Solutions** - Always address root causes, not symptoms. Investigate underlying problems before implementing fixes. Avoid workarounds or patches that mask the real issue.

## Quick Reference

| Task | How To |
|------|--------|
| Database query | `db_utils.execute_query("SELECT * FROM x WHERE id = %s", (id,), fetch=True)` |
| Load credentials | `from db_credentials_loader import set_database_url; set_database_url()` |
| Run migration | Create script in `scripts/migrations/`, use `db_credentials_loader` |
| Frontend build | `cd frontend && npm run build` then copy to `app/static/` |

## Problem-Solving Philosophy

**Address Root Causes, Not Symptoms**
- When fixing bugs or issues, always investigate the underlying root cause
- Use the "5 Whys" technique: ask "why" multiple times to get to the fundamental problem
- Avoid workarounds, try-catch blocks that hide errors, or conditional logic that masks issues
- Examples of patches to avoid:
  - Adding null checks without fixing why nulls occur
  - Catching exceptions without addressing why they're thrown
  - Adding conditional logic to work around incorrect data flow
  - Implementing client-side fixes for server-side problems
- Instead, fix the source: correct data flow, fix validation, address architectural issues

## Modular Rules

Detailed standards are organized in `.claude/rules/`:
- `database.md` - PostgreSQL syntax, queries, migrations
- `deployment.md` - Dockerfile, frontend build, deployment process
- `frontend.md` - React/TypeScript patterns, performance monitoring
- `code-quality.md` - General standards, error handling, testing

## Key Files

- **Database**: `app/db_utils.py`, `app/db_credentials_loader.py`
- **Main App**: `app/strava_app.py`
- **Frontend Entry**: `frontend/src/App.tsx`
- **Dockerfile**: `app/Dockerfile.strava`
- **Build Script**: `scripts/build_and_copy.bat`

## Visual Development

### Design Principles
- Comprehensive brand framework: `docs/branding/YOUR_TRAINING_MONKEY_BRAND_FRAMEWORK.md`
- Quick reference style guide: `docs/branding/QUICK_REFERENCE_STYLE_GUIDE.md`
- Design principles summary: `.claude/context/design-principles.md`
- When making visual (front-end, UI/UX) changes, always refer to these files for guidance

### Quick Visual Check
IMMEDIATELY after implementing any front-end change:
1. **Start mock server**: `scripts\start_mock_server.bat` (localhost:5001)
2. **Navigate to affected pages** - Use Playwright MCP to visit each changed view
3. **Verify design compliance** - Compare against style guide
4. **Capture evidence** - Take full page screenshot at desktop viewport (1440px)
5. **Check for errors** - Run `mcp__playwright__browser_console_messages`

### Brand Compliance Quick Check
- [ ] Colors use CSS variables (not hard-coded hex)
- [ ] Body text left-aligned, max-width: 75ch
- [ ] Y, T, M letters emphasized in sage green (#6B8F7F)
- [ ] No emoji icons in user-facing UI
- [ ] Max 1 orange CTA (#FF5722) per page
- [ ] Contrast meets WCAG 4.5:1

### Comprehensive Design Review
Invoke `/design-review` slash command or `@agent-design-review` subagent for thorough design validation when:
- Completing significant UI/UX features
- Before finalizing PRs with visual changes
- Needing comprehensive accessibility and responsiveness testing

## Local Development (Mock Mode)

For UI development without Cloud SQL:
```bash
scripts\start_mock_server.bat
```
- URL: `http://localhost:5001/dashboard`
- Auto-authenticated as demo user
- Fake data for all pages (Activities, Journal, Coach, etc.)
