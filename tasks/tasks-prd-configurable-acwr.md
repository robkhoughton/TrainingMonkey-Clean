# Task List: Configurable ACWR with Exponential Decay

## Relevant Files

- `app/acwr_configuration_schema.sql` - Database schema for ACWR configurations (already exists)
- `app/acwr_configuration_service.py` - Core service for ACWR configuration management (already exists)
- `app/strava_app.py` - Main Flask application with admin API endpoints
- `app/templates/admin_acwr_configuration.html` - Admin interface for ACWR configuration management
- `app/static/js/admin_acwr_configuration.js` - Frontend JavaScript for admin interface
- `app/utils/feature_flags.py` - Feature flag system for gradual rollout
- `app/strava_training_load.py` - Main ACWR calculation functions
- `app/garmin_training_load.py` - Garmin-specific ACWR calculations
- `app/unified_metrics_service.py` - Metrics aggregation service
- `app/settings_utils.py` - Settings validation and recalculation
- `app/acwr_visualization_service.py` - Service for generating visualization data
- `app/acwr_migration_service.py` - Service for historical data migration
- `app/test_acwr_configuration_service.py` - Unit tests for ACWR configuration service
- `app/test_acwr_visualization_service.py` - Unit tests for visualization service
- `app/test_acwr_migration_service.py` - Unit tests for migration service

### Notes

- The database schema and core service already exist from previous work
- Integration with existing feature flag system is required
- Admin interface follows existing patterns from TRIMP enhancement features
- Unit tests should be placed alongside the code files they are testing
- Use `python -m pytest [optional/path/to/test/file]` to run tests

## Tasks

### Phase 1: Foundation (Weeks 1-2)

- [ ] 1.0 Database Schema and Core Infrastructure
  - [ ] 1.1 Execute the existing ACWR configuration schema SQL to create tables
  - [ ] 1.2 Verify database constraints and indexes are properly created
  - [ ] 1.3 Insert default configuration with 42-day chronic period and 0.05 decay rate
  - [ ] 1.4 Test database connectivity and table access from Python services
  - [ ] 1.5 Create database migration script for production deployment
  - [ ] 1.6 Validate existing acwr_configuration_service.py functionality
  - [ ] 1.7 Test core service methods (get_user_configuration, create_configuration, assign_configuration_to_user)

- [ ] 2.0 Feature Flag Integration and Rollout Control
  - [ ] 2.1 Add 'enhanced_acwr_calculation' feature flag to utils/feature_flags.py
  - [ ] 2.2 Implement admin-only access (user_id=1) for initial testing
  - [ ] 2.3 Add beta user support (user_ids 2, 3) for gradual rollout
  - [ ] 2.4 Create feature flag toggle functionality in admin interface
  - [ ] 2.5 Add feature flag status monitoring and logging
  - [ ] 2.6 Implement fallback to existing 28-day calculation when disabled
  - [ ] 2.7 Test feature flag integration with existing TRIMP enhancement patterns

### Phase 2: Mathematical Core Implementation (Weeks 3-4)

- [ ] 3.0 Exponential Decay Calculation Engine
  - [ ] 3.1 Implement core exponential decay formula: Weight = e^(-decay_rate × days_ago)
  - [ ] 3.2 Create calculate_exponential_weighted_average method with comprehensive validation
  - [ ] 3.3 Implement chronic load calculation: Σ(load × weight) / Σ(weight)
  - [ ] 3.4 Add edge case handling: insufficient data, future dates, missing values
  - [ ] 3.5 Create mathematical validation tests for decay formula accuracy
  - [ ] 3.6 Implement data availability detection for minimum chronic period
  - [ ] 3.7 Add performance optimization for large activity datasets
  - [ ] 3.8 Create comprehensive unit tests for mathematical calculations

- [ ] 4.0 Enhanced ACWR Calculation Integration
  - [ ] 4.1 Update strava_training_load.py to use enhanced ACWR calculation when feature flag enabled
  - [ ] 4.2 Update garmin_training_load.py to use enhanced ACWR calculation when feature flag enabled
  - [ ] 4.3 Update elevation_migration_module.py to use enhanced calculations
  - [ ] 4.4 Maintain existing 7-day acute period calculation unchanged
  - [ ] 4.5 Preserve existing normalized divergence calculation
  - [ ] 4.6 Update unified_metrics_service.py to use enhanced calculations
  - [ ] 4.7 Add calculation method tracking (enhanced vs standard)
  - [ ] 4.8 Implement calculation result caching for performance

### Phase 3: Admin Interface Development (Weeks 5-6)

- [ ] 5.0 Configuration Management Interface
  - [ ] 5.1 Create admin_acwr_configuration.html template with configuration management panel
  - [ ] 5.2 Implement configuration creation form with validation (chronic period 28-90 days, decay rate 0.01-0.20)
  - [ ] 5.3 Add configuration editing interface with impact warnings
  - [ ] 5.4 Create user assignment interface with bulk assignment capabilities
  - [ ] 5.5 Implement configuration deactivation (soft delete) functionality
  - [ ] 5.6 Add assignment history tracking with timestamps and admin attribution
  - [ ] 5.7 Create rollback capabilities for configuration assignments
  - [ ] 5.8 Add real-time validation with helpful error messages

- [ ] 6.0 API Endpoints and Backend Integration
  - [ ] 6.1 Implement GET /api/admin/acwr-configurations endpoint to list configurations
  - [ ] 6.2 Create POST /api/admin/acwr-configurations endpoint for creating configurations
  - [ ] 6.3 Add PUT /api/admin/acwr-configurations/<id> endpoint for updating configurations
  - [ ] 6.4 Implement POST /api/admin/acwr-configurations/<id>/assign endpoint for user assignment
  - [ ] 6.5 Create GET /api/admin/acwr-configurations/<id>/preview endpoint for calculation preview
  - [ ] 6.6 Add POST /api/admin/acwr-configurations/recalculate endpoint for triggering migration
  - [ ] 6.7 Implement proper error handling and validation for all endpoints
  - [ ] 6.8 Add admin authentication checks to all endpoints

