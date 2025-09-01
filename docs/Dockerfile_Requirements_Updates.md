# Dockerfile and Requirements Updates for Phase 1

**Date:** December 2024  
**Purpose:** Document necessary changes to support Phase 1 OAuth transition implementation  
**Status:** Ready for deployment  

## Overview

This document outlines the required updates to the Dockerfile and requirements file to support the Phase 1 implementation of the OAuth transition to centralized API access.

## Dockerfile Updates

### New Python Modules Added

The following new Python modules must be copied to the Docker container:

#### OAuth and Security Modules:
```dockerfile
# Copy Phase 1 OAuth and Security modules
COPY oauth_error_handler.py .
COPY secure_token_storage.py .
COPY oauth_rate_limiter.py .
```

#### Legal and Registration Modules:
```dockerfile
# Copy Phase 1 Legal and Registration modules
COPY legal_document_versioning.py .
COPY legal_compliance.py .
COPY legal_validation.py .
COPY legal_audit_trail.py .
COPY registration_validation.py .
COPY password_generator.py .
COPY user_account_manager.py .
COPY registration_status_tracker.py .
COPY registration_session_manager.py .
COPY csrf_protection.py .
```

#### Configuration Files:
```dockerfile
# Copy the actual configuration files
COPY config.json .
COPY strava_config.json .  # NEW: Centralized OAuth credentials
COPY Training_Metrics_Reference_Guide.md .
```

### Template Updates

The templates directory now includes new legal and onboarding templates:
```dockerfile
# Copy templates directory (includes new legal and onboarding templates)
COPY templates/ /app/templates/
```

**New templates included:**
- `templates/legal/terms.html`
- `templates/legal/privacy.html`
- `templates/legal/disclaimer.html`
- `templates/signup.html`
- `templates/onboarding/strava_welcome.html`
- `templates/oauth_success.html`

## Requirements File Updates

### Current Dependencies Analysis

The current `strava_requirements.txt` already includes all necessary dependencies for Phase 1:

#### Core Dependencies (Already Present):
- `flask>=2.3.0` - Web framework
- `Flask-Login>=0.6.0` - User authentication
- `cryptography>=3.4.8` - **Critical for secure token storage**
- `psycopg2-binary>=2.9.0` - Database operations
- `python-dotenv>=1.0.0` - Environment variable management
- `stravalib>=1.5.0` - Strava API integration
- `requests>=2.31.0` - HTTP requests
- `gunicorn>=21.0.0` - Production server

#### No Additional Dependencies Required

All Phase 1 functionality uses only the existing dependencies. The implementation leverages:
- **cryptography** for Fernet encryption in secure token storage
- **Flask-Login** for user authentication and session management
- **psycopg2-binary** for database operations and audit logging
- **python-dotenv** for environment variable management
- **stravalib** for OAuth token management and API calls

## Deployment Checklist

### Pre-Deployment Verification:

1. **File Existence Check:**
   ```bash
   # Verify all new Python modules exist
   ls -la *.py | grep -E "(oauth|legal|registration|secure|csrf)"
   
   # Verify configuration files exist
   ls -la strava_config.json
   
   # Verify new templates exist
   ls -la templates/legal/
   ls -la templates/onboarding/
   ```

2. **Import Test:**
   ```python
   # Test imports in Python
   python -c "
   from oauth_error_handler import handle_oauth_error
   from secure_token_storage import SecureTokenStorage
   from oauth_rate_limiter import rate_limiter
   from legal_compliance import LegalCompliance
   print('All imports successful')
   "
   ```

3. **Configuration Validation:**
   ```python
   # Validate strava_config.json
   import json
   with open('strava_config.json', 'r') as f:
       config = json.load(f)
       assert 'client_id' in config
       assert 'client_secret' in config
       print('Configuration valid')
   ```

### Docker Build Verification:

1. **Build Test:**
   ```bash
   docker build -f Dockerfile.strava -t training-monkey-phase1 .
   ```

