# Local Deployment with New ACWR Configuration Features

This guide will help you deploy the Training Monkey app locally with direct connection to the cloud database, including the new ACWR configuration features we just implemented.

## 🆕 New Features Included

### 1. **Overtraining Risk Over Time Chart**
- Combined view of Internal ACWR, External ACWR, and Normalized Divergence
- Matches the Parameter Visualization page design
- Proper risk zones with color coding
- Smaller markers and consistent sizing with other dashboard charts

### 2. **Configurable ACWR Parameters**
- Per-user dashboard configuration
- Chronic period: 28-90 days (configurable)
- Decay rate: 0.01-0.20 (exponential weighting)
- Real-time recalculation with custom parameters

### 3. **Parameter Visualization Integration**
- "Apply to Dashboard" button on Parameter Visualization page
- "Check Current" button to see current dashboard configuration
- Preview functionality (the Parameter Visualization chart IS the preview)

## 📋 Database Rules Compliance

**Important**: This project follows strict database rules for one-time operations:

- ✅ **Use SQL Editor** for creating tables, adding columns, etc.
- ❌ **Don't use code** for one-time database operations
- 🎯 **Purpose**: Keeps codebase clean and follows established patterns

The deployment script will **check** if required tables exist but **won't create them automatically**. You need to create the `user_dashboard_configs` table manually using your cloud database's SQL Editor.

## 🚀 Quick Deployment

### Option 1: Automated Script (Recommended)
```bash
# Run the automated deployment script
cd scripts
python deploy_local_with_cloud_db.py
```

### Option 2: Windows Batch File
```cmd
# Run the Windows batch file
cd scripts
deploy_local_with_cloud_db.bat
```

### Option 3: Manual Steps
```bash
# 1. Set up database connection
cd scripts
python setup_local_database_connection.py

# 2. Create database tables
# You need to manually create the user_dashboard_configs table in your cloud database
# using the SQL Editor. The script will check if it exists but won't create it automatically.
# This follows the project's database rules for one-time operations.

# 3. Install dependencies
cd ../app
pip install -r strava_requirements.txt
cd ../frontend
npm install

# 4. Build frontend
npm run build
cd ..
xcopy frontend\build\* app\build\ /E /Y

# 5. Start development server
cd app
python run_flask.py
```

## 🔧 Configuration

### Database Connection
The script will prompt you for:
- **Host**: `10.109.208.9` (default from deployment)
- **Port**: `5432` (default)
- **Database**: `train-d` (default)
- **Username**: `appuser` (default)
- **Password**: You'll need to enter this

### Environment Variables
The script creates a `.env` file in the `app` directory with:
- Database connection string
- Flask configuration
- API keys (optional)

## 📱 Available URLs

Once deployed, you can access:
- **Landing Page**: http://localhost:5001/landing
- **Login Page**: http://localhost:5001/login
- **Dashboard**: http://localhost:5001/dashboard
- **Parameter Visualization**: http://localhost:5001/acwr-visualization

## 🆕 Testing the New Features

### 1. **View the New Dashboard Chart**
1. Go to http://localhost:5001/dashboard
2. Look for the "Overtraining Risk Over Time" chart
3. Notice the combined view with three lines and risk zones
4. Check the chart note to see which calculation method is being used

### 2. **Configure Dashboard ACWR Parameters**
1. Go to http://localhost:5001/acwr-visualization
2. Select a user from the dropdown
3. Adjust the chronic period slider (28-90 days)
4. Adjust the decay rate slider (0.01-0.20)
5. Click "Apply to Dashboard"
6. Go back to the dashboard to see the updated chart

### 3. **Check Current Configuration**
1. On the Parameter Visualization page
2. Click "Check Current" to see the current dashboard configuration
3. The status will show either custom config or default config

## 🗄️ Database Schema

The deployment automatically creates the `user_dashboard_configs` table:

```sql
CREATE TABLE user_dashboard_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    chronic_period_days INTEGER NOT NULL CHECK (chronic_period_days >= 28 AND chronic_period_days <= 90),
    decay_rate REAL NOT NULL CHECK (decay_rate >= 0.01 AND decay_rate <= 0.20),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

## 🔍 Troubleshooting

### Database Connection Issues
- Ensure your IP is whitelisted in Google Cloud SQL
- Verify the database credentials are correct
- Check that the Google Cloud SQL instance is running

### Frontend Build Issues
- Ensure Node.js and npm are installed
- Try running `npm install` manually in the frontend directory
- Check for TypeScript errors in the console

### Port Conflicts
- The app runs on port 5001
- If port 5001 is in use, the script will offer to kill the conflicting process
- You can manually change the port in `app/run_flask.py`

## 📊 What's Different

### Dashboard Chart Changes
- **Before**: Two separate charts (ACWR and Normalized Divergence)
- **After**: One combined chart with all three metrics
- **Sizing**: Now matches other dashboard charts
- **Markers**: Smaller, more consistent with other charts
- **Labels**: Better spacing, no crowding

### Configuration System
- **Before**: Fixed 28-day chronic period, no exponential decay
- **After**: Configurable chronic period (28-90 days) with exponential decay
- **Storage**: Per-user configuration in database
- **Interface**: Easy-to-use controls on Parameter Visualization page

## 🎯 Next Steps

1. **Test the new features** with your training data
2. **Experiment with different configurations** to see how they affect the charts
3. **Compare the dashboard** with the Parameter Visualization page
4. **Apply your preferred configuration** to the dashboard

The system is now ready for testing with all the new ACWR configuration features!
