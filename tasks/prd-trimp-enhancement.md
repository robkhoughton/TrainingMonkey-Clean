# Product Requirements Document: TRIMP Calculation Enhancement

## Introduction/Overview

This feature enhances the TRIMP (Training Impulse) calculation system in Your Training Monkey to use heart rate stream data instead of average heart rate values, significantly improving accuracy for variable-intensity workouts like intervals. The enhancement addresses discrepancies with competing platforms like Runalyze while maintaining backward compatibility and system performance.

**Problem Solved**: Current TRIMP calculations underestimate training load for interval and variable-intensity workouts because they use average heart rate instead of the complete heart rate stream data available from Strava.

**Goal**: Implement heart rate stream-based TRIMP calculations that achieve <5% difference from industry-standard platforms while maintaining system performance and user experience.

## Goals

1. **Accuracy**: Achieve <5% difference from Runalyze TRIMP values for test dataset
2. **Performance**: Maintain <2x processing time increase for typical activities
3. **Compatibility**: Preserve existing functionality with average HR fallback
4. **Reliability**: Ensure robust error handling and logging for production use
5. **Scalability**: Support both new and historical activity processing
6. **User Experience**: Seamless rollout with feature flags and admin controls

## User Stories

### Primary Users
- **Athletes**: "As an athlete, I want accurate TRIMP calculations that reflect my actual training intensity so that my training load metrics are reliable for planning and recovery."
- **Coaches**: "As a coach, I want precise training load data so I can make informed decisions about athlete training progression and injury prevention."

### Secondary Users
- **System Administrators**: "As an admin, I want to control the rollout of enhanced TRIMP calculations so I can validate accuracy before full deployment."
- **Beta Users**: "As a beta user, I want to test the new TRIMP calculations on my data so I can provide feedback before general release."

## Functional Requirements

### Core Calculation Enhancement
1. **FR-1**: The system must modify the `calculate_banister_trimp()` function to accept an optional `hr_stream` parameter containing heart rate array data.
2. **FR-2**: The system must calculate TRIMP using heart rate stream data when available, processing each sample individually and summing the results.
3. **FR-3**: The system must fall back to average heart rate calculation when stream data is unavailable or invalid.
4. **FR-4**: The system must maintain the existing function signature for backward compatibility with current codebase.
5. **FR-5**: The system must clamp heart rate reserve values to [0,1] range for each sample to prevent calculation errors.

### Data Processing
6. **FR-6**: The system must distribute total activity duration across all heart rate samples in the stream.
7. **FR-7**: The system must handle varying heart rate stream sample rates (typically 1Hz from Strava).
8. **FR-8**: The system must validate heart rate data quality and skip invalid samples (≤0 bpm).
9. **FR-9**: The system must use existing gender coefficients (k = 1.92 for male, 1.67 for female).

### Database Integration
10. **FR-10**: The system must add database fields to track calculation method, sample count, and processing timestamp.
11. **FR-11**: The system must maintain multi-user data isolation by filtering all queries by user_id.
12. **FR-12**: The system must store heart rate stream data efficiently for future recalculations.

### Error Handling & Logging
13. **FR-13**: The system must include comprehensive try/catch blocks with meaningful error messages.
14. **FR-14**: The system must log which calculation method was used (stream vs average) for each activity.
15. **FR-15**: The system must handle edge cases including empty streams, missing data, and API failures gracefully.

### Performance & Caching
16. **FR-16**: The system must process typical heart rate streams (up to 2 hours) within 2 seconds.
17. **FR-17**: The system must implement efficient heart rate stream storage to balance database size and retrieval speed.
18. **FR-18**: The system must not cache frequently accessed activities as per user requirements.

### Historical Data Processing
19. **FR-19**: The system must provide admin-triggered recalculation of historical activities.
20. **FR-20**: The system must process historical activities in batches to prevent system overload.
21. **FR-21**: The system must maintain data integrity during historical recalculation processes.

### Feature Rollout
22. **FR-22**: The system must implement feature flags for gradual rollout (admin → beta users → general release).
23. **FR-23**: The system must allow admins to toggle between calculation methods for testing purposes.
24. **FR-24**: The system must provide admin dashboard controls for managing the enhancement rollout.

## Non-Goals (Out of Scope)

