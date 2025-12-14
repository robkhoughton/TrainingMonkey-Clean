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
  size = 150
}) => {
  // Calculate angles (gauge spans 180 degrees, horizontal orientation)
  const clampedExternalValue = Math.max(0, Math.min(max, externalValue));
  const clampedInternalValue = Math.max(0, Math.min(max, internalValue));
  const externalAngle = (clampedExternalValue / max) * 180;
  const internalAngle = (clampedInternalValue / max) * 180;

  const radius = 50; // Widened radius to match divergence gauge
  const strokeWidth = 8; // Match divergence gauge thickness
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
      fontFamily: '"Roboto Mono", "JetBrains Mono", "Courier New", monospace',
      height: '100%'
    }}>
      <div style={{
        position: 'relative',
        width: size,
        height: size * 0.6,
        marginTop: '0px',
        marginBottom: '4px'
      }}>
        <svg width={size} height={size * 0.6} viewBox={`0 0 ${size} ${size * 0.6}`}>
          <defs>
            {/* Sharp gradients for depth */}
            <linearGradient id="trackGradient" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#e8e8e8" />
              <stop offset="100%" stopColor="#d0d0d0" />
            </linearGradient>
            <linearGradient id="blueZone" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#5dade2" stopOpacity="0.8" />
              <stop offset="100%" stopColor="#2874a6" stopOpacity="0.8" />
            </linearGradient>
            <linearGradient id="greenZone" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#2ecc71" stopOpacity="0.9" />
              <stop offset="100%" stopColor="#27ae60" stopOpacity="0.9" />
            </linearGradient>
            <linearGradient id="orangeZone" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#f1c40f" stopOpacity="0.9" />
              <stop offset="100%" stopColor="#f39c12" stopOpacity="0.9" />
            </linearGradient>
            <linearGradient id="redZone" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#e74c3c" stopOpacity="0.9" />
              <stop offset="100%" stopColor="#c0392b" stopOpacity="0.9" />
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

            const tickOuterRadius = radius + (isKey ? 8 : isMajor ? 6 : 4);
            const tickInnerRadius = radius - 1;

            const outerX = centerX + tickOuterRadius * Math.cos(tickAngle);
            const outerY = centerY + tickOuterRadius * Math.sin(tickAngle);
            const innerX = centerX + tickInnerRadius * Math.cos(tickAngle);
            const innerY = centerY + tickInnerRadius * Math.sin(tickAngle);

            return (
              <g key={i}>
                <line
                  x1={innerX} y1={innerY} x2={outerX} y2={outerY}
                  stroke="#e0e0e0"
                  strokeWidth={isKey ? 1.5 : isMajor ? 1 : 0.5}
                  opacity={isKey ? 0.9 : isMajor ? 0.7 : 0.5}
                  strokeLinecap="round"
                />
                {isKey && (
                  <text
                    x={centerX + (radius + 16) * Math.cos(tickAngle)}
                    y={centerY + (radius + 16) * Math.sin(tickAngle) + 4}
                    fill="#f0f0f0"
                    fontSize="10"
                    fontWeight="800"
                    textAnchor="middle"
                    fontFamily='"Roboto Mono", monospace'
                  >
                    {value.toFixed(1)}
                  </text>
                )}
              </g>
            );
          })}

          {/* Color-coded needles - crisp and sharp */}
          <line
            x1={centerX} y1={centerY} x2={externalNeedleX} y2={externalNeedleY}
            stroke="#2ecc71" strokeWidth={3.5} strokeLinecap="round"
          />
          <line
            x1={centerX} y1={centerY} x2={internalNeedleX} y2={internalNeedleY}
            stroke="#3498db" strokeWidth={3.5} strokeLinecap="round"
          />

          {/* Center pivot */}
          <circle cx={centerX} cy={centerY} r={4} fill="#2c3e50" style={{ filter: 'drop-shadow(0 1px 2px rgba(0,0,0,0.5))' }} />
          <circle cx={centerX} cy={centerY} r={1.5} fill="#ecf0f1" />
        </svg>
      </div>

      {/* High-precision value displays */}
      <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%', paddingLeft: '10px', paddingRight: '10px', marginTop: 'auto', paddingBottom: '0px' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{
            fontSize: '20px', fontWeight: '800', color: '#f0f0f0',
            fontFamily: '"Roboto Mono", monospace', letterSpacing: '-0.5px',
            textShadow: '0 2px 4px rgba(0,0,0,0.5)', fontVariantNumeric: 'tabular-nums'
          }}>
            {typeof externalValue === 'number' && !isNaN(externalValue) ? externalValue.toFixed(2) : 'N/A'}
          </div>
          <div style={{ fontSize: '9px', color: '#2ecc71', fontWeight: '800', textTransform: 'uppercase', letterSpacing: '0.8px' }}>
            EXTERNAL
          </div>
        </div>
        <div style={{ textAlign: 'center' }}>
          <div style={{
            fontSize: '20px', fontWeight: '800', color: '#f0f0f0',
            fontFamily: '"Roboto Mono", monospace', letterSpacing: '-0.5px',
            textShadow: '0 2px 4px rgba(0,0,0,0.5)', fontVariantNumeric: 'tabular-nums'
          }}>
            {typeof internalValue === 'number' && !isNaN(internalValue) ? internalValue.toFixed(2) : 'N/A'}
          </div>
          <div style={{ fontSize: '9px', color: '#3498db', fontWeight: '800', textTransform: 'uppercase', letterSpacing: '0.8px' }}>
            INTERNAL
          </div>
        </div>
      </div>
    </div>
  );
};

