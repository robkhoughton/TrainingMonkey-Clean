/**
 * PostWorkoutEntryPage — dark mode, full-screen post-workout debrief.
 *
 * Shown when the app detects a recent Strava activity with no subjectives logged.
 * Flow: form → saving → autopsy (inline)
 */
import React, { useState, useEffect } from 'react';

interface Props {
  activityName: string | null;
  activityDate: string | null;
  onDismiss: () => void;
  onNextWorkout: () => void;
}

type Phase = 'form' | 'saving' | 'autopsy';

interface AutopsyResult {
  analysis: string;
  alignment_score: number | null;
}

// ─── Signal quality (matches Journal page logic) ──────────────────────────────
const PHYSIO_KEYWORDS = [
  'legs', 'leg', 'breathing', 'breath', 'lungs', 'lung',
  'heart', 'heavy', 'sharp', 'tight', 'fatigued', 'fatigue',
  'strong', 'flat', 'dead', 'muscles', 'muscle', 'tired',
  'fresh', 'stiff', 'sore', 'weak', 'powerful', 'labored',
  'sluggish', 'snappy', 'responsive', 'burn', 'burning',
  'ache', 'pain', 'effort', 'exhausted', 'energized',
];
const EXO_KEYWORDS = [
  'sleep', 'slept', 'nutrition', 'fuel', 'fueling', 'stress',
  'heat', 'cold', 'altitude', 'hydration', 'hydrated',
  'dehydrated', 'alcohol', 'food', 'eating', 'ate',
  'drank', 'drink', 'weather', 'conditions', 'sick',
  'illness', 'coffee', 'work', 'travel', 'humidity',
  'humid', 'wind', 'rain', 'snow', 'hot', 'nausea',
  'stomach', 'busy', 'late', 'early',
];
const LEVEL_CONFIG = [
  { label: 'No Signal',  color: '#9ca3af' },
  { label: 'Baseline',   color: '#f59e0b' },
  { label: 'Developing', color: '#d97706' },
  { label: 'Clear',      color: '#6B8F7F' },
  { label: 'Diagnostic', color: '#16a34a' },
];
const HINTS = [
  '— keep writing',
  '— describe how you felt physically',
  '— add a context factor (sleep, heat, stress…)',
  '— add more depth',
  '',
];

function noteSignal(text: string): { bars: boolean[]; level: number } {
  const lower = text.toLowerCase();
  const wordCount = text.trim().split(/\s+/).filter(Boolean).length;
  const physioHits = PHYSIO_KEYWORDS.filter(k => lower.includes(k)).length;
  const exoHits = EXO_KEYWORDS.filter(k => lower.includes(k)).length;
  const bars = [
    wordCount >= 8  || physioHits > 0 || exoHits > 0,
    wordCount >= 16 || (physioHits > 0 && exoHits > 0),
    (wordCount >= 16 && (physioHits > 0 || exoHits > 0)) || wordCount >= 24 || physioHits >= 2 || exoHits >= 2,
    wordCount >= 24 && physioHits > 0 && exoHits > 0,
  ];
  return { bars, level: bars.filter(Boolean).length };
}

// ─── Helpers ──────────────────────────────────────────────────────────────────
function formatDate(dateStr: string | null): string {
  if (!dateStr) return '';
  try {
    return new Date(dateStr + 'T12:00:00').toLocaleDateString('en-US', {
      weekday: 'long', month: 'long', day: 'numeric'
    });
  } catch { return dateStr; }
}

function alignmentColor(score: number | null): string {
  if (score === null) return '#7D9CB8';
  if (score >= 8) return '#6B8F7F';
  if (score >= 6) return '#d97706';
  if (score >= 4) return '#fb923c';
  return '#ef4444';
}

const SAVING_MESSAGES = [
  'Analyzing your effort...',
  'Comparing prescribed vs actual...',
  'Building your debrief...',
  'Calibrating athlete model...',
];

