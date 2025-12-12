# Task List: TRIMP Calculation Enhancement

## Relevant Files

- `app/strava_training_load.py` - Contains the main `calculate_banister_trimp()` function that needs enhancement with heart rate stream processing capability
- `app/utils/feature_flags.py` - Feature flag system for gradual rollout (admin → beta users → general release)
- `app/feature_flags.py` - Legacy feature flag system that may need updates
- `app/db_utils.py` - Database utilities for schema validation and data operations
- `app/strava_app.py` - Main Flask application with admin routes and sync endpoints
- `app/settings_utils.py` - Contains existing TRIMP calculation utilities that may need integration
- `app/process_activities_for_date_range.py` - Activity processing logic that calls TRIMP calculations
- `app/test_trimp_enhancement.py` - Unit tests for the enhanced TRIMP calculation function
- `app/test_feature_flags.py` - Unit tests for feature flag functionality
- `app/test_hr_stream_processing.py` - Unit tests for heart rate stream data processing
- `app/test_historical_recalculation.py` - Unit tests for historical data processing
- `app/test_admin_controls.py` - Unit tests for admin dashboard controls

### Notes

- Unit tests should be placed alongside the code files they are testing
- Database schema changes should be executed manually via SQL editor following project rules
- Feature flags should follow existing patterns in `app/utils/feature_flags.py`
- All database operations must maintain multi-user data isolation with `user_id` filtering

## Tasks

- [x] 1.0 Enhance TRIMP Calculation Function
  - [x] 1.1 Modify `calculate_banister_trimp()` function signature to accept optional `hr_stream` parameter
  - [x] 1.2 Implement heart rate stream processing logic with individual sample calculations
  - [x] 1.3 Add fallback to average HR calculation when stream data is unavailable
  - [x] 1.4 Implement proper duration distribution across HR samples
  - [x] 1.5 Add comprehensive error handling and validation for HR stream data
  - [x] 1.6 Add logging to track which calculation method was used (stream vs average)
  - [x] 1.7 Ensure mathematical precision with proper rounding (2 decimal places)
  - [x] 1.8 Maintain backward compatibility with existing function calls

- [x] 2.0 Implement Database Schema Changes
  - [x] 2.1 Execute SQL commands to add `trimp_calculation_method` field to activities table
  - [x] 2.2 Execute SQL commands to add `hr_stream_sample_count` field to activities table
  - [x] 2.3 Execute SQL commands to add `trimp_processed_at` timestamp field to activities table
  - [x] 2.4 Execute SQL commands to create `hr_streams` table for efficient HR data storage
  - [x] 2.5 Add database indexes for performance optimization on new fields
  - [x] 2.6 Update `db_utils.py` with schema validation functions for new fields
  - [x] 2.7 Add helper functions for HR stream data storage and retrieval

- [x] 3.0 Add Feature Flag System for Gradual Rollout
  - [x] 3.1 Add `enhanced_trimp_calculation` feature flag to `app/utils/feature_flags.py`
  - [x] 3.2 Implement admin access (user_id=1) for early testing
  - [x] 3.3 Add beta user access for user_id=2 and user_id=3
  - [x] 3.4 Update TRIMP calculation calls to check feature flag before using enhanced method
  - [x] 3.5 Add logging to track feature flag usage and calculation method selection
  - [x] 3.6 Test feature flag system with admin user (user_id=1)

- [x] 4.0 Create Admin Controls and Dashboard
  - [x] 4.1 Add admin route `/admin/trimp-settings` for TRIMP calculation management
  - [x] 4.2 Create admin interface to toggle between calculation methods
  - [x] 4.3 Add admin controls for feature flag management (enable/disable for users)
  - [x] 4.4 Implement admin dashboard showing calculation method statistics
  - [x] 4.5 Add admin controls for triggering historical recalculation
  - [x] 4.6 Create admin monitoring dashboard for TRIMP calculation performance
  - [x] 4.7 Add admin validation tools for comparing calculation methods

- [x] 5.0 Implement Historical Data Processing
  - [x] 5.1 Create `recalculate_historical_trimp()` function for batch processing
  - [x] 5.2 Implement batch processing logic to prevent system overload
  - [x] 5.3 Add admin-triggered historical recalculation endpoint
  - [x] 5.4 Implement progress tracking for historical recalculation jobs
  - [x] 5.5 Add error handling and rollback capability for failed recalculations
  - [x] 5.6 Create historical recalculation status reporting
  - [x] 5.7 Implement data integrity validation during recalculation

- [x] 6.0 Add Comprehensive Testing Suite
  - [x] 6.1 Create unit tests for enhanced `calculate_banister_trimp()` function
  - [x] 6.2 Test heart rate stream processing with various sample rates
  - [x] 6.3 Test fallback to average HR calculation when stream data unavailable
  - [x] 6.4 Test edge cases (empty streams, invalid data, missing samples)
  - [x] 6.5 Create unit tests for feature flag functionality
  - [x] 6.6 Test admin controls and dashboard functionality
  - [x] 6.7 Create integration tests for historical data processing
  - [x] 6.8 Test database schema changes and data integrity
  - [x] 6.9 Create performance tests for large HR streams (2+ hour activities)

- [x] 7.0 Deploy with Monitoring and Validation
  - [x] 7.1 Deploy enhanced TRIMP calculation with feature flags disabled
  - [x] 7.2 Enable feature flag for admin user (user_id=1) for initial testing
  - [x] 7.3 Monitor calculation performance and accuracy metrics
  - [x] 7.4 Enable feature flag for beta users (user_id=2, user_id=3)
  - [x] 7.5 Collect feedback and validate accuracy against external sources
  - [x] 7.6 Enable feature flag for general release after validation
  - [x] 7.7 Monitor system performance and user experience metrics
  - [x] 7.8 Document deployment process and rollback procedures
