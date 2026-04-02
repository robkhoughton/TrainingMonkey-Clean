import React, { useState, useEffect, useCallback } from 'react';
import styles from './TrainingLoadDashboard.module.css'; // Reuse existing styles
import { usePagePerformanceMonitoring, useComponentPerformanceMonitoring } from './usePerformanceMonitoring';

// Phase 6C: structured_output shape from the LLM
interface StructuredOutput {
  target_date?: string;
  assessment?: {
    category?: string;
    primary_driver?: string;
    primary_signal?: string;
  };
  divergence?: {
    severity?: string;
    direction?: string;
  };
  risk?: {
    injury_risk_level?: string;
  };
  context?: {
    autopsy_informed?: boolean;
  };
  [key: string]: unknown;
}

interface JournalEntry {
  date: string;
  is_today: boolean;
  is_future?: boolean;  // NEW: indicates if entry is for a future date
  is_tomorrow?: boolean;  // NEW: indicates if entry is for tomorrow
  has_observations?: boolean;  // NEW: indicates if journal observations have been saved
  is_next_incomplete?: boolean;  // NEW: indicates this is the next workout to complete
  todays_decision: string;
  activity_summary: {
    type: string;
    distance: number;
    elevation: number;
    workout_classification: string;
    total_trimp: number;
    activity_id?: number;
  } | null;  // Can be null for future dates
  observations: {
    energy_level: number | null;
    rpe_score: number | null;
    pain_percentage: number | null;
    notes: string;
    sleep_quality: number | null;      // Phase 6B
    morning_soreness: number | null;   // Phase 6B
  };
  ai_autopsy: {
    autopsy_analysis?: string;
    alignment_score?: number;
    generated_at?: string;
  };
  // Phase 6C: machine-readable recommendation metadata (null for pre-Phase-1 rows)
  structured_output: StructuredOutput | null;
  recommendation_target_date: string | null;
}

interface JournalResponse {
  success: boolean;
  data: JournalEntry[];
  center_date: string;
  date_range: string;
  error?: string;
}

