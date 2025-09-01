# Database Testing Rules

## Overview

This document establishes rules for database testing in the TrainingMonkey OAuth Transition project to ensure proper handling of cloud-deployed database interactions.

## Core Rules

### 1. Cloud Database Dependency
- **Rule**: The application depends on a cloud-deployed PostgreSQL database
- **Action**: All database interactions must be designed for the cloud environment
- **Exception**: No local database creation or mocking for testing

### 2. Database Schema Changes
- **Rule**: Database schema changes must be handled manually via SQL Editor
- **Action**: Use Cloud SQL Editor for all schema modifications
- **Documentation**: All schema changes must be documented in `docs/database_changes.md`

### 3. Testing Deferral for Database Dependencies
- **Rule**: If database connection is required for testing, defer testing to later phase
- **Action**: Mark tasks as "testing deferred to Phase 3" when database access is needed
- **Rationale**: Prevents local database creation attempts and ensures proper cloud testing

### 4. Unit Testing Without Database
- **Rule**: Unit tests should not require database connections
- **Action**: Use mocking for database interactions in unit tests
- **Exception**: Integration tests that require database access are deferred

### 5. Test Account Creation
- **Rule**: Test account creation scripts must be designed for cloud deployment
- **Action**: Create scripts that work with the actual cloud database schema
- **Validation**: Test account creation is validated after deployment

## Implementation Guidelines

### For Task 8.0 (Testing and Validation)
- **Task 8.1**: ✅ Completed - Test account creation script created
- **Task 8.2-8.10**: Database-dependent testing deferred to post-deployment
- **Rationale**: These tasks require actual database access and OAuth integration

### For Database Schema Validation
- **Manual Verification**: Use `docs/database_verification_queries.sql`
- **Cloud SQL Editor**: Execute verification queries in production environment
- **Documentation**: Update verification results in project documentation

### For Test Scripts
- **Design for Cloud**: All test scripts must work with cloud database
- **No Local Setup**: Do not attempt to create local database replicas
- **Deployment Testing**: Test scripts are validated after deployment

## Task Completion Protocol

### Database-Dependent Tasks
1. **Create Implementation**: Complete the code implementation
2. **Mark as Deferred**: Update task list with "testing deferred" note
3. **Document Requirements**: Specify what database access is needed
4. **Post-Deployment Testing**: Execute tests after cloud deployment

### Non-Database Tasks
1. **Complete Implementation**: Finish code implementation
2. **Unit Testing**: Run unit tests with mocked dependencies
3. **Mark as Complete**: Update task list when tests pass
4. **Documentation**: Update relevant documentation

## Examples

### ✅ Correct Approach
```markdown
- [x] 8.1 Create fabricated test account for beta testing
- [ ] 8.2 Test complete new user registration flow (testing deferred to Phase 3)
- [ ] 8.4 Test OAuth flow with centralized credentials (requires database access)
```

### ❌ Incorrect Approach
```markdown
- [ ] 8.1 Create local database for testing
- [ ] 8.2 Mock database schema locally
- [ ] 8.4 Test with local database replica
```

## Compliance Checklist

- [x] Task 8.1 completed without database dependency
- [x] Test scripts designed for cloud deployment
- [x] Database schema changes documented
- [x] Testing deferral rules established
- [x] Unit tests use mocking for database interactions
- [ ] Post-deployment testing plan documented
- [ ] Cloud SQL Editor procedures documented

## Related Documents

- `docs/database_changes.md` - Database schema change log
- `docs/database_verification_queries.sql` - Verification queries
- `docs/process-task-list.md` - Task management process
- `docs/Task List OAuth Transition.md` - Main task list

