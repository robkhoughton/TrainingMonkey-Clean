# Performance Monitoring Implementation (RUM Metrics)

**Date:** October 11, 2025  
**Status:** ✅ Implemented - Ready for Testing

---

## 📊 Overview

Implemented comprehensive Real User Monitoring (RUM) system to track app efficiency and page load delays. This system captures:

1. **Page-Level Metrics** - Core Web Vitals, load timing, resource metrics
2. **Component Performance** - React component fetch/render breakdown
3. **API Timing** - Client-side API call performance

---

## ✅ What Was Implemented

### 1. Frontend Performance Monitoring Hooks

**File:** `frontend/src/usePerformanceMonitoring.ts`

Three new React hooks:
- `usePagePerformanceMonitoring(pageName)` - Tracks page load metrics
- `useComponentPerformanceMonitoring(componentName)` - Tracks component performance
- `trackAPIPerformance(apiName, fetchFn)` - Tracks individual API calls

**Features:**
- Automatic metric capture using browser Performance API
- Core Web Vitals tracking (TTFB, FCP, LCP)
- Detailed timing breakdown (DNS, connection, response, render)
- Resource loading metrics
- Non-blocking error handling

### 2. Frontend Integration

Added performance monitoring to all main pages:

| Page | File | Monitoring Type |
|------|------|-----------------|
| Dashboard | `TrainingLoadDashboard.tsx` | Page + Component |
| Activities | `ActivitiesPage.tsx` | Page + Component |
| Journal | `JournalPage.tsx` | Page + Component |
| Settings | `SettingsPage.tsx` | Page only |

**Example Metrics Logged:**
```
📊 Page Performance Metrics:
  - Page: dashboard
  - TTFB: 245ms
  - DOM Complete: 1,234ms
  - Load Complete: 1,456ms
  - LCP: 1,122ms

📈 Component Performance (TrainingLoadDashboard):
  - Fetch: 325ms
  - Process: 45ms
  - Render: 123ms
  - Total: 493ms
  - Data Points: 120
```

### 3. Backend API Endpoints

**File:** `app/strava_app.py` (lines 2325-2479)

Three new endpoints for receiving metrics:

#### `/api/analytics/rum-metrics` (POST)
Receives page-level RUM metrics from frontend
- Core Web Vitals (TTFB, FCP, LCP)
- Timing breakdown (DNS, connection, render)
- Resource metrics (count, size)
- Context (viewport, connection type)

#### `/api/analytics/component-performance` (POST)
Receives component-level performance data
- Fetch time (API calls)
- Processing time (data transformation)
- Render time (React rendering)
- Error tracking

#### `/api/analytics/api-timing` (POST)
Receives client-side API call timing
- Duration (including network latency)
- Success/failure status
- Error messages

**Design Notes:**
- All endpoints return 200 even on error (non-blocking)
- Metrics logged to console for immediate visibility
- Uses existing `db_utils` connection management
- PostgreSQL parameterized queries (%s placeholders)

### 4. Database Schema

**File:** `sql/create_rum_metrics_tables.sql`

Three new tables with proper indexes and retention policies:

#### `rum_metrics` - Page Load Metrics
- Core Web Vitals (ttfb, fcp, lcp)
- Detailed timing breakdown
- Resource metrics
- User context (viewport, connection type)
- Indexed on: page, user_id, timestamp, lcp, ttfb

#### `component_performance` - Component Metrics
- Fetch/process/render timing
- Data point counts
- Error tracking
- Indexed on: page, user_id, timestamp, slow queries

#### `api_timing_client` - Client-Side API Timing
- API call duration
- Success/error status
- Indexed on: api_name, user_id, timestamp, slow queries

**Retention Policy:**
- 90-day retention (matching existing `api_logs`)
- Cleanup function: `cleanup_rum_metrics(days_to_keep)`
- To be scheduled in Cloud Scheduler/cron

---

## 🚀 Deployment Steps

### Step 1: Create Database Tables

