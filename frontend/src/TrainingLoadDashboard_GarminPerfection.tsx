// TrainingLoadDashboard.tsx - FIXED VERSION
import React, { useState, useEffect } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, ReferenceArea, ComposedChart, ReferenceLine, Bar
} from 'recharts';
import styles from './TrainingLoadDashboard.module.css';
import defaultTheme from './chartTheme';
import { useChartDimensions } from './useChartDimensions';

// Define interfaces for your data
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
  "7day_avg_load": number;
  "28day_avg_load": number;
  "7day_avg_trimp": number;
  "28day_avg_trimp": number;
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
}

// New interfaces for LLM recommendations and wellness metrics
interface LLMRecommendation {
  id: number;
  generation_date: string;
  valid_until: string;
  daily_recommendation: string;
  weekly_recommendation: string;
  pattern_insights: string;
}

interface WellnessMetric {
  date: string;
  weight_lbs: number | null;
  perceived_effort: number | null;
  feeling_score: number | null;
  notes: string | null;
}

const TrainingLoadDashboard: React.FC = () => {
  console.log("TrainingLoadDashboard component initialized");
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
  const [latestActivityId, setLatestActivityId] = useState<number>(0);

  // New state for LLM recommendations and wellness metrics
  const [recommendation, setRecommendation] = useState<LLMRecommendation | null>(null);
  const [isLoadingRecommendation, setIsLoadingRecommendation] = useState<boolean>(false);
  const [wellnessMetrics, setWellnessMetrics] = useState<WellnessMetric[]>([]);
  const [isUpdatingWellness, setIsUpdatingWellness] = useState<boolean>(false);
  const [syncStatus, setSyncStatus] = useState<any>(null);
  const [isTestingConnection, setIsTestingConnection] = useState(false);
  const [connectionTestResult, setConnectionTestResult] = useState<any>(null);
  // Get chart dimensions from custom hook
  const chartDimensions = useChartDimensions(dateRange);

  // Use the theme colors
  const colors = defaultTheme.colors;

  // Format X-axis labels
  const formatXAxis = (dateStr: string) => {
    if (!dateStr) return '';
    const [year, month, day] = dateStr.split('-').map(Number);
    return `${month}/${day}`;
  };

  // Format date for tooltip display - FIXED date handling
  const formatTooltipDate = (dateStr: string) => {
    if (!dateStr) return '';
    // For tooltip display, show a more readable format
    try {
      // Split the date string to get components without timezone conversion
      const [year, month, day] = dateStr.split('-').map(Number);
      // Create a date object with proper values (month is 0-indexed in JS Date)
      const dateObj = new Date(year, month - 1, day);
      // Format to a more user-friendly string
      return dateObj.toLocaleDateString(undefined, {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
    } catch (e) {
      // Fallback if parsing fails
      return dateStr;
    }
  };

  // Helper function to determine the appropriate unit for each metric - FIXED units
  const getUnitByMetricName = (metricName: string): string => {
    // ACWR values should be unitless
    if (metricName.includes('ACWR') || metricName.includes('Divergence')) {
      return '';
    }

    // Handle specific units
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

    // Miles-based metrics (distance, load, etc.)
    if (metricName.includes('Miles') ||
        metricName.includes('Distance') ||
        metricName.includes('Load') ||
        metricName === 'Total Miles') {
      return ' miles';
    }

    // Default: no unit
    return '';
  };

  // Custom tooltip component - FIXED tooltip display
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload || !payload.length) {
      return null;
    }

    // Format the date properly without timezone issues
    const formattedDate = formatTooltipDate(label);

    return (
      <div className={styles.customTooltip}>
        <p className={styles.tooltipLabel}>
          {formattedDate}
        </p>
        <div className={styles.tooltipContent}>
          {payload.map((entry: any, index: number) => (
            <div key={`item-${index}`} className={styles.tooltipItem}>
              <span className={styles.tooltipKey} style={{ color: entry.color }}>
                {entry.name}:
              </span>
              <span className={styles.tooltipValue}>
                {entry.value === null || entry.value === undefined
                  ? "N/A"
                  : `${parseFloat(entry.value).toFixed(2)}${getUnitByMetricName(entry.name)}`}
              </span>
            </div>
          ))}
        </div>
      </div>
    );
  };

  // Custom X-axis tick component with minor ticks
  const CustomXAxisTick = (props: any) => {
    const { x, y, payload, index, majorTickInterval, showMinorTicks, minorTickHeight, majorTickHeight } = props;

    // Determine if this is a major tick
    const isMajorTick = index % (majorTickInterval + 1) === 0;

    // Determine tick height and opacity
    const tickHeight = isMajorTick ? majorTickHeight : minorTickHeight;
    const tickOpacity = isMajorTick ? 1 : 0.6;

    return (
      <g transform={`translate(${x},${y})`}>
        {/* Draw the tick mark */}
        <line
          x1={0}
          y1={0}
          x2={0}
          y2={tickHeight}
          stroke={isMajorTick ? "#666" : "#999"}
          strokeOpacity={tickOpacity}
          className={isMajorTick ? styles.majorTick : styles.minorTick}
        />

        {/* Only show labels for major ticks */}
        {isMajorTick && (
          <text
            x={0}
            y={majorTickHeight + 4}
            dy={8}
            textAnchor="middle"
            fill="#666"
            fontSize={10}
          >
            {formatXAxis(payload.value)}
          </text>
        )}
      </g>
    );
  };

  // Helper functions
  const getAcwrStatus = (acwr: number) => {
    if (!acwr) return { color: '#ecf0f1', label: 'N/A' };
    if (acwr < 0.8) return { color: colors.warning, label: 'Undertraining' };
    if (acwr <= 1.3) return { color: colors.secondary, label: 'Optimal' };
    if (acwr <= 1.5) return { color: colors.warning, label: 'High Risk' };
    return { color: colors.danger, label: 'Very High Risk' };
  };

  const getDivergenceStatus = (divergence: number) => {
    if (divergence === undefined || divergence === null) return { color: '#ecf0f1', label: 'N/A' };
    if (divergence < -0.15) return { color: colors.danger, label: 'High Overtraining Risk' };
    if (divergence < -0.05) return { color: colors.warning, label: 'Moderate Risk' };
    if (divergence < 0.15) return { color: colors.secondary, label: 'Balanced' };
    return { color: colors.primary, label: 'Efficient' };
  };

  // Calculate normalized divergence between external and internal ACWR
  const calculateNormalizedDivergence = (externalAcwr: number, internalAcwr: number) => {
    if (externalAcwr === null || internalAcwr === null) return null;
    if (externalAcwr === 0 && internalAcwr === 0) return 0;

    const avgAcwr = (externalAcwr + internalAcwr) / 2;
    if (avgAcwr === 0) return 0;

    return parseFloat(((externalAcwr - internalAcwr) / avgAcwr).toFixed(3));
  };

  // Filter data based on date range using string comparison for reliability
  const filteredData = () => {
    if (data.length === 0) return [];

    const days = parseInt(dateRange, 10);

    // Find the latest date using string comparison
    const allDates = data.map(item => item.date).sort();
    const maxDate = allDates[allDates.length - 1];

    // Calculate cutoff date by working with Date objects (safely)
    const maxDateObj = new Date(`${maxDate}T12:00:00Z`); // Force noon UTC time
    const cutoffDateObj = new Date(maxDateObj);
    cutoffDateObj.setDate(cutoffDateObj.getDate() - days + 1); // +1 for inclusive

    // Convert back to YYYY-MM-DD format
    const cutoffDate = cutoffDateObj.toISOString().split('T')[0];

    // Filter using string comparison for reliability
    return data.filter(item => {
      return item.date >= cutoffDate && item.date <= maxDate;
    });
  };

  // Function to fetch LLM recommendations
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
      }
    } catch (error) {
      console.error("Error fetching recommendations:", error);
    } finally {
      setIsLoadingRecommendation(false);
    }
  };

  // Function to generate new recommendations
  const generateNewRecommendation = async () => {
    try {
      setIsLoadingRecommendation(true);
      const response = await fetch('/api/llm-recommendations/generate', {
        method: 'POST'
      });

      if (!response.ok) {
        throw new Error(`API responded with status ${response.status}`);
      }

      const result = await response.json();

      if (result.recommendation) {
        setRecommendation(result.recommendation);
      }
    } catch (error) {
      console.error("Error generating new recommendation:", error);
    } finally {
      setIsLoadingRecommendation(false);
    }
  };

