import React, { useState, useEffect } from 'react';
import styles from './TrainingLoadDashboard.module.css';

// ─── Quick Journal Modal ───────────────────────────────────────────────────

interface QuickJournalModalProps {
  date: string;           // YYYY-MM-DD
  onDone: () => void;     // called on submit OR skip
}

const QuickJournalModal: React.FC<QuickJournalModalProps> = ({ date, onDone }) => {
  const [energy, setEnergy] = useState<number | null>(null);
  const [rpe, setRpe] = useState<number | null>(null);
  const [pain, setPain] = useState<number | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const complete = energy !== null && rpe !== null && pain !== null;

  const handleSubmit = async () => {
    if (!complete || submitting) return;
    setSubmitting(true);
    try {
      await fetch('/api/journal', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          date,
          energy_level: energy,
          rpe_score: rpe,
          pain_percentage: pain,
        }),
      });
    } catch (_) {
      // Non-blocking — don't prevent the user from continuing
    } finally {
      onDone();
    }
  };

  const btnBase: React.CSSProperties = {
    padding: '6px 0',
    minWidth: '36px',
    border: '1px solid #d1d5db',
    borderRadius: '4px',
    fontSize: '13px',
    fontWeight: '600',
    cursor: 'pointer',
    transition: 'background 0.12s, color 0.12s, border-color 0.12s',
    background: 'white',
    color: '#374151',
  };

  const btnActive: React.CSSProperties = {
    ...btnBase,
    background: '#1B2E4B',
    color: 'white',
    borderColor: '#1B2E4B',
  };

  return (
    <div style={{
      position: 'fixed', inset: 0,
      background: 'rgba(0,0,0,0.45)',
      display: 'flex', alignItems: 'flex-end', justifyContent: 'center',
      zIndex: 1000,
      animation: 'ytm-backdrop-in 0.18s ease',
    }}>
      <style>{`
        @keyframes ytm-backdrop-in { from { opacity: 0 } to { opacity: 1 } }
        @keyframes ytm-sheet-up { from { transform: translateY(40px); opacity: 0 } to { transform: translateY(0); opacity: 1 } }
      `}</style>

      <div style={{
        background: 'white',
        borderRadius: '12px 12px 0 0',
        width: '100%', maxWidth: '560px',
        overflow: 'hidden',
        animation: 'ytm-sheet-up 0.22s cubic-bezier(0.22,1,0.36,1)',
        boxShadow: '0 -8px 32px rgba(0,0,0,0.18)',
      }}>
        {/* Header */}
        <div style={{
          background: 'linear-gradient(90deg, #E6F0FF 0%, #7D9CB8 50%, #1B2E4B 100%)',
          padding: '0.875rem 1.25rem',
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        }}>
          <div>
            <div style={{ fontSize: '10px', letterSpacing: '0.14em', fontWeight: '700', color: '#7D9CB8', textTransform: 'uppercase' }}>
              Sync Complete
            </div>
            <div style={{ fontSize: '15px', fontWeight: '700', color: 'white', marginTop: '1px' }}>
              How was today's session?
            </div>
          </div>
          <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.6)' }}>{date}</div>
        </div>

        {/* Fields */}
        <div style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '1.1rem' }}>

          {/* Energy */}
          <div>
            <div style={{ fontSize: '11px', fontWeight: '700', letterSpacing: '0.1em', color: '#6b7280', textTransform: 'uppercase', marginBottom: '0.5rem', textAlign: 'left' }}>
              Energy going in
            </div>
            <div style={{ display: 'flex', gap: '6px' }}>
              {[
                { v: 1, label: '1', sub: 'Barely out of bed' },
                { v: 2, label: '2', sub: 'Low' },
                { v: 3, label: '3', sub: 'Normal' },
                { v: 4, label: '4', sub: 'High' },
                { v: 5, label: '5', sub: 'Fired up' },
              ].map(({ v, label, sub }) => (
                <button
                  key={v}
                  onClick={() => setEnergy(v)}
                  title={sub}
                  style={energy === v ? btnActive : btnBase}
                >
                  {label}
                </button>
              ))}
              {energy !== null && (
                <span style={{ fontSize: '12px', color: '#6b7280', alignSelf: 'center', marginLeft: '6px' }}>
                  {['', 'Barely out of bed', 'Low', 'Normal', 'High', 'Fired up'][energy]}
                </span>
              )}
            </div>
          </div>

          {/* RPE */}
          <div>
            <div style={{ fontSize: '11px', fontWeight: '700', letterSpacing: '0.1em', color: '#6b7280', textTransform: 'uppercase', marginBottom: '0.5rem', textAlign: 'left' }}>
              How hard did it feel (RPE)
            </div>
            <div style={{ display: 'flex', gap: '5px', flexWrap: 'wrap' }}>
              {[1,2,3,4,5,6,7,8,9,10].map(v => (
                <button
                  key={v}
                  onClick={() => setRpe(v)}
                  style={rpe === v ? btnActive : btnBase}
                >
                  {v}
                </button>
              ))}
              {rpe !== null && (
                <span style={{ fontSize: '12px', color: '#6b7280', alignSelf: 'center', marginLeft: '4px' }}>
                  {rpe <= 3 ? 'Easy' : rpe <= 5 ? 'Moderate' : rpe <= 7 ? 'Hard' : rpe <= 9 ? 'Very hard' : 'Max effort'}
                </span>
              )}
            </div>
          </div>

          {/* Pain */}
          <div>
            <div style={{ fontSize: '11px', fontWeight: '700', letterSpacing: '0.1em', color: '#6b7280', textTransform: 'uppercase', marginBottom: '0.5rem', textAlign: 'left' }}>
              Pain — % of time thinking about it
            </div>
            <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
              {[0, 20, 40, 60, 80, 100].map(v => (
                <button
                  key={v}
                  onClick={() => setPain(v)}
                  style={pain === v ? { ...btnActive, borderColor: v >= 60 ? '#dc2626' : '#1B2E4B', background: v >= 60 ? '#dc2626' : '#1B2E4B' } : { ...btnBase, borderColor: v >= 60 ? '#fca5a5' : '#d1d5db', color: v >= 60 ? '#dc2626' : '#374151' }}
                >
                  {v}%
                </button>
              ))}
            </div>
          </div>

          {/* Actions */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingTop: '0.25rem' }}>
            <button
              onClick={onDone}
              style={{ fontSize: '13px', color: '#9ca3af', background: 'none', border: 'none', cursor: 'pointer', padding: '4px 0', textAlign: 'left' }}
            >
              Skip for now
            </button>
            <button
              onClick={handleSubmit}
              disabled={!complete || submitting}
              style={{
                padding: '8px 24px',
                borderRadius: '4px',
                border: 'none',
                fontSize: '13px',
                fontWeight: '600',
                cursor: complete ? 'pointer' : 'not-allowed',
                background: complete ? '#1B2E4B' : '#e5e7eb',
                color: complete ? 'white' : '#9ca3af',
                transition: 'background 0.2s, color 0.2s',
              }}
            >
              {submitting ? 'Saving...' : 'Save debrief'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// ─── ManualSyncComponent ───────────────────────────────────────────────────

interface ManualSyncProps {
  onSyncComplete?: () => void;
}

const ManualSyncComponent: React.FC<ManualSyncProps> = ({ onSyncComplete }) => {
  const [syncPeriod, setSyncPeriod] = useState(7);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [showJournalModal, setShowJournalModal] = useState(false);

  const todayStr = new Date().toISOString().split('T')[0];

  const handleJournalDone = () => {
    setShowJournalModal(false);
    if (onSyncComplete) {
      setTimeout(() => { onSyncComplete(); }, 500);
    }
  };

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
        // Show quick journal modal before refreshing dashboard
        setTimeout(() => { setShowJournalModal(true); }, 600);
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
    <>
    {showJournalModal && (
      <QuickJournalModal date={todayStr} onDone={handleJournalDone} />
    )}
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
    </>
  );
};

export default ManualSyncComponent;