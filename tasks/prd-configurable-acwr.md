# Product Requirements Document: Configurable ACWR with Exponential Decay

## Introduction/Overview

The current ACWR (Acute:Chronic Workload Ratio) calculation uses a fixed 28-day chronic period with simple averaging, which doesn't accurately reflect how training load impacts athletes over time. This feature introduces a configurable ACWR system that allows administrators to set personalized chronic periods (minimum 28 days) and exponential decay rates, providing more accurate and individualized training load analysis.

**Problem Solved:** The existing 28-day simple average doesn't account for the diminishing impact of older training sessions, leading to less accurate injury risk assessment and training load management.

**Goal:** Provide administrators with tools to configure and optimize ACWR calculations for individual users, improving training load accuracy and injury prevention.

## Goals

1. **Flexibility**: Allow chronic period configuration from 28-90 days based on data availability
2. **Accuracy**: Implement exponential decay weighting to better reflect training load impact over time
3. **Administrative Control**: Provide comprehensive admin dashboard for configuration management
4. **Visualization**: Enable administrators to visualize parameter impacts before implementation
5. **Gradual Rollout**: Deploy safely using feature flags (admin → beta → all users)
6. **Data Integrity**: Recalculate all historical data to maintain consistency
7. **Performance**: Optimize for accuracy over speed in calculations

## User Stories

### Administrator Stories
- **As an administrator**, I want to create multiple ACWR configuration profiles so that I can optimize calculations for different user types
- **As an administrator**, I want to assign specific configurations to individual users so that each user gets personalized ACWR calculations
- **As an administrator**, I want to visualize how different parameters affect chronic load calculations so that I can make informed configuration decisions
- **As an administrator**, I want to preview parameter changes before applying them so that I can validate the impact
- **As an administrator**, I want to recalculate historical data with new parameters so that all data remains consistent

### System Stories
- **As the system**, I want to automatically determine minimum chronic period based on user's data availability so that calculations are always meaningful
- **As the system**, I want to validate decay rate parameters so that calculations remain within reasonable bounds
- **As the system**, I want to cache calculation results so that performance is optimized for repeated queries

## Functional Requirements

### 1. Configuration Management
1.1. The system must allow administrators to create named ACWR configuration profiles
1.2. The system must validate chronic period is between 28-90 days
1.3. The system must validate decay rate is between 0.01-0.20 with guidance text
1.4. The system must automatically determine minimum chronic period based on user's data availability
1.5. The system must allow editing of existing configurations with impact warnings
1.6. The system must allow deactivation of configurations (soft delete)

### 2. User Assignment
2.1. The system must allow administrators to assign configurations to individual users
2.2. The system must support bulk assignment of configurations to multiple users
2.3. The system must maintain assignment history with timestamps and admin attribution
2.4. The system must prevent multiple active configurations per user
2.5. The system must provide rollback capabilities for configuration assignments

### 3. Visualization Dashboard
3.1. The system must provide 3D surface plot showing chronic load across parameter combinations
3.2. The system must provide 2D heatmap with color-coded chronic load values
3.3. The system must provide time series comparison of different parameter sets
3.4. The system must provide ACWR ratio visualization with risk zone indicators
3.5. The system must allow real-time parameter adjustment with live preview
3.6. The system must support export of visualization data and images

### 4. Calculation Engine
4.1. The system must implement exponential decay formula: Weight = e^(-decay_rate × days_ago)
4.2. The system must calculate chronic load as weighted average: Σ(load × weight) / Σ(weight)
4.3. The system must maintain existing 7-day acute period calculation
4.4. The system must handle edge cases: insufficient data, future dates, missing values
4.5. The system must preserve existing normalized divergence calculation

### 5. Feature Flag Integration
5.1. The system must integrate with existing feature flag system for gradual rollout
5.2. The system must support admin-only access initially
5.3. The system must support beta user rollout (user_ids 2, 3)
5.4. The system must support gradual rollout to all users
5.5. The system must provide fallback to existing 28-day calculation when disabled

### 6. Data Migration
6.1. The system must recalculate all historical data with new parameters
6.2. The system must provide batch processing for large datasets
6.3. The system must maintain data integrity during migration
6.4. The system must provide progress tracking for migration operations
6.5. The system must support rollback of migration if needed

### 7. Performance & Caching
7.1. The system must cache calculation results to avoid repeated computation
7.2. The system must provide background processing for large calculations
7.3. The system must optimize database queries for parameter matrix calculations
7.4. The system must provide progress indicators for long-running operations

### 8. Admin Interface
8.1. The system must provide configuration management interface
8.2. The system must provide user assignment interface
8.3. The system must provide visualization dashboard
8.4. The system must provide migration status monitoring
8.5. The system must provide audit logging for all configuration changes

## Non-Goals (Out of Scope)