// Function to format training decision text with styled components
const formatTrainingDecision = (text: string): React.ReactNode => {
  if (!text || text === 'No AI recommendation available') {
    return <span style={{ fontStyle: 'italic', color: '#6b7280' }}>{text}</span>;
  }

  // Split by lines and process each
  const lines = text.split('\n');
  const elements: React.ReactNode[] = [];
  
  lines.forEach((line, index) => {
    const trimmedLine = line.trim();

    // Skip empty lines
    if (!trimmedLine) {
      elements.push(<br key={`br-${index}`} />);
      return;
    }

    // Strip LLM-generated date-stamped sub-headers in all markdown variants:
    //   "TRAINING DECISION: 2026-03-30"
    //   "**TRAINING DECISION: 2026-03-30**"
    //   "# TRAINING DECISION: 2026-03-30"
    //   "## TRAINING DECISION: 2026-03-30"
    // The Journal already shows the date in the row header — these LLM labels are redundant.
    const cleanedForPattern = trimmedLine.replace(/^#+\s*/, '').replace(/\*\*/g, '').trim();
    if (/^TRAINING DECISION:\s*\d{4}-\d{2}-\d{2}$/i.test(cleanedForPattern)) {
      return;
    }

    // Check for headers (##)
    if (trimmedLine.startsWith('##')) {
      const headerText = trimmedLine.replace(/^##+\s*/, '');
      elements.push(
        <h3 key={`h3-${index}`} style={{
          fontSize: '1rem',
          fontWeight: '700',
          color: '#1e293b',
          marginTop: index > 0 ? '1rem' : '0',
          marginBottom: '0.5rem',
          paddingBottom: '0.25rem',
          borderBottom: '2px solid #e2e8f0'
        }}>
          {formatBoldText(headerText)}
        </h3>
      );
      return;
    }
    
    // Check for main headers (#)
    if (trimmedLine.startsWith('# ')) {
      const headerText = trimmedLine.replace(/^#+\s*/, '');
      elements.push(
        <h2 key={`h2-${index}`} style={{
          fontSize: '1.1rem',
          fontWeight: '700',
          color: '#1e293b',
          marginTop: index > 0 ? '1.25rem' : '0',
          marginBottom: '0.75rem',
          paddingBottom: '0.5rem',
          borderBottom: '3px solid #3b82f6'
        }}>
          {formatBoldText(headerText)}
        </h2>
      );
      return;
    }
    
    // Regular paragraph
    const paragraph = (
      <p key={`p-${index}`} style={{
        margin: '0.5rem 0',
        lineHeight: '1.6',
        color: '#374151'
      }}>
        {formatBoldText(trimmedLine)}
      </p>
    );
    elements.push(paragraph);
  });
  
  return <div>{elements}</div>;
};

// Helper function to format bold text (**text**)
const formatBoldText = (text: string): React.ReactNode => {
  const parts: React.ReactNode[] = [];
  const boldRegex = /\*\*(.*?)\*\*/g;
  let lastIndex = 0;
  let match;
  let key = 0;
  
  while ((match = boldRegex.exec(text)) !== null) {
    // Add text before the match
    if (match.index > lastIndex) {
      parts.push(text.substring(lastIndex, match.index));
    }
    
    // Add bold text
    parts.push(
      <strong key={`bold-${key++}`} style={{
        fontWeight: '700',
        color: '#1e293b'
      }}>
        {match[1]}
      </strong>
    );
    
    lastIndex = match.index + match[0].length;
  }
  
  // Add remaining text
  if (lastIndex < text.length) {
    parts.push(text.substring(lastIndex));
  }
  
  return parts.length > 0 ? <>{parts}</> : text;
};

// ─── Phase 6B: Morning Readiness Card ──────────────────────────────────────
interface MorningReadinessCardProps {
  todayStr: string;
  onSaved: () => void;
}

interface WellnessData {
  hrv_value: number | null;
  hrv_baseline_30d: number | null;
  resting_hr: number | null;
  rhr_baseline_7d: number | null;
  sleep_duration_secs: number | null;
  sleep_score: number | null;
  weight: number | null;
  weight_baseline_7d: number | null;
  spo2: number | null;
  respiration_rate: number | null;
  vo2max: number | null;
  hrv_source: string | null;
  readiness_state: 'GREEN' | 'AMBER' | 'RED' | null;
  readiness_flags: {
    hrv_suppressed?: boolean;
    rhr_elevated?: boolean;
    sleep_deficit?: boolean;
    sleep_poor_score?: boolean;
    high_soreness?: boolean;
  } | null;
}

const MorningReadinessCard: React.FC<MorningReadinessCardProps> = ({ todayStr, onSaved }) => {
  const [sleepQuality, setSleepQuality] = useState<number>(3);
  const [morningSoreness, setMorningSoreness] = useState<number>(0);
  const [wellness, setWellness] = useState<WellnessData | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`/api/readiness?date=${todayStr}`)
      .then(r => r.json())
      .then(data => {
        if (data.sleep_quality !== undefined) setSleepQuality(data.sleep_quality ?? 3);
        if (data.morning_soreness !== undefined) setMorningSoreness(data.morning_soreness ?? 0);
        setWellness(data);
      })
      .catch(() => {});
  }, [todayStr]);

  const handleSave = async () => {
    setIsSaving(true);
    setError(null);
    try {
      const response = await fetch('/api/readiness', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          date: todayStr,
          sleep_quality: sleepQuality,
          morning_soreness: morningSoreness
        })
      });
      const result = await response.json();
      if (!result.success) {
        throw new Error(result.error || 'Failed to save readiness data');
      }
      onSaved();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div style={{
      border: '1px solid #d1d5db',
      borderRadius: '6px',
      padding: '14px 16px',
      backgroundColor: '#f9fafb',
      marginBottom: '12px'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
        <div style={{ fontSize: '0.9rem', fontWeight: '600', color: '#374151' }}>
          How are you feeling this morning?
        </div>
        {wellness?.readiness_state && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <div style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '5px',
              padding: '3px 10px',
              borderRadius: '12px',
              fontSize: '0.75rem',
              fontWeight: '700',
              letterSpacing: '0.05em',
              backgroundColor:
                wellness.readiness_state === 'GREEN' ? '#f0fdf4' :
                wellness.readiness_state === 'AMBER' ? '#fffbeb' : '#fef2f2',
              border: `1px solid ${
                wellness.readiness_state === 'GREEN' ? '#86efac' :
                wellness.readiness_state === 'AMBER' ? '#fcd34d' : '#fca5a5'
              }`,
              color:
                wellness.readiness_state === 'GREEN' ? '#16a34a' :
                wellness.readiness_state === 'AMBER' ? '#d97706' : '#dc2626',
            }}>
              <span style={{
                width: '7px', height: '7px', borderRadius: '50%',
                backgroundColor:
                  wellness.readiness_state === 'GREEN' ? '#16a34a' :
                  wellness.readiness_state === 'AMBER' ? '#d97706' : '#dc2626',
                flexShrink: 0
              }} />
              {wellness.readiness_state}
            </div>
            {wellness.readiness_flags && (
              <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                {wellness.readiness_flags.hrv_suppressed && (
                  <span style={{ fontSize: '0.7rem', color: '#6b7280', backgroundColor: '#f3f4f6', borderRadius: '4px', padding: '1px 6px' }}>HRV suppressed</span>
                )}
                {wellness.readiness_flags.rhr_elevated && (
                  <span style={{ fontSize: '0.7rem', color: '#6b7280', backgroundColor: '#f3f4f6', borderRadius: '4px', padding: '1px 6px' }}>RHR elevated</span>
                )}
                {wellness.readiness_flags.sleep_deficit && (
                  <span style={{ fontSize: '0.7rem', color: '#6b7280', backgroundColor: '#f3f4f6', borderRadius: '4px', padding: '1px 6px' }}>Sleep deficit</span>
                )}
                {wellness.readiness_flags.sleep_poor_score && (
                  <span style={{ fontSize: '0.7rem', color: '#6b7280', backgroundColor: '#f3f4f6', borderRadius: '4px', padding: '1px 6px' }}>Poor sleep</span>
                )}
                {wellness.readiness_flags.high_soreness && (
                  <span style={{ fontSize: '0.7rem', color: '#6b7280', backgroundColor: '#f3f4f6', borderRadius: '4px', padding: '1px 6px' }}>High soreness</span>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Sleep Quality */}
      <div style={{ marginBottom: '10px' }}>
        <label style={{ fontSize: '0.8rem', color: '#6b7280', display: 'block', marginBottom: '4px' }}>
          Sleep Quality: {sleepQuality} &nbsp;
          <span style={{ fontWeight: '400', color: '#9ca3af' }}>
            (1 = Very poor sleep, 5 = Excellent)
          </span>
        </label>
        <input
          type="range"
          min={1}
          max={5}
          step={1}
          value={sleepQuality}
          onChange={(e) => setSleepQuality(parseInt(e.target.value))}
          style={{ width: '200px', cursor: 'pointer' }}
        />
        <div style={{ display: 'flex', justifyContent: 'space-between', width: '200px', fontSize: '0.7rem', color: '#9ca3af', marginTop: '2px' }}>
          {[1,2,3,4,5].map(n => <span key={n}>{n}</span>)}
        </div>
      </div>

      {/* Morning Soreness */}
      <div style={{ marginBottom: '12px' }}>
        <label style={{ fontSize: '0.8rem', color: '#6b7280', display: 'block', marginBottom: '4px' }}>
          Morning Soreness: {morningSoreness} &nbsp;
          <span style={{ fontWeight: '400', color: '#9ca3af' }}>
            (0 = Fresh legs, 100 = Very sore)
          </span>
        </label>
        <input
          type="range"
          min={0}
          max={100}
          step={5}
          value={morningSoreness}
          onChange={(e) => setMorningSoreness(parseInt(e.target.value))}
          style={{ width: '200px', cursor: 'pointer' }}
        />
        <div style={{ display: 'flex', justifyContent: 'space-between', width: '200px', fontSize: '0.7rem', color: '#9ca3af', marginTop: '2px' }}>
          <span>0</span><span>50</span><span>100</span>
        </div>
      </div>

      {error && (
        <div style={{ fontSize: '0.8rem', color: '#dc2626', marginBottom: '8px' }}>{error}</div>
      )}

      <button
        onClick={handleSave}
        disabled={isSaving}
        style={{
          backgroundColor: '#3b82f6',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          padding: '6px 16px',
          fontSize: '0.8rem',
          fontWeight: '600',
          cursor: isSaving ? 'not-allowed' : 'pointer',
          opacity: isSaving ? 0.7 : 1
        }}
      >
        {isSaving ? 'Saving...' : 'Save'}
      </button>

      {/* intervals.icu wellness data */}
      {wellness && wellness.hrv_source === 'intervals_icu' && (
        <div style={{
          marginTop: '16px',
          paddingTop: '14px',
          borderTop: '1px solid #e5e7eb'
        }}>
          <div style={{ fontSize: '0.75rem', color: '#9ca3af', marginBottom: '10px', fontWeight: '500', letterSpacing: '0.04em', textTransform: 'uppercase' }}>
            Synced from intervals.icu
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>

            {wellness.hrv_value !== null && (() => {
              const ratio = wellness.hrv_baseline_30d ? wellness.hrv_value / wellness.hrv_baseline_30d : null;
              const color = ratio ? (ratio < 0.85 ? '#d97706' : ratio > 1.15 ? '#6B8F7F' : '#374151') : '#374151';
              const tag   = ratio ? (ratio < 0.85 ? ' ↓' : ratio > 1.15 ? ' ↑' : '') : '';
              return (
                <div style={{ background: 'white', border: '1px solid #e5e7eb', borderRadius: '6px', padding: '6px 10px', minWidth: '80px' }}>
                  <div style={{ fontSize: '0.7rem', color: '#9ca3af', marginBottom: '2px' }}>HRV</div>
                  <div style={{ fontSize: '0.95rem', fontWeight: '600', color }}>{wellness.hrv_value.toFixed(0)}ms{tag}</div>
                  {wellness.hrv_baseline_30d && <div style={{ fontSize: '0.7rem', color: '#9ca3af' }}>avg {wellness.hrv_baseline_30d.toFixed(0)}ms</div>}
                </div>
              );
            })()}

            {wellness.resting_hr !== null && (() => {
              const diff  = wellness.rhr_baseline_7d ? ((wellness.resting_hr - wellness.rhr_baseline_7d) / wellness.rhr_baseline_7d) * 100 : null;
              const color = diff !== null ? (diff >= 10 ? '#d97706' : diff >= 5 ? '#d97706' : '#374151') : '#374151';
              const tag   = diff !== null ? (diff >= 5 ? ' ↑' : diff <= -5 ? ' ↓' : '') : '';
              return (
                <div style={{ background: 'white', border: '1px solid #e5e7eb', borderRadius: '6px', padding: '6px 10px', minWidth: '80px' }}>
                  <div style={{ fontSize: '0.7rem', color: '#9ca3af', marginBottom: '2px' }}>Resting HR</div>
                  <div style={{ fontSize: '0.95rem', fontWeight: '600', color }}>{wellness.resting_hr}bpm{tag}</div>
                  {wellness.rhr_baseline_7d && <div style={{ fontSize: '0.7rem', color: '#9ca3af' }}>avg {wellness.rhr_baseline_7d.toFixed(0)}bpm</div>}
                </div>
              );
            })()}

            {wellness.sleep_duration_secs !== null && (() => {
              const hrs   = wellness.sleep_duration_secs / 3600;
              const color = hrs < 6 ? '#d97706' : hrs < 7 ? '#d97706' : '#374151';
              return (
                <div style={{ background: 'white', border: '1px solid #e5e7eb', borderRadius: '6px', padding: '6px 10px', minWidth: '80px' }}>
                  <div style={{ fontSize: '0.7rem', color: '#9ca3af', marginBottom: '2px' }}>Sleep</div>
                  <div style={{ fontSize: '0.95rem', fontWeight: '600', color }}>{hrs.toFixed(1)}hrs</div>
                  {wellness.sleep_score !== null && <div style={{ fontSize: '0.7rem', color: '#9ca3af' }}>score {wellness.sleep_score}/100</div>}
                </div>
              );
            })()}

            {wellness.weight !== null && (
              <div style={{ background: 'white', border: '1px solid #e5e7eb', borderRadius: '6px', padding: '6px 10px', minWidth: '80px' }}>
                <div style={{ fontSize: '0.7rem', color: '#9ca3af', marginBottom: '2px' }}>Weight</div>
                <div style={{ fontSize: '0.95rem', fontWeight: '600', color: '#374151' }}>{wellness.weight.toFixed(1)}kg</div>
                {wellness.weight_baseline_7d && (
                  <div style={{ fontSize: '0.7rem', color: '#9ca3af' }}>
                    {(wellness.weight - wellness.weight_baseline_7d) >= 0 ? '+' : ''}{(wellness.weight - wellness.weight_baseline_7d).toFixed(1)}kg
                  </div>
                )}
              </div>
            )}

            {wellness.spo2 !== null && wellness.spo2 < 95 && (
              <div style={{ background: 'white', border: '1px solid #fca5a5', borderRadius: '6px', padding: '6px 10px', minWidth: '80px' }}>
                <div style={{ fontSize: '0.7rem', color: '#9ca3af', marginBottom: '2px' }}>SpO2</div>
                <div style={{ fontSize: '0.95rem', fontWeight: '600', color: '#dc2626' }}>{wellness.spo2.toFixed(0)}%</div>
              </div>
            )}

            {wellness.vo2max !== null && (
              <div style={{ background: 'white', border: '1px solid #e5e7eb', borderRadius: '6px', padding: '6px 10px', minWidth: '80px' }}>
                <div style={{ fontSize: '0.7rem', color: '#9ca3af', marginBottom: '2px' }}>VO2max</div>
                <div style={{ fontSize: '0.95rem', fontWeight: '600', color: '#374151' }}>{wellness.vo2max.toFixed(0)}</div>
              </div>
            )}

          </div>
        </div>
      )}
    </div>
  );
};


// ─── Shared utility ──────────────────────────────────────────────────────────
const formatSnakeCase = (s: string): string =>
  s.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());

// ─── Phase 5: Why This Recommendation ───────────────────────────────────────
interface ConversationMessage {
  role: 'user' | 'assistant';
  content: string;
}

interface WhyPanelState {
  status: 'idle' | 'loading' | 'active' | 'error';
  conversation: ConversationMessage[];
  inputText: string;
  isSendingTurn: boolean;
}

interface WhyRecommendationPanelProps {
  structuredOutput: any;           // the structured_output JSONB field
  targetDate: string;              // recommendation_target_date (YYYY-MM-DD)
  todaysDecision: string;          // the prose recommendation text (read-only, displayed above)
  onRegenerate?: () => void;       // optional callback to force-regenerate the recommendation
  isRegenerating?: boolean;        // true while regeneration is in-flight
}

const WhyRecommendationPanel: React.FC<WhyRecommendationPanelProps> = ({ structuredOutput, targetDate, todaysDecision: _todaysDecision, onRegenerate, isRegenerating }) => {
  const [state, setState] = useState<WhyPanelState>({
    status: 'idle',
    conversation: [],
    inputText: '',
    isSendingTurn: false
  });

  const divergenceSeverity = (structuredOutput as StructuredOutput).divergence?.severity;
  const divergenceDirection = (structuredOutput as StructuredOutput).divergence?.direction;
  const divergenceLabel = [divergenceSeverity, divergenceDirection]
    .filter(Boolean)
    .map(v => formatSnakeCase(v as string))
    .join(' ');

  const assessmentCategory = (structuredOutput as StructuredOutput).assessment?.category
    ? formatSnakeCase((structuredOutput as StructuredOutput).assessment!.category!)
    : null;

  const riskLevel = (structuredOutput as StructuredOutput).risk?.injury_risk_level
    ? formatSnakeCase((structuredOutput as StructuredOutput).risk!.injury_risk_level!)
    : null;

  const primaryDriver = (structuredOutput as StructuredOutput).assessment?.primary_driver || null;

  const metaRowStyle: React.CSSProperties = {
    display: 'flex',
    gap: '6px',
    fontSize: '0.75rem',
    color: '#6b7280',
    marginBottom: '4px',
    flexWrap: 'wrap',
    alignItems: 'baseline'
  };

  const labelStyle: React.CSSProperties = {
    color: '#6b7280',
    fontWeight: '600',
    flexShrink: 0
  };

  const valueStyle: React.CSSProperties = {
    color: '#111827',
    fontWeight: '500'
  };

  const handleWhyClick = async () => {
    setState(s => ({ ...s, status: 'loading' }));
    try {
      const res = await fetch('/api/recommendation-conversation/explain', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          recommendation_date: targetDate,
          structured_output: structuredOutput,
          metrics: {}
        })
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setState(s => ({ ...s, status: 'active', conversation: data.conversation }));
    } catch (err) {
      setState(s => ({ ...s, status: 'error' }));
    }
  };

  const handleSend = async () => {
    if (!state.inputText.trim() || state.isSendingTurn) return;
    const userMessage = state.inputText.trim();
    setState(s => ({ ...s, isSendingTurn: true, inputText: '' }));
    try {
      const res = await fetch('/api/recommendation-conversation/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          recommendation_date: targetDate,
          message: userMessage,
          conversation: state.conversation,
          structured_output: structuredOutput
        })
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setState(s => ({ ...s, conversation: data.conversation, isSendingTurn: false }));
    } catch (err) {
      setState(s => ({ ...s, isSendingTurn: false }));
    }
  };

  const handleDone = () => {
    // Fire-and-forget extraction — don't await
    fetch('/api/recommendation-conversation/finish', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({
        recommendation_date: targetDate,
        conversation: state.conversation
      })
    }).catch(() => {}); // swallow errors — extraction is non-critical
    setState(s => ({ ...s, status: 'idle' }));
  };

  const handleKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSend();
    }
  };

  return (
    <div style={{
      marginTop: '12px',
      paddingTop: '10px',
      borderTop: '1px solid #d1d5db'
    }}>
      {/* State: idle */}
      {state.status === 'idle' && (
        <div style={{ marginTop: '8px', display: 'flex', gap: '8px', flexWrap: 'wrap', alignItems: 'center' }}>
          <button
            onClick={handleWhyClick}
            style={{
              backgroundColor: 'transparent',
              color: '#3b82f6',
              border: '1px solid #3b82f6',
              borderRadius: '4px',
              padding: '4px 10px',
              fontSize: '0.75rem',
              fontWeight: '600',
              cursor: 'pointer'
            }}
          >
            Why this recommendation?
          </button>
          <a
            href="/?tab=coach"
            style={{
              backgroundColor: 'transparent',
              color: '#6b7280',
              border: '1px solid #d1d5db',
              borderRadius: '4px',
              padding: '4px 10px',
              fontSize: '0.75rem',
              fontWeight: '600',
              textDecoration: 'none',
              display: 'inline-block'
            }}
          >
            Week Plan
          </a>
          {onRegenerate && (
            <button
              onClick={onRegenerate}
              disabled={isRegenerating}
              style={{
                backgroundColor: 'transparent',
                color: isRegenerating ? '#9ca3af' : '#6b7280',
                border: '1px solid #d1d5db',
                borderRadius: '4px',
                padding: '4px 10px',
                fontSize: '0.75rem',
                fontWeight: '600',
                cursor: isRegenerating ? 'not-allowed' : 'pointer'
              }}
            >
              {isRegenerating ? 'Regenerating...' : 'Refresh Rec'}
            </button>
          )}
        </div>
      )}

      {/* State: loading */}
      {state.status === 'loading' && (
        <div style={{ marginTop: '8px', fontSize: '0.75rem', color: '#6b7280', fontStyle: 'italic' }}>
          Generating explanation...
        </div>
      )}

      {/* State: error */}
      {state.status === 'error' && (
        <div style={{ marginTop: '8px' }}>
          <span style={{ fontSize: '0.75rem', color: '#dc2626' }}>
            Could not load explanation. Please try again.
          </span>
          <button
            onClick={() => setState(s => ({ ...s, status: 'idle' }))}
            style={{
              marginLeft: '8px',
              backgroundColor: 'transparent',
              color: '#3b82f6',
              border: '1px solid #3b82f6',
              borderRadius: '4px',
              padding: '2px 8px',
              fontSize: '0.75rem',
              cursor: 'pointer'
            }}
          >
            Retry
          </button>
        </div>
      )}

      {/* State: active — conversation */}
      {state.status === 'active' && (
        <div style={{ marginTop: '10px' }}>
          <div style={{
            maxHeight: '300px',
            overflowY: 'auto',
            border: '1px solid #e5e7eb',
            borderRadius: '6px',
            padding: '8px',
            backgroundColor: '#f9fafb',
            display: 'flex',
            flexDirection: 'column',
            gap: '8px'
          }}>
            {state.conversation.map((msg, idx) => (
              <div
                key={idx}
                style={{
                  display: 'flex',
                  justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start'
                }}
              >
                <div style={{
                  maxWidth: '85%',
                  padding: '8px 10px',
                  borderRadius: '6px',
                  fontSize: '0.8rem',
                  lineHeight: '1.5',
                  backgroundColor: msg.role === 'user' ? '#dbeafe' : '#f3f4f6',
                  color: '#1f2937',
                  textAlign: 'left'
                }}>
                  {msg.content}
                </div>
              </div>
            ))}
          </div>

          {/* Input row */}
          <div style={{ display: 'flex', gap: '6px', marginTop: '8px', alignItems: 'center' }}>
            <input
              type="text"
              value={state.inputText}
              onChange={(e) => setState(s => ({ ...s, inputText: e.target.value }))}
              onKeyDown={handleKeyDown}
              placeholder="Ask a follow-up question..."
              disabled={state.isSendingTurn}
              style={{
                flex: 1,
                padding: '5px 8px',
                border: '1px solid #d1d5db',
                borderRadius: '4px',
                fontSize: '0.8rem',
                opacity: state.isSendingTurn ? 0.6 : 1
              }}
            />
            <button
              onClick={handleSend}
              disabled={state.isSendingTurn || !state.inputText.trim()}
              style={{
                backgroundColor: '#3b82f6',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                padding: '5px 12px',
                fontSize: '0.8rem',
                fontWeight: '600',
                cursor: (state.isSendingTurn || !state.inputText.trim()) ? 'not-allowed' : 'pointer',
                opacity: (state.isSendingTurn || !state.inputText.trim()) ? 0.6 : 1
              }}
            >
              Send
            </button>
            <button
              onClick={handleDone}
              style={{
                backgroundColor: '#6b7280',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                padding: '5px 12px',
                fontSize: '0.8rem',
                fontWeight: '600',
                cursor: 'pointer'
              }}
            >
              Done
            </button>
          </div>
        </div>
      )}
    </div>
  );
};


