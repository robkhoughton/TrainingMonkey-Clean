---
ContentType:
status: AI Raw
Next Steps:
expert_review:
title: Step-by-Step Deployment from React to Cloud Run
description:
agent:
authors:
  - Rob Houghton
notes:
revision_notes:
manual date created:
created_at: 2026-04-01 15:37
updated_at: 2026-04-01 15:37
tags:
  - type/note
links:
---
# Step-by-Step Deployment from React to Cloud Run


Step-by-Step Deployment from React to Cloud Run:

## 1. Rebuild React App
cmd
cd C:\Users\robho\Documents\VAULT\TrainingMonkey-Clean\frontend
npm run build

## 2. Clean Old Build Files
cmd
cd C:\Users\robho\Documents\VAULT\TrainingMonkey-Clean
del /Q app\static\js\main.*.js
del /Q app\static\js\main.*.LICENSE.txt
del /Q app\static\css\main.*.css
del /Q app\build\static\js\main.*.js
del /Q app\build\static\js\main.*.LICENSE.txt
del /Q app\build\static\css\main.*.css

## 3. Copy to Deployment
cmd
cd C:\Users\robho\Documents\VAULT\TrainingMonkey-Clean
xcopy frontend\build\* app\build\ /E /Y
xcopy frontend\build\static\* app\static\ /E /Y
copy frontend\build\training-monkey-runner.webp app\static\training-monkey-runner.webp

## 4. Deploy to Cloud Run
cmd
cd C:\Users\robho\Documents\VAULT\TrainingMonkey-Clean\app
deploy_strava_simple.bat
