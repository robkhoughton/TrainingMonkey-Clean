#!/usr/bin/env python3
"""
Create RUM Metrics Tables in PostgreSQL
Direct database connection per project rules
"""

import psycopg2
import sys

DATABASE_URL = "postgresql://appuser:trainmonk25@35.223.144.85:5432/train-d"

def create_rum_tables():
    """Create RUM metrics tables with indexes and cleanup function"""
    
    try:
        print("Connecting to PostgreSQL database...")
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Table 1: rum_metrics
        print("\nCreating rum_metrics table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rum_metrics (
                id SERIAL PRIMARY KEY,
                page VARCHAR(100) NOT NULL,
                user_id INTEGER,
                
                -- Core Web Vitals
                ttfb INTEGER,
                fcp INTEGER,
                lcp INTEGER,
                
                -- Detailed Timing Breakdown
                dns_time INTEGER,
                connection_time INTEGER,
                request_time INTEGER,
                response_time INTEGER,
                dom_interactive_time INTEGER,
                dom_complete_time INTEGER,
                load_complete INTEGER,
                
                -- Resource Metrics
                resource_count INTEGER,
                total_resource_size BIGINT,
                
                -- Context Information
                user_agent TEXT,
                viewport_width INTEGER,
                viewport_height INTEGER,
                connection_type VARCHAR(50),
                
                -- Timestamp
                timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
        print("  [SUCCESS] rum_metrics table created")
        
        # Indexes for rum_metrics
        print("Creating indexes for rum_metrics...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rum_page ON rum_metrics(page, timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rum_user ON rum_metrics(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rum_timestamp ON rum_metrics(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rum_lcp ON rum_metrics(lcp) WHERE lcp IS NOT NULL")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rum_ttfb ON rum_metrics(ttfb) WHERE ttfb IS NOT NULL")
        print("  [SUCCESS] rum_metrics indexes created")
        
        # Table comments
        cursor.execute("COMMENT ON TABLE rum_metrics IS 'Real User Monitoring metrics capturing page load performance and Core Web Vitals'")
        
        # Table 2: component_performance
        print("\nCreating component_performance table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS component_performance (
                id SERIAL PRIMARY KEY,
                page VARCHAR(100) NOT NULL,
                user_id INTEGER,
                
                -- Performance Breakdown
                fetch_time_ms INTEGER,
                process_time_ms INTEGER,
                render_time_ms INTEGER,
                total_time_ms INTEGER,
                
                -- Data Context
                data_points INTEGER,
                error TEXT,
                
                -- Timestamp
                timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
        print("  [SUCCESS] component_performance table created")
        
        # Indexes for component_performance
        print("Creating indexes for component_performance...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_comp_perf_page ON component_performance(page, timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_comp_perf_user ON component_performance(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_comp_perf_timestamp ON component_performance(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_comp_perf_slow ON component_performance(total_time_ms) WHERE total_time_ms > 2000")
        print("  [SUCCESS] component_performance indexes created")
        
        # Table comments
        cursor.execute("COMMENT ON TABLE component_performance IS 'Component-level performance metrics for React components'")
        
        # Table 3: api_timing_client
        print("\nCreating api_timing_client table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_timing_client (
                id SERIAL PRIMARY KEY,
                api_name VARCHAR(255) NOT NULL,
                user_id INTEGER,
                
                -- Timing
                duration_ms INTEGER NOT NULL,
                success BOOLEAN NOT NULL,
                error TEXT,
                
                -- Timestamp
                timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
        print("  [SUCCESS] api_timing_client table created")
        
        # Indexes for api_timing_client
        print("Creating indexes for api_timing_client...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_api_timing_name ON api_timing_client(api_name, timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_api_timing_user ON api_timing_client(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_api_timing_timestamp ON api_timing_client(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_api_timing_slow ON api_timing_client(duration_ms) WHERE duration_ms > 1000")
        print("  [SUCCESS] api_timing_client indexes created")
        
        # Table comments
        cursor.execute("COMMENT ON TABLE api_timing_client IS 'Client-side API call timing (complements server-side api_logs table)'")
        
        # Create cleanup function
        print("\nCreating cleanup function...")
        cursor.execute("""
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
        """)
        cursor.execute("COMMENT ON FUNCTION cleanup_rum_metrics IS 'Remove RUM metrics older than specified days (default 90)'")
        print("  [SUCCESS] cleanup_rum_metrics function created")
        
        # Commit all changes
        conn.commit()
        
        # Verify tables exist
        print("\nVerifying tables...")
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('rum_metrics', 'component_performance', 'api_timing_client')
            ORDER BY table_name
        """)
        tables = cursor.fetchall()
        print(f"  Found {len(tables)} tables:")
        for table in tables:
            print(f"    - {table[0]}")
        
        # Check row counts
        print("\nChecking table status...")
        for table_name in ['rum_metrics', 'component_performance', 'api_timing_client']:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  {table_name}: {count} rows")
        
        cursor.close()
        conn.close()
        
        print("\n" + "="*60)
        print("SUCCESS: All RUM metrics tables created successfully!")
        print("="*60)
        print("\nNext steps:")
        print("1. Build frontend: cd frontend && npm run build")
        print("2. Deploy app: .\\scripts\\deploy.bat")
        print("3. Run Lighthouse audit: .\\run_lighthouse_audit.bat")
        print("4. Monitor metrics in browser console")
        
        return True
        
    except psycopg2.Error as e:
        print(f"\nERROR: Database error occurred")
        print(f"Details: {e}")
        return False
        
    except Exception as e:
        print(f"\nERROR: Unexpected error")
        print(f"Details: {e}")
        return False


if __name__ == "__main__":
    success = create_rum_tables()
    sys.exit(0 if success else 1)




