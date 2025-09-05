import React, { useState, useEffect } from 'react';

// TypeScript interfaces for proper type safety
interface SyncStatus {
  status: 'ready' | 'syncing' | 'success' | 'error';
  message: string;
}

interface IntegratedDashboardBannerProps {
  dateRange: string;
  setDateRange: (value: string) => void;
  onSyncComplete: () => void;
}

interface SyncResponse {
  success: boolean;
  error?: string;
  message?: string;
  activities_processed?: number;
  date_range?: string;
}

const IntegratedDashboardBanner: React.FC<IntegratedDashboardBannerProps> = ({
  dateRange = '14',
  setDateRange = () => {},
  onSyncComplete = () => {}
}) => {
  const [isSyncing, setIsSyncing] = useState<boolean>(false);
  const [syncStatus, setSyncStatus] = useState<'ready' | 'syncing' | 'success' | 'error'>('ready');
  const [statusMessage, setStatusMessage] = useState<string>('');

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

  // Strava brand color
  const stravaOrange = '#FC5200';

  const handleManualSync = async (): Promise<void> => {
    try {
      setIsSyncing(true);
      setSyncStatus('syncing');
      setStatusMessage('Syncing with Strava...');
      const response: Response = await fetch('/sync-with-auto-refresh', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ days: 30 })
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
      padding: '0.75rem 1.25rem',
      borderRadius: '0.5rem',
      border: 'none',
      fontSize: '0.9rem',
      fontWeight: '500',
      cursor: isSyncing ? 'not-allowed' : 'pointer',
      transition: 'all 0.2s ease',
      minWidth: '140px',
      justifyContent: 'center'
    };

    switch (syncStatus) {
      case 'syncing':
        return {
          ...baseStyle,
          backgroundColor: '#f59e0b',
          color: 'white',
          cursor: 'not-allowed'
        };
      case 'success':
        return {
          ...baseStyle,
          backgroundColor: '#10b981',
          color: 'white'
        };
      case 'error':
        return {
          ...baseStyle,
          backgroundColor: '#ef4444',
          color: 'white'
        };
      default:
        return {
          ...baseStyle,
          backgroundColor: stravaOrange,
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
            width: '1rem',
            height: '1rem',
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

  return (
    <div style={{
      background: 'linear-gradient(135deg, #8B7355 0%, #A0956B 50%, #B8A882 100%)',
      padding: '1.5rem',
      borderRadius: '1rem',
      marginBottom: '1.5rem',
      boxShadow: '0 4px 20px rgba(139, 115, 85, 0.3)'
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

          .period-select:focus {
            outline: none;
            box-shadow: 0 0 0 3px rgba(255, 255, 255, 0.3);
          }
        `}
      </style>

      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr 3fr 1fr',
        gap: '1.5rem',
        alignItems: 'stretch',
        margin: '0 auto'
      }}>

        {/* Left Card - Manual Sync */}
        <div style={{
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
          borderRadius: '0.75rem',
          padding: '1.25rem',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: '1rem',
          boxShadow: '0 2px 10px rgba(0, 0, 0, 0.1)',
          backdropFilter: 'blur(10px)',
          minHeight: '100px'
        }}>
          <div>
            <h3 style={{
              margin: '0',
              fontSize: '1rem',
              fontWeight: '600',
              color: '#2F4F4F'
            }}>
              Data Sync Period
            </h3>

            {/* Sync Period Dropdown */}
            <div style={{ marginBottom: '1rem' }}>
              <label style={{
                display: 'block',
                fontSize: '0.8rem',
                color: '#2F4F4F',
                marginBottom: '0.5rem',
                fontWeight: '500'
              }}>
              </label>
              <select
                style={{
                  padding: '0.5rem',
                  borderRadius: '0.375rem',
                  border: '1px solid #d1d5db',
                  backgroundColor: 'white',
                  fontSize: '0.8rem',
                  color: '#2F4F4F',
                  cursor: 'pointer',
                  width: '100%',
                  textAlign: 'center'
                }}
                defaultValue="30"
              >
                <option value="7">7 Days</option>
                <option value="14">14 Days</option>
                <option value="30">30 Days</option>
                <option value="60">60 Days</option>
                <option value="90">90 Days</option>
              </select>
            </div>

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
                margin: '0.5rem 0 0 0',
                fontSize: '0.8rem',
                color: syncStatus === 'error' ? '#dc2626' :
                       syncStatus === 'success' ? '#059669' : '#6b7280'
              }}>
                {statusMessage}
              </p>
            )}


          </div>

          {/* Powered by Strava - Compliant with Brand Guidelines */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            paddingTop: '0.5rem',
            borderTop: '1px solid #e5e7eb'
          }}>
            <span style={{
              fontSize: '0.8rem',
              fontWeight: '500',
              color: stravaOrange
            }}>
              POWERED BY
            </span>
            <span style={{
              fontSize: '0.9rem',
              fontWeight: 'bold',
              color: stravaOrange,
              letterSpacing: '0.5px'
            }}>
              STRAVA
            </span>
          </div>
        </div>

        {/* Center Card - Your Training Monkey Branding */}
        <div style={{
          // backgroundColor: 'rgba(255, 255, 255, 0.95)', //
          borderRadius: '0.75rem',
          padding: '1rem',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          textAlign: 'center',
          boxShadow: '0 2px 10px rgba(0, 0, 0, 0.1)',
          backdropFilter: 'blur(10px)',
          position: 'relative',
          overflow: 'hidden',
          minHeight: '140px',
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
              fontSize: '2rem',
              fontWeight: '900',
              color: 'white',                           // Clean white text
              WebkitTextStroke: '1px #8B4513',       // Very fine dark brown stroke
              textShadow: '2px 2px 4px rgba(0, 0, 0, 0.5)', // Subtle drop shadow for depth
              letterSpacing: '0em',
              lineHeight: '1.25',
              textTransform: 'uppercase',
              fontFamily: 'Arial, sans-serif',
              fontWeight: '900'
            }}>
              Your Training Monkey
            </h1>

            <p style={{
              margin: '0.75rem 0 0 0',
              fontSize: '1.25rem',
              color: 'white',
              fontWeight: '600',
              fontStyle: 'italic',
              WebkitTextStroke: '0.35px #8B4513',
              letterSpacing: '0.3px',
              textShadow: '0 1px 2px rgba(255, 255, 255, 0.8)'
            }}>
              Train that monkey on your back
            </p>
          </div>
        </div>

        {/* Right Card - Time Period Selector */}
        <div style={{
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
          borderRadius: '0.75rem',
          padding: '1.5rem',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: '0.75rem',
          boxShadow: '0 2px 10px rgba(0, 0, 0, 0.1)',
          backdropFilter: 'blur(10px)',
          minHeight: '140px'
        }}>
          <h3 style={{
            margin: '0',
            fontSize: '1rem',
            fontWeight: '600',
            color: '#2F4F4F'
          }}>
            Time Period
          </h3>

          <select
            value={dateRange}
            onChange={(e) => setDateRange(e.target.value)}
            className="period-select"
            style={{
              padding: '0.5rem',
              borderRadius: '0.375rem',
              border: '1px solid #d1d5db',
              backgroundColor: 'white',
              fontSize: '0.8rem',
              fontWeight: '500',
              color: '#2F4F4F',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
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

          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            fontSize: '0.8rem',
            color: '#696969'
          }}>
            <span>📊</span>
            <span>Chart Range</span>
          </div>
        </div>
      </div>

      {/* Responsive adjustments */}
      <style>
        {`
          @media (max-width: 768px) {
            .banner-grid {
              grid-template-columns: 1fr !important;
              gap: 1rem !important;
            }
          }

          @media (max-width: 1024px) {
            .banner-grid {
              grid-template-columns: 1fr 1fr 1fr !important;
            }
          }
        `}
      </style>
    </div>
  );
};

export default IntegratedDashboardBanner;