// Circular Gauge for Divergence (Car Dashboard Style)
interface CircularDivergenceGaugeProps {
  divergence: number;
  size?: number;
}

const CircularDivergenceGauge: React.FC<CircularDivergenceGaugeProps> = ({
  divergence,
  size = 150
}) => {
  // Map divergence (-0.5 to +0.5) to gauge angle (0° to 180°) - 9 o'clock to 3 o'clock
  const clampedDivergence = Math.max(-0.5, Math.min(0.5, divergence));
  const normalizedValue = (clampedDivergence + 0.5) / 1.0; // 0 to 1
  const angle = normalizedValue * 180; // 0° to 180° (9-3 o'clock)

  const radius = 50; // Match ACWR gauge
  const strokeWidth = 8;
  const centerX = size / 2;
  const centerY = size / 2 + 5; // Match ACWR vertical position

  // Needle position (starts at 180° / 9 o'clock position)
  const needleAngle = (angle + 180) * (Math.PI / 180);
  const needleLength = radius - 5;
  const needleX = centerX + needleLength * Math.cos(needleAngle);
  const needleY = centerY + needleLength * Math.sin(needleAngle);

  // Create arc path (9 o'clock to 3 o'clock)
  const createArc = (startAngle: number, endAngle: number, r: number = radius) => {
    const startRad = (startAngle + 180) * (Math.PI / 180);
    const endRad = (endAngle + 180) * (Math.PI / 180);
    const x1 = centerX + r * Math.cos(startRad);
    const y1 = centerY + r * Math.sin(startRad);
    const x2 = centerX + r * Math.cos(endRad);
    const y2 = centerY + r * Math.sin(endRad);
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
      fontFamily: '"Roboto Mono", "JetBrains Mono", "Courier New", monospace',
      height: '100%'
    }}>
      <div style={{
        position: 'relative',
        width: size,
        height: size * 0.6,
        marginTop: '0px',
        marginBottom: '2px'
      }}>
        <svg width={size} height={size * 0.75} viewBox={`0 0 ${size} ${size * 0.75}`}>
          <defs>
            <linearGradient id="divGaugeRed" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#e74c3c" stopOpacity="0.9" />
              <stop offset="100%" stopColor="#c0392b" stopOpacity="0.9" />
            </linearGradient>
            <linearGradient id="divGaugeGreen" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#2ecc71" stopOpacity="0.9" />
              <stop offset="100%" stopColor="#27ae60" stopOpacity="0.9" />
            </linearGradient>
            <radialGradient id="needleGradient">
              <stop offset="0%" stopColor="#ffffff" />
              <stop offset="100%" stopColor="#e0e0e0" />
            </radialGradient>
          </defs>

          {/* Background track */}
          <path d={createArc(0, 180)} fill="none" stroke="#e0e0e0" strokeWidth={strokeWidth} opacity={0.3} />

          {/* Red zone (0° to 54°): -0.5 to -0.2 */}
          <path d={createArc(0, 54)} fill="none" stroke="url(#divGaugeRed)" strokeWidth={strokeWidth} opacity={0.9} />

          {/* Green zone (54° to 144°): -0.2 to +0.3 */}
          <path d={createArc(54, 144)} fill="none" stroke="url(#divGaugeGreen)" strokeWidth={strokeWidth} opacity={0.9} />

          {/* Red zone (144° to 180°): +0.3 to +0.5 */}
          <path d={createArc(144, 180)} fill="none" stroke="url(#divGaugeRed)" strokeWidth={strokeWidth} opacity={0.9} />

          {/* Tick marks */}
          {Array.from({ length: 11 }, (_, i) => {
            const value = -0.5 + (i * 0.1);
            const tickAngle = (i / 10) * 180;
            const tickRad = (tickAngle + 180) * (Math.PI / 180);
            const isKey = i % 2 === 0;

            const tickOuterRadius = radius + (isKey ? 8 : 6);
            const tickInnerRadius = radius - 1;

            const outerX = centerX + tickOuterRadius * Math.cos(tickRad);
            const outerY = centerY + tickOuterRadius * Math.sin(tickRad);
            const innerX = centerX + tickInnerRadius * Math.cos(tickRad);
            const innerY = centerY + tickInnerRadius * Math.sin(tickRad);

            return (
              <g key={i}>
                <line
                  x1={innerX} y1={innerY} x2={outerX} y2={outerY}
                  stroke="#e0e0e0"
                  strokeWidth={isKey ? 1.5 : 1}
                  opacity={isKey ? 0.9 : 0.7}
                  strokeLinecap="round"
                />
                {isKey && (
                  <text
                    x={centerX + (radius + 16) * Math.cos(tickRad)}
                    y={centerY + (radius + 16) * Math.sin(tickRad) + 4}
                    fill="#f0f0f0"
                    fontSize="10"
                    fontWeight="800"
                    textAnchor="middle"
                    fontFamily='"Roboto Mono", monospace'
                  >
                    {value.toFixed(1)}
                  </text>
                )}
              </g>
            );
          })}

          {/* White metallic needle - crisp and sharp */}
          <line
            x1={centerX} y1={centerY}
            x2={needleX} y2={needleY}
            stroke="#ffffff"
            strokeWidth={4}
            strokeLinecap="round"
          />

          {/* Center pivot with metallic look */}
          <circle cx={centerX} cy={centerY} r={6} fill="#1a1a1a" style={{ filter: 'drop-shadow(0 2px 6px rgba(0,0,0,0.8))' }} />
          <circle cx={centerX} cy={centerY} r={3.5} fill="url(#needleGradient)" />
          <circle cx={centerX} cy={centerY} r={1.5} fill="#ffffff" opacity={0.8} />
        </svg>
      </div>

      {/* Value display - positioned at same height as ACWR */}
      <div style={{ marginTop: 'auto', width: '100%', paddingBottom: '0px' }}>
        <div style={{
          fontSize: '20px',
          fontWeight: '800',
          color: '#f0f0f0',
          fontFamily: '"Roboto Mono", monospace',
          letterSpacing: '-0.5px',
          textShadow: '0 2px 4px rgba(0,0,0,0.5)',
          fontVariantNumeric: 'tabular-nums',
          textAlign: 'center'
        }}>
          {typeof divergence === 'number' && !isNaN(divergence) ? divergence.toFixed(2) : 'N/A'}
        </div>
        <div style={{
          fontSize: '9px',
          color: '#f0f0f0',
          fontWeight: '800',
          textTransform: 'uppercase',
          letterSpacing: '0.8px',
          textAlign: 'center'
        }}>
          DIVERGENCE
        </div>
      </div>
    </div>
  );
};