1. **NG-1**: Real-time TRIMP calculation during live activities (post-activity processing only)
2. **NG-2**: Integration with other heart rate calculation methods beyond Banister TRIMP
3. **NG-3**: Automatic comparison with external platforms (Runalyze, etc.) - manual validation only
4. **NG-4**: User-facing calculation method indicators in the UI (nice-to-have but not necessary)
5. **NG-5**: Caching of frequently accessed activities
6. **NG-6**: Real-time notifications of calculation method changes to users

## Design Considerations

### Technical Architecture
- **Function Enhancement**: Modify existing `calculate_banister_trimp()` in `strava_training_load.py` (lines 692-725)
- **Data Flow**: Strava API → Heart Rate Stream → TRIMP Calculation → Database Storage
- **Fallback Strategy**: Average HR calculation when stream data unavailable
- **Performance Target**: <2 seconds for 2-hour activities with 1Hz HR data

### Database Schema Changes
The following SQL statements should be executed manually via SQL editor:

```sql
-- Add new fields to activities table
ALTER TABLE activities ADD COLUMN trimp_calculation_method VARCHAR(20) DEFAULT 'average';
ALTER TABLE activities ADD COLUMN hr_stream_sample_count INTEGER DEFAULT 0;
ALTER TABLE activities ADD COLUMN trimp_processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Create heart rate streams table for efficient storage
CREATE TABLE IF NOT EXISTS hr_streams (
    id SERIAL PRIMARY KEY,
    activity_id INTEGER REFERENCES activities(activity_id),
    user_id INTEGER REFERENCES user_settings(id),
    hr_data JSONB, -- Store heart rate array as JSON
    sample_rate REAL DEFAULT 1.0, -- Hz
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_hr_streams_activity (activity_id),
    INDEX idx_hr_streams_user (user_id)
);
```

## Technical Considerations

### Dependencies
- **Strava API**: Heart rate stream data availability via `get_activity_streams()`
- **Existing Code**: Integration with current `strava_training_load.py` module
- **Database**: PostgreSQL/SQLite compatibility for new schema fields
- **Performance**: NumPy for efficient array processing

### Implementation Approach
1. **Phase 1**: Enhance calculation function with stream processing capability
2. **Phase 2**: Implement database schema changes and data storage
3. **Phase 3**: Add feature flags and admin controls
4. **Phase 4**: Implement historical data processing tools
5. **Phase 5**: Deploy with gradual rollout strategy

### Mathematical Implementation
```
TRIMP = Σ(duration_per_sample × hr_reserve_fraction × 0.64^(k × hr_reserve_fraction))
```
Where:
- `duration_per_sample = total_duration_minutes / stream_length`
- `hr_reserve_fraction = (hr_sample - resting_hr) / (max_hr - resting_hr)`
- `k = 1.92` (male) or `1.67` (female)

## Success Metrics

### Accuracy Metrics
- **Primary**: <5% difference from Runalyze TRIMP values on test dataset
- **Secondary**: Improved accuracy for interval workouts vs steady-state activities
- **Validation**: Mathematical correctness verified through unit tests

### Performance Metrics
- **Processing Time**: <2 seconds for typical 2-hour activities
- **Database Impact**: <20% increase in storage requirements
- **API Efficiency**: Minimal additional Strava API calls

### User Experience Metrics
- **Rollout Success**: Zero user-reported issues during feature flag deployment
- **Data Integrity**: 100% successful historical recalculation completion
- **System Stability**: No performance degradation during peak usage

## Open Questions

1. **Heart Rate Stream Storage**: Should we implement compression for large HR streams to optimize database storage?
2. **Batch Processing**: What batch size should be used for historical activity recalculation to balance performance and system load?
3. **Error Recovery**: How should the system handle partial failures during historical recalculation (retry mechanism, rollback strategy)?
4. **Monitoring**: What specific metrics should be monitored during rollout to detect issues early?
5. **Documentation**: Should we create user-facing documentation explaining the enhanced TRIMP calculations?

---

**Target Audience**: Junior developers with Python Flask experience
**Implementation Priority**: High (addresses core accuracy issues)
**Estimated Effort**: 3-5 days for core implementation, 2-3 days for testing and deployment
**Risk Level**: Medium (database changes, performance impact)

