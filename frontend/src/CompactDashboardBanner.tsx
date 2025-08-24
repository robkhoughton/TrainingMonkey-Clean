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
  size = 110 // Increased even more to maximize space
}) => {
  // Calculate angle (gauge spans 180 degrees)
  const clampedValue = Math.max(0, Math.min(max, value));
  const angle = (clampedValue / max) * 180;
  
  // Color zones based on ACWR thresholds - matching chart colors
  const getColorForValue = (val: number) => {
    if (val < 0.8) return '#3498db'; // Blue - low load (matching chart)
    if (val <= 1.3) return '#2ecc71'; // Green - optimal (matching chart)
    if (val <= 1.5) return '#e67e22'; // Orange - moderate risk (matching chart)
    return '#e74c3c'; // Red - high risk (matching chart)
  };
  
  const radius = (size - 15) / 2; // Increased radius for bigger gauge
  const strokeWidth = 10; // Increased stroke width for better visibility
  const centerX = size / 2;
  const centerY = size / 2;
  
  // Needle position - adjusted for horizontal gauge (9 o'clock to 3 o'clock)
  const needleAngle = (angle + 180) * (Math.PI / 180); // Offset by 180° for horizontal orientation
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
      justifyContent: 'center',
      position: 'relative'
    }}>
      {/* Gauge SVG - maximized */}
      <div style={{ position: 'relative' }}>
        <svg width={size} height={size * 0.65} viewBox={`0 0 ${size} ${size * 0.65}`}>
          {/* Horizontal 180-degree gauge: 9 o'clock to 3 o'clock */}
          {(() => {
            const createHorizontalPath = (startAngle: number, endAngle: number) => {
              // Convert to horizontal orientation: 0° = 9 o'clock (left), 180° = 3 o'clock (right)
              const startRad = (startAngle + 180) * (Math.PI / 180);
              const endRad = (endAngle + 180) * (Math.PI / 180);
              
              const x1 = centerX + radius * Math.cos(startRad);
              const y1 = centerY + radius * Math.sin(startRad);
              const x2 = centerX + radius * Math.cos(endRad);
              const y2 = centerY + radius * Math.sin(endRad);
              
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
          
          {/* Needle - thicker for bigger gauge */}
          <line
            x1={centerX}
            y1={centerY}
            x2={needleX}
            y2={needleY}
            stroke="#2c3e50"
            strokeWidth={4} // Thicker needle for bigger gauge
            strokeLinecap="round"
          />
          
          {/* Center dot - bigger */}
          <circle
            cx={centerX}
            cy={centerY}
            r={4} // Bigger center dot
            fill="#2c3e50"
          />
          
          {/* Scale labels positioned properly for horizontal gauge - simplified */}
          {/* Tick marks every 0.5 units around the outside edge */}
          {(() => {
            const ticks = [];
            for (let i = 0; i <= 4; i++) { // 0, 0.5, 1.0, 1.5, 2.0
              const value = i * 0.5;
              const angle = (value / 2.0) * 180; // Convert to angle (0-180°)
              const tickAngle = (angle + 180) * (Math.PI / 180); // Horizontal orientation
              
              // Outer tick position
              const tickOuterRadius = radius + 8;
              const tickInnerRadius = radius + 3;
              
              const outerX = centerX + tickOuterRadius * Math.cos(tickAngle);
              const outerY = centerY + tickOuterRadius * Math.sin(tickAngle);
              const innerX = centerX + tickInnerRadius * Math.cos(tickAngle);
              const innerY = centerY + tickInnerRadius * Math.sin(tickAngle);
              
              // Label position
              const labelRadius = radius + 15;
              const labelX = centerX + labelRadius * Math.cos(tickAngle);
              const labelY = centerY + labelRadius * Math.sin(tickAngle);
              
              ticks.push(
                <g key={value}>
                  {/* Tick mark - all the same */}
                  <line
                    x1={innerX}
                    y1={innerY}
                    x2={outerX}
                    y2={outerY}
                    stroke="#666"
                    strokeWidth={1}
                    opacity={0.7}
                  />
                  {/* Label - all the same font */}
                  <text
                    x={labelX}
                    y={labelY + 3}
                    fill="#666"
                    fontSize="7"
                    textAnchor="middle"
                    fontWeight="400"
                  >
                    {value === 0 ? "0" : value === 1.0 ? "1.0" : value.toFixed(1)}
                  </text>
                </g>
              );
            }
            return ticks;
          })()}
        </svg>
        
        {/* Centered numeric value - positioned in middle of gauge - larger font */}
        <div style={{
          position: 'absolute',
          top: '45%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          textAlign: 'center'
        }}>
          <div style={{
            fontSize: '1.3rem', // Larger font for bigger gauge
            fontWeight: 'bold',
            color: getColorForValue(value || 0),
            marginBottom: '2px',
            fontFamily: 'Arial, sans-serif'
          }}>
            {value ? value.toFixed(2) : 'N/A'}
          </div>
        </div>
      </div>
      
      {/* Labels below gauge - reduced spacing */}
      <div style={{ textAlign: 'center', marginTop: '1px' }}>
        <div style={{
          fontSize: '0.75rem', // Slightly larger for bigger gauge
          color: '#6b7280',
          fontWeight: '600',
          textTransform: 'uppercase',
          letterSpacing: '0.3px',
          lineHeight: '1'
        }}>
          {label}
        </div>
        <div style={{
          fontSize: '0.7rem', // Slightly larger
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
      minWidth: 100, // Increased for bigger balance bar
      height: '100%',
      justifyContent: 'center',
      position: 'relative'
    }}>
      {/* Balance bar - much larger and more prominent */}
      <div style={{ width: '100%', height: '45px', position: 'relative', marginTop: '2px' }}>
        <svg width="100%" height="100%" viewBox="0 0 100 45">
          {/* Background track - much larger */}
          <rect x="12" y="18" width="76" height="10" rx="5" fill="#e5e7eb" />
          
          {/* Color segments - matching divergence risk zones */}
          <rect x="12" y="18" width="19" height="10" rx="5" fill="#e74c3c" opacity="0.8" />
          <rect x="31" y="18" width="38" height="10" rx="0" fill="#2ecc71" opacity="0.8" />
          <rect x="69" y="18" width="19" height="10" rx="5" fill="#3498db" opacity="0.8" />
          
          {/* Training load intensity ring around indicator - larger */}
          <circle
            cx={50 + (normalizedDivergence * 25)} // Adjusted for larger scale
            cy="23"
            r="8" // Much larger ring
            fill="none"
            stroke={intensityColor}
            strokeWidth="3"
            opacity="0.7"
          />
          
          {/* Main indicator dot - larger */}
          <circle
            cx={50 + (normalizedDivergence * 25)}
            cy="23"
            r="5" // Much larger indicator
            fill="#2c3e50"
            stroke="white"
            strokeWidth="2"
          />
          
          {/* Scale labels - simplified tick marks below the bar */}
          {(() => {
            const ticks = [];
            const values = [-0.5, -0.25, 0, 0.25, 0.5]; // Divergence range
            
            for (let i = 0; i < values.length; i++) {
              const value = values[i];
              const position = 50 + (value / 0.5) * 25; // Scale to slider position
              
              ticks.push(
                <g key={value}>
                  {/* Tick mark below the bar */}
                  <line
                    x1={position}
                    y1="28"
                    x2={position}
                    y2="33"
                    stroke="#666"
                    strokeWidth="1"
                    opacity="0.7"
                  />
                  {/* Label below tick */}
                  <text
                    x={position}
                    y="38"
                    fill="#666"
                    fontSize="5"
                    textAnchor="middle"
                    fontWeight="400"
                  >
                    {value === 0 ? "0" : value.toFixed(2)}
                  </text>
                </g>
              );
            }
            return ticks;
          })()}
        </svg>
        
        {/* Centered numeric value - positioned in middle like gauges */}
        <div style={{
          position: 'absolute',
          top: '15%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          textAlign: 'center'
        }}>
          <div style={{
            fontSize: '1.4rem', // Larger to match bigger gauges
            fontWeight: 'bold',
            color: '#3498db',
            fontFamily: 'Arial, sans-serif'
          }}>
            {divergence ? divergence.toFixed(2) : 'N/A'}
          </div>
        </div>
      </div>
      
      {/* Labels below balance bar - matching gauge style */}
      <div style={{ textAlign: 'center', marginTop: '1px' }}>
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
            margin: '0 0 0.2rem 0', // Reduced bottom margin to save space
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
              size={110} // Increased to maximize space
            />
            
            <MiniStrainGauge
              value={metrics?.internalAcwr || 0}
              max={2.0}
              label="Internal"
              subLabel="Strain"
              type="internal"
              size={110} // Increased to maximize space
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