# Strava Sync Service

## Project Overview

This service integrates with Strava to provide training load metrics and AI-powered recommendations for the Training Monkey™ Dashboard. It fetches activities from Strava, calculates training metrics, and generates insights to help users optimize their training.

## Codebase Analysis

### Files Summary
- **Python Files**: 16 files (9,505 total lines)
- **JSON Files**: 7 files (99 total lines)
- **Total**: 23 files (9,604 lines)

### Core Components

1. **Strava API Integration**
   - OAuth authentication flow
   - Activity data fetching and processing
   - Token management with auto-refresh

2. **Training Load Calculation**
   - Banister TRIMP (Training Impulse)
   - Acute-to-Chronic Workload Ratio (ACWR)
   - Normalized divergence metrics

3. **Web Application**
   - Flask-based backend API
   - User authentication and multi-user support
   - React dashboard integration

4. **AI Recommendations**
   - Training recommendations based on activity data
   - Workout "autopsy" analysis
   - Daily and weekly training insights

### Key Files Breakdown

| File                           | Lines | Description                                       |
|--------------------------------|-------|---------------------------------------------------|
| strava_app.py                  | 2,695 | Main Flask application with API endpoints         |
| garmin_training_load.py        | 1,615 | Legacy Garmin training load calculations          |
| llm_recommendations_module.py  | 1,453 | AI recommendation generation logic                |
| strava_training_load.py        | 1,026 | Strava activity processing and metrics            |
| strava_training_load_before.py | 1,058 | Previous version of training load calculations    |
| db_utils.py                    | 582   | Database utilities and queries                    |
| unified_metrics_service.py     | 326   | Consolidated metrics service                      |
| enhanced_token_management.py   | 253   | Strava token management and refresh               |
| auth.py                        | 137   | User authentication                               |
| timezone_utils.py              | 89    | Timezone handling utilities                       |
| create_dashboard_user.py       | 57    | User creation script                              |
| create_admin.py                | 54    | Admin user creation script                        |
| run_full_sync.py               | 32    | Script to run a complete sync                     |
| local_debug.py                 | 59    | Debugging utilities                               |

### Configuration Files

- `strava_config.json`: Strava API credentials and HR parameters
- `strava_tokens.json`: Strava API access tokens
- `config.json`: General application configuration

## Architecture

The service follows a modular architecture:

1. **Data Collection Layer**
   - Strava API integration (strava_training_load.py)
   - Token management (enhanced_token_management.py)

2. **Processing Layer**
   - Training load calculations
   - Moving averages and metrics

3. **Persistence Layer**
   - Database utilities (db_utils.py)
   - Multi-user data storage

4. **API Layer**
   - Flask endpoints (strava_app.py)
   - Authentication (auth.py)

5. **AI Recommendation Layer**
   - LLM integration (llm_recommendations_module.py)
   - Training insights generation

## Key Features

- Multi-user support with individual Strava connections
- Automatic token refresh and robust error handling
- Training load metrics with internal/external load comparison
- AI-powered training recommendations and workout analysis
- Journal entries for tracking workout observations
- Comprehensive REST API for frontend integration