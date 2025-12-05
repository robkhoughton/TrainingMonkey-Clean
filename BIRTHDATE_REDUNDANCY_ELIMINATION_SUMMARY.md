# Birthdate Data Collection Redundancy Elimination

## Summary
Successfully eliminated redundant data collection for age, email, and gender by consolidating birthdate collection to onboarding and removing duplicate fields from settings.

## Changes Made

### 1. Onboarding Form (welcome_post_strava.html)
**Before:**
- Collected numeric age (13-100)
- Auto-calculated max HR from age

**After:**
- Collects birth month (dropdown: January - December)
- Collects birth year (dropdown: current year - 13 to current year - 100)
- Auto-calculates max HR from birth year
- Stores birthdate as YYYY-MM-01 (day=1 for privacy)
- Privacy note: "month/year only for privacy"

### 2. Onboarding Backend (strava_app.py:9880 - welcome_stage1)
**Before:**
- Accepted `age` parameter
- Stored only `age` in database

**After:**
- Accepts `birth_month` and `birth_year` parameters
- Creates birthdate: `date(birth_year, birth_month, 1)`
- Calculates age from birthdate using `calculate_age_from_birthdate()`
- Stores both `birthdate` and calculated `age` in database

### 3. Settings Profile Page (settings_profile.html)
**Before:**
- Showed email input (redundant with signup)
- Showed birthdate date picker (full date)
- Showed gender selector (redundant with onboarding)

**After:**
- Only shows birth month dropdown
- Only shows birth year dropdown
- Email and gender removed (already set during signup/onboarding)
- Pre-selects current values from database
- Updated meta description

### 4. Settings Profile Backend (strava_app.py:6725 - update_profile_settings)
**Before:**
- Accepted and updated: email, birthdate (full date), gender
- Required all three fields

**After:**
- Accepts only: birth_month, birth_year
- Validates month (1-12) and year (reasonable age range)
- Creates birthdate with day=1 for privacy
- Calculates and stores both birthdate and age

## Privacy Enhancement
- **Before:** Could collect full birthdate (day/month/year)
- **After:** Only collects month/year, stores as YYYY-MM-01
- **Impact:** +/- 1 month makes no difference in training calculations
- **Benefit:** Reduced PII (Personally Identifiable Information)

## Data Flow
1. **Signup:** User provides email and password → stored in `user_settings`
2. **Onboarding:** User provides birth month/year, gender, training data → stored in `user_settings`
3. **Settings:** User can only update birth month/year → updates `birthdate` and `age` in `user_settings`

## Database Schema (user_settings table)
- `email` (TEXT) - Set at signup, no longer editable in settings
- `gender` (TEXT) - Set at onboarding, no longer editable in settings
- `birthdate` (DATE) - Collected as month/year, stored as YYYY-MM-01
- `age` (INTEGER) - Auto-calculated from birthdate for backward compatibility

## Testing Results
All tests pass:
- ✓ Birthdate stored as YYYY-MM-01 (day=1 for privacy)
- ✓ Age calculation works correctly with month/year
- ✓ Database structure supports all required fields
- ✓ Email and gender remain in database (set once, not editable)
- ✓ Settings page only shows/updates birthdate

## Current State
- **45 total users** in database
- **44 users** have age set (from old onboarding)
- **5 users** have birthdate set (from settings)
- All new users will have birthdate set during onboarding
- Existing users can update to birth month/year in settings

## Files Modified
1. `app/templates/welcome_post_strava.html` - Onboarding form
2. `app/templates/settings_profile.html` - Settings profile page
3. `app/strava_app.py` - Both onboarding and settings backends
4. Created `app/test_birthdate_flow.py` - Test verification script

## Backward Compatibility
- Both `age` and `birthdate` fields maintained in database
- Age calculation function works with existing full-date birthdates
- Existing users with only age will work normally
- Age is recalculated whenever birthdate is updated