// Vertical Risk Bar with Color Zones and Arrowhead Indicator (Car Dashboard Style)
interface VerticalRiskBarProps {
  riskLevel: number; // 0 to 100
  size?: number;
}

const VerticalRiskBar: React.FC<VerticalRiskBarProps> = ({
  riskLevel,
  size = 150
}) => {
  const clampedRisk = Math.max(0, Math.min(100, riskLevel));
  const barWidth = 20; // Narrower to give gauges more room
  const barHeight = size * 0.55; // Reduced from 0.65 to fit better
  const centerX = size / 2;

  // Calculate arrowhead position (inverted: 0% at top, 100% at bottom)
  const arrowY = 10 + ((100 - clampedRisk) / 100) * barHeight;

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      minWidth: size,
      position: 'relative',
      fontFamily: '"Roboto Mono", "JetBrains Mono", "Courier New", monospace',
      height: '100%'
    }}>
      <div style={{
        position: 'relative',
        width: size,
        height: barHeight + 20,
        marginTop: '0px',
        marginBottom: '2px'
      }}>
        <svg width={size} height={barHeight + 20} viewBox={`0 0 ${size} ${barHeight + 20}`}>
          <defs>
            <linearGradient id="greenZoneGrad" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#27ae60" stopOpacity="0.9" />
              <stop offset="100%" stopColor="#2ecc71" stopOpacity="0.9" />
            </linearGradient>
            <linearGradient id="yellowZoneGrad" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#f1c40f" stopOpacity="0.9" />
              <stop offset="100%" stopColor="#f39c12" stopOpacity="0.9" />
            </linearGradient>
            <linearGradient id="redZoneGrad" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#e74c3c" stopOpacity="0.9" />
              <stop offset="100%" stopColor="#c0392b" stopOpacity="0.9" />
            </linearGradient>
          </defs>

          {/* Red zone (top 30%): 70-100% risk */}
          <rect
            x={centerX - barWidth / 2}
            y={10}
            width={barWidth}
            height={barHeight * 0.3}
            rx={2}
            fill="url(#redZoneGrad)"
            stroke="#8b0000"
            strokeWidth={1}
          />

          {/* Yellow zone (middle 30%): 40-70% risk */}
          <rect
            x={centerX - barWidth / 2}
            y={10 + barHeight * 0.3}
            width={barWidth}
            height={barHeight * 0.3}
            fill="url(#yellowZoneGrad)"
            stroke="#d68910"
            strokeWidth={1}
          />

          {/* Green zone (bottom 40%): 0-40% risk */}
          <rect
            x={centerX - barWidth / 2}
            y={10 + barHeight * 0.6}
            width={barWidth}
            height={barHeight * 0.4}
            rx={2}
            fill="url(#greenZoneGrad)"
            stroke="#1e7e34"
            strokeWidth={1}
          />

          {/* Arrowhead indicator pointing toward the bar */}
          <g>
            {/* Arrowhead pointing left toward the bar at the risk level */}
            <polygon
              points={`${centerX - barWidth / 2 - 2},${arrowY} ${centerX - barWidth / 2 - 12},${arrowY - 6} ${centerX - barWidth / 2 - 12},${arrowY + 6}`}
              fill="#ffffff"
              stroke="#000000"
              strokeWidth={1.5}
              style={{ filter: 'drop-shadow(0 2px 6px rgba(0,0,0,0.7))' }}
            />
            {/* Highlight on arrowhead for 3D effect */}
            <polygon
              points={`${centerX - barWidth / 2 - 3},${arrowY} ${centerX - barWidth / 2 - 11},${arrowY - 5} ${centerX - barWidth / 2 - 11},${arrowY + 5}`}
              fill="#f0f0f0"
              opacity={0.5}
            />
          </g>

          {/* Tick marks on right side */}
          {Array.from({ length: 6 }, (_, i) => {
            const y = 10 + (i / 5) * barHeight;
            const label = 100 - i * 20;

            return (
              <g key={i}>
                <line
                  x1={centerX + barWidth / 2}
                  y1={y}
                  x2={centerX + barWidth / 2 + 6}
                  y2={y}
                  stroke="#f0f0f0"
                  strokeWidth={1.5}
                  opacity={0.8}
                />
                <text
                  x={centerX + barWidth / 2 + 10}
                  y={y + 3}
                  fill="#f0f0f0"
                  fontSize="8"
                  fontWeight="700"
                  textAnchor="start"
                  fontFamily='"Roboto Mono", monospace'
                >
                  {label}
                </text>
              </g>
            );
          })}
        </svg>
      </div>

      {/* Label */}
      <div style={{
        fontSize: '9px',
        color: '#f0f0f0',
        fontWeight: '800',
        textTransform: 'uppercase',
        letterSpacing: '0.8px',
        marginTop: 'auto',
        textAlign: 'center',
        paddingBottom: '0px'
      }}>
        RISK LEVEL
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
      padding: '0.5rem 0.5rem 1.25rem 0.5rem',
      borderRadius: '0.5rem', // Match dashboard cards
      marginBottom: '1rem',
      boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15), 0 2px 4px rgba(0, 0, 0, 0.1)' // Enhanced depth
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
          alignItems: 'stretch',
          justifyContent: 'stretch',
          textAlign: 'center',
          boxShadow: '0 6px 16px rgba(0, 0, 0, 0.2), 0 2px 6px rgba(0, 0, 0, 0.15), inset 0 1px 0 rgba(255,255,255,0.1)',
          border: '3px solid #7a7a7a',
          position: 'relative',
          overflow: 'hidden',
          height: '165px',
          boxSizing: 'border-box' as const
        }}>
          <img
            src="/static/images/YTM_Logo_cropped.webp"
            alt="Your Training Monkey Logo"
            style={{
              height: '100%',
              width: '100%',
              objectFit: 'cover',
              display: 'block',
              margin: '0',
              padding: '0',
              flex: '1 1 auto',
              alignSelf: 'stretch',
              minHeight: '0'
            }}
          />
        </div>

        {/* Card 2: Training Balance (with Gauges) - Carbon fiber sports car style */}
        <div id="at-a-glance-meters" style={{
          background: `
            repeating-linear-gradient(
              45deg,
              #080808 0px,
              #2a2a2a 2px,
              #080808 4px,
              #080808 6px
            ),
            repeating-linear-gradient(
              -45deg,
              #080808 0px,
              #2a2a2a 2px,
              #080808 4px,
              #080808 6px
            ),
            linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 50%, #0a0a0a 100%)
          `,
          borderRadius: '0.5rem',
          padding: '0.5rem 0.5rem 0.75rem 0.5rem',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          boxShadow: '0 6px 16px rgba(0, 0, 0, 0.2), 0 2px 6px rgba(0, 0, 0, 0.15), inset 0 1px 0 rgba(255,255,255,0.1)',
          border: '3px solid #7a7a7a',
          height: '165px',
          position: 'relative' as const,
          boxSizing: 'border-box' as const
        }}>
          {/* Dynamic Risk Assessment Title */}
          {(() => {
            // Calculate risk score using the same weighted logic as the vertical bar
            const externalAcwr = metrics?.externalAcwr || 0;
            const internalAcwr = metrics?.internalAcwr || 0;
            const divergence = metrics?.normalizedDivergence || 0;
            const daysSinceRest = metrics?.daysSinceRest || 0;
            
            // Calculate risk score (0-100) - same logic as vertical bar
            let riskScore = 0;
            
            // ACWR contribution (40%)
            const avgAcwr = (externalAcwr + internalAcwr) / 2;
            if (avgAcwr > 1.5) riskScore += 40;
            else if (avgAcwr > 1.3) riskScore += 30;
            else if (avgAcwr > 1.1) riskScore += 20;
            else if (avgAcwr > 0.8) riskScore += 10;
            
            // Divergence contribution (40%)
            if (divergence < -0.25) riskScore += 40;
            else if (divergence < -0.15) riskScore += 30;
            else if (divergence < -0.05) riskScore += 15;
            
            // Days since rest contribution (20%)
            if (daysSinceRest > 7) riskScore += 20;
            else if (daysSinceRest > 6) riskScore += 15;
            else if (daysSinceRest > 5) riskScore += 10;
            
            const finalRiskScore = Math.min(100, riskScore);
            
            // Determine risk level based on score thresholds (matching bar interpretation)
            let riskLevel = 'LOW';
            let riskColor = '#2ecc71'; // Green
            
            if (finalRiskScore > 70) {
              riskLevel = 'HIGH';
              riskColor = '#e74c3c'; // Red
            } else if (finalRiskScore > 40) {
              riskLevel = 'MODERATE';
              riskColor = '#f39c12'; // Orange
            }
            
            return (
              <h3 style={{
                margin: '0 0 0.25rem 0',
                fontSize: '0.95rem',
                fontWeight: '600',
                color: '#f0f0f0',
                textAlign: 'center'
              }}>
                Injury Risk At-A-Glance - <span style={{ color: riskColor, fontWeight: '700' }}>{riskLevel}</span>
              </h3>
            );
          })()}

          {/* Consolidated gauges container - car dashboard style layout */}
          <div style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'flex-start',
            gap: '0.5rem',
            flex: 1,
            minHeight: '40px',
            marginTop: '0'
          }}>
            {/* Left Gauge: Training Strain (Dual ACWR) */}
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
                size={150}
              />
            </MetricTooltip>

            {/* Center: Vertical Risk Bar */}
            <MetricTooltip
              data-metric-tooltip
              metric="Injury Risk Level"
              value={(() => {
                const externalAcwr = metrics?.externalAcwr || 0;
                const internalAcwr = metrics?.internalAcwr || 0;
                const divergence = metrics?.normalizedDivergence || 0;
                const daysSinceRest = metrics?.daysSinceRest || 0;

                // Calculate risk level (0-100)
                let riskScore = 0;

                // ACWR contribution (40%)
                const avgAcwr = (externalAcwr + internalAcwr) / 2;
                if (avgAcwr > 1.5) riskScore += 40;
                else if (avgAcwr > 1.3) riskScore += 30;
                else if (avgAcwr > 1.1) riskScore += 20;
                else if (avgAcwr > 0.8) riskScore += 10;

                // Divergence contribution (40%)
                if (divergence < -0.25) riskScore += 40;
                else if (divergence < -0.15) riskScore += 30;
                else if (divergence < -0.05) riskScore += 15;

                // Days since rest contribution (20%)
                if (daysSinceRest > 7) riskScore += 20;
                else if (daysSinceRest > 6) riskScore += 15;
                else if (daysSinceRest > 5) riskScore += 10;

                return Math.min(100, riskScore);
              })().toFixed(0) + '%'}
              description="Overall injury risk assessment based on training strain, divergence, and recovery status. Combines ACWR, training balance, and days since rest into a single risk metric."
              interpretation="Green (0-40%): Low risk, training well-balanced. Orange (40-70%): Moderate risk, monitor closely. Red (70-100%): High risk, consider rest or reduced load."
              warning={(() => {
                const riskLevel = (() => {
                  const externalAcwr = metrics?.externalAcwr || 0;
                  const internalAcwr = metrics?.internalAcwr || 0;
                  const divergence = metrics?.normalizedDivergence || 0;
                  const daysSinceRest = metrics?.daysSinceRest || 0;
                  let riskScore = 0;
                  const avgAcwr = (externalAcwr + internalAcwr) / 2;
                  if (avgAcwr > 1.5) riskScore += 40;
                  else if (avgAcwr > 1.3) riskScore += 30;
                  else if (avgAcwr > 1.1) riskScore += 20;
                  else if (avgAcwr > 0.8) riskScore += 10;
                  if (divergence < -0.25) riskScore += 40;
                  else if (divergence < -0.15) riskScore += 30;
                  else if (divergence < -0.05) riskScore += 15;
                  if (daysSinceRest > 7) riskScore += 20;
                  else if (daysSinceRest > 6) riskScore += 15;
                  else if (daysSinceRest > 5) riskScore += 10;
                  return Math.min(100, riskScore);
                })();

                if (riskLevel > 70) return "High injury risk - rest strongly recommended";
                if (riskLevel > 40) return "Moderate risk - monitor and consider reducing intensity";
                return undefined;
              })()}
              position="top"
            >
              <VerticalRiskBar
                riskLevel={(() => {
                  const externalAcwr = metrics?.externalAcwr || 0;
                  const internalAcwr = metrics?.internalAcwr || 0;
                  const divergence = metrics?.normalizedDivergence || 0;
                  const daysSinceRest = metrics?.daysSinceRest || 0;

                  // Calculate risk level (0-100)
                  let riskScore = 0;

                  // ACWR contribution (40%)
                  const avgAcwr = (externalAcwr + internalAcwr) / 2;
                  if (avgAcwr > 1.5) riskScore += 40;
                  else if (avgAcwr > 1.3) riskScore += 30;
                  else if (avgAcwr > 1.1) riskScore += 20;
                  else if (avgAcwr > 0.8) riskScore += 10;

                  // Divergence contribution (40%)
                  if (divergence < -0.25) riskScore += 40;
                  else if (divergence < -0.15) riskScore += 30;
                  else if (divergence < -0.05) riskScore += 15;

                  // Days since rest contribution (20%)
                  if (daysSinceRest > 7) riskScore += 20;
                  else if (daysSinceRest > 6) riskScore += 15;
                  else if (daysSinceRest > 5) riskScore += 10;

                  return Math.min(100, riskScore);
                })()}
                size={150}
              />
            </MetricTooltip>

            {/* Right Gauge: Divergence */}
            <MetricTooltip
              data-metric-tooltip
              metric="Training Balance (Divergence)"
              value={typeof metrics?.normalizedDivergence === 'number' && !isNaN(metrics.normalizedDivergence) ? metrics.normalizedDivergence.toFixed(3) : '0.000'}
              description="Normalized divergence between external and internal training load. Shows if your heart rate stress matches your external training effort."
              interpretation="Negative values indicate your body is working harder than expected (fatigue/overtraining), positive values suggest good fitness/recovery."
              warning={(metrics?.normalizedDivergence || 0) < -0.15 ? "High overtraining risk - rest recommended" : (metrics?.normalizedDivergence || 0) < -0.05 ? "Moderate fatigue - consider easier training" : undefined}
              position="top"
            >
              <CircularDivergenceGauge
                divergence={metrics?.normalizedDivergence || 0}
                size={150}
              />
            </MetricTooltip>
          </div>
        </div>

        {/* Card 3: Recovery Status */}
        <div id="recovery-metrics" style={{
          backgroundColor: 'white',
          borderRadius: '0.5rem',
          padding: '0.5rem 0.5rem 0.75rem 0.5rem',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          boxShadow: '0 6px 16px rgba(0, 0, 0, 0.2), 0 2px 6px rgba(0, 0, 0, 0.15), inset 0 1px 0 rgba(255,255,255,0.1)',
          border: '3px solid #7a7a7a',
          height: '165px',
          boxSizing: 'border-box' as const
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
          padding: '0.5rem 0.5rem 0.75rem 0.5rem',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: '0.5rem',
          boxShadow: '0 6px 16px rgba(0, 0, 0, 0.2), 0 2px 6px rgba(0, 0, 0, 0.15), inset 0 1px 0 rgba(255,255,255,0.1)',
          border: '3px solid #7a7a7a',
          height: '165px',
          boxSizing: 'border-box' as const
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
              padding: '0.25rem 0.5rem',
              borderRadius: '0.25rem',
              border: '1px solid #d1d5db',
              backgroundColor: 'white',
              fontSize: '0.75rem',
              color: colors.dark,
              cursor: 'pointer',
              width: 'auto',
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