// ─── Phase 6C: Recommendation Meta Panel ────────────────────────────────────
interface RecommendationMetaPanelProps {
  structuredOutput: StructuredOutput;
  targetDate: string | null;
}

const RecommendationMetaPanel: React.FC<RecommendationMetaPanelProps> = ({ structuredOutput, targetDate }) => {
  const divergenceSeverity = structuredOutput.divergence?.severity;
  const divergenceDirection = structuredOutput.divergence?.direction;
  const divergenceLabel = [divergenceSeverity, divergenceDirection]
    .filter(Boolean)
    .map(v => formatSnakeCase(v as string))
    .join(' ');

  const assessmentCategory = structuredOutput.assessment?.category
    ? formatSnakeCase(structuredOutput.assessment.category)
    : null;

  const riskLevel = structuredOutput.risk?.injury_risk_level
    ? formatSnakeCase(structuredOutput.risk.injury_risk_level)
    : null;

  const primaryDriver = structuredOutput.assessment?.primary_driver || null;
  const autopsyInformed = structuredOutput.context?.autopsy_informed === true;

  const displayDate = targetDate || (structuredOutput.target_date ?? null);

  const metaRowStyle: React.CSSProperties = {
    display: 'flex',
    gap: '6px',
    fontSize: '0.75rem',
    color: '#6b7280',
    marginBottom: '4px',
    flexWrap: 'wrap',
    alignItems: 'baseline'
  };

  const labelStyle: React.CSSProperties = {
    color: '#6b7280',
    fontWeight: '600',
    flexShrink: 0
  };

  const valueStyle: React.CSSProperties = {
    color: '#111827',
    fontWeight: '500'
  };

  return (
    <div style={{
      marginTop: '12px',
      paddingTop: '10px',
      borderTop: '1px solid #d1d5db'
    }}>
      <div style={{ fontSize: '0.75rem', fontWeight: '700', color: '#374151', letterSpacing: '0.05em', marginBottom: '8px', textTransform: 'uppercase' }}>
        Why this recommendation
      </div>

      {displayDate && (
        <div style={metaRowStyle}>
          <span style={labelStyle}>Recommendation for:</span>
          <span style={valueStyle}>{displayDate}</span>
        </div>
      )}

      {divergenceLabel && (
        <div style={metaRowStyle}>
          <span style={labelStyle}>Divergence:</span>
          <span style={valueStyle}>{divergenceLabel}</span>
        </div>
      )}

      {assessmentCategory && (
        <div style={metaRowStyle}>
          <span style={labelStyle}>Assessment:</span>
          <span style={valueStyle}>{assessmentCategory}</span>
        </div>
      )}

      {riskLevel && (
        <div style={metaRowStyle}>
          <span style={labelStyle}>Risk level:</span>
          <span style={valueStyle}>{riskLevel}</span>
        </div>
      )}

      {primaryDriver && (
        <div style={{ ...metaRowStyle, flexDirection: 'column', gap: '2px' }}>
          <span style={labelStyle}>Primary driver:</span>
          <span style={{ ...valueStyle, fontStyle: 'italic' }}>{primaryDriver}</span>
        </div>
      )}

      {autopsyInformed && (
        <div style={{ marginTop: '4px' }}>
          <span style={{
            fontSize: '0.7rem',
            color: '#059669',
            fontWeight: '600',
            backgroundColor: '#d1fae5',
            padding: '2px 6px',
            borderRadius: '3px'
          }}>
            Autopsy-informed
          </span>
        </div>
      )}
    </div>
  );
};


