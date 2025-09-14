-- Database Cleanup Analysis Script
-- Run this first to understand what data exists in both tables

-- ============================================================================
-- 1. DATA ANALYSIS
-- ============================================================================

-- Check record counts in both tables
SELECT 'acwr_enhanced_calculations' as table_name, COUNT(*) as record_count
FROM acwr_enhanced_calculations
UNION ALL
SELECT 'enhanced_acwr_calculations' as table_name, COUNT(*) as record_count
FROM enhanced_acwr_calculations;

-- Check data distribution by user
SELECT 'acwr_enhanced_calculations' as table_name, user_id, COUNT(*) as records
FROM acwr_enhanced_calculations
GROUP BY user_id
UNION ALL
SELECT 'enhanced_acwr_calculations' as table_name, user_id, COUNT(*) as records
FROM enhanced_acwr_calculations
GROUP BY user_id
ORDER BY table_name, user_id;

-- Check date ranges in both tables
SELECT 'acwr_enhanced_calculations' as table_name, 
       MIN(calculation_date) as earliest_date, 
       MAX(calculation_date) as latest_date
FROM acwr_enhanced_calculations
UNION ALL
SELECT 'enhanced_acwr_calculations' as table_name,
       MIN(calculation_timestamp) as earliest_date,
       MAX(calculation_timestamp) as latest_date
FROM enhanced_acwr_calculations;

-- ============================================================================
-- 2. SCHEMA COMPARISON
-- ============================================================================

-- Compare column structures
SELECT 'acwr_enhanced_calculations' as table_name, column_name, data_type
FROM information_schema.columns 
WHERE table_name = 'acwr_enhanced_calculations'
UNION ALL
SELECT 'enhanced_acwr_calculations' as table_name, column_name, data_type
FROM information_schema.columns 
WHERE table_name = 'enhanced_acwr_calculations'
ORDER BY table_name, column_name;

-- ============================================================================
-- 3. DATA QUALITY CHECK
-- ============================================================================

-- Check for NULL values in key columns (acwr_enhanced_calculations)
SELECT 'acwr_enhanced_calculations' as table_name,
       COUNT(*) as total_records,
       COUNT(acwr_ratio) as non_null_acwr_ratio,
       COUNT(acute_load) as non_null_acute_load,
       COUNT(chronic_load) as non_null_chronic_load
FROM acwr_enhanced_calculations;

-- Check for NULL values in key columns (enhanced_acwr_calculations)
SELECT 'enhanced_acwr_calculations' as table_name,
       COUNT(*) as total_records,
       COUNT(enhanced_acute_chronic_ratio) as non_null_acwr_ratio,
       COUNT(enhanced_chronic_load) as non_null_chronic_load,
       COUNT(enhanced_chronic_trimp) as non_null_chronic_trimp
FROM enhanced_acwr_calculations;

-- ============================================================================
-- 4. SAMPLE DATA INSPECTION
-- ============================================================================

-- Sample data from acwr_enhanced_calculations
SELECT 'acwr_enhanced_calculations' as source_table,
       user_id, activity_id, configuration_id, acwr_ratio, 
       acute_load, chronic_load, calculation_date
FROM acwr_enhanced_calculations
ORDER BY calculation_date DESC
LIMIT 5;

-- Sample data from enhanced_acwr_calculations
SELECT 'enhanced_acwr_calculations' as source_table,
       user_id, activity_date, configuration_id, 
       enhanced_acute_chronic_ratio, enhanced_chronic_load, 
       enhanced_chronic_trimp, calculation_timestamp
FROM enhanced_acwr_calculations
ORDER BY calculation_timestamp DESC
LIMIT 5;
