# Task List: Route Optimization for strava_app.py

## Relevant Files

- `app/strava_app.py` - Main Flask application containing all 92 routes to be optimized
- `app/utils/feature_flags.py` - Existing feature flag system for safe route disabling
- `app/trimp_deployment_monitor.py` - Existing monitoring system for deployment validation
- `app/system_monitoring_dashboard.py` - Existing monitoring infrastructure for performance tracking
- `app/tests/test_registration_flow.py` - Existing test infrastructure for route validation
- `app/tests/test_legal_validation.py` - Legal system test infrastructure
- `app/tests/test_registration_validation.py` - Registration system test infrastructure
- `app/debug_routes.py` - Debug route utilities (may be removed)
- `docs/onboarding_verification_checklist.md` - Existing verification procedures
- `app/registration_session_manager.py` - Registration session management system
- `app/onboarding_manager.py` - Onboarding system management
- `app/legal_compliance.py` - Legal compliance system
- `app/legal_document_versioning.py` - Legal document versioning system

### Notes

- The application already has a robust feature flag system in `app/utils/feature_flags.py` that can be leveraged for safe route disabling
- Existing monitoring infrastructure in `trimp_deployment_monitor.py` and `system_monitoring_dashboard.py` can be adapted for route optimization monitoring
- Comprehensive test infrastructure exists for registration, legal, and onboarding systems
- Database operations should be handled manually via SQL editor per project rules [[memory:7619135]]

## Tasks

- [ ] 1.0 Pre-Implementation Analysis and Preparation
  - [ ] 1.1 Audit all 92 routes in `strava_app.py` and create comprehensive route inventory with categories (core, debug, admin, registration, legal)
  - [ ] 1.2 Identify external dependencies by searching for API clients, mobile app integrations, and third-party services that might use specific routes
  - [ ] 1.3 Document current route usage patterns by analyzing access logs and identifying high-traffic vs. unused routes
  - [ ] 1.4 Create baseline performance metrics (startup time, memory usage, route registration time) for comparison
  - [ ] 1.5 Set up monitoring and logging infrastructure for tracking route optimization progress
  - [ ] 1.6 Create rollback plan and backup procedures for each phase of route removal

- [ ] 2.0 Implement Route Disabling Infrastructure
  - [ ] 2.1 Extend existing feature flag system in `app/utils/feature_flags.py` to support route-level disabling
  - [ ] 2.2 Create route disabling decorator that can conditionally disable routes based on feature flags
  - [ ] 2.3 Implement route monitoring system to track disabled route access attempts and log them appropriately
  - [ ] 2.4 Create admin interface for enabling/disabling routes during testing phase
  - [ ] 2.5 Add route disabling functionality to existing monitoring dashboard in `app/system_monitoring_dashboard.py`
  - [ ] 2.6 Test route disabling infrastructure with non-critical routes to ensure it works correctly

- [ ] 3.0 Phase 1: Remove Debug and Security-Risk Routes
  - [ ] 3.1 Disable debug route `/api/training-data-raw` using feature flag system and monitor for 48 hours
  - [ ] 3.2 Disable database initialization route `/init-database` using feature flag system and monitor for 48 hours
  - [ ] 3.3 Verify no external systems or clients are accessing these debug routes during monitoring period
  - [ ] 3.4 Remove debug route `/api/training-data-raw` (line 1433) from `strava_app.py` after successful monitoring
  - [ ] 3.5 Remove database initialization route `/init-database` (line 1400) from `strava_app.py` after successful monitoring
  - [ ] 3.6 Update any documentation or comments that reference the removed debug routes
  - [ ] 3.7 Run comprehensive application tests to ensure no functionality is broken by debug route removal

