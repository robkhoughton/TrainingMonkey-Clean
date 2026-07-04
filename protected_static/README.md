# protected_static/ — DO NOT let the deploy pipeline touch this directory

Canonical, protected backups of static assets that are **NOT produced by the
React build** and are therefore silently destroyed by any deploy step that
wildcard-cleans `app/static/js/*` or `app/static/css/*`.

## What lives here

| File                  | Live copy (served)                     | Lines |
| --------------------- | -------------------------------------- | ----- |
| `getting_started.css` | `app/static/css/getting_started.css`   | ~2897 |
| `getting_started.js`  | `app/static/js/getting_started.js`     | ~1165 |

These two files style/script **8 server-rendered Flask pages** (not the React
SPA), via `base_settings.html` and `base_getting_started.html`:
settings_hrzones, settings_integrations, settings_acwr_archive, guide,
tutorials, faq, get_most_out, getting_started_resources.

If either file goes missing from `app/static/`, all 8 pages render with broken
fonts and navigation.

## Why this backup exists

They are hand-maintained, live in the same directories as content-hashed React
bundles (`main.*.js` / `main.*.css`), and have been wiped before by a wildcard
`rm app/static/css/*` in the deploy clean step. The deploy clean step was fixed
(2026-04-15) to target only `main.*` patterns — but this directory is the
belt-and-suspenders backup in case a manual command or future script wildcards
again.

## Recovery

1. Preferred: `cp protected_static/getting_started.css app/static/css/` and
   `cp protected_static/getting_started.js  app/static/js/`
2. Fallback (if this dir is also lost): restore from git commit `27889ae`.

## Maintenance

**Self-maintaining via the `/deploy` skill.** Step 2 ("Protect non-build static
assets") of `.claude/commands/deploy.md` runs before the clean step on every
deploy and:

- refreshes these backups from the live files when the live files are healthy
  (non-empty), so the backup never goes stale; and
- if a live file is already missing/empty but the backup exists, **restores the
  live file from the backup** instead of clobbering a good backup with a bad
  source.

So as long as you deploy through `/deploy`, no manual re-copy is needed. Only if
you edit `getting_started.*` and want the backup updated *without* deploying
should you copy them here by hand. These are the only two non-build assets in
`app/static/js|css/`; everything else there is disposable build output.
