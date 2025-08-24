import React, { useState } from 'react';
import styles from './TrainingLoadDashboard.module.css';

interface ManualSyncProps {
  onSyncComplete?: () => void;
}

const ManualSyncComponent: React.FC<ManualSyncProps> = ({ onSyncComplete }) => {
  const [syncPeriod, setSyncPeriod] = useState(7);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const syncOptions = [
    { value: 7, label: '7 days (Quick sync)', estimated: '~30 seconds' },
    { value: 30, label: '30 days (Standard)', estimated: '~2 minutes' },
    { value: 90, label: '90 days (Full sync)', estimated: '~5 minutes' },
    { value: 365, label: '1 year (Complete rebuild)', estimated: '~10 minutes' }
  ];

  const handleSync = async () => {
    setIsLoading(true);
    setResult(null);
    setError(null);

    try {
      const response = await fetch('/sync-with-auto-refresh', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          days: syncPeriod
        })
      });

      const data = await response.json();

      if (data.success) {
        setResult(data);
        // Call the callback to refresh dashboard data
        if (onSyncComplete) {
          setTimeout(() => {
            onSyncComplete();
          }, 1000);
        }
      } else {
        setError(data.error || 'Sync failed');
      }
    } catch (err) {
      setError('Network error: ' + (err instanceof Error ? err.message : String(err)));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={styles.chartContainer} style={{
      background: 'linear-gradient(135deg, #FC5200, #ff8c00)',
      color: 'white',
      marginBottom: '1rem'
    }}>
      <h2 className={styles.chartTitle} style={{ color: 'white', marginBottom: '1rem' }}>
        🔄 Manual Strava Sync
      </h2>

      <div style={{
        display: 'flex',
        gap: '15px',
        alignItems: 'flex-end',
        flexWrap: 'wrap',
        marginBottom: '1rem'
      }}>
        <div style={{ flex: 1, minWidth: '250px' }}>
          <label style={{
            display: 'block',
            marginBottom: '8px',
            fontSize: '14px',
            opacity: 0.9,
            color: 'white'
          }}>
            Select sync period:
          </label>
          <select
            value={syncPeriod}
            onChange={(e) => setSyncPeriod(parseInt(e.target.value))}
            disabled={isLoading}
            style={{
              width: '100%',
              padding: '12px',
              border: 'none',
              borderRadius: '8px',
              fontSize: '14px',
              background: 'rgba(255, 255, 255, 0.9)',
              color: '#333'
            }}
          >
            {syncOptions.map(option => (
              <option key={option.value} value={option.value}>
                {option.label} - {option.estimated}
              </option>
            ))}
          </select>
        </div>

        <button
          onClick={handleSync}
          disabled={isLoading}
          style={{
            padding: '12px 24px',
            background: 'rgba(255, 255, 255, 0.2)',
            color: 'white',
            border: '2px solid rgba(255, 255, 255, 0.3)',
            borderRadius: '8px',
            fontWeight: '600',
            cursor: isLoading ? 'not-allowed' : 'pointer',
            transition: 'all 0.3s ease',
            whiteSpace: 'nowrap',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            opacity: isLoading ? 0.6 : 1
          }}
          onMouseEnter={(e) => {
            if (!isLoading) {
              e.currentTarget.style.background = 'rgba(255, 255, 255, 0.3)';
              e.currentTarget.style.transform = 'translateY(-1px)';
            }
          }}
          onMouseLeave={(e) => {
            if (!isLoading) {
              e.currentTarget.style.background = 'rgba(255, 255, 255, 0.2)';
              e.currentTarget.style.transform = 'translateY(0)';
            }
          }}
        >
          {isLoading ? (
            <>
              <div style={{
                width: '16px',
                height: '16px',
                border: '2px solid rgba(255, 255, 255, 0.3)',
                borderTop: '2px solid white',
                borderRadius: '50%',
                animation: 'spin 1s linear infinite'
              }} />
              Syncing...
            </>
          ) : (
            <>
              🚀 Start Sync
            </>
          )}
        </button>
      </div>

      {isLoading && (
        <div style={{
          padding: '12px',
          background: 'rgba(255, 255, 255, 0.1)',
          borderRadius: '6px',
          fontSize: '14px',
          marginBottom: '1rem',
          border: '1px solid rgba(255, 255, 255, 0.2)'
        }}>
          <strong>⚠️ Please wait:</strong> Syncing {syncPeriod} days of activities.
          This process may take several minutes depending on your activity count.
          Do not refresh the page.
        </div>
      )}

      {result && (
        <div style={{
          padding: '12px',
          background: 'rgba(72, 187, 120, 0.2)',
          borderRadius: '6px',
          fontSize: '14px',
          marginBottom: '1rem',
          border: '1px solid rgba(72, 187, 120, 0.3)'
        }}>
          <strong>✅ Sync completed!</strong><br/>
          {result.message}<br/>
          <small>Range: {result.date_range}</small>
        </div>
      )}

      {error && (
        <div style={{
          padding: '12px',
          background: 'rgba(245, 101, 101, 0.2)',
          borderRadius: '6px',
          fontSize: '14px',
          marginBottom: '1rem',
          border: '1px solid rgba(245, 101, 101, 0.3)'
        }}>
          <strong>❌ Sync failed:</strong><br/>
          {error}
        </div>
      )}

      <div style={{
        fontSize: '12px',
        opacity: 0.8,
        lineHeight: '1.4'
      }}>
        <strong>💡 Tip:</strong> Use 7-day sync for regular updates.
        Use longer periods only when setting up or if you notice missing activities.
      </div>

      {/* Add keyframes for spin animation */}
      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

export default ManualSyncComponent;