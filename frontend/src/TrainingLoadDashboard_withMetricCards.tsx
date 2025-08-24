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

// LLMRecommendation interface from recommendations_component.ts
interface LLMRecommendation {
  id: number;
  generation_date: string;
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

  // Recommendation state variables from recommendations_component.ts
  const [recommendation, setRecommendation] = useState<LLMRecommendation | null>(null);
  const [isLoadingRecommendation, setIsLoadingRecommendation] = useState<boolean>(false);

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

  // Custom tooltip component (restored)
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload || !payload.length) {
      return null;
    }

    const formattedDate = formatTooltipDate(label);

    // Get the activity_id from the first payload item
    const activityId = payload[0]?.payload?.activity_id;

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

          {/* Add the required "View on Strava" link */}
          {activityId && activityId > 0 && (
            <div className={styles.tooltipItem} style={{ marginTop: '8px', paddingTop: '8px', borderTop: '1px solid #eee' }}>
              <a
                href={`https://www.strava.com/activities/${activityId}`}
                target="_blank"
                rel="noopener noreferrer"
                style={{
                  color: '#FC5200',
                  textDecoration: 'underline',
                  fontSize: '12px',
                  fontWeight: 'bold'
                }}
              >
                View on Strava
              </a>
            </div>
          )}
        </div>
      </div>
    );
  };

  // Status helper functions (restored)
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

  // Calculate normalized divergence
  const calculateNormalizedDivergence = (externalAcwr: number, internalAcwr: number) => {
    if (externalAcwr === null || internalAcwr === null) return null;
    if (externalAcwr === 0 && internalAcwr === 0) return 0;

    const avgAcwr = (externalAcwr + internalAcwr) / 2;
    if (avgAcwr === 0) return 0;

    return parseFloat(((externalAcwr - internalAcwr) / avgAcwr).toFixed(3));
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
    console.log("generateNewRecommendation called");
    try {
      setIsLoadingRecommendation(true);
      console.log("Sending request to /api/llm-recommendations/generate");
      const response = await fetch('/api/llm-recommendations/generate', { // Corrected endpoint
        method: 'POST'
      });
      console.log("Generate recommendation response status:", response.status);

      if (!response.ok) {
        console.error(`API response not OK: ${response.status}`);
        throw new Error(`API responded with status ${response.status}`);
      }

      const result = await response.json();
      console.log("Generate recommendation API result:", result);

      if (result.recommendation) {
        console.log("Setting recommendation state with:", result.recommendation);
        setRecommendation(result.recommendation);
      } else {
        console.log("No recommendation in result after generation:", result);
        setRecommendation(null); // Explicitly set to null if no recommendation
      }
    } catch (e) {
      console.error("Failed to generate new recommendation:", e);
      setError("Failed to generate new AI recommendations."); // Set error in main dashboard error state
      setRecommendation(null);
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
        const response = await fetch(`/api/training-data?t=${new Date().getTime()}`);

        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(`API responded with status ${response.status}: ${errorText}`);
        }

        const result = await response.json();

        if (!result.data || !Array.isArray(result.data) || result.data.length === 0) {
          throw new Error("No data returned from API");
        }

        console.log(`Successfully received ${result.data.length} records from Strava`);

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

      {/* Metrics Grid */}
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
                interval={chartDimensions.majorTickInterval}
                tickFormatter={formatXAxis}
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

              {/* External ACWR (Miles) */}
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
                  if (payload.activity_id === 0) return null;
                  if (payload.acute_chronic_ratio === null || payload.acute_chronic_ratio === undefined) return null;
                  return <circle cx={cx} cy={cy} r={4} fill={colors.primary} />;
                }}
                activeDot={{ r: 6 }}
              />

              {/* Internal ACWR (TRIMP) */}
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
                  if (payload.activity_id === 0) return null;
                  if (payload.trimp_acute_chronic_ratio === null || payload.trimp_acute_chronic_ratio === undefined) return null;
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
                interval={chartDimensions.majorTickInterval}
                tickFormatter={formatXAxis}
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

              {/* Divergence Line */}
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
                  if (payload.activity_id === 0) return null;
                  if (payload.normalized_divergence === null || payload.normalized_divergence === undefined) return null;
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
                interval={chartDimensions.majorTickInterval}
                tickFormatter={formatXAxis}
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

              {/* Moving average Line */}
              <Line
                yAxisId="miles"
                type="monotone"
                dataKey="7day_avg_load"
                name="7-Day Avg Miles"
                stroke={colors.secondary}
                strokeWidth={defaultTheme.lineStyles.thin.strokeWidth}
                dot={false}
                isAnimationActive={false}
                connectNulls={true}
              />

              {/* TRIMP Line */}
              <Line
                yAxisId="trimp"
                type="monotone"
                dataKey="trimp"
                name="TRIMP"
                stroke={colors.trimp}
                strokeWidth={defaultTheme.lineStyles.thin.strokeWidth}
                connectNulls={false}
                isAnimationActive={false}
                dot={(props) => {
                  if (!props || !props.cx || !props.cy || !props.payload) return null;
                  const { cx, cy, payload } = props;
                  if (payload.activity_id === 0 || payload.trimp === 0 || payload.trimp === null || payload.trimp === undefined) return null;
                  return <circle cx={cx} cy={cy} r={4} fill={colors.trimp} />;
                }}
                activeDot={{ r: 6 }}
              />

              {/* Moving Average TRIMP Line */}
              <Line
                yAxisId="trimp"
                type="monotone"
                dataKey="7day_avg_trimp"
                name="7-Day Avg TRIMP"
                stroke={colors.accent}
                strokeWidth={defaultTheme.lineStyles.thin.strokeWidth}
                strokeDasharray={defaultTheme.lineStyles.dashed.strokeDasharray}
                dot={false}
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
                interval={chartDimensions.majorTickInterval}
                tickFormatter={formatXAxis}
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

              {/* Elevation Gain Line */}
              <Line
                yAxisId="elevation"
                type="monotone"
                dataKey="elevation_gain_feet"
                name="Elevation Gain"
                stroke={colors.dark}
                strokeWidth={defaultTheme.lineStyles.thin.strokeWidth}
                connectNulls={false}
                isAnimationActive={false}
                dot={(props) => {
                  if (!props || !props.cx || !props.cy || !props.payload) return null;
                  const { cx, cy, payload } = props;
                  if (payload.activity_id === 0 || payload.elevation_gain_feet === 0 || payload.elevation_gain_feet === null || payload.elevation_gain_feet === undefined) return null;
                  return <circle cx={cx} cy={cy} r={4} fill={colors.dark} />;
                }}
                activeDot={{ r: 6 }}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
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