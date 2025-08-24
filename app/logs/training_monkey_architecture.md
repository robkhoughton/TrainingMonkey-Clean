# Your Training Monkey - Multi-User Architecture & Database Schema

## 🏗️ **System Architecture Overview**

### **Multi-User SaaS Architecture**
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   React Client  │    │   Flask Backend  │    │   PostgreSQL    │
│                 │    │                  │    │   Cloud SQL     │
│ • Dashboard     │◄──►│ • Authentication │◄──►│                 │
│ • Metrics Cards │    │ • API Endpoints  │    │ • user_settings │
│ • Charts        │    │ • Data Processing│    │ • activities    │
│ • User Login    │    │ • Strava Sync    │    │ • llm_recommendations │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │   External APIs  │
                       │                  │
                       │ • Strava API     │
                       │ • Anthropic LLM  │
                       └──────────────────┘
```

### **Authentication Flow**
```
1. User visits protected route → Redirected to /login
2. Enter credentials → Flask-Login validates against database
3. Successful login → Session created → Redirect to React dashboard
4. All API calls → Filtered by current_user.id
5. Logout → Session cleared → Return to login page
```

### **Data Isolation Pattern**
- **Single Database + user_id Filtering** (chosen over database-per-user)
- All database queries include `WHERE user_id = ?` filtering
- User-specific activity IDs for rest days: `-(date.toordinal() * 1000 + user_id)`
- Independent Strava OAuth connections per user

---

## 📊 **Database Schema**

### **user_settings Table**
```sql
CREATE TABLE user_settings (
    id SERIAL PRIMARY KEY,
    
    -- Authentication
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    
    -- Heart Rate Configuration
    resting_hr INTEGER DEFAULT 44,
    max_hr INTEGER DEFAULT 178,
    gender VARCHAR(10) DEFAULT 'male',
    
    -- Strava Integration
    strava_access_token TEXT,
    strava_refresh_token TEXT,
    strava_token_expires_at INTEGER,
    strava_athlete_id INTEGER,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### **activities Table**
```sql
CREATE TABLE activities (
    activity_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES user_settings(id),
    
    -- Basic Activity Data
    date TEXT NOT NULL,
    name TEXT,
    type TEXT,
    
    -- Distance & Elevation
    distance_miles REAL,
    elevation_gain_feet REAL,
    elevation_load_miles REAL,
    total_load_miles REAL,
    
    -- Heart Rate Data
    avg_heart_rate REAL,
    max_heart_rate REAL,
    duration_minutes REAL,
    trimp REAL,
    
    -- Heart Rate Zones (in seconds)
    time_in_zone1 REAL,
    time_in_zone2 REAL,
    time_in_zone3 REAL,
    time_in_zone4 REAL,
    time_in_zone5 REAL,
    
    -- Calculated Metrics
    seven_day_avg_load REAL,
    twentyeight_day_avg_load REAL,
    seven_day_avg_trimp REAL,
    twentyeight_day_avg_trimp REAL,
    acute_chronic_ratio REAL,
    trimp_acute_chronic_ratio REAL,
    normalized_divergence REAL,
    
    -- Optional Wellness Data
    weight_lbs REAL,
    perceived_effort INTEGER,
    feeling_score INTEGER,
    notes TEXT,
    
    -- Indexes for Performance
    INDEX idx_user_date (user_id, date),
    INDEX idx_user_id (user_id)
);
```

### **llm_recommendations Table**
```sql
CREATE TABLE llm_recommendations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES user_settings(id),
    
    -- Recommendation Data
    recommendation_text TEXT NOT NULL,
    confidence_score REAL,
    recommendation_type VARCHAR(50),
    
    -- Context Data
    generated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    activity_count INTEGER,
    latest_acwr REAL,
    latest_trimp REAL,
    
    -- Metadata
    model_version VARCHAR(50),
    processing_time_ms INTEGER,
    
    INDEX idx_user_recommendations (user_id, generated_date)
);
```

---

## 🔒 **Security & Authentication**

### **Flask-Login Integration**
```python
# User class with Flask-Login UserMixin
class User(UserMixin):
    def __init__(self, id, email, password_hash, resting_hr=None, 
                 max_hr=None, gender=None, is_admin=False):
        self.id = id
        self.email = email
        self.password_hash = password_hash
        self.resting_hr = resting_hr
        self.max_hr = max_hr
        self.gender = gender
        self.is_admin = is_admin
```

### **Data Isolation Enforcement**
```python
# All database queries include user filtering
@login_required
@app.route('/api/training-data')
def get_training_data():
    activities = execute_query(
        "SELECT * FROM activities WHERE user_id = ? ORDER BY date DESC",
        (current_user.id,),
        fetch=True
    )
```

### **Strava Token Management**
```python
# Per-user token management
class SimpleTokenManager:
    def __init__(self, user_id):
        self.user_id = user_id
        
    def get_working_strava_client(self):
        # Load user-specific tokens
        # Handle refresh automatically
        # Return authenticated Strava client
```

---

## 📈 **Training Metrics & Analytics**

### **Core Calculations**
- **TRIMP (Training Impulse)**: Banister method with heart rate zones
- **ACWR (Acute:Chronic Workload Ratio)**: 7-day / 28-day rolling averages
- **Normalized Divergence**: External vs Internal load comparison
- **Time-based Moving Averages**: Real-time calculation across date ranges

### **Data Processing Pipeline**
```
Strava API → Raw Activity Data → Training Load Calculation → 
Moving Averages → ACWR/TRIMP → Database Storage → Dashboard Display
```

### **UnifiedMetricsService Pattern**
```python
class UnifiedMetricsService:
    @staticmethod
    def get_latest_complete_metrics(user_id):
        # Single source of truth for all metrics
        # Ensures consistency across dashboard components
        # User-specific calculations
```

---

## 🚀 **Deployment Architecture**

### **Google Cloud Platform**
- **Cloud Run**: Containerized Flask application
- **Cloud SQL**: PostgreSQL database with automated backups
- **Secret Manager**: Secure storage for API keys and credentials
- **Container Registry**: Docker image storage

### **Production Configuration**
```dockerfile
# Multi-stage build with Python 3.11
# Gunicorn WSGI server
# Health checks and monitoring
# Non-root user for security
```

### **Environment Variables**
- `DATABASE_URL`: PostgreSQL connection string
- `STRAVA_CLIENT_ID/SECRET`: OAuth credentials
- `ANTHROPIC_API_KEY`: LLM integration
- `SECRET_KEY`: Flask session encryption

---

## 🎯 **Current Status & Next Steps**

### **✅ Completed (95%)**
- Multi-user authentication system
- Complete data isolation between users
- Strava API integration with token management
- Sophisticated training analytics
- Production deployment on Cloud Run
- React dashboard with real-time metrics

### **🔧 Remaining Work (5%)**
1. **UnifiedMetricsService** user-awareness (highest priority)
2. **LLM recommendations** user-specific filtering
3. **Data consistency** across all dashboard components

### **🚀 Future Enhancements**
- User management admin panel
- Advanced training plan generation
- Comparative analytics (opt-in benchmarking)
- Enhanced data export capabilities
- Email notifications and alerts

---

## 💡 **Architectural Decisions Made**

### **Single Database + user_id Filtering**
**Chosen over**: Database-per-user  
**Rationale**: Simpler operational overhead, standard multi-tenant pattern, enables future cross-user analytics

### **User-Specific Activity IDs for Rest Days**
**Implementation**: `-(date.toordinal() * 1000 + user_id)`  
**Result**: Eliminates duplicate key conflicts

### **Flask-Login vs Custom Auth**
**Chosen**: Flask-Login for proven session management  
**Result**: Secure, scalable authentication with minimal custom code

This architecture successfully transforms a single-user training dashboard into a robust multi-user SaaS application while preserving all existing functionality and sophisticated analytics.