const CARBON: React.CSSProperties = {
  background: '#1B2E4B',
  backgroundImage: [
    'linear-gradient(135deg, rgba(255,255,255,0.04) 25%, transparent 25%)',
    'linear-gradient(225deg, rgba(255,255,255,0.04) 25%, transparent 25%)',
    'linear-gradient(315deg, rgba(255,255,255,0.04) 25%, transparent 25%)',
    'linear-gradient(45deg,  rgba(255,255,255,0.04) 25%, transparent 25%)',
  ].join(', '),
  backgroundSize: '4px 4px',
};

// ─── Slider ──────────────────────────────────────────────────────────────────
interface SliderProps {
  label: string;
  min: number; max: number; step: number;
  value: number; onChange: (v: number) => void;
  leftLabel: string; rightLabel: string;
  accentColor?: string;
}

const DarkSlider: React.FC<SliderProps> = ({
  label, min, max, step, value, onChange, leftLabel, rightLabel, accentColor = '#6B8F7F'
}) => {
  const pct = ((value - min) / (max - min)) * 100;
  return (
    <div style={{ marginBottom: '28px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '10px' }}>
        <label style={{ fontSize: '0.8rem', color: '#7D9CB8', letterSpacing: '0.08em', textTransform: 'uppercase', fontWeight: '600' }}>
          {label}
        </label>
        <span style={{ fontSize: '1.5rem', fontWeight: '700', color: '#E6F0FF', fontVariantNumeric: 'tabular-nums' }}>
          {value}
        </span>
      </div>
      <div style={{ position: 'relative', height: '4px', backgroundColor: '#162440', borderRadius: '2px', margin: '8px 0 6px' }}>
        <div style={{ position: 'absolute', left: 0, top: 0, height: '100%', width: `${pct}%`, backgroundColor: accentColor, borderRadius: '2px', transition: 'width 0.1s ease' }} />
        <input
          type="range" min={min} max={max} step={step} value={value}
          onChange={e => onChange(Number(e.target.value))}
          style={{ position: 'absolute', top: '-8px', left: 0, width: '100%', height: '20px', opacity: 0, cursor: 'pointer', margin: 0 }}
        />
        <div style={{
          position: 'absolute', left: `${pct}%`, top: '50%',
          transform: 'translate(-50%, -50%)',
          width: '16px', height: '16px', backgroundColor: accentColor, borderRadius: '50%',
          boxShadow: '0 0 0 3px rgba(107,143,127,0.2)',
          transition: 'left 0.1s ease', pointerEvents: 'none'
        }} />
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: '#7D9CB8', marginTop: '4px' }}>
        <span>{leftLabel}</span><span>{rightLabel}</span>
      </div>
    </div>
  );
};

