import React, { useState, useEffect, useRef } from 'react';
import { RaceReadinessCard, AthleteModelPanel, RaceReadiness, AthleteModel } from './CoachPage';
import CoachingStyleSpectrum from './CoachingStyleSpectrum';
import RiskToleranceSelector from './RiskToleranceSelector';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine, Legend, ReferenceArea,
} from 'recharts';

// ============================================================================
// INTERFACES
// ============================================================================

interface RaceGoal {
  id: number;
  race_name: string;
  race_date: string;
  race_type: string | null;
  priority: 'A' | 'B' | 'C';
  target_time: string | null;
  notes: string | null;
  elevation_gain_feet: number | null;
  distance_miles: number | null;
}

interface GoalFormData {
  race_name: string;
  race_date: string;
  race_type: string;
  priority: 'A' | 'B' | 'C';
  target_time_h: string;
  target_time_m: string;
  target_time_s: string;
  notes: string;
  elevation_gain_feet: string;
  distance_miles: string;
}

interface AerobicAssessment {
  id: number;
  activity_id: number;
  activity_name: string;
  test_date: string;
  warmup_minutes: number;
  first_half_avg_hr: number;
  second_half_avg_hr: number;
  drift_pct: number;
  aet_bpm: number;
  ant_bpm: number | null;
  gap_pct: number | null;
  gap_status: string | null;
  interpretation: string;
  steady_state_minutes: number;
  avg_pace_sec_per_mi: number | null;
  pace_source: string | null;
  notes: string | null;
  distance_miles: number | null;
}

// Recorded daily effective (dynamic) AeT: measured baseline adjusted for overnight HRV.
// A model output, never a measurement — the chart labels it as such.
interface EffectiveAetDaily {
  date: string;
  baseline_aet: number;
  effective_aet: number;
  aet_offset: number;
  hrv_z: number | null;
  readiness_state: string | null;
  fallback_reason: string | null;
}

interface HRActivity {
  activity_id: number;
  name: string;
  date: string;
  duration_minutes: number;
  avg_heart_rate: number;
  sport_type: string;
  distance_miles: number | null;
  sample_rate: number;
  already_assessed: number;
}

interface HRStreamPoint {
  t: number;  // minutes
  hr: number;
}

interface DriftPreview {
  valid: boolean;
  first_half_avg_hr: number;
  second_half_avg_hr: number;
  drift_pct: number;
  aet_bpm: number;
  interpretation: string;
  steady_state_minutes: number;
  ant_bpm: number | null;
  gap_pct: number | null;
  gap_status: string | null;
  avg_pace_sec_per_mi?: number;
  pace_source?: string;
}

type AeTMethod = 'hr_drift' | 'lactate_step';

interface LactateStageInput {
  grade: string;
  hr: string;
  lactate: string;
}

interface LactateStepTest {
  id: number;
  test_date: string;
  speed: number | null;
  speed_unit: string;
  stages: { stage: number; grade: number | null; hr: number; lactate: number }[];
  baseline_lactate: number | null;
  lt1_bpm: number | null;
  lt1_grade: number | null;
  valid: boolean;
  notes: string | null;
}

interface LactatePreview {
  valid: boolean;
  lt1_bpm?: number;
  lt1_grade?: number | null;
  lt1_stage?: number;
  baseline_lactate?: number;
  peak_lactate?: number;
  rise_threshold_mmol?: number;
  interpretation?: string;
  error?: string;
}

const EMPTY_FORM: GoalFormData = {
  race_name: '',
  race_date: '',
  race_type: 'Trail',
  priority: 'A',
  target_time_h: '',
  target_time_m: '',
  target_time_s: '',
  notes: '',
  elevation_gain_feet: '',
  distance_miles: '',
};

// ============================================================================
// HELPERS
// ============================================================================

const minutesToHMS = (totalMinutes: number | null) => {
  if (!totalMinutes) return { h: '', m: '', s: '' };
  const h = Math.floor(totalMinutes / 60);
  const m = Math.floor(totalMinutes % 60);
  const s = Math.round((totalMinutes % 1) * 60);
  return { h: h.toString(), m: m.toString().padStart(2, '0'), s: s.toString().padStart(2, '0') };
};

const hmsToMinutes = (h: string, m: string, s: string): number | null => {
  if (!h && !m && !s) return null;
  return (parseInt(h || '0', 10) * 60) + parseInt(m || '0', 10) + (parseInt(s || '0', 10) / 60);
};

const formatDate = (iso: string) => {
  const d = new Date(iso + 'T12:00:00');
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
};

// ISO date -> epoch ms at local noon (for a continuous time X-axis, matching formatDate).
const dateToTs = (iso: string) => new Date(iso + 'T12:00:00').getTime();

// Readiness-state palette (matches TodayPage's readiness gauge). Status colors, always
// paired with a text label in the legend/tooltip — never identity by color alone.
const READY_GREEN = '#16a34a';
const READY_AMBER = '#d97706';
const READY_RED   = '#dc2626';
const readinessColor = (state: string | null | undefined) => {
  if (state === 'RED') return READY_RED;
  if (state === 'YELLOW_SYMPATHETIC' || state === 'YELLOW_PARASYMPATHETIC') return READY_AMBER;
  if (state === 'GREEN') return READY_GREEN;
  return '#94a3b8'; // UNKNOWN / no reading
};
const READY_LABEL: Record<string, string> = {
  GREEN: 'Green', YELLOW_SYMPATHETIC: 'Caution',
  YELLOW_PARASYMPATHETIC: 'Deep hole', RED: 'Overreaching', UNKNOWN: 'No reading',
};

// Seconds-per-mile -> "m:ss".
const fmtPace = (sec: number | null | undefined) => {
  if (sec == null || sec <= 0) return null;
  const t = Math.round(sec);
  return `${Math.floor(t / 60)}:${String(t % 60).padStart(2, '0')}`;
};

const SAGE = '#6B8F7F';
const NAVY = '#1B2E4B';

// Dot for the daily effective-AeT line: filled in the day's readiness colour; a hollow
// dashed ring on days the offset was held (HRV stale/absent) so the fallback reads distinct.
const EffectiveDot = (props: any) => {
  const { cx, cy, payload } = props;
  if (cx == null || cy == null || payload?.effective == null) return null;
  if (payload.fallback) {
    return <circle cx={cx} cy={cy} r={3.5} fill="#fff" stroke="#94a3b8" strokeWidth={1.5} strokeDasharray="2 1.5" />;
  }
  return <circle cx={cx} cy={cy} r={3.5} fill={readinessColor(payload.state)} stroke="#fff" strokeWidth={1} />;
};

