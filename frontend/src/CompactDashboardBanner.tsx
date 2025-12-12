import React, { useState, useEffect } from 'react';
import ContextualTooltip from './ContextualTooltip';
import MetricTooltip from './MetricTooltip';

// TypeScript interfaces for proper type safety
interface CompactDashboardBannerProps {
  onSyncComplete: () => void;
  metrics: {
    externalAcwr: number;
    internalAcwr: number;
    sevenDayAvgLoad: number;
    sevenDayAvgTrimp: number;
    daysSinceRest: number;
    normalizedDivergence: number;
  };
}

interface SyncResponse {
  success: boolean;
  error?: string;
  message?: string;
  activities_processed?: number;
  date_range?: string;
}

// High-Precision Dual ACWR Gauge Component
interface DualNeedleStrainGaugeProps {
  externalValue: number;
  internalValue: number;
  max: number;
  size?: number;
}

const DualNeedleStrainGauge: React.FC<DualNeedleStrainGaugeProps> = ({
  externalValue,
  internalValue,
  max = 2.0,
  size = 140
}) => {
  // Calculate angles (gauge spans 180 degrees, horizontal orientation)
  const clampedExternalValue = Math.max(0, Math.min(max, externalValue));
  const clampedInternalValue = Math.max(0, Math.min(max, internalValue));
  const externalAngle = (clampedExternalValue / max) * 180;
  const internalAngle = (clampedInternalValue / max) * 180;

  const radius = 45; // Optimized radius
  const strokeWidth = 3; // Thin, precise arc segments (3px)
  const centerX = size / 2;
  const centerY = size / 2 + 5; // Slight vertical adjustment

  // Needle positions (9 o'clock to 3 o'clock orientation)
  const externalNeedleAngle = (externalAngle + 180) * (Math.PI / 180);
  const internalNeedleAngle = (internalAngle + 180) * (Math.PI / 180);
  const needleLength = radius - 2;

  const externalNeedleX = centerX + needleLength * Math.cos(externalNeedleAngle);
  const externalNeedleY = centerY + needleLength * Math.sin(externalNeedleAngle);
  const internalNeedleX = centerX + needleLength * Math.cos(internalNeedleAngle);
  const internalNeedleY = centerY + needleLength * Math.sin(internalNeedleAngle);

  // Create arc path helper
  const createArc = (startAngle: number, endAngle: number, r: number = radius) => {
    if (isNaN(startAngle) || isNaN(endAngle)) return 'M 0 0';
    const startRad = (startAngle + 180) * (Math.PI / 180);
    const endRad = (endAngle + 180) * (Math.PI / 180);
    const x1 = centerX + r * Math.cos(startRad);
    const y1 = centerY + r * Math.sin(startRad);
    const x2 = centerX + r * Math.cos(endRad);
    const y2 = centerY + r * Math.sin(endRad);
    if (isNaN(x1) || isNaN(y1) || isNaN(x2) || isNaN(y2)) return 'M 0 0';
    const largeArcFlag = (endAngle - startAngle) > 180 ? 1 : 0;
    return `M ${x1.toFixed(2)} ${y1.toFixed(2)} A ${r} ${r} 0 ${largeArcFlag} 1 ${x2.toFixed(2)} ${y2.toFixed(2)}`;
  };

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      minWidth: size,
      position: 'relative',
      fontFamily: '"Roboto Mono", "JetBrains Mono", "Courier New", monospace'
    }}>
      <div style={{
        position: 'relative',
        width: size,
        height: size * 0.6,
        marginTop: '8px',
        marginBottom: '2px'
      }}>
        <svg width={size} height={size * 0.6} viewBox={`0 0 ${size} ${size * 0.6}`}>
          <defs>
            {/* Sharp gradients for depth */}
            <linearGradient id="trackGradient" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#e8e8e8" />
              <stop offset="100%" stopColor="#d0d0d0" />
            </linearGradient>
            <linearGradient id="blueZone" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#5dade2" stopOpacity="0.4" />
              <stop offset="100%" stopColor="#2874a6" stopOpacity="0.4" />
            </linearGradient>
            <linearGradient id="greenZone" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#58d68d" stopOpacity="0.5" />
              <stop offset="100%" stopColor="#229954" stopOpacity="0.5" />
            </linearGradient>
            <linearGradient id="orangeZone" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#f5b041" stopOpacity="0.5" />
              <stop offset="100%" stopColor="#d68910" stopOpacity="0.5" />
            </linearGradient>
            <linearGradient id="redZone" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#ec7063" stopOpacity="0.5" />
              <stop offset="100%" stopColor="#c0392b" stopOpacity="0.5" />
            </linearGradient>
          </defs>

          {/* Clean base track */}
          <path d={createArc(0, 180)} fill="none" stroke="url(#trackGradient)" strokeWidth={strokeWidth + 1} opacity={0.3} />

          {/* Color-coded risk zones */}
          <path d={createArc(0, 72)} fill="none" stroke="url(#blueZone)" strokeWidth={strokeWidth} />
          <path d={createArc(72, 117)} fill="none" stroke="url(#greenZone)" strokeWidth={strokeWidth} />
          <path d={createArc(117, 135)} fill="none" stroke="url(#orangeZone)" strokeWidth={strokeWidth} />
          <path d={createArc(135, 180)} fill="none" stroke="url(#redZone)" strokeWidth={strokeWidth} />

          {/* Ultra-precise tick marks - every 0.1 units */}
          {Array.from({ length: 21 }, (_, i) => {
            const value = i * 0.1;
            const angle = (value / max) * 180;
            const tickAngle = (angle + 180) * (Math.PI / 180);
            const isMajor = i % 2 === 0; // Major every 0.2
            const isKey = [0, 8, 10, 13, 15, 20].includes(i); // Key thresholds

            const tickOuterRadius = radius + (isKey ? 10 : isMajor ? 7 : 5);
            const tickInnerRadius = radius + 1;

            const outerX = centerX + tickOuterRadius * Math.cos(tickAngle);
            const outerY = centerY + tickOuterRadius * Math.sin(tickAngle);
            const innerX = centerX + tickInnerRadius * Math.cos(tickAngle);
            const innerY = centerY + tickInnerRadius * Math.sin(tickAngle);

            return (
              <g key={i}>
                <line
                  x1={innerX} y1={innerY} x2={outerX} y2={outerY}
                  stroke="#2c3e50"
                  strokeWidth={isKey ? 1.5 : isMajor ? 1 : 0.5}
                  opacity={isKey ? 1 : isMajor ? 0.7 : 0.4}
                  strokeLinecap="round"
                />
                {isKey && (
                  <text
                    x={centerX + (radius + 18) * Math.cos(tickAngle)}
                    y={centerY + (radius + 18) * Math.sin(tickAngle) + 3}
                    fill="#2c3e50"
                    fontSize="8"
                    fontWeight="700"
                    textAnchor="middle"
                    fontFamily='"Roboto Mono", monospace'
                  >
                    {value.toFixed(1)}
                  </text>
                )}
              </g>
            );
          })}

          {/* Bold needles with glow effect */}
          <line
            x1={centerX} y1={centerY} x2={externalNeedleX} y2={externalNeedleY}
            stroke="#27ae60" strokeWidth={3.5} strokeLinecap="round"
            style={{ filter: 'drop-shadow(0 0 3px rgba(39, 174, 96, 0.8))' }}
          />
          <line
            x1={centerX} y1={centerY} x2={internalNeedleX} y2={internalNeedleY}
            stroke="#2980b9" strokeWidth={3.5} strokeLinecap="round"
            style={{ filter: 'drop-shadow(0 0 3px rgba(41, 128, 185, 0.8))' }}
          />

          {/* Center pivot */}
          <circle cx={centerX} cy={centerY} r={4} fill="#2c3e50" style={{ filter: 'drop-shadow(0 1px 2px rgba(0,0,0,0.5))' }} />
          <circle cx={centerX} cy={centerY} r={1.5} fill="#ecf0f1" />
        </svg>
      </div>

      {/* High-precision value displays */}
      <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%', paddingLeft: '10px', paddingRight: '10px' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{
            fontSize: '20px', fontWeight: '800', color: '#1a1a1a',
            fontFamily: '"Roboto Mono", monospace', letterSpacing: '-0.5px',
            textShadow: '0 2px 4px rgba(0,0,0,0.15)', fontVariantNumeric: 'tabular-nums'
          }}>
            {typeof externalValue === 'number' && !isNaN(externalValue) ? externalValue.toFixed(2) : 'N/A'}
          </div>
          <div style={{ fontSize: '9px', color: '#27ae60', fontWeight: '800', textTransform: 'uppercase', letterSpacing: '0.8px' }}>
            EXTERNAL
          </div>
        </div>
        <div style={{ textAlign: 'center' }}>
          <div style={{
            fontSize: '20px', fontWeight: '800', color: '#1a1a1a',
            fontFamily: '"Roboto Mono", monospace', letterSpacing: '-0.5px',
            textShadow: '0 2px 4px rgba(0,0,0,0.15)', fontVariantNumeric: 'tabular-nums'
          }}>
            {typeof internalValue === 'number' && !isNaN(internalValue) ? internalValue.toFixed(2) : 'N/A'}
          </div>
          <div style={{ fontSize: '9px', color: '#2980b9', fontWeight: '800', textTransform: 'uppercase', letterSpacing: '0.8px' }}>
            INTERNAL
          </div>
        </div>
      </div>
    </div>
  );
};

