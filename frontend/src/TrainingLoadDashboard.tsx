import React, { useState, useEffect } from 'react';
import {
  Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, ReferenceArea, ComposedChart, ReferenceLine, Bar
} from 'recharts';
import styles from './TrainingLoadDashboard.module.css';
import defaultTheme from './chartTheme';
import { useChartDimensions } from './useChartDimensions';
import CompactDashboardBanner from './CompactDashboardBanner';
import { usePagePerformanceMonitoring, useComponentPerformanceMonitoring } from './usePerformanceMonitoring';

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
  is_autopsy_informed?: boolean;  // NEW: indicates if generated with autopsy insights
  autopsy_count?: number;  // NEW: number of recent autopsies used
  avg_alignment_score?: number;  // NEW: average alignment score from autopsies
}

const coerceNumber = (value: any, fallback: number = NaN): number => {
  if (typeof value === 'number') {
    return Number.isFinite(value) ? value : fallback;
  }

  if (typeof value === 'string') {
    const parsed = parseFloat(value);
    return Number.isFinite(parsed) ? parsed : fallback;
  }

  if (value != null && typeof value.valueOf === 'function') {
    const primitive = value.valueOf();
    if (typeof primitive === 'number') {
      return Number.isFinite(primitive) ? primitive : fallback;
    }
    if (typeof primitive === 'string') {
      const parsed = parseFloat(primitive);
      return Number.isFinite(parsed) ? parsed : fallback;
    }
  }

  return fallback;
};

const formatNumber = (value: any, digits: number, fallback = 'N/A'): string => {
  const num = coerceNumber(value);
  if (!Number.isFinite(num)) {
    return fallback;
  }
  return num.toFixed(digits);
};

const formatScaledNumber = (value: any, scale: number, digits: number, fallback = 'N/A'): string => {
  const num = coerceNumber(value);
  if (!Number.isFinite(num)) {
    return fallback;
  }
  const scaled = num * scale;
  if (!Number.isFinite(scaled)) {
    return fallback;
  }
  return scaled.toFixed(digits);
};

interface TrainingLoadDashboardProps {
  onNavigateToTab?: (tab: string) => void;
}