// ─── Main component ──────────────────────────────────────────────────────────
const PostWorkoutEntryPage: React.FC<Props> = ({ activityName, activityDate, onDismiss, onNextWorkout }) => {
  const [phase, setPhase]     = useState<Phase>('form');
  const [energy, setEnergy]   = useState(3);
  const [rpe, setRpe]         = useState(5);
  const [pain, setPain]       = useState(0);
  const [notes, setNotes]     = useState('');
  const [touched, setTouched] = useState(false);
  const [savingMsg, setSavingMsg] = useState(SAVING_MESSAGES[0]);
  const [autopsy, setAutopsy] = useState<AutopsyResult | null>(null);
  const [error, setError]     = useState<string | null>(null);
  const [msgIdx, setMsgIdx]   = useState(0);

  useEffect(() => {
    if (phase !== 'saving') return;
    const id = setInterval(() => {
      setMsgIdx(i => {
        const next = (i + 1) % SAVING_MESSAGES.length;
        setSavingMsg(SAVING_MESSAGES[next]);
        return next;
      });
    }, 1800);
    return () => clearInterval(id);
  }, [phase]);

  const touch = (fn: (v: number) => void) => (v: number) => { fn(v); setTouched(true); };

  const signal = notes.trim().length > 0 ? noteSignal(notes) : null;
  const signalCfg = signal ? LEVEL_CONFIG[signal.level] : null;

  const handleSave = async () => {
    if (!activityDate) return;
    setPhase('saving');
    setError(null);
    setSavingMsg(SAVING_MESSAGES[0]);
    setMsgIdx(0);
    try {
      const resp = await fetch('/api/journal', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          date: activityDate,
          energy_level: energy,
          rpe_score: rpe,
          pain_percentage: pain,
          notes: notes.trim() || null,
        }),
      });
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.error || 'Failed to save');
      setAutopsy({ analysis: data.autopsy_analysis || '', alignment_score: data.alignment_score ?? null });
      setPhase('autopsy');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong');
      setPhase('form');
    }
  };

  // ─── Form phase ──────────────────────────────────────────────────────────
  if (phase === 'form') {
    return (
      <div style={{ minHeight: '100vh', backgroundColor: '#1B2E4B', display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '48px 24px 80px' }}>
        <div style={{ width: '100%', maxWidth: '520px' }}>

          {/* Header */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '8px' }}>
            <div style={{ fontSize: '0.7rem', letterSpacing: '0.12em', color: '#7D9CB8', textTransform: 'uppercase', fontWeight: '600' }}>
              Workout Debrief
            </div>
            <div style={{ fontSize: '0.75rem', color: '#7D9CB8' }}>
              {formatDate(activityDate)}
            </div>
          </div>
          <h1 style={{ margin: '0 0 32px', fontSize: '1.5rem', fontWeight: '700', color: '#E6F0FF', lineHeight: '1.3' }}>
            {activityName || 'Workout'}
          </h1>

          {/* Form card */}
          <div style={{ ...CARBON, border: '1px solid rgba(255,87,34,0.7)', borderRadius: '8px', padding: '32px 32px 28px', marginBottom: '20px' }}>
            <DarkSlider
              label="Energy Level" min={1} max={5} step={1}
              value={energy} onChange={touch(setEnergy)}
              leftLabel="Depleted" rightLabel="Strong"
              accentColor="#6B8F7F"
            />
            <DarkSlider
              label="Effort / RPE" min={1} max={10} step={1}
              value={rpe} onChange={touch(setRpe)}
              leftLabel="Easy" rightLabel="Max"
              accentColor="#7D9CB8"
            />
            <DarkSlider
              label="Pain / Discomfort" min={0} max={100} step={5}
              value={pain} onChange={touch(setPain)}
              leftLabel="None" rightLabel="Severe"
              accentColor={pain >= 60 ? '#ef4444' : pain >= 30 ? '#d97706' : '#7D9CB8'}
            />

            {/* Notes */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <label style={{ fontSize: '0.8rem', color: '#7D9CB8', letterSpacing: '0.08em', textTransform: 'uppercase', fontWeight: '600' }}>
                  Notes
                </label>
                {signal && signalCfg && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <div style={{ display: 'flex', gap: '2px', alignItems: 'flex-end' }}>
                      {[0, 1, 2, 3].map(i => (
                        <div key={i} style={{
                          width: '4px', height: `${8 + i * 4}px`, borderRadius: '2px',
                          backgroundColor: signal.bars[i] ? signalCfg.color : 'rgba(125,156,184,0.2)',
                          transition: 'background-color 0.18s ease',
                        }} />
                      ))}
                    </div>
                    <span style={{ fontSize: '10px', fontWeight: '700', color: signalCfg.color, letterSpacing: '0.08em', textTransform: 'uppercase' }}>
                      {signalCfg.label}
                    </span>
                    {signal.level < 4 && (
                      <span style={{ fontSize: '10px', color: '#7D9CB8' }}>
                        {HINTS[signal.level]}
                      </span>
                    )}
                  </div>
                )}
              </div>
              <textarea
                value={notes}
                onChange={e => setNotes(e.target.value)}
                placeholder="How did it feel? Any deviations from the plan?"
                rows={4}
                style={{
                  width: '100%', backgroundColor: '#162440',
                  border: '1px solid rgba(125,156,184,0.3)', borderRadius: '4px',
                  color: '#E6F0FF', fontSize: '0.9rem', lineHeight: '1.6',
                  padding: '12px 14px', resize: 'vertical', outline: 'none',
                  boxSizing: 'border-box',
                }}
              />
            </div>
          </div>

          {error && (
            <div style={{ marginBottom: '12px', padding: '10px 14px', backgroundColor: 'rgba(239,68,68,0.12)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: '4px', color: '#fca5a5', fontSize: '0.85rem' }}>
              {error}
            </div>
          )}

          {/* Actions */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <button
              onClick={handleSave}
              disabled={!touched}
              style={{
                backgroundColor: touched ? '#FF5722' : '#2d4a6e',
                color: touched ? 'white' : '#7D9CB8',
                border: 'none', borderRadius: '4px',
                padding: '14px 32px', fontSize: '0.9rem', fontWeight: '700',
                letterSpacing: '0.06em', cursor: touched ? 'pointer' : 'not-allowed',
                textTransform: 'uppercase',
                transition: 'background-color 0.3s ease, color 0.3s ease',
              }}
            >
              Log Result
            </button>
            <button
              onClick={onDismiss}
              style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#7D9CB8', fontSize: '0.85rem', padding: '0' }}
            >
              Skip for now
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ─── Saving phase ─────────────────────────────────────────────────────────
  if (phase === 'saving') {
    return (
      <div style={{ minHeight: '100vh', backgroundColor: '#1B2E4B', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '24px' }}>
        <div style={{ width: '40px', height: '40px', border: '2px solid #2d4a6e', borderTop: '2px solid #FF5722', borderRadius: '50%', animation: 'spin 1s linear infinite' }} />
        <div style={{ color: '#7D9CB8', fontSize: '0.9rem', letterSpacing: '0.04em' }}>{savingMsg}</div>
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    );
  }

  // ─── Autopsy phase ────────────────────────────────────────────────────────
  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#1B2E4B', display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '48px 24px 80px' }}>
      <div style={{ width: '100%', maxWidth: '640px' }}>

        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '8px' }}>
          <div style={{ fontSize: '0.7rem', letterSpacing: '0.12em', color: '#7D9CB8', textTransform: 'uppercase', fontWeight: '600' }}>
            Debrief — {formatDate(activityDate)}
          </div>
          {autopsy?.alignment_score != null && (
            <div style={{
              display: 'inline-flex', alignItems: 'center', gap: '6px',
              padding: '4px 12px',
              backgroundColor: 'rgba(0,0,0,0.2)',
              border: `1px solid ${alignmentColor(autopsy.alignment_score)}`,
              borderRadius: '4px',
            }}>
              <span style={{ fontSize: '0.7rem', color: '#7D9CB8', letterSpacing: '0.06em', textTransform: 'uppercase' }}>Alignment</span>
              <span style={{ fontSize: '1.1rem', fontWeight: '700', color: alignmentColor(autopsy.alignment_score), fontVariantNumeric: 'tabular-nums' }}>
                {autopsy.alignment_score}/10
              </span>
            </div>
          )}
        </div>
        <h1 style={{ margin: '0 0 32px', fontSize: '1.4rem', fontWeight: '700', color: '#E6F0FF' }}>
          {activityName || 'Workout'}
        </h1>

        {/* Analysis card */}
        <div style={{
          ...CARBON,
          border: '1px solid rgba(255,87,34,0.7)',
          borderLeft: `3px solid ${alignmentColor(autopsy?.alignment_score ?? null)}`,
          borderRadius: '8px', padding: '28px 32px', marginBottom: '24px',
        }}>
          <div style={{ color: '#E6F0FF', fontSize: '0.9rem', lineHeight: '1.75', whiteSpace: 'pre-wrap', maxWidth: '75ch' }}>
            {autopsy?.analysis || 'No analysis generated.'}
          </div>
        </div>

        {/* Actions */}
        <div style={{ display: 'flex', gap: '12px' }}>
          <button
            onClick={onDismiss}
            style={{ backgroundColor: '#FF5722', color: 'white', border: 'none', borderRadius: '4px', padding: '12px 28px', fontSize: '0.875rem', fontWeight: '700', letterSpacing: '0.06em', cursor: 'pointer', textTransform: 'uppercase' }}
          >
            Check Training Status
          </button>
          <button
            onClick={onNextWorkout}
            style={{ backgroundColor: 'transparent', color: '#E6F0FF', border: '1px solid #2d4a6e', borderRadius: '4px', padding: '12px 28px', fontSize: '0.875rem', fontWeight: '600', cursor: 'pointer' }}
          >
            See Next Workout
          </button>
        </div>
      </div>
    </div>
  );
};

export default PostWorkoutEntryPage;
