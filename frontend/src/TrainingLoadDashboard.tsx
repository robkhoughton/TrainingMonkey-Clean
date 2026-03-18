import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import {
  Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, ReferenceArea, ComposedChart, ReferenceLine, Bar
} from 'recharts';
import styles from './TrainingLoadDashboard.module.css';
import defaultTheme from './chartTheme';
import { useChartDimensions } from './useChartDimensions';
import CompactDashboardBanner from './CompactDashboardBanner';
import { usePagePerformanceMonitoring, useComponentPerformanceMonitoring } from './usePerformanceMonitoring';
import DailyStatusPopup from './DailyStatusPopup';
import JournalTeaserCard from './JournalTeaserCard';
import DashboardTour from './DashboardTour';

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
  // Backend-computed risk fields (user-specific thresholds from get_adjusted_thresholds())
  injuryRiskScore?: number;
  injuryRiskLabel?: string;
  acwrHighThreshold?: number;
  acwrUndertrainingThreshold?: number;
  divergenceWarnThreshold?: number;
  divergenceModerateThreshold?: number;
  dashboardConfig?: {
    chronic_period_days: number;
    decay_rate: number;
    is_active: boolean;
  };
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
  const [userToday, setUserToday] = useState<string | null>(null);
  const [dateRange, setDateRange] = useState('30');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [renderKey, setRenderKey] = useState(0);
  const [selectedSports, setSelectedSports] = useState(['running', 'cycling', 'swimming', 'rowing', 'backcountry_skiing', 'strength']);
  const [hasCyclingData, setHasCyclingData] = useState(false);
  const [hasSwimmingData, setHasSwimmingData] = useState(false);
  const [hasRowingData, setHasRowingData] = useState(false);
  const [hasBackcountrySkiingData, setHasBackcountrySkiingData] = useState(false);
  const [hasStrengthData, setHasStrengthData] = useState(false);
  const [showStatusPopup, setShowStatusPopup] = useState(false);
  const [tourStep, setTourStep] = useState(0);

  // FIXED: Proper frozen tooltip state management
  const [frozenTooltipData, setFrozenTooltipData] = useState<{
    payload: any[];
    label: string;
    coordinate: { x: number; y: number };
  } | null>(null);

  // Post-sync journal prompt state (Phase 6A)
  const [showJournalModal, setShowJournalModal] = useState(false);
  const [syncedActivityName, setSyncedActivityName] = useState('your workout');
  const [journalForm, setJournalForm] = useState<{
    energy_level: number | null;
    rpe_score: number | null;
    notes: string;
  }>({ energy_level: null, rpe_score: null, notes: '' });

  const handleSyncComplete = async () => {
    // Check if today's journal observations already exist before prompting
    try {
      const res = await fetch('/api/journal', { credentials: 'include' });
      const data = await res.json();
      if (data.success && data.data) {
        const todayEntry = data.data.find((e: any) => e.is_today);
        const hasActivity = todayEntry?.activity_summary?.activity_id != null;
        if (!hasActivity || todayEntry?.has_observations) {
          // No activity to journal, or already journaled — just reload
          window.location.reload();
          return;
        }
        if (todayEntry?.activity_summary?.name) {
          setSyncedActivityName(todayEntry.activity_summary.name);
        }
      }
    } catch {
      // On error, fall through and show modal anyway
    }
    setJournalForm({ energy_level: null, rpe_score: null, notes: '' });
    setShowJournalModal(true);
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

  // Custom tooltip component with click-to-pin functionality
  const CustomTooltip = ({ active, payload, label, coordinate }: any) => {
    // Use frozen data if available, otherwise active data
    const currentData = frozenTooltipData || (active ? { payload, label, coordinate } : null);

    if (!currentData || !currentData.payload || !currentData.payload.length) {
      return null;
    }

    const formattedDate = formatTooltipDate(currentData.label);
    const activityId = currentData.payload[0]?.payload?.activity_id;
    const frozen = !!frozenTooltipData;

    // Clamp position to viewport
    const TOOLTIP_WIDTH = 280;
    const TOOLTIP_HEIGHT_EST = 300;
    const rawLeft = currentData.coordinate ? currentData.coordinate.x + 20 : 0;
    const rawTop = currentData.coordinate ? currentData.coordinate.y - 100 : 0;
    const clampedLeft = Math.min(rawLeft, (typeof window !== 'undefined' ? window.innerWidth : 1440) - TOOLTIP_WIDTH - 16);
    const clampedTop = Math.min(Math.max(16, rawTop), (typeof window !== 'undefined' ? window.innerHeight : 900) - TOOLTIP_HEIGHT_EST - 16);

    const tooltipContent = (
      <div
        style={{
          backgroundColor: 'white',
          border: frozen ? '2px solid #1B2E4B' : '2px solid #3b82f6',
          borderRadius: '8px',
          padding: '0',
          boxShadow: frozen
            ? '0 8px 24px rgba(27, 46, 75, 0.25)'
            : '0 4px 12px rgba(59, 130, 246, 0.2)',
          width: `${TOOLTIP_WIDTH}px`,
          fontSize: '12px',
          fontFamily: 'Arial, sans-serif',
          position: frozen ? 'fixed' : 'relative',
          zIndex: 50000,
          pointerEvents: 'auto',
          cursor: 'default',
          left: frozen ? `${clampedLeft}px` : 'auto',
          top: frozen ? `${clampedTop}px` : 'auto',
          transition: 'border-color 0.15s, box-shadow 0.15s',
          overflow: 'hidden',
        }}
        onClick={(e) => {
          e.stopPropagation();
        }}
        onMouseEnter={(e) => {
          if (!frozen) {
            (e.currentTarget as HTMLDivElement).style.borderColor = '#1B2E4B';
            (e.currentTarget as HTMLDivElement).style.boxShadow = '0 6px 18px rgba(27, 46, 75, 0.2)';
          }
        }}
        onMouseLeave={(e) => {
          if (!frozen) {
            (e.currentTarget as HTMLDivElement).style.borderColor = '#3b82f6';
            (e.currentTarget as HTMLDivElement).style.boxShadow = '0 4px 12px rgba(59, 130, 246, 0.2)';
          }
        }}
      >
        {/* Header */}
        <div style={{
          background: frozen ? '#1B2E4B' : '#EBF5FF',
          padding: '8px 12px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}>
          <span style={{
            fontWeight: 'bold',
            fontSize: '13px',
            color: frozen ? 'white' : '#1B2E4B',
          }}>
            {formattedDate}
          </span>
          {frozen ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{
                fontSize: '10px',
                fontWeight: '700',
                letterSpacing: '0.06em',
                color: '#7D9CB8',
                textTransform: 'uppercase',
              }}>
                Pinned
              </span>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setFrozenTooltipData(null);
                }}
                style={{
                  background: 'rgba(255,255,255,0.15)',
                  color: 'white',
                  border: '1px solid rgba(255,255,255,0.3)',
                  borderRadius: '4px',
                  width: '20px',
                  height: '20px',
                  fontSize: '13px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: 'bold',
                  lineHeight: 1,
                  flexShrink: 0,
                }}
              >
                ×
              </button>
            </div>
          ) : null}
        </div>

        {/* Data rows */}
        <div style={{ padding: '10px 12px 8px' }}>
          {currentData.payload.map((entry: any, index: number) => {
            let displayName = entry.name;
            let displayValue = entry.value;

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
            } else if (entry.dataKey === 'running_distance') {
              displayName = 'Running Distance';
            } else if (entry.dataKey === 'running_elevation') {
              displayName = 'Running Elevation (mile equiv)';
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
                marginBottom: '4px',
              }}>
                <span style={{
                  color: entry.color,
                  fontWeight: '500',
                  marginRight: '8px',
                  fontSize: '11px',
                }}>
                  {displayName}:
                </span>
                <span style={{ fontWeight: 'bold', fontSize: '12px', color: '#1F2937' }}>
                  {(() => {
                    if (displayValue === null || displayValue === undefined) return 'N/A';
                    const digits = displayName.includes('ACWR') || displayName.includes('Divergence') ? 3 : 1;
                    const numericValue = coerceNumber(displayValue, NaN);
                    if (Number.isFinite(numericValue)) return numericValue.toFixed(digits);
                    return typeof displayValue === 'string' ? displayValue : 'N/A';
                  })()}
                </span>
              </div>
            );
          })}
        </div>

        {/* Strava link */}
        {activityId && activityId !== 0 && (
          <div style={{
            borderTop: '1px solid #e5e7eb',
            padding: '8px 12px',
            textAlign: 'center',
          }}>
            <a
              href={`https://www.strava.com/activities/${activityId}`}
              target="_blank"
              rel="noopener noreferrer"
              onClick={(e) => e.stopPropagation()}
              style={{
                display: 'inline-block',
                padding: '6px 16px',
                backgroundColor: '#fc4c02',
                color: 'white',
                textDecoration: 'none',
                borderRadius: '4px',
                fontSize: '12px',
                fontWeight: '600',
                transition: 'background-color 0.15s, transform 0.15s',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = '#e73c00';
                e.currentTarget.style.transform = 'scale(1.04)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = '#fc4c02';
                e.currentTarget.style.transform = 'scale(1)';
              }}
            >
              View on Strava
            </a>
          </div>
        )}

        {/* Click-to-pin affordance — only shown in hover state */}
        {!frozen && (
          <div style={{
            background: '#EBF5FF',
            borderTop: '1px solid #dbeafe',
            padding: '5px 12px',
            textAlign: 'center',
            fontSize: '11px',
            color: '#3b82f6',
            fontWeight: '500',
            letterSpacing: '0.01em',
          }}>
            Click chart to pin
          </div>
        )}
      </div>
    );

    // When frozen, portal to document.body so Recharts' wrapper hiding can't affect it
    if (frozenTooltipData) {
      return createPortal(tooltipContent, document.body);
    }
    return tooltipContent;
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

  // Filter data based on date range, anchored to user_today from the backend.
  // Using the last activity date as the anchor would silently shift the window
  // if the user hasn't synced recently.
  const filteredData = () => {
    if (data.length === 0) return [];

    const days = parseInt(dateRange, 10);
    // Prefer server-authoritative today; fall back to last activity date only if unavailable
    const allDates = data.map(item => item.date).sort();
    const anchorDate = userToday ?? allDates[allDates.length - 1];

    const anchorDateObj = new Date(`${anchorDate}T12:00:00Z`);
    const cutoffDateObj = new Date(anchorDateObj);
    cutoffDateObj.setDate(cutoffDateObj.getDate() - days + 1);

    const cutoffDate = cutoffDateObj.toISOString().split('T')[0];

    return data.filter(item => {
      return item.date >= cutoffDate && item.date <= anchorDate;
    });
  };

  // COMMENTED OUT: Dead code - LLM recommendations are fetched via /api/journal instead
  // These functions were never wired to UI. Delete after verifying Journal page works.
  /*
  const fetchRecommendations = async () => {
    console.log("fetchRecommendations called");
    try {
      setIsLoadingRecommendation(true);
      const response = await fetch('/api/llm-recommendations');
      if (!response.ok) {
        throw new Error(`API responded with status ${response.status}`);
      }
      const result = await response.json();
      if (result.recommendation) {
        setRecommendation(result.recommendation);
      } else {
        setRecommendation(null);
      }
    } catch (e) {
      console.error("Failed to fetch recommendations:", e);
      setRecommendation(null);
    } finally {
      setIsLoadingRecommendation(false);
    }
  };

  const fetchJournalStatus = async () => {
    try {
      const response = await fetch('/api/journal-status');
      if (!response.ok) return;
      const result = await response.json();
      if (result.success && result.status) {
        setJournalStatus(result.status);
      }
    } catch (e) {
      console.error("Failed to fetch journal status:", e);
    }
  };

  const generateNewRecommendation = async () => {
    try {
      setIsLoadingRecommendation(true);
      const response = await fetch('/api/llm-recommendations/generate', { method: 'POST' });
      if (!response.ok) {
        throw new Error(`Generation failed: ${response.status}`);
      }
      await fetchRecommendations();
      await fetchJournalStatus();
    } catch (e) {
      console.error("Failed to generate recommendation:", e);
    } finally {
      setIsLoadingRecommendation(false);
    }
  };
  */

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

            // FIXED: Always use backend-calculated divergence, never recalculate on frontend
            // This ensures consistency with backend's canonical UnifiedMetricsService calculation
            const normalizedDivergence = coerceNumber(row.normalized_divergence, 0);

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
          if (result.has_rowing_data !== undefined) {
            setHasRowingData(result.has_rowing_data);
          }
          if (result.has_backcountry_skiing_data !== undefined) {
            setHasBackcountrySkiingData(result.has_backcountry_skiing_data);
          }
          if (result.has_strength_data !== undefined) {
            setHasStrengthData(result.has_strength_data);
          }

          // Use backend current_metrics: decay-adjusted values as of today, not just the last
          // array entry (which may be days stale if the user hasn't trained recently).
          const cm = result.current_metrics;
          setMetrics(prev => ({
            ...prev,
            externalAcwr: coerceNumber(cm?.external_acwr, 0),
            internalAcwr: coerceNumber(cm?.internal_acwr, 0),
            sevenDayAvgLoad: coerceNumber(cm?.seven_day_avg_load, 0),
            sevenDayAvgTrimp: coerceNumber(cm?.seven_day_avg_trimp, 0),
            daysSinceRest: typeof result.days_since_rest === 'number' ? result.days_since_rest : 0,
            normalizedDivergence: coerceNumber(cm?.normalized_divergence, 0),
            injuryRiskScore: typeof cm?.injury_risk_score === 'number' ? cm.injury_risk_score : undefined,
            injuryRiskLabel: typeof cm?.injury_risk_label === 'string' ? cm.injury_risk_label : undefined,
            acwrHighThreshold: typeof cm?.acwr_high_threshold === 'number' ? cm.acwr_high_threshold : undefined,
            acwrUndertrainingThreshold: typeof cm?.acwr_undertraining_threshold === 'number' ? cm.acwr_undertraining_threshold : undefined,
            divergenceWarnThreshold: typeof cm?.divergence_warn_threshold === 'number' ? cm.divergence_warn_threshold : undefined,
            divergenceModerateThreshold: typeof cm?.divergence_moderate_threshold === 'number' ? cm.divergence_moderate_threshold : undefined,
          }));

          // Store user_today so filteredData() anchors to the real current date, not the last activity date
          if (typeof result.user_today === 'string') {
            setUserToday(result.user_today);
          }

          console.log('Metrics from current_metrics:', {
            externalAcwr: cm?.external_acwr,
            internalAcwr: cm?.internal_acwr,
            daysSinceRest: result.days_since_rest,
            normalizedDivergence: cm?.normalized_divergence,
            injuryRiskScore: cm?.injury_risk_score,
            injuryRiskLabel: cm?.injury_risk_label,
          });

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
      // COMMENTED OUT: Dead code - see comment above
      // fetchRecommendations();
      // fetchJournalStatus();
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

  // Fetch dashboard configuration separately for display purposes only
  // This shows users what calculation method is being used (custom vs default)
  // Note: ACWR values come from database (pre-calculated), this is just for explanatory text
  useEffect(() => {
    const fetchDashboardConfig = async () => {
      try {
        const response = await fetch('/api/user/dashboard-config');
        if (!response.ok) return; // Gracefully handle if endpoint unavailable

        const result = await response.json();
        if (result.success && result.config) {
          setMetrics(prev => ({
            ...prev,
            dashboardConfig: result.config
          }));
          console.log('Dashboard config loaded:', result.config);
        }
      } catch (e) {
        console.error("Failed to fetch dashboard config:", e);
        // Fail silently - will show default explanation text
      }
    };

    fetchDashboardConfig();
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

  // Check if should show tour or pop-up (after metrics are loaded, with delay)
  useEffect(() => {
    const checkShowTourOrPopup = async () => {
      const today = new Date().toDateString();
      let tourCompleted = localStorage.getItem('dashboardTour_completed');
      const lastShown = localStorage.getItem('statusPopup_lastShown');
      const visitedJournalToday = localStorage.getItem('journal_visited_' + today);

      // For local deployment: Check journal count - if >= 3, disable tour
      try {
        const journalResponse = await fetch('/api/journal-entries-count');
        if (journalResponse.ok) {
          const journalData = await journalResponse.json();
          if (journalData.success && journalData.count_last_week >= 3) {
            // Journal count above threshold - disable tour for local deployment
            localStorage.setItem('dashboardTour_completed', 'true');
            tourCompleted = 'true';
            console.log('Tour disabled: Journal count >= 3 (local deployment mode)');
          }
        }
      } catch (error) {
        console.error('Error checking journal count:', error);
        // Continue with normal tour logic if check fails
      }

      console.log('Tour check:', {
        tourCompleted,
        externalAcwr: metrics.externalAcwr,
        lastShown,
        visitedJournalToday
      });

      // If tour not completed, start tour after 3 seconds
      if (!tourCompleted && metrics.externalAcwr > 0) {
        console.log('Starting tour in 3 seconds...');
        setTimeout(() => {
          console.log('Setting tour step to 1');
          setTourStep(1);
        }, 3000);
      }
      // Otherwise, show popup if appropriate
      else if (lastShown !== today && !visitedJournalToday && metrics.externalAcwr > 0) {
        console.log('Starting popup in 5 seconds...');
        setTimeout(() => {
          setShowStatusPopup(true);
        }, 5000);
      }
    };

    // Only check after data is loaded
    if (!isLoading && metrics.externalAcwr > 0) {
      checkShowTourOrPopup();
    }
  }, [isLoading, metrics.externalAcwr]);

  // Handle navigation to Journal
  const handleNavigateToJournal = () => {
    localStorage.setItem('statusPopup_lastShown', new Date().toDateString());
    setShowStatusPopup(false);
    onNavigateToTab?.('journal');
  };

  // Handle dismiss popup
  const handleDismissPopup = () => {
    localStorage.setItem('statusPopup_lastShown', new Date().toDateString());
    setShowStatusPopup(false);
    // Badge will show on Journal tab (handled by App.tsx)
  };

  // Handle tour navigation
  const handleTourNext = () => {
    setTourStep(tourStep + 1);
  };

  const handleTourSkip = () => {
    localStorage.setItem('dashboardTour_completed', 'true');
    setTourStep(0);
  };

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

  // Post-sync journal modal handlers
  const handleJournalSkip = () => {
    setShowJournalModal(false);
    window.location.reload();
  };

  const handleJournalSave = async () => {
    const today = new Date().toISOString().split('T')[0];
    try {
      const response = await fetch('/api/journal', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          date: today,
          energy_level: journalForm.energy_level,
          rpe_score: journalForm.rpe_score,
          notes: journalForm.notes || null,
        }),
      });
      if (!response.ok) {
        console.error('Journal save failed:', await response.text());
      }
    } catch (err) {
      console.error('Journal save error:', err);
    }
    setShowJournalModal(false);
    window.location.reload();
  };

  // Main dashboard render
  return (
    <div className={styles.container}>
      {/* Post-Sync Journal Prompt Modal (Phase 6A) */}
      {showJournalModal && (
        <div style={{
          position: 'fixed',
          inset: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.65)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
        }}>
          <div style={{
            backgroundColor: '#1B2E4B',
            borderRadius: '10px',
            padding: '28px 28px 24px',
            width: '100%',
            maxWidth: '460px',
            boxShadow: '0 24px 64px rgba(0,0,0,0.55), 0 0 0 1px rgba(125,156,184,0.15)',
          }}>
            {/* Header */}
            <div style={{ marginBottom: '22px' }}>
              <h2 style={{
                margin: '0 0 6px',
                fontFamily: '"DM Serif Display", Georgia, serif',
                fontSize: '1.625rem',
                fontWeight: '400',
                color: '#ffffff',
                lineHeight: '1.2',
                letterSpacing: '-0.01em',
              }}>
                What your watch can't tell us
              </h2>
              {syncedActivityName && syncedActivityName !== 'your workout' && (
                <p style={{
                  margin: 0,
                  fontSize: '0.8rem',
                  color: '#7D9CB8',
                  fontStyle: 'italic',
                  letterSpacing: '0.02em',
                }}>
                  {syncedActivityName}
                </p>
              )}
              <div style={{
                marginTop: '16px',
                height: '1px',
                background: 'linear-gradient(90deg, rgba(125,156,184,0.5) 0%, rgba(27,46,75,0) 100%)',
              }} />
            </div>

            {/* Energy level */}
            <div style={{ marginBottom: '14px' }}>
              <label style={{
                display: 'block',
                fontSize: '0.7rem',
                fontWeight: '700',
                color: '#7D9CB8',
                marginBottom: '6px',
                textTransform: 'uppercase',
                letterSpacing: '0.1em',
              }}>
                How did you feel going in?
              </label>
              <select
                value={journalForm.energy_level ?? ''}
                onChange={(e) => setJournalForm(f => ({ ...f, energy_level: e.target.value ? Number(e.target.value) : null }))}
                style={{
                  width: '100%',
                  padding: '8px 10px',
                  border: '1px solid rgba(125,156,184,0.3)',
                  borderRadius: '6px',
                  fontSize: '0.875rem',
                  color: '#E6F0FF',
                  backgroundColor: 'rgba(255,255,255,0.06)',
                  outline: 'none',
                  cursor: 'pointer',
                }}
              >
                <option value="" style={{ backgroundColor: '#1B2E4B' }}>Select...</option>
                <option value="1" style={{ backgroundColor: '#1B2E4B' }}>1 — Barely got out of bed</option>
                <option value="2" style={{ backgroundColor: '#1B2E4B' }}>2 — Low energy</option>
                <option value="3" style={{ backgroundColor: '#1B2E4B' }}>3 — Normal</option>
                <option value="4" style={{ backgroundColor: '#1B2E4B' }}>4 — High energy</option>
                <option value="5" style={{ backgroundColor: '#1B2E4B' }}>5 — Fired up</option>
              </select>
            </div>

            {/* RPE */}
            <div style={{ marginBottom: '14px' }}>
              <label style={{
                display: 'block',
                fontSize: '0.7rem',
                fontWeight: '700',
                color: '#7D9CB8',
                marginBottom: '6px',
                textTransform: 'uppercase',
                letterSpacing: '0.1em',
              }}>
                How hard did it feel? (RPE 1–10)
              </label>
              <select
                value={journalForm.rpe_score ?? ''}
                onChange={(e) => setJournalForm(f => ({ ...f, rpe_score: e.target.value ? Number(e.target.value) : null }))}
                style={{
                  width: '100%',
                  padding: '8px 10px',
                  border: '1px solid rgba(125,156,184,0.3)',
                  borderRadius: '6px',
                  fontSize: '0.875rem',
                  color: '#E6F0FF',
                  backgroundColor: 'rgba(255,255,255,0.06)',
                  outline: 'none',
                  cursor: 'pointer',
                }}
              >
                <option value="" style={{ backgroundColor: '#1B2E4B' }}>Select...</option>
                {[1,2,3,4,5,6,7,8,9,10].map(n => (
                  <option key={n} value={n} style={{ backgroundColor: '#1B2E4B' }}>{n}</option>
                ))}
              </select>
            </div>

            {/* Notes */}
            <div style={{ marginBottom: '22px' }}>
              <label style={{
                display: 'block',
                fontSize: '0.7rem',
                fontWeight: '700',
                color: '#7D9CB8',
                marginBottom: '6px',
                textTransform: 'uppercase',
                letterSpacing: '0.1em',
              }}>
                Notes
              </label>
              <textarea
                value={journalForm.notes}
                onChange={(e) => setJournalForm(f => ({ ...f, notes: e.target.value }))}
                placeholder="Anything to add?"
                rows={3}
                style={{
                  width: '100%',
                  padding: '8px 10px',
                  border: '1px solid rgba(125,156,184,0.3)',
                  borderRadius: '6px',
                  fontSize: '0.875rem',
                  color: '#E6F0FF',
                  backgroundColor: 'rgba(255,255,255,0.06)',
                  resize: 'vertical',
                  boxSizing: 'border-box',
                  outline: 'none',
                }}
              />
            </div>

            {/* Buttons */}
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', alignItems: 'center' }}>
              <button
                onClick={handleJournalSkip}
                style={{
                  padding: '8px 18px',
                  border: '1px solid rgba(125,156,184,0.25)',
                  borderRadius: '6px',
                  backgroundColor: 'transparent',
                  color: 'rgba(125,156,184,0.7)',
                  fontSize: '0.8rem',
                  fontWeight: '600',
                  cursor: 'pointer',
                  letterSpacing: '0.02em',
                }}
              >
                Skip
              </button>
              <button
                onClick={handleJournalSave}
                style={{
                  padding: '9px 22px',
                  border: 'none',
                  borderRadius: '6px',
                  backgroundColor: '#3b82f6',
                  color: 'white',
                  fontSize: '0.875rem',
                  fontWeight: '700',
                  cursor: 'pointer',
                  letterSpacing: '0.02em',
                }}
              >
                Save &amp; Continue
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Dashboard Tour (for new users) */}
      <DashboardTour
        step={tourStep}
        onNext={handleTourNext}
        onSkip={handleTourSkip}
        metrics={metrics}
        onNavigateToJournal={() => onNavigateToTab?.('journal')}
      />

      {/* Daily Status Pop-up (conditional) */}
      {showStatusPopup && (
        <DailyStatusPopup
          metrics={metrics}
          onNavigateToJournal={handleNavigateToJournal}
          onDismiss={handleDismissPopup}
        />
      )}

      {/* Journal Teaser Card (always visible at top) */}
      <JournalTeaserCard
        metrics={metrics}
        onNavigateToJournal={() => onNavigateToTab?.('journal')}
      />

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
          {(hasCyclingData || hasSwimmingData || hasRowingData || hasBackcountrySkiingData || hasStrengthData) && (
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
                {hasRowingData && (
                  <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={selectedSports.includes('rowing')}
                      onChange={() => setSelectedSports(prev =>
                        prev.includes('rowing') ? prev.filter(s => s !== 'rowing') : [...prev, 'rowing']
                      )}
                    />
                    <span style={{ color: '#9b59b6' }}>Rowing</span>
                  </label>
                )}
                {hasBackcountrySkiingData && (
                  <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={selectedSports.includes('backcountry_skiing')}
                      onChange={() => setSelectedSports(prev =>
                        prev.includes('backcountry_skiing') ? prev.filter(s => s !== 'backcountry_skiing') : [...prev, 'backcountry_skiing']
                      )}
                    />
                    <span style={{ color: '#16a085' }}>Backcountry Skiing</span>
                  </label>
                )}
                {hasStrengthData && (
                  <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={selectedSports.includes('strength')}
                      onChange={() => setSelectedSports(prev =>
                        prev.includes('strength') ? prev.filter(s => s !== 'strength') : [...prev, 'strength']
                      )}
                    />
                    <span style={{ color: '#e91e63' }}>Strength/Yoga</span>
                  </label>
                )}
              </div>
            </div>
          )}
        </div>

      {/* Overtraining Risk Over Time Chart */}
      <div id="overtraining-risk-chart" className={styles.chartContainer}>
        <h2 className={styles.chartTitle}>Overtraining Risk</h2>
        <div className={styles.chartWrapper} style={{ width: chartDimensions.width, height: chartDimensions.height }}>
          <ResponsiveContainer width="100%" height="100%" key={`overtraining-risk-${renderKey}`}>
            <ComposedChart
              data={filtered}
              margin={{ top: 5, right: 50, left: 20, bottom: 5 }}
              onClick={(data: any, event: any) => {
                if (data && data.activePayload && data.activePayload.length && !frozenTooltipData) {
                  setFrozenTooltipData({
                    payload: data.activePayload,
                    label: data.activeLabel,
                    coordinate: data.activeCoordinate,
                  });
                  if (event) event.stopPropagation();
                }
              }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="date"
                interval={chartDimensions.majorTickInterval}
                tickFormatter={formatXAxis}
                padding={{ left: 10, right: 10 }}
              />
              <YAxis
                yAxisId={0}
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
                domain={[0.3, -0.45]}
                reversed={false}
                allowDataOverflow={true}
                ticks={[-0.45, -0.3, -0.15, 0, 0.15, 0.3]}
                label={{
                  value: 'Normalized Divergence',
                  angle: 90,
                  position: 'insideRight',
                  style: { textAnchor: 'middle', fontSize: '14px', fontWeight: '500', fill: '#dc3545' }
                }}
                tickFormatter={(value) => {
                  const num = coerceNumber(value, NaN);
                  if (!Number.isFinite(num)) return '0';
                  // Special case for zero - just show "0"
                  if (num === 0) return '0';
                  // Add + sign for positive values to emphasize direction
                  // Make extreme values bold to show direction
                  const formatted = num > 0 ? `+${num.toFixed(2)}` : num.toFixed(2);
                  return formatted;
                }}
                tick={(props) => {
                  const { x, y, payload } = props;
                  const isExtreme = Math.abs(payload.value) === 0.3 || Math.abs(payload.value) === 0.45;
                  const isZero = payload.value === 0;
                  return (
                    <text
                      x={x}
                      y={y}
                      textAnchor="start"
                      fill="#666"
                      fontSize={isZero ? 12 : 11}
                      fontWeight={isExtreme || isZero ? 'bold' : 'normal'}
                      dx={5}
                    >
                      {payload.value === 0 ? '0' :
                       payload.value > 0 ? `+${payload.value.toFixed(2)}` :
                       payload.value.toFixed(2)}
                    </text>
                  );
                }}
                width={65}
              />
              <Tooltip
                content={<CustomTooltip />}
                cursor={{ strokeDasharray: '3 3' }}
                wrapperStyle={{ pointerEvents: 'auto' }}
              />
              <Legend />

              {/* Risk zones — boundaries from user-specific thresholds (get_adjusted_thresholds()) */}
              <ReferenceArea
                yAxisId={0}
                y1={0}
                y2={metrics.acwrUndertrainingThreshold ?? 0.8}
                fill="rgba(40, 167, 69, 0.15)"
                stroke="rgba(40, 167, 69, 0.3)"
                strokeWidth={1}
                label={{ value: "Low Risk", position: "insideTopLeft", fontSize: 10, fill: "green" }}
              />
              <ReferenceArea
                yAxisId={0}
                y1={metrics.acwrUndertrainingThreshold ?? 0.8}
                y2={metrics.acwrHighThreshold ?? 1.3}
                fill="rgba(255, 193, 7, 0.2)"
                stroke="rgba(255, 193, 7, 0.3)"
                strokeWidth={1}
                label={{ value: "Balanced", position: "insideTopLeft", fontSize: 10, fill: "#b8860b" }}
              />
              <ReferenceArea
                yAxisId={0}
                y1={metrics.acwrHighThreshold ?? 1.3}
                y2={(metrics.acwrHighThreshold ?? 1.3) + 0.2}
                fill="rgba(255, 87, 34, 0.25)"
                stroke="rgba(255, 87, 34, 0.3)"
                strokeWidth={1}
                label={{ value: "Moderate Risk", position: "insideTopLeft", fontSize: 10, fill: "#ff5722" }}
              />
              <ReferenceArea
                yAxisId={0}
                y1={(metrics.acwrHighThreshold ?? 1.3) + 0.2}
                y2={2.5}
                fill="rgba(199, 21, 133, 0.25)"
                stroke="rgba(199, 21, 133, 0.3)"
                strokeWidth={1}
                label={{ value: "High Risk", position: "insideTopLeft", fontSize: 10, fill: "#c71585" }}
              />

              {/* Internal Load (TRIMP) Line */}
              <Line
                yAxisId={0}
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
                yAxisId={0}
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

              {/* Prominent direction indicators for secondary axis */}
              <ReferenceLine
                yAxisId="divergence"
                y={-0.45}
                stroke="transparent"
                label={{
                  value: "−",
                  position: "insideTopRight",
                  fill: "#dc3545",
                  fontSize: 28,
                  fontWeight: "bold",
                  offset: 10
                }}
              />
              <ReferenceLine
                yAxisId="divergence"
                y={0.3}
                stroke="transparent"
                label={{
                  value: "+",
                  position: "insideBottomRight",
                  fill: "#28a745",
                  fontSize: 28,
                  fontWeight: "bold",
                  offset: 10
                }}
              />
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
        <h2 className={styles.chartTitle}>Internal Load</h2>
        <div className={styles.chartWrapper} style={{ width: chartDimensions.width, height: chartDimensions.height }}>
          <ResponsiveContainer width="100%" height="100%" key={`internal-load-${renderKey}`}>
            <ComposedChart
              data={filtered}
              margin={{ top: 5, right: 40, left: 20, bottom: 5 }}
              onClick={(data: any, event: any) => {
                if (data && data.activePayload && data.activePayload.length && !frozenTooltipData) {
                  setFrozenTooltipData({
                    payload: data.activePayload,
                    label: data.activeLabel,
                    coordinate: data.activeCoordinate,
                  });
                  if (event) event.stopPropagation();
                }
              }}
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
                opacity={1.0}
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
        <h2 className={styles.chartTitle}>External Work</h2>
        <div className={styles.chartWrapper} style={{ width: chartDimensions.width, height: chartDimensions.height }}>
          <ResponsiveContainer width="100%" height="100%" key={`external-load-${renderKey}`}>
            <ComposedChart
              data={filtered}
              margin={{ top: 5, right: 40, left: 20, bottom: 5 }}
              onClick={(data: any, event: any) => {
                if (data && data.activePayload && data.activePayload.length && !frozenTooltipData) {
                  setFrozenTooltipData({
                    payload: data.activePayload,
                    label: data.activeLabel,
                    coordinate: data.activeCoordinate,
                  });
                  if (event) event.stopPropagation();
                }
              }}
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

              {/* Running Distance - stacked with all other sports */}
              <Bar
                yAxisId="miles"
                dataKey="running_distance"
                name="Running"
                fill={colors.primary}
                barSize={chartDimensions.barSize}
                opacity={selectedSports.includes('running') ? 1.0 : 0.5}
                stackId="external"
                isAnimationActive={false}
              />

              {/* Running Elevation - stacked with all other sports */}
              <Bar
                yAxisId="miles"
                dataKey="running_elevation"
                name="Elevation"
                fill={colors.secondary}
                barSize={chartDimensions.barSize}
                opacity={selectedSports.includes('running') ? 1.0 : 0.5}
                stackId="external"
                isAnimationActive={false}
              />

              {/* Cycling load bars - stacked with all other sports */}
              {hasCyclingData && (
                <Bar
                  yAxisId="miles"
                  dataKey="cycling_load"
                  name="Cycling"
                  fill="#3498db"
                  barSize={chartDimensions.barSize}
                  opacity={selectedSports.includes('cycling') ? 1.0 : 0.5}
                  stackId="external"
                  isAnimationActive={false}
                />
              )}

              {/* Swimming load bars - stacked with all other sports */}
              {hasSwimmingData && (
                <Bar
                  yAxisId="miles"
                  dataKey="swimming_load"
                  name="Swimming Load (running equiv)"
                  fill="#e67e22"
                  barSize={chartDimensions.barSize}
                  opacity={selectedSports.includes('swimming') ? 1.0 : 0.5}
                  stackId="external"
                  isAnimationActive={false}
                />
              )}

              {/* Rowing load bars - stacked with all other sports */}
              {hasRowingData && (
                <Bar
                  yAxisId="miles"
                  dataKey="rowing_load"
                  name="Rowing"
                  fill="#9b59b6"
                  barSize={chartDimensions.barSize}
                  opacity={selectedSports.includes('rowing') ? 1.0 : 0.5}
                  stackId="external"
                  isAnimationActive={false}
                />
              )}

              {/* Backcountry skiing load bars - stacked with all other sports */}
              {hasBackcountrySkiingData && (
                <Bar
                  yAxisId="miles"
                  dataKey="backcountry_skiing_load"
                  name="Backcountry Skiing Load (running equiv)"
                  fill="#16a085"
                  barSize={chartDimensions.barSize}
                  opacity={selectedSports.includes('backcountry_skiing') ? 1.0 : 0.5}
                  stackId="external"
                  isAnimationActive={false}
                />
              )}

              {/* Strength load bars (yoga, weight training, etc.) - stacked with all other sports */}
              {hasStrengthData && (
                <Bar
                  yAxisId="miles"
                  dataKey="strength_load"
                  name="Strength/Yoga"
                  fill="#e91e63"
                  barSize={chartDimensions.barSize}
                  opacity={selectedSports.includes('strength') ? 1.0 : 0.5}
                  stackId="external"
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
        {/* Custom Legend: Bars on first line, Lines on second line */}
        <div style={{ marginTop: '10px', marginBottom: '10px' }}>
          {/* Bar legend items - first line */}
          <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', flexWrap: 'wrap', gap: '16px', marginBottom: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <div style={{ width: '16px', height: '12px', backgroundColor: colors.primary, opacity: selectedSports.includes('running') ? 1.0 : 0.5 }}></div>
              <span style={{ fontSize: '12px' }}>Running</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <div style={{ width: '16px', height: '12px', backgroundColor: colors.secondary, opacity: selectedSports.includes('running') ? 1.0 : 0.5 }}></div>
              <span style={{ fontSize: '12px' }}>Elevation</span>
            </div>
            {hasCyclingData && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <div style={{ width: '16px', height: '12px', backgroundColor: '#3498db', opacity: selectedSports.includes('cycling') ? 1.0 : 0.5 }}></div>
                <span style={{ fontSize: '12px' }}>Cycling</span>
              </div>
            )}
            {hasSwimmingData && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <div style={{ width: '16px', height: '12px', backgroundColor: '#e67e22', opacity: selectedSports.includes('swimming') ? 1.0 : 0.5 }}></div>
                <span style={{ fontSize: '12px' }}>Swimming</span>
              </div>
            )}
            {hasRowingData && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <div style={{ width: '16px', height: '12px', backgroundColor: '#9b59b6', opacity: selectedSports.includes('rowing') ? 1.0 : 0.5 }}></div>
                <span style={{ fontSize: '12px' }}>Rowing</span>
              </div>
            )}
            {hasBackcountrySkiingData && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <div style={{ width: '16px', height: '12px', backgroundColor: '#16a085', opacity: selectedSports.includes('backcountry_skiing') ? 1.0 : 0.5 }}></div>
                <span style={{ fontSize: '12px' }}>Backcountry Skiing</span>
              </div>
            )}
            {hasStrengthData && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <div style={{ width: '16px', height: '12px', backgroundColor: '#e91e63', opacity: selectedSports.includes('strength') ? 1.0 : 0.5 }}></div>
                <span style={{ fontSize: '12px' }}>Strength/Yoga</span>
              </div>
            )}
          </div>
          {/* Line legend items - second line */}
          <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <svg width="24" height="4" style={{ overflow: 'visible' }}>
                <line x1="0" y1="2" x2="24" y2="2" stroke={colors.dark} strokeWidth="4" strokeDasharray="8 4" />
              </svg>
              <span style={{ fontSize: '12px' }}>7-Day Avg (mile equiv)</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <svg width="24" height="4" style={{ overflow: 'visible' }}>
                <line x1="0" y1="2" x2="24" y2="2" stroke={colors.warning} strokeWidth="2" />
                <circle cx="12" cy="2" r="3" fill={colors.warning} />
              </svg>
              <span style={{ fontSize: '12px' }}>Elevation Gain (ft)</span>
            </div>
          </div>
        </div>
        <p className={styles.chartNote}>
          External Work: stacked bar shows total daily load from all sports (running-mile equivalents), with 7-day moving average. Each color represents a different sport.
        </p>
      </div>

    </div>
  );
};

export default TrainingLoadDashboard;