// High-Precision Balance Bar with Ultra-Tight Tick Marks
const BalanceIndicator: React.FC<{
  divergence: number;
  trainingLoad: number;
  avgTrainingLoad: number;
  width?: number;
}> = ({ divergence, trainingLoad, avgTrainingLoad, width = 200 }) => {

  // Calculate balance position (-0.5 to +0.5 range)
  const clampedDivergence = Math.max(-0.5, Math.min(0.5, divergence));
  const normalizedPosition = (clampedDivergence + 0.5) / 1.0; // 0 to 1

  const barHeight = 4; // Thin precision bar
  const trackY = 30;
  const padding = 15;
  const trackWidth = width - (padding * 2);

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      minWidth: width,
      position: 'relative',
      fontFamily: '"Roboto Mono", "JetBrains Mono", "Courier New", monospace'
    }}>
      {/* Precision value display at top */}
      <div style={{
        fontSize: '20px',
        fontWeight: '800',
        color: '#1a1a1a',
        fontFamily: '"Roboto Mono", monospace',
        letterSpacing: '-0.5px',
        textShadow: '0 2px 4px rgba(0,0,0,0.15)',
        fontVariantNumeric: 'tabular-nums',
        marginTop: '8px',
        marginBottom: '8px'
      }}>
        {typeof divergence === 'number' && !isNaN(divergence) ? divergence.toFixed(2) : 'N/A'}
      </div>

      <div style={{ width: '100%', height: '60px', position: 'relative' }}>
        <svg width={width} height="60" viewBox={`0 0 ${width} 60`}>
          <defs>
            <linearGradient id="barTrackGradient" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#e0e0e0" />
              <stop offset="100%" stopColor="#c8c8c8" />
            </linearGradient>
            <linearGradient id="barBlueZone" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#2874a6" stopOpacity="0.5" />
              <stop offset="100%" stopColor="#5dade2" stopOpacity="0.5" />
            </linearGradient>
            <linearGradient id="barGreenZone" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#229954" stopOpacity="0.6" />
              <stop offset="100%" stopColor="#58d68d" stopOpacity="0.6" />
            </linearGradient>
            <linearGradient id="barRedZone" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#ec7063" stopOpacity="0.5" />
              <stop offset="100%" stopColor="#c0392b" stopOpacity="0.5" />
            </linearGradient>
          </defs>

          {/* Base track */}
          <rect x={padding} y={trackY} width={trackWidth} height={barHeight} rx={2} fill="url(#barTrackGradient)" opacity={0.3} />

          {/* Color zones: Red (left 20%), Green (middle 60%), Red (right 20%) */}
          <rect x={padding} y={trackY} width={trackWidth * 0.2} height={barHeight} rx={2} fill="url(#barRedZone)" />
          <rect x={padding + trackWidth * 0.2} y={trackY} width={trackWidth * 0.6} height={barHeight} fill="url(#barGreenZone)" />
          <rect x={padding + trackWidth * 0.8} y={trackY} width={trackWidth * 0.2} height={barHeight} rx={2} fill="url(#barRedZone)" />

          {/* Ultra-precise tick marks - every 0.05 units from -0.5 to +0.5 */}
          {Array.from({ length: 21 }, (_, i) => {
            const value = -0.5 + (i * 0.05);
            const position = padding + (i / 20) * trackWidth;
            const isMajor = i % 2 === 0; // Major every 0.1
            const isKey = [0, 5, 10, 15, 20].includes(i); // -0.5, -0.25, 0, 0.25, 0.5

            return (
              <g key={i}>
                <line
                  x1={position} y1={trackY + barHeight}
                  x2={position} y2={trackY + barHeight + (isKey ? 10 : isMajor ? 7 : 4)}
                  stroke="#2c3e50"
                  strokeWidth={isKey ? 1.5 : isMajor ? 1 : 0.5}
                  opacity={isKey ? 1 : isMajor ? 0.7 : 0.4}
                  strokeLinecap="round"
                />
                {isKey && (
                  <text
                    x={position}
                    y={trackY + barHeight + 20}
                    fill="#2c3e50"
                    fontSize="8"
                    fontWeight="700"
                    textAnchor="middle"
                    fontFamily='"Roboto Mono", monospace'
                  >
                    {value.toFixed(2)}
                  </text>
                )}
              </g>
            );
          })}

          {/* Precision indicator - inverted arrowhead above bar */}
          <g>
            {/* Inverted arrowhead pointing down toward bar */}
            <polygon
              points={`${padding + normalizedPosition * trackWidth},${trackY - 2} ${padding + normalizedPosition * trackWidth - 5},${trackY - 10} ${padding + normalizedPosition * trackWidth + 5},${trackY - 10}`}
              fill="#2c3e50"
              style={{ filter: 'drop-shadow(0 1px 2px rgba(0,0,0,0.3))' }}
            />
          </g>
        </svg>
      </div>

      {/* Labels */}
      <div style={{ textAlign: 'center', marginTop: '2px' }}>
        <div style={{
          fontSize: '9px',
          color: '#6b7280',
          fontWeight: '800',
          textTransform: 'uppercase',
          letterSpacing: '0.8px'
        }}>
          DIVERGENCE
        </div>
      </div>
    </div>
  );
};