2. **Container Test:**
   ```bash
   docker run --rm -p 8080:8080 training-monkey-phase1
   ```

3. **Health Check:**
   ```bash
   curl -f http://localhost:8080/health
   ```

## Configuration Requirements

### Environment Variables:

The following environment variables should be set in the deployment environment:

```bash
# Required for Phase 1
SECRET_KEY=your_app_secret_key
DATABASE_URL=your_database_url

# Optional (fallback for OAuth)
STRAVA_CLIENT_ID=your_client_id
STRAVA_CLIENT_SECRET=your_client_secret

# Optional (for enhanced security)
TOKEN_ENCRYPTION_KEY=your_encryption_key
TOKEN_INTEGRITY_SECRET=your_integrity_secret
```

### Configuration File:

**`strava_config.json`** must be present with:
```json
{
    "client_id": "your_strava_client_id",
    "client_secret": "your_strava_client_secret",
    "resting_hr": 44,
    "max_hr": 178,
    "gender": "male"
}
```

## Security Considerations

### File Permissions:
- Ensure `strava_config.json` has appropriate permissions (readable by app user)
- Configuration files should not be world-readable

### Environment Variables:
- Use secure environment variable management
- Avoid hardcoding secrets in Dockerfile
- Consider using secret management services

### Database Access:
- Ensure database user has permissions for new tables
- Verify connection string includes necessary privileges

## Troubleshooting

### Common Issues:

#### Import Errors:
```bash
# Check if all modules are copied
docker exec -it container_name ls -la /app/*.py

# Check Python path
docker exec -it container_name python -c "import sys; print(sys.path)"
```

#### Configuration Errors:
```bash
# Check if strava_config.json exists
docker exec -it container_name ls -la /app/strava_config.json

# Validate configuration
docker exec -it container_name python -c "
import json
with open('strava_config.json', 'r') as f:
    config = json.load(f)
    print('Config valid:', 'client_id' in config)
"
```

#### Database Errors:
```bash
# Check database connection
docker exec -it container_name python -c "
import db_utils
result = db_utils.execute_query('SELECT 1')
print('DB connection:', result is not None)
"
```

### Debug Endpoints:

After deployment, verify functionality using:
- `GET /health` - Basic health check
- `GET /api/token/status` - Token management status
- `GET /api/oauth-security/status` - OAuth security status
- `GET /api/legal/status` - Legal compliance status

## Performance Considerations

### Memory Usage:
- New modules add minimal memory overhead
- Rate limiting uses in-memory storage (consider Redis for high traffic)
- Audit logging may increase database usage

### Startup Time:
- Additional imports may slightly increase startup time
- Consider lazy loading for non-critical modules

### Security Overhead:
- Token encryption adds minimal CPU overhead
- Rate limiting checks are fast (in-memory)
- Audit logging is asynchronous

## Rollback Plan

If issues arise, the following rollback steps can be taken:

1. **Database Rollback:**
   ```sql
   -- Drop new tables (if needed)
   DROP TABLE IF EXISTS legal_compliance;
   DROP TABLE IF EXISTS oauth_security_log;
   DROP TABLE IF EXISTS token_audit_log;
   
   -- Remove new columns (if needed)
   ALTER TABLE user_settings DROP COLUMN IF EXISTS legal_terms_accepted_at;
   -- ... (other columns)
   ```

2. **Code Rollback:**
   - Revert to previous Dockerfile
   - Remove new Python modules
   - Restore previous strava_app.py

3. **Configuration Rollback:**
   - Remove strava_config.json
   - Restore previous environment variables

## Conclusion

The Dockerfile and requirements updates are minimal and well-contained. All necessary dependencies are already present, and the new modules integrate seamlessly with the existing architecture. The deployment should proceed smoothly with proper testing and monitoring.

---

**Document Version:** 1.0  
**Last Updated:** December 2024  
**Maintained By:** Development Team
