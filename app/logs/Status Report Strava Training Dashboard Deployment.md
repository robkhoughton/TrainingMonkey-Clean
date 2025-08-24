# **Status Report: Strava Training Dashboard Cloud Deployment**

## **Current Infrastructure Assessment**

### **✅ Existing Cloud Resources (Ready to Use)**
- **Database**: `train-monk-db` (PostgreSQL 14, us-central1-b, RUNNABLE)
  - Tier: db-custom-4-16384 (4 vCPU, 16GB RAM)
  - Private IP: 10.109.208.9 (secure internal networking)
  - Public IP: Disabled (good security posture)
- **Project**: `dev-ruler-460822-e8` (properly configured)
- **Secret Manager**: 6 existing secrets (infrastructure ready)
- **Cloud Run Services**: 3 existing services (deployment patterns established)

### **✅ Existing Strava Application Files**
- `strava_app.py` - Main Flask application (functional)
- `strava_training_load.py` - Core data processing logic
- `strava_requirements.txt` - Dependencies defined
- `Dockerfile.strava.txt` - Container configuration
- `deploy_strava.bat` - Deployment script template
- `strava_config.json` - OAuth credentials (Client ID: 47238)

### **✅ Proven Deployment Pattern**
Your existing Garmin services demonstrate:
- Successful Cloud Run deployments
- Database connectivity working
- Secret Manager integration functional
- Container registry operations established

## **Recommended Deployment Strategy: Single-User Personal Dashboard**

### **Phase 1: Secret Management Setup (30 minutes)**
**Objective**: Add Strava credentials to existing Secret Manager

**Tasks for Junior Engineer**:
```batch
REM Add Strava app credentials (use existing values from strava_config.json)
echo 47238 | gcloud secrets create strava-client-id --data-file=-
echo 65cb63b7b469b09d96ce72124fa7af7af4bf80e3 | gcloud secrets create strava-client-secret --data-file=-

REM Create app secret key for session management
powershell -Command "[System.Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes((New-Guid).ToString()))" | gcloud secrets create app-secret-key --data-file=-
```

**Validation**:
- Verify secrets created: `gcloud secrets list | findstr strava`
- Confirm access: `gcloud secrets versions access latest --secret="strava-client-id"`

### **Phase 2: Database Schema Preparation (45 minutes)**
**Objective**: Add minimal single-user Strava support to existing database

**Tasks for Junior Engineer**:
1. **Connect to existing database**:
   ```batch
   gcloud sql connect train-monk-db --user=postgres
   ```

2. **Check existing schema and add Strava columns**:
   ```sql
   -- Check if user_settings table exists
   \dt user_settings
   
   -- If it exists, add Strava columns
   ALTER TABLE user_settings ADD COLUMN IF NOT EXISTS strava_access_token TEXT;
   ALTER TABLE user_settings ADD COLUMN IF NOT EXISTS strava_refresh_token TEXT;
   ALTER TABLE user_settings ADD COLUMN IF NOT EXISTS strava_token_expires_at BIGINT;
   ALTER TABLE user_settings ADD COLUMN IF NOT EXISTS strava_athlete_id BIGINT;
   
   -- If user_settings doesn't exist, create it
   CREATE TABLE IF NOT EXISTS user_settings (
       id SERIAL PRIMARY KEY,
       email VARCHAR(255) UNIQUE,
       resting_hr INTEGER DEFAULT 44,
       max_hr INTEGER DEFAULT 178,
       gender VARCHAR(10) DEFAULT 'male',
       strava_access_token TEXT,
       strava_refresh_token TEXT,
       strava_token_expires_at BIGINT,
       strava_athlete_id BIGINT,
       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   );
   
   -- Insert/update personal user record
   INSERT INTO user_settings (email, resting_hr, max_hr, gender) 
   VALUES ('rob.houghton.ca@gmail.com', 44, 178, 'male')
   ON CONFLICT (email) DO NOTHING;
   ```

3. **Ensure activities table has user isolation**:
   ```sql
   -- Check activities table structure
   \d activities
   
   -- Add user_id if missing (for future multi-user support)
   ALTER TABLE activities ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES user_settings(id);
   
   -- Set default user for existing activities
   UPDATE activities SET user_id = 1 WHERE user_id IS NULL;
   ```

**Validation**:
- Confirm tables exist: `\dt`
- Verify columns added: `\d user_settings`
- Check user record: `SELECT * FROM user_settings;`

### **Phase 3: Application Configuration (60 minutes)**
**Objective**: Modify strava_app.py for single-user cloud deployment

**Key Changes Needed**:
1. **Remove multi-user complexity**: Hardcode user_id = 1
2. **Add Secret Manager integration**: Replace local config file reading
3. **Update database connection**: Use existing `database-url` secret
4. **Simplify OAuth flow**: Direct to single user account
5. **Add Cloud Run health checks**: `/health` endpoint
6. **Ensure compatibility**: Work with existing `db_utils.py` and `strava_training_load.py`

**Files to Modify**:
- `strava_app.py` (main application)
- Potentially update `db_utils.py` if needed for cloud compatibility

### **Phase 4: Container Preparation (30 minutes)**
**Objective**: Prepare Docker container using existing patterns

**Tasks for Junior Engineer**:
1. **Review existing Dockerfile.strava.txt**
2. **Update strava_requirements.txt** for cloud deployment:
   ```
   # Add to existing requirements
   google-cloud-secret-manager==2.16.4
   google-cloud-sql-connector==1.4.3
   ```
