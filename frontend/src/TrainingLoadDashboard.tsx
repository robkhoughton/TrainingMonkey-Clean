import React, { useState, useEffect } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, ReferenceArea, ComposedChart, ReferenceLine, Bar
} from 'recharts';
import styles from './TrainingLoadDashboard.module.css';
import defaultTheme from './chartTheme';
import { useChartDimensions } from './useChartDimensions';
import CompactDashboardBanner from './CompactDashboardBanner';

// Define interfaces for your data (keeping your original structure)
interface TrainingDataRow {
  date: string;
  activity_id: number;
  distance_miles: number;
  elevation_gain_feet: number;
  elevation_load_miles: number;
  total_load_miles: number;
  avg_heart_rate: number;
  max_heart_rate: number;
  duration_minutes: number;
  trimp: number;
  time_in_zone1: number;
  time_in_zone2: number;
  time_in_zone3: number;
  time_in_zone4: number;
  time_in_zone5: number;
  acute_chronic_ratio: number;
  trimp_acute_chronic_ratio: number;
  normalized_divergence?: number;
  seven_day_avg_load: number;
  twentyeight_day_avg_load: number;
  seven_day_avg_trimp: number;
  twentyeight_day_avg_trimp: number;
  name: string;
  type: string;
  weight_lbs?: number;
  perceived_effort?: number;
  feeling_score?: number;
  notes?: string;
}

interface ProcessedDataRow extends TrainingDataRow {
  dateObj: Date;
}

interface Metrics {
  externalAcwr: number;
  internalAcwr: number;
  sevenDayAvgLoad: number;
  sevenDayAvgTrimp: number;
  daysSinceRest: number;
  normalizedDivergence: number;
  dashboardConfig?: {
    chronic_period_days: number;
    decay_rate: number;
    is_active: boolean;
  };
}

// LLMRecommendation interface from recommendations_component.ts
interface LLMRecommendation {
  id: number;
  generation_date: string;
  target_date: string;
  valid_until: string;
  daily_recommendation: string;
  weekly_recommendation: string;
  pattern_insights: string;
}

