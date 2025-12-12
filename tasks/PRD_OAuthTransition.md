# Product Requirements Document: OAuth Transition to Centralized API Access

## 1. Introduction/Overview

**Feature Name:** OAuth Transition to Centralized API Access  
**Version:** 1.0  
**Date:** January 2025  

### Problem Statement
Your Training Monkey currently uses a hybrid OAuth model where users must create their own Strava applications to access the service. This creates significant friction in the onboarding process and limits scalability. With Strava's approval for centralized API access supporting up to 999 athletes, we need to transition to a streamlined, centralized OAuth flow that simplifies user onboarding while maintaining proper legal compliance.

### Goal
Transform the user onboarding experience from a complex, multi-step process requiring individual Strava app creation to a seamless, one-click Strava connection that maintains all existing functionality while adding proper legal compliance and progressive feature unlocking.

## 2. Goals

### Primary Goals
1. **Simplify User Onboarding**: Reduce signup friction by eliminating the need for users to create individual Strava applications
2. **Maintain Seamless Experience**: Ensure existing users continue working without any required action
3. **Legal Compliance**: Implement proper terms of service, privacy policy, and medical disclaimers
4. **Progressive Onboarding**: Create a tiered onboarding experience that unlocks features as users engage

### Secondary Goals
1. **Technical Scalability**: Centralize OAuth token management for easier maintenance
2. **Data Preservation**: Maintain all existing user data and connections during transition
3. **Error Reduction**: Minimize OAuth-related errors and support tickets
4. **Beta Testing**: Validate the new flow with one fabricated test account before full rollout

## 3. User Stories

### New User Journey
- **As a** new trail runner  
- **I want to** sign up for Your Training Monkey quickly  
- **So that** I can start analyzing my training data without technical complexity

- **As a** new user  
- **I want to** understand what data I'm sharing and how it's used  
- **So that** I can make an informed decision about using the service

- **As a** new user  
- **I want to** see immediate value from the platform  
- **So that** I'm motivated to continue using it

### Existing User Journey
- **As an** existing user  
- **I want to** continue using the platform without interruption  
- **So that** my training analysis isn't disrupted

- **As an** existing user  
- **I want to** understand the benefits of the new system  
- **So that** I can choose when to migrate if desired

### Legal Compliance
- **As a** user  
- **I want to** clearly understand the terms of service and privacy policy  
- **So that** I know my rights and responsibilities

- **As a** user  
- **I want to** understand the medical disclaimers  
- **So that** I use the recommendations responsibly

## 4. Functional Requirements

### 4.1 Legal Documentation System
1. The system must display Terms and Conditions during signup
2. The system must display Privacy Policy during signup  
3. The system must display Medical Disclaimer during signup
4. The system must require explicit acceptance of all legal documents
5. The system must log legal document acceptance with timestamp and IP address
6. The system must track legal document versions for compliance

### 4.2 User Registration Flow
7. The system must allow users to create accounts with email and basic information
8. The system must validate email format and uniqueness
9. The system must generate secure random passwords for new accounts
10. The system must store user registration data with proper encryption
11. The system must track account status (pending_verification, pending_strava_connection, active)

### 4.3 Centralized OAuth Integration
12. The system must use centralized Strava app credentials for all OAuth flows
13. The system must handle OAuth token exchange using approved app credentials
14. The system must store Strava tokens securely in the database
15. The system must refresh expired tokens automatically
16. The system must handle OAuth errors gracefully with user-friendly messages

### 4.4 Progressive Onboarding System
17. The system must implement minimal tiered onboarding with progressive feature unlocking
18. The system must show basic dashboard immediately after Strava connection
19. The system must unlock advanced features as users engage with the platform
20. The system must provide basic onboarding guidance for new features
21. The system must track onboarding completion status

### 4.5 Existing User Migration
22. The system must preserve all existing user data during transition
23. The system must maintain existing Strava connections without disruption
24. The system must allow existing users to continue using current OAuth flow
25. The system must provide optional migration path for existing users
26. The system must not require any action from existing users

### 4.6 Database Schema Updates
27. The system must add legal compliance tracking columns to user_settings table
28. The system must create legal_compliance table for audit trail
29. The system must add onboarding progress tracking fields
30. The system must maintain backward compatibility with existing data

### 4.7 Error Handling and Monitoring
31. The system must log all OAuth-related errors for monitoring
32. The system must provide clear error messages to users
33. The system must implement retry logic for transient OAuth failures
34. The system must track onboarding funnel metrics
35. The system must alert on critical OAuth failures

## 5. Non-Goals (Out of Scope)

### What This Feature Will NOT Include
- **Email verification system** - Will be implemented in early future phase
- **Account recovery system** - Password reset functionality deferred to later
- **Data export/deletion tools** - GDPR compliance tools deferred to later
- **Advanced security features** - Rate limiting and brute force protection deferred to later
- **Analytics dashboard** - Onboarding analytics will be basic logging only
- **Mobile app integration** - This is web-only implementation
- **Enterprise features** - B2B functionality will be future consideration
- **Multi-language support** - English only for initial implementation

## 6. Design Considerations

### UI/UX Requirements
- **Consistent with existing design** - Use current color scheme and styling
- **Mobile responsive** - All new pages must work on mobile devices
- **Accessibility compliant** - Follow WCAG 2.1 AA standards
- **Clear legal presentation** - Legal documents must be easily readable
- **Progressive disclosure** - Show information as needed, not all at once

### User Experience Flow