```bash
# Run SQL script manually in SQL Editor (per project rules)
# Execute: sql/create_rum_metrics_tables.sql
```

**Expected result:** 3 new tables created with indexes

### Step 2: Build Frontend

```bash
cd frontend
npm run build
cd ..
```

### Step 3: Deploy to Cloud

```bash
# Use existing deployment script
.\scripts\deploy.bat
# or
gcloud app deploy
```

### Step 4: Verify Deployment

1. Open browser DevTools Console
2. Navigate to Dashboard
3. Look for console logs:
   ```
   📊 Page Performance Metrics: {...}
   📈 Component Performance: {...}
   ```

### Step 5: Schedule Cleanup Job

Add to Cloud Scheduler:
```sql
-- Run daily at 2 AM
SELECT cleanup_rum_metrics(90);
```

---

## 📈 How to Analyze Performance

### Query 1: Page Load Summary (Last 7 Days)

```sql
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
```

**What to look for:**
- avg_load_ms < 2000 (good), < 3000 (acceptable), > 3000 (slow)
- avg_lcp_ms < 2500 (good), 2500-4000 (needs improvement), > 4000 (poor)
- p95_load_ms should be < 5000

### Query 2: Component Performance Breakdown

```sql
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
```

**What to look for:**
- Fetch time > 1000ms = slow API
- Process time > 500ms = inefficient data transformation
- Render time > 500ms = complex UI rendering
- Error count > 5% of loads = reliability issue

### Query 3: Identify Slow Page Loads

```sql
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
```

### Query 4: Network Latency Analysis

Compare client-side timing (includes network) vs server-side timing:

```sql
SELECT 
    endpoint,
    COUNT(*) as requests,
    ROUND(AVG(response_time_ms)) as avg_server_ms,
    (SELECT ROUND(AVG(duration_ms)) 
     FROM api_timing_client 
     WHERE api_name LIKE '%' || endpoint || '%'
       AND timestamp > NOW() - INTERVAL '24 hours'
    ) as avg_client_ms,
    -- Network latency = client time - server time
    (SELECT ROUND(AVG(duration_ms)) 
     FROM api_timing_client 
     WHERE api_name LIKE '%' || endpoint || '%'
       AND timestamp > NOW() - INTERVAL '24 hours'
    ) - ROUND(AVG(response_time_ms)) as avg_network_latency_ms
FROM api_logs
WHERE timestamp > NOW() - INTERVAL '24 hours'
  AND status_code = 200
GROUP BY endpoint
ORDER BY avg_network_latency_ms DESC
LIMIT 20;
```

---

## 🎯 Performance Targets

### Core Web Vitals (Google Standards)

| Metric | Good | Needs Improvement | Poor |
|--------|------|-------------------|------|
| **LCP** (Largest Contentful Paint) | < 2.5s | 2.5s - 4.0s | > 4.0s |
| **FID** (First Input Delay) | < 100ms | 100ms - 300ms | > 300ms |
| **CLS** (Cumulative Layout Shift) | < 0.1 | 0.1 - 0.25 | > 0.25 |

### TrainingMonkey Targets

| Metric | Target | Current Status |
|--------|--------|----------------|
| Dashboard Load | < 2s | To be measured |
| TTFB | < 500ms | To be measured |
| API Response Time | < 1s | ~674ms (from api_logs) |
| Component Render | < 500ms | To be measured |
| Error Rate | < 5% | Currently 16% (needs improvement) |

---

## 🔍 Lighthouse Audit

### How to Run Lighthouse

**Option 1: Chrome DevTools**
1. Open your deployed app in Chrome
2. Open DevTools (F12)
3. Go to "Lighthouse" tab
4. Select "Performance" category
5. Click "Analyze page load"

**Option 2: Command Line**
```bash
# Install Lighthouse CLI
npm install -g lighthouse

# Run audit on deployed app
lighthouse https://your-app-url.com --view --only-categories=performance

# Save results
lighthouse https://your-app-url.com --output=html --output-path=./lighthouse-report.html
```

