# New User Account Creation Process

## Overview

This document summarizes the complete new user account creation process for TrainingMonkey, including the intended flow, current implementation, and key components.

## Intended New User Experience Flow

### 1. Landing Page (`/`)
- **Purpose**: Initial entry point for new users
- **Content**: 
  - Hero section with value proposition
  - Call-to-action buttons
  - Feature highlights
  - Social proof/testimonials
- **Next Step**: "Get Started" button leads to `/getting-started`

### 2. Getting Started Page (`/getting-started`)
- **Purpose**: Onboarding introduction and progress tracking
- **Content**:
  - Welcome message
  - 4-step progress indicator
  - Step-by-step guidance
  - FAQ section
- **Next Step**: "Create Your Account" button leads to `/create-account`

### 3. Account Creation (`/create-account`)
- **Purpose**: User registration and account setup
- **Content**:
  - Registration form
  - Terms of service acceptance
  - Privacy policy acknowledgment
- **Next Step**: Account creation leads to `/connect-strava`

### 4. Strava Connection (`/connect-strava`)
- **Purpose**: OAuth integration with Strava
- **Content**:
  - Strava OAuth flow
  - Permission explanations
  - Connection status
- **Next Step**: Successful connection leads to `/goals-setup`

### 5. Goals Setup (`/goals-setup`)
- **Purpose**: Training goal configuration
- **Content**:
  - Goal setting form
  - Training preferences
  - Experience level selection
- **Next Step**: Goals setup leads to `/dashboard`

### 6. Dashboard (`/dashboard`)
- **Purpose**: Main application interface
- **Content**:
  - Training load visualization
  - AI recommendations
  - Progress tracking
  - Feature access

## Current Implementation Status

### ✅ Completed Components

1. **Landing Page** (`app/templates/landing.html`)
   - Fully implemented with modern design
   - Responsive layout
   - Clear call-to-action flow

2. **Getting Started Page** (`app/templates/getting_started_resources.html`)
   - 4-step progress indicator
   - Dynamic step completion logic
   - FAQ section
   - Proper state management

3. **Goals Setup Page** (`app/templates/goals_setup.html`)
   - Goal configuration form
   - Training preferences
   - Integration with onboarding flow

4. **Dashboard** (`/dashboard`)
   - React-based training load visualization
   - AI recommendations system
   - Static file serving properly configured

5. **Onboarding Manager** (`app/onboarding_manager.py`)
   - Step tracking and progression
   - Feature unlocking system
   - Database integration (PostgreSQL)

6. **Static File Serving** (`app/strava_app.py`)
   - Proper React build integration
   - Manifest and image file serving
   - Route configuration for all assets

### 🔄 Partially Implemented Components

1. **Account Creation** (`/create-account`)
   - Route exists but may need form implementation
   - Integration with user management system

2. **Strava Connection** (`/connect-strava`)
   - OAuth flow implemented
   - Legacy fallback system available
   - Token management system

### ❌ Missing Components

1. **User Registration Form**
   - Complete registration form implementation
   - Validation and error handling
   - Integration with database

2. **Account Verification**
   - Email verification system
   - Account activation process

3. **User Management Integration**
   - User creation in database
   - Session management
   - Authentication system

## Key Technical Components

### Database Schema
- **Users Table**: User account information
- **Onboarding Progress**: Step completion tracking
- **Feature Unlocking**: Progressive feature access
- **Strava Integration**: OAuth token storage

### Authentication Flow
1. **OAuth Integration**: Centralized Strava app
2. **Token Management**: Automatic refresh system
3. **Session Handling**: User state persistence
4. **Legacy Fallback**: Manual credential entry

### State Management
- **Onboarding Steps**: Progress tracking
- **Feature Access**: Unlocked features
- **User Context**: Current user state
- **Navigation Flow**: Step-to-step progression

## Database Rules Compliance

### PostgreSQL Requirements
- **Connection**: Direct cloud database connection
- **Syntax**: `%s` placeholders (not `?`)
- **Data Types**: PostgreSQL-specific types
- **Schema Management**: SQL Editor only

### Date Handling
- **Format**: `YYYY-MM-DD` format
- **Operations**: `datetime.date` objects
- **API Responses**: Consistent date formatting
- **Database Queries**: Proper date parameter binding

## File Structure

```
app/
├── templates/
│   ├── landing.html                    # Landing page
│   ├── getting_started_resources.html  # Getting started page
│   ├── goals_setup.html               # Goals setup page
│   └── strava_setup.html              # Legacy Strava setup
├── onboarding_manager.py              # Onboarding logic
├── strava_app.py                      # Main Flask app
└── build/                             # React build output
    ├── index.html
    ├── manifest.json
    ├── training-monkey-runner.webp
    └── static/
        ├── css/
        └── js/
```

## Route Configuration

### Main Routes
- `/` → Landing page
- `/getting-started` → Getting started page
- `/create-account` → Account creation (needs implementation)
- `/connect-strava` → Strava OAuth flow
- `/goals-setup` → Goals configuration
- `/dashboard` → Main application

### Static File Routes
- `/static/<filename>` → React build assets
- `/static/manifest.json` → App manifest
- `/static/training-monkey-runner.webp` → Runner image
- `/favicon.ico` → Favicon
- `/manifest.json` → Root manifest

## Next Steps for Completion

### Immediate Priorities
1. **Complete Account Creation Form**
   - Implement registration form
   - Add validation and error handling
   - Integrate with user management system

2. **User Management Integration**
   - User creation in database
   - Session management
   - Authentication system

3. **End-to-End Flow Testing**
   - Test complete user journey
   - Verify all redirects and state management
   - Validate database operations

### Future Enhancements
1. **Email Verification System**
   - Account activation emails
   - Verification token management

2. **Enhanced Onboarding**
   - Interactive tutorials
   - Progress saving
   - Resume capability

3. **Analytics Integration**
   - User journey tracking
   - Conversion metrics
   - A/B testing framework

## Conclusion

The new user account creation process is well-structured with a clear 4-step flow. The core components are implemented and functional, with proper database integration and static file serving. The main remaining work is completing the account creation form and integrating it with the user management system.

The implementation follows all project rules including PostgreSQL compliance, proper date handling, and direct cloud database connection. The onboarding system provides a smooth user experience with progressive feature unlocking and state management.
