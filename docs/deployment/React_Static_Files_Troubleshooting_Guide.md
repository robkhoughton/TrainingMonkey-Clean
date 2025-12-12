# React Static Files Troubleshooting Guide

## Overview
This document summarizes the resolution of React static file serving issues in the TrainingMonkey application and provides guidance for future troubleshooting.

## Problem Summary
The React dashboard was loading but CSS and JavaScript files were returning 404 errors, preventing proper styling and functionality.

## Root Cause Analysis

### Issue 1: Missing Build Files
**Problem**: React build files were not copied to the Flask app directory for local development.
**Symptoms**: 404 errors for all static files (CSS, JS, manifest.json)
**Solution**: Copy frontend build files to app directory
```bash
xcopy frontend\build\* app\build\ /E /Y
```

### Issue 2: Incorrect React Build Configuration
**Problem**: React was configured with `"homepage": "/static"` causing double static paths.
**Symptoms**: Requests like `/static/static/js/main.xxx.js` (double static)
**Solution**: Temporarily change package.json homepage setting
```json
"homepage": "."
```
Then rebuild and copy files.

### Issue 3: Flask Static File Serving Conflict
**Problem**: Custom static route was being overridden by Flask's default static handling.
**Symptoms**: Files exist in `app/build/static/` but still get 404 errors
**Solution**: Copy React build files to Flask's default static folder
```bash
xcopy app\build\static\* app\static\ /E /Y
```

## Final Solution Architecture

### Local Development Setup
1. **Dashboard Route**: Serves `index.html` from `app/build/`
2. **Static Files**: Served by Flask's default static handler from `app/static/`
3. **File Structure**:
   ```
   app/
   ├── build/
   │   └── index.html          # Dashboard entry point
   └── static/
       ├── js/                 # React JavaScript files
       ├── css/                # React CSS files
       └── manifest.json       # App manifest
   ```

### Cloud Deployment
The Dockerfile already handles both locations correctly:
```dockerfile
COPY build/ /app/build/        # For dashboard route
COPY static/ /app/static/      # For static file serving
```

## Troubleshooting Checklist

### Step 1: Verify File Locations
```bash
# Check if build files exist
ls app/build/index.html
ls app/build/static/js/
ls app/build/static/css/

# Check if static files are in Flask's static folder
ls app/static/js/
ls app/static/css/
```

### Step 2: Check React Build Configuration
```json
// In frontend/package.json
{
  "homepage": "/static"    // For production deployment
  // OR
  "homepage": "."          // For local development
}
```

### Step 3: Verify Flask Routes
- Dashboard route: `@app.route('/dashboard')` → serves from `build/`
- Static files: Flask default → serves from `static/`
- No custom static route needed

### Step 4: Test Static File Access
```bash
# Test direct file access
curl http://localhost:5001/static/js/main.xxx.js
curl http://localhost:5001/static/css/main.xxx.css
```

## Common Error Patterns

### Pattern 1: Double Static Path
**Error**: `GET /static/static/js/main.xxx.js 404`
**Cause**: React homepage configuration issue
**Fix**: Rebuild with correct homepage setting

### Pattern 2: Files Not Found
**Error**: `GET /static/js/main.xxx.js 404`
**Cause**: Files not in Flask's static folder
**Fix**: Copy files to `app/static/`

### Pattern 3: Dashboard Loads But No Styling
**Error**: CSS files return 404
**Cause**: Static files not accessible
**Fix**: Ensure files are in both `app/build/static/` and `app/static/`

## Development Workflow

### For Local Development
**Option 1: Use automated script (recommended)**
```bash
scripts\deploy_local.bat
```

**Option 2: Manual steps**
1. Make React changes in `frontend/src/`
2. Change homepage: Set `"homepage": "."` in `frontend/package.json`
3. Build React app: `cd frontend && npm run build`
4. Copy to app directory: `xcopy frontend\build\* app\build\ /E /Y`
5. Copy static files: `xcopy app\build\static\* app\static\ /E /Y`
6. Restore homepage: Set `"homepage": "/static"` in `frontend/package.json`
7. Test locally: `http://localhost:5001/dashboard`

### For Production Deployment
1. Use deployment script: `scripts/deploy.bat`
2. Script handles React build and file copying
3. Dockerfile handles both build and static locations
4. **Note**: Both local and production now use `"homepage": "."` for consistent behavior

## Key Lessons Learned

1. **Flask Static Handling**: Flask automatically serves files from `static/` folder at `/static/` URLs
2. **React Homepage Setting**: Controls how React generates asset paths
3. **Dual Location Strategy**: Files need to be in both `build/` (for dashboard) and `static/` (for assets)
4. **Deployment vs Development**: Cloud deployment was already correctly configured

## Prevention Strategies

1. **Documentation**: Keep this guide updated with any changes
2. **Automation**: Consider updating local deployment script to handle both locations
3. **Testing**: Always test both dashboard loading and static file access
4. **Monitoring**: Watch for 404 errors in browser console during development

## Related Files

- `frontend/package.json` - React build configuration
- `app/strava_app.py` - Flask routes and static serving
- `app/Dockerfile.strava` - Cloud deployment configuration
- `scripts/deploy.bat` - Local deployment script
- `docs/LOCAL_DEVELOPMENT_SETUP.md` - General development setup

## Quick Reference Commands

```bash
# Rebuild and copy for local development
cd frontend && npm run build
cd .. && xcopy frontend\build\* app\build\ /E /Y
xcopy app\build\static\* app\static\ /E /Y

# Test static file access
curl http://localhost:5001/static/js/main.xxx.js

# Check file locations
ls app/build/index.html
ls app/static/js/
ls app/static/css/
```

---
*Last Updated: September 16, 2025*
*Created during resolution of React static file serving issues*