**Option 3: PageSpeed Insights**
Visit: https://pagespeed.web.dev/  
Enter your app URL

### What Lighthouse Measures

- **Performance Score** (0-100)
- **First Contentful Paint (FCP)** - When first content appears
- **Largest Contentful Paint (LCP)** - When main content visible
- **Total Blocking Time (TBT)** - How long page is unresponsive
- **Cumulative Layout Shift (CLS)** - Visual stability
- **Speed Index** - How quickly content is visually displayed

### Expected Issues to Address

Based on typical React SPA patterns, you may see:
1. **Large JavaScript bundles** - Consider code splitting
2. **Render-blocking resources** - Optimize CSS/JS loading
3. **Image optimization** - Compress and lazy-load images
4. **Unused JavaScript** - Tree-shake dependencies
5. **Third-party scripts** - Defer non-critical scripts

---

## 📊 Sample Output

After deployment, you'll see logs like this:

**Server Logs:**
```
INFO: RUM Metrics - Page: dashboard, TTFB: 245ms, Load Complete: 1456ms, LCP: 1122ms
INFO: Component Performance - TrainingLoadDashboard: Fetch: 325ms, Process: 45ms, Render: 123ms, Total: 493ms
INFO: API Timing - training-data: 352ms
```

**Browser Console:**
```javascript
📊 Page Performance Metrics: {
  page: 'dashboard',
  ttfb: '245ms',
  domComplete: '1234ms',
  loadComplete: '1456ms',
  lcp: '1122ms'
}

📈 Component Performance (TrainingLoadDashboard): {
  fetch: '325ms',
  process: '45ms',
  render: '123ms',
  total: '493ms',
  dataPoints: 120
}

🌐 API Call (training-data): 352ms
```

---

## 🐛 Troubleshooting

### Issue: No metrics being logged

**Check:**
1. Are database tables created? Run `\dt rum_*` in SQL editor
2. Are endpoints deployed? Check app logs for "PERFORMANCE MONITORING ENDPOINTS"
3. Are frontend changes built? Run `npm run build` in frontend/
4. Check browser console for errors in performance monitoring

### Issue: Metrics logging but errors in console

**Common causes:**
- Database connection issues → Check db_utils connection pool
- Missing user_id reference → Check users table exists
- TypeScript compilation errors → Run `npm run build` and fix errors

### Issue: Performance seems worse after adding monitoring

**Expected:** Minimal overhead (< 10ms per page load)
- Metrics are sent async with `keepalive: true`
- Failed metrics don't block page load
- Consider sampling (only log 10% of page loads for high-traffic)

---

## 📝 Next Steps

1. **Deploy changes** (run deployment script)
2. **Create database tables** (execute SQL script)
3. **Run Lighthouse audit** (document baseline scores)
4. **Collect 7 days of data** (let metrics accumulate)
5. **Analyze performance** (run queries above)
6. **Identify bottlenecks** (focus on slowest pages/components)
7. **Optimize** (based on data, not assumptions)
8. **Measure again** (verify improvements)

---

## 🎓 Key Learnings

1. **Measure first, optimize second** - Don't guess at bottlenecks
2. **User experience varies** - Network, device, location all matter
3. **Server time ≠ User time** - Network latency is significant
4. **95th percentile matters** - Average doesn't show worst-case experience
5. **Monitor continuously** - Performance degrades over time

---

## 📚 Additional Resources

- [Web Vitals Guide](https://web.dev/vitals/)
- [Lighthouse Documentation](https://developers.google.com/web/tools/lighthouse)
- [React Performance](https://react.dev/learn/render-and-commit)
- [PostgreSQL Performance](https://www.postgresql.org/docs/current/performance-tips.html)

---

**Implementation by:** Cursor AI Assistant  
**Review Status:** ⏳ Pending user testing  
**Deployment Status:** ⏳ Ready to deploy




