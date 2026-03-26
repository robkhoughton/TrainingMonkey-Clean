import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import YTMSpinner from './YTMSpinner';
import styles from './TrainingLoadDashboard.module.css';

// ─── Design tokens (match tactical dark system) ────────────────────────────

const CARBON: React.CSSProperties = {
  backgroundColor: '#1B2E4B',
  backgroundImage: [
    'linear-gradient(135deg, rgba(255,255,255,0.04) 25%, transparent 25%)',
    'linear-gradient(225deg, rgba(255,255,255,0.04) 25%, transparent 25%)',
    'linear-gradient(315deg, rgba(255,255,255,0.04) 25%, transparent 25%)',
    'linear-gradient(45deg,  rgba(255,255,255,0.04) 25%, transparent 25%)',
  ].join(', '),
  backgroundSize: '4px 4px',
};

const FIELD_LABEL: React.CSSProperties = {
  display: 'block',
  marginBottom: '8px',
  fontSize: '0.72rem',
  fontWeight: 700,
  color: '#7D9CB8',
  textTransform: 'uppercase',
  letterSpacing: '0.08em',
};

const PROCESSING_MESSAGES = [
  'Saving observations...',
  'Analyzing your workout...',
  'Building tomorrow\'s plan...',
  'Finalizing...',
];

// ─── Types ─────────────────────────────────────────────────────────────────

type Phase = 'form' | 'processing' | 'autopsy';

interface AutopsyData {
  analysis: string;
  score: number | null;
}

interface QuickJournalModalProps {
  date: string;
  onDone: () => void;
}

// ─── Quick Journal Modal ───────────────────────────────────────────────────