const TrainingLoadDashboard: React.FC<TrainingLoadDashboardProps> = ({ onNavigateToTab }) => {
  console.log("TrainingLoadDashboard component initialized");

  // Performance monitoring
  usePagePerformanceMonitoring('dashboard');
  const perfMonitor = useComponentPerformanceMonitoring('TrainingLoadDashboard');

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
  const [dateRange, setDateRange] = useState('30');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [renderKey, setRenderKey] = useState(0);
  const [selectedSports, setSelectedSports] = useState(['running', 'cycling', 'swimming']);
  const [hasCyclingData, setHasCyclingData] = useState(false);
  const [hasSwimmingData, setHasSwimmingData] = useState(false);

  // Recommendation state variables from recommendations_component.ts
  const [recommendation, setRecommendation] = useState<LLMRecommendation | null>(null);
  const [isLoadingRecommendation, setIsLoadingRecommendation] = useState<boolean>(false);

  // NEW: Journal status for workflow enforcement
  const [journalStatus, setJournalStatus] = useState<{
    has_activity: boolean;
    activity_date: string | null;
    has_journal: boolean;
    allow_manual_generation: boolean;
    reason: string;
  } | null>(null);

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
  
  // FIXED: Properly extract Pacific date components without converting back to UTC
  const pacificFormatter = new Intl.DateTimeFormat('en-US', {
    timeZone: "America/Los_Angeles",
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  });
  
  const parts = pacificFormatter.formatToParts(today);
  const year = parts.find(p => p.type === 'year')?.value || '';
  const month = parts.find(p => p.type === 'month')?.value || '';
  const day = parts.find(p => p.type === 'day')?.value || '';
  const todayStr = `${year}-${month}-${day}`;
  
  // Calculate tomorrow's date string
  const tomorrowDate = new Date(todayStr + 'T12:00:00');
  tomorrowDate.setDate(tomorrowDate.getDate() + 1);
  const tomorrowStr = tomorrowDate.toISOString().split('T')[0];

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
  } else if (targetDate > tomorrowDate) {
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
    const [, month, day] = dateStr.split('-').map(Number);
    return `${month}/${day}`;
  };

  const formatTooltipDate = (dateStr: string): string => {
    if (!dateStr) return '';
    try {
      const [, month, day] = dateStr.split('-').map(Number);
      const dateObj = new Date(new Date().getFullYear(), month - 1, day);
      return dateObj.toLocaleDateString(undefined, {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
    } catch (e) {
      return dateStr;
    }
  };

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
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
                  {(() => {
                    if (displayValue === null || displayValue === undefined) {
                      return 'N/A';
                    }

                    const digits = displayName.includes('ACWR') || displayName.includes('Divergence') ? 3 : 1;
                    const numericValue = coerceNumber(displayValue, NaN);

                    if (Number.isFinite(numericValue)) {
                      return numericValue.toFixed(digits);
                    }

                    return typeof displayValue === 'string' ? displayValue : 'N/A';
                  })()}
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
    // Check for null, undefined, or NaN
    if (externalAcwr == null || internalAcwr == null || isNaN(externalAcwr) || isNaN(internalAcwr)) {
      return null;
    }
    if (externalAcwr === 0 && internalAcwr === 0) return 0;

    const avgAcwr = (externalAcwr + internalAcwr) / 2;
    if (avgAcwr === 0) return 0;

    const result = (externalAcwr - internalAcwr) / avgAcwr;
    if (isNaN(result)) {
      return null;
    }

    return parseFloat(result.toFixed(3));
  };

  // FIXED: Dynamic domain calculation for normalized divergence with inverted axis
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const getDivergenceDomain = (data: ProcessedDataRow[]) => {
    const divergenceValues = data
      .map(d => coerceNumber(d.normalized_divergence, NaN))
      .filter((value): value is number => value !== null && value !== undefined);

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

  // NEW: Function to fetch journal status for workflow enforcement
  const fetchJournalStatus = async () => {
    try {
      console.log("Fetching journal status...");
      const response = await fetch('/api/journal-status');
      
      if (!response.ok) {
        console.error(`Journal status API response not OK: ${response.status}`);
        return;
      }

      const result = await response.json();
      console.log("Journal status result:", result);

      if (result.success && result.status) {
        setJournalStatus(result.status);
      }
    } catch (e) {
      console.error("Failed to fetch journal status:", e);
      // Don't fail the dashboard - just allow manual generation
      setJournalStatus({
        has_activity: false,
        activity_date: null,
        has_journal: false,
        allow_manual_generation: true,
        reason: 'error'
      });
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
        
        // Step 3: Refresh journal status
        await fetchJournalStatus();

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
          perfMonitor.trackFetchStart();
          const response = await fetch(`/api/training-data?t=${new Date().getTime()}&include_sport_breakdown=true`);

          if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`API responded with status ${response.status}: ${errorText}`);
          }

          const result = await response.json();
          perfMonitor.trackFetchEnd();

          // Handle no data case gracefully - check if we can sync instead of throwing error
          if (!result.data || !Array.isArray(result.data) || result.data.length === 0) {
            console.log("No training data found, checking sync capabilities...");
            
            // If we can sync, show the no-data state with sync button
            if (result.can_sync) {
              console.log("User can sync data - showing no-data state");
              setData([]); // Set empty data array
              setIsLoading(false);
              return; // Exit early, let the no-data state render
            } else {
              // Only throw error if we truly can't get data and can't sync
              throw new Error("No data returned from API and sync not available");
            }
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

            const externalAcwr = coerceNumber(row.acute_chronic_ratio, 0);
            const internalAcwr = coerceNumber(row.trimp_acute_chronic_ratio, 0);
            const sevenDayAvgLoad = coerceNumber(row.seven_day_avg_load, 0);
            const sevenDayAvgTrimp = coerceNumber(row.seven_day_avg_trimp, 0);

            let normalizedDivergence = row.normalized_divergence !== undefined
              ? coerceNumber(row.normalized_divergence, NaN)
              : NaN;

            if (!Number.isFinite(normalizedDivergence)) {
              normalizedDivergence = calculateNormalizedDivergence(externalAcwr, internalAcwr) ?? NaN;
            }

            return {
              ...row,
              dateObj,
              acute_chronic_ratio: externalAcwr,
              trimp_acute_chronic_ratio: internalAcwr,
              seven_day_avg_load: sevenDayAvgLoad,
              seven_day_avg_trimp: sevenDayAvgTrimp,
              normalized_divergence: Number.isFinite(normalizedDivergence) ? normalizedDivergence : 0
            };
          });

          processedData.sort((a, b) => a.date.localeCompare(b.date));
          setData(processedData);

          if (result.has_cycling_data !== undefined) {
            setHasCyclingData(result.has_cycling_data);
          }
          if (result.has_swimming_data !== undefined) {
            setHasSwimmingData(result.has_swimming_data);
          }

          // Get stats from the API
          try {
            const statsResponse = await fetch(`/api/stats?t=${new Date().getTime()}`);

            if (statsResponse.ok) {
              const statsData = await statsResponse.json();

              const latestNormalized = processedData.length > 0
                ? coerceNumber(processedData[processedData.length - 1].normalized_divergence, NaN)
                : NaN;

              setMetrics({
                externalAcwr: coerceNumber(statsData.latestMetrics?.externalAcwr, 0),
                internalAcwr: coerceNumber(statsData.latestMetrics?.internalAcwr, 0),
                sevenDayAvgLoad: coerceNumber(statsData.latestMetrics?.sevenDayAvgLoad, 0),
                sevenDayAvgTrimp: coerceNumber(statsData.latestMetrics?.sevenDayAvgTrimp, 0),
                daysSinceRest: coerceNumber(statsData.daysSinceRest, 0),
                normalizedDivergence: Number.isFinite(latestNormalized) ? latestNormalized : 0,
                dashboardConfig: result.dashboard_config || undefined
              });
            }
          } catch (statsError) {
            console.warn("Failed to fetch stats, using data from main endpoint");
          }

        } catch (error) {
          console.error("Error loading data:", error);
          setError(`Failed to load data: ${error instanceof Error ? error.message : String(error)}`);
          perfMonitor.reportMetrics(0, error instanceof Error ? error.message : String(error));
        } finally {
          setIsLoading(false);
          setRenderKey(prevKey => prevKey + 1);
          // Report performance metrics on successful load
          if (!error) {
            perfMonitor.reportMetrics(data.length);
          }
        }
      };

      loadData();
      fetchRecommendations(); // Fetch recommendations on initial load
      fetchJournalStatus(); // Fetch journal status for workflow enforcement
    // eslint-disable-next-line react-hooks/exhaustive-deps
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
        <h1 className={styles.title}>No Training Data Available</h1>
        <p>No training data found for the selected time period.</p>
        <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', marginTop: '1rem' }}>
          <button
            onClick={() => setDateRange('90')}
            className={styles.retryButton}
          >
            View Last 90 Days
          </button>
          {/* Show sync button if user has Strava connected */}
          <button
            onClick={async () => {
              try {
                console.log('Starting Strava sync from no-data state...');
                const response = await fetch('/sync-with-auto-refresh', {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' }
                });
                
                const result = await response.json();
                console.log('Sync result:', result);
                
                if (result.success) {
                  console.log('Sync started successfully, reloading page...');
                  // Wait a moment for sync to start, then reload
                  setTimeout(() => {
                    window.location.reload();
                  }, 2000);
                } else {
                  console.error('Sync failed:', result.error);
                  alert(`Sync failed: ${result.error}`);
                }
              } catch (error) {
                console.error('Error starting sync:', error);
                alert('Error starting sync. Please try again.');
              }
            }}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.5rem 1rem',
              borderRadius: '0.375rem',
              border: 'none',
              fontSize: '0.85rem',
              fontWeight: '500',
              cursor: 'pointer',
              backgroundColor: '#FC5200',
              color: 'white',
              transition: 'all 0.2s ease'
            }}
          >
            <span>🔄</span>
            Sync Strava Data
          </button>
        </div>
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

      {/* Consolidated Dashboard Controls */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '0.25rem',
          padding: '0.5rem',
          backgroundColor: 'white',
          borderRadius: '0.5rem',
          boxShadow: '0 1px 2px rgba(0, 0, 0, 0.05)',
          flexWrap: 'wrap',
          gap: '1rem'
        }}>
          {/* Left side: Training Charts and Time Period */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
            <h2 style={{ margin: 0, fontSize: '1.1rem', fontWeight: '600', color: '#374151' }}>
              Training Charts
            </h2>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
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
              <label style={{ fontSize: '0.875rem', fontWeight: '500', color: '#374151' }}>
                Time Period
              </label>
            </div>
          </div>

          {/* Right side: Show Sports (only if multi-sport data exists) */}
          {(hasCyclingData || hasSwimmingData) && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
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
                {hasCyclingData && (
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
                )}
                {hasSwimmingData && (
                  <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={selectedSports.includes('swimming')}
                      onChange={() => setSelectedSports(prev =>
                        prev.includes('swimming') ? prev.filter(s => s !== 'swimming') : [...prev, 'swimming']
                      )}
                    />
                    <span style={{ color: '#e67e22' }}>Swimming</span>
                  </label>
                )}
              </div>
            </div>
          )}
        </div>

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
                  style: { textAnchor: 'middle', fontSize: '14px', fontWeight: '500' }
                }}
                tickFormatter={(value) => {
                  const num = coerceNumber(value, NaN);
                  return Number.isFinite(num) ? num.toFixed(1) : '0';
                }}
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
                  style: { textAnchor: 'middle', fontSize: '14px', fontWeight: '500', fill: '#dc3545' }
                }}
                tickFormatter={(value) => {
                  const num = coerceNumber(value, NaN);
                  return Number.isFinite(num) ? num.toFixed(2) : '0';
                }}
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

              {/* Cycling load bars - separate from running stack */}
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

              {/* Swimming load bars - separate from running stack */}
              {hasSwimmingData && (
                <Bar
                  yAxisId="miles"
                  dataKey="swimming_load"
                  name="Swimming Load (running equiv)"
                  fill="#e67e22"
                  barSize={chartDimensions.barSize}
                  opacity={selectedSports.includes('swimming') ? 0.7 : 0.3}
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

      {/* Coaching Link Section */}
      <div className={styles.chartContainer}>
        <div style={{
          padding: '2rem',
          textAlign: 'center',
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          borderRadius: '0.75rem',
          color: 'white',
          boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
        }}>
          <div style={{
            fontSize: '3rem',
            marginBottom: '1rem'
          }}>
            🧠
          </div>
          <h2 style={{
            fontSize: '1.5rem',
            fontWeight: '700',
            marginBottom: '0.75rem',
            color: 'white'
          }}>
            Your AI Training Coach
          </h2>
          <p style={{
            fontSize: '1rem',
            marginBottom: '1.5rem',
            opacity: 0.95,
            maxWidth: '600px',
            margin: '0 auto 1.5rem'
          }}>
            Get comprehensive coaching analysis including weekly strategy, training stage guidance,
            race preparation, and personalized AI recommendations based on your training patterns.
          </p>
          <button
            onClick={() => onNavigateToTab?.('coach')}
            style={{
              padding: '0.875rem 2rem',
              fontSize: '1rem',
              fontWeight: '600',
              backgroundColor: 'white',
              color: '#667eea',
              border: 'none',
              borderRadius: '0.5rem',
              cursor: 'pointer',
              boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
              transition: 'all 0.2s ease',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.5rem'
            }}
            onMouseOver={(e) => {
              e.currentTarget.style.transform = 'translateY(-2px)';
              e.currentTarget.style.boxShadow = '0 4px 8px rgba(0, 0, 0, 0.15)';
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.transform = 'translateY(0)';
              e.currentTarget.style.boxShadow = '0 2px 4px rgba(0, 0, 0, 0.1)';
            }}
          >
            <span>View Full Coaching Analysis</span>
            <span style={{ fontSize: '1.2rem' }}>→</span>
          </button>
        </div>
      </div>

    </div>
  );
};

export default TrainingLoadDashboard;