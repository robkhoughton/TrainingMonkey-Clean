# Training Monkey™ - Intelligent Trail Running Analytics Platform

## Project Overview

Training Monkey™ is a comprehensive trail running analytics platform that integrates with Strava to provide advanced training work/load metrics and AI-powered recommendations. The platform fetches activities from Strava, calculates sophisticated training metrics, and generates personalized insights via a Claude API to help runners optimize their training and prevent overtraining.

## Project Structure

```
TrainingMonkey-Clean/
├── app/                    # Flask backend application
│   ├── strava_app.py      # Main Flask application with API endpoints
│   ├── garmin_training_load.py        # Training load calculations
│   ├── llm_recommendations_module.py  # AI recommendation generation
│   ├── strava_training_load.py        # Strava activity processing
│   ├── db_utils.py                    # Database utilities and queries
│   ├── auth.py                        # User authentication
│   ├── config.json                   # Application configuration
│   ├── strava_config.json            # Strava API credentials
│   ├── templates/                    # HTML templates
│   ├── static/                       # Static assets
│   └── build/                        # Frontend build output (deployment)
├── frontend/              # React TypeScript frontend
│   ├── src/               # React source code
│   ├── public/            # Public assets
│   ├── package.json       # Dependencies and scripts
│   └── build/             # Production build output
├── docs/                  # Documentation
│   ├── setup-guide.md     # Setup instructions
│   └── Deployment_script.txt # Deployment process
└── scripts/               # Utility scripts
```

## Architecture Overview

The platform follows a modern, clean architecture with clear separation of concerns:

### Backend (Flask)
- **API Layer**: RESTful endpoints for frontend communication
- **Data Processing**: Training work/load calculations and metrics analysis
- **AI Integration**: LLM-powered training recommendations
- **Authentication**: Multi-user support with secure authentication
- **Database**: User data persistence and activity storage

### Frontend (React + TypeScript)
- **Dashboard**: Interactive training load visualization
- **Charts**: ACWR and training metrics display
- **User Interface**: Modern, responsive design
- **State Management**: Client-side data handling

### Key Features

- **Multi-user Support**: Individual Strava connections per user
- **Advanced Metrics**: 
  - Banister TRIMP (Training Impulse)
  - Acute-to-Chronic Work/Load Ratio (ACWR)
  - Normalized divergence metrics
  - Internal load vs External work comparison
- **AI-Powered Insights**: 
  - Personalized training recommendations
  - Workout "autopsy" analysis
  - Daily and weekly training insights
- **Robust Integration**: 
  - Automatic Strava token refresh
  - Comprehensive error handling
  - Real-time data synchronization

## Development Setup

### Prerequisites
- Python 3.8+
- Node.js 16+
- npm or yarn
- Google Cloud Platform account (for deployment)

### Backend Setup
```bash
# Navigate to backend directory
cd app/

# Install Python dependencies
pip install -r strava_requirements.txt

# Configure Strava API credentials
cp strava_config.json.example strava_config.json
# Edit strava_config.json with your Strava API credentials

# Initialize database
python create_admin.py
```

### Frontend Setup
```bash
# Navigate to frontend directory
cd frontend/

# Install dependencies
npm install

# Start development server
npm start
```

### Environment Configuration
1. **Strava API Setup**: Configure `app/strava_config.json` with your Strava API credentials
2. **Database**: Ensure your database connection is configured in `app/config.json`
3. **Development Proxy**: Frontend is configured to proxy API calls to `http://127.0.0.1:8080`

## Development Workflow

### Local Development
1. **Start Backend**: Run Flask app from `app/` directory
   ```bash
   cd app/
   python strava_app.py
   ```

2. **Start Frontend**: Run React development server
   ```bash
   cd frontend/
   npm start
   ```

3. **Development Flow**:
   - Frontend runs on `http://localhost:3000`
   - Backend API runs on `http://localhost:8080`
   - Frontend proxies API calls to backend during development

### Code Organization
- **Backend Logic**: All Flask routes and business logic in `app/`
- **Frontend Components**: React components in `frontend/src/`
- **Shared Assets**: Static files organized in respective directories
- **Documentation**: Setup guides and deployment docs in `docs/`

## Deployment Process

### Production Deployment to Google Cloud Run

1. **Build Frontend**
   ```bash
   cd frontend/
   npm run build
   ```

2. **Copy Build to Backend**
   ```bash
   # From project root
   xcopy frontend\build\* app\build\ /E /Y
   ```

3. **Deploy to Cloud Run**
   ```bash
   cd app/
   # Use your deployment script
   deploy_strava_simple.bat
   ```

### Deployment Architecture
- **Frontend**: Built React app served from `app/build/`
- **Backend**: Flask API running on Cloud Run
- **Static Assets**: Served directly by Flask from build directory
- **Database**: Cloud SQL or similar managed database service

## Core Components

### Backend Services
- **strava_app.py** (2,695 lines): Main Flask application with API endpoints
- **garmin_training_load.py** (1,615 lines): Training load calculations
- **llm_recommendations_module.py** (1,453 lines): AI recommendation generation
- **strava_training_load.py** (1,026 lines): Strava activity processing
- **db_utils.py** (582 lines): Database utilities and queries
- **auth.py** (137 lines): User authentication system

### Frontend Components
- **TrainingLoadDashboard.tsx**: Main dashboard with training metrics
- **JournalPage.tsx**: Training journal and notes
- **SettingsPage.tsx**: User preferences and configuration
- **ActivitiesPage.tsx**: Activity history and details

## Configuration

### Strava Integration
- OAuth 2.0 authentication flow
- Automatic token refresh
- Activity data fetching and processing
- Multi-user token management

### Training Metrics
- **TRIMP Calculation**: Training impulse based on heart rate zones
- **ACWR Analysis**: Acute-to-chronic workload ratio for injury prevention
- **Load Comparison**: Internal vs external load analysis
- **Trend Analysis**: Moving averages and performance trends

## Contributing

1. Follow the established directory structure
2. Backend changes go in `app/`
3. Frontend changes go in `frontend/`
4. Documentation updates go in `docs/`
5. Test both frontend and backend before deployment

## Support

For setup issues, see `docs/setup-guide.md`
For deployment questions, see `docs/Deployment_script.txt`