const AetTooltip = ({ active, payload }: any) => {
  if (!active || !payload?.length) return null;
  const p = payload[0]?.payload || {};
  return (
    <div style={{ background: '#fff', border: '1px solid #d1dce8', borderRadius: '6px', padding: '8px 10px', fontSize: '0.75rem', lineHeight: 1.5 }}>
      <div style={{ fontWeight: 700, color: NAVY, marginBottom: '3px' }}>
        {new Date(p.ts).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
      </div>
      {p.baseline != null && (
        <div style={{ color: NAVY }}>Baseline AeT (measured): <strong>{p.baseline} bpm</strong></div>
      )}
      {p.effective != null && (
        <div style={{ color: SAGE }}>
          Effective AeT (model): <strong>{p.effective} bpm</strong>
          {p.offset ? ` (${p.offset > 0 ? '+' : ''}${p.offset} bpm)` : ''}
        </div>
      )}
      {p.effective != null && (
        <div style={{ color: p.fallback ? '#94a3b8' : readinessColor(p.state) }}>
          {p.fallback ? 'HRV stale/absent — held near baseline' : `Readiness: ${READY_LABEL[p.state] || p.state || '—'}`}
        </div>
      )}
      {p.ant != null && <div style={{ color: '#7D9CB8' }}>AnT: <strong>{p.ant} bpm</strong></div>}
      {p.drift != null && <div style={{ color: '#7D9CB8' }}>Drift: <strong>{Number(p.drift).toFixed(1)}%</strong></div>}
    </div>
  );
};


// ============================================================================
// TACTICAL FORM STYLES
// ============================================================================

const CARBON = {
  backgroundColor: '#1B2E4B',
  backgroundImage: [
    'linear-gradient(135deg, rgba(255,255,255,0.04) 25%, transparent 25%)',
    'linear-gradient(225deg, rgba(255,255,255,0.04) 25%, transparent 25%)',
    'linear-gradient(315deg, rgba(255,255,255,0.04) 25%, transparent 25%)',
    'linear-gradient(45deg,  rgba(255,255,255,0.04) 25%, transparent 25%)',
  ].join(', '),
  backgroundSize: '4px 4px',
};

const tacticalLabel: React.CSSProperties = {
  display: 'block',
  marginBottom: '6px',
  fontSize: '0.72rem',
  fontWeight: 700,
  color: '#7D9CB8',
  textTransform: 'uppercase',
  letterSpacing: '0.08em',
};

const tacticalInput: React.CSSProperties = {
  padding: '7px 10px',
  backgroundColor: '#162440',
  border: '1px solid #7D9CB8',
  borderRadius: '4px',
  color: '#E6F0FF',
  fontSize: '0.875rem',
  width: '100%',
  boxSizing: 'border-box',
  WebkitAppearance: 'none',
  MozAppearance: 'textfield',
} as React.CSSProperties;

// ============================================================================
// RACE GOAL MODAL
// ============================================================================

interface GoalModalProps {
  mode: 'add' | 'edit';
  initialData?: RaceGoal;
  onSave: () => void;
  onClose: () => void;
}

const PANEL_EXPAND_STYLE = `
  @keyframes panelExpand {
    from { opacity: 0; transform: scale(0.88) translateX(28px); }
    to   { opacity: 1; transform: scale(1)    translateX(0);     }
  }
  @keyframes backdropFadeIn {
    from { opacity: 0; }
    to   { opacity: 1; }
  }
`;

const GoalModal: React.FC<GoalModalProps> = ({ mode, initialData, onSave, onClose }) => {
  const [form, setForm] = useState<GoalFormData>(() => {
    if (mode === 'edit' && initialData) {
      const hms = minutesToHMS(initialData.target_time ? parseFloat(initialData.target_time) : null);
      return {
        race_name: initialData.race_name,
        race_date: initialData.race_date,
        race_type: initialData.race_type || 'Trail',
        priority: initialData.priority,
        target_time_h: hms.h,
        target_time_m: hms.m,
        target_time_s: hms.s,
        notes: initialData.notes || '',
        elevation_gain_feet: initialData.elevation_gain_feet != null ? String(initialData.elevation_gain_feet) : '',
        distance_miles: initialData.distance_miles != null ? String(initialData.distance_miles) : '',
      };
    }
    return EMPTY_FORM;
  });

  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const timeMRef = useRef<HTMLInputElement>(null);
  const timeSRef = useRef<HTMLInputElement>(null);

  const set = (field: keyof GoalFormData, value: string) =>
    setForm(f => ({ ...f, [field]: value }));

  const handleSubmit = async () => {
    if (!form.race_name.trim()) { setError('Race name is required'); return; }
    if (!form.race_date) { setError('Race date is required'); return; }

    setIsSaving(true);
    setError(null);

    const payload = {
      race_name: form.race_name.trim(),
      race_date: form.race_date,
      race_type: form.race_type || null,
      priority: form.priority,
      target_time: hmsToMinutes(form.target_time_h, form.target_time_m, form.target_time_s),
      notes: form.notes.trim() || null,
      elevation_gain_feet: form.elevation_gain_feet ? parseFloat(form.elevation_gain_feet) : null,
      distance_miles: form.distance_miles ? parseFloat(form.distance_miles) : null,
    };

    try {
      const url = mode === 'edit' ? `/api/coach/race-goals/${initialData!.id}` : '/api/coach/race-goals';
      const method = mode === 'edit' ? 'PUT' : 'POST';
      const res = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const d = await res.json();
        throw new Error(d.error || 'Failed to save');
      }
      onSave();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save race goal');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <>
      <style>{PANEL_EXPAND_STYLE}</style>
      <div
        style={{
          position: 'fixed', inset: 0, zIndex: 1000,
          backgroundColor: 'rgba(0,0,0,0.65)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          padding: '20px',
          animation: 'backdropFadeIn 0.2s ease-out',
        }}
        onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
      >
        <div style={{
          ...CARBON,
          border: '1px solid rgba(255,87,34,0.7)',
          borderRadius: '8px',
          overflow: 'hidden',
          width: '100%',
          maxWidth: '560px',
          maxHeight: '90vh',
          overflowY: 'auto',
          animation: 'panelExpand 0.25s cubic-bezier(0.34, 1.56, 0.64, 1)',
          transformOrigin: 'right top',
        }}>
          {/* Header */}
          <div style={{
            background: 'linear-gradient(90deg, #E6F0FF 0%, #7D9CB8 50%, #1B2E4B 100%)',
            padding: '12px 24px',
          }}>
          <span style={{ fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.12em', color: '#1B2E4B', textTransform: 'uppercase' }}>
            {mode === 'add' ? 'Add Race Goal' : 'Modify Goal'}
          </span>
        </div>

        <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '18px' }}>

          {error && (
            <div style={{ padding: '10px 14px', backgroundColor: 'rgba(220,38,38,0.08)', borderLeft: '3px solid #dc2626', borderRadius: '4px', fontSize: '0.8rem', color: '#dc2626' }}>
              {error}
            </div>
          )}

          {/* Race Name */}
          <div>
            <label style={tacticalLabel}>Race Name <span style={{ color: 'rgba(255,87,34,0.8)' }}>*</span></label>
            <input
              type="text"
              value={form.race_name}
              onChange={e => set('race_name', e.target.value)}
              style={tacticalInput}
              placeholder="Western States 100"
            />
          </div>

          {/* Date + Priority */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
            <div>
              <label style={tacticalLabel}>Race Date <span style={{ color: 'rgba(255,87,34,0.8)' }}>*</span></label>
              <input type="date" value={form.race_date} onChange={e => set('race_date', e.target.value)} style={tacticalInput} />
            </div>
            <div>
              <label style={tacticalLabel}>Priority</label>
              <select
                value={form.priority}
                onChange={e => set('priority', e.target.value as 'A' | 'B' | 'C')}
                style={{
                  ...tacticalInput,
                  appearance: 'none',
                  backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='6'%3E%3Cpath d='M0 0l5 6 5-6z' fill='%237D9CB8'/%3E%3C/svg%3E")`,
                  backgroundRepeat: 'no-repeat',
                  backgroundPosition: 'right 10px center',
                  paddingRight: '28px',
                } as React.CSSProperties}
              >
                <option value="A">"A" Race — Primary goal</option>
                <option value="B">B Race — Secondary</option>
                <option value="C">C Race — Training/tune-up</option>
              </select>
            </div>
          </div>

          {/* Type + Distance */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
            <div>
              <label style={tacticalLabel}>Race Type</label>
              <select
                value={form.race_type}
                onChange={e => set('race_type', e.target.value)}
                style={{
                  ...tacticalInput,
                  appearance: 'none',
                  backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='6'%3E%3Cpath d='M0 0l5 6 5-6z' fill='%237D9CB8'/%3E%3C/svg%3E")`,
                  backgroundRepeat: 'no-repeat',
                  backgroundPosition: 'right 10px center',
                  paddingRight: '28px',
                } as React.CSSProperties}
              >
                <option value="Trail">Trail</option>
                <option value="Road">Road</option>
                <option value="Other">Other</option>
              </select>
            </div>
            <div>
              <label style={tacticalLabel}>Distance (miles)</label>
              <input
                type="number"
                min="0"
                step="0.1"
                value={form.distance_miles}
                onChange={e => set('distance_miles', e.target.value)}
                style={tacticalInput}
                placeholder="100"
              />
            </div>
          </div>

          {/* Target Time */}
          <div>
            <label style={tacticalLabel}>Target Time</label>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              {[
                { field: 'target_time_h' as const, placeholder: 'H', max: 2, ref: undefined, nextRef: timeMRef },
                { field: 'target_time_m' as const, placeholder: 'MM', max: 2, ref: timeMRef, nextRef: timeSRef },
                { field: 'target_time_s' as const, placeholder: 'SS', max: 2, ref: timeSRef, nextRef: undefined },
              ].map((cfg, i) => (
                <React.Fragment key={cfg.field}>
                  <input
                    ref={cfg.ref}
                    type="number"
                    min="0"
                    max={i === 0 ? 99 : 59}
                    value={form[cfg.field]}
                    onChange={e => {
                      set(cfg.field, e.target.value);
                      if (e.target.value.length >= cfg.max && cfg.nextRef?.current) {
                        cfg.nextRef.current.focus();
                      }
                    }}
                    style={{ ...tacticalInput, width: i === 0 ? '70px' : '62px', textAlign: 'center' }}
                    placeholder={cfg.placeholder}
                  />
                  {i < 2 && <span style={{ color: '#7D9CB8', fontWeight: 700 }}>:</span>}
                </React.Fragment>
              ))}
              <span style={{ fontSize: '0.75rem', color: 'rgba(125,156,184,0.6)' }}>H : MM : SS</span>
            </div>
          </div>

          {/* Elevation */}
          <div>
            <label style={tacticalLabel}>Elevation Gain (feet)</label>
            <input
              type="number"
              min="0"
              value={form.elevation_gain_feet}
              onChange={e => set('elevation_gain_feet', e.target.value)}
              style={{ ...tacticalInput, width: '160px' }}
              placeholder="18,000"
            />
          </div>

          {/* Notes */}
          <div>
            <label style={tacticalLabel}>Notes <span style={{ color: 'rgba(125,156,184,0.5)', fontWeight: 400, textTransform: 'none', letterSpacing: 0 }}>— optional</span></label>
            <textarea
              value={form.notes}
              onChange={e => set('notes', e.target.value)}
              style={{ ...tacticalInput, minHeight: '70px', resize: 'vertical', fontFamily: 'inherit' }}
              placeholder="Course notes, crew access, key checkpoints..."
            />
          </div>

          {/* Actions */}
          <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
            <button
              onClick={onClose}
              disabled={isSaving}
              style={{
                padding: '8px 20px',
                backgroundColor: 'rgba(230,240,255,0.07)',
                color: '#E6F0FF',
                border: '1px solid rgba(125,156,184,0.4)',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '0.8rem',
                fontWeight: 600,
              }}
            >
              Cancel
            </button>
            <button
              onClick={handleSubmit}
              disabled={isSaving}
              style={{
                padding: '8px 28px',
                backgroundColor: '#FF5722',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: isSaving ? 'not-allowed' : 'pointer',
                fontSize: '0.8rem',
                fontWeight: 700,
                letterSpacing: '0.06em',
                opacity: isSaving ? 0.6 : 1,
              }}
            >
              {isSaving ? 'Saving...' : mode === 'add' ? 'Set Target' : 'Commit Changes'}
            </button>
          </div>
        </div>
      </div>
    </div>
  </>
  );
};

// ============================================================================
// PREF MODAL
// ============================================================================

// ============================================================================
// ATHLETE PROFILE MODAL
// ============================================================================

interface AthleteProfileModalProps {
  primarySport: string;
  secondarySport: string;
  experienceLevel: string;
  onSave: (primarySport: string, secondarySport: string, experienceLevel: string) => void;
  onClose: () => void;
}

const AthleteProfileModal: React.FC<AthleteProfileModalProps> = ({
  primarySport, secondarySport, experienceLevel, onSave, onClose,
}) => {
  const [ps, setPs] = useState(primarySport);
  const [ss, setSs] = useState(secondarySport);
  const [el, setEl] = useState(experienceLevel);

  return (
    <div
      style={{
        position: 'fixed', inset: 0, zIndex: 1000,
        backgroundColor: 'rgba(0,0,0,0.65)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        padding: '20px',
        animation: 'backdropFadeIn 0.2s ease-out',
      }}
      onClick={e => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div style={{
        ...CARBON,
        border: '1px solid rgba(255,87,34,0.7)',
        borderRadius: '8px',
        overflow: 'hidden',
        width: '100%',
        maxWidth: '480px',
        animation: 'panelExpand 0.25s cubic-bezier(0.34, 1.56, 0.64, 1)',
        transformOrigin: 'right top',
      }}>
        <div style={{
          background: 'linear-gradient(90deg, #E6F0FF 0%, #7D9CB8 50%, #1B2E4B 100%)',
          padding: '12px 24px',
        }}>
          <span style={{ fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.12em', color: '#1B2E4B', textTransform: 'uppercase' }}>
            Athlete Profile
          </span>
        </div>

        <div style={{ padding: '20px 24px 24px' }}>
          <div style={{ marginBottom: '16px' }}>
            <label style={tacticalLabel}>Primary Sport</label>
            <select value={ps} onChange={e => setPs(e.target.value)} style={tacticalInput}>
              <option value="trail_running">Trail Running</option>
              <option value="running">Running (Road/Flat)</option>
              <option value="cycling">Cycling</option>
              <option value="swimming">Swimming</option>
              <option value="strength">Strength Training</option>
              <option value="other">Other</option>
            </select>
          </div>

          <div style={{ marginBottom: '16px' }}>
            <label style={tacticalLabel}>Secondary Sport (Cross-Training)</label>
            <select value={ss} onChange={e => setSs(e.target.value)} style={tacticalInput}>
              <option value="">None</option>
              <option value="running">Running</option>
              <option value="cycling">Cycling</option>
              <option value="swimming">Swimming</option>
              <option value="rowing">Rowing</option>
              <option value="backcountry_skiing">Backcountry Skiing</option>
              <option value="strength">Strength Training</option>
              <option value="other">Other</option>
            </select>
          </div>

          <div style={{ marginBottom: '8px' }}>
            <label style={tacticalLabel}>Year Began Trail Running</label>
            <select value={el} onChange={e => setEl(e.target.value)} style={tacticalInput}>
              {(() => {
                const currentYear = new Date().getFullYear();
                const options = [];
                for (let y = currentYear; y >= currentYear - 10; y--) {
                  options.push(<option key={y} value={String(y)}>{y}</option>);
                }
                return options;
              })()}
            </select>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '24px' }}>
            <button
              onClick={() => onSave(ps, ss, el)}
              style={{
                padding: '8px 24px',
                backgroundColor: '#FF5722',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '0.8rem',
                fontWeight: 700,
                letterSpacing: '0.06em',
              }}
            >
              Apply
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

interface PrefModalProps {
  pref: 'communication' | 'risk';
  coachingSpectrum: number;
  riskTolerance: string;
  onSpectrumChange: (v: number) => void;
  onRiskChange: (v: string) => void;
  onClose: () => void;
}

const PrefModal: React.FC<PrefModalProps> = ({
  pref, coachingSpectrum, riskTolerance, onSpectrumChange, onRiskChange, onClose,
}) => {
  const title = pref === 'communication' ? 'Communication Style' : 'Risk Tolerance';
  const description = pref === 'communication'
    ? 'How the AI communicates training advice and feedback'
    : 'How the AI balances risk vs. performance in recommendations';

  return (
    <div
      style={{
        position: 'fixed', inset: 0, zIndex: 1000,
        backgroundColor: 'rgba(0,0,0,0.65)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        padding: '20px',
        animation: 'backdropFadeIn 0.2s ease-out',
      }}
      onClick={e => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div style={{
        ...CARBON,
        border: '1px solid rgba(255,87,34,0.7)',
        borderRadius: '8px',
        overflow: 'hidden',
        width: '100%',
        maxWidth: '560px',
        maxHeight: '90vh',
        overflowY: 'auto',
        animation: 'panelExpand 0.25s cubic-bezier(0.34, 1.56, 0.64, 1)',
        transformOrigin: 'right top',
      }}>
        {/* Header */}
        <div style={{
          background: 'linear-gradient(90deg, #E6F0FF 0%, #7D9CB8 50%, #1B2E4B 100%)',
          padding: '12px 24px',
        }}>
          <span style={{ fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.12em', color: '#1B2E4B', textTransform: 'uppercase' }}>
            {title}
          </span>
        </div>

        <div style={{ padding: '20px 24px 24px' }}>
          <p style={{ margin: '0 0 20px', fontSize: '0.78rem', color: 'rgba(125,156,184,0.75)', lineHeight: '1.5' }}>
            {description}
          </p>

          {pref === 'communication' ? (
            <CoachingStyleSpectrum initialValue={coachingSpectrum} onChange={onSpectrumChange} />
          ) : (
            <RiskToleranceSelector value={riskTolerance} onChange={onRiskChange} />
          )}

          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '24px' }}>
            <button
              onClick={onClose}
              style={{
                padding: '8px 24px',
                backgroundColor: '#FF5722',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '0.8rem',
                fontWeight: 700,
                letterSpacing: '0.06em',
              }}
            >
              Apply
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// ============================================================================
// AEROBIC ASSESSMENT PANEL
// ============================================================================

const driftColor = (pct: number) =>
  pct < 1.5 ? '#3b82f6' : pct <= 5.0 ? '#16a34a' : pct <= 10.0 ? '#d97706' : '#dc2626';

const driftLabel = (pct: number) =>
  pct < 1.5 ? 'Too Low' : pct <= 5.0 ? 'Valid' : pct <= 10.0 ? 'Above AeT' : 'High';

interface AerobicAssessmentPanelProps {
  method: AeTMethod;
  onMethodChange: (m: AeTMethod) => void;
  assessments: AerobicAssessment[];
  effectiveAet: EffectiveAetDaily[];
  hrActivities: HRActivity[];
  selectedActivityId: number | null;
  onActivitySelect: (id: number | null) => void;
  warmupMinutes: number;
  setWarmupMinutes: (v: number) => void;
  cooldownMinutes: number;
  setCooldownMinutes: (v: number) => void;
  antBpm: string;
  setAntBpm: (v: string) => void;
  assessmentNotes: string;
  setAssessmentNotes: (v: string) => void;
  driftPreview: DriftPreview | null;
  isAnalyzing: boolean;
  isSavingAssessment: boolean;
  assessmentError: string | null;
  hrStream: HRStreamPoint[];
  streamTotalMinutes: number;
  isLoadingStream: boolean;
  onAnalyze: () => void;
  onSave: () => void;
  onDelete: (id: number) => void;
  onBackfill: () => Promise<void>;
  isBackfilling: boolean;
}

const AerobicAssessmentPanel: React.FC<AerobicAssessmentPanelProps> = ({
  method, onMethodChange,
  assessments, hrActivities, selectedActivityId, onActivitySelect,
  warmupMinutes, setWarmupMinutes, cooldownMinutes, setCooldownMinutes,
  antBpm, setAntBpm, assessmentNotes, setAssessmentNotes, driftPreview,
  isAnalyzing, isSavingAssessment, assessmentError,
  hrStream, streamTotalMinutes, isLoadingStream,
  onAnalyze, onSave, onDelete, onBackfill, isBackfilling,
}) => {
  const cardStyle: React.CSSProperties = {
    backgroundColor: 'white',
    borderRadius: '8px',
    border: '1px solid #d1dce8',
    boxShadow: '0 2px 6px rgba(0,0,0,0.07)',
    overflow: 'hidden',
  };
  const headerStyle: React.CSSProperties = {
    background: 'linear-gradient(90deg, #E6F0FF 0%, #7D9CB8 50%, #1B2E4B 100%)',
    padding: '10px 16px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
  };
  const labelStyle: React.CSSProperties = {
    fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.12em',
    color: '#1B2E4B', textTransform: 'uppercase',
  };
  const inputStyle: React.CSSProperties = {
    width: '100%', padding: '7px 10px', borderRadius: '5px',
    border: '1px solid rgba(125,156,184,0.35)', backgroundColor: '#1B2E4B',
    color: '#E6F0FF', fontSize: '0.82rem', boxSizing: 'border-box',
  };
  const fieldLabelStyle: React.CSSProperties = {
    display: 'block', fontSize: '0.68rem', fontWeight: 600,
    letterSpacing: '0.08em', color: 'rgba(230,240,255,0.6)',
    textTransform: 'uppercase', marginBottom: '4px',
  };

  // Chart data — oldest first
  const chartData = [...assessments]
    .sort((a, b) => a.test_date.localeCompare(b.test_date))
    .map(a => ({
      date: formatDate(a.test_date),
      aet: a.aet_bpm,
      ant: a.ant_bpm ?? undefined,
      drift: a.drift_pct,
    }));

  const hasAnt = assessments.some(a => a.ant_bpm !== null);

  return (
    <div style={cardStyle}>
      {/* Header */}
      <div style={headerStyle}>
        <span style={labelStyle}>Aerobic Assessment</span>
        <MethodToggle method={method} onChange={onMethodChange} />
      </div>

      <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '16px' }}>

        <ProtocolInstructions method='hr_drift' />

        {/* ── INPUT SECTION ── */}
        <div style={{ ...CARBON, borderRadius: '7px', padding: '14px', display: 'flex', flexDirection: 'column', gap: '12px' }}>

          {/* Activity selector */}
          <div>
            <label style={fieldLabelStyle}>Select Activity</label>
            <select
              value={selectedActivityId ?? ''}
              onChange={e => onActivitySelect(e.target.value ? Number(e.target.value) : null)}
              style={{ ...inputStyle, cursor: 'pointer' }}
            >
              <option value=''>— choose a run with HR data —</option>
              {hrActivities.map(a => (
                <option key={a.activity_id} value={a.activity_id}>
                  {formatDate(a.date)} · {a.name}{a.distance_miles ? ` (${a.distance_miles.toFixed(1)} mi)` : ''}{a.already_assessed ? ' ✓' : ''}
                </option>
              ))}
            </select>
            {hrActivities.length === 0 && (
              <div style={{ marginTop: '8px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '0.7rem', color: 'rgba(230,240,255,0.5)' }}>No HR streams stored yet.</span>
                <button
                  onClick={onBackfill}
                  disabled={isBackfilling}
                  style={{
                    padding: '4px 10px', fontSize: '0.7rem', fontWeight: 700,
                    borderRadius: '4px', border: 'none', cursor: isBackfilling ? 'not-allowed' : 'pointer',
                    backgroundColor: isBackfilling ? 'rgba(107,143,127,0.4)' : '#6B8F7F',
                    color: '#fff', letterSpacing: '0.05em',
                  }}
                >
                  {isBackfilling ? 'Fetching...' : 'Fetch last 7 days'}
                </button>
              </div>
            )}
          </div>

          {/* HR chart + trim sliders — shown once a stream is loaded */}
          {isLoadingStream && (
            <div style={{ textAlign: 'center', fontSize: '0.72rem', color: 'rgba(230,240,255,0.5)', padding: '12px 0' }}>
              Loading HR stream…
            </div>
          )}

          {hrStream.length > 0 && !isLoadingStream && (() => {
            const maxT = streamTotalMinutes;
            const cooldownStart = maxT - cooldownMinutes;
            return (
              <div>
                {/* Chart */}
                <div style={{ marginBottom: '10px' }}>
                  <ResponsiveContainer width='100%' height={140}>
                    <LineChart data={hrStream} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
                      <CartesianGrid strokeDasharray='2 4' stroke='rgba(230,240,255,0.07)' />
                      <XAxis
                        dataKey='t'
                        type='number'
                        domain={[0, maxT]}
                        tickFormatter={v => `${Math.round(v)}m`}
                        tick={{ fontSize: 9, fill: 'rgba(230,240,255,0.4)' }}
                        tickCount={7}
                      />
                      <YAxis
                        domain={['auto', 'auto']}
                        tick={{ fontSize: 9, fill: 'rgba(230,240,255,0.4)' }}
                        width={34}
                      />
                      <Tooltip
                        contentStyle={{ backgroundColor: '#0d1b2e', border: '1px solid rgba(230,240,255,0.15)', borderRadius: '4px', fontSize: '0.72rem' }}
                        labelFormatter={v => `${Number(v).toFixed(1)} min`}
                        formatter={(v: any) => [`${v} bpm`, 'HR']}
                      />
                      {/* Shade excluded warmup region */}
                      {warmupMinutes > 0 && (
                        <ReferenceArea x1={0} x2={warmupMinutes} fill='rgba(255,87,34,0.18)' />
                      )}
                      {/* Shade excluded cooldown region */}
                      {cooldownMinutes > 0 && (
                        <ReferenceArea x1={cooldownStart} x2={maxT} fill='rgba(255,87,34,0.18)' />
                      )}
                      {/* Boundary lines */}
                      {warmupMinutes > 0 && (
                        <ReferenceLine x={warmupMinutes} stroke='#FF5722' strokeDasharray='3 2' strokeWidth={1.5} />
                      )}
                      {cooldownMinutes > 0 && (
                        <ReferenceLine x={cooldownStart} stroke='#FF5722' strokeDasharray='3 2' strokeWidth={1.5} />
                      )}
                      <Line type='monotone' dataKey='hr' stroke='#6B8F7F' strokeWidth={1.5} dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>

                {/* Trim sliders */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                  <div>
                    <label style={fieldLabelStyle}>
                      Trim start: <span style={{ color: '#FF5722', fontWeight: 700 }}>{warmupMinutes} min</span>
                    </label>
                    <input
                      type='range' min={0} max={Math.min(60, Math.floor(maxT * 0.8))} step={1}
                      value={warmupMinutes}
                      onChange={e => setWarmupMinutes(Number(e.target.value))}
                      style={{ width: '100%', accentColor: '#FF5722' }}
                    />
                  </div>
                  <div>
                    <label style={fieldLabelStyle}>
                      Trim end: <span style={{ color: '#FF5722', fontWeight: 700 }}>{cooldownMinutes} min</span>
                    </label>
                    <input
                      type='range' min={0} max={Math.floor(maxT * 0.4)} step={1}
                      value={Math.floor(maxT * 0.4) - cooldownMinutes}
                      onChange={e => setCooldownMinutes(Math.floor(maxT * 0.4) - Number(e.target.value))}
                      style={{ width: '100%', accentColor: '#FF5722' }}
                    />
                  </div>
                </div>
                <div style={{ fontSize: '0.65rem', color: 'rgba(230,240,255,0.35)', marginTop: '4px' }}>
                  Analysis window: {warmupMinutes} – {maxT - cooldownMinutes} min
                  ({Math.round(maxT - warmupMinutes - cooldownMinutes)} min)
                </div>
              </div>
            );
          })()}

          {/* AnT bpm (optional) */}
          <div>
            <label style={fieldLabelStyle}>AnT bpm (optional — from hill TT)</label>
            <input
              type='number' placeholder='e.g. 168'
              value={antBpm}
              onChange={e => setAntBpm(e.target.value)}
              style={inputStyle}
              min={100} max={220}
            />
          </div>

          {/* Analyze button */}
          <button
            onClick={onAnalyze}
            disabled={!selectedActivityId || isAnalyzing}
            style={{
              padding: '8px 20px', borderRadius: '5px', border: 'none',
              backgroundColor: selectedActivityId ? '#FF5722' : 'rgba(125,156,184,0.25)',
              color: selectedActivityId ? 'white' : 'rgba(230,240,255,0.4)',
              fontSize: '0.78rem', fontWeight: 700, letterSpacing: '0.06em',
              cursor: selectedActivityId ? 'pointer' : 'not-allowed',
              alignSelf: 'flex-start',
            }}
          >
            {isAnalyzing ? 'Analyzing...' : 'Analyze'}
          </button>
        </div>

        {/* ── ERROR ── */}
        {assessmentError && (
          <div style={{ padding: '10px 14px', backgroundColor: '#fff0f0', border: '1px solid #fca5a5', borderRadius: '6px', fontSize: '0.8rem', color: '#dc2626' }}>
            {assessmentError}
          </div>
        )}

        {/* ── PREVIEW RESULT ── */}
        {driftPreview && (
          <div style={{ ...CARBON, borderRadius: '7px', padding: '14px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span style={{ fontSize: '0.68rem', fontWeight: 700, letterSpacing: '0.1em', color: 'rgba(230,240,255,0.5)', textTransform: 'uppercase' }}>Result Preview</span>
              <span style={{
                padding: '2px 10px', borderRadius: '10px', fontSize: '0.72rem', fontWeight: 700,
                backgroundColor: driftColor(driftPreview.drift_pct),
                color: 'white',
              }}>
                {driftLabel(driftPreview.drift_pct)}
              </span>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '8px' }}>
              {[
                { label: 'First Half', value: `${driftPreview.first_half_avg_hr.toFixed(0)} bpm` },
                { label: 'Second Half', value: `${driftPreview.second_half_avg_hr.toFixed(0)} bpm` },
                { label: 'Drift', value: `${driftPreview.drift_pct.toFixed(1)}%`, color: driftColor(driftPreview.drift_pct) },
              ].map(({ label, value, color }) => (
                <div key={label} style={{ textAlign: 'center', padding: '8px', backgroundColor: 'rgba(255,255,255,0.05)', borderRadius: '5px' }}>
                  <div style={{ fontSize: '0.65rem', color: 'rgba(230,240,255,0.5)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>{label}</div>
                  <div style={{ fontSize: '1.1rem', fontWeight: 700, color: color ?? '#E6F0FF', marginTop: '2px' }}>{value}</div>
                </div>
              ))}
            </div>

            <div style={{ padding: '8px 10px', backgroundColor: 'rgba(255,255,255,0.05)', borderRadius: '5px', borderLeft: `3px solid ${driftColor(driftPreview.drift_pct)}` }}>
              <div style={{ fontSize: '0.72rem', fontWeight: 700, color: '#E6F0FF' }}>
                AeT: {driftPreview.aet_bpm.toFixed(0)} bpm
              </div>
              <div style={{ fontSize: '0.75rem', color: 'rgba(230,240,255,0.7)', marginTop: '3px', lineHeight: 1.4 }}>
                {driftPreview.interpretation}
              </div>
            </div>

            {driftPreview.gap_pct !== null && (
              <div style={{ fontSize: '0.75rem', color: 'rgba(230,240,255,0.7)', padding: '6px 10px', backgroundColor: 'rgba(255,255,255,0.04)', borderRadius: '5px' }}>
                AeT/AnT gap: <strong style={{ color: '#E6F0FF' }}>{driftPreview.gap_pct.toFixed(1)}%</strong> — {driftPreview.gap_status}
              </div>
            )}

            <div style={{ fontSize: '0.67rem', color: 'rgba(230,240,255,0.4)' }}>
              Steady-state window: {driftPreview.steady_state_minutes.toFixed(0)} min
            </div>

            {/* Notes field */}
            <div>
              <label style={{ ...fieldLabelStyle, color: 'rgba(230,240,255,0.5)' }}>Notes (optional)</label>
              <textarea
                value={assessmentNotes}
                onChange={e => setAssessmentNotes(e.target.value)}
                placeholder='Conditions, terrain, how you felt...'
                rows={2}
                style={{ ...inputStyle, resize: 'vertical', fontFamily: 'inherit' }}
              />
            </div>

            <button
              onClick={onSave}
              disabled={isSavingAssessment}
              style={{
                padding: '8px 20px', borderRadius: '5px', border: 'none',
                backgroundColor: '#16a34a', color: 'white',
                fontSize: '0.78rem', fontWeight: 700, letterSpacing: '0.06em',
                cursor: 'pointer', alignSelf: 'flex-start',
              }}
            >
              {isSavingAssessment ? 'Saving...' : 'Save Assessment'}
            </button>
          </div>
        )}

        {/* ── HISTORY CHART ── */}
        {chartData.length >= 2 && (
          <div>
            <div style={{ fontSize: '0.68rem', fontWeight: 700, letterSpacing: '0.1em', color: '#4a6285', textTransform: 'uppercase', marginBottom: '8px' }}>
              AeT Progression
            </div>
            <ResponsiveContainer width='100%' height={200}>
              <LineChart data={chartData} margin={{ top: 4, right: 30, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray='3 3' stroke='rgba(0,0,0,0.08)' />
                <XAxis dataKey='date' tick={{ fontSize: 11, fill: '#7D9CB8' }} />
                <YAxis yAxisId='hr' domain={['auto', 'auto']} tick={{ fontSize: 11, fill: '#7D9CB8' }} label={{ value: 'bpm', angle: -90, position: 'insideLeft', fontSize: 10, fill: '#7D9CB8' }} />
                <YAxis yAxisId='drift' orientation='right' domain={[0, 'auto']} tick={{ fontSize: 11, fill: '#7D9CB8' }} label={{ value: 'drift %', angle: 90, position: 'insideRight', fontSize: 10, fill: '#7D9CB8' }} />
                <Tooltip
                  contentStyle={{ fontSize: '0.78rem', border: '1px solid #d1dce8' }}
                  formatter={(value: number, name: string) => {
                    if (name === 'AeT bpm' || name === 'AnT bpm') return [`${Number(value).toFixed(0)} bpm`, name];
                    if (name === 'Drift %') return [`${Number(value).toFixed(1)}%`, name];
                    return [value, name];
                  }}
                />
                <Legend iconSize={10} wrapperStyle={{ fontSize: '0.72rem' }} />
                <ReferenceLine yAxisId='drift' y={5} stroke='#d97706' strokeDasharray='4 2' label={{ value: '5% AeT', fontSize: 10, fill: '#d97706' }} />
                <Line yAxisId='hr' type='monotone' dataKey='aet' name='AeT bpm' stroke='#FF5722' strokeWidth={2} dot={{ r: 4, fill: '#FF5722' }} activeDot={{ r: 5 }} />
                {hasAnt && <Line yAxisId='hr' type='monotone' dataKey='ant' name='AnT bpm' stroke='#7D9CB8' strokeWidth={2} strokeDasharray='5 3' dot={{ r: 3 }} />}
                <Line yAxisId='drift' type='monotone' dataKey='drift' name='Drift %' stroke='rgba(125,156,184,0.6)' strokeWidth={1.5} strokeDasharray='3 2' dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* ── HISTORY TABLE ── */}
        {assessments.length > 0 ? (
          <div>
            <div style={{ fontSize: '0.68rem', fontWeight: 700, letterSpacing: '0.1em', color: '#4a6285', textTransform: 'uppercase', marginBottom: '8px' }}>
              Test History
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              {assessments.map(a => (
                <div key={a.id} style={{
                  display: 'flex', alignItems: 'flex-start', gap: '10px',
                  padding: '10px 12px', backgroundColor: '#f8fafc',
                  borderRadius: '6px', border: '1px solid #e2e8f0',
                }}>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                      <span style={{ fontSize: '0.78rem', fontWeight: 700, color: '#1B2E4B' }}>
                        {formatDate(a.test_date)}
                      </span>
                      <span style={{
                        padding: '1px 8px', borderRadius: '8px', fontSize: '0.68rem', fontWeight: 700,
                        backgroundColor: driftColor(a.drift_pct), color: 'white',
                      }}>
                        {driftLabel(a.drift_pct)} · {a.drift_pct.toFixed(1)}%
                      </span>
                      <span style={{ fontSize: '0.72rem', color: '#4a6285', fontWeight: 600 }}>
                        AeT {a.aet_bpm.toFixed(0)} bpm
                      </span>
                      {a.gap_pct !== null && (
                        <span style={{ fontSize: '0.7rem', color: '#7D9CB8' }}>
                          gap {a.gap_pct.toFixed(1)}%
                        </span>
                      )}
                    </div>
                    <div style={{ fontSize: '0.72rem', color: '#64748b', marginTop: '3px', lineHeight: 1.4 }}>
                      {a.activity_name}{a.distance_miles ? ` · ${a.distance_miles.toFixed(1)} mi` : ''} · {a.steady_state_minutes.toFixed(0)} min steady-state
                    </div>
                    {a.notes && (
                      <div style={{ fontSize: '0.7rem', color: '#94a3b8', marginTop: '2px', fontStyle: 'italic' }}>{a.notes}</div>
                    )}
                  </div>
                  <button
                    onClick={() => onDelete(a.id)}
                    title='Delete'
                    style={{
                      flexShrink: 0, padding: '3px 8px', fontSize: '0.68rem',
                      border: '1px solid #e2e8f0', borderRadius: '4px',
                      backgroundColor: 'transparent', color: '#94a3b8',
                      cursor: 'pointer',
                    }}
                  >
                    Remove
                  </button>
                </div>
              ))}
            </div>
          </div>
        ) : !driftPreview && (
          <div style={{ textAlign: 'center', padding: '20px', color: '#94a3b8', fontSize: '0.8rem' }}>
            No drift tests recorded. Select a steady-state run to analyze.
          </div>
        )}

      </div>
    </div>
  );
};

// ============================================================================
// AeT METHOD TOGGLE  (segmented control — lives in each panel header)
// ============================================================================

const MethodToggle: React.FC<{ method: AeTMethod; onChange: (m: AeTMethod) => void }> = ({ method, onChange }) => {
  const opt = (m: AeTMethod, label: string) => {
    const active = method === m;
    return (
      <button
        key={m}
        onClick={() => !active && onChange(m)}
        style={{
          padding: '3px 10px',
          fontSize: '0.62rem',
          fontWeight: 700,
          letterSpacing: '0.06em',
          textTransform: 'uppercase',
          border: 'none',
          borderRadius: '4px',
          cursor: active ? 'default' : 'pointer',
          backgroundColor: active ? '#1B2E4B' : 'transparent',
          color: active ? '#E6F0FF' : 'rgba(27,46,75,0.65)',
        }}
        aria-pressed={active}
      >
        {label}
      </button>
    );
  };
  return (
    <div style={{
      display: 'flex', gap: '2px', padding: '2px',
      borderRadius: '6px', backgroundColor: 'rgba(27,46,75,0.12)',
    }}>
      {opt('hr_drift', 'HR Drift')}
      {opt('lactate_step', 'Lactate Step')}
    </div>
  );
};

// ============================================================================
// PROTOCOL INSTRUCTIONS  (in-app step-by-step for the selected method)
// ============================================================================

const ProtocolInstructions: React.FC<{ method: AeTMethod }> = ({ method }) => {
  const headingStyle: React.CSSProperties = {
    fontSize: '0.68rem', fontWeight: 700, letterSpacing: '0.1em',
    color: '#4a6285', textTransform: 'uppercase', marginBottom: '8px',
  };
  const steps: { label: string; text: string }[] = method === 'lactate_step'
    ? [
        { label: 'Warm-up', text: '10–15 min very easy, then take a clean baseline fingertip lactate sample. This low reading anchors the rise.' },
        { label: 'Start', text: 'Hold a fixed, comfortable speed at 0–1% grade — effort clearly below AeT (HR ~20–25 bpm under your estimated AeT).' },
        { label: 'Each stage', text: '3–4 min. Keep speed fixed; raise the grade +1.5%. At the end of each stage record steady-state HR and draw a lactate sample.' },
        { label: 'Stop', text: 'Stop once two consecutive stages read ≥ baseline + 0.3 mmol and trending up. Keep peak ~2.5–3 mmol — this is a light test, do not push to LT2.' },
        { label: 'Be consistent', text: 'Same warm-up, stage length, speed, and increment every time. Control heat, hydration, caffeine, glycogen, and time of day.' },
      ]
    : [
        { label: 'Warm-up', text: '10 min easy, conversational, nose-breathing. Do not skip.' },
        { label: 'Steady state', text: '60 min at one constant effort. Lock in a starting HR ~10 bpm below estimated AeT and hold it — drift is the signal, do not adjust.' },
        { label: 'Terrain', text: 'Treadmill (fixed speed + grade) or a flat loop (<70 ft gain/hour). Out-and-back routes are invalid.' },
        { label: 'After the run', text: 'Submit the activity below — the system computes drift %, AeT bpm, and gap status from the HR stream.' },
      ];
  return (
    <div style={{
      backgroundColor: '#f8fafc', border: '1px solid #e2e8f0',
      borderRadius: '7px', padding: '14px',
    }}>
      <div style={headingStyle}>
        {method === 'lactate_step' ? 'LT1 Lactate Step Test — Protocol' : 'HR Drift Test — Protocol'}
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {steps.map(s => (
          <div key={s.label} style={{ display: 'flex', gap: '10px', alignItems: 'baseline' }}>
            <span style={{
              flexShrink: 0, minWidth: '78px', fontSize: '0.68rem', fontWeight: 700,
              color: '#1B2E4B', letterSpacing: '0.03em',
            }}>{s.label}</span>
            <span style={{ fontSize: '0.74rem', color: '#475569', lineHeight: 1.45 }}>{s.text}</span>
          </div>
        ))}
      </div>
      <div style={{ fontSize: '0.65rem', color: '#94a3b8', marginTop: '10px', lineHeight: 1.4 }}>
        Both methods measure the same boundary (AeT = your Zone 2 ceiling). The step test reads it
        directly from lactate; the drift test estimates it from HR. Pick whichever you can run consistently.
      </div>
    </div>
  );
};

// ============================================================================
// LACTATE STEP TEST PANEL
// ============================================================================

interface LactateStepTestPanelProps {
  method: AeTMethod;
  onMethodChange: (m: AeTMethod) => void;
  tests: LactateStepTest[];
  speed: string;
  setSpeed: (v: string) => void;
  speedUnit: string;
  setSpeedUnit: (v: string) => void;
  baseline: string;
  setBaseline: (v: string) => void;
  stages: LactateStageInput[];
  setStages: (s: LactateStageInput[]) => void;
  notes: string;
  setNotes: (v: string) => void;
  preview: LactatePreview | null;
  isAnalyzing: boolean;
  isSaving: boolean;
  error: string | null;
  onAnalyze: () => void;
  onSave: () => void;
  onDelete: (id: number) => void;
}

const GRADE_STEP = 1.5;

const LactateStepTestPanel: React.FC<LactateStepTestPanelProps> = ({
  method, onMethodChange, tests, speed, setSpeed, speedUnit, setSpeedUnit,
  baseline, setBaseline, stages, setStages, notes, setNotes,
  preview, isAnalyzing, isSaving, error, onAnalyze, onSave, onDelete,
}) => {
  const cardStyle: React.CSSProperties = {
    backgroundColor: 'white', borderRadius: '8px', border: '1px solid #d1dce8',
    boxShadow: '0 2px 6px rgba(0,0,0,0.07)', overflow: 'hidden',
  };
  const headerStyle: React.CSSProperties = {
    background: 'linear-gradient(90deg, #E6F0FF 0%, #7D9CB8 50%, #1B2E4B 100%)',
    padding: '10px 16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between',
  };
  const labelStyle: React.CSSProperties = {
    fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.12em',
    color: '#1B2E4B', textTransform: 'uppercase',
  };
  const inputStyle: React.CSSProperties = {
    width: '100%', padding: '7px 10px', borderRadius: '5px',
    border: '1px solid rgba(125,156,184,0.35)', backgroundColor: '#1B2E4B',
    color: '#E6F0FF', fontSize: '0.82rem', boxSizing: 'border-box',
  };
  const fieldLabelStyle: React.CSSProperties = {
    display: 'block', fontSize: '0.68rem', fontWeight: 600,
    letterSpacing: '0.08em', color: 'rgba(230,240,255,0.6)',
    textTransform: 'uppercase', marginBottom: '4px',
  };
  const cellInput: React.CSSProperties = {
    ...inputStyle, padding: '5px 7px', fontSize: '0.78rem', textAlign: 'center',
  };

  const updateStage = (idx: number, field: keyof LactateStageInput, value: string) => {
    const next = stages.map((s, i) => (i === idx ? { ...s, [field]: value } : s));
    setStages(next);
  };
  const addStage = () => {
    const last = stages[stages.length - 1];
    const nextGrade = last && last.grade !== '' && !isNaN(Number(last.grade))
      ? (Number(last.grade) + GRADE_STEP).toFixed(1)
      : (stages.length * GRADE_STEP).toFixed(1);
    setStages([...stages, { grade: nextGrade, hr: '', lactate: '' }]);
  };
  const removeStage = (idx: number) => {
    if (stages.length <= 2) return;
    setStages(stages.filter((_, i) => i !== idx));
  };

  // Curve data for preview + the entered table (oldest stage first)
  const curveData = stages
    .map((s, i) => ({
      stage: i + 1,
      grade: s.grade !== '' ? Number(s.grade) : null,
      lactate: s.lactate !== '' && !isNaN(Number(s.lactate)) ? Number(s.lactate) : null,
      hr: s.hr !== '' && !isNaN(Number(s.hr)) ? Number(s.hr) : null,
    }))
    .filter(d => d.lactate !== null);

  const baselineNum = baseline !== '' && !isNaN(Number(baseline)) ? Number(baseline) : null;
  const riseLine = preview?.baseline_lactate != null
    ? preview.baseline_lactate + (preview.rise_threshold_mmol ?? 0.3)
    : baselineNum != null ? baselineNum + 0.3 : null;

  // AeT progression across valid tests (oldest first)
  const progression = [...tests]
    .filter(t => t.valid && t.lt1_bpm != null)
    .sort((a, b) => a.test_date.localeCompare(b.test_date))
    .map(t => ({ date: formatDate(t.test_date), aet: t.lt1_bpm as number }));

  const canAnalyze = curveData.length >= 2 && !isAnalyzing;

  return (
    <div style={cardStyle}>
      {/* Header with method toggle */}
      <div style={headerStyle}>
        <span style={labelStyle}>Aerobic Assessment</span>
        <MethodToggle method={method} onChange={onMethodChange} />
      </div>

      <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '16px' }}>

        <ProtocolInstructions method='lactate_step' />

        {/* ── ENTRY SECTION ── */}
        <div style={{ ...CARBON, borderRadius: '7px', padding: '14px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div style={{ fontSize: '0.68rem', fontWeight: 700, letterSpacing: '0.1em', color: 'rgba(230,240,255,0.6)', textTransform: 'uppercase' }}>
            Enter step table
          </div>

          {/* Speed + baseline row */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '10px' }}>
            <div>
              <label style={fieldLabelStyle}>Test speed</label>
              <input type='number' inputMode='decimal' placeholder='e.g. 6.0'
                value={speed} onChange={e => setSpeed(e.target.value)} style={inputStyle} min={0} step={0.1} />
            </div>
            <div>
              <label style={fieldLabelStyle}>Unit</label>
              <select value={speedUnit} onChange={e => setSpeedUnit(e.target.value)} style={{ ...inputStyle, cursor: 'pointer' }}>
                <option value='mph'>mph</option>
                <option value='kph'>kph</option>
                <option value='min/mi'>min/mi</option>
                <option value='min/km'>min/km</option>
              </select>
            </div>
            <div>
              <label style={fieldLabelStyle}>Baseline mmol</label>
              <input type='number' inputMode='decimal' placeholder='warm-up'
                value={baseline} onChange={e => setBaseline(e.target.value)} style={inputStyle} min={0} step={0.1} />
            </div>
          </div>

          {/* Stage table */}
          <div>
            <div style={{ display: 'grid', gridTemplateColumns: '34px 1fr 1fr 1fr 28px', gap: '6px', marginBottom: '4px' }}>
              {['#', 'Grade %', 'HR bpm', 'Lactate', ''].map((h, i) => (
                <div key={i} style={{ fontSize: '0.62rem', fontWeight: 700, letterSpacing: '0.06em', color: 'rgba(230,240,255,0.45)', textTransform: 'uppercase', textAlign: i === 0 || i === 4 ? 'center' : 'left' }}>{h}</div>
              ))}
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
              {stages.map((s, idx) => (
                <div key={idx} style={{ display: 'grid', gridTemplateColumns: '34px 1fr 1fr 1fr 28px', gap: '6px', alignItems: 'center' }}>
                  <div style={{ textAlign: 'center', fontSize: '0.78rem', fontWeight: 700, color: 'rgba(230,240,255,0.5)' }}>{idx + 1}</div>
                  <input type='number' inputMode='decimal' value={s.grade} onChange={e => updateStage(idx, 'grade', e.target.value)} style={cellInput} step={0.1} />
                  <input type='number' inputMode='numeric' value={s.hr} onChange={e => updateStage(idx, 'hr', e.target.value)} style={cellInput} min={30} max={230} />
                  <input type='number' inputMode='decimal' value={s.lactate} onChange={e => updateStage(idx, 'lactate', e.target.value)} style={cellInput} min={0} step={0.1} />
                  <button onClick={() => removeStage(idx)} title='Remove stage'
                    disabled={stages.length <= 2}
                    style={{
                      border: 'none', background: 'transparent', cursor: stages.length <= 2 ? 'not-allowed' : 'pointer',
                      color: stages.length <= 2 ? 'rgba(230,240,255,0.2)' : 'rgba(230,240,255,0.55)', fontSize: '1rem', lineHeight: 1,
                    }}>×</button>
                </div>
              ))}
            </div>
            <button onClick={addStage}
              style={{
                marginTop: '8px', padding: '5px 12px', fontSize: '0.7rem', fontWeight: 700,
                borderRadius: '4px', border: '1px dashed rgba(230,240,255,0.3)', cursor: 'pointer',
                backgroundColor: 'transparent', color: 'rgba(230,240,255,0.7)', letterSpacing: '0.05em',
              }}>+ Add stage</button>
          </div>

          <button onClick={onAnalyze} disabled={!canAnalyze}
            style={{
              padding: '8px 20px', borderRadius: '5px', border: 'none',
              backgroundColor: canAnalyze ? '#FF5722' : 'rgba(125,156,184,0.25)',
              color: canAnalyze ? 'white' : 'rgba(230,240,255,0.4)',
              fontSize: '0.78rem', fontWeight: 700, letterSpacing: '0.06em',
              cursor: canAnalyze ? 'pointer' : 'not-allowed', alignSelf: 'flex-start',
            }}>
            {isAnalyzing ? 'Analyzing...' : 'Analyze'}
          </button>
        </div>

        {/* ── ERROR ── */}
        {error && (
          <div style={{ padding: '10px 14px', backgroundColor: '#fff0f0', border: '1px solid #fca5a5', borderRadius: '6px', fontSize: '0.8rem', color: '#dc2626' }}>
            {error}
          </div>
        )}

        {/* ── PREVIEW (lactate curve = signature) ── */}
        {preview && (
          <div style={{ ...CARBON, borderRadius: '7px', padding: '14px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span style={{ fontSize: '0.68rem', fontWeight: 700, letterSpacing: '0.1em', color: 'rgba(230,240,255,0.5)', textTransform: 'uppercase' }}>Result Preview</span>
              <span style={{
                padding: '2px 10px', borderRadius: '10px', fontSize: '0.72rem', fontWeight: 700,
                backgroundColor: preview.valid ? '#16a34a' : '#dc2626', color: 'white',
              }}>
                {preview.valid ? 'LT1 found' : 'No LT1'}
              </span>
            </div>

            {/* Lactate curve */}
            {curveData.length >= 2 && (
              <ResponsiveContainer width='100%' height={180}>
                <LineChart data={curveData} margin={{ top: 6, right: 10, left: -18, bottom: 2 }}>
                  <CartesianGrid strokeDasharray='2 4' stroke='rgba(230,240,255,0.07)' />
                  <XAxis dataKey='grade' type='number' domain={['auto', 'auto']}
                    tickFormatter={v => `${v}%`} tick={{ fontSize: 9, fill: 'rgba(230,240,255,0.45)' }} />
                  <YAxis domain={[0, 'auto']} tick={{ fontSize: 9, fill: 'rgba(230,240,255,0.45)' }} width={34} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0d1b2e', border: '1px solid rgba(230,240,255,0.15)', borderRadius: '4px', fontSize: '0.72rem' }}
                    labelFormatter={v => `${v}% grade`}
                    formatter={(val: any, _n: any, p: any) => [`${val} mmol${p?.payload?.hr ? ` · ${p.payload.hr} bpm` : ''}`, 'Lactate']}
                  />
                  {preview.baseline_lactate != null && (
                    <ReferenceLine y={preview.baseline_lactate} stroke='rgba(125,156,184,0.6)' strokeDasharray='4 2'
                      label={{ value: 'baseline', fontSize: 9, fill: '#7D9CB8', position: 'insideBottomLeft' }} />
                  )}
                  {riseLine != null && (
                    <ReferenceLine y={riseLine} stroke='#d97706' strokeDasharray='4 2'
                      label={{ value: '+0.3 LT1', fontSize: 9, fill: '#d97706', position: 'insideTopLeft' }} />
                  )}
                  {preview.valid && preview.lt1_grade != null && (
                    <ReferenceLine x={preview.lt1_grade} stroke='#FF5722' strokeWidth={1.5}
                      label={{ value: 'LT1', fontSize: 10, fill: '#FF5722', position: 'top' }} />
                  )}
                  <Line type='monotone' dataKey='lactate' stroke='#6B8F7F' strokeWidth={2} dot={{ r: 3, fill: '#6B8F7F' }} activeDot={{ r: 5 }} />
                </LineChart>
              </ResponsiveContainer>
            )}

            {preview.valid ? (
              <>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '8px' }}>
                  {[
                    { label: 'AeT (LT1)', value: `${preview.lt1_bpm?.toFixed(0)} bpm`, color: '#FF5722' },
                    { label: 'At grade', value: preview.lt1_grade != null ? `${preview.lt1_grade.toFixed(1)}%` : '—' },
                    { label: 'Baseline', value: `${preview.baseline_lactate?.toFixed(1)} mmol` },
                  ].map(({ label, value, color }) => (
                    <div key={label} style={{ textAlign: 'center', padding: '8px', backgroundColor: 'rgba(255,255,255,0.05)', borderRadius: '5px' }}>
                      <div style={{ fontSize: '0.65rem', color: 'rgba(230,240,255,0.5)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>{label}</div>
                      <div style={{ fontSize: '1.1rem', fontWeight: 700, color: color ?? '#E6F0FF', marginTop: '2px' }}>{value}</div>
                    </div>
                  ))}
                </div>
                <div style={{ padding: '8px 10px', backgroundColor: 'rgba(255,255,255,0.05)', borderRadius: '5px', borderLeft: '3px solid #FF5722', fontSize: '0.75rem', color: 'rgba(230,240,255,0.75)', lineHeight: 1.45 }}>
                  {preview.interpretation}
                </div>
              </>
            ) : (
              <div style={{ padding: '8px 10px', backgroundColor: 'rgba(220,38,38,0.12)', borderRadius: '5px', borderLeft: '3px solid #dc2626', fontSize: '0.75rem', color: 'rgba(230,240,255,0.8)', lineHeight: 1.45 }}>
                {preview.error}
              </div>
            )}

            {/* Notes + Save (only when a valid LT1 is found) */}
            {preview.valid && (
              <>
                <div>
                  <label style={{ ...fieldLabelStyle, color: 'rgba(230,240,255,0.5)' }}>Notes (optional)</label>
                  <textarea value={notes} onChange={e => setNotes(e.target.value)}
                    placeholder='Conditions, hydration, time of day...' rows={2}
                    style={{ ...inputStyle, resize: 'vertical', fontFamily: 'inherit' }} />
                </div>
                <button onClick={onSave} disabled={isSaving}
                  style={{
                    padding: '8px 20px', borderRadius: '5px', border: 'none',
                    backgroundColor: '#16a34a', color: 'white', fontSize: '0.78rem',
                    fontWeight: 700, letterSpacing: '0.06em', cursor: 'pointer', alignSelf: 'flex-start',
                  }}>
                  {isSaving ? 'Saving...' : 'Save Test'}
                </button>
              </>
            )}
          </div>
        )}

        {/* ── AeT PROGRESSION ── */}
        {progression.length >= 2 && (
          <div>
            <div style={{ fontSize: '0.68rem', fontWeight: 700, letterSpacing: '0.1em', color: '#4a6285', textTransform: 'uppercase', marginBottom: '8px' }}>
              AeT Progression (LT1)
            </div>
            <ResponsiveContainer width='100%' height={200}>
              <LineChart data={progression} margin={{ top: 4, right: 20, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray='3 3' stroke='rgba(0,0,0,0.08)' />
                <XAxis dataKey='date' tick={{ fontSize: 11, fill: '#7D9CB8' }} />
                <YAxis domain={['auto', 'auto']} tick={{ fontSize: 11, fill: '#7D9CB8' }} label={{ value: 'bpm', angle: -90, position: 'insideLeft', fontSize: 10, fill: '#7D9CB8' }} />
                <Tooltip contentStyle={{ fontSize: '0.78rem', border: '1px solid #d1dce8' }} formatter={(v: number) => [`${Number(v).toFixed(0)} bpm`, 'AeT (LT1)']} />
                <Line type='monotone' dataKey='aet' name='AeT (LT1)' stroke='#FF5722' strokeWidth={2} dot={{ r: 4, fill: '#FF5722' }} activeDot={{ r: 5 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* ── HISTORY ── */}
        {tests.length > 0 ? (
          <div>
            <div style={{ fontSize: '0.68rem', fontWeight: 700, letterSpacing: '0.1em', color: '#4a6285', textTransform: 'uppercase', marginBottom: '8px' }}>
              Test History
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              {tests.map(t => (
                <div key={t.id} style={{ display: 'flex', alignItems: 'flex-start', gap: '10px', padding: '10px 12px', backgroundColor: '#f8fafc', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                      <span style={{ fontSize: '0.78rem', fontWeight: 700, color: '#1B2E4B' }}>{formatDate(t.test_date)}</span>
                      {t.valid && t.lt1_bpm != null ? (
                        <span style={{ padding: '1px 8px', borderRadius: '8px', fontSize: '0.68rem', fontWeight: 700, backgroundColor: '#16a34a', color: 'white' }}>
                          AeT {t.lt1_bpm.toFixed(0)} bpm
                        </span>
                      ) : (
                        <span style={{ padding: '1px 8px', borderRadius: '8px', fontSize: '0.68rem', fontWeight: 700, backgroundColor: '#dc2626', color: 'white' }}>No LT1</span>
                      )}
                      {t.lt1_grade != null && <span style={{ fontSize: '0.72rem', color: '#4a6285', fontWeight: 600 }}>{t.lt1_grade.toFixed(1)}% grade</span>}
                    </div>
                    <div style={{ fontSize: '0.72rem', color: '#64748b', marginTop: '3px', lineHeight: 1.4 }}>
                      {t.stages?.length || 0} stages
                      {t.speed != null ? ` · ${t.speed} ${t.speed_unit}` : ''}
                      {t.baseline_lactate != null ? ` · baseline ${t.baseline_lactate.toFixed(1)} mmol` : ''}
                    </div>
                    {t.notes && <div style={{ fontSize: '0.7rem', color: '#94a3b8', marginTop: '2px', fontStyle: 'italic' }}>{t.notes}</div>}
                  </div>
                  <button onClick={() => onDelete(t.id)} title='Delete'
                    style={{ flexShrink: 0, padding: '3px 8px', fontSize: '0.68rem', border: '1px solid #e2e8f0', borderRadius: '4px', backgroundColor: 'transparent', color: '#94a3b8', cursor: 'pointer' }}>
                    Remove
                  </button>
                </div>
              ))}
            </div>
          </div>
        ) : !preview && (
          <div style={{ textAlign: 'center', padding: '20px', color: '#94a3b8', fontSize: '0.8rem' }}>
            No step tests recorded. Enter your step table above to find LT1.
          </div>
        )}

      </div>
    </div>
  );
};

// ============================================================================
// SEASON PAGE
// ============================================================================

const SeasonPage: React.FC = () => {
  const [goals, setGoals] = useState<RaceGoal[]>([]);
  const [checkedIds, setCheckedIds] = useState<Set<number>>(new Set());
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [modalMode, setModalMode] = useState<'add' | 'edit' | null>(null);
  const [editingGoal, setEditingGoal] = useState<RaceGoal | null>(null);

  const [raceReadiness, setRaceReadiness] = useState<RaceReadiness | null>(null);
  const [athleteModel, setAthleteModel] = useState<AthleteModel | null>(null);
  const [coachingSpectrum, setCoachingSpectrum] = useState<number>(50);
  const [riskTolerance, setRiskTolerance] = useState<string>('balanced');
  const [primarySport, setPrimarySport] = useState<string>('trail_running');
  const [secondarySport, setSecondarySport] = useState<string>('');
  const [experienceLevel, setExperienceLevel] = useState<string>(String(new Date().getFullYear()));

  const [isLoading, setIsLoading] = useState(true);
  const [isSavingStyle, setIsSavingStyle] = useState(false);
  const [editingPref, setEditingPref] = useState<'communication' | 'risk' | null>(null);
  const [editingProfile, setEditingProfile] = useState(false);

  // Aerobic Assessment
  const [assessments, setAssessments] = useState<AerobicAssessment[]>([]);
  const [effectiveAet, setEffectiveAet] = useState<EffectiveAetDaily[]>([]);
  const [hrActivities, setHrActivities] = useState<HRActivity[]>([]);
  const [selectedActivityId, setSelectedActivityId] = useState<number | null>(null);
  const [warmupMinutes, setWarmupMinutes] = useState<number>(10);
  const [antBpm, setAntBpm] = useState<string>('');
  const [assessmentNotes, setAssessmentNotes] = useState<string>('');
  const [driftPreview, setDriftPreview] = useState<DriftPreview | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isSavingAssessment, setIsSavingAssessment] = useState(false);
  const [assessmentError, setAssessmentError] = useState<string | null>(null);
  const [isBackfilling, setIsBackfilling] = useState(false);
  const [hrStream, setHrStream] = useState<HRStreamPoint[]>([]);
  const [streamTotalMinutes, setStreamTotalMinutes] = useState<number>(0);
  const [isLoadingStream, setIsLoadingStream] = useState(false);
  const [cooldownMinutes, setCooldownMinutes] = useState<number>(0);

  // AeT assessment method + LT1 Lactate Step Test
  const [aetMethod, setAetMethod] = useState<AeTMethod>('hr_drift');
  const [lactateTests, setLactateTests] = useState<LactateStepTest[]>([]);
  const [lactateSpeed, setLactateSpeed] = useState<string>('');
  const [lactateSpeedUnit, setLactateSpeedUnit] = useState<string>('mph');
  const [lactateBaseline, setLactateBaseline] = useState<string>('');
  const [lactateStages, setLactateStages] = useState<LactateStageInput[]>([
    { grade: '0', hr: '', lactate: '' },
    { grade: '1.5', hr: '', lactate: '' },
    { grade: '3.0', hr: '', lactate: '' },
    { grade: '4.5', hr: '', lactate: '' },
  ]);
  const [lactateNotes, setLactateNotes] = useState<string>('');
  const [lactatePreview, setLactatePreview] = useState<LactatePreview | null>(null);
  const [isAnalyzingLactate, setIsAnalyzingLactate] = useState(false);
  const [isSavingLactate, setIsSavingLactate] = useState(false);
  const [lactateError, setLactateError] = useState<string | null>(null);

  // ──────────────────────────────────────────
  // FETCH
  // ──────────────────────────────────────────

  const fetchAll = async () => {
    try {
      const [goalsRes, readinessRes, modelRes, settingsRes, assessmentsRes, hrActivitiesRes, lactateRes, effAetRes] = await Promise.all([
        fetch('/api/coach/race-goals'),
        fetch('/api/coach/race-readiness'),
        fetch('/api/athlete-model'),
        fetch('/api/user-settings'),
        fetch('/api/coach/aerobic-assessments'),
        fetch('/api/coach/activities-with-hr'),
        fetch('/api/coach/lactate-step-tests'),
        fetch('/api/coach/effective-aet-history'),
      ]);

      if (goalsRes.ok) {
        const d = await goalsRes.json();
        const list: RaceGoal[] = d.goals || [];
        setGoals(list);
        // Default selection: nearest A race
        if (selectedId === null) {
          const aRace = list.find(g => g.priority === 'A');
          if (aRace) setSelectedId(aRace.id);
        }
      }

      if (readinessRes.ok) {
        const d = await readinessRes.json();
        if (d.success && d.readiness) setRaceReadiness(d.readiness);
      }

      if (modelRes.ok) {
        const d = await modelRes.json();
        if (d.success) setAthleteModel(d.model);
      }

      if (settingsRes.ok) {
        const d = await settingsRes.json();
        setCoachingSpectrum(d.coaching_style_spectrum ?? 50);
        setRiskTolerance(d.recommendation_style ?? 'balanced');
        setPrimarySport(d.primary_sport ?? 'trail_running');
        setSecondarySport(d.secondary_sport ?? '');
        const rawExp = d.training_experience ?? '';
        // If stored value is a legacy enum, default to current year
        const legacyEnums = ['beginner', 'intermediate', 'advanced', 'elite'];
        setExperienceLevel(legacyEnums.includes(rawExp) || !rawExp
          ? String(new Date().getFullYear())
          : rawExp
        );
        setAetMethod(d.aet_assessment_method === 'lactate_step' ? 'lactate_step' : 'hr_drift');
      }
      if (assessmentsRes.ok) {
        const d = await assessmentsRes.json();
        if (d.success) setAssessments(d.assessments || []);
      }

      if (hrActivitiesRes.ok) {
        const d = await hrActivitiesRes.json();
        if (d.success) setHrActivities(d.activities || []);
      }

      if (lactateRes.ok) {
        const d = await lactateRes.json();
        if (d.success) setLactateTests(d.tests || []);
      }

      if (effAetRes.ok) {
        const d = await effAetRes.json();
        if (d.success) setEffectiveAet(d.history || []);
      }
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => { fetchAll(); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Scroll to anchor after data loads (supports links like /?tab=coach&subtab=season#athlete-model)
  useEffect(() => {
    if (isLoading) return;
    const hash = window.location.hash.slice(1);
    if (!hash) return;
    const el = document.getElementById(hash);
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }, [isLoading]);

  // ──────────────────────────────────────────
  // HANDLERS — RACE LIST
  // ──────────────────────────────────────────

  const toggleCheck = (id: number, e: React.MouseEvent) => {
    e.stopPropagation();
    setCheckedIds(prev => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const toggleSelectAll = () => {
    if (checkedIds.size === goals.length) {
      setCheckedIds(new Set());
    } else {
      setCheckedIds(new Set(goals.map(g => g.id)));
    }
  };

  const handleDelete = async (ids: number[]) => {
    if (!window.confirm(`Delete ${ids.length} race goal${ids.length > 1 ? 's' : ''}?`)) return;
    await Promise.all(ids.map(id => fetch(`/api/coach/race-goals/${id}`, { method: 'DELETE' })));
    setCheckedIds(new Set());
    if (ids.includes(selectedId ?? -1)) setSelectedId(null);
    fetchAll();
  };

  const handleEdit = () => {
    const goal = goals.find(g => g.id === [...checkedIds][0]);
    if (goal) { setEditingGoal(goal); setModalMode('edit'); }
  };

  // ──────────────────────────────────────────
  // HANDLERS — STYLE SETTINGS
  // ──────────────────────────────────────────

  const saveStyle = async (spectrum: number, risk: string) => {
    setIsSavingStyle(true);
    try {
      await fetch('/api/user-settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ coaching_style_spectrum: spectrum, recommendation_style: risk }),
      });
    } finally {
      setIsSavingStyle(false);
    }
  };

  const handleSpectrumChange = (value: number) => {
    setCoachingSpectrum(value);
    saveStyle(value, riskTolerance);
  };

  const handleRiskChange = (value: string) => {
    setRiskTolerance(value);
    saveStyle(coachingSpectrum, value);
  };

  const handleProfileSave = async (ps: string, ss: string, el: string) => {
    setPrimarySport(ps);
    setSecondarySport(ss);
    setExperienceLevel(el);
    setEditingProfile(false);
    await fetch('/api/user-settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ primary_sport: ps, secondary_sport: ss || null, training_experience: el }),
    });
  };

  // ──────────────────────────────────────────
  // HANDLERS — AEROBIC ASSESSMENT
  // ──────────────────────────────────────────

  const handleActivitySelect = async (activityId: number | null) => {
    setSelectedActivityId(activityId);
    setDriftPreview(null);
    setAssessmentError(null);
    setHrStream([]);
    setStreamTotalMinutes(0);
    setCooldownMinutes(0);
    if (!activityId) return;
    setIsLoadingStream(true);
    try {
      const res = await fetch(`/api/coach/hr-stream/${activityId}`);
      const d = await res.json();
      if (d.success) {
        setHrStream(d.data);
        setStreamTotalMinutes(d.total_minutes);
      } else {
        setAssessmentError(d.error || 'Could not load HR stream.');
      }
    } catch {
      setAssessmentError('Network error loading HR stream.');
    } finally {
      setIsLoadingStream(false);
    }
  };

  const handleAnalyzePreview = async () => {
    if (!selectedActivityId) return;
    setIsAnalyzing(true);
    setAssessmentError(null);
    setDriftPreview(null);
    try {
      const res = await fetch('/api/coach/aerobic-assessments/preview', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          activity_id: selectedActivityId,
          warmup_minutes: warmupMinutes,
          cooldown_minutes: cooldownMinutes,
          ant_bpm: antBpm ? parseFloat(antBpm) : null,
        }),
      });
      const d = await res.json();
      if (d.success) {
        setDriftPreview(d.analysis);
      } else {
        setAssessmentError(d.error || 'Analysis failed.');
      }
    } catch {
      setAssessmentError('Network error. Please try again.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleSaveAssessment = async () => {
    if (!selectedActivityId || !driftPreview) return;
    setIsSavingAssessment(true);
    setAssessmentError(null);
    try {
      const res = await fetch('/api/coach/aerobic-assessments', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          activity_id: selectedActivityId,
          warmup_minutes: warmupMinutes,
          cooldown_minutes: cooldownMinutes,
          ant_bpm: antBpm ? parseFloat(antBpm) : null,
          notes: assessmentNotes || null,
        }),
      });
      const d = await res.json();
      if (d.success) {
        setDriftPreview(null);
        setSelectedActivityId(null);
        setAntBpm('');
        setAssessmentNotes('');
        setWarmupMinutes(10);
        setCooldownMinutes(0);
        setHrStream([]);
        setStreamTotalMinutes(0);
        fetchAll();
      } else {
        setAssessmentError(d.error || 'Save failed.');
      }
    } catch {
      setAssessmentError('Network error. Please try again.');
    } finally {
      setIsSavingAssessment(false);
    }
  };

  const handleDeleteAssessment = async (id: number) => {
    if (!window.confirm('Delete this assessment?')) return;
    await fetch(`/api/coach/aerobic-assessments/${id}`, { method: 'DELETE' });
    fetchAll();
  };

  // ── AeT method + Lactate Step Test handlers ──
  const handleSetMethod = async (m: AeTMethod) => {
    setAetMethod(m);
    setAssessmentError(null);
    setLactateError(null);
    try {
      await fetch('/api/coach/aet-method', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ method: m }),
      });
    } catch {
      /* non-blocking — the toggle still reflects the choice locally */
    }
  };

  const buildLactateStagesPayload = () =>
    lactateStages
      .map((s, i) => ({
        stage: i + 1,
        grade: s.grade !== '' ? parseFloat(s.grade) : null,
        hr: s.hr !== '' ? parseFloat(s.hr) : null,
        lactate: s.lactate !== '' ? parseFloat(s.lactate) : null,
      }))
      .filter(s => s.hr !== null && s.lactate !== null);

  const handleAnalyzeLactate = async () => {
    setIsAnalyzingLactate(true);
    setLactateError(null);
    setLactatePreview(null);
    try {
      const res = await fetch('/api/coach/lactate-step-tests/preview', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          stages: buildLactateStagesPayload(),
          baseline_lactate: lactateBaseline !== '' ? parseFloat(lactateBaseline) : null,
        }),
      });
      const d = await res.json();
      // Show the analysis either way: a valid LT1, or the invalid verdict with its reason.
      if (d.analysis) {
        setLactatePreview(d.analysis);
      } else {
        setLactateError(d.error || 'Analysis failed.');
      }
    } catch {
      setLactateError('Network error. Please try again.');
    } finally {
      setIsAnalyzingLactate(false);
    }
  };

  const handleSaveLactate = async () => {
    if (!lactatePreview?.valid) return;
    setIsSavingLactate(true);
    setLactateError(null);
    try {
      const res = await fetch('/api/coach/lactate-step-tests', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          stages: buildLactateStagesPayload(),
          baseline_lactate: lactateBaseline !== '' ? parseFloat(lactateBaseline) : null,
          speed: lactateSpeed !== '' ? parseFloat(lactateSpeed) : null,
          speed_unit: lactateSpeedUnit,
          notes: lactateNotes || null,
        }),
      });
      const d = await res.json();
      if (d.success) {
        setLactatePreview(null);
        setLactateNotes('');
        setLactateStages([
          { grade: '0', hr: '', lactate: '' },
          { grade: '1.5', hr: '', lactate: '' },
          { grade: '3.0', hr: '', lactate: '' },
          { grade: '4.5', hr: '', lactate: '' },
        ]);
        setLactateBaseline('');
        fetchAll();
      } else {
        setLactateError(d.error || 'Save failed.');
      }
    } catch {
      setLactateError('Network error. Please try again.');
    } finally {
      setIsSavingLactate(false);
    }
  };

  const handleDeleteLactate = async (id: number) => {
    if (!window.confirm('Delete this step test?')) return;
    await fetch(`/api/coach/lactate-step-tests/${id}`, { method: 'DELETE' });
    fetchAll();
  };

  const handleBackfill = async () => {
    setIsBackfilling(true);
    setAssessmentError(null);
    try {
      const res = await fetch('/api/coach/backfill-hr-streams', { method: 'POST' });
      const d = await res.json();
      if (d.success) {
        await fetchAll();
        if (d.fetched === 0) {
          const detail = d.errors?.length ? ` (${d.errors[0]})` : '';
          setAssessmentError(`${d.message}${detail}`);
        }
      } else {
        setAssessmentError(d.error || 'Backfill failed.');
      }
    } catch {
      setAssessmentError('Network error during backfill.');
    } finally {
      setIsBackfilling(false);
    }
  };

  // ──────────────────────────────────────────
  // RENDER HELPERS
  // ──────────────────────────────────────────

  const sorted = [...goals].sort((a, b) => {
    const pri = { A: 0, B: 1, C: 2 };
    if (pri[a.priority] !== pri[b.priority]) return pri[a.priority] - pri[b.priority];
    return new Date(a.race_date + 'T12:00:00').getTime() - new Date(b.race_date + 'T12:00:00').getTime();
  });

  const priorityLabel = (p: 'A' | 'B' | 'C') =>
    p === 'A' ? '"A"' : p;

  const priorityColor = (p: 'A' | 'B' | 'C') =>
    p === 'A' ? '#FF5722' : p === 'B' ? '#7D9CB8' : 'rgba(125,156,184,0.5)';

  const communicationLabel = (v: number) => {
    if (v <= 25) return 'Casual';
    if (v <= 50) return 'Supportive';
    if (v <= 75) return 'Motivational';
    return 'Analytical';
  };

  const riskLabel = (v: string) => v.charAt(0).toUpperCase() + v.slice(1);

  const sportLabel = (v: string) => {
    const map: Record<string, string> = {
      trail_running: 'Trail Running', running: 'Running', road_running: 'Road Running',
      cycling: 'Cycling', swimming: 'Swimming', triathlon: 'Triathlon',
      rowing: 'Rowing', backcountry_skiing: 'Backcountry Skiing',
      strength: 'Strength', other: 'Other', '': 'None',
    };
    return map[v] ?? v;
  };

  const experienceLabel = (v: string) => {
    // Legacy enum values
    const legacy: Record<string, string> = {
      beginner: 'Beginner', intermediate: 'Intermediate', advanced: 'Advanced', elite: 'Elite',
    };
    if (legacy[v]) return legacy[v];
    // Year value — show as "Since YYYY"
    if (/^\d{4}$/.test(v)) return `Since ${v}`;
    return v;
  };

  if (isLoading) {
    return (
      <div style={{ padding: '40px', textAlign: 'center', color: '#7D9CB8', fontSize: '0.875rem' }}>
        Loading season data...
      </div>
    );
  }

  // ──────────────────────────────────────────
  // RENDER
  // ──────────────────────────────────────────

  return (
    <>
      {/* Race Goal Modal */}
      {modalMode && (
        <GoalModal
          mode={modalMode}
          initialData={editingGoal ?? undefined}
          onSave={() => { setModalMode(null); setEditingGoal(null); setCheckedIds(new Set()); fetchAll(); }}
          onClose={() => { setModalMode(null); setEditingGoal(null); }}
        />
      )}

      {/* Athlete Profile Modal */}
      {editingProfile && (
        <AthleteProfileModal
          primarySport={primarySport}
          secondarySport={secondarySport}
          experienceLevel={experienceLevel}
          onSave={handleProfileSave}
          onClose={() => setEditingProfile(false)}
        />
      )}

      {/* Coaching Pref Modal */}
      {editingPref && (
        <PrefModal
          pref={editingPref}
          coachingSpectrum={coachingSpectrum}
          riskTolerance={riskTolerance}
          onSpectrumChange={handleSpectrumChange}
          onRiskChange={handleRiskChange}
          onClose={() => setEditingPref(null)}
        />
      )}

      <div style={{ display: 'flex', gap: '20px', alignItems: 'flex-start', background: '#f0f4f8', borderRadius: '10px', padding: '16px', maxWidth: '1200px', margin: '0 auto' }}>

        {/* ── LEFT SIDEBAR COLUMN ── */}
        <div style={{ width: '280px', flexShrink: 0, display: 'flex', flexDirection: 'column', gap: '12px' }}>

        {/* Race Season card */}
        <div style={{
          backgroundColor: 'white',
          borderRadius: '8px',
          border: '1px solid #d1dce8',
          boxShadow: '0 2px 6px rgba(0,0,0,0.07)',
          overflow: 'hidden',
        }}>
          {/* Panel header */}
          <div style={{
            background: 'linear-gradient(90deg, #E6F0FF 0%, #7D9CB8 50%, #1B2E4B 100%)',
            padding: '10px 16px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}>
            <span style={{ fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.12em', color: '#1B2E4B', textTransform: 'uppercase' }}>
              Race Season
            </span>
            {goals.length > 0 && (
              <input
                type="checkbox"
                checked={checkedIds.size === goals.length && goals.length > 0}
                onChange={toggleSelectAll}
                title="Select all"
                style={{ accentColor: '#FF5722', cursor: 'pointer' }}
              />
            )}
          </div>

          {/* Action bar — visible when items checked */}
          {checkedIds.size > 0 && (
            <div style={{
              padding: '8px 16px',
              backgroundColor: '#1B2E4B',
              display: 'flex',
              gap: '8px',
              alignItems: 'center',
              borderBottom: '1px solid rgba(125,156,184,0.2)',
            }}>
              <span style={{ fontSize: '0.72rem', color: '#7D9CB8', flex: 1 }}>
                {checkedIds.size} selected
              </span>
              {checkedIds.size === 1 && (
                <button
                  onClick={handleEdit}
                  style={{
                    padding: '4px 12px',
                    backgroundColor: 'rgba(125,156,184,0.15)',
                    border: '1px solid rgba(125,156,184,0.4)',
                    borderRadius: '4px',
                    color: '#E6F0FF',
                    fontSize: '0.72rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                  }}
                >
                  Edit
                </button>
              )}
              <button
                onClick={() => handleDelete([...checkedIds])}
                style={{
                  padding: '4px 12px',
                  backgroundColor: 'rgba(220,38,38,0.15)',
                  border: '1px solid rgba(220,38,38,0.4)',
                  borderRadius: '4px',
                  color: '#fca5a5',
                  fontSize: '0.72rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                Delete
              </button>
            </div>
          )}

          {/* Race rows */}
          <div>
            {sorted.length === 0 ? (
              <div style={{ padding: '24px 16px', textAlign: 'center', color: '#9ca3af', fontSize: '0.8rem' }}>
                No races configured
              </div>
            ) : (
              sorted.map(goal => {
                const isSelected = selectedId === goal.id;
                const isChecked = checkedIds.has(goal.id);
                return (
                  <div
                    key={goal.id}
                    onClick={() => setSelectedId(goal.id)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '10px',
                      padding: '10px 16px',
                      backgroundColor: isSelected ? '#f0f7ff' : 'white',
                      borderLeft: isSelected ? '3px solid #3b82f6' : '3px solid transparent',
                      borderBottom: '1px solid #f3f4f6',
                      cursor: 'pointer',
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={isChecked}
                      onChange={() => {}}
                      onClick={e => toggleCheck(goal.id, e)}
                      style={{ accentColor: '#FF5722', cursor: 'pointer', flexShrink: 0 }}
                    />
                    {/* Priority badge */}
                    <span style={{
                      fontSize: '0.7rem',
                      fontWeight: 700,
                      color: priorityColor(goal.priority),
                      letterSpacing: '0.04em',
                      flexShrink: 0,
                      minWidth: '20px',
                    }}>
                      {priorityLabel(goal.priority)}
                    </span>
                    {/* Name + meta */}
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{
                        fontSize: '0.8rem',
                        fontWeight: 600,
                        color: '#1F2937',
                        whiteSpace: 'nowrap',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                      }}>
                        {goal.race_name}
                      </div>
                      <div style={{ fontSize: '0.7rem', color: '#9ca3af', marginTop: '2px' }}>
                        {formatDate(goal.race_date)}
                        {goal.distance_miles ? ` · ${goal.distance_miles}mi` : ''}
                        {goal.race_type ? ` · ${goal.race_type}` : ''}
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>

          {/* Add Race button */}
          <div style={{ padding: '12px 16px', borderTop: '1px solid #f3f4f6' }}>
            <button
              onClick={() => { setEditingGoal(null); setModalMode('add'); }}
              style={{
                width: '100%',
                padding: '8px',
                backgroundColor: '#FF5722',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '0.75rem',
                fontWeight: 700,
                letterSpacing: '0.06em',
              }}
            >
              + Add Race
            </button>
          </div>
        </div>{/* end Race Season card */}

        {/* Coaching Preferences card */}
        <div style={{
          backgroundColor: 'white',
          borderRadius: '8px',
          border: '1px solid #d1dce8',
          boxShadow: '0 2px 6px rgba(0,0,0,0.07)',
          overflow: 'hidden',
        }}>
          <div style={{
            background: 'linear-gradient(90deg, #E6F0FF 0%, #7D9CB8 50%, #1B2E4B 100%)',
            padding: '10px 16px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}>
            <span style={{ fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.12em', color: '#1B2E4B', textTransform: 'uppercase' }}>
              Coaching Preferences
            </span>
            {isSavingStyle && (
              <span style={{ fontSize: '0.62rem', color: '#1B2E4B', opacity: 0.6 }}>Saving...</span>
            )}
          </div>

          <div style={{ padding: '10px 16px', borderBottom: '1px solid #f3f4f6', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#1F2937' }}>Communication</div>
              <div style={{ fontSize: '0.7rem', color: '#6b7280', marginTop: '1px' }}>{communicationLabel(coachingSpectrum)}</div>
            </div>
            <button
              onClick={() => setEditingPref('communication')}
              style={{ padding: '4px 12px', backgroundColor: 'white', border: '1px solid #dee2e6', borderRadius: '4px', cursor: 'pointer', fontSize: '0.72rem', fontWeight: 600, color: '#6b7280', flexShrink: 0 }}
            >
              Edit
            </button>
          </div>

          <div style={{ padding: '10px 16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#1F2937' }}>Risk Tolerance</div>
              <div style={{ fontSize: '0.7rem', color: '#6b7280', marginTop: '1px' }}>{riskLabel(riskTolerance)}</div>
            </div>
            <button
              onClick={() => setEditingPref('risk')}
              style={{ padding: '4px 12px', backgroundColor: 'white', border: '1px solid #dee2e6', borderRadius: '4px', cursor: 'pointer', fontSize: '0.72rem', fontWeight: 600, color: '#6b7280', flexShrink: 0 }}
            >
              Edit
            </button>
          </div>
        </div>{/* end Coaching Preferences card */}

        {/* Athlete Profile card */}
        <div style={{
          backgroundColor: 'white',
          borderRadius: '8px',
          border: '1px solid #d1dce8',
          boxShadow: '0 2px 6px rgba(0,0,0,0.07)',
          overflow: 'hidden',
        }}>
          <div style={{
            background: 'linear-gradient(90deg, #E6F0FF 0%, #7D9CB8 50%, #1B2E4B 100%)',
            padding: '10px 16px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}>
            <span style={{ fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.12em', color: '#1B2E4B', textTransform: 'uppercase' }}>
              Athlete Profile
            </span>
          </div>

          <div style={{ padding: '10px 16px', borderBottom: '1px solid #f3f4f6', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#1F2937' }}>Primary Sport</div>
              <div style={{ fontSize: '0.7rem', color: '#6b7280', marginTop: '1px' }}>{sportLabel(primarySport)}</div>
            </div>
            <button
              onClick={() => setEditingProfile(true)}
              style={{ padding: '4px 12px', backgroundColor: 'white', border: '1px solid #dee2e6', borderRadius: '4px', cursor: 'pointer', fontSize: '0.72rem', fontWeight: 600, color: '#6b7280', flexShrink: 0 }}
            >
              Edit
            </button>
          </div>

          <div style={{ padding: '10px 16px', borderBottom: '1px solid #f3f4f6', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#1F2937' }}>Cross-Training</div>
              <div style={{ fontSize: '0.7rem', color: '#6b7280', marginTop: '1px' }}>{sportLabel(secondarySport)}</div>
            </div>
          </div>

          <div style={{ padding: '10px 16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#1F2937' }}>Experience</div>
              <div style={{ fontSize: '0.7rem', color: '#6b7280', marginTop: '1px' }}>{experienceLabel(experienceLevel)}</div>
            </div>
          </div>
        </div>{/* end Athlete Profile card */}

        </div>{/* end LEFT SIDEBAR COLUMN */}

        {/* ── RIGHT MAIN AREA ── */}
        <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <RaceReadinessCard readiness={raceReadiness} />
          <AthleteModelPanel
            model={athleteModel}
            onOpenGoalModal={() => { setEditingGoal(null); setModalMode('add'); }}
            onOpenProfileModal={() => setEditingProfile(true)}
            onOpenPrefsModal={() => setEditingPref('communication')}
          />
          {aetMethod === 'lactate_step' ? (
            <LactateStepTestPanel
              method={aetMethod}
              onMethodChange={handleSetMethod}
              tests={lactateTests}
              speed={lactateSpeed}
              setSpeed={setLactateSpeed}
              speedUnit={lactateSpeedUnit}
              setSpeedUnit={setLactateSpeedUnit}
              baseline={lactateBaseline}
              setBaseline={setLactateBaseline}
              stages={lactateStages}
              setStages={setLactateStages}
              notes={lactateNotes}
              setNotes={setLactateNotes}
              preview={lactatePreview}
              isAnalyzing={isAnalyzingLactate}
              isSaving={isSavingLactate}
              error={lactateError}
              onAnalyze={handleAnalyzeLactate}
              onSave={handleSaveLactate}
              onDelete={handleDeleteLactate}
            />
          ) : (
            <AerobicAssessmentPanel
              method={aetMethod}
              onMethodChange={handleSetMethod}
              assessments={assessments}
              effectiveAet={effectiveAet}
              hrActivities={hrActivities}
              selectedActivityId={selectedActivityId}
              onActivitySelect={handleActivitySelect}
              warmupMinutes={warmupMinutes}
              setWarmupMinutes={setWarmupMinutes}
              cooldownMinutes={cooldownMinutes}
              setCooldownMinutes={setCooldownMinutes}
              antBpm={antBpm}
              setAntBpm={setAntBpm}
              assessmentNotes={assessmentNotes}
              setAssessmentNotes={setAssessmentNotes}
              driftPreview={driftPreview}
              isAnalyzing={isAnalyzing}
              isSavingAssessment={isSavingAssessment}
              assessmentError={assessmentError}
              hrStream={hrStream}
              streamTotalMinutes={streamTotalMinutes}
              isLoadingStream={isLoadingStream}
              onAnalyze={handleAnalyzePreview}
              onSave={handleSaveAssessment}
              onDelete={handleDeleteAssessment}
              onBackfill={handleBackfill}
              isBackfilling={isBackfilling}
            />
          )}
        </div>

      </div>
    </>
  );
};

export default SeasonPage;
