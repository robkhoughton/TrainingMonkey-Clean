/**
 * Performance Monitoring Hook
 * Implements Real User Monitoring (RUM) metrics for TrainingMonkey
 * 
 * Tracks:
 * - Core Web Vitals (TTFB, FCP, LCP)
 * - Page load timing breakdown
 * - Resource loading metrics
 * - Component-level performance
 */

import { useEffect, useRef, useCallback, useMemo } from 'react';

interface RUMMetrics {
  page: string;
  // Core Web Vitals
  ttfb?: number; // Time to First Byte
  fcp?: number; // First Contentful Paint
  lcp?: number; // Largest Contentful Paint
  
  // Detailed timing breakdown
  dns_time?: number;
  connection_time?: number;
  request_time?: number;
  response_time?: number;
  dom_interactive_time?: number;
  dom_complete_time?: number;
  load_complete?: number;
  
  // Resource metrics
  resource_count?: number;
  total_resource_size?: number;
  
  // Component-specific metrics
  component_mount_time?: number;
  data_fetch_time?: number;
  render_time?: number;
  
  // Context
  timestamp: string;
  user_agent?: string;
  viewport_width?: number;
  viewport_height?: number;
  connection_type?: string;
}

interface ComponentPerformanceMetrics {
  page: string;
  fetch_time_ms: number;
  process_time_ms: number;
  render_time_ms: number;
  total_time_ms: number;
  data_points?: number;
  error?: string;
}

/**
 * Send metrics to backend
 */
const sendMetrics = async (endpoint: string, metrics: any): Promise<void> => {
  try {
    await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(metrics),
      // Use keepalive to ensure metrics are sent even if page is closing
      keepalive: true
    });
  } catch (error) {
    // Silently fail - don't disrupt user experience for monitoring
    console.warn('Failed to send performance metrics:', error);
  }
};

/**
 * Hook for page-level RUM metrics
 * Captures navigation timing and Core Web Vitals
 */
export const usePagePerformanceMonitoring = (pageName: string) => {
  const metricsReported = useRef(false);

  useEffect(() => {
    // Only report once per page mount
    if (metricsReported.current) return;

    const reportMetrics = () => {
      // Prevent duplicate reporting
      if (metricsReported.current) return;
      metricsReported.current = true;

      const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      
      if (!navigation) {
        console.warn('Navigation timing not available');
        return;
      }

      // Calculate all timing metrics
      const metrics: RUMMetrics = {
        page: pageName,
        
        // Core metrics
        ttfb: Math.round(navigation.responseStart - navigation.requestStart),
        dom_interactive_time: Math.round(navigation.domInteractive - navigation.fetchStart),
        dom_complete_time: Math.round(navigation.domComplete - navigation.fetchStart),
        load_complete: Math.round(navigation.loadEventEnd - navigation.fetchStart),
        
        // Detailed breakdown
        dns_time: Math.round(navigation.domainLookupEnd - navigation.domainLookupStart),
        connection_time: Math.round(navigation.connectEnd - navigation.connectStart),
        request_time: Math.round(navigation.responseStart - navigation.requestStart),
        response_time: Math.round(navigation.responseEnd - navigation.responseStart),
        
        // Resource metrics
        resource_count: performance.getEntriesByType('resource').length,
        total_resource_size: performance.getEntriesByType('resource').reduce(
          (sum, resource: any) => sum + (resource.transferSize || 0), 
          0
        ),
        
        // Context
        timestamp: new Date().toISOString(),
        user_agent: navigator.userAgent,
        viewport_width: window.innerWidth,
        viewport_height: window.innerHeight,
        connection_type: (navigator as any).connection?.effectiveType || 'unknown'
      };

      // Try to get Largest Contentful Paint (LCP) if available
      try {
        const lcpEntry = performance.getEntriesByType('largest-contentful-paint').slice(-1)[0] as any;
        if (lcpEntry) {
          metrics.lcp = Math.round(lcpEntry.renderTime || lcpEntry.loadTime);
        }
      } catch (e) {
        // LCP not available in all browsers
      }

      console.log('📊 Page Performance Metrics:', {
        page: pageName,
        ttfb: `${metrics.ttfb}ms`,
        domComplete: `${metrics.dom_complete_time}ms`,
        loadComplete: `${metrics.load_complete}ms`,
        lcp: metrics.lcp ? `${metrics.lcp}ms` : 'N/A'
      });

      // Send to backend
      sendMetrics('/api/analytics/rum-metrics', metrics);
    };

    // Report after load completes or after a short delay
    if (document.readyState === 'complete') {
      // Small delay to ensure all timing is captured
      setTimeout(reportMetrics, 100);
    } else {
      window.addEventListener('load', () => setTimeout(reportMetrics, 100));
    }

    // Cleanup
    return () => {
      metricsReported.current = false;
    };
  }, [pageName]);
};

/**
 * Hook for component-level performance monitoring
 * Tracks data fetching, processing, and rendering time
 */
export const useComponentPerformanceMonitoring = (componentName: string) => {
  const startTime = useRef(performance.now());
  const fetchStartTime = useRef<number | null>(null);
  const fetchEndTime = useRef<number | null>(null);

  const trackFetchStart = useCallback(() => {
    fetchStartTime.current = performance.now();
  }, []);

  const trackFetchEnd = useCallback(() => {
    fetchEndTime.current = performance.now();
  }, []);

  const reportMetrics = useCallback((dataPoints?: number, error?: string) => {
    const totalTime = performance.now() - startTime.current;
    const fetchTime = (fetchStartTime.current && fetchEndTime.current)
      ? fetchEndTime.current - fetchStartTime.current
      : 0;
    const processTime = fetchEndTime.current
      ? performance.now() - fetchEndTime.current
      : 0;

    const metrics: ComponentPerformanceMetrics = {
      page: componentName,
      fetch_time_ms: Math.round(fetchTime),
      process_time_ms: Math.round(processTime),
      render_time_ms: Math.round(totalTime - fetchTime - processTime),
      total_time_ms: Math.round(totalTime),
      data_points: dataPoints,
      error: error
    };

    console.log(`📈 Component Performance (${componentName}):`, {
      fetch: `${metrics.fetch_time_ms}ms`,
      process: `${metrics.process_time_ms}ms`,
      render: `${metrics.render_time_ms}ms`,
      total: `${metrics.total_time_ms}ms`,
      dataPoints: dataPoints || 'N/A'
    });

    sendMetrics('/api/analytics/component-performance', metrics);
  }, [componentName]);

  return useMemo(() => ({
    trackFetchStart,
    trackFetchEnd,
    reportMetrics
  }), [trackFetchStart, trackFetchEnd, reportMetrics]);
};

/**
 * Track individual API call performance
 */
export const trackAPIPerformance = async (
  apiName: string, 
  fetchFn: () => Promise<any>
): Promise<any> => {
  const start = performance.now();
  
  try {
    const result = await fetchFn();
    const duration = Math.round(performance.now() - start);
    
    // Log to console
    console.log(`🌐 API Call (${apiName}): ${duration}ms`);
    
    // Send to backend (async, don't wait)
    sendMetrics('/api/analytics/api-timing', {
      api_name: apiName,
      duration_ms: duration,
      success: true,
      timestamp: new Date().toISOString()
    });
    
    return result;
  } catch (error) {
    const duration = Math.round(performance.now() - start);
    
    console.error(`🌐 API Call Failed (${apiName}): ${duration}ms`, error);
    
    sendMetrics('/api/analytics/api-timing', {
      api_name: apiName,
      duration_ms: duration,
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
      timestamp: new Date().toISOString()
    });
    
    throw error;
  }
};




