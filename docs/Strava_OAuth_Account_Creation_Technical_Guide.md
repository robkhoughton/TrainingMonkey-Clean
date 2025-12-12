# Strava OAuth Account Creation Technical Guide

## Overview

This document provides a comprehensive technical guide for how Your Training Monkey handles new user account creation through the Strava OAuth integration flow.

## Process Flow

### 1. Landing Page Entry
- New users start at `/landing` (marketing page)
- Click "Connect with Strava" button
- Redirected to `/auth/strava-signup`

### 2. Strava OAuth Initiation
- System redirects to Strava OAuth with:
  - `client_id`: From environment variables or session
  - `redirect_uri`: `https://yourtrainingmonkey.com/oauth-callback`
  - `scope`: `read,activity:read_all`
  - `approval_prompt`: `force`

### 3. OAuth Callback Processing (`/oauth-callback`)

#### User Detection Logic
The system checks if the user already exists by:

1. **Email Check**: Look for `strava_{athlete_id}@training-monkey.com`
2. **Athlete ID Check**: If not found by email, check if any user has the Strava athlete ID

```python
existing_user = User.get_by_email(f"strava_{athlete_id}@training-monkey.com")

if not existing_user:
    athlete_query = """
        SELECT id, email FROM user_settings 
        WHERE strava_athlete_id = %s
    """
    athlete_result = db_utils.execute_query(athlete_query, (int(athlete_id),), fetch=True)
    if athlete_result and athlete_result[0]:
        existing_user = User.get(athlete_result[0]['id'])
```

#### Existing User Path
If user exists:
- Log them into existing account
- Update Strava tokens in database
- Show "Welcome back!" message
- Redirect to `/welcome-post-strava`

#### New User Path
If user doesn't exist:

##### Account Creation
```python
# Generate secure credentials
temp_password = secrets.token_urlsafe(16)  # 16-character random password
password_hash = generate_password_hash(temp_password)

# Create email from Strava athlete ID
email = f"strava_{athlete_id}@training-monkey.com"

# Extract user data from Strava
first_name = getattr(athlete, 'firstname', '')
last_name = getattr(athlete, 'lastname', '')
gender = getattr(athlete, 'sex', 'male')
resting_hr = getattr(athlete, 'resting_hr', None) or 44
max_hr = getattr(athlete, 'max_hr', None) or 178
```

##### Database Insert
```sql
INSERT INTO user_settings (
    email, password_hash, is_admin, 
    resting_hr, max_hr, gender,
    strava_athlete_id, strava_access_token, strava_refresh_token, strava_token_expires_at
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
```

##### Automatic Login
```python
# Log in the new user automatically
login_user(new_user)
session['is_first_login'] = True
session['signup_source'] = 'landing_page'

flash(f'Welcome to Your Training Monkey, {first_name}! Let\'s analyze your training data.', 'success')
return redirect('/welcome-post-strava')
```

## Generated Credentials

### Email Format
- **Pattern**: `strava_{athlete_id}@training-monkey.com`
- **Example**: `strava_12345678@training-monkey.com`
- **Source**: Strava athlete ID from OAuth response

### Password
- **Generation**: `secrets.token_urlsafe(16)`
- **Length**: 16 characters
- **Character Set**: URL-safe base64 (letters, numbers, hyphens, underscores)
- **Security**: Cryptographically secure random generation
- **Storage**: Hashed using Werkzeug's `generate_password_hash()`

### Important Note
**Users never need to know or use the generated password** - the system automatically logs them in after account creation.

## Post-Creation Flow

### 1. Welcome Page (`/welcome-post-strava`)
- Shows success message with user's first name
- Displays onboarding progress (3 steps completed)
- Provides next steps:
  - Set training goals
  - Let system analyze training data
  - Start receiving AI recommendations
- Action buttons: "Set My Goals" and "View Dashboard"

### 2. Onboarding System
- Session flags set: `is_first_login = True`, `signup_source = 'landing_page'`
- Comprehensive onboarding manager with multiple steps:
  - `WELCOME`
  - `STRAVA_CONNECTED`
  - `FIRST_ACTIVITY`
  - `DATA_SYNC`
  - `DASHBOARD_INTRO`
  - `FEATURES_TOUR`
  - `GOALS_SETUP`
  - `FIRST_RECOMMENDATION`
  - `JOURNAL_INTRO`
  - `COMPLETED`

### 3. Data Requirements Check
- System checks if user has 14+ days of training data
- If sufficient data: Redirect to dashboard with `highlight=divergence&new_user=true`
- If insufficient data: Show onboarding page with data collection progress

## Security Considerations

### Password Security
- Generated passwords are cryptographically secure
- Passwords are immediately hashed before database storage
- Original password is never stored or logged

### OAuth Security
- Uses Strava's official OAuth 2.0 flow
- Tokens are stored securely in database
- Token refresh mechanism implemented

### Session Management
- Automatic login after account creation
- Session flags track onboarding state
- CSRF protection on sensitive operations

## Database Schema

### user_settings Table Fields Used
- `id` (SERIAL PRIMARY KEY)
- `email` (VARCHAR)
- `password_hash` (VARCHAR)
- `is_admin` (BOOLEAN)
- `resting_hr` (INTEGER)
- `max_hr` (INTEGER)
- `gender` (VARCHAR)
- `strava_athlete_id` (INTEGER)
- `strava_access_token` (VARCHAR)
- `strava_refresh_token` (VARCHAR)
- `strava_token_expires_at` (TIMESTAMP)

## Error Handling

### OAuth Errors
- Missing authorization code: 400 error
- Missing Strava credentials: 400 error
- Token exchange failure: 500 error

### Database Errors
- Account creation failure: Redirect to home with error message
- User loading failure: Redirect to home with error message
- Token update failure: Redirect to Strava setup with error message

### User Experience
- All errors show user-friendly flash messages
- Graceful fallbacks to prevent system crashes
- Comprehensive logging for debugging

## Testing Scenarios

### Scenario 1: Truly New User
1. User has Strava account but no TrainingMonkey account
2. Goes through OAuth flow
3. New account created with generated credentials
4. Automatically logged in and redirected to welcome page

### Scenario 2: Existing User
1. User already has TrainingMonkey account linked to Strava
2. Goes through OAuth flow
3. Logged into existing account
4. Strava tokens updated
5. Redirected to welcome page with "Welcome back!" message

### Scenario 3: User with Different Strava Account
1. User has TrainingMonkey account linked to different Strava account
2. Goes through OAuth with new Strava account
3. New TrainingMonkey account created
4. User now has two separate TrainingMonkey accounts

## Implementation Notes

### Code Location
- Main OAuth callback: `app/strava_app.py` lines 210-351
- User model: `app/auth.py`
- Onboarding system: `app/onboarding_manager.py`
- Welcome page template: `app/templates/welcome_post_strava.html`

### Dependencies
- Flask-Login for session management
- Werkzeug for password hashing
- Stravalib for Strava API integration
- PostgreSQL for data storage

### Environment Variables Required
- `STRAVA_CLIENT_ID`
- `STRAVA_CLIENT_SECRET`
- `SECRET_KEY` (for Flask sessions)

## Conclusion

The new user account creation process is fully automated and secure. Users never need to manually create accounts or remember generated passwords. The system seamlessly integrates with Strava OAuth to provide a smooth onboarding experience while maintaining security best practices.
