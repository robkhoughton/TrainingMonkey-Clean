-- API Logs Table for Comprehensive Monitoring
-- This table tracks API request/response data for performance monitoring

CREATE TABLE IF NOT EXISTS api_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    response_time_ms INTEGER,
    status_code INTEGER,
    user_id INTEGER,
    error_message TEXT,
    request_size_bytes INTEGER,
    response_size_bytes INTEGER,
    user_agent TEXT,
    ip_address INET,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_api_logs_timestamp ON api_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_api_logs_endpoint ON api_logs(endpoint);
CREATE INDEX IF NOT EXISTS idx_api_logs_user_id ON api_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_api_logs_status_code ON api_logs(status_code);

-- Create a composite index for dashboard queries
CREATE INDEX IF NOT EXISTS idx_api_logs_dashboard ON api_logs(timestamp, endpoint, status_code);

-- Add comments for documentation
COMMENT ON TABLE api_logs IS 'Logs API requests and responses for performance monitoring';
COMMENT ON COLUMN api_logs.response_time_ms IS 'Response time in milliseconds';
COMMENT ON COLUMN api_logs.endpoint IS 'API endpoint path (e.g., /api/training-data)';
COMMENT ON COLUMN api_logs.method IS 'HTTP method (GET, POST, PUT, DELETE)';
COMMENT ON COLUMN api_logs.status_code IS 'HTTP status code (200, 404, 500, etc.)';
COMMENT ON COLUMN api_logs.user_id IS 'User ID if authenticated, NULL for anonymous requests';
