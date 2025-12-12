-- Add column to track email collection modal dismissals
-- Run this in SQL Editor before deploying new code

ALTER TABLE user_settings 
ADD COLUMN IF NOT EXISTS email_modal_dismissals INTEGER DEFAULT 0;

-- Verify the column was added
SELECT column_name, data_type, column_default
FROM information_schema.columns 
WHERE table_name = 'user_settings' 
AND column_name = 'email_modal_dismissals';

-- Check current email status
SELECT 
    COUNT(*) as total_users,
    COUNT(CASE WHEN email LIKE '%@training-monkey.com' THEN 1 END) as synthetic_emails,
    COUNT(CASE WHEN email NOT LIKE '%@training-monkey.com' THEN 1 END) as real_emails
FROM user_settings;






