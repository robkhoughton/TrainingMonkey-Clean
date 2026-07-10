---
allowed-tools: Bash
description: Build React frontend, copy assets, and deploy to Cloud Run
model: haiku
---

Build, copy, and deploy the Your Training Monkey frontend and backend.

## How to run

Run the entire deploy as a **single** Bash command so it needs only one approval.
Do not split it into separate steps or run the individual commands yourself.

```bash
bash /c/Users/robho/Documents/VAULT/TrainingMonkey-Clean/scripts/deploy_all.sh
```

The script runs all five stages in order and stops at the first hard failure:

1. **Build React frontend** — `npm run build` in `frontend/`.
2. **Protect non-build static assets** — refresh the `protected_static/` backups of
   the hand-maintained `getting_started.*` files (only overwrite a backup from a
   non-empty live file; heal a missing/empty live file from the backup).
3. **Clean stale build artifacts** — delete only React-generated `main.*` bundles,
   never whole directories (non-React assets live alongside them).
4. **Copy build artifacts** — copy `frontend/build/` into `app/build/` and `app/static/`.
5. **Deploy** — run `deploy_strava_simple.bat` from `app/`.

## On success

Report: build output summary, files copied, deploy output.

## On failure

The script prints `DEPLOY FAILED at <step>` to stderr and exits non-zero. Report which
step failed and the exact error message, then stop. Do not attempt recovery steps.
