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

// Dual Needle Strain Gauge Component
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
  size = 120 // Restored to proper size
}) => {
  // Calculate angles (gauge spans 180 degrees)
  const clampedExternalValue = Math.max(0, Math.min(max, externalValue));
  const clampedInternalValue = Math.max(0, Math.min(max, internalValue));
  const externalAngle = (clampedExternalValue / max) * 180;
  const internalAngle = (clampedInternalValue / max) * 180;
  
  // Color zones based on ACWR thresholds - matching chart colors
  const getColorForValue = (val: number) => {
    if (val < 0.8) return '#3498db'; // Blue - low load (matching chart)
    if (val <= 1.3) return '#2ecc71'; // Green - optimal (matching chart)
    if (val <= 1.5) return '#e67e22'; // Orange - moderate risk (matching chart)
    return '#e74c3c'; // Red - high risk (matching chart)
  };
  
  const radius = (size - 15) / 2; // Adjusted radius for smaller gauge
  const strokeWidth = 6; // Reduced stroke width for tighter look
  const centerX = size / 2;
  const centerY = size / 2;
  
  // Needle positions - adjusted for horizontal gauge (9 o'clock to 3 o'clock)
  const externalNeedleAngle = (externalAngle + 180) * (Math.PI / 180);
  const internalNeedleAngle = (internalAngle + 180) * (Math.PI / 180);
  const needleLength = radius - 5;
  
  const externalNeedleX = centerX + needleLength * Math.cos(externalNeedleAngle);
  const externalNeedleY = centerY + needleLength * Math.sin(externalNeedleAngle);
  const internalNeedleX = centerX + needleLength * Math.cos(internalNeedleAngle);
  const internalNeedleY = centerY + needleLength * Math.sin(internalNeedleAngle);
  
  return (
    <div style={{ 
      display: 'flex', 
      flexDirection: 'column', 
      alignItems: 'center',
      minWidth: size,
      height: '100%',
      justifyContent: 'flex-start', // Changed to eliminate gap
      position: 'relative'
    }}>
      {/* Gauge SVG - positioned lower with overflow protection */}
      <div style={{ position: 'relative', overflow: 'visible', marginTop: '15px' }}>
        <svg width={size} height={size * 0.6} viewBox={`-15 -10 ${size + 30} ${size * 0.6 + 25}`}>
          {/* Horizontal 180-degree gauge: 9 o'clock to 3 o'clock */}
          {(() => {
            const createHorizontalPath = (startAngle: number, endAngle: number) => {
              // CRITICAL: Validate inputs to prevent NaN in SVG path
              if (startAngle == null || endAngle == null || isNaN(startAngle) || isNaN(endAngle)) {
                console.warn('Invalid angles for SVG path:', { startAngle, endAngle });
                return `M 0 0 L 0 0`; // Return empty path
              }
              
              // Convert to horizontal orientation: 0° = 9 o'clock (left), 180° = 3 o'clock (right)
              const startRad = (startAngle + 180) * (Math.PI / 180);
              const endRad = (endAngle + 180) * (Math.PI / 180);
              
              const x1 = centerX + radius * Math.cos(startRad);
              const y1 = centerY + radius * Math.sin(startRad);
              const x2 = centerX + radius * Math.cos(endRad);
              const y2 = centerY + radius * Math.sin(endRad);
              
              // Additional safety check for calculated values
              if (isNaN(x1) || isNaN(y1) || isNaN(x2) || isNaN(y2)) {
                console.warn('NaN in calculated SVG coordinates:', { x1, y1, x2, y2 });
                return `M 0 0 L 0 0`;
              }
              
              const largeArcFlag = (endAngle - startAngle) > 180 ? 1 : 0;
              
              return `M ${x1.toFixed(2)} ${y1.toFixed(2)} A ${radius} ${radius} 0 ${largeArcFlag} 1 ${x2.toFixed(2)} ${y2.toFixed(2)}`;
            };
            
            return (
              <>
                {/* Blue: 0-0.8 ACWR (9 o'clock to ~10:30) */}
                <path
                  d={createHorizontalPath(0, 72)}
                  fill="none"
                  stroke="#3498db"
                  strokeWidth={strokeWidth}
                  opacity={0.9}
                />
                
                {/* Green: 0.8-1.3 ACWR (~10:30 to ~1:30) */}
                <path
                  d={createHorizontalPath(72, 117)}
                  fill="none"
                  stroke="#2ecc71"
                  strokeWidth={strokeWidth}
                  opacity={0.9}
                />
                
                {/* Orange: 1.3-1.5 ACWR (~1:30 to ~2:15) */}
                <path
                  d={createHorizontalPath(117, 135)}
                  fill="none"
                  stroke="#e67e22"
                  strokeWidth={strokeWidth}
                  opacity={0.9}
                />
                
                {/* Red: 1.5-2.0 ACWR (~2:15 to 3 o'clock) */}
                <path
                  d={createHorizontalPath(135, 180)}
                  fill="none"
                  stroke="#e74c3c"
                  strokeWidth={strokeWidth}
                  opacity={0.9}
                />
              </>
            );
          })()}
          
          {/* External Needle (Green) - lighter weight */}
          <line
            x1={centerX}
            y1={centerY}
            x2={externalNeedleX}
            y2={externalNeedleY}
            stroke="#2ecc71" // Green for external
            strokeWidth={2.5}
            strokeLinecap="round"
          />
          
          {/* Internal Needle (Blue) - lighter weight */}
          <line
            x1={centerX}
            y1={centerY}
            x2={internalNeedleX}
            y2={internalNeedleY}
            stroke="#3498db" // Blue for internal
            strokeWidth={2.5}
            strokeLinecap="round"
          />
          
          {/* Center dot - bigger */}
          <circle
            cx={centerX}
            cy={centerY}
            r={5}
            fill="#2c3e50"
          />
          
          {/* Scientific tick marks and labels - more detailed */}
          {(() => {
            const ticks = [];
            // Major ticks every 0.2 units, minor ticks every 0.1 units
            for (let i = 0; i <= 20; i++) { // 0, 0.1, 0.2, ..., 2.0
              const value = i * 0.1;
              const angle = (value / 2.0) * 180; // Convert to angle (0-180°)
              const tickAngle = (angle + 180) * (Math.PI / 180); // Horizontal orientation
              
              const isMajorTick = i % 2 === 0; // Every 0.2 units
              const tickOuterRadius = radius + (isMajorTick ? 12 : 8);
              const tickInnerRadius = radius + (isMajorTick ? 4 : 6);
              
              const outerX = centerX + tickOuterRadius * Math.cos(tickAngle);
              const outerY = centerY + tickOuterRadius * Math.sin(tickAngle);
              const innerX = centerX + tickInnerRadius * Math.cos(tickAngle);
              const innerY = centerY + tickInnerRadius * Math.sin(tickAngle);
              
              ticks.push(
                <g key={value}>
                  {/* Tick mark */}
                  <line
                    x1={innerX}
                    y1={innerY}
                    x2={outerX}
                    y2={outerY}
                    stroke="#666"
                    strokeWidth={isMajorTick ? 2 : 1}
                    opacity={isMajorTick ? 0.8 : 0.5}
                  />
                  {/* Label for major ticks */}
                  {isMajorTick && (
                    <text
                      x={centerX + (radius + 20) * Math.cos(tickAngle)}
                      y={centerY + (radius + 20) * Math.sin(tickAngle) + 4}
                      fill="#666"
                      fontSize="10"
                      textAnchor="middle"
                      fontWeight="500"
                    >
                      {value === 0 ? "0" : value === 1.0 ? "1.0" : value === 2.0 ? "2.0" : (typeof value === 'number' && !isNaN(value) ? value.toFixed(1) : "N/A")}
                    </text>
                  )}
                </g>
              );
            }
            return ticks;
          })()}
        </svg>
      </div>
      
      {/* External values positioned outside gauge - eliminate gap */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        width: '100%', 
        marginTop: '-5px', // Negative margin to pull values closer to gauge
        padding: '0 2px'
      }}>
        {/* External value (Green) */}
        <div style={{ textAlign: 'center' }}>
          <div style={{
            fontSize: '1.1rem',
            fontWeight: 'bold',
            color: '#2ecc71', // Green for external
            fontFamily: 'Arial, sans-serif'
          }}>
            {typeof externalValue === 'number' && !isNaN(externalValue) ? externalValue.toFixed(2) : 'N/A'}
          </div>
          <div style={{
            fontSize: '0.7rem',
            color: '#6b7280',
            fontWeight: '600',
            textTransform: 'capitalize',
            letterSpacing: '0.3px'
          }}>
            External
          </div>
        </div>
        
        {/* Internal value (Blue) */}
        <div style={{ textAlign: 'center' }}>
          <div style={{
            fontSize: '1.1rem',
            fontWeight: 'bold',
            color: '#3498db', // Blue for internal
            fontFamily: 'Arial, sans-serif'
          }}>
            {typeof internalValue === 'number' && !isNaN(internalValue) ? internalValue.toFixed(2) : 'N/A'}
          </div>
          <div style={{
            fontSize: '0.7rem',
            color: '#6b7280',
            fontWeight: '600',
            textTransform: 'capitalize',
            letterSpacing: '0.3px'
          }}>
            Internal
          </div>
        </div>
      </div>
    </div>
  );
};