3. **Test local container build**:
   ```batch
   docker build -f Dockerfile.strava.txt -t test-strava-app .
   docker run -p 8080:8080 test-strava-app
   ```

### **Phase 5: Cloud Deployment (45 minutes)**
**Objective**: Deploy using proven deployment pattern from existing services

**Tasks for Junior Engineer**:
1. **Modify deploy_strava.bat** to match existing successful patterns:
   - Use existing database instance: `train-monk-db`
   - Reference existing secrets: `database-url`
   - Follow same Cloud Run configuration as `training-monkey` service

2. **Deploy command structure** (Windows batch compatible):
   ```batch
   REM Build and push image
   docker build -f Dockerfile.strava.txt -t gcr.io/dev-ruler-460822-e8/strava-training-personal .
   docker push gcr.io/dev-ruler-460822-e8/strava-training-personal
   
   REM Deploy to Cloud Run
   gcloud run deploy strava-training-personal ^
     --image gcr.io/dev-ruler-460822-e8/strava-training-personal ^
     --platform managed ^
     --region us-central1 ^
     --allow-unauthenticated ^
     --add-cloudsql-instances dev-ruler-460822-e8:us-central1:train-monk-db ^
     --update-secrets DATABASE_URL=database-url:latest,STRAVA_CLIENT_ID=strava-client-id:latest,STRAVA_CLIENT_SECRET=strava-client-secret:latest,SECRET_KEY=app-secret-key:latest ^
     --memory 512Mi ^
     --cpu 1 ^
     --timeout 300 ^
     --max-instances 3 ^
     --port 8080
   ```

### **Phase 6: Testing & Validation (60 minutes)**
**Objective**: Verify complete functionality

**Test Sequence**:
1. **Health checks**:
   - Service responds: `curl https://[service-url]/health`
   - Database connectivity confirmed
   - Secret access working

2. **Strava OAuth flow**:
   - Navigate to service URL
   - Complete Strava authorization
   - Verify tokens saved to database

3. **Data sync functionality**:
   - Trigger activity sync
   - Confirm activities appear in database
   - Verify training metrics calculate correctly

4. **Dashboard display**:
   - All existing functionality preserved
   - Charts and metrics display
   - Performance acceptable (<2 second load times)

## **Resource Requirements**

### **Estimated Costs** (Personal Single-User)
- **Incremental cost**: ~$5-10/month (sharing existing database)
- **Existing infrastructure**: Already paid for
- **No additional Cloud SQL charges**: Using existing `train-monk-db` instance

### **Timeline Estimate**
- **Setup and configuration**: 3-4 hours
- **Testing and validation**: 1-2 hours
- **Troubleshooting buffer**: 2-3 hours
- **Total project time**: 6-9 hours (1-1.5 working days)

## **Risk Assessment**

### **Low Risk Items** ✅
- Database connectivity (proven with 3 existing services)
- Secret Manager usage (6 secrets already managed)
- Container deployment (established patterns exist)
- Strava API integration (working locally)

### **Medium Risk Items** ⚠️
- OAuth callback URL changes (cloud domain vs localhost)
- Database schema modifications (should backup first)
- Environment variable differences (cloud vs local)

### **High Risk Items** 🚨
- None identified (leveraging proven infrastructure)

### **Mitigation Strategies**
- **Database backup**: Before any schema changes
- **Gradual deployment**: Test each phase before proceeding
- **Rollback plan**: Maintain local working version
- **Follow existing patterns**: Mirror successful `training-monkey` service

## **Success Criteria**

### **Deployment Success**
1. ✅ Cloud Run service starts and responds to health checks
2. ✅ Database connection established from cloud service
3. ✅ Secret Manager integration working

### **Functional Success**
1. ✅ Strava OAuth flow completes successfully
2. ✅ Activities sync from Strava to cloud database
3. ✅ Training metrics display correctly on dashboard
4. ✅ All existing local functionality preserved

### **Performance Success**
1. ✅ Dashboard loads in <3 seconds
2. ✅ Sync operations complete in <30 seconds
3. ✅ 99%+ uptime (following existing service patterns)

## **Implementation Guidance for Junior Engineer**

### **Pre-Implementation Checklist**
- [ ] Verify access to Google Cloud Console
- [ ] Confirm gcloud CLI configured for project `dev-ruler-460822-e8`
- [ ] Test database connectivity: `gcloud sql connect train-monk-db --user=postgres`
- [ ] Review existing successful services for patterns

### **Implementation Order**
1. **Start with Phase 1** (secrets) - lowest risk, immediate validation
2. **Phase 2** (database) - create backup first
3. **Phase 3** (application) - work incrementally
4. **Phase 4** (container) - test locally first
5. **Phase 5** (deployment) - follow existing patterns exactly
6. **Phase 6** (validation) - comprehensive testing

### **When to Escalate**
- Database connection issues persist after 30 minutes
- Container build fails repeatedly
- OAuth flow doesn't work after cloud deployment
- Any error messages not similar to existing service patterns

## **Post-Deployment: Path to Multi-User**

Once single-user deployment is successful:
1. **Add authentication system** (Flask-Login)
2. **Implement user registration** 
3. **Update database queries** to filter by user_id
4. **Add user management interface**

This foundation provides a solid, proven path forward with minimal risk and maximum reuse of your existing, working infrastructure.