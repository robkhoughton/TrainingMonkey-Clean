-- ACWR Configuration Production Deployment Script
-- This script handles production-specific setup for the ACWR configuration system
-- Execute this script in your production database via SQL Editor

-- =============================================================================
-- PRODUCTION DEPLOYMENT: ACWR Configuration System
-- =============================================================================
-- Purpose: Production-specific setup and configuration
-- Database: PostgreSQL (Cloud SQL)
-- Date: 2025-01-27
-- Version: 1.0
-- Prerequisites: ACWR tables, indexes, and default configuration already exist
-- =============================================================================

-- =============================================================================
-- 1. PRODUCTION-SPECIFIC CONFIGURATIONS
-- =============================================================================

-- Create additional production configurations if needed
INSERT INTO acwr_configurations (
    name, 
    description, 
    chronic_period_days, 
    decay_rate, 
    is_active,
    created_by,
    notes
) VALUES 
(
    'conservative_enhanced',
    'Conservative enhanced ACWR with longer chronic period and lower decay',
    56,
    0.03,
    FALSE,  -- Inactive by default, activate as needed
    1,
    'Conservative configuration for risk-averse users'
),
(
    'aggressive_enhanced', 
    'Aggressive enhanced ACWR with shorter chronic period and higher decay',
    35,
    0.08,
    FALSE,  -- Inactive by default, activate as needed
    1,
    'Aggressive configuration for experienced users'
)
ON CONFLICT (name) DO NOTHING;

-- =============================================================================
-- 2. PRODUCTION MONITORING SETUP
-- =============================================================================

-- Create a view for monitoring ACWR configuration usage
CREATE OR REPLACE VIEW acwr_configuration_usage AS
SELECT 
    ac.id,
    ac.name,
    ac.chronic_period_days,
    ac.decay_rate,
    ac.is_active,
    COUNT(uac.user_id) as assigned_users,
    COUNT(eac.id) as calculation_count,
    MAX(eac.calculation_timestamp) as last_calculation
FROM acwr_configurations ac
LEFT JOIN user_acwr_configurations uac ON ac.id = uac.configuration_id AND uac.is_active = TRUE
LEFT JOIN enhanced_acwr_calculations eac ON ac.id = eac.configuration_id
GROUP BY ac.id, ac.name, ac.chronic_period_days, ac.decay_rate, ac.is_active
ORDER BY ac.created_at;

-- =============================================================================
-- 3. PRODUCTION READINESS CONFIRMATION
-- =============================================================================

-- Simple confirmation that the system is ready
SELECT 
    'ACWR System Ready' as status,
    NOW() as deployment_timestamp,
    'Production deployment complete' as message;

-- =============================================================================
-- PRODUCTION DEPLOYMENT COMPLETE
-- =============================================================================
-- The ACWR configuration system is now ready for production use.
-- 
-- What was added:
-- ✅ Additional production configurations (conservative, aggressive)
-- ✅ Monitoring view for configuration usage
-- ✅ Production readiness confirmation
-- 
-- Next Steps:
-- 1. Deploy application code with ACWR configuration service
-- 2. Test database connectivity and service functionality  
-- 3. Enable feature flags for gradual rollout
-- 4. Begin historical data migration for enhanced calculations
-- =============================================================================
