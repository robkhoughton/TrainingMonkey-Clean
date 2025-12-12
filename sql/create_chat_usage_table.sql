-- Chat Usage Tracking Table
-- Tracks daily token usage and message counts per user for rate limiting

CREATE TABLE IF NOT EXISTS chat_usage (
    user_id INTEGER REFERENCES user_settings(id),
    date TEXT NOT NULL,
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    message_count INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, date)
);

-- Index for efficient lookups by user and date
CREATE INDEX IF NOT EXISTS idx_chat_usage_user_date ON chat_usage(user_id, date);
