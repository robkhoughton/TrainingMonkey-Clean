-- ============================================================================
-- Real User Monitoring (RUM) Metrics Tables
-- ============================================================================
-- These tables capture frontend performance metrics for TrainingMonkey
-- Created: 2025-10-11
--
-- IMPORTANT: Execute these CREATE TABLE statements manually in SQL Editor
-- Per project rules, do not execute schema changes via application code
-- ============================================================================

-- Table 1: Page-Level RUM Metrics
-- Captures Core Web Vitals and page load timing
CREATE TABLE IF NOT EXISTS rum_metrics (
    id SERIAL PRIMARY KEY,
    page VARCHAR(100) NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    
    -- Core Web Vitals
    ttfb INTEGER,                       -- Time to First Byte (ms)
    fcp INTEGER,                        -- First Contentful Paint (ms)
    lcp INTEGER,                        -- Largest Contentful Paint (ms)
    
    -- Detailed Timing Breakdown
    dns_time INTEGER,                   -- DNS lookup time (ms)
    connection_time INTEGER,            -- TCP connection time (ms)
    request_time INTEGER,               -- Request time (ms)
    response_time INTEGER,              -- Response download time (ms)
    dom_interactive_time INTEGER,       -- DOM Interactive time (ms)
    dom_complete_time INTEGER,          -- DOM Complete time (ms)
    load_complete INTEGER,              -- Full page load time (ms)
    
    -- Resource Metrics
    resource_count INTEGER,             -- Number of resources loaded
    total_resource_size BIGINT,         -- Total bytes transferred
    
    -- Context Information
    user_agent TEXT,                    -- Browser user agent
    viewport_width INTEGER,             -- Browser viewport width (px)
    viewport_height INTEGER,            -- Browser viewport height (px)
    connection_type VARCHAR(50),        -- Connection type (4g, wifi, etc)
    
    -- Timestamp
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for RUM metrics
CREATE INDEX IF NOT EXISTS idx_rum_page ON rum_metrics(page, timestamp);
CREATE INDEX IF NOT EXISTS idx_rum_user ON rum_metrics(user_id);
CREATE INDEX IF NOT EXISTS idx_rum_timestamp ON rum_metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_rum_lcp ON rum_metrics(lcp) WHERE lcp IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_rum_ttfb ON rum_metrics(ttfb) WHERE ttfb IS NOT NULL;

-- Table comments
COMMENT ON TABLE rum_metrics IS 'Real User Monitoring metrics capturing page load performance and Core Web Vitals';
COMMENT ON COLUMN rum_metrics.ttfb IS 'Time to First Byte - server response time';
COMMENT ON COLUMN rum_metrics.fcp IS 'First Contentful Paint - when first content renders';
COMMENT ON COLUMN rum_metrics.lcp IS 'Largest Contentful Paint - when main content visible (Core Web Vital)';
COMMENT ON COLUMN rum_metrics.load_complete IS 'Total page load time from navigation start';


-- ============================================================================
-- Table 2: Component-Level Performance Metrics
-- Captures React component render and data fetch performance
-- ============================================================================

CREATE TABLE IF NOT EXISTS component_performance (
    id SERIAL PRIMARY KEY,
    page VARCHAR(100) NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    
    -- Performance Breakdown
    fetch_time_ms INTEGER,              -- Time to fetch data from API (ms)
    process_time_ms INTEGER,            -- Time to process/transform data (ms)
    render_time_ms INTEGER,             -- Time to render component (ms)
    total_time_ms INTEGER,              -- Total time from mount to complete (ms)
    
    -- Data Context
    data_points INTEGER,                -- Number of data points processed
    error TEXT,                         -- Error message if load failed
    
    -- Timestamp
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for component performance
CREATE INDEX IF NOT EXISTS idx_comp_perf_page ON component_performance(page, timestamp);
CREATE INDEX IF NOT EXISTS idx_comp_perf_user ON component_performance(user_id);
CREATE INDEX IF NOT EXISTS idx_comp_perf_timestamp ON component_performance(timestamp);
CREATE INDEX IF NOT EXISTS idx_comp_perf_slow ON component_performance(total_time_ms) WHERE total_time_ms > 2000;

-- Table comments
COMMENT ON TABLE component_performance IS 'Component-level performance metrics for React components';
COMMENT ON COLUMN component_performance.fetch_time_ms IS 'Time spent fetching data from backend APIs';
COMMENT ON COLUMN component_performance.process_time_ms IS 'Time spent processing and transforming data in JavaScript';
COMMENT ON COLUMN component_performance.render_time_ms IS 'Time spent in React rendering and DOM updates';


-- ============================================================================
-- Table 3: Client-Side API Timing
-- Captures frontend perspective of API call performance
-- ============================================================================

CREATE TABLE IF NOT EXISTS api_timing_client (
    id SERIAL PRIMARY KEY,
    api_name VARCHAR(255) NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    
    -- Timing
    duration_ms INTEGER NOT NULL,       -- Total API call duration (ms)
    success BOOLEAN NOT NULL,           -- Whether call succeeded
    error TEXT,                         -- Error message if failed
    
    -- Timestamp
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for API timing
CREATE INDEX IF NOT EXISTS idx_api_timing_name ON api_timing_client(api_name, timestamp);
CREATE INDEX IF NOT EXISTS idx_api_timing_user ON api_timing_client(user_id);
CREATE INDEX IF NOT EXISTS idx_api_timing_timestamp ON api_timing_client(timestamp);
CREATE INDEX IF NOT EXISTS idx_api_timing_slow ON api_timing_client(duration_ms) WHERE duration_ms > 1000;

-- Table comments
COMMENT ON TABLE api_timing_client IS 'Client-side API call timing (complements server-side api_logs table)';
COMMENT ON COLUMN api_timing_client.duration_ms IS 'Total time from fetch() call to response received, including network latency';


-- ============================================================================
-- Retention Policies
-- ============================================================================
-- Keep RUM metrics for 90 days (matching api_logs retention)
-- Run cleanup daily via Cloud Scheduler or cron

-- Cleanup function for RUM metrics
CREATE OR REPLACE FUNCTION cleanup_rum_metrics(days_to_keep INTEGER DEFAULT 90)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM rum_metrics 
    WHERE timestamp < NOW() - (days_to_keep || ' days')::INTERVAL;
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    DELETE FROM component_performance 
    WHERE timestamp < NOW() - (days_to_keep || ' days')::INTERVAL;
    
    DELETE FROM api_timing_client 
    WHERE timestamp < NOW() - (days_to_keep || ' days')::INTERVAL;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION cleanup_rum_metrics IS 'Remove RUM metrics older than specified days (default 90)';


-- ============================================================================
-- Useful Queries for Performance Analysis
-- ============================================================================

-- Query 1: Average page load metrics by page
/*
SELECT 
    page,
    COUNT(*) as page_loads,
    ROUND(AVG(ttfb)) as avg_ttfb_ms,
    ROUND(AVG(load_complete)) as avg_load_ms,
    ROUND(AVG(lcp)) as avg_lcp_ms,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY load_complete) as p95_load_ms
FROM rum_metrics
WHERE timestamp > NOW() - INTERVAL '7 days'
GROUP BY page
ORDER BY avg_load_ms DESC;
*/

-- Query 2: Component performance summary
/*
SELECT 
    page,
    COUNT(*) as loads,
    ROUND(AVG(fetch_time_ms)) as avg_fetch_ms,
    ROUND(AVG(process_time_ms)) as avg_process_ms,
    ROUND(AVG(render_time_ms)) as avg_render_ms,
    ROUND(AVG(total_time_ms)) as avg_total_ms,
    COUNT(CASE WHEN error IS NOT NULL THEN 1 END) as error_count
FROM component_performance
WHERE timestamp > NOW() - INTERVAL '7 days'
GROUP BY page
ORDER BY avg_total_ms DESC;
*/

-- Query 3: Slow page loads (LCP > 2.5s is poor)
/*
SELECT 
    page,
    user_id,
    ttfb,
    load_complete,
    lcp,
    connection_type,
    timestamp
FROM rum_metrics
WHERE lcp > 2500
  AND timestamp > NOW() - INTERVAL '24 hours'
ORDER BY lcp DESC
LIMIT 20;
*/

-- Query 4: API performance comparison (client vs server)
/*
SELECT 
    act.api_name,
    COUNT(*) as calls,
    ROUND(AVG(act.duration_ms)) as avg_client_ms,
    (SELECT ROUND(AVG(al.response_time_ms))
     FROM api_logs al 
     WHERE al.endpoint LIKE '%' || SUBSTRING(act.api_name FROM '/api/(.+)') || '%'
       AND al.timestamp > NOW() - INTERVAL '24 hours'
    ) as avg_server_ms,
    ROUND(AVG(act.duration_ms) - 
     (SELECT AVG(al.response_time_ms)
      FROM api_logs al 
      WHERE al.endpoint LIKE '%' || SUBSTRING(act.api_name FROM '/api/(.+)') || '%'
        AND al.timestamp > NOW() - INTERVAL '24 hours'
     )) as avg_network_latency_ms
FROM api_timing_client act
WHERE act.timestamp > NOW() - INTERVAL '24 hours'
GROUP BY act.api_name
ORDER BY avg_client_ms DESC;
*/


-- ============================================================================
-- END RUM METRICS SCHEMA
-- ============================================================================