const CompactDashboardBanner: React.FC<CompactDashboardBannerProps> = ({
  onSyncComplete = () => {},
  metrics
}) => {
  const [isSyncing, setIsSyncing] = useState<boolean>(false);
  const [syncStatus, setSyncStatus] = useState<'ready' | 'syncing' | 'success' | 'error'>('ready');
  const [statusMessage, setStatusMessage] = useState<string>('');
  const [selectedDays, setSelectedDays] = useState<number>(7); // Default to 7 days

  // PROACTIVE TOKEN REFRESH: Refresh tokens when component mounts
  useEffect(() => {
    const refreshTokensProactively = async () => {
      try {
        const response = await fetch('/proactive-token-refresh', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
        });
        
        const result = await response.json();
        
        if (result.success && result.refreshed) {
          console.log('✅ Tokens refreshed proactively:', result.message);
        } else if (result.success && !result.refreshed) {
          console.log('✅ Tokens are still valid:', result.message);
        } else if (result.needs_reauth) {
          console.warn('⚠️ Re-authentication required:', result.message);
        } else {
          console.log('ℹ️ Token status:', result.message);
        }
      } catch (error) {
        console.error('Error checking token status:', error);
      }
    };

    // Refresh tokens proactively when component mounts
    refreshTokensProactively();
  }, []); // Empty dependency array means this runs once when component mounts

  // Dashboard color palette (blue-gray theme)
  const colors = {
    primary: '#3498db',
    secondary: '#2ecc71',
    warning: '#e67e22',
    danger: '#e74c3c',
    dark: '#2c3e50',
    accent: '#6c5ce7',
    background: '#f9fafb'
  };

  const handleManualSync = async (): Promise<void> => {
    try {
      setIsSyncing(true);
      setSyncStatus('syncing');
      setStatusMessage('Syncing with Strava...');
      const response: Response = await fetch('/sync-with-auto-refresh', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ days: selectedDays }) // Use selected value instead of hardcoded 30
      });

      const result: SyncResponse = await response.json();

      if (result.success) {
        setSyncStatus('success');
        setStatusMessage('Sync completed successfully!');
        setTimeout(() => {
          if (onSyncComplete) onSyncComplete();
        }, 1500);
      } else {
        setSyncStatus('error');
        setStatusMessage(result.error || 'Sync failed');
      }
    } catch (error) {
      setSyncStatus('error');
      setStatusMessage('Connection error');
    } finally {
      setIsSyncing(false);
      setTimeout(() => {
        setSyncStatus('ready');
        setStatusMessage('');
      }, 3000);
    }
  };

  const getSyncButtonStyle = (): React.CSSProperties => {
    const baseStyle = {
      display: 'flex',
      alignItems: 'center',
      gap: '0.5rem',
      padding: '0.5rem 1rem',
      borderRadius: '0.375rem',
      border: 'none',
      fontSize: '0.85rem',
      fontWeight: '500',
      cursor: isSyncing ? 'not-allowed' : 'pointer',
      transition: 'all 0.2s ease',
      minWidth: '120px',
      justifyContent: 'center'
    };

    switch (syncStatus) {
      case 'syncing':
        return {
          ...baseStyle,
          backgroundColor: colors.warning,
          color: 'white',
          cursor: 'not-allowed'
        };
      case 'success':
        return {
          ...baseStyle,
          backgroundColor: colors.secondary,
          color: 'white'
        };
      case 'error':
        return {
          ...baseStyle,
          backgroundColor: colors.danger,
          color: 'white'
        };
      default:
        return {
          ...baseStyle,
          backgroundColor: '#FC5200', // Keep Strava orange for compliance
          color: 'white'
        };
    }
  };

  const getSyncIcon = (): JSX.Element => {
    switch (syncStatus) {
      case 'syncing':
        return (
          <span style={{
            display: 'inline-block',
            width: '0.85rem',
            height: '0.85rem',
            border: '2px solid #ffffff40',
            borderTop: '2px solid #ffffff',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite'
          }} />
        );
      case 'success':
        return <span>✓</span>;
      case 'error':
        return <span>⚠</span>;
      default:
        return <span>🔄</span>;
    }
  };

  const getSyncText = (): string => {
    switch (syncStatus) {
      case 'syncing':
        return 'Syncing...';
      case 'success':
        return 'Success!';
      case 'error':
        return 'Try Again';
      default:
        return 'Sync Data';
    }
  };

  // Calculate average training load for balance indicator - with null safety
  const avgTrainingLoad = ((metrics?.sevenDayAvgLoad || 0) + (metrics?.sevenDayAvgTrimp || 0) / 30) / 2; // Simplified average

  return (
    <div style={{
      background: `linear-gradient(135deg, #778899 0%, #C0C0C0 50%, #F5F5F5 100%)`, // Muted gradient closer to card background
      padding: '0.5rem',
      borderRadius: '0.5rem', // Match dashboard cards
      marginBottom: '1rem',
      boxShadow: '0 1px 2px rgba(0, 0, 0, 0.05)' // Match dashboard cards
    }}>
      <style>
        {`
          @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
          }

          .sync-button:hover:not(:disabled) {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
          }
        `}
      </style>

      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1.5fr 1.5fr 1fr',
        gap: '1rem',
        alignItems: 'stretch'
      }}>

        {/* Card 1: Branding (Far Left) */}
        <div style={{
          backgroundColor: '#233858',
          borderRadius: '0.5rem',
          padding: '0',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          textAlign: 'center',
          boxShadow: '0 1px 2px rgba(0, 0, 0, 0.05)',
          position: 'relative',
          overflow: 'hidden',
          maxHeight: '180px'
        }}>
          <img
            src="/static/images/YTM_Logo_cropped.webp"
            alt="Your Training Monkey Logo"
            style={{
              height: '100%'
            }}
          />
        </div>

        {/* Card 2: Training Balance (with Gauges) */}
        <div id="at-a-glance-meters" style={{
          backgroundColor: 'white',
          borderRadius: '0.5rem',
          padding: '0.5rem',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          boxShadow: '0 1px 2px rgba(0, 0, 0, 0.05)',
          minHeight: '155px',
          maxHeight: '155px'
        }}>
          {/* Dynamic Risk Assessment Title */}
          {(() => {
            // Determine risk level based on metrics
            const externalAcwr = metrics?.externalAcwr || 0;
            const internalAcwr = metrics?.internalAcwr || 0;
            const divergence = metrics?.normalizedDivergence || 0;
            
            // Risk assessment logic
            let riskLevel = 'LOW';
            let riskColor = '#2ecc71'; // Green
            
            if (externalAcwr > 1.3 || internalAcwr > 1.3 || divergence < -0.15) {
              riskLevel = 'HIGH';
              riskColor = '#e74c3c'; // Red
            } else if (externalAcwr > 1.1 || internalAcwr > 1.1 || divergence < -0.05) {
              riskLevel = 'MODERATE';
              riskColor = '#f39c12'; // Orange
            }
            
            return (
              <h3 style={{
                margin: '0 0 0.5rem 0',
                fontSize: '0.95rem',
                fontWeight: '600',
                color: colors.dark,
                textAlign: 'center'
              }}>
                Injury Risk At-A-Glance - <span style={{ color: riskColor, fontWeight: '700' }}>{riskLevel}</span>
              </h3>
            );
          })()}

          {/* Consolidated gauges container - centralized */}
          <div style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'stretch',
            gap: '1.5rem', // Increased space between gauge and bar for better horizontal use
            flex: 1,
            minHeight: '40px',
            marginLeft: '20px' // Add left margin to centralize
          }}>
            <MetricTooltip
              data-metric-tooltip
              metric="Training Strain (Dual ACWR)"
              value={`Ext: ${typeof metrics?.externalAcwr === 'number' ? metrics.externalAcwr.toFixed(2) : '0.00'}, Int: ${typeof metrics?.internalAcwr === 'number' ? metrics.internalAcwr.toFixed(2) : '0.00'}`}
              description="Dual ACWR display showing both external training load (distance, elevation) and internal stress (heart rate zones) on a single gauge. Green needle = external, blue needle = internal."
              interpretation="Compare needle positions to assess training balance. Both needles in green zone (0.8-1.3) indicates optimal training load."
              warning={(metrics?.externalAcwr || 0) > 1.3 || (metrics?.internalAcwr || 0) > 1.3 ? "High strain detected - consider reducing training intensity" : undefined}
              position="top"
            >
              <DualNeedleStrainGauge
                externalValue={metrics?.externalAcwr || 0}
                internalValue={metrics?.internalAcwr || 0}
                max={2.0}
                size={120}
              />
            </MetricTooltip>
            
            <MetricTooltip
              data-metric-tooltip
              metric="Training Balance"
              value={typeof metrics?.normalizedDivergence === 'number' && !isNaN(metrics.normalizedDivergence) ? metrics.normalizedDivergence.toFixed(3) : '0.000'}
              description="Normalized divergence between external and internal training load. Shows if your heart rate stress matches your external training effort."
              interpretation="Negative values indicate your body is working harder than expected (fatigue/overtraining), positive values suggest good fitness/recovery."
              warning={(metrics?.normalizedDivergence || 0) < -0.15 ? "High overtraining risk - rest recommended" : (metrics?.normalizedDivergence || 0) < -0.05 ? "Moderate fatigue - consider easier training" : undefined}
              position="top"
            >
              <BalanceIndicator
                divergence={metrics?.normalizedDivergence || 0}
                trainingLoad={metrics?.sevenDayAvgLoad || 0}
                avgTrainingLoad={avgTrainingLoad}
                width={200}
              />
            </MetricTooltip>
          </div>
        </div>

        {/* Card 3: Recovery Status */}
        <div id="recovery-metrics" style={{
          backgroundColor: 'white',
          borderRadius: '0.5rem',
          padding: '0.5rem',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          boxShadow: '0 1px 2px rgba(0, 0, 0, 0.05)',
          minHeight: '155px',
          maxHeight: '155px'
        }}>
          <ContextualTooltip
            content={
              <div>
                <div style={{ fontWeight: '600', marginBottom: '0.5rem' }}>
                  Recovery Status
                </div>
                <div style={{ fontSize: '0.8rem', lineHeight: '1.4' }}>
                  Tracks your recovery metrics including days since rest and 7-day training load. 
                  Helps identify when you need rest or can handle more training.
                </div>
              </div>
            }
            position="bottom"
            delay={300}
          >
            <h3 style={{
              margin: '0 0 0.5rem 0',
              fontSize: '0.95rem', // Matches Training Balance
              fontWeight: '600',
              color: colors.dark,
              cursor: 'help'
            }}>
              Recovery Status
            </h3>
          </ContextualTooltip>

          <div style={{ display: 'flex', justifyContent: 'space-around', alignItems: 'center' }}>
            <MetricTooltip
              data-metric-tooltip
              metric="Days Since Rest"
              value={metrics?.daysSinceRest || 0}
              description="Number of consecutive days without a rest day. Extended training blocks without rest can increase injury risk."
              interpretation="Consider a rest day when this reaches 6-7 days to allow for proper recovery."
              warning={(metrics?.daysSinceRest || 0) > 6 ? "Extended training block - rest day recommended" : undefined}
              position="top"
            >
              <div style={{ textAlign: 'center', cursor: 'help' }}>
                <p style={{ margin: '0', fontSize: '0.75rem', color: '#6b7280' }}>Days Since Rest</p>
                <p style={{
                  margin: '0',
                  fontSize: '1.3rem', // Slightly larger for emphasis
                  fontWeight: 'bold',
                  color: (metrics?.daysSinceRest || 0) > 6 ? colors.warning : colors.secondary
                }}>
                  {metrics?.daysSinceRest || 0}
                </p>
              </div>
            </MetricTooltip>

            <ContextualTooltip
              content={
                <div>
                  <div style={{ fontWeight: '600', marginBottom: '0.5rem' }}>
                    7-Day Training Load Summary
                  </div>
                  <div style={{ fontSize: '0.8rem', lineHeight: '1.4', marginBottom: '0.5rem' }}>
                    <strong>External Load:</strong> Total distance and elevation over 7 days<br/>
                    <strong>Internal Load:</strong> Total TRIMP (heart rate stress) over 7 days
                  </div>
                  <div style={{ fontSize: '0.8rem', lineHeight: '1.4' }}>
                    These metrics help track your weekly training volume and intensity.
                  </div>
                </div>
              }
              position="top"
              delay={300}
            >
              <div style={{ textAlign: 'center', cursor: 'help' }}>
                <p style={{
                  margin: '0',
                  fontSize: '0.75rem',  // Label styling
                  color: '#6b7280'      // Label styling
                }}>
                  7-Day Total Load
                </p>

                {/* Value only - large and bold */}
                <p style={{
                  margin: '0',
                  fontSize: '1.1rem',   // Value styling (matches ACWR values)
                  fontWeight: 'bold',
                  color: colors.primary
                }}>
                  {typeof metrics?.sevenDayAvgLoad === 'number' && !isNaN(metrics.sevenDayAvgLoad) ? (metrics.sevenDayAvgLoad * 7).toFixed(1) : "N/A"}
                </p>

                {/* Unit only - small gray to match label */}
                <p style={{
                  margin: '0',
                  fontSize: '0.75rem',  // Unit styling (matches "7-Day Total Load" label)
                  color: '#6b7280'      // Unit styling (matches "7-Day Total Load" label)
                }}>
                  miles equivalent
                </p>

                {/* Value only - large and bold */}
                <p style={{
                  margin: '0',
                  fontSize: '1.1rem',   // Value styling (matches ACWR values)
                  fontWeight: 'bold',
                  color: colors.primary
                }}>
                  {typeof metrics?.sevenDayAvgTrimp === 'number' && !isNaN(metrics.sevenDayAvgTrimp) ? (metrics.sevenDayAvgTrimp * 7).toFixed(0) : "N/A"}
                </p>

                {/* Unit only - small gray to match label */}
                <p style={{
                  margin: '0',
                  fontSize: '0.75rem',  // Unit styling (matches "7-Day Total Load" label)
                  color: '#6b7280'      // Unit styling (matches "7-Day Total Load" label)
                }}>
                  TRIMP
                </p>
              </div>
            </ContextualTooltip>
          </div>

          <div style={{
            fontSize: '0.7rem', // Matches Training Balance
            color: (metrics?.daysSinceRest || 0) > 6 ? colors.warning : colors.secondary, // CONSISTENT COLORS
            fontWeight: '500',
            textAlign: 'center'
          }}>
            {(metrics?.daysSinceRest || 0) > 6 ? "Need rest" : "On track"}
          </div>
        </div>

        {/* Card 4: Data Sync (Far Right) */}
        <div style={{
          backgroundColor: 'white',
          borderRadius: '0.5rem',
          padding: '0.5rem',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: '0.5rem',
          boxShadow: '0 1px 2px rgba(0, 0, 0, 0.05)',
          minHeight: '155px',
          maxHeight: '155px'
        }}>
          <h3 style={{
            margin: '0',
            fontSize: '0.9rem',
            fontWeight: '600',
            color: colors.dark
          }}>
            Data Sync
          </h3>

          <select
            value={selectedDays}
            onChange={(e) => setSelectedDays(parseInt(e.target.value))}
            style={{
              padding: '0.25rem',
              borderRadius: '0.25rem',
              border: '1px solid #d1d5db',
              backgroundColor: 'white',
              fontSize: '0.75rem',
              color: colors.dark,
              cursor: 'pointer',
              width: '100%',
              textAlign: 'center'
            }}
          >
            <option value="7">7 Days</option>
            <option value="14">14 Days</option>
            <option value="30">30 Days</option>
            <option value="60">60 Days</option>
            <option value="90">90 Days</option>
          </select>

          <button
            id="sync-data-button"
            onClick={handleManualSync}
            disabled={isSyncing}
            className="sync-button"
            style={getSyncButtonStyle()}
          >
            {getSyncIcon()}
            {getSyncText()}
          </button>

          {statusMessage && (
            <p style={{
              margin: '0',
              fontSize: '0.7rem',
              color: syncStatus === 'error' ? '#dc2626' :
                     syncStatus === 'success' ? '#059669' : '#6b7280'
            }}>
              {statusMessage}
            </p>
          )}



          {/* Powered by Strava - Compliant with Brand Guidelines */}
          <div style={{
            fontSize: '0.65rem',
            fontWeight: '500',
            color: '#FC5200',
            textAlign: 'center'
          }}>
            POWERED BY STRAVA
          </div>
        </div>
      </div>

      {/* Responsive adjustments */}
      <style>
        {`
          @media (max-width: 768px) {
            .compact-banner-grid {
              grid-template-columns: 1fr 1fr !important;
              gap: 0.5rem !important;
            }
          }

          @media (max-width: 480px) {
            .compact-banner-grid {
              grid-template-columns: 1fr !important;
            }
          }
        `}
      </style>
    </div>
  );
};

export default CompactDashboardBanner;