// Enhanced Balance Bar with Training Load Integration
const BalanceIndicator: React.FC<{
  divergence: number;
  trainingLoad: number;
  avgTrainingLoad: number;
  width?: number;
}> = ({ divergence, trainingLoad, avgTrainingLoad, width = 180 }) => {
  
  // Calculate balance position (-1 to +1 range)
  const normalizedDivergence = Math.max(-0.5, Math.min(0.5, divergence)) / 0.5; // Clamp to -1 to +1
  
  // Training load intensity (relative to average)
  const loadIntensity = avgTrainingLoad > 0 ? trainingLoad / avgTrainingLoad : 1;
  const intensityColor = loadIntensity > 1.3 ? '#e74c3c' : loadIntensity > 1.1 ? '#e67e22' : '#2ecc71';
  
  // Bar position (center at 50%, range 15% to 85%)
  const indicatorPosition = 50 + (normalizedDivergence * 35); // 35% max deviation from center
  
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      minWidth: width,
      height: '100%',
      justifyContent: 'flex-start', // Changed to eliminate gap
      position: 'relative'
    }}>
      {/* Scientific instrument-style balance bar - aligned with gauge axis */}
      <div style={{ width: '100%', height: '50px', position: 'relative', marginTop: '25px' }}>
        <svg width="100%" height="100%" viewBox={`0 0 ${width} 50`}>
          {/* Scientific instrument background track - dynamic width */}
          <rect x="10" y="20" width={width - 20} height="8" rx="4" fill="#f8f9fa" stroke="#e9ecef" strokeWidth="1" />
          
          {/* Color segments - extended to both ends for full scale coverage */}
          <rect x="10" y="20" width={(width - 20) * 0.2} height="8" rx="4" fill="#3498db" opacity="0.7" />
          <rect x={10 + (width - 20) * 0.2} y="20" width={(width - 20) * 0.6} height="8" rx="0" fill="#2ecc71" opacity="0.7" />
          <rect x={10 + (width - 20) * 0.8} y="20" width={(width - 20) * 0.2} height="8" rx="4" fill="#e74c3c" opacity="0.7" />
          
          {/* Scientific instrument indicator - reversed for risk assessment */}
          <circle
            cx={width/2 - (normalizedDivergence * (width - 20) * 0.4)} // Dynamic positioning for full scale
            cy="24"
            r="4" // Restored indicator size
            fill="#2c3e50"
            stroke="white"
            strokeWidth="1.5"
          />
          
          {/* Precision crosshair indicator */}
          <line
            x1={width/2 - (normalizedDivergence * (width - 20) * 0.4) - 6}
            y1="24"
            x2={width/2 - (normalizedDivergence * (width - 20) * 0.4) + 6}
            y2="24"
            stroke="#2c3e50"
            strokeWidth="1"
            opacity="0.8"
          />
          <line
            x1={width/2 - (normalizedDivergence * (width - 20) * 0.4)}
            y1="18"
            x2={width/2 - (normalizedDivergence * (width - 20) * 0.4)}
            y2="30"
            stroke="#2c3e50"
            strokeWidth="1"
            opacity="0.8"
          />
          
          {/* Enhanced scale labels - extended to both ends */}
          {(() => {
            const ticks = [];
            const values = [-0.6, -0.5, -0.4, -0.3, -0.2, -0.1, 0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6]; // Full scale to both ends
            
            for (let i = 0; i < values.length; i++) {
              const value = values[i];
              const position = width/2 - (value / 0.6) * (width - 20) * 0.4; // Dynamic positioning for full scale
              const isMajorTick = value % 0.1 === 0 && (value === 0 || value % 0.2 === 0); // Major ticks at 0, ±0.2, ±0.4, ±0.6
              
              ticks.push(
                <g key={value}>
                  {/* Scientific instrument tick marks - restored */}
                  <line
                    x1={position}
                    y1={isMajorTick ? "32" : "35"}
                    x2={position}
                    y2={isMajorTick ? "40" : "37"}
                    stroke="#666"
                    strokeWidth={isMajorTick ? "1.5" : "0.8"}
                    opacity={isMajorTick ? "0.9" : "0.6"}
                  />
                  {/* Scientific instrument labels - restored */}
                  {isMajorTick && (
                    <text
                      x={position}
                      y="46"
                      fill="#666"
                      fontSize="8"
                      textAnchor="middle"
                      fontWeight="500"
                      fontFamily="monospace"
                    >
                      {value === 0 ? "0" : (typeof value === 'number' && !isNaN(value) ? value.toFixed(1) : "N/A")}
                    </text>
                  )}
                </g>
              );
            }
            return ticks;
          })()}
        </svg>
        
        {/* Scientific instrument numeric display - restored */}
        <div style={{
          position: 'absolute',
          top: '15%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          textAlign: 'center'
        }}>
          <div style={{
            fontSize: '1.2rem', // Restored size
            fontWeight: 'bold',
            color: '#2c3e50',
            fontFamily: 'monospace', // Scientific instrument font
            letterSpacing: '0.5px'
          }}>
            {typeof divergence === 'number' && !isNaN(divergence) ? divergence.toFixed(2) : 'N/A'}
          </div>
        </div>
      </div>
      
      {/* Labels below balance bar - add space from tick labels */}
      <div style={{ textAlign: 'center', marginTop: '5px' }}>
        <div style={{
          fontSize: '0.75rem', // Match gauge label size
          color: '#6b7280',
          fontWeight: '600',
          textTransform: 'uppercase',
          letterSpacing: '0.3px',
          lineHeight: '1'
        }}>
          Economy
        </div>
        <div style={{
          fontSize: '0.7rem', // Match gauge sublabel size
          color: '#9ca3af',
          lineHeight: '1'
        }}>
          Divergence
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
      padding: '1rem',
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
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
          borderRadius: '0.5rem', // Match dashboard cards
          padding: '0.75rem',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          textAlign: 'center',
          boxShadow: '0 1px 2px rgba(0, 0, 0, 0.05)', // Match dashboard cards
          backdropFilter: 'blur(10px)',
          position: 'relative',
          overflow: 'hidden',
          minHeight: '80px', // Compact height
          backgroundImage: `url('/static/training-monkey-runner.webp')`,
          backgroundSize: 'cover',
          backgroundPosition: 'center 30%',
          backgroundRepeat: 'no-repeat'
        }}>
          {/* Overlay for better text readability */}
          <div style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(255, 255, 255, 0.15)',
            pointerEvents: 'none'
          }} />

          <div style={{ position: 'relative', zIndex: 2 }}>
            <h1 style={{
              margin: '0',
              fontSize: '1.1rem', // Reduced from 2rem
              fontWeight: '900',
              color: 'white',
              WebkitTextStroke: '1px #2c3e50', // Dashboard dark color
              textShadow: '2px 2px 4px rgba(0, 0, 0, 0.5)',
              letterSpacing: '0em',
              lineHeight: '1.1',
              textTransform: 'capitalize',
              fontFamily: 'Arial, sans-serif'
            }}>
              Your Training Monkey
            </h1>

            <p style={{
              margin: '0.25rem 0 0 0', // Reduced margin
              fontSize: '0.7rem', // Reduced from 1.25rem
              color: 'white',
              fontWeight: '600',
              fontStyle: 'italic',
              WebkitTextStroke: '0.25px #2c3e50',
              letterSpacing: '0.2px',
              textShadow: '0 1px 2px rgba(255, 255, 255, 0.8)'
            }}>
              Train that monkey on your back
            </p>
            
          </div>
        </div>

        {/* Card 2: Training Balance (with Gauges) */}
        <div style={{
          backgroundColor: 'white',
          borderRadius: '0.5rem',
          padding: '0.75rem',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          boxShadow: '0 1px 2px rgba(0, 0, 0, 0.05)',
          minHeight: '80px' // Maintaining original height constraint
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
            gap: '0.5rem', // Add space between gauge and bar
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
                size={100}
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
        <div style={{
          backgroundColor: 'white',
          borderRadius: '0.5rem',
          padding: '0.75rem',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          boxShadow: '0 1px 2px rgba(0, 0, 0, 0.05)',
          minHeight: '80px'
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
          padding: '0.75rem',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: '0.5rem',
          boxShadow: '0 1px 2px rgba(0, 0, 0, 0.05)',
          minHeight: '80px'
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