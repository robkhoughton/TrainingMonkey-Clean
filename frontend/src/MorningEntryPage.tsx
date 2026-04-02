/**
 * MorningEntryPage — collect morning subjectives before routing to Today.
 *
 * Shows watch data (HRV, RHR, sleep) as reference so the user can make
 * an informed input. No readiness verdict here — that surfaces on Today
 * after subjectives are submitted and synthesized.
 *
 * Flow: see watch data → set sliders → save → Today tab (shows verdict)
 */
import React, { useState, useEffect } from 'react';

interface WellnessTiles {
  hrv_value: number | null;
  hrv_baseline_30d: number | null;
  resting_hr: number | null;
  rhr_baseline_7d: number | null;
  sleep_duration_secs: number | null;
  sleep_score: number | null;
  weight: number | null;
  weight_baseline_7d: number | null;
  spo2: number | null;
  hrv_source: string | null;
  sleep_quality: number | null;
  morning_soreness: number | null;
}

interface Props {
  onToday: () => void;
  onNextWorkout: () => void;
  onDismiss: () => void;
}

function todayStr(): string {
  return new Date().toISOString().split('T')[0];
}

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
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
        <label style={{
          fontSize: '0.8rem', color: '#7D9CB8', letterSpacing: '0.08em',
          textTransform: 'uppercase', fontWeight: '600'
        }}>
          {label}
        </label>
        <span style={{ fontSize: '1.5rem', fontWeight: '700', color: '#E6F0FF', fontVariantNumeric: 'tabular-nums' }}>
          {value}
        </span>
      </div>
      <div style={{ position: 'relative', height: '4px', backgroundColor: '#162440', borderRadius: '2px', margin: '8px 0 6px' }}>
        <div style={{
          position: 'absolute', left: 0, top: 0, height: '100%',
          width: `${pct}%`, backgroundColor: accentColor, borderRadius: '2px',
          transition: 'width 0.1s ease'
        }} />
        <input
          type="range" min={min} max={max} step={step} value={value}
          onChange={e => onChange(Number(e.target.value))}
          style={{
            position: 'absolute', top: '-8px', left: 0, width: '100%',
            height: '20px', opacity: 0, cursor: 'pointer', margin: 0
          }}
        />
        <div style={{
          position: 'absolute', left: `${pct}%`, top: '50%',
          transform: 'translate(-50%, -50%)',
          width: '16px', height: '16px', backgroundColor: accentColor, borderRadius: '50%',
          boxShadow: `0 0 0 3px rgba(107,143,127,0.2)`,
          transition: 'left 0.1s ease', pointerEvents: 'none'
        }} />
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: '#7D9CB8', marginTop: '4px' }}>
        <span>{leftLabel}</span><span>{rightLabel}</span>
      </div>
    </div>
  );
};

// ─── Watch data tile ──────────────────────────────────────────────────────────
interface TileProps {
  label: string;
  value: React.ReactNode;
  sub?: React.ReactNode;
  accent?: boolean;
  alert?: boolean;
}

const WellnessTile: React.FC<TileProps> = ({ label, value, sub, accent, alert }) => (
  <div style={{
    backgroundColor: alert ? 'rgba(239,68,68,0.1)' : '#162440',
    border: `1px solid ${alert ? 'rgba(239,68,68,0.3)' : accent ? 'rgba(107,143,127,0.3)' : 'rgba(45,74,110,0.8)'}`,
    borderRadius: '6px',
    padding: '10px 14px',
    minWidth: '80px',
  }}>
    <div style={{ fontSize: '0.65rem', color: '#7D9CB8', letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: '4px' }}>
      {label}
    </div>
    <div style={{
      fontSize: '1.05rem', fontWeight: '700',
      color: alert ? '#ef4444' : accent ? '#6B8F7F' : '#E6F0FF',
      lineHeight: '1.2'
    }}>
      {value}
    </div>
    {sub && (
      <div style={{ fontSize: '0.65rem', color: '#7D9CB8', marginTop: '3px' }}>{sub}</div>
    )}
  </div>
);

const flagStyle: React.CSSProperties = {
  fontSize: '0.7rem', color: '#7D9CB8',
  backgroundColor: 'rgba(125,156,184,0.12)',
  border: '1px solid rgba(125,156,184,0.2)',
  borderRadius: '3px', padding: '2px 8px',
};