- **End-user configuration**: Users cannot directly modify their own ACWR parameters (admin-only)
- **Real-time parameter changes**: Parameter changes require recalculation, not instant updates
- **Multiple active configurations per user**: Each user has one active configuration at a time
- **Custom decay formulas**: Only exponential decay is supported (not linear, polynomial, etc.)
- **Cross-user configuration sharing**: Configurations are not automatically shared between users
- **Mobile-specific optimizations**: Focus on desktop admin interface initially

## Design Considerations

### Admin Dashboard Layout
- **Configuration Panel**: List, create, edit, delete configurations
- **User Assignment Panel**: Assign configurations to users with bulk operations
- **Visualization Panel**: 3D surface plot, heatmap, time series, ACWR comparison
- **Migration Panel**: Monitor recalculation progress and status
- **Audit Panel**: View configuration change history

### Visualization Components
- **3D Surface Plot**: Interactive 3D visualization using Three.js or Plotly.js
- **2D Heatmap**: Color-coded grid with hover tooltips
- **Time Series**: Multi-line plots with toggle visibility
- **Parameter Controls**: Sliders and dropdowns for real-time adjustment
- **Export Options**: PNG/SVG images, CSV data, PDF reports

### User Experience
- **Progressive Disclosure**: Show basic options first, advanced options on demand
- **Validation Feedback**: Real-time validation with helpful error messages
- **Preview Mode**: Show impact before applying changes
- **Undo/Redo**: Support for configuration changes
- **Help Documentation**: Contextual help and parameter guidance

## Technical Considerations

### Database Schema
- **acwr_configurations**: Store configuration profiles
- **user_acwr_configurations**: Link users to configurations
- **enhanced_acwr_calculations**: Store calculation results
- **Migration tracking**: Monitor recalculation progress

### Integration Points
- **strava_training_load.py**: Main ACWR calculation function
- **garmin_training_load.py**: Garmin-specific calculations
- **feature_flags.py**: Gradual rollout control
- **unified_metrics_service.py**: Metrics aggregation
- **settings_utils.py**: Settings validation

### Performance Optimizations
- **Lazy Loading**: Load visualization data on demand
- **Caching**: Cache calculation results and visualization data
- **Batch Processing**: Process large datasets in chunks
- **Background Jobs**: Handle long-running calculations asynchronously

### API Endpoints
- `GET /api/admin/acwr-configurations`: List configurations
- `POST /api/admin/acwr-configurations`: Create configuration
- `PUT /api/admin/acwr-configurations/<id>`: Update configuration
- `POST /api/admin/acwr-configurations/<id>/assign`: Assign to users
- `GET /api/admin/acwr-configurations/<id>/preview`: Preview calculations
- `POST /api/admin/acwr-configurations/recalculate`: Trigger migration

## Success Metrics

### Primary Metrics
- **Admin Dashboard Usage**: Track configuration creation and user assignment frequency
- **Configuration Adoption**: Monitor how many users are assigned to new configurations
- **Visualization Engagement**: Track dashboard usage and export frequency
- **Migration Success Rate**: Monitor successful recalculation completion rates

### Secondary Metrics
- **Performance Impact**: Monitor calculation time and database query performance
- **Error Rates**: Track configuration validation failures and calculation errors
- **User Feedback**: Collect admin feedback on configuration effectiveness
- **System Stability**: Monitor for any performance degradation or errors

## Open Questions

1. **Default Configuration**: What should be the default chronic period and decay rate for new users?
2. **Parameter Validation**: Should there be additional validation rules beyond the specified ranges?
3. **Visualization Performance**: What's the maximum number of parameter combinations to display simultaneously?
4. **Migration Strategy**: Should migration be user-by-user or system-wide?
5. **Backup Strategy**: How should we handle rollback if new calculations prove problematic?
6. **Documentation**: What level of user documentation is needed for the admin interface?
7. **Testing Strategy**: How should we validate the accuracy of exponential decay calculations?
8. **Future Enhancements**: Should we plan for user-specific configuration access in future phases?

## Implementation Phases

### Phase 1: Foundation (Weeks 1-2)
- Database schema creation
- Basic configuration service
- Feature flag integration

### Phase 2: Admin Interface (Weeks 3-4)
- Configuration management interface
- User assignment interface
- Basic validation and error handling

### Phase 3: Visualization (Weeks 5-6)
- 3D surface plot implementation
- Heatmap and time series visualizations
- Interactive parameter controls

### Phase 4: Integration (Weeks 7-8)
- ACWR calculation engine updates
- Migration script development
- Performance optimization

### Phase 5: Testing & Rollout (Weeks 9-10)
- Comprehensive testing
- Admin user rollout
- Beta user rollout
- Performance monitoring

### Phase 6: Full Deployment (Weeks 11-12)
- Gradual rollout to all users
- Historical data migration
- Documentation and training
- Success metrics analysis