const checkSyncStatus = async () => {
  try {
    // Since Strava doesn't have a specific sync-status endpoint,
    // check if we have recent data instead:
    const response = await fetch('/api/stats');
    if (response.ok) {
      const stats = await response.json();
      return {
        isRunning: false,
        lastSync: stats.lastActivity,
        totalActivities: stats.totalActivities
      };
    }
    return { isRunning: false, error: 'Unable to check status' };
  } catch (error) {
    console.error('Error checking sync status:', error);
    return { isRunning: false, error: error.message };
  }
};

const syncStravaData = async (days = 7) => {
  try {
    // You'll need to implement OAuth flow or use stored tokens
    const response = await fetch('/sync', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        days: days,
        // Add access_token if you have it stored
        // access_token: 'your_strava_token'
      })
    });

    if (!response.ok) {
      throw new Error(`Sync failed: ${response.status}`);
    }

    const result = await response.json();
    return result;
  } catch (error) {
    console.error('Sync error:', error);
    throw error;
  }
};

const testGarminConnection = async () => {
  setIsTestingConnection(true);
  setConnectionTestResult(null);

  try {
    const response = await fetch('/api/test-connection', {
      method: 'POST'
    });

    const result = await response.json();
    setConnectionTestResult(result);
  } catch (error) {
    setConnectionTestResult({
      success: false,
      error: 'Failed to test connection'
    });
  } finally {
    setIsTestingConnection(false);
  }
};

const startGarminSync = async (days: number = 30, includeWellness: boolean = true) => {
  try {
    const response = await fetch('/api/sync', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        days: days,
        include_wellness: includeWellness
      })
    });

    if (response.ok) {
      // Start polling for status updates
      const pollInterval = setInterval(() => {
        checkSyncStatus();
      }, 2000);

      // Stop polling after 10 minutes
      setTimeout(() => clearInterval(pollInterval), 600000);
    } else {
      const error = await response.json();
      console.error('Sync failed:', error);
    }
  } catch (error) {
    console.error('Error starting sync:', error);
  }
};

const testGarminConnection = async () => {
  setIsTestingConnection(true);
  setConnectionTestResult(null);

  try {
    const response = await fetch('/api/test-connection', {
      method: 'POST'
    });

    const result = await response.json();
    setConnectionTestResult(result);
  } catch (error) {
    setConnectionTestResult({
      success: false,
      error: 'Failed to test connection'
    });
  } finally {
    setIsTestingConnection(false);
  }
};

// Add this useEffect to check sync status on component mount
useEffect(() => {
  checkSyncStatus();
  // Check sync status every 30 seconds
  const interval = setInterval(checkSyncStatus, 30000);
  return () => clearInterval(interval);
}, []);