// ─── Phase D: Alignment Query ────────────────────────────────────────────────
interface AlignmentQuery {
  id: number;
  activity_date: string;
  alignment_score: number;
  status: string;
}

interface AlignmentQueryCardProps {
  query: AlignmentQuery;
  onDismissed: () => void;
}

const AlignmentQueryCard: React.FC<AlignmentQueryCardProps> = ({ query, onDismissed }) => {
  const [responseText, setResponseText] = useState('');
  const [isBusy, setIsBusy] = useState(false);
  const [confirmed, setConfirmed] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const postAction = async (endpoint: string, body?: object) => {
    setIsBusy(true);
    setError(null);
    try {
      const res = await fetch(`/api/alignment-queries/${query.id}/${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: body ? JSON.stringify(body) : undefined,
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.error || `HTTP ${res.status}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Request failed');
      setIsBusy(false);
      return false;
    }
    setIsBusy(false);
    return true;
  };

  const handleSubmit = async () => {
    if (!responseText.trim()) return;
    const ok = await postAction('respond', { response: responseText.trim() });
    if (ok) {
      setConfirmed(true);
      setTimeout(() => onDismissed(), 2000);
    }
  };

  const handleSnooze = async () => {
    const ok = await postAction('snooze');
    if (ok) onDismissed();
  };

  const handleDismiss = async () => {
    const ok = await postAction('dismiss');
    if (ok) onDismissed();
  };

  const formattedDate = (() => {
    const d = new Date(`${query.activity_date}T12:00:00Z`);
    return d.toLocaleDateString(undefined, { weekday: 'long', month: 'long', day: 'numeric' });
  })();

  if (confirmed) {
    return (
      <div style={{
        border: '1px solid var(--color-border, #d1d5db)',
        borderRadius: '6px',
        padding: '14px 16px',
        backgroundColor: 'var(--color-surface-alt, #f0fdf4)',
        marginBottom: '16px',
        fontSize: '0.875rem',
        color: 'var(--color-text-muted, #374151)',
        fontStyle: 'italic'
      }}>
        Got it — thanks for letting us know.
      </div>
    );
  }

  return (
    <div style={{
      border: '1px solid var(--color-amber-border, #fbbf24)',
      borderRadius: '6px',
      padding: '14px 16px',
      backgroundColor: 'var(--color-amber-surface, #fffbeb)',
      marginBottom: '16px'
    }}>
      <div style={{
        fontSize: '0.875rem',
        fontWeight: '600',
        color: 'var(--color-text, #1f2937)',
        marginBottom: '8px'
      }}>
        Your training was off-plan on {formattedDate}. What happened?
      </div>

      <textarea
        value={responseText}
        onChange={(e) => setResponseText(e.target.value)}
        placeholder="E.g. feeling run-down, travel, unexpected work commitment..."
        rows={3}
        disabled={isBusy}
        style={{
          width: '100%',
          boxSizing: 'border-box',
          padding: '6px 8px',
          border: '1px solid var(--color-border, #d1d5db)',
          borderRadius: '4px',
          fontSize: '0.8rem',
          resize: 'vertical',
          opacity: isBusy ? 0.6 : 1,
          marginBottom: '8px'
        }}
      />

      {error && (
        <div style={{ fontSize: '0.75rem', color: '#dc2626', marginBottom: '6px' }}>{error}</div>
      )}

      <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
        <button
          onClick={handleSubmit}
          disabled={isBusy || !responseText.trim()}
          style={{
            backgroundColor: 'var(--color-primary, #3b82f6)',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            padding: '5px 14px',
            fontSize: '0.8rem',
            fontWeight: '600',
            cursor: (isBusy || !responseText.trim()) ? 'not-allowed' : 'pointer',
            opacity: (isBusy || !responseText.trim()) ? 0.6 : 1
          }}
        >
          Submit
        </button>
        <button
          onClick={handleSnooze}
          disabled={isBusy}
          style={{
            backgroundColor: 'transparent',
            color: 'var(--color-text-muted, #6b7280)',
            border: '1px solid var(--color-border, #d1d5db)',
            borderRadius: '4px',
            padding: '5px 14px',
            fontSize: '0.8rem',
            fontWeight: '500',
            cursor: isBusy ? 'not-allowed' : 'pointer',
            opacity: isBusy ? 0.6 : 1
          }}
        >
          Not now
        </button>
        <button
          onClick={handleDismiss}
          disabled={isBusy}
          style={{
            backgroundColor: 'transparent',
            color: 'var(--color-text-muted, #6b7280)',
            border: 'none',
            padding: '5px 8px',
            fontSize: '0.75rem',
            cursor: isBusy ? 'not-allowed' : 'pointer',
            opacity: isBusy ? 0.6 : 1,
            textDecoration: 'underline'
          }}
        >
          Never ask again
        </button>
      </div>
    </div>
  );
};


const JournalPage: React.FC = () => {
  // Performance monitoring
  usePagePerformanceMonitoring('journal');
  const perfMonitor = useComponentPerformanceMonitoring('JournalPage');

  const [journalData, setJournalData] = useState<JournalEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [centerDate, setCenterDate] = useState<string>('');
  const [isSaving, setIsSaving] = useState<string | null>(null);
  const [savedEntries, setSavedEntries] = useState<Set<string>>(new Set()); // Track saved entries
  const [isRegenerating, setIsRegenerating] = useState<string | null>(null); // date being regenerated
  // Phase 6B: track dates where readiness was submitted this session
  const [readinessSubmitted, setReadinessSubmitted] = useState<Set<string>>(new Set());
  const [isGenerating, setIsGenerating] = useState(false);
  // Phase D: alignment query
  const [pendingQuery, setPendingQuery] = useState<AlignmentQuery | null>(null);
  // Early warning: physical distress pattern
  const [earlyWarning, setEarlyWarning] = useState<string | null>(null);
  
  // Modal state for full-screen autopsy display
  const [modalOpen, setModalOpen] = useState(false);
  const [modalAutopsy, setModalAutopsy] = useState<JournalEntry | null>(null);

  // Open modal with autopsy analysis
  const openAutopsyModal = (entry: JournalEntry) => {
    setModalAutopsy(entry);
    setModalOpen(true);
  };

  // Close modal
  const closeAutopsyModal = () => {
    setModalOpen(false);
    setModalAutopsy(null);
  };

  // Helper function to get alignment score color
  const getAlignmentScoreColor = (score: number): string => {
    if (score >= 8) return '#10b981'; // green
    if (score >= 6) return '#f59e0b'; // yellow
    if (score >= 4) return '#f97316'; // orange
    return '#ef4444'; // red
  };

  // Check if entry has been modified from saved state
  const hasUnsavedChanges = (entry: JournalEntry): boolean => {
    // If we just saved this entry, no unsaved changes
    if (savedEntries.has(entry.date)) {
      return false;
    }

    // Check if any field has a value (indicating user input)
    return !!(
      entry.observations.energy_level ||
      entry.observations.rpe_score ||
      entry.observations.pain_percentage ||
      entry.observations.notes?.trim()
    );
  };

  // Fetch journal data
  const fetchJournalData = useCallback(async (date?: string) => {
    try {
      setIsLoading(true);
      setError(null);

      perfMonitor.trackFetchStart();
      const url = date ? `/api/journal?date=${date}` : '/api/journal';
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`Failed to fetch journal data: ${response.status}`);
      }

      const result: JournalResponse = await response.json();
      perfMonitor.trackFetchEnd();

      if (result.success) {
        setJournalData(result.data);
        setCenterDate(result.center_date);

        // Mark entries as saved if they have observations in the database
        const newSavedEntries = new Set<string>();
        result.data.forEach(entry => {
          if (entry.observations.energy_level ||
              entry.observations.rpe_score ||
              entry.observations.pain_percentage ||
              entry.observations.notes?.trim()) {
            newSavedEntries.add(entry.date);
          }
        });
        setSavedEntries(newSavedEntries);
        perfMonitor.reportMetrics(result.data.length);
      } else {
        throw new Error(result.error || 'Unknown error');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load journal data');
      perfMonitor.reportMetrics(0, err instanceof Error ? err.message : 'Failed to load journal data');
    } finally {
      setIsLoading(false);
    }
  }, [perfMonitor]);

  // Save journal entry
  const saveJournalEntry = async (date: string, observations: any) => {
    try {
      setIsSaving(date);

      const response = await fetch('/api/journal', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          date,
          energy_level: observations.energy_level,
          rpe_score: observations.rpe_score,
          pain_percentage: observations.pain_percentage,
          notes: observations.notes
        })
      });

      const result = await response.json();

      if (result.success) {
        // Update local state to preserve user selections
        setJournalData(prev => prev.map(entry =>
          entry.date === date
            ? {
                ...entry,
                observations: {
                  ...entry.observations,
                  energy_level: observations.energy_level,
                  rpe_score: observations.rpe_score,
                  pain_percentage: observations.pain_percentage,
                  notes: observations.notes
                }
              }
            : entry
        ));

        // Mark this entry as saved
        setSavedEntries(prev => new Set(prev).add(date));

        // Refresh data to get any new autopsy analysis and auto-open modal
        setTimeout(async () => {
          try {
            const url = centerDate ? `/api/journal?date=${centerDate}` : '/api/journal';
            const response = await fetch(url);

            if (response.ok) {
              const result: JournalResponse = await response.json();
              if (result.success) {
                setJournalData(result.data);
                // Phase D: re-check for alignment queries after autopsy may have been generated
                fetchPendingAlignmentQuery();
                
                // Find the saved entry and open modal if autopsy is available
                const savedEntry = result.data.find(e => e.date === date);
                if (savedEntry?.ai_autopsy?.autopsy_analysis) {
                  openAutopsyModal(savedEntry);
                  // Auto-regen recommendation for next day (silently, in background)
                  const nextDay = new Date(date + 'T12:00:00');
                  nextDay.setDate(nextDay.getDate() + 1);
                  const nextDateStr = nextDay.toISOString().split('T')[0];
                  regenRecommendationSilent(nextDateStr);
                }
              }
            }
          } catch (err) {
            console.error('Failed to refresh data:', err);
          }
        }, 1500);

      } else {
        throw new Error(result.error || 'Failed to save journal entry');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save journal entry');

      // On error, refresh data to ensure consistency
      try {
        const refreshResponse = await fetch('/api/journal');
        const refreshData = await refreshResponse.json();
        if (refreshData.success) {
          setJournalData(refreshData.data);
        }
      } catch (refreshErr) {
        console.error('Failed to refresh data after error:', refreshErr);
      }
    } finally {
      setIsSaving(null);
    }
  };

  // Handle observation changes
  const handleObservationChange = (date: string, field: string, value: any) => {
    setJournalData(prev => prev.map(entry =>
      entry.date === date
        ? {
            ...entry,
            observations: {
              ...entry.observations,
              [field]: value
            }
          }
        : entry
    ));

    // Remove from saved entries when user makes changes
    setSavedEntries(prev => {
      const newSet = new Set(prev);
      newSet.delete(date);
      return newSet;
    });
  };

  // Phase D: fetch pending alignment query
  const fetchPendingAlignmentQuery = useCallback(async () => {
    try {
      const res = await fetch('/api/alignment-queries/pending', { credentials: 'include' });
      if (!res.ok) return;
      const data = await res.json();
      if (data.pending) {
        setPendingQuery({
          id: data.id,
          activity_date: data.activity_date,
          alignment_score: data.alignment_score,
          status: data.status,
        });
      } else {
        setPendingQuery(null);
      }
    } catch {
      // Non-critical — silently ignore
    }
  }, []);

  // Handle save
  const handleSave = (date: string) => {
    const entry = journalData.find(e => e.date === date);
    if (entry) {
      saveJournalEntry(date, entry.observations);
    }
  };

  // Silent background regen — fires after autopsy is generated, no blocking UI.
  // Defined here so handleMarkRestDay (below) can reference it without a forward dependency.
  const regenRecommendationSilent = async (forDate: string) => {
    const POLL_INTERVAL_MS = 2000;
    const TIMEOUT_MS = 90000;
    try {
      const startResponse = await fetch('/api/llm-recommendations/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ target_date: forDate })
      });
      if (!startResponse.ok) return;
      const { job_id } = await startResponse.json();
      const deadline = Date.now() + TIMEOUT_MS;
      while (Date.now() < deadline) {
        await new Promise(resolve => setTimeout(resolve, POLL_INTERVAL_MS));
        const statusResponse = await fetch(`/api/llm-recommendations/status/${job_id}`, {
          credentials: 'include'
        });
        const { status } = await statusResponse.json();
        if (status === 'complete') {
          await fetchJournalData(centerDate || undefined);
          return;
        }
        if (status === 'error') return;
      }
    } catch {
      // Non-critical — silently ignore regen errors
    }
  };

  // Handle marking rest day
  const handleMarkRestDay = async (date: string) => {
    // Prompt user for notes about why they're skipping the workout
    const notes = window.prompt(
      `Why are you skipping today's prescribed workout?\n\nEnter your notes (this will be used to generate an autopsy and inform tomorrow's recommendation):`,
      'Decided to rest due to '
    );

    // If user cancels, don't proceed
    if (notes === null) {
      return;
    }

    // Require at least some input
    if (!notes.trim()) {
      alert('Please enter a reason for skipping the workout.');
      return;
    }

    try {
      setIsSaving(date);

      const response = await fetch('/api/journal', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          date: date,
          is_rest_day: true,
          notes: notes.trim()
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to mark rest day');
      }

      const result = await response.json();
      console.log('Rest day marked successfully:', result);

      if (result.user_message) {
        alert(result.user_message);
      }

      // Mark as saved
      setSavedEntries(prev => new Set(prev).add(date));

      // Refresh journal data then auto-regen tomorrow's recommendation
      try {
        await fetchJournalData(centerDate);
        const nextDay = new Date(date + 'T12:00:00');
        nextDay.setDate(nextDay.getDate() + 1);
        regenRecommendationSilent(nextDay.toISOString().split('T')[0]);
      } catch (refreshErr) {
        console.error('Failed to refresh data after rest day:', refreshErr);
      }

    } catch (error) {
      console.error('Error marking rest day:', error);
      alert(`Failed to mark rest day: ${error instanceof Error ? error.message : String(error)}`);
    } finally {
      setIsSaving(null);
    }
  };

  // Generate recommendation on demand (async — POST returns 202 + job_id, then poll)
  const handleGenerateRecommendation = async (forDate?: string) => {
    const POLL_INTERVAL_MS = 2000;
    const TIMEOUT_MS = 90000;
    try {
      setIsGenerating(true);

      const body = forDate ? JSON.stringify({ target_date: forDate }) : undefined;
      const startResponse = await fetch('/api/llm-recommendations/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body
      });
      if (!startResponse.ok) {
        const result = await startResponse.json();
        alert(`Could not start recommendation generation: ${result.error || 'Unknown error'}`);
        return;
      }
      const { job_id } = await startResponse.json();

      const deadline = Date.now() + TIMEOUT_MS;
      while (Date.now() < deadline) {
        await new Promise(resolve => setTimeout(resolve, POLL_INTERVAL_MS));
        const statusResponse = await fetch(`/api/llm-recommendations/status/${job_id}`, {
          credentials: 'include'
        });
        const { status, error } = await statusResponse.json();
        if (status === 'complete') {
          await fetchJournalData(centerDate || undefined);
          return;
        }
        if (status === 'error') {
          alert(`Recommendation generation failed: ${error || 'Unknown error'}`);
          return;
        }
        // status === 'pending' — continue polling
      }
      alert('Recommendation generation is taking longer than expected. It may complete in the background — refresh in a moment.');
    } catch (error) {
      alert(`Could not generate recommendation: ${error instanceof Error ? error.message : String(error)}`);
    } finally {
      setIsGenerating(false);
    }
  };

  // Navigation functions
  const navigateToPrevious = () => {
    const prevDate = new Date(centerDate);
    prevDate.setDate(prevDate.getDate() - 7);
    fetchJournalData(prevDate.toISOString().split('T')[0]);
  };

  const navigateToNext = () => {
    const nextDate = new Date(centerDate);
    nextDate.setDate(nextDate.getDate() + 7);
    fetchJournalData(nextDate.toISOString().split('T')[0]);
  };

  const navigateToToday = () => {
    fetchJournalData(); // No date parameter = today
  };

  // Initial load
  useEffect(() => {
    fetchJournalData();
  }, [fetchJournalData]);

  // Phase D: fetch pending alignment query on mount
  useEffect(() => {
    fetchPendingAlignmentQuery();
  }, [fetchPendingAlignmentQuery]);

  // Early warning: fetch on mount
  useEffect(() => {
    fetch('/api/athlete-model/early-warning', { credentials: 'include' })
      .then(r => r.ok ? r.json() : null)
      .then(data => { if (data?.active) setEarlyWarning(data.message); })
      .catch(() => {});
  }, []);

  // Format date for display
  const formatDate = (dateStr: string) => {
    const date = new Date(`${dateStr}T12:00:00Z`);
    return date.toLocaleDateString(undefined, {
      weekday: 'short',
      month: 'short',
      day: 'numeric'
    });
  };

  const formatFullDate = (dateStr: string) => {
    const date = new Date(`${dateStr}T12:00:00Z`);
    return date.toLocaleDateString(undefined, {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  if (isLoading) {
    return (
      <div className={styles.loading}>
        <h2>Loading Training Journal...</h2>
        <p>Fetching your training diary...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.error}>
        <h2>Error Loading Journal</h2>
        <p>{error}</p>
        <button onClick={() => fetchJournalData()} className={styles.retryButtonEnhanced}>Retry</button>
      </div>
    );
  }

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '20px'
      }}>
        <h1 style={{ margin: 0, color: '#1f2937' }}>Training Journal</h1>
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <button
            onClick={navigateToPrevious}
            className={`${styles.journalNavButton} ${styles.navButtonBlue}`}
          >
            ← Previous Week
          </button>
          <button
            onClick={navigateToToday}
            className={`${styles.journalNavButton} ${styles.navButtonGreen}`}
          >
            Today
          </button>
          <button
            onClick={navigateToNext}
            className={`${styles.journalNavButton} ${styles.navButtonBlue}`}
          >
            Next Week →
          </button>
        </div>
      </div>

      {error && (
        <div style={{
          padding: '12px',
          backgroundColor: '#fef2f2',
          border: '1px solid #fecaca',
          borderRadius: '4px',
          color: '#dc2626',
          marginBottom: '20px'
        }}>
          {error}
        </div>
      )}

      {/* Early warning: physical distress pattern banner */}
      {earlyWarning && (
        <div style={{
          padding: '14px 18px',
          marginBottom: '16px',
          backgroundColor: '#fefce8',
          border: '1px solid #ca8a04',
          borderLeft: '4px solid #ca8a04',
          borderRadius: '6px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          gap: '12px',
        }}>
          <div style={{ color: '#713f12', fontSize: '0.9rem', lineHeight: '1.5' }}>
            <strong style={{ display: 'block', marginBottom: '4px' }}>Early Warning</strong>
            {earlyWarning}
          </div>
          <button
            onClick={() => setEarlyWarning(null)}
            style={{
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              color: '#92400e',
              fontSize: '1.1rem',
              lineHeight: '1',
              padding: '0',
              flexShrink: 0,
            }}
            aria-label="Dismiss warning"
          >×</button>
        </div>
      )}

      {/* Phase D: Alignment Query Card — shown above journal table when pending */}
      {pendingQuery && (
        <AlignmentQueryCard
          query={pendingQuery}
          onDismissed={() => setPendingQuery(null)}
        />
      )}

      <div style={{ backgroundColor: 'white', borderRadius: '8px', padding: '20px' }}>
        <div style={{ overflowX: 'auto', overflowY: 'auto', maxHeight: '80vh' }}>
          <table style={{
            width: '100%',
            borderCollapse: 'collapse',
            fontSize: '0.9rem'
          }}>
            <thead style={{
              position: 'sticky',
              top: 0,
              backgroundColor: '#f8f9fa',
              zIndex: 10,
              boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
            }}>
              <tr style={{ borderBottom: '2px solid #dee2e6' }}>
                <th style={{ padding: '12px 4px', textAlign: 'center', minWidth: '120px' }}>Date</th>
                <th style={{ padding: '12px 4px', textAlign: 'center', maxWidth: '500px', minWidth: '350px' }}>Today's Training Decision</th>
                <th style={{ padding: '12px 4px', textAlign: 'center', minWidth: '160px' }}>Actual Activity</th>
                <th style={{ padding: '12px 4px', textAlign: 'center', minWidth: '70px' }}>
                  <span 
                    style={{ cursor: 'help', borderBottom: '1px dotted #6b7280' }}
                    title="How did you feel going into the session? Fired up = 5, Barely got out of bed = 1"
                  >
                    Energy
                  </span>
                </th>
                <th style={{ padding: '12px 4px', textAlign: 'center', minWidth: '70px' }}>
                  <span 
                    style={{ cursor: 'help', borderBottom: '1px dotted #6b7280' }}
                    title="Rate of Perceived Exertion: How hard did the workout feel? 1 = Very Easy, 10 = Maximum Effort"
                  >
                    RPE
                  </span>
                </th>
                <th style={{ padding: '12px 4px', textAlign: 'center', minWidth: '70px' }}>
                  <span 
                    style={{ cursor: 'help', borderBottom: '1px dotted #6b7280' }}
                    title="The % of time during your activity that you were thinking about the pain"
                  >
                    Pain %
                  </span>
                </th>
                <th style={{ padding: '12px 4px', textAlign: 'center', maxWidth: '450px', minWidth: '350px' }}>Notes</th>
                <th style={{ padding: '12px 4px', textAlign: 'center', minWidth: '70px' }}>Alignment</th>
                <th style={{ padding: '12px 4px', textAlign: 'center', minWidth: '100px' }}>Actions</th>
              </tr>
            </thead>

            <tbody>
              {journalData.map((entry) => (
                <React.Fragment key={entry.date}>
                  {/* Next Incomplete Workout row - special rendering */}
                  {entry.is_next_incomplete ? (
                    <tr style={{
                      borderBottom: '2px solid #3b82f6',
                      backgroundColor: '#eff6ff'
                    }}>
                      {/* Date Column */}
                      <td style={{ padding: '16px 8px', verticalAlign: 'top' }}>
                        <div style={{ fontWeight: '600', color: '#3b82f6' }}>
                          {formatDate(entry.date)}
                          <div style={{ fontSize: '0.75rem', color: '#6b7280', marginTop: '4px' }}>
                            NEXT WORKOUT
                          </div>
                        </div>
                      </td>

                      {/* Next Workout Recommendation - spans multiple columns */}
                      <td colSpan={8} style={{ padding: '16px', verticalAlign: 'top' }}>
                        {entry.todays_decision && !entry.todays_decision.includes('No recommendation available') ? (
                          /* Has actual recommendation */
                          <div style={{
                            border: '2px solid #3b82f6',
                            borderRadius: '8px',
                            padding: '16px',
                            backgroundColor: 'white'
                          }}>
                            {/* Phase 6B: Morning Readiness Card — shown for today only, when no readiness yet */}
                            {entry.is_today &&
                              entry.observations.sleep_quality == null &&
                              !readinessSubmitted.has(entry.date) && (
                                <MorningReadinessCard
                                  todayStr={entry.date}
                                  onSaved={() => {
                                    setReadinessSubmitted(prev => new Set(prev).add(entry.date));
                                    fetchJournalData(centerDate || undefined);
                                  }}
                                />
                              )}

                            <div style={{
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'space-between',
                              marginBottom: '12px',
                              gap: '8px'
                            }}>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                <span style={{
                                  fontSize: '1.1rem',
                                  fontWeight: '600',
                                  color: '#1f2937'
                                }}>
                                  Training Decision for {formatDate(entry.date)}
                                </span>
                                <span style={{
                                  backgroundColor: '#10b981',
                                  color: 'white',
                                  padding: '4px 8px',
                                  borderRadius: '12px',
                                  fontSize: '0.75rem',
                                  fontWeight: '600'
                                }}>
                                  Autopsy-Informed
                                </span>
                              </div>
                              {/* Compact Mark as Rest Day button - hide if activity already recorded (real or manual rest).
                                  == null intentionally catches both null and undefined:
                                  null  = no activity recorded yet (show button)
                                  negative int = manually marked rest day (hide)
                                  positive int = real Strava activity (hide) */}
                              {(entry.activity_summary?.activity_id == null) && (
                                <button
                                  onClick={() => handleMarkRestDay(entry.date)}
                                  disabled={isSaving === entry.date}
                                  style={{
                                    backgroundColor: '#9333ea',
                                    color: 'white',
                                    padding: '6px 12px',
                                    borderRadius: '4px',
                                    border: 'none',
                                    fontSize: '0.8rem',
                                    fontWeight: '600',
                                    cursor: isSaving === entry.date ? 'not-allowed' : 'pointer',
                                    opacity: isSaving === entry.date ? 0.6 : 1,
                                    whiteSpace: 'nowrap'
                                  }}
                                >
                                  {isSaving === entry.date ? 'Marking...' : 'Mark as Rest Day'}
                                </button>
                              )}
                            </div>
                            <div style={{
                              fontSize: '0.9rem',
                              lineHeight: '1.6',
                              color: '#374151',
                              textAlign: 'left',
                              maxHeight: '400px',
                              overflowY: 'auto'
                            }}>
                              {formatTrainingDecision(entry.todays_decision)}
                            </div>

                            {/* Phase 5: Why This Recommendation Panel */}
                            <WhyRecommendationPanel
                              structuredOutput={entry.structured_output || {}}
                              targetDate={entry.recommendation_target_date || entry.date}
                              todaysDecision={entry.todays_decision || ''}
                              isRegenerating={isRegenerating === entry.date}
                              onRegenerate={() => {
                                const forDate = entry.recommendation_target_date || entry.date;
                                setIsRegenerating(entry.date);
                                regenRecommendationSilent(forDate).finally(() => setIsRegenerating(null));
                              }}
                            />
                          </div>
                        ) : (
                          /* No recommendation yet - prompt to complete journal */
                          <div style={{
                            border: '2px dashed #d1d5db',
                            borderRadius: '8px',
                            padding: '24px',
                            backgroundColor: '#f9fafb',
                            textAlign: 'center'
                          }}>
                            <div style={{ fontSize: '2rem', marginBottom: '12px' }}>📝</div>
                            <div style={{
                              fontSize: '1rem',
                              fontWeight: '600',
                              color: '#374151',
                              marginBottom: '8px'
                            }}>
                              No Recommendation Available for {formatDate(entry.date)}
                            </div>
                            <div style={{
                              fontSize: '0.875rem',
                              color: '#6b7280',
                              lineHeight: '1.5'
                            }}>
                              Generate fresh recommendations by entering observations/notes for today's activity and clicking Save
                            </div>
                          </div>
                        )}
                      </td>
                    </tr>
                  ) : (
                    /* Regular past/today row */
                    <tr style={{
                      borderBottom: '1px solid #e5e7eb',
                      backgroundColor: entry.is_today ? '#f0f9ff' : 'white'
                    }}>
                      {/* Date Column */}
                      <td style={{ padding: '12px 8px', verticalAlign: 'top' }}>
                        <div style={{ fontWeight: entry.is_today ? '600' : 'normal' }}>
                          {formatDate(entry.date)}
                        </div>
                      </td>

                      {/* Today's Training Decision */}
                      <td style={{ padding: '12px 8px', verticalAlign: 'top' }}>
                        <div style={{
                          display: 'flex',
                          flexDirection: 'column',
                          gap: '8px',
                          width: '350px',
                          minWidth: '350px',
                          maxWidth: '500px'
                        }}>
                          {(!entry.todays_decision || entry.todays_decision.includes('No recommendation available')) ? (
                            (entry.is_today || entry.is_tomorrow) ? (
                              <button
                                onClick={() => handleGenerateRecommendation(entry.date)}
                                disabled={isGenerating}
                                style={{
                                  backgroundColor: '#3b82f6',
                                  color: 'white',
                                  padding: '8px 14px',
                                  borderRadius: '4px',
                                  border: 'none',
                                  fontSize: '0.8rem',
                                  fontWeight: '600',
                                  cursor: isGenerating ? 'not-allowed' : 'pointer',
                                  opacity: isGenerating ? 0.6 : 1
                                }}
                              >
                                {isGenerating ? 'Generating...' : 'Generate Recommendation'}
                              </button>
                            ) : (
                              <span style={{ fontSize: '0.875rem', color: '#9ca3af', fontStyle: 'italic' }}>No recommendation</span>
                            )
                          ) : (
                            <div style={{
                              fontSize: '0.875rem',
                              lineHeight: '1.6',
                              maxHeight: '120px',
                              overflowY: 'auto',
                              color: '#374151',
                              textAlign: 'left'
                            }}>
                              {formatTrainingDecision(entry.todays_decision)}
                            </div>
                          )}
                        </div>
                      </td>


                      <td style={{ padding: '12px 4px', verticalAlign: 'top' }}>
                        <div style={{ fontSize: '0.875rem', lineHeight: '1.4', color: '#374151' }}>
                          {/* IMPROVED: Check for activity type properly */}
                          {!entry.activity_summary || !entry.activity_summary.type || entry.activity_summary.type === 'rest' ? (
                            <span style={{ fontStyle: 'italic', color: '#6b7280' }}>Rest Day</span>
                          ) : (
                          <>
                            <div><strong>{entry.activity_summary.type}</strong></div>
                            <div>
                              {entry.activity_summary.distance != null ? entry.activity_summary.distance.toFixed(1) : '0.0'} mi, {entry.activity_summary.elevation || 0} ft
                            </div>
                            <div>TRIMP: {entry.activity_summary.total_trimp || 0}</div>
                            <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>
                              ({entry.activity_summary.workout_classification})
                            </div>

                            {/* REQUIRED: "View on Strava" link for each actual activity */}
                            {entry.activity_summary.activity_id && entry.activity_summary.activity_id > 0 && (
                              <div style={{ marginTop: '6px' }}>
                                <a
                                  href={`https://www.strava.com/activities/${entry.activity_summary.activity_id}`}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  style={{
                                    fontSize: '0.75rem',
                                    color: '#FC5200',
                                    textDecoration: 'none',
                                    fontWeight: 'bold',
                                    padding: '2px 6px',
                                    borderRadius: '3px',
                                    backgroundColor: '#fef3c7',
                                    border: '1px solid #FC5200',
                                    display: 'inline-block'
                                  }}
                                  onMouseEnter={(e) => {
                                    e.currentTarget.style.backgroundColor = '#FC5200';
                                    e.currentTarget.style.color = 'white';
                                  }}
                                  onMouseLeave={(e) => {
                                    e.currentTarget.style.backgroundColor = '#fef3c7';
                                    e.currentTarget.style.color = '#FC5200';
                                  }}
                                >
                                  View on Strava
                                </a>
                              </div>
                            )}
                          </>
                        )}
                      </div>
                    </td>

                    {/* Energy Level */}
                    <td style={{ padding: '12px 4px', textAlign: 'center', verticalAlign: 'top' }}>
                      <select
                        value={entry.observations.energy_level || ''}
                        onChange={(e) => handleObservationChange(
                          entry.date,
                          'energy_level',
                          e.target.value ? parseInt(e.target.value) : null
                        )}
                        style={{
                          width: '50px',
                          padding: '4px',
                          border: '1px solid #d1d5db',
                          borderRadius: '4px',
                          fontSize: '0.875rem'
                        }}
                      >
                        <option value="">-</option>
                        <option value="1">1</option>
                        <option value="2">2</option>
                        <option value="3">3</option>
                        <option value="4">4</option>
                        <option value="5">5</option>
                      </select>
                    </td>

                    {/* RPE Score */}
                    <td style={{ padding: '12px 4px', textAlign: 'center', verticalAlign: 'top' }}>
                      <select
                        value={entry.observations.rpe_score || ''}
                        onChange={(e) => handleObservationChange(
                          entry.date,
                          'rpe_score',
                          e.target.value ? parseInt(e.target.value) : null
                        )}
                        style={{
                          width: '50px',
                          padding: '4px',
                          border: '1px solid #d1d5db',
                          borderRadius: '4px',
                          fontSize: '0.875rem'
                        }}
                      >
                        <option value="">-</option>
                        {[1,2,3,4,5,6,7,8,9,10].map(n => (
                          <option key={n} value={n}>{n}</option>
                        ))}
                      </select>
                    </td>

                    {/* Pain Percentage */}
                    <td style={{ padding: '12px 4px', textAlign: 'center', verticalAlign: 'top' }}>
                      <select
                        value={entry.observations.pain_percentage ?? ''}
                        onChange={(e) => handleObservationChange(
                          entry.date,
                          'pain_percentage',
                          e.target.value ? parseInt(e.target.value) : null
                        )}
                        style={{
                          width: '60px',
                          padding: '4px',
                          border: '1px solid #d1d5db',
                          borderRadius: '4px',
                          fontSize: '0.875rem'
                        }}
                      >
                        <option value="">-</option>
                        <option value="0">0%</option>
                        <option value="20">20%</option>
                        <option value="40">40%</option>
                        <option value="60">60%</option>
                        <option value="80">80%</option>
                        <option value="100">100%</option>
                      </select>
                    </td>

                    {/* Notes */}
                    <td style={{ padding: '12px 8px', verticalAlign: 'top' }}>
                      {(() => {
                        const text = entry.observations.notes || '';
                        const words = text.trim().split(/\s+/).filter(w => w.length > 0);
                        const wordCount = words.length;
                        const lower = text.toLowerCase();

                        const physioKeywords = [
                          'legs', 'leg', 'breathing', 'breath', 'lungs', 'lung',
                          'heart', 'heavy', 'sharp', 'tight', 'fatigued', 'fatigue',
                          'strong', 'flat', 'dead', 'muscles', 'muscle', 'tired',
                          'fresh', 'stiff', 'sore', 'weak', 'powerful', 'labored',
                          'sluggish', 'snappy', 'responsive', 'burn', 'burning',
                          'ache', 'pain', 'effort', 'exhausted', 'energized',
                        ];
                        const exoKeywords = [
                          'sleep', 'slept', 'nutrition', 'fuel', 'fueling', 'stress',
                          'heat', 'cold', 'altitude', 'hydration', 'hydrated',
                          'dehydrated', 'alcohol', 'food', 'eating', 'ate',
                          'drank', 'drink', 'weather', 'conditions', 'sick',
                          'illness', 'coffee', 'work', 'travel', 'humidity',
                          'humid', 'wind', 'rain', 'snow', 'hot', 'nausea',
                          'stomach', 'busy', 'late', 'early',
                        ];

                        const physioHits = physioKeywords.filter(k => lower.includes(k)).length;
                        const exoHits   = exoKeywords.filter(k => lower.includes(k)).length;

                        // 4 bars — each one a progressively harder threshold
                        const bars = [
                          wordCount >= 8  || physioHits > 0 || exoHits > 0,
                          wordCount >= 16 || (physioHits > 0 && exoHits > 0),
                          (wordCount >= 16 && (physioHits > 0 || exoHits > 0)) || wordCount >= 24 || physioHits >= 2 || exoHits >= 2,
                          wordCount >= 24 && physioHits > 0 && exoHits > 0,
                        ];
                        const level = bars.filter(Boolean).length;

                        const levelConfig = [
                          { label: 'No Signal',   color: '#9ca3af' },
                          { label: 'Baseline',    color: '#f59e0b' },
                          { label: 'Developing',  color: '#d97706' },
                          { label: 'Clear',       color: '#6B8F7F' },
                          { label: 'Diagnostic',  color: '#16a34a' },
                        ];
                        const hints = [
                          '— keep writing',
                          '— describe how you felt physically',
                          '— add a context factor (sleep, heat, stress…)',
                          '— add more depth',
                          '',
                        ];
                        const cfg = levelConfig[level];

                        return (
                          <>
                            <textarea
                              value={text}
                              onChange={(e) => handleObservationChange(entry.date, 'notes', e.target.value)}
                              placeholder="Training notes..."
                              style={{
                                height: '100px',
                                padding: '6px',
                                border: '1px solid #d1d5db',
                                borderRadius: '4px',
                                fontSize: '0.875rem',
                                resize: 'vertical',
                                width: '350px',
                                minWidth: '350px',
                                maxWidth: '450px',
                                display: 'block',
                              }}
                            />
                            {text.trim().length > 0 && (
                              <div style={{
                                marginTop: '5px',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '6px',
                              }}>
                                {/* Signal bars */}
                                <div style={{ display: 'flex', gap: '2px', alignItems: 'flex-end', flexShrink: 0 }}>
                                  {[0, 1, 2, 3].map(i => (
                                    <div key={i} style={{
                                      width: '4px',
                                      height: `${8 + i * 4}px`,
                                      borderRadius: '2px',
                                      backgroundColor: bars[i] ? cfg.color : '#e5e7eb',
                                      transition: 'background-color 0.18s ease',
                                    }} />
                                  ))}
                                </div>
                                {/* Label */}
                                <span style={{
                                  fontSize: '10px',
                                  fontWeight: '700',
                                  color: cfg.color,
                                  letterSpacing: '0.08em',
                                  textTransform: 'uppercase',
                                  flexShrink: 0,
                                }}>
                                  {cfg.label}
                                </span>
                                {/* Hint */}
                                {level < 4 && (
                                  <span style={{
                                    fontSize: '10px',
                                    color: '#9ca3af',
                                    fontStyle: 'italic',
                                  }}>
                                    {hints[level]}
                                  </span>
                                )}
                              </div>
                            )}
                          </>
                        );
                      })()}
                    </td>

                    {/* Alignment Score Column */}
                    <td style={{ padding: '12px 8px', textAlign: 'center', verticalAlign: 'top' }}>
                      {entry.ai_autopsy.alignment_score ? (
                        <div style={{
                          padding: '4px 8px',
                          backgroundColor: getAlignmentScoreColor(entry.ai_autopsy.alignment_score),
                          color: 'white',
                          borderRadius: '12px',
                          fontSize: '0.8rem',
                          fontWeight: '600',
                          display: 'inline-block',
                          minWidth: '35px'
                        }}>
                          {entry.ai_autopsy.alignment_score}/10
                        </div>
                      ) : (
                        <span style={{ color: '#9ca3af', fontSize: '0.8rem' }}>-</span>
                      )}
                    </td>

                    {/* Actions - Progressive Multi-State Button */}
                    <td style={{ padding: '12px 8px', textAlign: 'center', verticalAlign: 'top' }}>
                      {(() => {
                        // Determine button state based on data and user actions
                        const hasUnsaved = hasUnsavedChanges(entry);
                        const isSaved = savedEntries.has(entry.date);
                        const hasAnalysis = entry.ai_autopsy.autopsy_analysis;
                        const isCurrentlySaving = isSaving === entry.date;
                        const isToday = entry.is_today;
                        const noActivityYet = !entry.activity_summary?.activity_id;

                        // State 0 FIRST: Today, no activity recorded yet, no observations typed — offer rest day
                        if (isToday && noActivityYet && !hasUnsaved && !isCurrentlySaving) {
                          return (
                            <button
                              onClick={() => handleMarkRestDay(entry.date)}
                              disabled={isCurrentlySaving}
                              className={`${styles.journalButton}`}
                              style={{ backgroundColor: '#9333ea', color: 'white', border: 'none' }}
                            >
                              Mark as Rest Day
                            </button>
                          );
                        }

                        // State 1: Unsaved changes or not yet saved — show Save (+ Rest Day for today)
                        if (hasUnsaved || (!isSaved && !isCurrentlySaving)) {
                          return (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', alignItems: 'center' }}>
                              <button
                                onClick={() => handleSave(entry.date)}
                                disabled={isCurrentlySaving}
                                className={`${styles.journalButton} ${isCurrentlySaving ? styles.buttonSaving : styles.buttonSave}`}
                              >
                                {isCurrentlySaving ? 'Saving...' : 'Save'}
                              </button>
                              {isToday && noActivityYet && (
                                <button
                                  onClick={() => handleMarkRestDay(entry.date)}
                                  disabled={isCurrentlySaving}
                                  style={{
                                    backgroundColor: 'transparent',
                                    color: '#9333ea',
                                    border: '1px solid #9333ea',
                                    borderRadius: '4px',
                                    padding: '3px 8px',
                                    fontSize: '0.7rem',
                                    fontWeight: '600',
                                    cursor: 'pointer',
                                    whiteSpace: 'nowrap'
                                  }}
                                >
                                  Rest Day
                                </button>
                              )}
                            </div>
                          );
                        }

                        // State 2: Just saved but no analysis yet - Show temporary "Saved!" state
                        if (isSaved && !hasAnalysis) {
                          return (
                            <button
                              disabled
                              className={`${styles.journalButton} ${styles.buttonSaved}`}
                            >
                              ✅ Saved!
                            </button>
                          );
                        }

                        // State 3: Analysis available - Show Analysis button
                        if (hasAnalysis) {
                          return (
                            <button
                              onClick={() => openAutopsyModal(entry)}
                              className={`${styles.journalButton} ${styles.buttonAnalysis}`}
                            >
                              🔍 Analysis
                            </button>
                          );
                        }

                        // Fallback state - shouldn't happen
                        return (
                          <button
                            disabled
                            className={`${styles.journalButton} ${styles.buttonFallback}`}
                          >
                            --
                          </button>
                        );
                      })()}
                    </td>
                  </tr>
                  )}
                  {/* End of next-incomplete/regular row conditional */}

                </React.Fragment>
              ))}
            </tbody>
          </table>
        </div>

        {/* Summary section for all autopsies if any exist */}
        {journalData.some(entry => entry.ai_autopsy.autopsy_analysis) && (
          <div style={{
            marginTop: '2rem',
            padding: '16px',
            backgroundColor: '#f8f9fa',
            borderRadius: '8px',
            border: '1px solid #e9ecef'
          }}>
            <h3 style={{
              margin: '0 0 12px 0',
              color: '#374151',
              fontSize: '1.1rem'
            }}>
              📊 Training Analysis Summary
            </h3>
            <div style={{ fontSize: '0.9rem', color: '#6b7280' }}>
              {journalData.filter(entry => entry.ai_autopsy.autopsy_analysis).length} autopsy analysis(es) available.
              Click "🔍 View Analysis" buttons above to expand individual insights.
            </div>
          </div>
        )}

        {/* Strava Branding Compliance */}
        <div style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          marginTop: '20px',
          paddingTop: '15px',
          borderTop: '1px solid #e5e7eb',
          fontSize: '0.9rem'
        }}>
          <span style={{
            fontWeight: 'bold',
            color: '#FC5200',
            letterSpacing: '0.5px'
          }}>
            POWERED BY STRAVA
          </span>
        </div>
      </div>

      {/* Full-Screen Autopsy Modal */}
      {modalOpen && modalAutopsy && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.7)',
          zIndex: 1000,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '20px'
        }}
        onClick={closeAutopsyModal}
        >
          <div style={{
            backgroundColor: 'white',
            borderRadius: '12px',
            width: '95vw',
            maxHeight: '85vh',
            maxWidth: '1600px',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)'
          }}
          onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div style={{
              padding: '24px 32px',
              borderBottom: '2px solid #e5e7eb',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              backgroundColor: '#f8f9fa'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                <h2 style={{
                  margin: 0,
                  color: '#1f2937',
                  fontSize: '1.5rem',
                  fontWeight: '700'
                }}>
                  AI Training Analysis
                </h2>
                <div style={{
                  fontSize: '1.1rem',
                  color: '#6b7280',
                  fontWeight: '500'
                }}>
                  {formatFullDate(modalAutopsy.date)}
                </div>
                {modalAutopsy.ai_autopsy.alignment_score && (
                  <div style={{
                    padding: '8px 16px',
                    backgroundColor: getAlignmentScoreColor(modalAutopsy.ai_autopsy.alignment_score),
                    color: 'white',
                    borderRadius: '20px',
                    fontSize: '1rem',
                    fontWeight: '700'
                  }}>
                    Alignment: {modalAutopsy.ai_autopsy.alignment_score}/10
                  </div>
                )}
              </div>
              <button
                onClick={closeAutopsyModal}
                style={{
                  backgroundColor: '#ef4444',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  padding: '12px 24px',
                  fontSize: '1rem',
                  fontWeight: '600',
                  cursor: 'pointer',
                  transition: 'background-color 0.2s'
                }}
                onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#dc2626'}
                onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#ef4444'}
              >
                ✕ Close
              </button>
            </div>

            {/* Modal Body - Multi-Column Layout */}
            <div style={{
              flex: 1,
              padding: '32px',
              overflowY: 'auto',
              backgroundColor: '#ffffff'
            }}>
              {(() => {
                const text = modalAutopsy.ai_autopsy.autopsy_analysis || '';
                const rawParagraphs = text.split('\n\n').filter(p => p.trim());

                // Strip noise: --- separators, standalone alignment score lines,
                // and LLM preamble headers that duplicate modal header info
                const paragraphs = rawParagraphs.filter(p => {
                  const t = p.trim();
                  if (/^-{2,}$/.test(t)) return false;                        // --- separators
                  if (/^ALIGNMENT_SCORE:\s*\d/i.test(t)) return false;        // ALIGNMENT_SCORE: 7/10
                  if (/^\d+\/10$/.test(t)) return false;                      // standalone 7/10
                  if (/^TRAINING AUTOPSY ANALYSIS/i.test(t)) return false;    // LLM preamble header
                  return true;
                });

                // Split at section boundaries — find the section header closest to midpoint
                const sectionIndices = paragraphs.reduce<number[]>((acc, p, i) => {
                  if (p.match(/^[A-Z\s&':]+:/) && i > 0) acc.push(i);
                  return acc;
                }, []);
                const midpoint = Math.ceil(paragraphs.length / 2);
                const splitAt = sectionIndices.length > 0
                  ? sectionIndices.reduce((prev, curr) =>
                      Math.abs(curr - midpoint) < Math.abs(prev - midpoint) ? curr : prev)
                  : midpoint;
                const column1 = paragraphs.slice(0, splitAt);
                const column2 = paragraphs.slice(splitAt);
                
                return (
                  <div style={{
                    display: 'flex',
                    gap: '40px',
                    position: 'relative',
                    alignItems: 'flex-start',
                    justifyContent: 'center',
                    maxWidth: '100%'
                  }}>
                    {/* Column 1 */}
                    <div style={{
                      flex: '0 1 auto',
                      maxWidth: '70ch',
                      fontSize: '0.95rem',
                      lineHeight: '1.6',
                      color: '#374151',
                      textAlign: 'left',
                      paddingRight: '20px'
                    }}>
                      {column1.map((para, idx) => {
                        // Detect section headings (all caps followed by colon)
                        const isSection = para.match(/^[A-Z\s&']+:/);
                        
                        if (isSection) {
                          return (
                            <div key={`col1-${idx}`} style={{
                              marginTop: idx > 0 ? '2em' : '0',
                              marginBottom: '1em',
                              paddingBottom: '0.5em',
                              borderBottom: '2px solid #3b82f6'
                            }}>
                              <h3 style={{
                                margin: 0,
                                fontSize: '1.05rem',
                                fontWeight: '700',
                                color: '#1f2937',
                                letterSpacing: '0.02em'
                              }}>
                                {para}
                              </h3>
                            </div>
                          );
                        }
                        
                        return (
                          <p key={`col1-${idx}`} style={{ 
                            margin: '0 0 1.2em 0',
                            fontWeight: '400'
                          }}>
                            {formatBoldText(para)}
                          </p>
                        );
                      })}
                    </div>
                    
                    {/* Column Divider */}
                    <div style={{
                      width: '2px',
                      backgroundColor: '#d1d5db',
                      margin: '0 20px'
                    }} />
                    
                    {/* Column 2 */}
                    <div style={{
                      flex: '0 1 auto',
                      maxWidth: '70ch',
                      fontSize: '0.95rem',
                      lineHeight: '1.6',
                      color: '#374151',
                      textAlign: 'left',
                      paddingLeft: '20px'
                    }}>
                      {column2.map((para, idx) => {
                        // Detect section headings (all caps followed by colon)
                        const isSection = para.match(/^[A-Z\s&']+:/);
                        
                        if (isSection) {
                          return (
                            <div key={`col2-${idx}`} style={{
                              marginTop: idx > 0 ? '2em' : '0',
                              marginBottom: '1em',
                              paddingBottom: '0.5em',
                              borderBottom: '2px solid #3b82f6'
                            }}>
                              <h3 style={{
                                margin: 0,
                                fontSize: '1.05rem',
                                fontWeight: '700',
                                color: '#1f2937',
                                letterSpacing: '0.02em'
                              }}>
                                {para}
                              </h3>
                            </div>
                          );
                        }
                        
                        return (
                          <p key={`col2-${idx}`} style={{ 
                            margin: '0 0 1.2em 0',
                            fontWeight: '400'
                          }}>
                            {formatBoldText(para)}
                          </p>
                        );
                      })}
                    </div>
                  </div>
                );
              })()}
            </div>

            {/* Modal Footer */}
            {modalAutopsy.ai_autopsy.generated_at && (
              <div style={{
                padding: '16px 32px',
                borderTop: '1px solid #e5e7eb',
                backgroundColor: '#f8f9fa',
                fontSize: '0.875rem',
                color: '#6b7280',
                fontStyle: 'italic',
                textAlign: 'right'
              }}>
                Generated: {new Date(modalAutopsy.ai_autopsy.generated_at).toLocaleString()}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default JournalPage;