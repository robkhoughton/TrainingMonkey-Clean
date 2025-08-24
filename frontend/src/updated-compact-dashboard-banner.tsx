import React, { useState } from 'react';

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

// Mini Strain Gauge Component
interface MiniStrainGaugeProps {
  value: number;
  max: number;
  label: string;
  subLabel: string;
  type: 'external' | 'internal';
  size?: number;
}

const MiniStrainGauge: React.FC<MiniStrainGaugeProps> = ({
  value,
  max = 2.0,
  label,
  subLabel,
  type,
  size = 55
}) => {
  // Calculate angle (gauge spans 180 degrees)
  const clampedValue = Math.max(0, Math.min(max, value));
  const angle = (clampedValue / max) * 180;
  
  // Color zones based on ACWR thresholds
  const getColorForValue = (val: number) => {
    if (val < 0.8) return '#e67e22'; // Orange - undertraining
    if (val <= 1.3) return '#2ecc71'; // Green - optimal
    if (val <= 1.5) return '#e67e22'; // Orange - elevated risk
    return '#e74c3c'; // Red - high risk
  };
  
  // Gauge color segments
  const segments = [
    { start: 0, end: 72, color: '#e67e22' }, // 0-0.8 (undertraining)
    { start: 72, end: 117, color: '#2ecc71' }, // 0.8-1.3 (optimal)
    { start: 117, end: 135, color: '#e67e22' }, // 1.3-1.5 (elevated)
    { start: 135, end: 180, color: '#e74c3c' } // 1.5+ (high risk)
  ];
  
  const radius = (size - 8) / 2;
  const strokeWidth = 6;
  const centerX = size / 2;
  const centerY = size / 2;
  
  // Generate arc path
  const createArcPath = (startAngle: number, endAngle: number) => {
    const start = (startAngle - 90) * (Math.PI / 180);
    const end = (endAngle - 90) * (Math.PI / 180);
    
    const x1 = centerX + radius * Math.cos(start);
    const y1 = centerY + radius * Math.sin(start);
    const x2 = centerX + radius * Math.cos(end);
    const y2 = centerY + radius * Math.sin(end);
    
    const largeArc = endAngle - startAngle > 180 ? 1 : 0;
    
    return `M ${x1} ${y1} A ${radius} ${radius} 0 ${largeArc} 1 ${x2} ${y2}`;
  };
  
  // Needle position
  const needleAngle = (angle - 90) * (Math.PI / 180);
  const needleLength = radius - 3;
  const needleX = centerX + needleLength * Math.cos(needleAngle);
  const needleY = centerY + needleLength * Math.sin(needleAngle);
  
  return (
    <div style={{ 
      display: 'flex', 
      flexDirection: 'column', 
      alignItems: 'center',
      minWidth: size,
      height: '100%',
      justifyContent: 'space-between'
    }}>
      {/* Gauge SVG - maximized within card height */}
      <svg width={size} height={size * 0.6} viewBox={`0 0 ${size} ${size * 0.6}`}>
        {/* Background segments */}
        {segments.map((segment, index) => (
          <path
            key={index}
            d={createArcPath(segment.start, segment.end)}
            fill="none"
            stroke={segment.color}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            opacity={0.8}
          />
        ))}
        
        {/* Needle */}
        <line
          x1={centerX}
          y1={centerY}
          x2={needleX}
          y2={needleY}
          stroke="#2c3e50"
          strokeWidth={2}
          strokeLinecap="round"
        />
        
        {/* Center dot */}
        <circle
          cx={centerX}
          cy={centerY}
          r={2}
          fill="#2c3e50"
        />
        
        {/* Scale labels - smaller and positioned better */}
        <text
          x="15%"
          y="90%"
          fill="#666"
          fontSize={size * 0.1}
          textAnchor="middle"
        >
          0.8
        </text>
        <text
          x="50%"
          y="95%"
          fill="#666"
          fontSize={size * 0.1}
          textAnchor="middle"
        >
          1.3
        </text>
        <text
          x="85%"
          y="90%"
          fill="#666"
          fontSize={size * 0.1}
          textAnchor="middle"
        >
          1.5
        </text>
      </svg>
      
      {/* Value display - compact */}
      <div style={{ textAlign: 'center', marginTop: '2px' }}>
        <div style={{
          fontSize: '0.85rem',
          fontWeight: 'bold',
          color: getColorForValue(value),
          marginBottom: '1px'
        }}>
          {value ? value.toFixed(2) : 'N/A'}
        </div>
        <div style={{
          fontSize: '0.6rem',
          color: '#6b7280',
          fontWeight: '600',
          textTransform: 'uppercase',
          letterSpacing: '0.3px',
          lineHeight: '1.1'
        }}>
          {label}
        </div>
        <div style={{
          fontSize: '0.55rem',
          color: '#9ca3af',
          lineHeight: '1'
        }}>
          {subLabel}
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
}> = ({ divergence, trainingLoad, avgTrainingLoad }) => {
  
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
      minWidth: 65,
      height: '100%',
      justifyContent: 'space-between'
    }}>
      {/* Balance bar - maximized height */}
      <div style={{ width: '100%', height: '35px', position: 'relative', marginTop: '4px' }}>
        <svg width="100%" height="100%" viewBox="0 0 65 35">
          {/* Background track */}
          <rect x="8" y="15" width="49" height="6" rx="3" fill="#e5e7eb" />
          
          {/* Color segments */}
          <rect x="8" y="15" width="14" height="6" rx="3" fill="#e74c3c" opacity="0.7" />
          <rect x="22" y="15" width="21" height="6" rx="0" fill="#2ecc71" opacity="0.7" />
          <rect x="43" y="15" width="14" height="6" rx="3" fill="#3498db" opacity="0.7" />
          
          {/* Training load intensity ring around indicator */}
          <circle
            cx={indicatorPosition * 0.65} // Scale to SVG coordinate system
            cy="18"
            r="5"
            fill="none"
            stroke={intensityColor}
            strokeWidth="2"
            opacity="0.6"
          />
          
          {/* Main indicator dot */}
          <circle
            cx={indicatorPosition * 0.65}
            cy="18"
            r="3"
            fill="#2c3e50"
            stroke="white"
            strokeWidth="1"
          />
          
          {/* Scale labels */}
          <text x="8" y="13" fill="#666" fontSize="4" textAnchor="middle">High Risk</text>
          <text x="20" y="13" fill="#666" fontSize="4" textAnchor="middle">Moderate</text>
          <text x="32.5" y="13" fill="#666" fontSize="4" textAnchor="middle">Balanced</text>
          <text x="45" y="13" fill="#666" fontSize="4" textAnchor="middle">Efficient</text>
          <text x="57" y="13" fill="#666" fontSize="4" textAnchor="middle">Adaptation</text>
          
          {/* Training load indicator */}
          <text x="32.5" y="30" fill={intensityColor} fontSize="4" textAnchor="middle" fontWeight="bold">
            Load: {loadIntensity.toFixed(1)}x
          </text>
        </svg>
      </div>
      
      {/* Value display */}
      <div style={{ textAlign: 'center', marginTop: '1px' }}>
        <div style={{
          fontSize: '0.85rem',
          fontWeight: 'bold',
          color: '#3498db',
          marginBottom: '1px'
        }}>
          {divergence ? divergence.toFixed(2) : 'N/A'}
        </div>
        <div style={{
          fontSize: '0.6rem',
          color: '#6b7280',
          fontWeight: '600',
          textTransform: 'uppercase',
          letterSpacing: '0.3px',
          lineHeight: '1.1'
        }}>
          Balance
        </div>
        <div style={{
          fontSize: '0.55rem',
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
              textTransform: 'uppercase',
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
          {/* Card title */}
          <h3 style={{
            margin: '0 0 0.3rem 0',
            fontSize: '0.95rem',
            fontWeight: '600',
            color: colors.dark,
            textAlign: 'center'
          }}>
            Training Balance
          </h3>

          {/* Gauges container - maximized within remaining space */}
          <div style={{ 
            display: 'flex', 
            justifyContent: 'space-around', 
            alignItems: 'stretch',
            gap: '0.5rem',
            flex: 1,
            minHeight: '50px' // Ensure minimum space for gauges
          }}>
            <MiniStrainGauge
              value={metrics?.externalAcwr || 0}
              max={2.0}
              label="External"
              subLabel="Strain"
              type="external"
              size={55}
            />
            
            <MiniStrainGauge
              value={metrics?.internalAcwr || 0}
              max={2.0}
              label="Internal"
              subLabel="Strain"
              type="internal"
              size={55}
            />
            
            <BalanceIndicator
              divergence={metrics?.normalizedDivergence || 0}
              trainingLoad={metrics?.sevenDayAvgLoad || 0}
              avgTrainingLoad={avgTrainingLoad}
            />
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
          <h3 style={{
            margin: '0 0 0.5rem 0',
            fontSize: '0.95rem', // Matches Training Balance
            fontWeight: '600',
            color: colors.dark
          }}>
            Recovery Status
          </h3>

          <div style={{ display: 'flex', justifyContent: 'space-around', alignItems: 'center' }}>
            <div style={{ textAlign: 'center' }}>
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

            <div style={{ textAlign: 'center' }}>
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
                {metrics?.sevenDayAvgLoad ? (metrics.sevenDayAvgLoad * 7).toFixed(1) : "N/A"}
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
                {metrics?.sevenDayAvgTrimp ? (metrics.sevenDayAvgTrimp * 7).toFixed(0) : "N/A"}
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