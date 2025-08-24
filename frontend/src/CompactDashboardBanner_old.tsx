import React, { useState } from 'react';

// TypeScript interfaces for proper type safety
// interface SyncStatus {
//   status: 'ready' | 'syncing' | 'success' | 'error';
//   message: string;
// }

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

  // Status helper functions
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

        {/* Card 2: Training Load Status */}
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
            fontSize: '0.95rem', // Slightly larger for 1.5fr width
            fontWeight: '600',
            color: colors.dark
          }}>
            Training Load Status
          </h3>

          <div style={{ display: 'flex', justifyContent: 'space-around', alignItems: 'center' }}>
            <div style={{ textAlign: 'center' }}>
              <p style={{ margin: '0', fontSize: '0.75rem', color: '#6b7280' }}>External ACWR</p>
              <p style={{
                margin: '0',
                fontSize: '1.1rem', // Slightly larger for better proportion
                fontWeight: 'bold',
                color: getAcwrStatus(metrics.externalAcwr).color
              }}>
                {metrics.externalAcwr ? metrics.externalAcwr.toFixed(2) : "N/A"}
              </p>
            </div>
            <div style={{ textAlign: 'center' }}>
              <p style={{ margin: '0', fontSize: '0.75rem', color: '#6b7280' }}>Internal ACWR</p>
              <p style={{
                margin: '0',
                fontSize: '1.1rem',
                fontWeight: 'bold',
                color: getAcwrStatus(metrics.internalAcwr).color
              }}>
                {metrics.internalAcwr ? metrics.internalAcwr.toFixed(2) : "N/A"}
              </p>
            </div>
            <div style={{ textAlign: 'center' }}>
              <p style={{ margin: '0', fontSize: '0.75rem', color: '#6b7280' }}>Divergence</p>
              <p style={{
                margin: '0',
                fontSize: '1.1rem',
                fontWeight: 'bold',
                color: getDivergenceStatus(metrics.normalizedDivergence).color
              }}>
                {metrics.normalizedDivergence ? metrics.normalizedDivergence.toFixed(2) : "N/A"}
              </p>
            </div>
          </div>

          <div style={{
            fontSize: '0.7rem', // Matches Recovery Status subtext
            color: getDivergenceStatus(metrics.normalizedDivergence).color,
            fontWeight: '500',
            textAlign: 'center'
          }}>
            {getDivergenceStatus(metrics.normalizedDivergence).label}
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
            fontSize: '0.95rem', // Matches Training Load Status
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
                color: metrics.daysSinceRest > 6 ? colors.warning : colors.secondary
              }}>
                {metrics.daysSinceRest}
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
                {metrics.sevenDayAvgLoad ? (metrics.sevenDayAvgLoad * 7).toFixed(1) : "N/A"}
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
                {metrics.sevenDayAvgTrimp ? (metrics.sevenDayAvgTrimp * 7).toFixed(0) : "N/A"}
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
            fontSize: '0.7rem', // Matches Training Load Status
            color: metrics.daysSinceRest > 6 ? colors.warning : colors.secondary, // CONSISTENT COLORS
            fontWeight: '500',
            textAlign: 'center'
          }}>
            {metrics.daysSinceRest > 6 ? "Need rest" : "On track"}
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