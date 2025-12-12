# Local Development Setup Guide

## Quick Start

### 1. Check for Port Conflicts
Before starting the Flask app, always check if port 5001 is already in use:

```bash
# Check what's running on port 5001
netstat -ano | findstr :5001

# If you see a process, identify it:
tasklist /fi "PID eq <PID_NUMBER>"

# Kill conflicting processes (usually Docker):
taskkill /f /pid <PID_NUMBER>
```

### 2. Start Flask App
```bash
cd app
python run_flask.py
```

### 3. Access Landing Page
Open your browser and go to: `http://localhost:5001/landing`

## Common Issues & Solutions

### Issue: 404 Error on /landing
**Cause**: Port 5001 occupied by Docker or other service
**Solution**: 
1. Kill the conflicting process
2. Restart Flask app

### Issue: Debug Script Works But Browser Doesn't
**Cause**: Different service running on port 5001
**Solution**: Always check `netstat -ano | findstr :5001` first

### Issue: Duplicate Route Conflicts
**Cause**: Multiple `@app.route('/')` definitions in strava_app.py
**Solution**: Keep only one root route definition

## Development Workflow

1. **Start Development**:
   ```bash
   cd app
   python run_flask.py
   ```

2. **Make Changes**:
   - Edit `app/templates/landing.html`
   - Save file
   - Refresh browser (auto-reload enabled)

3. **Test Changes**:
   - Browser: `http://localhost:5001/landing`
   - Debug script: `python test_with_context.py`

## File Structure

```
TrainingMonkey-Clean/
├── app/
│   ├── run_flask.py          # Flask startup script
│   ├── strava_app.py         # Main Flask application
│   ├── templates/
│   │   └── landing.html      # Landing page template
│   ├── static/
│   │   └── images/
│   │       └── wireframe-runner.jpg
│   └── test_with_context.py  # Debug/testing script
└── docs/
    └── LOCAL_DEVELOPMENT_SETUP.md
```

## Troubleshooting Commands

```bash
# Check if Flask app is running
netstat -an | findstr :5001

# Test routes programmatically
python test_with_context.py

# Kill all Python processes (if needed)
taskkill /f /im python.exe

# Check specific process
tasklist /fi "PID eq <PID>"
```

## Key Lessons Learned

1. **Always check port conflicts first** - Docker often occupies port 5000, so we use 5001
2. **Debug scripts work differently** - They use Flask test client, not HTTP requests
3. **Route conflicts matter** - Duplicate routes can cause 404 errors
4. **Request context is crucial** - Templates need proper context to render

## Quick Reference

| Issue | Check | Solution |
|-------|-------|----------|
| 404 on /landing | `netstat -ano \| findstr :5001` | Kill conflicting process |
| Debug works, browser doesn't | Port conflict | Restart Flask app |
| Template errors | Request context | Use test client or browser |
| Route not found | Route registration | Check for duplicate routes |