const TrainingLoadDashboard: React.FC = () => {
  console.log("TrainingLoadDashboard component initialized");

  // State variables (restored from your original)
  const [data, setData] = useState<ProcessedDataRow[]>([]);
  const [metrics, setMetrics] = useState<Metrics>({
    externalAcwr: 0,
    internalAcwr: 0,
    sevenDayAvgLoad: 0,
    sevenDayAvgTrimp: 0,
    daysSinceRest: 0,
    normalizedDivergence: 0
  });
  const [dateRange, setDateRange] = useState('14');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [renderKey, setRenderKey] = useState(0);
  const [selectedSports, setSelectedSports] = useState(['running', 'cycling']);
  const [hasCyclingData, setHasCyclingData] = useState(false);
  const [sportSummary, setSportSummary] = useState([]);

  // Recommendation state variables from recommendations_component.ts
  const [recommendation, setRecommendation] = useState<LLMRecommendation | null>(null);
  const [isLoadingRecommendation, setIsLoadingRecommendation] = useState<boolean>(false);

  // FIXED: Proper frozen tooltip state management
  const [frozenTooltipData, setFrozenTooltipData] = useState<{
    payload: any[];
    label: string;
    coordinate: { x: number; y: number };
  } | null>(null);

const getRecommendationDateContext = (recommendation) => {
  if (!recommendation) {
    return {
      targetDate: '',
      displayTitle: 'Training Decision',
      isForToday: false,
      isForTomorrow: false
    };
  }

  // Use Pacific timezone for consistent date comparison with backend
  const today = new Date();
  const pacificToday = new Date(today.toLocaleString("en-US", {timeZone: "America/Los_Angeles"}));
  const todayStr = pacificToday.toISOString().split('T')[0];
  const tomorrow = new Date(pacificToday);
  tomorrow.setDate(tomorrow.getDate() + 1);
  const tomorrowStr = tomorrow.toISOString().split('T')[0];

  // FIXED: Handle both date and timestamp formats for target_date
  let targetDateStr;
  let targetDate;

  if (recommendation.target_date) {
    // Extract just the date part from "2025-08-10T00:00:00Z" or "2025-08-10"
    targetDateStr = recommendation.target_date.split('T')[0];
    targetDate = new Date(targetDateStr + 'T12:00:00');
  } else if (recommendation.generation_date) {
    targetDateStr = recommendation.generation_date.split('T')[0];
    targetDate = new Date(targetDateStr + 'T12:00:00');
  } else {
    return {
      targetDate: '',
      displayTitle: 'Training Decision',
      isForToday: false,
      isForTomorrow: false
    };
  }

  const targetDateFormatted = targetDate.toLocaleDateString(undefined, {
    weekday: 'long',
    month: 'short',
    day: 'numeric'
  });

  let displayTitle = '';
  let isForToday = false;
  let isForTomorrow = false;

  if (targetDateStr === todayStr) {
    displayTitle = `Today's Training Decision (${targetDateFormatted})`;
    isForToday = true;
  } else if (targetDateStr === tomorrowStr) {
    displayTitle = `Tomorrow's Training Decision (${targetDateFormatted})`;
    isForTomorrow = true;
  } else if (targetDate > tomorrow) {
    displayTitle = `Next Training Decision (${targetDateFormatted})`;
  } else {
    displayTitle = `Training Decision (${targetDateFormatted})`;
  }

  return {
    targetDate: targetDateStr,
    displayTitle,
    isForToday,
    isForTomorrow
  };
};

  const handleSyncComplete = () => {
    console.log("Sync completed, refreshing dashboard data...");
    window.location.reload();
  };

  // Get chart dimensions from custom hook
  const chartDimensions = useChartDimensions(dateRange);

  // Use the theme colors
  const colors = defaultTheme.colors;

  // Helper functions - FIXED: Ensure proper function syntax
  const formatXAxis = (dateStr: string): string => {
    if (!dateStr) return '';
    const [year, month, day] = dateStr.split('-').map(Number);
    return `${month}/${day}`;
  };

  const formatTooltipDate = (dateStr: string): string => {
    if (!dateStr) return '';
    try {
      const [year, month, day] = dateStr.split('-').map(Number);
      const dateObj = new Date(year, month - 1, day);
      return dateObj.toLocaleDateString(undefined, {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
    } catch (e) {
      return dateStr;
    }
  };

  const getUnitByMetricName = (metricName: string): string => {
    if (metricName.includes('ACWR') || metricName.includes('Divergence')) {
      return '';
    }
    if (metricName.includes('TRIMP')) {
      return '';
    }
    if (metricName.includes('Elevation Gain')) {
      return ' ft';
    }
    if (metricName.includes('Weight')) {
      return ' lbs';
    }
    if (metricName.includes('Effort') || metricName.includes('Feeling')) {
      return '/10';
    }
    if (metricName.includes('Miles') ||
        metricName.includes('Distance') ||
        metricName.includes('Load') ||
        metricName === 'Total Miles') {
      return ' miles';
    }
    return '';
  };

  // FIXED: Custom tooltip component with proper click-to-freeze functionality
  const CustomTooltip = ({ active, payload, label, coordinate }: any) => {
    // Use frozen data if available, otherwise active data
    const currentData = frozenTooltipData || (active ? { payload, label, coordinate } : null);

    if (!currentData || !currentData.payload || !currentData.payload.length) {
      return null;
    }

    const formattedDate = formatTooltipDate(currentData.label);
    const activityId = currentData.payload[0]?.payload?.activity_id;

    return (
      <div
        style={{
          backgroundColor: 'white',
          border: '2px solid #3b82f6',
          borderRadius: '8px',
          padding: '12px',
          boxShadow: '0 6px 16px rgba(0, 0, 0, 0.2)',
          minWidth: '240px',
          maxWidth: '320px',
          fontSize: '12px',
          fontFamily: 'Arial, sans-serif',
          position: frozenTooltipData ? 'fixed' : 'relative',
          zIndex: 50000,
          pointerEvents: 'auto',
          cursor: frozenTooltipData ? 'default' : 'pointer',
          left: frozenTooltipData && currentData.coordinate ? `${currentData.coordinate.x + 20}px` : 'auto',
          top: frozenTooltipData && currentData.coordinate ? `${Math.max(20, currentData.coordinate.y - 100)}px` : 'auto'
        }}
        onClick={(e) => {
          e.stopPropagation();
          if (!frozenTooltipData && active && payload && coordinate) {
            setFrozenTooltipData({ payload, label, coordinate });
          }
        }}
      >
        {/* Close button for frozen tooltips */}
        {frozenTooltipData && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              setFrozenTooltipData(null);
            }}
            style={{
              position: 'absolute',
              top: '6px',
              right: '6px',
              background: '#ef4444',
              color: 'white',
              border: 'none',
              borderRadius: '50%',
              width: '20px',
              height: '20px',
              fontSize: '14px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: 'bold'
            }}
          >
            ×
          </button>
        )}

        <p style={{
          margin: '0 0 10px 0',
          fontWeight: 'bold',
          fontSize: '14px',
          borderBottom: '1px solid #e5e7eb',
          paddingBottom: '6px'
        }}>
          {formattedDate}
          {!frozenTooltipData && (
            <span style={{ fontSize: '10px', color: '#6b7280', marginLeft: '8px' }}>
              (Click to freeze)
            </span>
          )}
        </p>

        <div style={{ marginBottom: '10px' }}>
          {currentData.payload.map((entry: any, index: number) => {
            let displayName = entry.name;
            let displayValue = entry.value;

            // Fix naming for specific metrics
            if (entry.dataKey === 'normalized_divergence') {
              displayName = 'Normalized Divergence';
            } else if (entry.dataKey === 'acute_chronic_ratio') {
              displayName = 'External ACWR (mile equiv)';
            } else if (entry.dataKey === 'trimp_acute_chronic_ratio') {
              displayName = 'Internal ACWR';
            } else if (entry.dataKey === 'total_load_miles') {
              displayName = 'Total Load (mile equiv)';
            } else if (entry.dataKey === 'elevation_load_miles') {
              displayName = 'Elevation Load (mile equiv)';
            } else if (entry.dataKey === 'seven_day_avg_load') {
              displayName = '7-Day Avg (mile equiv)';
            } else if (entry.dataKey === 'seven_day_avg_trimp') {
              displayName = '7-Day Avg TRIMP';
            }

            return (
              <div key={`item-${index}`} style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '3px'
              }}>
                <span style={{
                  color: entry.color,
                  fontWeight: '500',
                  marginRight: '8px',
                  fontSize: '11px'
                }}>
                  {displayName}:
                </span>
                <span style={{ fontWeight: 'bold', fontSize: '12px' }}>
                  {displayValue === null || displayValue === undefined
                    ? 'N/A'
                    : typeof displayValue === 'number'
                    ? displayValue.toFixed(displayName.includes('ACWR') || displayName.includes('Divergence') ? 3 : 1)
                    : displayValue
                  }
                </span>
              </div>
            );
          })}
        </div>

        {/* Enhanced Strava Link */}
        {activityId && activityId !== 0 && (
          <div style={{
            borderTop: '1px solid #e5e7eb',
            paddingTop: '8px',
            textAlign: 'center'
          }}>
            <a
              href={`https://www.strava.com/activities/${activityId}`}
              target="_blank"
              rel="noopener noreferrer"
              onClick={(e) => e.stopPropagation()}
              style={{
                display: 'inline-block',
                padding: '8px 16px',
                backgroundColor: '#fc4c02',
                color: 'white',
                textDecoration: 'none',
                borderRadius: '6px',
                fontSize: '12px',
                fontWeight: 'bold',
                transition: 'all 0.2s',
                border: '2px solid #fc4c02'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = '#e73c00';
                e.currentTarget.style.borderColor = '#e73c00';
                e.currentTarget.style.transform = 'scale(1.05)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = '#fc4c02';
                e.currentTarget.style.borderColor = '#fc4c02';
                e.currentTarget.style.transform = 'scale(1)';
              }}
            >
              🔗 View on Strava
            </a>
          </div>
        )}
      </div>
    );
  };

  // Calculate normalized divergence
  const calculateNormalizedDivergence = (externalAcwr: number, internalAcwr: number) => {
    if (externalAcwr === null || internalAcwr === null) return null;
    if (externalAcwr === 0 && internalAcwr === 0) return 0;

    const avgAcwr = (externalAcwr + internalAcwr) / 2;
    if (avgAcwr === 0) return 0;

    return parseFloat(((externalAcwr - internalAcwr) / avgAcwr).toFixed(3));
  };

  // FIXED: Dynamic domain calculation for normalized divergence with inverted axis
  const getDivergenceDomain = (data: ProcessedDataRow[]) => {
    const divergenceValues = data
      .map(d => d.normalized_divergence)
      .filter(val => val !== null && val !== undefined && !isNaN(val as number)) as number[];

    if (divergenceValues.length === 0) {
      return [0.3, -0.3]; // Inverted: positive at top, negative at bottom
    }

    const minVal = Math.min(...divergenceValues);
    const maxVal = Math.max(...divergenceValues);

    // Add 20% padding and ensure minimum range
    const padding = Math.max(0.05, (maxVal - minVal) * 0.2);
    const domainTop = Math.max(0.3, maxVal + padding);    // Most positive (top)
    const domainBottom = Math.min(-0.3, minVal - padding); // Most negative (bottom)

    return [domainTop, domainBottom]; // Inverted order for chart
  };

  // Filter data based on date range
  const filteredData = () => {
    if (data.length === 0) return [];

    const days = parseInt(dateRange, 10);
    const allDates = data.map(item => item.date).sort();
    const maxDate = allDates[allDates.length - 1];

    const maxDateObj = new Date(`${maxDate}T12:00:00Z`);
    const cutoffDateObj = new Date(maxDateObj);
    cutoffDateObj.setDate(cutoffDateObj.getDate() - days + 1);

    const cutoffDate = cutoffDateObj.toISOString().split('T')[0];

    return data.filter(item => {
      return item.date >= cutoffDate && item.date <= maxDate;
    });
  };

  // Function to fetch LLM recommendations from recommendations_component.ts
  const fetchRecommendations = async () => {
    console.log("fetchRecommendations called");
    try {
      setIsLoadingRecommendation(true);
      console.log("Fetching recommendations from /api/llm-recommendations");
      const response = await fetch('/api/llm-recommendations');
      console.log("Response status:", response.status);

      if (!response.ok) {
        console.error(`API response not OK: ${response.status}`);
        throw new Error(`API responded with status ${response.status}`);
      }

      const result = await response.json();
      console.log("Recommendation API result:", result);

      if (result.recommendation) {
        console.log("Setting recommendation state with:", result.recommendation);
        setRecommendation(result.recommendation);
      } else {
        console.log("No recommendation in result:", result);
        setRecommendation(null); // Explicitly set to null if no recommendation
      }
    } catch (e) {
      console.error("Failed to fetch recommendations:", e);
      setError("Failed to load AI recommendations."); // Set error in main dashboard error state
      setRecommendation(null);
    } finally {
      setIsLoadingRecommendation(false);
    }
  };

  // Function to generate new LLM recommendations from recommendations_component.ts
  const generateNewRecommendation = async () => {
      try {
        setIsLoadingRecommendation(true);

        // Step 1: Generate new recommendation
        const response = await fetch('/api/llm-recommendations/generate', {
          method: 'POST'
        });

        if (!response.ok) {
          throw new Error(`Generation failed: ${response.status}`);
        }

        const result = await response.json();
        console.log("Generated successfully:", result);

        // Step 2: Fetch the latest recommendation (same as page refresh)
        await fetchRecommendations(); // This ensures consistent data format

      } catch (e) {
        console.error("Failed to generate recommendation:", e);
        setError("Failed to generate new AI recommendations.");
      } finally {
        setIsLoadingRecommendation(false);
      }
    };

  // Main data loading effect (using your working API endpoints)
  useEffect(() => {
      const loadData = async () => {
        try {
          setIsLoading(true);
          setError(null);

          console.log("Fetching data from Strava API...");
          const response = await fetch(`/api/training-data?t=${new Date().getTime()}&include_sport_breakdown=true`);

          if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`API responded with status ${response.status}: ${errorText}`);
          }

          const result = await response.json();

          if (!result.data || !Array.isArray(result.data) || result.data.length === 0) {
            throw new Error("No data returned from API");
          }

          console.log(`Successfully received ${result.data.length} records from Strava`);
          
          // Store dashboard configuration if available
          if (result.dashboard_config) {
            console.log('Dashboard using custom configuration:', result.dashboard_config);
          } else {
            console.log('Dashboard using default configuration');
          }

          // Process data with proper date handling
          const processedData = result.data.map((row: TrainingDataRow) => {
            const dateObj = new Date(`${row.date}T12:00:00Z`);

            let normalizedDivergence = row.normalized_divergence;
            if (normalizedDivergence === undefined) {
              normalizedDivergence = calculateNormalizedDivergence(
                row.acute_chronic_ratio,
                row.trimp_acute_chronic_ratio
              );
            }

            return {
              ...row,
              dateObj,
              normalized_divergence: normalizedDivergence
            };
          });

          processedData.sort((a, b) => a.date.localeCompare(b.date));
          setData(processedData);

          if (result.has_cycling_data !== undefined) {
            setHasCyclingData(result.has_cycling_data);
          }
          if (result.sport_summary) {
            setSportSummary(result.sport_summary);
          }

          // Get stats from the API
          try {
            const statsResponse = await fetch(`/api/stats?t=${new Date().getTime()}`);

            if (statsResponse.ok) {
              const statsData = await statsResponse.json();

              setMetrics({
                externalAcwr: statsData.latestMetrics.externalAcwr || 0,
                internalAcwr: statsData.latestMetrics.internalAcwr || 0,
                sevenDayAvgLoad: statsData.latestMetrics.sevenDayAvgLoad || 0,
                sevenDayAvgTrimp: statsData.latestMetrics.sevenDayAvgTrimp || 0,
                daysSinceRest: statsData.daysSinceRest || 0,
                normalizedDivergence: processedData.length > 0 ?
                  processedData[processedData.length - 1].normalized_divergence as number : 0,
                dashboardConfig: result.dashboard_config || undefined
              });
            }
          } catch (statsError) {
            console.warn("Failed to fetch stats, using data from main endpoint");
          }

        } catch (error) {
          console.error("Error loading data:", error);
          setError(`Failed to load data: ${error instanceof Error ? error.message : String(error)}`);
        } finally {
          setIsLoading(false);
          setRenderKey(prevKey => prevKey + 1);
        }
      };

      loadData();
      fetchRecommendations(); // Fetch recommendations on initial load
    }, []);

  // FIXED: Click outside handler for frozen tooltips
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (frozenTooltipData) {
        const target = event.target as Element;
        // Don't close if clicking on the tooltip itself
        if (!target.closest('[style*="position: fixed"]')) {
          setFrozenTooltipData(null);
        }
      }
    };

    if (frozenTooltipData) {
      document.addEventListener('click', handleClickOutside);
      return () => document.removeEventListener('click', handleClickOutside);
    }
  }, [frozenTooltipData]);

  // Handle date range change
  useEffect(() => {
    setRenderKey(prevKey => prevKey + 1);
  }, [dateRange]);

  // Loading state
  if (isLoading) {
    return (
      <div className={styles.loading}>
        <h1 className={styles.title}>Loading dashboard...</h1>
        <p>Fetching training data from Strava...</p>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className={styles.error}>
        <h1 className={styles.errorTitle}>Error Loading Dashboard</h1>
        <p className={styles.errorMessage}>{error}</p>
        <button
          onClick={() => window.location.reload()}
          className={styles.retryButton}
        >
          Retry
        </button>
      </div>
    );
  }

  // Prepare data for charts
  const filtered = filteredData();

  // No data state
  if (filtered.length === 0) {
    return (
      <div className={styles.noData}>
        <h1 className={styles.title}>No Data Available</h1>
        <p>No training data found for the selected time period.</p>
        <button
          onClick={() => setDateRange('90')}
          className={styles.retryButton}
        >
          View Last 90 Days
        </button>
      </div>
    );
  }

  // Main dashboard render
  return (
    <div className={styles.container}>
      {/* COMPACT DASHBOARD BANNER */}
      <CompactDashboardBanner
        onSyncComplete={handleSyncComplete}
        metrics={metrics}
      />

      {/* Chart Time Period Control */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '0.25rem',
          padding: '0.25rem',
          backgroundColor: 'white',
          borderRadius: '0.5rem',
          boxShadow: '0 1px 2px rgba(0, 0, 0, 0.05)'
        }}>
          <h2 style={{ margin: 0, fontSize: '1.1rem', fontWeight: '600', color: '#374151' }}>
            Training Charts
          </h2>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0rem' }}>
            <label style={{ fontSize: '0.875rem', fontWeight: '500', color: '#374151' }}>
              Time Period:
            </label>
            <select
              value={dateRange}
              onChange={(e) => setDateRange(e.target.value)}
              style={{
                padding: '0.375rem',
                borderRadius: '0.375rem',
                border: '1px solid #d1d5db',
                backgroundColor: 'white',
                fontSize: '0.875rem',
                color: '#374151',
                cursor: 'pointer'
              }}
            >
              <option value="7">7 Days</option>
              <option value="14">14 Days</option>
              <option value="30">30 Days</option>
              <option value="60">60 Days</option>
              <option value="90">90 Days</option>
            </select>
          </div>
        </div>

      {/* Sport Filter Controls - only show if cycling data exists */}
      {hasCyclingData && (
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '0.25rem',
          padding: '0.5rem',
          backgroundColor: 'white',
          borderRadius: '0.5rem',
          boxShadow: '0 1px 2px rgba(0, 0, 0, 0.05)'
        }}>
          <span style={{ fontWeight: '500', color: '#374151' }}>Show Sports:</span>
          <div style={{ display: 'flex', gap: '1rem' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={selectedSports.includes('running')}
                onChange={() => setSelectedSports(prev =>
                  prev.includes('running') ? prev.filter(s => s !== 'running') : [...prev, 'running']
                )}
              />
              <span style={{ color: '#2ecc71' }}>Running</span>
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={selectedSports.includes('cycling')}
                onChange={() => setSelectedSports(prev =>
                  prev.includes('cycling') ? prev.filter(s => s !== 'cycling') : [...prev, 'cycling']
                )}
              />
              <span style={{ color: '#3498db' }}>Cycling</span>
            </label>
          </div>
        </div>
      )}

      {/* Overtraining Risk Over Time Chart */}
      <div className={styles.chartContainer}>
        <h2 className={styles.chartTitle}>Overtraining Risk</h2>
        <div className={styles.chartWrapper} style={{ width: chartDimensions.width, height: chartDimensions.height }}>
          <ResponsiveContainer width="100%" height="100%" key={`overtraining-risk-${renderKey}`}>
            <ComposedChart
              data={filtered}
              margin={{ top: 5, right: 50, left: 20, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="date"
                interval={chartDimensions.majorTickInterval}
                tickFormatter={formatXAxis}
                padding={{ left: 10, right: 10 }}
              />
              <YAxis
                domain={[0, 2.5]}
                label={{
                  value: 'ACWR',
                  angle: -90,
                  position: 'insideLeft',
                  style: { textAnchor: 'middle', fontSize: '12px', fontWeight: '500' }
                }}
                tickFormatter={(value) => value.toFixed(1)}
                width={60}
              />
              <YAxis
                yAxisId="divergence"
                orientation="right"
                domain={[-0.5, 0.2]}
                reversed={true}
                label={{
                  value: 'Normalized Divergence',
                  angle: 90,
                  position: 'insideRight',
                  style: { textAnchor: 'middle', fontSize: '12px', fontWeight: '500' }
                }}
                tickFormatter={(value) => value.toFixed(2)}
                width={60}
              />
              <Tooltip
                content={<CustomTooltip />}
                cursor={{ strokeDasharray: '3 3' }}
                wrapperStyle={{ pointerEvents: 'auto' }}
              />
              <Legend />

              {/* Risk zones with improved color contrast */}
              {/* Low Risk: < 0.8 */}
              <ReferenceArea
                y1={0}
                y2={0.8}
                fill="rgba(40, 167, 69, 0.15)"
                stroke="rgba(40, 167, 69, 0.3)"
                strokeWidth={1}
                label={{ value: "Low Risk", position: "insideTopLeft", fontSize: 10, fill: "green" }}
              />
              
              {/* Balanced: 0.8-1.3 */}
              <ReferenceArea
                y1={0.8}
                y2={1.3}
                fill="rgba(255, 193, 7, 0.2)"
                stroke="rgba(255, 193, 7, 0.3)"
                strokeWidth={1}
                label={{ value: "Balanced", position: "insideTopLeft", fontSize: 10, fill: "#b8860b" }}
              />
              
              {/* Moderate Risk: 1.3-1.5 */}
              <ReferenceArea
                y1={1.3}
                y2={1.5}
                fill="rgba(255, 87, 34, 0.25)"
                stroke="rgba(255, 87, 34, 0.3)"
                strokeWidth={1}
                label={{ value: "Moderate Risk", position: "insideTopLeft", fontSize: 10, fill: "#ff5722" }}
              />
              
              {/* High Risk: >1.5 */}
              <ReferenceArea
                y1={1.5}
                y2={2.5}
                fill="rgba(199, 21, 133, 0.25)"
                stroke="rgba(199, 21, 133, 0.3)"
                strokeWidth={1}
                label={{ value: "High Risk", position: "insideTopLeft", fontSize: 10, fill: "#c71585" }}
              />

              {/* Internal Load (TRIMP) Line */}
              <Line
                type="monotone"
                dataKey="trimp_acute_chronic_ratio"
                name="Internal Load (TRIMP)"
                stroke="#007bff"
                strokeWidth={defaultTheme.lineStyles.regular.strokeWidth}
                dot={(props) => {
                  if (!props || !props.cx || !props.cy || !props.payload) return null;
                  const { cx, cy, payload } = props;
                  if (payload.activity_id === 0) return null;
                  if (payload.trimp_acute_chronic_ratio === null || payload.trimp_acute_chronic_ratio === undefined) return null;
                  return <circle cx={cx} cy={cy} r={3} fill="#007bff" />;
                }}
                activeDot={{ r: 5 }}
                connectNulls={false}
                isAnimationActive={false}
              />

              {/* External Work Line */}
              <Line
                type="monotone"
                dataKey="acute_chronic_ratio"
                name="External Work"
                stroke="#28a745"
                strokeWidth={defaultTheme.lineStyles.regular.strokeWidth}
                dot={(props) => {
                  if (!props || !props.cx || !props.cy || !props.payload) return null;
                  const { cx, cy, payload } = props;
                  if (payload.activity_id === 0) return null;
                  if (payload.acute_chronic_ratio === null || payload.acute_chronic_ratio === undefined) return null;
                  return <circle cx={cx} cy={cy} r={3} fill="#28a745" />;
                }}
                activeDot={{ r: 5 }}
                connectNulls={false}
                isAnimationActive={false}
              />

              {/* Normalized Divergence Line */}
              <Line
                yAxisId="divergence"
                type="monotone"
                dataKey="normalized_divergence"
                name="Normalized Divergence"
                stroke="#dc3545"
                strokeWidth={defaultTheme.lineStyles.regular.strokeWidth}
                strokeDasharray="5 5"
                dot={(props) => {
                  if (!props || !props.cx || !props.cy || !props.payload) return null;
                  const { cx, cy, payload } = props;
                  if (payload.activity_id === 0) return null;
                  if (payload.normalized_divergence === null || payload.normalized_divergence === undefined) return null;
                  return <circle cx={cx} cy={cy} r={2} fill="#dc3545" />;
                }}
                activeDot={{ r: 4 }}
                connectNulls={false}
                isAnimationActive={false}
              />

              {/* Zero reference line for divergence */}
              <ReferenceLine yAxisId="divergence" y={0} stroke="#666" strokeWidth={1} strokeDasharray="3 3" />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
        <p className={styles.chartNote}>
          Negative divergence indicates internal stress (TRIMP) is higher than external load, suggesting potential overtraining.
          <br/><strong>ACWR Calculation:</strong> {metrics.dashboardConfig ? 
            `Acute (7-day average) ÷ Chronic (${metrics.dashboardConfig.chronic_period_days}-day exponential decay, rate: ${metrics.dashboardConfig.decay_rate})` :
            'Acute (7-day average) ÷ Chronic (28-day simple average). No exponential decay weighting applied.'
          }
        </p>
      </div>

      {/* FIXED: Internal Load Chart with proper 7-day average display */}
      <div className={styles.chartContainer}>
        <h2 className={styles.chartTitle}>Internal Load Trend</h2>
        <div className={styles.chartWrapper} style={{ width: chartDimensions.width, height: chartDimensions.height }}>
          <ResponsiveContainer width="100%" height="100%" key={`internal-load-${renderKey}`}>
            <ComposedChart
              data={filtered}
              margin={{ top: 5, right: 40, left: 20, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="date"
                interval={chartDimensions.majorTickInterval}
                tickFormatter={formatXAxis}
                padding={{ left: 10, right: 10 }}
              />
              <YAxis
                label={{ value: 'TRIMP', angle: -90, position: 'insideLeft' }}
              />
              <Tooltip
                content={<CustomTooltip />}
                cursor={{ strokeDasharray: '3 3' }}
                wrapperStyle={{ pointerEvents: 'auto' }}
              />
              <Legend />

              {/* Daily TRIMP - Bars */}
              <Bar
                dataKey="trimp"
                name="Daily TRIMP"
                fill={colors.trimp}
                barSize={chartDimensions.barSize}
                opacity={0.8}
                isAnimationActive={false}
              />

              {/* FIXED: 7-Day Average TRIMP - Line with proper data handling */}
              <Line
                type="monotone"
                dataKey="seven_day_avg_trimp"
                stroke={colors.warning}
                strokeWidth={4}
                dot={false}
                name="7-Day Avg TRIMP"
                strokeDasharray="8 4"
                isAnimationActive={false}
                connectNulls={false}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
        <p className={styles.chartNote}>
          Internal training stress (TRIMP) with 7-day moving average trend line.
        </p>
      </div>

      {/* FIXED: External Load Chart with proper 7-day average display */}
      <div className={styles.chartContainer}>
        <h2 className={styles.chartTitle}>External Work Trend</h2>
        <div className={styles.chartWrapper} style={{ width: chartDimensions.width, height: chartDimensions.height }}>
          <ResponsiveContainer width="100%" height="100%" key={`external-load-${renderKey}`}>
            <ComposedChart
              data={filtered}
              margin={{ top: 5, right: 40, left: 20, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="date"
                interval={chartDimensions.majorTickInterval}
                tickFormatter={formatXAxis}
                padding={{ left: 10, right: 10 }}
              />
              <YAxis
                yAxisId="miles"
                label={{ value: 'Mile Equivalent', angle: -90, position: 'insideLeft' }}
              />
              <YAxis
                yAxisId="elevation"
                orientation="right"
                label={{ value: 'Elevation (ft)', angle: 90, position: 'insideRight' }}
              />
              <Tooltip
                content={<CustomTooltip />}
                cursor={{ strokeDasharray: '3 3' }}
                wrapperStyle={{ pointerEvents: 'auto' }}
              />
              <Legend />

              {/* Distance component - existing logic preserved */}
              <Bar
                yAxisId="miles"
                dataKey="distance_miles"
                name="Distance (miles)"
                fill={colors.primary}
                barSize={chartDimensions.barSize}
                opacity={selectedSports.includes('running') ? 0.7 : 0.3}
                stackId="external"
                isAnimationActive={false}
              />

              {/* Elevation Load component - existing logic preserved */}
              <Bar
                yAxisId="miles"
                dataKey="elevation_load_miles"
                name="Elevation Load (mile equiv)"
                fill={colors.secondary}
                barSize={chartDimensions.barSize}
                opacity={selectedSports.includes('running') ? 0.7 : 0.3}
                stackId="external"
                isAnimationActive={false}
              />

              {/* NEW: Cycling load bars - separate from running stack */}
              {hasCyclingData && (
                <Bar
                  yAxisId="miles"
                  dataKey="cycling_load"
                  name="Cycling Load (running equiv)"
                  fill="#3498db"
                  barSize={chartDimensions.barSize}
                  opacity={selectedSports.includes('cycling') ? 0.7 : 0.3}
                  isAnimationActive={false}
                />
              )}

              {/* 7-Day Average Total Load - existing logic preserved */}
              <Line
                yAxisId="miles"
                type="monotone"
                dataKey="seven_day_avg_load"
                stroke={colors.dark}
                strokeWidth={4}
                dot={false}
                name="7-Day Avg (mile equiv)"
                strokeDasharray="8 4"
                isAnimationActive={false}
                connectNulls={false}
              />

              {/* Elevation gain - existing logic preserved */}
              <Line
                yAxisId="elevation"
                type="monotone"
                dataKey="elevation_gain_feet"
                stroke={colors.warning}
                strokeWidth={2}
                dot={{ fill: colors.warning, strokeWidth: 1, r: 3 }}
                name="Elevation Gain (ft)"
                isAnimationActive={false}
                connectNulls={false}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
        <p className={styles.chartNote}>
          External training load: distance + elevation converted to mile equivalent, with 7-day moving average.
        </p>
      </div>

      {/* Enhanced Training Recommendations Section */}
      <div className={styles.chartContainer}>
        <h2 className={styles.chartTitle}>Training Recommendations & Analysis</h2>

        {/* Status Banner */}
        <div style={{
          backgroundColor:
            metrics.normalizedDivergence < -0.15 ? '#fee2e2' : // red-100
            metrics.normalizedDivergence < -0.05 ? '#fef3c7' : // yellow-100
            metrics.externalAcwr > 1.3 || metrics.internalAcwr > 1.3 ? '#fed7aa' : // orange-100
            '#d1fae5', // green-100
          color:
            metrics.normalizedDivergence < -0.15 ? '#991b1b' : // red-800
            metrics.normalizedDivergence < -0.05 ? '#92400e' : // yellow-800
            metrics.externalAcwr > 1.3 || metrics.internalAcwr > 1.3 ? '#9a3412' : // orange-800
            '#065f46', // green-800
          padding: '0.75rem',
          borderRadius: '0.5rem',
          marginBottom: '1rem',
          fontWeight: '600',
          textAlign: 'center' as const
        }}>
          Assessment Status: {
            metrics.normalizedDivergence < -0.15 ? 'HIGH OVERTRAINING RISK' :
            metrics.normalizedDivergence < -0.05 ? 'MODERATE FATIGUE' :
            metrics.externalAcwr > 1.3 || metrics.internalAcwr > 1.3 ? 'ELEVATED ACWR' :
            metrics.daysSinceRest > 7 ? 'EXTENDED TRAINING BLOCK' :
            'BALANCED TRAINING'
          }
        </div>

        <div className={styles.recommendationsGrid}>
          {/* Today's Training Decision */}
          <div>
              {(() => {
                const dateContext = getRecommendationDateContext(recommendation);

                return (
                  <>
                    <h3 className={styles.recommendationHeading}>
                      🎯 {dateContext.displayTitle}
                      {dateContext.isForTomorrow && (
                        <span style={{
                          fontSize: '0.75rem',
                          backgroundColor: '#dbeafe',
                          color: '#1e40af',
                          padding: '0.25rem 0.5rem',
                          borderRadius: '0.25rem',
                          marginLeft: '0.5rem'
                        }}>
                          Plan Ahead
                        </span>
                      )}
                      {dateContext.isForToday && (
                        <span style={{
                          fontSize: '0.75rem',
                          backgroundColor: '#fef3c7',
                          color: '#92400e',
                          padding: '0.25rem 0.5rem',
                          borderRadius: '0.25rem',
                          marginLeft: '0.5rem'
                        }}>
                          Today
                        </span>
                      )}
                    </h3>

                    <div className={styles.recommendationTabs}>
                      <div className={styles.recommendationTab} style={{borderLeft: '3px solid #3b82f6'}}>
                        <h4 className={styles.tabHeading}>
                          🤖 AI Analysis
                          {recommendation && (
                            <span style={{
                              fontSize: '0.7rem',
                              color: '#6b7280',
                              fontWeight: 'normal',
                              marginLeft: '0.5rem'
                            }}>
                              • For {new Date((recommendation.target_date || recommendation.generation_date).split('T')[0] + 'T12:00:00').toLocaleDateString()}
                            </span>
                          )}
                        </h4>
                        <div style={{padding: '0.5rem 0'}}>
                          {recommendation ? (
                            <>
                              <p className={styles.recommendationText}>
                                {recommendation.daily_recommendation}
                              </p>
                              <div style={{marginTop: '0.5rem'}}>
                                <small style={{color: '#6b7280', fontSize: '0.75rem'}}>
                                  Based on: Ext ACWR {metrics.externalAcwr?.toFixed(2)},
                                  Int ACWR {metrics.internalAcwr?.toFixed(2)},
                                  Divergence {metrics.normalizedDivergence?.toFixed(2)}
                                  {dateContext.isForTomorrow && " • Plan your workout accordingly"}
                                  {dateContext.isForToday && " • Review before today's session"}
                                </small>
                              </div>
                            </>
                          ) : (
                            <div>
                              {isLoadingRecommendation ? (
                                <p>Generating AI analysis...</p>
                              ) : (
                                <p className={styles.recommendationText}>
                                  No AI recommendation available. Click "Generate AI Analysis" below.
                                </p>
                              )}
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Rules-Based section remains the same */}
                      <div className={styles.recommendationTab} style={{borderLeft: '3px solid #10b981'}}>
                        <h4 className={styles.tabHeading}>
                          📋 Rules-Based Quick Check
                        </h4>
                        <div style={{padding: '0.5rem 0'}}>
                          <p className={styles.recommendationText}>
                            {metrics.daysSinceRest > 7 ? (
                              <span style={{ color: colors.danger }}>
                                <strong>🛑 MANDATORY REST:</strong> {metrics.daysSinceRest} days without rest exceeds safe limits.
                                Complete rest day required.
                              </span>
                            ) : metrics.normalizedDivergence < -0.15 ? (
                              <span style={{ color: colors.danger }}>
                                <strong>⚠️ OVERTRAINING RISK:</strong> Normalized divergence ({metrics.normalizedDivergence?.toFixed(3)})
                                indicates high stress. Rest or very light recovery only.
                              </span>
                            ) : (metrics.externalAcwr > 1.3 && metrics.internalAcwr > 1.3) ? (
                              <span style={{ color: colors.warning }}>
                                <strong>📈 HIGH ACWR:</strong> Both ratios exceed 1.3. Reduce volume and intensity.
                              </span>
                            ) : metrics.normalizedDivergence < -0.05 && metrics.daysSinceRest > 5 ? (
                              <span style={{ color: colors.warning }}>
                                <strong>🔄 RECOVERY NEEDED:</strong> Active recovery recommended.
                              </span>
                            ) : (metrics.externalAcwr < 0.8 && metrics.internalAcwr < 0.8) ? (
                              <span style={{ color: colors.success }}>
                                <strong>📊 PROGRESSION OPPORTUNITY:</strong> Both ACWR values below 0.8 - gradual load increase possible.
                              </span>
                            ) : (
                              <span style={{ color: colors.success }}>
                                <strong>✅ BALANCED TRAINING:</strong> Metrics within optimal ranges. Continue current approach.
                              </span>
                            )}
                          </p>
                        </div>
                      </div>
                    </div>
                  </>
                );
              })()}
            </div>

          {/* Weekly Strategy */}
          <div>
            <h3 className={styles.recommendationHeading}>
              📅 Weekly Strategy
            </h3>

            <div className={styles.recommendationTabs}>
              <div className={styles.recommendationTab} style={{borderLeft: '3px solid #3b82f6'}}>
                <h4 className={styles.tabHeading}>
                  🤖 Strategic Planning
                </h4>
                <div style={{padding: '0.5rem 0'}}>
                  <p className={styles.recommendationText}>
                    {recommendation ? recommendation.weekly_recommendation : "Generate AI analysis for weekly planning insights"}
                  </p>
                </div>
              </div>

              <div className={styles.recommendationTab} style={{borderLeft: '3px solid #10b981'}}>
                <h4 className={styles.tabHeading}>
                  📋 ACWR Management
                </h4>
                <div style={{padding: '0.5rem 0'}}>
                  <p className={styles.recommendationText}>
                    {metrics.externalAcwr > 1.3 || metrics.internalAcwr > 1.3 ? (
                      <>
                        <strong>Step-back week needed:</strong> Current 7-day average ({metrics.sevenDayAvgLoad?.toFixed(1)} mi/day)
                        is too high. Target reducing to {(metrics.sevenDayAvgLoad * 0.75)?.toFixed(1)} mi/day over next 5-7 days.
                      </>
                    ) : metrics.externalAcwr < 0.8 && metrics.internalAcwr < 0.8 ? (
                      <>
                        <strong>Progressive build opportunity:</strong> Gradually increase 7-day average from {metrics.sevenDayAvgLoad?.toFixed(1)}
                        to {(metrics.sevenDayAvgLoad * 1.15)?.toFixed(1)} mi/day over next 2 weeks.
                      </>
                    ) : (
                      <>
                        <strong>Maintenance phase:</strong> Current 7-day average ({metrics.sevenDayAvgLoad?.toFixed(1)} mi/day)
                        is in optimal range. Continue with similar daily volumes.
                      </>
                    )}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Pattern Analysis */}
          <div>
            <h3 className={styles.recommendationHeading}>
              🔍 Pattern Analysis
            </h3>

            <div className={styles.recommendationTabs}>
              <div className={styles.recommendationTab} style={{borderLeft: '3px solid #3b82f6'}}>
                <h4 className={styles.tabHeading}>
                  🤖 Advanced Insights
                </h4>
                <div style={{padding: '0.5rem 0'}}>
                  <p className={styles.recommendationText}>
                    {recommendation ? recommendation.pattern_insights : "Generate AI analysis for detailed pattern recognition"}
                  </p>
                </div>
              </div>

              <div className={styles.recommendationTab} style={{borderLeft: '3px solid #10b981'}}>
                <h4 className={styles.tabHeading}>
                  📋 Key Observations
                </h4>
                <div style={{padding: '0.5rem 0'}}>
                  <div style={{display: 'flex', flexDirection: 'column' as const, gap: '0.75rem'}}>
                    <div>
                      <strong>Load Balance:</strong>
                      <span style={{marginLeft: '0.5rem', color: '#4b5563'}}>
                        {Math.abs(metrics.normalizedDivergence) < 0.05 ?
                          "External and internal loads are well-balanced, indicating good adaptation." :
                          metrics.normalizedDivergence < -0.05 ?
                          "Internal stress is elevated relative to external work - focus on recovery." :
                          "External work capacity exceeds internal stress - opportunity for intensity increases."
                        }
                      </span>
                    </div>

                    <div>
                      <strong>Recovery Pattern:</strong>
                      <span style={{marginLeft: '0.5rem', color: '#4b5563'}}>
                        {metrics.daysSinceRest <= 2 ? "Recent rest day supporting good recovery cycle." :
                         metrics.daysSinceRest <= 5 ? `${metrics.daysSinceRest} days since rest - within normal range.` :
                         `${metrics.daysSinceRest} days without rest - consider scheduling recovery soon.`}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Action Center */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginTop: '1.5rem',
          padding: '1rem',
          backgroundColor: '#f8f9fa',
          borderRadius: '0.5rem'
        }}>
          <div>
            {recommendation ? (
              <div>
                <span style={{fontWeight: '500', color: '#374151'}}>AI Analysis:</span>
                <span style={{marginLeft: '0.5rem', color: '#6b7280'}}>
                  {new Date(recommendation.generation_date).toLocaleDateString()}
                </span>
              </div>
            ) : (
              <div>
                <span style={{color: '#6b7280', fontSize: '0.875rem'}}>
                  AI analysis provides personalized insights based on your training patterns.
                </span>
              </div>
            )}
          </div>

          <div style={{display: 'flex', alignItems: 'center', gap: '1rem'}}>
            {recommendation ? (
              <button
                onClick={generateNewRecommendation}
                className={styles.refreshButton}
                disabled={isLoadingRecommendation}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem'
                }}
              >
                {isLoadingRecommendation ? (
                  <>
                    <span style={{
                      display: 'inline-block',
                      width: '1rem',
                      height: '1rem',
                      border: '2px solid #f3f4f6',
                      borderTop: '2px solid #3b82f6',
                      borderRadius: '50%',
                      animation: 'spin 1s linear infinite'
                    }}></span>
                    Updating...
                  </>
                ) : (
                  <>
                    <span>🔄</span>
                    Refresh Analysis
                  </>
                )}
              </button>
            ) : (
              <button
                onClick={generateNewRecommendation}
                className={styles.generateButton}
                disabled={isLoadingRecommendation}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem'
                }}
              >
                {isLoadingRecommendation ? (
                  <>
                    <span style={{
                      display: 'inline-block',
                      width: '1rem',
                      height: '1rem',
                      border: '2px solid #f3f4f6',
                      borderTop: '2px solid #3b82f6',
                      borderRadius: '50%',
                      animation: 'spin 1s linear infinite'
                    }}></span>
                    Generating...
                  </>
                ) : (
                  <>
                    <span>🤖</span>
                    Generate AI Analysis
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default TrainingLoadDashboard;