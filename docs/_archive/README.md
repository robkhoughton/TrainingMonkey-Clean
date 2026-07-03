# Docs Archive

Historical and superseded documentation moved out of the live `docs/` tree on **2026-07-03**
during a full docs cleanup. Nothing here is authoritative or maintained — it is kept for
provenance and history. Original subpaths are preserved (e.g. `_archive/JournalLLM/…`,
`_archive/deployment/…`).

To restore any file: `git mv docs/_archive/<path> docs/<path>`.

## What was archived and why

- **Root fix/status docs (frozen 2025-12-12)** — one-off records for work long since shipped:
  timezone fix, ESLint cleanup, email-verification debugging, compliance audit, chatbot plan,
  chat-context map, connection-pool note, project status review, quick reference, Strava OAuth
  technical guide, test organization, UX testing prompt, user-flow diagram, wireframe, app_README,
  local mock development, testing/QA guide.
- **`JournalLLM/`** — Nov–Dec 2025 autopsy/journal LLM fix summaries and deployment checklists.
- **`UserProgression/`** — shipped user-progression PRD, action plan, implementation summary.
- **`features/`** — historical feature implementation/deployment records (TRIMP enhancement,
  swimming, cycling, Garmin attribution, email templates, etc.). The live coaching roadmap
  `COACHING_FRAMEWORK_GAPS.md` was kept in `docs/features/`.
- **`database/`** — optimization plans/reports and cleanup guides (the live access/security/
  migration/schema/SQL guides stayed in `docs/database/`).
- **`deployment/`** — email-enforcement rollout, `email_verification_future/` (dormant feature
  incl. `.py` scripts), Google Analytics, SEO, Lighthouse, performance analysis, SMTP setup
  (the live deployment checklist / dev / environment / API-key / static-files guides stayed).
- **Shipped design & review docs** — `design_dynamic_aet_*`, `design_lt1_step_test_*`,
  `code_review_2026-06-09`, `refactor_plan_race_context_*` (the features they described are
  now shipped; methodology lives on in `docs/methodology/dynamic_aet.md`).
- **`guiding_principles_summary.md`** — stale dev standards that duplicated and contradicted the
  current `.claude/rules/` (SQL-Editor-only migrations, `datetime.now()`); superseded.
- **`screenshots/`** — old Playwright/test screenshot iterations.
- **`YTM roadmap_20251207.docx`** — superseded by `docs/architecture/YTM Roadmap.md`.

## Hard-deleted (not archived)
- `docs/README.md` (old) — upstream "AI Dev Tasks" boilerplate, unrelated to YTM; replaced with a real index.
- `docs/Review and compare @New_User_Accoun.txt` — a pasted working prompt, not documentation.
