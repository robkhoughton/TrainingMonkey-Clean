# Local Mock Development Setup

Run TrainingMonkey locally with fake data for UI development - no Cloud SQL required.

## Quick Start

```bash
# Option 1: Use the batch file
scripts\start_mock_server.bat

# Option 2: Run directly
cd app
set USE_MOCK_DB=true
python run_mock_server.py
```

Server starts at: **http://localhost:5001**

## What's Mocked

The mock database provides:

| Data | Description |
|------|-------------|
| **User** | `demo@trainingmonkey.com` with full settings |
| **Activities** | ~70 realistic activities over 90 days |
| **Recommendations** | AI coaching recommendations |
| **Journal** | 14 days of journal entries |
| **Race Goals** | 2 sample races (Half Marathon, 10K) |
| **Weekly Programs** | Current week's training program |

## Use Cases

### 1. Playwright UI Testing

Perfect for automated UI testing with MCP Playwright:

```javascript
// Playwright test example
await page.goto('http://localhost:5001');
// Mock data is always consistent - great for assertions
```

### 2. Design Agent Loop

For iterating on UI with a design agent:

1. Start mock server: `scripts\start_mock_server.bat`
2. Run Playwright MCP to capture screenshots
3. Send to design agent for feedback
4. Make changes, refresh, repeat

### 3. Frontend Development

Develop React components without database:

```bash
# Terminal 1: Mock Flask backend
scripts\start_mock_server.bat

# Terminal 2: React dev server (if needed)
cd frontend
npm start
```

## Configuration

### Environment Variables

| Variable | Value | Description |
|----------|-------|-------------|
| `USE_MOCK_DB` | `true` | Enables mock mode |
| `DATABASE_URL` | `mock://localhost/trainingmonkey` | Set automatically |

### In .env File

```env
# Add this line to use mock mode
USE_MOCK_DB=true
```

## Mock Data Customization

The mock data is defined in `app/mock_db_utils.py`. You can:

### Reset Data

```python
from mock_db_utils import reset_mock_data
reset_mock_data()  # Resets to initial state
```

### Modify Data Directly

```python
from mock_db_utils import get_mock_store
store = get_mock_store()

# Add a custom activity
store.activities.append({
    'activity_id': 999,
    'user_id': 1,
    'date': '2025-12-10',
    'name': 'Test Run',
    # ... other fields
})
```

### Customize Default User

Edit `MockDataStore.__init__()` in `mock_db_utils.py`:

```python
self.user_settings = {
    1: {
        'email': 'your-test-email@example.com',
        'age': 40,
        # ... customize as needed
    }
}
```

## Architecture

```
┌─────────────────────────────────────────────┐
│              Flask App (strava_app.py)       │
│                      │                       │
│                      ▼                       │
│  ┌─────────────────────────────────────┐    │
│  │    db_utils import (patched)         │    │
│  │              │                       │    │
│  │    ┌────────┴────────┐               │    │
│  │    │                 │               │    │
│  │    ▼                 ▼               │    │
│  │ mock_db_utils   OR  db_utils         │    │
│  │ (fake data)         (Cloud SQL)      │    │
│  └─────────────────────────────────────┘    │
└─────────────────────────────────────────────┘
```

## Limitations

Mock mode does **not** support:

- Real Strava OAuth (use test credentials)
- Actual data sync from Strava
- Complex PostgreSQL-specific queries
- Persistent data (resets on restart)

For testing these features, use the real database or a local PostgreSQL instance.

## Troubleshooting

### "Module not found" errors

Make sure you're running from the `app/` directory or using the batch file.

### Data looks stale

Mock data is regenerated relative to the current date on each startup. Restart the server for fresh dates.

### Need different data patterns

Edit `_generate_mock_activities()` in `mock_db_utils.py` to change:
- Activity frequency
- Distance/elevation ranges
- Heart rate zones
- Activity types

## Files

| File | Purpose |
|------|---------|
| `app/mock_db_utils.py` | Mock database implementation |
| `app/run_mock_server.py` | Startup script with patching |
| `scripts/start_mock_server.bat` | Windows launcher |
| `app/db_credentials_loader.py` | Mock mode detection |