- [ ] 4.0 Phase 2: Optimize Registration System Routes
  - [ ] 4.1 Analyze current registration flow to identify which tracking routes are truly redundant vs. essential
  - [ ] 4.2 Disable redundant registration tracking routes using feature flags: `/api/registration/track-email-verification`, `/api/registration/track-onboarding-start`, `/api/registration/track-onboarding-complete`
  - [ ] 4.3 Monitor registration flow for 72 hours to ensure user experience remains intact
  - [ ] 4.4 Remove redundant email verification tracking route `/api/registration/track-email-verification` (line 4821)
  - [ ] 4.5 Remove redundant onboarding start tracking route `/api/registration/track-onboarding-start` (line 4862)
  - [ ] 4.6 Remove redundant onboarding complete tracking route `/api/registration/track-onboarding-complete` (line 4881)
  - [ ] 4.7 Consolidate session management routes by removing `/api/registration/extend-session` (line 5149) and `/api/registration/user-sessions/<int:user_id>` (line 5181)
  - [ ] 4.8 Test complete registration flow from signup to onboarding completion to ensure no functionality is lost
  - [ ] 4.9 Update registration system documentation to reflect the streamlined route structure

- [ ] 5.0 Phase 3: Streamline Admin Analytics Routes
  - [ ] 5.1 Identify which admin analytics routes are essential vs. excessive by analyzing usage patterns
  - [ ] 5.2 Disable excessive admin analytics routes using feature flags: `/api/admin/session-analytics`, `/api/admin/cleanup-expired-sessions`, `/api/admin/registration-summary`
  - [ ] 5.3 Monitor admin operations for 48 hours to ensure core admin functionality remains intact
  - [ ] 5.4 Remove session analytics route `/api/admin/session-analytics` (line 5214) after successful monitoring
  - [ ] 5.5 Remove cleanup expired sessions route `/api/admin/cleanup-expired-sessions` (line 5233) after successful monitoring
  - [ ] 5.6 Remove registration summary route `/api/admin/registration-summary` (line 4901) after successful monitoring
  - [ ] 5.7 Remove registration status route `/api/admin/registration-status/<int:user_id>` (line 4920) after successful monitoring
  - [ ] 5.8 Remove cleanup registrations route `/api/admin/cleanup-registrations-with-tracking` (line 4939) after successful monitoring
  - [ ] 5.9 Remove session invalidation route `/api/admin/invalidate-session` (line 5257) after successful monitoring
  - [ ] 5.10 Test all remaining admin functionality to ensure TRIMP settings, feature flags, and user management still work correctly

- [ ] 6.0 Phase 4: Final Cleanup and Validation
  - [ ] 6.1 Perform final route count audit to confirm reduction from 92 to 72-77 routes (15-20 route reduction)
  - [ ] 6.2 Remove any remaining redundant or unused routes identified during the optimization process
  - [ ] 6.3 Clean up any orphaned imports, unused functions, or dead code related to removed routes
  - [ ] 6.4 Update route documentation and comments to reflect the optimized route structure
  - [ ] 6.5 Run comprehensive integration tests to ensure all remaining functionality works correctly
  - [ ] 6.6 Validate that all external API contracts and integrations are preserved
  - [ ] 6.7 Verify that legal compliance system remains completely intact and functional
  - [ ] 6.8 Remove feature flags used for route disabling since routes are now permanently removed

- [ ] 7.0 Performance Testing and Documentation
  - [ ] 7.1 Measure and document application startup time improvement (target: 15-20% reduction)
  - [ ] 7.2 Measure and document memory usage reduction (target: 10-15% reduction)
  - [ ] 7.3 Measure and document route registration time improvement (target: 25-30% reduction)
  - [ ] 7.4 Run performance benchmarks comparing before/after optimization results
  - [ ] 7.5 Update API documentation to reflect removed routes and provide migration guidance if needed
  - [ ] 7.6 Create deployment guide for the optimized route structure
  - [ ] 7.7 Document lessons learned and best practices for future route optimization efforts
  - [ ] 7.8 Create monitoring dashboard for ongoing route performance tracking
