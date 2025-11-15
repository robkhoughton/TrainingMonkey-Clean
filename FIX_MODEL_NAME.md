# URGENT FIX: Model Name Typo

## The Problem
**Error:** `claude-sonnet-4.5-20250929` (has a DOT)  
**Correct:** `claude-sonnet-4-5-20250929` (needs a DASH)

## The Fix

Edit `app/config.json` and change line 4:

**BEFORE:**
```json
"model": "claude-sonnet-4.5-20250929",
```

**AFTER:**
```json
"model": "claude-sonnet-4-5-20250929",
```

Just change the dot (`.`) to a dash (`-`) between the 4 and 5.

## After Editing

Save the file and redeploy:
```
cd C:\Users\robho\Documents\TrainingMonkey-Clean\app
deploy_strava_simple.bat
```

## This Will Fix

- ✅ Autopsy generation (no more fallback)
- ✅ Tomorrow's Training Decision generation
- ✅ All AI recommendations

The API is working, you have credits - it was just a typo in the model name!

