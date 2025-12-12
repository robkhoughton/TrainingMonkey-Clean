---
paths: ["app/Dockerfile*", "app/*.py", "frontend/**/*", "scripts/deployment/*"]
---

# Deployment Standards

## Deployment Model

**Local deployment only** - User runs all deployment commands manually.
- Assistant prepares code changes but NEVER runs deployment commands
- User initiates deployment via `app/deploy_strava_simple.bat`
- All changes tested locally before deployment

## Dockerfile Requirements (CRITICAL)

The project uses **explicit file copying** in `app/Dockerfile.strava` for security.

### When Creating New Python Files

**Every new `.py` file in `app/` MUST be added to Dockerfile.strava.**

1. Create your new file: `app/my_new_module.py`
2. Test locally
3. Add to Dockerfile.strava in the "Core modules" section:
   ```dockerfile
   COPY my_new_module.py .
   ```
4. Commit both the new file AND the Dockerfile change

### Failure Pattern

If deployment succeeds but you see `ModuleNotFoundError: No module named 'xyz'`:
- The module exists locally but is missing from Dockerfile COPY list
- Fix: Add the COPY line and redeploy

### Verification

After creating new Python files, verify they're in the Dockerfile:
```bash
grep "my_new_module" app/Dockerfile.strava
```

## Frontend Build Process

React app in `frontend/` must be built and copied to `app/static/` for deployment.

### Build and Copy Sequence (from project root)

```cmd
cd frontend
npm run build
cd ..
del /Q app\static\js\main.*.js
del /Q app\static\js\main.*.LICENSE.txt
del /Q app\static\css\main.*.css
del /Q app\build\static\js\main.*.js
del /Q app\build\static\js\main.*.LICENSE.txt
del /Q app\build\static\css\main.*.css
xcopy frontend\build\* app\build\ /E /Y
xcopy frontend\build\static\* app\static\ /E /Y
copy frontend\build\training-monkey-runner.webp app\static\training-monkey-runner.webp
```

Or use: `scripts/build_and_copy.bat`

### Key Points

- Always delete old versioned files before copying new ones
- Build creates versioned JS files (e.g., `main.34e5b039.js`)
- `index.html` auto-references correct version
- After ANY frontend changes, rebuild and copy before testing/deployment

### Copy Destinations

| Source | Destination |
|--------|-------------|
| `frontend/build/*` | `app/build/` |
| `frontend/build/static/*` | `app/static/` |
| `frontend/build/training-monkey-runner.webp` | `app/static/` |

## Pre-Deployment Checklist

Before user deploys:
1. All new Python files added to Dockerfile.strava
2. Frontend built and copied (if React changes made)
3. Migration scripts created (if schema changes needed)
4. Local testing completed
5. Changes committed to git

## Common Deployment Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| `ModuleNotFoundError` | Missing COPY in Dockerfile | Add COPY line |
| Old frontend showing | Build not copied | Run build and copy sequence |
| Database errors | Migration not run | User runs migration script |