const QuickJournalModal: React.FC<QuickJournalModalProps> = ({ date, onDone }) => {
  const navigate = useNavigate();
  const [phase, setPhase] = useState<Phase>('form');
  const [energy, setEnergy] = useState<number | null>(null);
  const [rpe, setRpe]       = useState<number | null>(null);
  const [pain, setPain]     = useState<number | null>(null);
  const [statusMsg, setStatusMsg] = useState(PROCESSING_MESSAGES[0]);
  const [autopsyData, setAutopsyData] = useState<AutopsyData | null>(null);
  const msgIdxRef = useRef(0);

  const complete = energy !== null && rpe !== null && pain !== null;

  // Cycle processing messages
  useEffect(() => {
    if (phase !== 'processing') return;
    msgIdxRef.current = 0;
    setStatusMsg(PROCESSING_MESSAGES[0]);
    const timer = setInterval(() => {
      msgIdxRef.current = Math.min(msgIdxRef.current + 1, PROCESSING_MESSAGES.length - 1);
      setStatusMsg(PROCESSING_MESSAGES[msgIdxRef.current]);
    }, 5000);
    return () => clearInterval(timer);
  }, [phase]);

  const handleSubmit = async () => {
    if (!complete) return;
    setPhase('processing');
    try {
      const res = await fetch('/api/journal', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ date, energy_level: energy, rpe_score: rpe, pain_percentage: pain }),
      });
      const data = await res.json();
      if (data.autopsy_analysis) {
        setAutopsyData({ analysis: data.autopsy_analysis, score: data.alignment_score ?? null });
        setPhase('autopsy');
      } else {
        navigate('/journal');
      }
    } catch (_) {
      onDone(); // network error — close modal, stay on dashboard
    }
  };

  const scoreColor = (score: number | null) => {
    if (score === null) return '#7D9CB8';
    if (score >= 7) return '#16A34A';
    if (score >= 4) return '#f59e0b';
    return '#dc2626';
  };

  // ── Shared selector button styles ────────────────────────────────────────

  const btnOff: React.CSSProperties = {
    padding: '6px 0',
    minWidth: '38px',
    background: 'rgba(230,240,255,0.05)',
    border: '1px solid rgba(125,156,184,0.22)',
    borderRadius: '4px',
    fontSize: '13px',
    fontWeight: 600,
    color: '#7D9CB8',
    cursor: 'pointer',
    transition: 'all 0.13s',
  };
  const btnOn: React.CSSProperties = {
    ...btnOff,
    background: 'rgba(255,87,34,0.14)',
    border: '1px solid rgba(255,87,34,0.55)',
    color: '#E6F0FF',
    boxShadow: '0 0 8px rgba(255,87,34,0.18)',
  };
  const btnPainOff: React.CSSProperties = {
    ...btnOff,
    border: '1px solid rgba(220,38,38,0.3)',
    color: '#fca5a5',
  };
  const btnPainOn: React.CSSProperties = {
    ...btnPainOff,
    background: 'rgba(220,38,38,0.18)',
    border: '1px solid rgba(220,38,38,0.7)',
    boxShadow: '0 0 8px rgba(220,38,38,0.2)',
  };

  // ── Shared container ─────────────────────────────────────────────────────

  return (
    <div style={{
      position: 'fixed', inset: 0,
      background: 'rgba(0,0,0,0.65)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      padding: '20px',
      zIndex: 1000,
    }}>
      <style>{`
        @keyframes ytm-modal-in {
          from { opacity: 0; transform: scale(0.97) translateY(10px); }
          to   { opacity: 1; transform: scale(1) translateY(0); }
        }
        @keyframes ytm-phase-fade {
          from { opacity: 0; transform: translateY(6px); }
          to   { opacity: 1; transform: translateY(0); }
        }
      `}</style>

      <div style={{
        ...CARBON,
        border: '1px solid rgba(255,87,34,0.65)',
        borderRadius: '8px',
        overflow: 'hidden',
        width: '100%',
        maxWidth: '560px',
        maxHeight: '90vh',
        overflowY: 'auto',
        animation: 'ytm-modal-in 0.24s cubic-bezier(0.22,1,0.36,1)',
        boxShadow: '0 24px 64px rgba(0,0,0,0.5), 0 0 0 1px rgba(255,87,34,0.1)',
      }}>

        {/* ── FORM PHASE ──────────────────────────────────────────────── */}
        {phase === 'form' && (
          <div style={{ animation: 'ytm-phase-fade 0.18s ease' }}>

            {/* Header */}
            <div style={{
              background: 'linear-gradient(90deg, #E6F0FF 0%, #7D9CB8 50%, #1B2E4B 100%)',
              padding: '12px 24px',
            }}>
              <span style={{ fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.12em', color: '#1B2E4B', textTransform: 'uppercase' }}>
                Post-Workout Debrief
              </span>
              <div style={{ fontSize: '0.95rem', fontWeight: 700, color: 'white', marginTop: '2px' }}>
                How was today's session?
              </div>
            </div>

            {/* Fields */}
            <div style={{ padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>

              {/* Energy */}
              <div>
                <span style={FIELD_LABEL}>Energy going in</span>
                <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', alignItems: 'center' }}>
                  {([
                    [1, 'Barely out of bed'],
                    [2, 'Low'],
                    [3, 'Normal'],
                    [4, 'High'],
                    [5, 'Fired up'],
                  ] as [number, string][]).map(([v, sub]) => (
                    <button key={v} onClick={() => setEnergy(v)} title={sub}
                      style={energy === v ? btnOn : btnOff}>
                      {v}
                    </button>
                  ))}
                  {energy !== null && (
                    <span style={{ fontSize: '11px', color: '#7D9CB8', marginLeft: '4px', fontStyle: 'italic' }}>
                      {['', 'Barely out of bed', 'Low', 'Normal', 'High', 'Fired up'][energy]}
                    </span>
                  )}
                </div>
              </div>

              {/* RPE */}
              <div>
                <span style={FIELD_LABEL}>Effort (RPE)</span>
                <div style={{ display: 'flex', gap: '5px', flexWrap: 'wrap', alignItems: 'center' }}>
                  {[1,2,3,4,5,6,7,8,9,10].map(v => (
                    <button key={v} onClick={() => setRpe(v)} style={rpe === v ? btnOn : btnOff}>{v}</button>
                  ))}
                  {rpe !== null && (
                    <span style={{ fontSize: '11px', color: '#7D9CB8', marginLeft: '4px', fontStyle: 'italic' }}>
                      {rpe <= 3 ? 'Easy' : rpe <= 5 ? 'Moderate' : rpe <= 7 ? 'Hard' : rpe <= 9 ? 'Very hard' : 'Max effort'}
                    </span>
                  )}
                </div>
              </div>

              {/* Pain */}
              <div>
                <span style={FIELD_LABEL}>Pain — % of time thinking about it</span>
                <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                  {[0, 20, 40, 60, 80, 100].map(v => (
                    <button key={v} onClick={() => setPain(v)}
                      style={pain === v
                        ? (v >= 60 ? btnPainOn  : btnOn)
                        : (v >= 60 ? btnPainOff : btnOff)
                      }>
                      {v}%
                    </button>
                  ))}
                </div>
              </div>

              {/* Actions */}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingTop: '4px' }}>
                <button onClick={onDone} style={{
                  fontSize: '12px', color: 'rgba(230,240,255,0.35)',
                  background: 'none', border: 'none', cursor: 'pointer', padding: '4px 0',
                }}>
                  Skip for now
                </button>
                <button onClick={handleSubmit} disabled={!complete} style={{
                  padding: '9px 28px',
                  borderRadius: '4px',
                  border: 'none',
                  fontSize: '0.72rem',
                  fontWeight: 700,
                  letterSpacing: '0.08em',
                  textTransform: 'uppercase',
                  cursor: complete ? 'pointer' : 'not-allowed',
                  background: complete ? '#FF5722' : 'rgba(230,240,255,0.07)',
                  color: complete ? 'white' : 'rgba(230,240,255,0.25)',
                  transition: 'background 0.2s, box-shadow 0.2s',
                  boxShadow: complete ? '0 2px 12px rgba(255,87,34,0.35)' : 'none',
                }}>
                  Log Debrief
                </button>
              </div>

            </div>
          </div>
        )}

        {/* ── PROCESSING PHASE ─────────────────────────────────────────── */}
        {phase === 'processing' && (
          <div style={{
            padding: '52px 24px 48px',
            display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '24px',
            animation: 'ytm-phase-fade 0.2s ease',
          }}>
            <YTMSpinner size={80} />
            <div style={{
              color: '#7D9CB8',
              fontSize: '0.8rem',
              fontWeight: 600,
              letterSpacing: '0.06em',
              textTransform: 'uppercase',
              opacity: 0.9,
            }}>
              {statusMsg}
            </div>
          </div>
        )}

        {/* ── AUTOPSY PHASE ────────────────────────────────────────────── */}
        {phase === 'autopsy' && autopsyData && (() => {
          const color = scoreColor(autopsyData.score);
          return (
            <div style={{ animation: 'ytm-phase-fade 0.22s ease' }}>

              {/* Header */}
              <div style={{
                background: 'linear-gradient(90deg, #E6F0FF 0%, #7D9CB8 50%, #1B2E4B 100%)',
                padding: '12px 24px',
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              }}>
                <span style={{ fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.12em', color: '#1B2E4B', textTransform: 'uppercase' }}>
                  Workout Autopsy
                </span>
                {autopsyData.score !== null && (
                  <span style={{
                    fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.06em',
                    color: color,
                    border: `1px solid ${color}`,
                    padding: '2px 10px', borderRadius: '10px',
                    background: `${color}18`,
                  }}>
                    {autopsyData.score}/10
                  </span>
                )}
              </div>

              {/* Autopsy content */}
              <div style={{ padding: '20px 24px 24px' }}>
                <div style={{
                  color: '#CBD5E1',
                  fontSize: '0.875rem',
                  lineHeight: '1.75',
                  maxHeight: '48vh',
                  overflowY: 'auto',
                  paddingRight: '6px',
                }}>
                  {autopsyData.analysis.split('\n').filter(l => l.trim()).map((line, i) => (
                    <p key={i} style={{ margin: '0 0 10px 0' }}>{line}</p>
                  ))}
                </div>

                {/* CTA */}
                <div style={{ display: 'flex', justifyContent: 'flex-end', paddingTop: '20px', borderTop: '1px solid rgba(125,156,184,0.15)', marginTop: '16px' }}>
                  <button onClick={() => navigate('/journal')} style={{
                    padding: '9px 28px',
                    borderRadius: '4px',
                    border: 'none',
                    fontSize: '0.72rem',
                    fontWeight: 700,
                    letterSpacing: '0.08em',
                    textTransform: 'uppercase',
                    cursor: 'pointer',
                    background: '#FF5722',
                    color: 'white',
                    boxShadow: '0 2px 12px rgba(255,87,34,0.35)',
                  }}>
                    See Training Plan
                  </button>
                </div>
              </div>

            </div>
          );
        })()}

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