// Add this component before your existing charts
const GarminSyncPanel = () => (
  <div className={styles.chartContainer}>
    <h2 className={styles.chartTitle}>Garmin Data Sync</h2>

    {/* Connection Status */}
    <div style={{ marginBottom: '1rem' }}>
      <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', marginBottom: '0.5rem' }}>
        <button
          onClick={testGarminConnection}
          disabled={isTestingConnection}
          className={styles.refreshButton}
          style={{ padding: '0.5rem 1rem' }}
        >
          {isTestingConnection ? 'Testing...' : 'Test Garmin Connection'}
        </button>

        {connectionTestResult && (
          <div style={{
            padding: '0.5rem',
            borderRadius: '0.25rem',
            backgroundColor: connectionTestResult.success ? '#d4edda' : '#f8d7da',
            color: connectionTestResult.success ? '#155724' : '#721c24',
            fontSize: '0.875rem'
          }}>
            {connectionTestResult.success
              ? `✅ ${connectionTestResult.message}`
              : `❌ ${connectionTestResult.error}`
            }
          </div>
        )}
      </div>
    </div>

    {/* Sync Status */}
    {syncStatus && (
      <div style={{ marginBottom: '1rem' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
          <div>
            <strong>Database Status:</strong>
            <div style={{ fontSize: '0.875rem', color: '#6b7280' }}>
              Total Activities: {syncStatus.total_activities}
            </div>
            <div style={{ fontSize: '0.875rem', color: '#6b7280' }}>
              Latest Activity: {syncStatus.last_activity_date || 'None'}
            </div>
          </div>

          <div>
            <strong>Last Sync:</strong>
            <div style={{ fontSize: '0.875rem', color: '#6b7280' }}>
              {syncStatus.last_sync
                ? new Date(syncStatus.last_sync).toLocaleString()
                : 'Never'
              }
            </div>
          </div>
        </div>

        {syncStatus.is_running && (
          <div style={{
            marginTop: '1rem',
            padding: '1rem',
            backgroundColor: '#fff3cd',
            borderRadius: '0.375rem',
            border: '1px solid #ffeaa7'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <div style={{
                width: '1rem',
                height: '1rem',
                border: '2px solid #f3f4f6',
                borderTop: '2px solid #3b82f6',
                borderRadius: '50%',
                animation: 'spin 1s linear infinite'
              }}></div>
              <strong>Sync in Progress</strong>
            </div>
            <div style={{ marginTop: '0.5rem', fontSize: '0.875rem' }}>
              {syncStatus.progress}
            </div>
            {syncStatus.activities_processed > 0 && (
              <div style={{ fontSize: '0.875rem', color: '#6b7280' }}>
                Activities processed: {syncStatus.activities_processed}
              </div>
            )}
          </div>
        )}

        {syncStatus.last_error && (
          <div style={{
            marginTop: '1rem',
            padding: '1rem',
            backgroundColor: '#f8d7da',
            borderRadius: '0.375rem',
            border: '1px solid #f5c6cb',
            color: '#721c24'
          }}>
            <strong>Last Error:</strong>
            <div style={{ fontSize: '0.875rem', marginTop: '0.25rem' }}>
              {syncStatus.last_error}
            </div>
          </div>
        )}
      </div>
    )}

    {/* Sync Controls */}
    <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
      <button
        onClick={() => startGarminSync(7, true)}
        disabled={syncStatus?.is_running}
        className={styles.generateButton}
        style={{ padding: '0.75rem 1.5rem' }}
      >
        Sync Last 7 Days
      </button>

      <button
        onClick={() => startGarminSync(30, true)}
        disabled={syncStatus?.is_running}
        className={styles.generateButton}
        style={{ padding: '0.75rem 1.5rem' }}
      >
        Sync Last 30 Days
      </button>

      <button
        onClick={() => startGarminSync(90, true)}
        disabled={syncStatus?.is_running}
        className={styles.generateButton}
        style={{ padding: '0.75rem 1.5rem' }}
      >
        Sync Last 90 Days
      </button>
    </div>

    <div style={{ marginTop: '1rem', fontSize: '0.875rem', color: '#6b7280' }}>
      <p><strong>Note:</strong> First sync may take several minutes. The dashboard will update automatically when complete.</p>
      <p>Sync includes activities, wellness data (weight, effort, feeling), and calculates all training metrics.</p>
    </div>
  </div>
);

  // Function to fetch wellness metrics
  const fetchWellnessMetrics = async () => {
    try {
      const response = await fetch('/api/wellness-metrics');

      if (!response.ok) {
        throw new Error(`API responded with status ${response.status}`);
      }

      const result = await response.json();

      if (result.metrics) {
        setWellnessMetrics(result.metrics);
      }
    } catch (error) {
      console.error("Error fetching wellness metrics:", error);
    }
  };

  // Fetch data from the API
  useEffect(() => {
    const loadData = async () => {
      try {
        setIsLoading(true);
        setError(null);

        console.log("Fetching data from API...");
        const response = await fetch(`/api/training-data?t=${new Date().getTime()}`);

        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(`API responded with status ${response.status}: ${errorText}`);
        }

        const result = await response.json();

        if (!result.data || !Array.isArray(result.data) || result.data.length === 0) {
          throw new Error("No data returned from API");
        }

        console.log(`Successfully received ${result.data.length} records`);

        // Process data with proper date handling
        const processedData = result.data.map((row: TrainingDataRow) => {
          // Create dateObj using UTC noon to avoid timezone issues
          const dateObj = new Date(`${row.date}T12:00:00Z`);

          // Calculate normalized divergence if not present
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

        // Sort by date string for reliability
        processedData.sort((a, b) => a.date.localeCompare(b.date));
        setData(processedData);

        // Set the latest activity ID for wellness metrics
        if (processedData.length > 0) {
          // Find the latest non-rest activity
          const latestNonRestActivity = [...processedData]
            .reverse()
            .find(item => item.activity_id !== 0);

          if (latestNonRestActivity) {
            setLatestActivityId(latestNonRestActivity.activity_id);
          }
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
                processedData[processedData.length - 1].normalized_divergence as number : 0
            });
          }
        } catch (statsError) {
          console.warn("Failed to fetch stats, using data from main endpoint");

          // Fallback to calculating metrics from the main data
          if (processedData.length > 0) {
            const latestEntry = processedData[processedData.length - 1];

            // Calculate days since last rest
            const restDays = processedData.filter(item => item.activity_id === 0);
            let daysSinceRest = 0;

            if (restDays.length > 0) {
              const lastRestDate = new Date(Math.max(...restDays.map(d => d.dateObj.getTime())));
              const today = new Date();
              daysSinceRest = Math.floor((today.getTime() - lastRestDate.getTime()) / (24 * 60 * 60 * 1000));
            }

            setMetrics({
              externalAcwr: latestEntry.acute_chronic_ratio || 0,
              internalAcwr: latestEntry.trimp_acute_chronic_ratio || 0,
              sevenDayAvgLoad: latestEntry['7day_avg_load'] || 0,
              sevenDayAvgTrimp: latestEntry['7day_avg_trimp'] || 0,
              daysSinceRest: daysSinceRest,
              normalizedDivergence: latestEntry.normalized_divergence as number || 0
            });
          }
        }

        // Also fetch recommendations and wellness metrics
        console.log("About to fetch recommendations");
        fetchRecommendations();
        fetchWellnessMetrics();

      } catch (error) {
        console.error("Error loading data:", error);
        setError(`Failed to load data: ${error instanceof Error ? error.message : String(error)}`);
      } finally {
        setIsLoading(false);
        // Force re-render charts
        setRenderKey(prevKey => prevKey + 1);
      }
    };

    loadData();
  }, []);

// ADD THIS NEW useEffect HERE:
useEffect(() => {
  checkSyncStatus();
  // Check sync status every 30 seconds
  const interval = setInterval(checkSyncStatus, 30000);
  return () => clearInterval(interval);
}, []);

  // Handle date range change
  useEffect(() => {
    // Trigger re-render of charts
    setRenderKey(prevKey => prevKey + 1);
  }, [dateRange]);

  // Wellness Metrics History Chart
  const WellnessMetricsChart = () => {
    if (wellnessMetrics.length === 0) {
      return (
        <div className={styles.noData}>
          <p>No wellness metrics recorded yet.</p>
        </div>
      );
    }

    // Process data for the chart
    const chartData = wellnessMetrics.map(metric => ({
      date: metric.date,
      weight: metric.weight_lbs,
      effort: metric.perceived_effort,
      feeling: metric.feeling_score
    }));

    return (
      <div className={styles.chartWrapper} style={{ width: chartDimensions.width, height: chartDimensions.height }}>
        <ResponsiveContainer width="100%" height="100%" key={`wellness-${renderKey}`}>
          <ComposedChart
            data={chartData}
            margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="date"
              interval={0}
              tickLine={false}
              tick={(props) => (
                <CustomXAxisTick
                  {...props}
                  majorTickInterval={chartDimensions.majorTickInterval}
                  showMinorTicks={chartDimensions.showMinorTicks}
                  minorTickHeight={chartDimensions.minorTickHeight}
                  majorTickHeight={chartDimensions.majorTickHeight}
                />
              )}
              padding={{ left: 10, right: 10 }}
            />
            <YAxis
              yAxisId="weight"
              label={{ value: 'Weight (lbs)', angle: -90, position: 'insideLeft' }}
              domain={['dataMin - 5', 'dataMax + 5']}
            />
            <YAxis
              yAxisId="score"
              orientation="right"
              domain={[0, 10]}
              label={{ value: 'Score (1-10)', angle: 90, position: 'insideRight' }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend />

            {/* Weight Line */}
            <Line
              yAxisId="weight"
              type="monotone"
              dataKey="weight"
              name="Weight (lbs)"
              stroke={colors.primary}
              strokeWidth={defaultTheme.lineStyles.regular.strokeWidth}
              connectNulls={true}
              dot={(props) => {
                if (!props || !props.cx || !props.cy || !props.payload) return null;
                const { cx, cy, payload } = props;
                if (payload.weight === null || payload.weight === undefined) return null;
                return <circle cx={cx} cy={cy} r={4} fill={colors.primary} />;
              }}
            />

            {/* Perceived Effort Bars */}
            <Bar
              yAxisId="score"
              dataKey="effort"
              name="Perceived Effort"
              fill={colors.warning}
              barSize={chartDimensions.barSize / 2}
            />

            {/* Feeling Score Bars */}
            <Bar
              yAxisId="score"
              dataKey="feeling"
              name="Feeling Score"
              fill={colors.secondary}
              barSize={chartDimensions.barSize / 2}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    );
  };

const GarminSyncPanel = () => (
  <div className={styles.chartContainer}>
    <h2 className={styles.chartTitle}>Garmin Data Sync</h2>

    {/* Connection Status */}
    <div style={{ marginBottom: '1rem' }}>
      <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', marginBottom: '0.5rem' }}>
        <button
          onClick={testGarminConnection}
          disabled={isTestingConnection}
          className={styles.refreshButton}
          style={{ padding: '0.5rem 1rem' }}
        >
          {isTestingConnection ? 'Testing...' : 'Test Garmin Connection'}
        </button>

        {connectionTestResult && (
          <div style={{
            padding: '0.5rem',
            borderRadius: '0.25rem',
            backgroundColor: connectionTestResult.success ? '#d4edda' : '#f8d7da',
            color: connectionTestResult.success ? '#155724' : '#721c24',
            fontSize: '0.875rem'
          }}>
            {connectionTestResult.success
              ? `✅ ${connectionTestResult.message}`
              : `❌ ${connectionTestResult.error}`
            }
          </div>
        )}
      </div>
    </div>

    {/* Sync Status */}
    {syncStatus && (
      <div style={{ marginBottom: '1rem' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
          <div>
            <strong>Database Status:</strong>
            <div style={{ fontSize: '0.875rem', color: '#6b7280' }}>
              Total Activities: {syncStatus.total_activities}
            </div>
            <div style={{ fontSize: '0.875rem', color: '#6b7280' }}>
              Latest Activity: {syncStatus.last_activity_date || 'None'}
            </div>
          </div>

          <div>
            <strong>Last Sync:</strong>
            <div style={{ fontSize: '0.875rem', color: '#6b7280' }}>
              {syncStatus.last_sync
                ? new Date(syncStatus.last_sync).toLocaleString()
                : 'Never'
              }
            </div>
          </div>
        </div>

        {syncStatus.is_running && (
          <div style={{
            marginTop: '1rem',
            padding: '1rem',
            backgroundColor: '#fff3cd',
            borderRadius: '0.375rem',
            border: '1px solid #ffeaa7'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <div style={{
                width: '1rem',
                height: '1rem',
                border: '2px solid #f3f4f6',
                borderTop: '2px solid #3b82f6',
                borderRadius: '50%',
                animation: 'spin 1s linear infinite'
              }}></div>
              <strong>Sync in Progress</strong>
            </div>
            <div style={{ marginTop: '0.5rem', fontSize: '0.875rem' }}>
              {syncStatus.progress}
            </div>
            {syncStatus.activities_processed > 0 && (
              <div style={{ fontSize: '0.875rem', color: '#6b7280' }}>
                Activities processed: {syncStatus.activities_processed}
              </div>
            )}
          </div>
        )}

        {syncStatus.last_error && (
          <div style={{
            marginTop: '1rem',
            padding: '1rem',
            backgroundColor: '#f8d7da',
            borderRadius: '0.375rem',
            border: '1px solid #f5c6cb',
            color: '#721c24'
          }}>
            <strong>Last Error:</strong>
            <div style={{ fontSize: '0.875rem', marginTop: '0.25rem' }}>
              {syncStatus.last_error}
            </div>
          </div>
        )}
      </div>
    )}

    {/* Sync Controls */}
    <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
      <button
        onClick={() => startGarminSync(7, true)}
        disabled={syncStatus?.is_running}
        className={styles.generateButton}
        style={{ padding: '0.75rem 1.5rem' }}
      >
        Sync Last 7 Days
      </button>

      <button
        onClick={() => startGarminSync(30, true)}
        disabled={syncStatus?.is_running}
        className={styles.generateButton}
        style={{ padding: '0.75rem 1.5rem' }}
      >
        Sync Last 30 Days
      </button>

      <button
        onClick={() => startGarminSync(90, true)}
        disabled={syncStatus?.is_running}
        className={styles.generateButton}
        style={{ padding: '0.75rem 1.5rem' }}
      >
        Sync Last 90 Days
      </button>
    </div>

    <div style={{ marginTop: '1rem', fontSize: '0.875rem', color: '#6b7280' }}>
      <p><strong>Note:</strong> First sync may take several minutes. The dashboard will update automatically when complete.</p>
      <p>Sync includes activities, wellness data (weight, effort, feeling), and calculates all training metrics.</p>
    </div>
  </div>
);

  // Loading state
  if (isLoading) {
    return (
      <div className={styles.loading}>
        <h1 className={styles.title}>Loading dashboard...</h1>
        <p>Fetching training data from server...</p>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className={styles.error}>
        <h1 className={styles.errorTitle}>Error Loading Dashboard</h1>
        <p className={styles.errorMessage}>{error}</p>
        <div className={styles.errorTips}>
          <h2 className={styles.errorTipsTitle}>Troubleshooting Tips:</h2>
          <ul className={styles.errorTipsList}>
            <li>Make sure the Flask server is running on port 5000</li>
            <li>Check that CORS is enabled on the server</li>
            <li>Verify that the training_load_history.csv file exists and is readable</li>
            <li>Check browser console for additional error details</li>
          </ul>
          <button
            onClick={() => window.location.reload()}
            className={styles.retryButton}
          >
            Retry
          </button>
        </div>
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
      {/* Header with title and date range selector */}
      <div className={styles.header}>
        <h1 className={styles.title}>Rob's Training Load Dashboard</h1>
        <div className={styles.dateSelector}>
          <label htmlFor="dateRange" className={styles.dateSelectorLabel}>
            Time Period:
          </label>
          <select
            id="dateRange"
            value={dateRange}
            onChange={(e) => setDateRange(e.target.value)}
            className={styles.dateSelectorInput}
          >
            <option value="7">7 Days</option>
            <option value="14">14 Days</option>
            <option value="30">30 Days</option>
            <option value="60">60 Days</option>
            <option value="90">90 Days</option>
          </select>
        </div>
      </div>

      <GarminSyncPanel />

      <div className={styles.metricsGrid}>
        <div className={styles.metricCard}>
          <h3 className={styles.metricCardTitle}>Training Load Status</h3>
          <div className={styles.metricCardContent}>
            <div className={styles.metricItem}>
              <p className={styles.metricItemLabel}>External ACWR</p>
              <p
                className={styles.metricItemValue}
                style={{ color: getAcwrStatus(metrics.externalAcwr).color }}
              >
                {metrics.externalAcwr ? metrics.externalAcwr.toFixed(2) : "N/A"}
              </p>
            </div>
            <div className={styles.metricItem}>
              <p className={styles.metricItemLabel}>Internal ACWR</p>
              <p
                className={styles.metricItemValue}
                style={{ color: getAcwrStatus(metrics.internalAcwr).color }}
              >
                {metrics.internalAcwr ? metrics.internalAcwr.toFixed(2) : "N/A"}
              </p>
            </div>
            <div className={styles.metricItem}>
              <p className={styles.metricItemLabel}>Divergence</p>
              <p
                className={styles.metricItemValue}
                style={{ color: getDivergenceStatus(metrics.normalizedDivergence).color }}
              >
                {metrics.normalizedDivergence ? metrics.normalizedDivergence.toFixed(2) : "N/A"}
              </p>
            </div>
          </div>
          <div className={styles.metricStatus}>
            <p>
              Status: <span style={{ color: getDivergenceStatus(metrics.normalizedDivergence).color, fontWeight: 'bold' }}>
                {metrics.normalizedDivergence ? getDivergenceStatus(metrics.normalizedDivergence).label : "Unknown"}
              </span>
            </p>
          </div>
        </div>

        <div className={styles.metricCard}>
          <h3 className={styles.metricCardTitle}>Recovery Status</h3>
          <div className={styles.recoveryContent}>
            <div className={styles.recoveryItem}>
              <p className={styles.recoveryItemLabel}>Days Since Rest</p>
              <p
                className={styles.recoveryItemValue}
                style={{ color: metrics.daysSinceRest > 6 ? colors.warning : colors.secondary }}
              >
                {metrics.daysSinceRest}
              </p>
              <p className={styles.recoveryItemSubtext}>
                {metrics.daysSinceRest > 6 ? "Need rest day" : "Recovery on track"}
              </p>
            </div>
            <div className={styles.recoveryItem}>
              <p className={styles.recoveryItemLabel}>7-Day Avg Miles</p>
              <p
                className={styles.recoveryItemValue}
                style={{ color: colors.primary }}
              >
                {metrics.sevenDayAvgLoad ? metrics.sevenDayAvgLoad.toFixed(1) : "N/A"}
              </p>
              <p className={styles.recoveryItemSubtext}>With elevation</p>
            </div>
          </div>
        </div>
      </div>

      {/* Add Wellness Metrics Section */}
      <div className={styles.chartContainer}>
        <h2 className={styles.chartTitle}>Wellness Metrics</h2>
        <div className={styles.chartWrapper} style={{ width: chartDimensions.width, height: chartDimensions.height }}>
          <WellnessMetricsChart />
        </div>
        <p className={styles.chartNote}>
          Wellness metrics are automatically imported from Garmin Connect.
        </p>
      </div>

      {/* ACWR Chart */}
      <div className={styles.chartContainer}>
        <h2 className={styles.chartTitle}>Acute:Chronic Workload Ratio</h2>
        <div className={styles.chartWrapper} style={{ width: chartDimensions.width, height: chartDimensions.height }}>
          <ResponsiveContainer width="100%" height="100%" key={`acwr-${renderKey}`}>
            <LineChart
              data={filtered}
              margin={{ top: 5, right: 30, left: 20, bottom: 25 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="date"
                interval={0} // Show all ticks to enable minor ticks
                tickLine={false} // Disable default tick lines
                tick={(props) => (
                  <CustomXAxisTick
                    {...props}
                    majorTickInterval={chartDimensions.majorTickInterval}
                    showMinorTicks={chartDimensions.showMinorTicks}
                    minorTickHeight={chartDimensions.minorTickHeight}
                    majorTickHeight={chartDimensions.majorTickHeight}
                  />
                )}
                padding={{ left: 10, right: 10 }}
              />
              <YAxis
                domain={[0.5, 2]}
                label={{ value: 'ACWR', angle: -90, position: 'insideLeft' }}
              />
              <Tooltip
                content={<CustomTooltip />}
                isAnimationActive={false}
              />
              <Legend />

              <ReferenceArea
                y1={0.8}
                y2={1.3}
                stroke={colors.secondary}
                strokeWidth={defaultTheme.referenceAreas.optimal.strokeWidth}
                strokeOpacity={defaultTheme.referenceAreas.optimal.strokeOpacity}
                fill={`${colors.secondary}${defaultTheme.referenceAreas.optimal.fillOpacity}`}
                label={{
                  value: "Optimal ACWR (0.8-1.3)",
                  position: "insideTopRight",
                  fill: colors.secondary,
                  fontSize: defaultTheme.referenceAreas.optimal.fontSize,
                  fontWeight: 'bold'
                }}
              />

              {/* External ACWR (Miles) - calculated metric */}
              <Line
                type="monotone"
                dataKey="acute_chronic_ratio"
                name="External ACWR (Miles)"
                stroke={colors.primary}
                strokeWidth={defaultTheme.lineStyles.regular.strokeWidth}
                connectNulls={true}
                isAnimationActive={false}
                dot={(props) => {
                  if (!props || !props.cx || !props.cy || !props.payload) return null;
                  const { cx, cy, payload } = props;

                  // Only show dots for actual activities, not rest days
                  if (payload.activity_id === 0) return null;

                  // Only show if we have valid data
                  if (payload.acute_chronic_ratio === null ||
                      payload.acute_chronic_ratio === undefined) return null;

                  return <circle cx={cx} cy={cy} r={4} fill={colors.primary} />;
                }}
                activeDot={{ r: 6 }}
              />

              {/* Internal ACWR (TRIMP) - calculated metric */}
              <Line
                type="monotone"
                dataKey="trimp_acute_chronic_ratio"
                name="Internal ACWR (TRIMP)"
                stroke={colors.trimp}
                strokeWidth={defaultTheme.lineStyles.regular.strokeWidth}
                connectNulls={true}
                isAnimationActive={false}
                dot={(props) => {
                  if (!props || !props.cx || !props.cy || !props.payload) return null;
                  const { cx, cy, payload } = props;

                  // Only show dots for actual activities, not rest days
                  if (payload.activity_id === 0) return null;

                  // Only show if we have valid data
                  if (payload.trimp_acute_chronic_ratio === null ||
                      payload.trimp_acute_chronic_ratio === undefined) return null;

                  return <circle cx={cx} cy={cy} r={4} fill={colors.trimp} />;
                }}
                activeDot={{ r: 6 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Divergence Metric Chart */}
      <div className={styles.chartContainer}>
        <h2 className={styles.chartTitle}>Overtraining Risk Analysis</h2>
        <div className={styles.chartWrapper} style={{ width: chartDimensions.width, height: chartDimensions.height }}>
          <ResponsiveContainer width="100%" height="100%" key={`divergence-${renderKey}`}>
            <ComposedChart
              data={filtered}
              margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="date"
                interval={0} // Show all ticks to enable minor ticks
                tickLine={false} // Disable default tick lines
                tick={(props) => (
                  <CustomXAxisTick
                    {...props}
                    majorTickInterval={chartDimensions.majorTickInterval}
                    showMinorTicks={chartDimensions.showMinorTicks}
                    minorTickHeight={chartDimensions.minorTickHeight}
                    majorTickHeight={chartDimensions.majorTickHeight}
                  />
                )}
                padding={{ left: 10, right: 10 }}
              />
              <YAxis
                domain={[-0.5, 0.5]}
                label={{ value: 'ACWR Divergence', angle: -90, position: 'insideLeft' }}
              />
              <Tooltip
                content={<CustomTooltip />}
                isAnimationActive={false}
              />
              <Legend />

              <ReferenceArea
                y1={-0.05}
                y2={0.15}
                stroke={colors.secondary}
                strokeWidth={defaultTheme.referenceAreas.optimal.strokeWidth}
                strokeOpacity={defaultTheme.referenceAreas.optimal.strokeOpacity}
                fill={`${colors.secondary}${defaultTheme.referenceAreas.optimal.fillOpacity}`}
                label={{
                  value: "Balanced Zone",
                  position: "insideTopRight",
                  fill: colors.secondary,
                  fontSize: defaultTheme.referenceAreas.optimal.fontSize,
                  fontWeight: 'bold'
                }}
              />

              <ReferenceArea
                y1={-0.5}
                y2={-0.15}
                stroke={colors.danger}
                strokeWidth={defaultTheme.referenceAreas.risk.strokeWidth}
                strokeOpacity={defaultTheme.referenceAreas.risk.strokeOpacity}
                fill={`${colors.danger}${defaultTheme.referenceAreas.risk.fillOpacity}`}
                label={{
                  value: "High Overtraining Risk",
                  position: "insideBottomLeft",
                  fill: colors.danger,
                  fontSize: defaultTheme.referenceAreas.risk.fontSize,
                  fontWeight: 'bold'
                }}
              />

              <ReferenceArea
                y1={-0.15}
                y2={-0.05}
                stroke={colors.warning}
                strokeWidth={defaultTheme.referenceAreas.moderate.strokeWidth}
                strokeOpacity={defaultTheme.referenceAreas.moderate.strokeOpacity}
                fill={`${colors.warning}${defaultTheme.referenceAreas.moderate.fillOpacity}`}
                label={{
                  value: "Moderate Risk",
                  position: "insideBottom",
                  fill: colors.warning,
                  fontSize: defaultTheme.referenceAreas.moderate.fontSize,
                  fontWeight: 'bold'
                }}
              />

              <ReferenceArea
                y1={0.15}
                y2={0.5}
                stroke={colors.primary}
                strokeWidth={defaultTheme.referenceAreas.efficient.strokeWidth}
                strokeOpacity={defaultTheme.referenceAreas.efficient.strokeOpacity}
                fill={`${colors.primary}${defaultTheme.referenceAreas.efficient.fillOpacity}`}
                label={{
                  value: "Efficient",
                  position: "insideTopLeft",
                  fill: colors.primary,
                  fontSize: defaultTheme.referenceAreas.efficient.fontSize,
                  fontWeight: 'bold'
                }}
              />

              {/* Divergence Line - calculated metric */}
              <Line
                type="monotone"
                dataKey="normalized_divergence"
                name="ACWR Divergence"
                stroke={colors.dark}
                strokeWidth={defaultTheme.lineStyles.regular.strokeWidth}
                connectNulls={true}
                isAnimationActive={false}
                dot={(props) => {
                  if (!props || !props.cx || !props.cy || !props.payload) return null;
                  const { cx, cy, payload } = props;

                  // Only show dots for actual activities, not rest days
                  if (payload.activity_id === 0) return null;

                  // Only show if we have valid data
                  if (payload.normalized_divergence === null ||
                      payload.normalized_divergence === undefined) return null;

                  return <circle cx={cx} cy={cy} r={4} fill={colors.dark} />;
                }}
                activeDot={{ r: 6 }}
              />
              <ReferenceLine y={0} stroke="#666" strokeWidth={1} strokeDasharray="3 3" />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
        <p className={styles.chartNote}>
          Negative values indicate internal stress (TRIMP) is higher than external load (miles),
          suggesting potential overtraining. Positive values show efficient handling of workload.
        </p>
      </div>

      {/* External & Internal Load Chart */}
      <div className={styles.chartContainer}>
        <h2 className={styles.chartTitle}>External & Internal Load Trends</h2>
        <div className={styles.chartWrapper} style={{ width: chartDimensions.width, height: chartDimensions.height }}>
          <ResponsiveContainer width="100%" height="100%" key={`load-${renderKey}`}>
            <ComposedChart
              data={filtered}
              margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="date"
                interval={0} // Show all ticks to enable minor ticks
                tickLine={false} // Disable default tick lines
                tick={(props) => (
                  <CustomXAxisTick
                    {...props}
                    majorTickInterval={chartDimensions.majorTickInterval}
                    showMinorTicks={chartDimensions.showMinorTicks}
                    minorTickHeight={chartDimensions.minorTickHeight}
                    majorTickHeight={chartDimensions.majorTickHeight}
                  />
                )}
                padding={{ left: 10, right: 10 }}
              />
              <YAxis
                yAxisId="miles"
                label={{ value: 'Miles', angle: -90, position: 'insideLeft' }}
              />
              <YAxis
                yAxisId="trimp"
                orientation="right"
                label={{ value: 'TRIMP', angle: 90, position: 'insideRight' }}
              />
              <Tooltip
                content={<CustomTooltip />}
                isAnimationActive={false}
              />
              <Legend />

              {/* Bar chart for daily miles */}
              <Bar
                yAxisId="miles"
                dataKey="total_load_miles"
                name="Total Miles"
                fill={colors.primary}
                barSize={chartDimensions.barSize}
                opacity={defaultTheme.barStyles.regular.opacity}
                isAnimationActive={false}
              />

              {/* Moving average Line - calculated metric */}
              <Line
                yAxisId="miles"
                type="monotone"
                dataKey="7day_avg_load"
                name="7-Day Avg Miles"
                stroke={colors.secondary}
                strokeWidth={defaultTheme.lineStyles.thin.strokeWidth}
                dot={false} // No dots for moving averages
                isAnimationActive={false}
                connectNulls={true}
              />

              {/* TRIMP Line - direct workout metric */}
              <Line
                yAxisId="trimp"
                type="monotone"
                dataKey="trimp"
                name="TRIMP"
                stroke={colors.trimp}
                strokeWidth={defaultTheme.lineStyles.thin.strokeWidth}
                connectNulls={false} // Direct workout metric
                isAnimationActive={false}
                dot={(props) => {
                  if (!props || !props.cx || !props.cy || !props.payload) return null;
                  const { cx, cy, payload } = props;

                  // Only show dots for actual activities with TRIMP values
                  if (payload.activity_id === 0 ||
                      payload.trimp === 0 ||
                      payload.trimp === null ||
                      payload.trimp === undefined) return null;

                  return <circle cx={cx} cy={cy} r={4} fill={colors.trimp} />;
                }}
                activeDot={{ r: 6 }}
              />

              {/* Moving Average TRIMP Line - calculated metric */}
              <Line
                yAxisId="trimp"
                type="monotone"
                dataKey="7day_avg_trimp"
                name="7-Day Avg TRIMP"
                stroke={colors.accent}
                strokeWidth={defaultTheme.lineStyles.thin.strokeWidth}
                strokeDasharray={defaultTheme.lineStyles.dashed.strokeDasharray}
                dot={false} // No dots for moving averages
                isAnimationActive={false}
                connectNulls={true}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Distance & Elevation Chart */}
      <div className={styles.chartContainer}>
        <h2 className={styles.chartTitle}>Distance & Elevation Analysis</h2>
        <div className={styles.chartWrapper} style={{ width: chartDimensions.width, height: chartDimensions.height }}>
          <ResponsiveContainer width="100%" height="100%" key={`elevation-${renderKey}`}>
            <ComposedChart
              data={filtered}
              margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="date"
                interval={0} // Show all ticks to enable minor ticks
                tickLine={false} // Disable default tick lines
                tick={(props) => (
                  <CustomXAxisTick
                    {...props}
                    majorTickInterval={chartDimensions.majorTickInterval}
                    showMinorTicks={chartDimensions.showMinorTicks}
                    minorTickHeight={chartDimensions.minorTickHeight}
                    majorTickHeight={chartDimensions.majorTickHeight}
                  />
                )}
                padding={{ left: 10, right: 10 }}
              />
              <YAxis
                yAxisId="miles"
                label={{ value: 'Miles', angle: -90, position: 'insideLeft' }}
              />
              <YAxis
                yAxisId="elevation"
                orientation="right"
                label={{ value: 'Elevation (ft)', angle: 90, position: 'insideRight' }}
              />
              <Tooltip
                content={<CustomTooltip />}
                isAnimationActive={false}
              />
              <Legend />

              {/* Stacked bar chart for distance components */}
              <Bar
                yAxisId="miles"
                dataKey="distance_miles"
                name="Distance"
                fill={colors.primary}
                barSize={chartDimensions.barSize}
                opacity={defaultTheme.barStyles.regular.opacity}
                stackId="a"
                isAnimationActive={false}
              />
              <Bar
                yAxisId="miles"
                dataKey="elevation_load_miles"
                name="Elevation Load"
                fill={colors.secondary}
                barSize={chartDimensions.barSize}
                opacity={defaultTheme.barStyles.regular.opacity}
                stackId="a"
                isAnimationActive={false}
              />

              {/* Elevation Gain Line - direct workout metric */}
              <Line
                yAxisId="elevation"
                type="monotone"
                dataKey="elevation_gain_feet"
                name="Elevation Gain"
                stroke={colors.dark}
                strokeWidth={defaultTheme.lineStyles.thin.strokeWidth}
                connectNulls={false} // Direct workout metric
                isAnimationActive={false}
                dot={(props) => {
                  if (!props || !props.cx || !props.cy || !props.payload) return null;
                  const { cx, cy, payload } = props;

                  // Only show dots for actual elevation gain
                  if (payload.activity_id === 0 ||
                      payload.elevation_gain_feet === 0 ||
                      payload.elevation_gain_feet === null ||
                      payload.elevation_gain_feet === undefined) return null;

                  return <circle cx={cx} cy={cy} r={4} fill={colors.dark} />;
                }}
                activeDot={{ r: 6 }}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Enhanced Training Recommendations Section - Using existing CSS classes */}
      <div className={styles.chartContainer}>
        <h2 className={styles.chartTitle}>Training Recommendations & Analysis</h2>

        {/* Status Banner - Using inline styles since CSS class doesn't exist */}
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
            <h3 className={styles.recommendationHeading}>
              🎯 Today's Training Decision
            </h3>

            <div className={styles.recommendationTabs}>
              <div className={styles.recommendationTab} style={{borderLeft: '3px solid #3b82f6'}}>
                <h4 className={styles.tabHeading}>
                  🤖 AI Analysis
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
                        <strong>⚠️ HIGH RISK:</strong> Normalized divergence of {metrics.normalizedDivergence?.toFixed(2)}
                        indicates significant overtraining risk. Rest or very light activity only.
                      </span>
                    ) : metrics.normalizedDivergence < -0.05 ? (
                      <span style={{ color: colors.warning }}>
                        <strong>🔶 CAUTION:</strong> Divergence of {metrics.normalizedDivergence?.toFixed(2)} shows
                        moderate fatigue. Reduce intensity by 20-30% from planned workout.
                      </span>
                    ) : metrics.externalAcwr > 1.3 || metrics.internalAcwr > 1.3 ? (
                      <span style={{ color: colors.warning }}>
                        <strong>📈 ELEVATED ACWR:</strong> External: {metrics.externalAcwr?.toFixed(2)},
                        Internal: {metrics.internalAcwr?.toFixed(2)}. Reduce volume by 25% to manage injury risk.
                      </span>
                    ) : metrics.daysSinceRest > 5 && metrics.normalizedDivergence < -0.02 ? (
                      <span style={{ color: colors.warning }}>
                        <strong>🔄 RECOVERY NEEDED:</strong> {metrics.daysSinceRest} days since rest with slight fatigue.
                        Active recovery or easy Zone 1-2 session recommended.
                      </span>
                    ) : metrics.externalAcwr < 0.8 && metrics.internalAcwr < 0.8 ? (
                      <span style={{ color: colors.primary }}>
                        <strong>📊 PROGRESSION OPPORTUNITY:</strong> Both ACWR values below 0.8 indicate potential
                        for 10-15% load increase if feeling good.
                      </span>
                    ) : (
                      <span style={{ color: colors.secondary }}>
                        <strong>✅ GREEN LIGHT:</strong> All metrics in optimal ranges. Proceed with planned training.
                        Current load balance looks sustainable.
                      </span>
                    )}
                  </p>
                  <div style={{display: 'flex', gap: '0.5rem', marginTop: '0.5rem', flexWrap: 'wrap' as const}}>
                    <div style={{
                      backgroundColor: getAcwrStatus(metrics.externalAcwr).color + '20',
                      color: getAcwrStatus(metrics.externalAcwr).color,
                      padding: '0.25rem 0.5rem',
                      borderRadius: '0.25rem',
                      fontSize: '0.75rem'
                    }}>
                      Ext ACWR: {metrics.externalAcwr?.toFixed(2)} ({getAcwrStatus(metrics.externalAcwr).label})
                    </div>
                    <div style={{
                      backgroundColor: getDivergenceStatus(metrics.normalizedDivergence).color + '20',
                      color: getDivergenceStatus(metrics.normalizedDivergence).color,
                      padding: '0.25rem 0.5rem',
                      borderRadius: '0.25rem',
                      fontSize: '0.75rem'
                    }}>
                      Divergence: {metrics.normalizedDivergence?.toFixed(2)} ({getDivergenceStatus(metrics.normalizedDivergence).label})
                    </div>
                  </div>
                </div>
              </div>
            </div>
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
                  {recommendation && (
                    <div style={{marginTop: '0.5rem'}}>
                      <small style={{color: '#6b7280', fontSize: '0.75rem'}}>
                        7-day avg: {metrics.sevenDayAvgLoad?.toFixed(1)} mi/day |
                        TRIMP: {metrics.sevenDayAvgTrimp?.toFixed(0)}/day
                      </small>
                    </div>
                  )}
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
                        is too high. Target reducing to {(metrics.sevenDayAvgLoad * 0.75)?.toFixed(1)} mi/day over next 5-7 days
                        through rest days and reduced volume sessions.
                      </>
                    ) : metrics.externalAcwr < 0.8 && metrics.internalAcwr < 0.8 ? (
                      <>
                        <strong>Progressive build opportunity:</strong> Gradually increase 7-day average from {metrics.sevenDayAvgLoad?.toFixed(1)}
                        to {(metrics.sevenDayAvgLoad * 1.15)?.toFixed(1)} mi/day over next 2 weeks. Add 1-2 miles to existing sessions.
                      </>
                    ) : (
                      <>
                        <strong>Maintenance phase:</strong> Current 7-day average ({metrics.sevenDayAvgLoad?.toFixed(1)} mi/day)
                        is in optimal range. Continue with similar daily volumes around this level.
                        {metrics.daysSinceRest > 3 && " Schedule rest day within next 2-3 days."}
                      </>
                    )}
                  </p>
                  <div style={{marginTop: '0.5rem', padding: '0.5rem', backgroundColor: '#f8f9fa', borderRadius: '0.25rem'}}>
                    <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
                      <span style={{fontWeight: '500', fontSize: '0.875rem'}}>Target Daily Avg:</span>
                      <span style={{fontWeight: '600', color: colors.primary}}>
                        {metrics.externalAcwr > 1.3 ?
                          `${(metrics.sevenDayAvgLoad * 0.75)?.toFixed(1)}-${(metrics.sevenDayAvgLoad * 0.85)?.toFixed(1)} mi` :
                          metrics.externalAcwr < 0.8 ?
                          `${(metrics.sevenDayAvgLoad * 1.05)?.toFixed(1)}-${(metrics.sevenDayAvgLoad * 1.15)?.toFixed(1)} mi` :
                          `${(metrics.sevenDayAvgLoad * 0.9)?.toFixed(1)}-${(metrics.sevenDayAvgLoad * 1.1)?.toFixed(1)} mi`
                        }
                      </span>
                    </div>
                  </div>
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
                          "External and internal loads are well-balanced, indicating good adaptation to current training." :
                          metrics.normalizedDivergence < -0.05 ?
                          "Internal stress is elevated relative to external work - focus on recovery quality and sleep." :
                          "External work capacity exceeds internal stress - opportunity for gradual intensity increases."
                        }
                      </span>
                    </div>

                    <div>
                      <strong>Recovery Pattern:</strong>
                      <span style={{marginLeft: '0.5rem', color: '#4b5563'}}>
                        {metrics.daysSinceRest <= 2 ? "Recent rest day supporting good recovery cycle." :
                         metrics.daysSinceRest <= 5 ? `${metrics.daysSinceRest} days since rest - within normal training block.` :
                         `${metrics.daysSinceRest} days without rest - consider scheduling recovery soon.`}
                      </span>
                    </div>

                    <div>
                      <strong>Trend Assessment:</strong>
                      <span style={{marginLeft: '0.5rem', color: '#4b5563'}}>
                        {metrics.externalAcwr > 1.2 && metrics.internalAcwr > 1.2 ?
                          "Both ACWR values trending high - monitor for plateau or step-back need." :
                          metrics.externalAcwr < 0.9 && metrics.internalAcwr < 0.9 ?
                          "Conservative loading phase - good foundation for future progression." :
                          "Balanced progression with sustainable load management."}
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
                  (Valid until: {new Date(recommendation.valid_until).toLocaleDateString()})
                </span>
              </div>
            ) : (
              <div>
                <span style={{color: '#6b7280', fontSize: '0.875rem'}}>
                  AI analysis provides personalized insights based on your training patterns and the comprehensive Training Metrics Reference Guide.
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
                    Updating Analysis...
                  </>
                ) : (
                  <>
                    <span>🔄</span>
                    Refresh AI Analysis
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

            <div style={{display: 'flex', alignItems: 'center', gap: '0.5rem'}}>
              <span style={{fontSize: '0.75rem', color: '#6b7280'}}>Data Confidence:</span>
              <div style={{display: 'flex', gap: '0.25rem'}}>
                <div style={{
                  width: '0.5rem',
                  height: '1rem',
                  backgroundColor: '#10b981',
                  borderRadius: '0.125rem'
                }} title="Distance & Duration: High"></div>
                <div style={{
                  width: '0.5rem',
                  height: '1rem',
                  backgroundColor: '#10b981',
                  borderRadius: '0.125rem'
                }} title="Heart Rate: High"></div>
                <div style={{
                  width: '0.5rem',
                  height: '1rem',
                  backgroundColor: '#f59e0b',
                  borderRadius: '0.125rem'
                }} title="TRIMP Calculations: Medium"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TrainingLoadDashboard;