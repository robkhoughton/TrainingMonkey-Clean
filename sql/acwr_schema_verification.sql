-- ACWR Schema Verification Queries (PostgreSQL)
-- Execute these queries to verify the ACWR configuration schema was created correctly

-- 1. Verify all ACWR tables exist
SELECT table_name, table_type 
FROM information_schema.tables 
WHERE table_name IN ('acwr_configurations', 'user_acwr_configurations', 'enhanced_acwr_calculations')
ORDER BY table_name;

-- 2. Verify acwr_configurations table structure
SELECT 
    column_name, 
    data_type, 
    is_nullable, 
    column_default,
    character_maximum_length
FROM information_schema.columns 
WHERE table_name = 'acwr_configurations'
ORDER BY ordinal_position;

-- 3. Verify user_acwr_configurations table structure
SELECT 
    column_name, 
    data_type, 
    is_nullable, 
    column_default,
    character_maximum_length
FROM information_schema.columns 
WHERE table_name = 'user_acwr_configurations'
ORDER BY ordinal_position;

-- 4. Verify enhanced_acwr_calculations table structure
SELECT 
    column_name, 
    data_type, 
    is_nullable, 
    column_default,
    character_maximum_length
FROM information_schema.columns 
WHERE table_name = 'enhanced_acwr_calculations'
ORDER BY ordinal_position;

-- 5. Verify primary key constraints
SELECT 
    tc.table_name, 
    kcu.column_name,
    tc.constraint_name,
    tc.constraint_type
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu 
    ON tc.constraint_name = kcu.constraint_name
WHERE tc.table_name IN ('acwr_configurations', 'user_acwr_configurations', 'enhanced_acwr_calculations')
    AND tc.constraint_type = 'PRIMARY KEY'
ORDER BY tc.table_name, kcu.ordinal_position;

-- 6. Verify foreign key constraints
SELECT 
    tc.table_name, 
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name,
    tc.constraint_name
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu 
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage ccu 
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.table_name IN ('acwr_configurations', 'user_acwr_configurations', 'enhanced_acwr_calculations')
    AND tc.constraint_type = 'FOREIGN KEY'
ORDER BY tc.table_name, kcu.column_name;

-- 7. Verify unique constraints
SELECT 
    tc.table_name, 
    kcu.column_name,
    tc.constraint_name,
    tc.constraint_type
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu 
    ON tc.constraint_name = kcu.constraint_name
WHERE tc.table_name IN ('acwr_configurations', 'user_acwr_configurations', 'enhanced_acwr_calculations')
    AND tc.constraint_type = 'UNIQUE'
ORDER BY tc.table_name, kcu.column_name;

-- 8. Verify check constraints
SELECT 
    tc.table_name, 
    tc.constraint_name,
    cc.check_clause
FROM information_schema.table_constraints tc
JOIN information_schema.check_constraints cc 
    ON tc.constraint_name = cc.constraint_name
WHERE tc.table_name IN ('acwr_configurations', 'user_acwr_configurations', 'enhanced_acwr_calculations')
    AND tc.constraint_type = 'CHECK'
ORDER BY tc.table_name, tc.constraint_name;

-- 9. Verify indexes were created
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes 
WHERE tablename IN ('acwr_configurations', 'user_acwr_configurations', 'enhanced_acwr_calculations')
ORDER BY tablename, indexname;

-- 10. Verify default configuration was inserted
SELECT 
    id,
    name,
    description,
    chronic_period_days,
    decay_rate,
    is_active,
    created_by,
    notes
FROM acwr_configurations 
WHERE name = 'default_enhanced';

-- 11. Verify sequence objects for SERIAL columns
SELECT 
    sequence_name,
    data_type,
    start_value,
    minimum_value,
    maximum_value,
    increment
FROM information_schema.sequences 
WHERE sequence_name LIKE '%acwr%'
ORDER BY sequence_name;

-- 12. Test data integrity constraints
-- This should succeed (valid data)
INSERT INTO acwr_configurations (name, description, chronic_period_days, decay_rate, is_active, created_by)
VALUES ('test_config', 'Test configuration', 35, 0.08, TRUE, 1);

-- This should fail (invalid chronic_period_days < 28)
-- INSERT INTO acwr_configurations (name, description, chronic_period_days, decay_rate, is_active, created_by)
-- VALUES ('invalid_config', 'Invalid config', 20, 0.05, TRUE, 1);

-- This should fail (invalid decay_rate > 1.0)
-- INSERT INTO acwr_configurations (name, description, chronic_period_days, decay_rate, is_active, created_by)
-- VALUES ('invalid_config2', 'Invalid config 2', 30, 1.5, TRUE, 1);

-- Clean up test data
DELETE FROM acwr_configurations WHERE name = 'test_config';

-- 13. Summary verification
SELECT 
    'Tables Created' as verification_type,
    COUNT(*) as count
FROM information_schema.tables 
WHERE table_name IN ('acwr_configurations', 'user_acwr_configurations', 'enhanced_acwr_calculations')

UNION ALL

SELECT 
    'Indexes Created' as verification_type,
    COUNT(*) as count
FROM pg_indexes 
WHERE tablename IN ('acwr_configurations', 'user_acwr_configurations', 'enhanced_acwr_calculations')

UNION ALL

SELECT 
    'Default Configuration' as verification_type,
    COUNT(*) as count
FROM acwr_configurations 
WHERE name = 'default_enhanced';
