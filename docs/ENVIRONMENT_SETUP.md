# Environment Setup Guide

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd app
pip install -r strava_requirements.txt
```

### 2. Set Up Environment Variables
```bash
python setup_environment.py
```

### 3. Start Development Server
```bash
./start_dev_server.ps1
```

## 🔧 Environment Variables

### Required for Basic Functionality

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `SECRET_KEY` | Flask secret key for sessions | ✅ | Auto-generated |
| `DB_PATH` | SQLite database path (local) | ✅ | `../training_data.db` |
| `PORT` | Flask app port | ❌ | `5000` |

### Required for Strava Integration

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `STRAVA_CLIENT_ID` | Strava API client ID | ✅ | None |
| `STRAVA_CLIENT_SECRET` | Strava API client secret | ✅ | None |

### Required for AI Recommendations

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `ANTHROPIC_API_KEY` | Anthropic Claude API key | ❌ | None |

### Production Only

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `DATABASE_URL` | PostgreSQL connection string | ❌ | None |
| `GOOGLE_CLOUD_PROJECT` | Google Cloud project ID | ❌ | `dev-ruler-460822-e8` |

## 📋 Setup Instructions

### 1. Strava API Setup

1. Go to https://www.strava.com/settings/api
2. Create a new application
3. Set callback domain to: `http://localhost:5000`
4. Copy the Client ID and Client Secret
5. Add to your `.env` file:
   ```
   STRAVA_CLIENT_ID=your-client-id
   STRAVA_CLIENT_SECRET=your-client-secret
   ```

### 2. Anthropic API Setup (Optional)

1. Go to https://console.anthropic.com/
2. Create an account and get an API key
3. Add to your `.env` file:
   ```
   ANTHROPIC_API_KEY=your-api-key
   ```

### 3. Database Setup

**Local Development (SQLite):**
- No setup required - SQLite file will be created automatically
- Database location: `../training_data.db`

**Production (PostgreSQL):**
- Set up PostgreSQL database
- Add connection string to `.env`:
  ```
  DATABASE_URL=postgresql://username:password@host:port/database
  ```

## 🔍 Environment Variable Priority

The app loads environment variables in this order:
1. System environment variables
2. `.env` file (if exists)
3. Default values

## 🛠️ Troubleshooting

### Issue: "python-dotenv not installed"
```bash
pip install python-dotenv
```

### Issue: "No .env file found"
```bash
python setup_environment.py
```

### Issue: "Missing API keys"
- Check that your `.env` file exists
- Verify API keys are correctly set
- Ensure no extra spaces or quotes around values

### Issue: "Database connection failed"
- For local development: Check `DB_PATH` points to valid location
- For production: Verify `DATABASE_URL` is correct

## 📁 File Structure

```
TrainingMonkey-Clean/
├── app/
│   ├── .env                    # Environment variables (create this)
│   ├── env_example.txt         # Example environment file
│   ├── setup_environment.py    # Setup script
│   ├── strava_requirements.txt # Python dependencies
│   └── ...
└── training_data.db           # SQLite database (auto-created)
```

## 🔒 Security Notes

- **Never commit `.env` files** to version control
- **Use strong secret keys** in production
- **Rotate API keys** regularly
- **Use environment-specific** configurations

## 🚀 Production Deployment

For production deployment, set these additional variables:
- `FLASK_ENV=production`
- `FLASK_DEBUG=False`
- `DATABASE_URL` (PostgreSQL)
- `GOOGLE_CLOUD_PROJECT` (if using Google Cloud)