### Phase 4: Advanced Visualization Dashboard (Weeks 7-8)

- [ ] 7.0 Visualization Data Generation Service
  - [ ] 7.1 Create acwr_visualization_service.py for generating visualization data
  - [ ] 7.2 Implement parameter matrix calculation (chronic_period × decay_rate combinations)
  - [ ] 7.3 Create 3D surface plot data generation for chronic load across parameter combinations
  - [ ] 7.4 Implement 2D heatmap data with color-coded chronic load values
  - [ ] 7.5 Add time series data generation for parameter comparison
  - [ ] 7.6 Create ACWR ratio visualization with risk zone indicators
  - [ ] 7.7 Implement sensitivity analysis for parameter combinations
  - [ ] 7.8 Add data quality indicators and confidence metrics

- [ ] 8.0 Interactive Visualization Components
  - [ ] 8.1 Integrate Three.js or Plotly.js for 3D surface plot visualization
  - [ ] 8.2 Create interactive 2D heatmap with hover tooltips and click selection
  - [ ] 8.3 Implement multi-line time series plots with toggle visibility
  - [ ] 8.4 Add real-time parameter adjustment with live preview functionality
  - [ ] 8.5 Create interactive parameter controls (sliders, dropdowns) with validation
  - [ ] 8.6 Implement export capabilities (PNG/SVG images, CSV data, PDF reports)
  - [ ] 8.7 Add parameter preset configurations (conservative, moderate, aggressive)
  - [ ] 8.8 Create "what-if" analysis capabilities with parameter comparison

### Phase 5: Historical Data Migration (Weeks 9-10)

- [ ] 9.0 Migration System Development
  - [ ] 9.1 Create acwr_migration_service.py for batch processing historical data
  - [ ] 9.2 Implement progress tracking for migration operations with real-time updates
  - [ ] 9.3 Add data integrity validation during migration with rollback capability
  - [ ] 9.4 Create rollback functionality for migration if needed
  - [ ] 9.5 Implement batch processing for large datasets (process in chunks of 1000 activities)
  - [ ] 9.6 Add migration status monitoring and error handling with detailed logging
  - [ ] 9.7 Create admin interface for triggering and monitoring migrations
  - [ ] 9.8 Implement migration performance optimization and memory management

- [ ] 10.0 Migration Execution and Validation
  - [ ] 10.1 Execute migration for admin user (user_id=1) as proof of concept
  - [ ] 10.2 Validate migration results against existing calculations
  - [ ] 10.3 Execute migration for beta users (user_ids 2, 3)
  - [ ] 10.4 Monitor system performance during migration operations
  - [ ] 10.5 Create migration rollback procedures and test them
  - [ ] 10.6 Document migration results and performance metrics
  - [ ] 10.7 Prepare for full system migration

### Phase 6: Testing, Optimization, and Deployment (Weeks 11-12)

- [ ] 11.0 Comprehensive Testing and Validation
  - [ ] 11.1 Create test_acwr_configuration_service.py with unit tests for configuration management
  - [ ] 11.2 Implement test_acwr_visualization_service.py with visualization data generation tests
  - [ ] 11.3 Create test_acwr_migration_service.py with migration functionality tests
  - [ ] 11.4 Add integration tests for API endpoints with authentication
  - [ ] 11.5 Implement edge case testing (insufficient data, extreme parameters)
  - [ ] 11.6 Create performance tests for large dataset calculations
  - [ ] 11.7 Add validation tests for exponential decay formula accuracy
  - [ ] 11.8 Implement feature flag integration tests

- [ ] 12.0 Performance Optimization and Caching
  - [ ] 12.1 Implement calculation result caching to avoid repeated computation
  - [ ] 12.2 Add background processing for large calculations with job queues
  - [ ] 12.3 Optimize database queries for parameter matrix calculations
  - [ ] 12.4 Implement lazy loading for visualization data
  - [ ] 12.5 Add progress indicators for long-running operations
  - [ ] 12.6 Create caching strategy for frequently accessed configurations
  - [ ] 12.7 Implement database query optimization for enhanced calculations
  - [ ] 12.8 Add performance monitoring and alerting

- [ ] 13.0 Documentation and Deployment
  - [ ] 13.1 Create comprehensive admin user guide for ACWR configuration
  - [ ] 13.2 Document API endpoints with examples and error codes
  - [ ] 13.3 Create deployment guide for database schema migration
  - [ ] 13.4 Document feature flag rollout strategy and procedures
  - [ ] 13.5 Create troubleshooting guide for common issues
  - [ ] 13.6 Add inline code documentation and comments
  - [ ] 13.7 Create performance monitoring and alerting documentation
  - [ ] 13.8 Prepare rollback procedures and emergency response plan

- [ ] 14.0 Gradual Rollout and Monitoring
  - [ ] 14.1 Deploy to production with admin-only access
  - [ ] 14.2 Monitor system performance and calculation accuracy
  - [ ] 14.3 Enable for beta users (user_ids 2, 3) after validation
  - [ ] 14.4 Collect user feedback and performance metrics
  - [ ] 14.5 Execute full historical data migration
  - [ ] 14.6 Enable gradual rollout to all users
  - [ ] 14.7 Monitor success metrics and system stability
  - [ ] 14.8 Document lessons learned and optimization opportunities
