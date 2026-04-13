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

### 2. Clean stale build artifacts

```bash
rm -f /c/Users/robho/Documents/VAULT/TrainingMonkey-Clean/app/static/js/* /c/Users/robho/Documents/VAULT/TrainingMonkey-Clean/app/static/css/* /c/Users/robho/Documents/VAULT/TrainingMonkey-Clean/app/build/static/js/* /c/Users/robho/Documents/VAULT/TrainingMonkey-Clean/app/build/static/css/*
```

### 3. Copy build artifacts

```bash
cp -r /c/Users/robho/Documents/VAULT/TrainingMonkey-Clean/frontend/build/. /c/Users/robho/Documents/VAULT/TrainingMonkey-Clean/app/build/ && cp -r /c/Users/robho/Documents/VAULT/TrainingMonkey-Clean/frontend/build/static/. /c/Users/robho/Documents/VAULT/TrainingMonkey-Clean/app/static/
```

### 4. Deploy

```bash
cd /c/Users/robho/Documents/VAULT/TrainingMonkey-Clean/app && echo "" | cmd //c "C:\\Users\\robho\\Documents\\VAULT\\TrainingMonkey-Clean\\app\\deploy_strava_simple.bat"
```

## On success

Report: build output summary, files copied, deploy output.

## On failure

Report: which step failed, the exact error message, and stop. Do not attempt recovery steps.
