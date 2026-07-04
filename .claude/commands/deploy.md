---
allowed-tools: Bash
description: Build React frontend, copy assets, and deploy to Cloud Run
model: haiku
---

Build, copy, and deploy the Your Training Monkey frontend and backend.

## Steps

Run these commands in sequence using the Bash tool. Stop and report any failure immediately — do not proceed to the next step.

### 1. Build React frontend

```bash
cd /c/Users/robho/Documents/VAULT/TrainingMonkey-Clean/frontend && npm run build
```

### 2. Protect non-build static assets

Refresh the `protected_static/` backup from the live `getting_started.*` files BEFORE the clean step runs. These files are hand-maintained (not React build output) but live in `app/static/js|css` alongside the versioned bundles. Guard rules: only overwrite the backup when the live file exists and is non-empty (so an already-damaged live file can never clobber a good backup); if a live file is missing/empty but the backup exists, heal it by restoring from the backup.

```bash
ROOT=/c/Users/robho/Documents/VAULT/TrainingMonkey-Clean
mkdir -p "$ROOT/protected_static"
for pair in "css/getting_started.css" "js/getting_started.js"; do
  sub="${pair%%/*}"; file="${pair##*/}"
  live="$ROOT/app/static/$sub/$file"
  backup="$ROOT/protected_static/$file"
  if [ -s "$live" ]; then
    cp -f "$live" "$backup" && echo "protected_static: refreshed $file from live"
  elif [ -s "$backup" ]; then
    cp -f "$backup" "$live" && echo "protected_static: WARNING live $file missing/empty — restored from backup"
  else
    echo "protected_static: ERROR both live and backup missing for $file — recover from git commit 27889ae" >&2
  fi
done
```

### 3. Clean stale build artifacts

Only delete React-generated versioned files — do NOT wipe entire directories (getting_started.css/js and other non-React assets live here too).

```bash
rm -f /c/Users/robho/Documents/VAULT/TrainingMonkey-Clean/app/static/js/main.*.js /c/Users/robho/Documents/VAULT/TrainingMonkey-Clean/app/static/js/main.*.js.LICENSE.txt /c/Users/robho/Documents/VAULT/TrainingMonkey-Clean/app/static/css/main.*.css /c/Users/robho/Documents/VAULT/TrainingMonkey-Clean/app/build/static/js/main.*.js /c/Users/robho/Documents/VAULT/TrainingMonkey-Clean/app/build/static/js/main.*.js.LICENSE.txt /c/Users/robho/Documents/VAULT/TrainingMonkey-Clean/app/build/static/css/main.*.css
```

### 4. Copy build artifacts

```bash
cp -r /c/Users/robho/Documents/VAULT/TrainingMonkey-Clean/frontend/build/. /c/Users/robho/Documents/VAULT/TrainingMonkey-Clean/app/build/ && cp -r /c/Users/robho/Documents/VAULT/TrainingMonkey-Clean/frontend/build/static/. /c/Users/robho/Documents/VAULT/TrainingMonkey-Clean/app/static/
```

### 5. Deploy

```bash
cd /c/Users/robho/Documents/VAULT/TrainingMonkey-Clean/app && echo "" | cmd //c "C:\\Users\\robho\\Documents\\VAULT\\TrainingMonkey-Clean\\app\\deploy_strava_simple.bat"
```

## On success

Report: build output summary, files copied, deploy output.

## On failure

Report: which step failed, the exact error message, and stop. Do not attempt recovery steps.