// ─── Main component ──────────────────────────────────────────────────────────
const MorningEntryPage: React.FC<Props> = ({ onToday, onNextWorkout, onDismiss }) => {
  const today = todayStr();
  const [sleepQuality, setSleepQuality] = useState(3);
  const [soreness, setSoreness] = useState(0);
  const [notes, setNotes] = useState('');
  const [wellness, setWellness] = useState<WellnessTiles | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [touched, setTouched] = useState(false);

  useEffect(() => {
    fetch(`/api/readiness?date=${today}`, { credentials: 'include' })
      .then(r => r.json())
      .then(data => {
        setWellness(data);
        // Pre-populate only from a prior save today
        if (data.sleep_quality != null) { setSleepQuality(data.sleep_quality); setTouched(true); }
        if (data.morning_soreness != null) { setSoreness(data.morning_soreness); setTouched(true); }
      })
      .catch(() => {});
  }, [today]);

  const saveEntry = async () => {
    const resp = await fetch('/api/readiness', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ date: today, sleep_quality: sleepQuality, morning_soreness: soreness }),
    });
    const data = await resp.json();
    if (!data.success) throw new Error(data.error || 'Failed to save');
  };

  const handleSave = async () => {
    setIsSaving(true);
    setError(null);
    try {
      await saveEntry();
      setSaved(true);
      setTimeout(onToday, 1400);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong');
    } finally {
      setIsSaving(false);
    }
  };

  const handleNextWorkout = async () => {
    setIsSaving(true);
    setError(null);
    try {
      await saveEntry();
      onNextWorkout();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong');
      setIsSaving(false);
    }
  };

  const hasWatchData = wellness?.hrv_source === 'intervals_icu';

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

  return (
    <div style={{
      minHeight: '100vh', backgroundColor: '#1B2E4B',
      display: 'flex', flexDirection: 'column', alignItems: 'center',
      padding: '48px 24px 80px',
    }}>
      <div style={{ width: '100%', maxWidth: '520px' }}>

        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '32px' }}>
          <div style={{
            fontSize: '0.7rem', letterSpacing: '0.12em', color: '#7D9CB8',
            textTransform: 'uppercase', fontWeight: '600',
          }}>
            Morning Check-In
          </div>
          <div style={{ fontSize: '0.75rem', color: '#7D9CB8' }}>
            {new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' })}
          </div>
        </div>

        {/* Watch data — reference for the user before they set sliders */}
        {hasWatchData && (
          <div style={{ marginBottom: '28px' }}>
            <div style={{
              fontSize: '0.65rem', color: '#7D9CB8', letterSpacing: '0.1em',
              textTransform: 'uppercase', fontWeight: '600', marginBottom: '10px'
            }}>
              Last night
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
              {wellness!.hrv_value !== null && (() => {
                const ratio = wellness!.hrv_baseline_30d ? wellness!.hrv_value! / wellness!.hrv_baseline_30d : null;
                const suppressed = ratio !== null && ratio < 0.85;
                return (
                  <WellnessTile
                    label="HRV"
                    value={`${wellness!.hrv_value!.toFixed(0)}ms${ratio ? (ratio < 0.85 ? ' ↓' : ratio > 1.15 ? ' ↑' : '') : ''}`}
                    sub={wellness!.hrv_baseline_30d ? `avg ${wellness!.hrv_baseline_30d.toFixed(0)}ms` : undefined}
                    accent={!suppressed && ratio !== null && ratio >= 1.0}
                    alert={suppressed}
                  />
                );
              })()}
              {wellness!.resting_hr !== null && (() => {
                const diff = wellness!.rhr_baseline_7d
                  ? ((wellness!.resting_hr! - wellness!.rhr_baseline_7d) / wellness!.rhr_baseline_7d) * 100
                  : null;
                const elevated = diff !== null && diff >= 8;
                return (
                  <WellnessTile
                    label="Resting HR"
                    value={`${wellness!.resting_hr}bpm${diff !== null ? (diff >= 5 ? ' ↑' : diff <= -5 ? ' ↓' : '') : ''}`}
                    sub={wellness!.rhr_baseline_7d ? `avg ${wellness!.rhr_baseline_7d.toFixed(0)}bpm` : undefined}
                    alert={elevated}
                  />
                );
              })()}
              {wellness!.sleep_duration_secs !== null && (() => {
                const hrs = wellness!.sleep_duration_secs! / 3600;
                return (
                  <WellnessTile
                    label="Sleep"
                    value={`${hrs.toFixed(1)}hrs`}
                    sub={wellness!.sleep_score !== null ? `score ${wellness!.sleep_score}/100` : undefined}
                    alert={hrs < 6}
                  />
                );
              })()}
              {wellness!.weight !== null && (
                <WellnessTile
                  label="Weight"
                  value={`${wellness!.weight!.toFixed(1)}kg`}
                  sub={wellness!.weight_baseline_7d != null
                    ? `${wellness!.weight! - wellness!.weight_baseline_7d >= 0 ? '+' : ''}${(wellness!.weight! - wellness!.weight_baseline_7d).toFixed(1)}kg`
                    : undefined}
                />
              )}
              {wellness!.spo2 !== null && wellness!.spo2 < 95 && (
                <WellnessTile label="SpO2" value={`${wellness!.spo2.toFixed(0)}%`} alert />
              )}
            </div>
          </div>
        )}

        {/* Input form */}
        <div style={{
          ...CARBON,
          border: '1px solid rgba(255,87,34,0.7)',
          borderRadius: '8px',
          padding: '28px 28px 24px',
          marginBottom: '20px',
        }}>
          <DarkSlider
            label="Sleep Quality"
            min={1} max={5} step={1}
            value={sleepQuality}
            onChange={v => { setSleepQuality(v); setTouched(true); }}
            leftLabel="Poor" rightLabel="Excellent"
            accentColor="#6B8F7F"
          />
          <DarkSlider
            label="Morning Soreness"
            min={0} max={100} step={5}
            value={soreness}
            onChange={v => { setSoreness(v); setTouched(true); }}
            leftLabel="Fresh" rightLabel="Very sore"
            accentColor={soreness >= 70 ? '#d97706' : '#7D9CB8'}
          />

          <div>
            <div style={{
              fontSize: '0.8rem', color: '#7D9CB8', letterSpacing: '0.08em',
              textTransform: 'uppercase', fontWeight: '600', marginBottom: '8px'
            }}>
              Notes <span style={{ fontSize: '0.7rem', fontWeight: '400', letterSpacing: 0, textTransform: 'none' }}>(optional)</span>
            </div>
            <textarea
              value={notes}
              onChange={e => setNotes(e.target.value)}
              placeholder="Anything notable this morning?"
              rows={3}
              style={{
                width: '100%', backgroundColor: '#162440',
                border: '1px solid rgba(125,156,184,0.3)', borderRadius: '4px',
                color: '#E6F0FF', fontSize: '0.875rem', lineHeight: '1.6',
                padding: '10px 12px', resize: 'vertical', outline: 'none',
                boxSizing: 'border-box',
              }}
            />
          </div>
        </div>

        {error && (
          <div style={{
            marginBottom: '12px', padding: '10px 14px',
            backgroundColor: 'rgba(239,68,68,0.12)', border: '1px solid rgba(239,68,68,0.3)',
            borderRadius: '4px', color: '#fca5a5', fontSize: '0.85rem'
          }}>
            {error}
          </div>
        )}

        {/* Actions */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <button
            onClick={handleSave}
            disabled={isSaving || saved || !touched}
            style={{
              backgroundColor: saved ? '#6B8F7F' : touched ? '#FF5722' : '#2d4a6e',
              color: touched ? 'white' : '#7D9CB8',
              border: 'none', borderRadius: '4px',
              padding: '14px 32px', fontSize: '0.9rem', fontWeight: '700',
              letterSpacing: '0.06em', cursor: (isSaving || saved || !touched) ? 'not-allowed' : 'pointer',
              textTransform: 'uppercase', opacity: isSaving ? 0.8 : 1,
              transition: 'background-color 0.3s ease, color 0.3s ease',
            }}
          >
            {saved ? 'Logged' : isSaving ? 'Saving...' : 'Check Training Status'}
          </button>
          <button
            onClick={handleNextWorkout}
            disabled={isSaving || !touched}
            style={{
              backgroundColor: 'transparent',
              color: touched ? '#E6F0FF' : '#7D9CB8',
              border: `1px solid ${touched ? '#2d4a6e' : 'rgba(45,74,110,0.5)'}`,
              borderRadius: '4px',
              padding: '13px 24px', fontSize: '0.875rem', fontWeight: '600',
              cursor: (isSaving || !touched) ? 'not-allowed' : 'pointer',
              transition: 'color 0.3s ease, border-color 0.3s ease',
            }}
          >
            See Next Workout
          </button>
          <button
            onClick={onDismiss}
            style={{
              background: 'none', border: 'none', cursor: 'pointer',
              color: '#7D9CB8', fontSize: '0.85rem', padding: '0',
            }}
          >
            Skip
          </button>
        </div>

      </div>
    </div>
  );
};

export default MorningEntryPage;
