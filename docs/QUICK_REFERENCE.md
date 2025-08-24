# Quick Reference - Training Monkey Development

## 🚀 Start Development Server

### Option 1: Automated Script (Recommended)
```bash
cd app
./start_dev_server.ps1    # PowerShell
# OR
start_dev_server.bat      # Windows Batch
```

### Option 2: Manual
```bash
cd app
python run_flask.py
```

## 🌐 Access URLs

- **Landing Page**: http://localhost:5000/landing
- **Login Page**: http://localhost:5000/login  
- **Dashboard**: http://localhost:5000/dashboard

## 🔧 Common Issues

### 404 Error on /landing
```bash
# Check port conflicts
netstat -ano | findstr :5000

# Kill conflicting process (usually Docker)
taskkill /f /pid <PID_NUMBER>
```

### Debug Script Works, Browser Doesn't
- **Cause**: Port 5000 occupied by different service
- **Solution**: Use automated startup script

### Template Errors
- **Cause**: Missing request context
- **Solution**: Use browser or test client

## 📁 Key Files

- `app/templates/landing.html` - Landing page template
- `app/run_flask.py` - Flask startup script
- `app/strava_app.py` - Main Flask application
- `docs/LOCAL_DEVELOPMENT_SETUP.md` - Full documentation

## 🛠️ Development Workflow

1. **Start server**: Use automated script
2. **Edit template**: Modify `landing.html`
3. **Save file**: Auto-reload enabled
4. **Refresh browser**: See changes immediately

## ⚡ Quick Commands

```bash
# Check if Flask is running
netstat -an | findstr :5000

# Test routes programmatically  
python test_with_context.py

# Kill all Python processes
taskkill /f /im python.exe
```

## 🎯 Key Lessons

1. **Always check port conflicts first**
2. **Docker often occupies port 5000**
3. **Debug scripts ≠ browser requests**
4. **Duplicate routes cause 404 errors**
