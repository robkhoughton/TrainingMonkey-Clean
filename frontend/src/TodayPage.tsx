import React, { useState, useEffect } from 'react';
import { RaceReadinessCard, RaceReadiness } from './CoachPage';

// ─── Brand tokens ─────────────────────────────────────────────────────────────
const FONT = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, sans-serif';
const BG    = '#1B2E4B';
const CARD  = '#243856';
const TEXT  = '#E6F0FF';
const MUTED = '#7D9CB8';
const SAGE  = '#6B8F7F';
const BLUE  = '#3b82f6';
const GREEN = '#16a34a';
const AMBER = '#d97706';
const RED_C = '#dc2626';
const DATA_HEADER_BG = 'linear-gradient(90deg, #1B2E4B 0%, #2d4a6e 100%)';


const CARD_STYLE: React.CSSProperties = {
  background: CARD, borderRadius: '8px',
  boxShadow: '0 2px 4px rgba(0,0,0,0.25)', overflow: 'hidden',
};

// ─── Types ────────────────────────────────────────────────────────────────────

interface WellnessData {
  readiness_state: 'GREEN' | 'YELLOW_SYMPATHETIC' | 'YELLOW_PARASYMPATHETIC' | 'RED' | 'UNKNOWN' | null;
  readiness_flags: Record<string, boolean>;
  readiness_narrative: string | null;
  hrv_value: number | null;
  hrv_source: string | null;
  hrv_z: number | null;
  rhr_z: number | null;
  hrv_reading_count: number | null;
  rhr_reading_count: number | null;
  resting_hr: number | null;
  sleep_duration_secs: number | null;
  sleep_score: number | null;
  is_overreaching: boolean;
}

interface TrainingMetrics {
  externalAcwr: number;
  internalAcwr: number;
  normalizedDivergence: number;
  injuryRiskScore: number;
  injuryRiskLabel: string;
  daysSinceRest: number;
}

// Matches the actual /api/journal response shape
interface JournalEntry {
  date: string;
  is_today: boolean;
  is_next_incomplete?: boolean;
  recommendation_target_date: string | null;
  todays_decision: string;
  structured_output?: any;
  observations: {
    pain_percentage: number | null;
    morning_soreness: number | null;
    energy_level: number | null;
    rpe_score: number | null;
    notes: string;
  };
}

// ─── Why Panel ────────────────────────────────────────────────────────────────
interface ConversationMessage { role: 'user' | 'assistant'; content: string; }
interface WhyPanelState {
  status: 'idle' | 'loading' | 'active' | 'error';
  conversation: ConversationMessage[];
  inputText: string;
  isSendingTurn: boolean;
}

const WhyRecommendationPanel: React.FC<{
  structuredOutput: any;
  targetDate: string;
}> = ({ structuredOutput, targetDate }) => {
  const [state, setState] = useState<WhyPanelState>({
    status: 'idle', conversation: [], inputText: '', isSendingTurn: false,
  });

  const handleWhyClick = async () => {
    setState(s => ({ ...s, status: 'loading' }));
    try {
      const res = await fetch('/api/recommendation-conversation/explain', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ recommendation_date: targetDate, structured_output: structuredOutput, metrics: {} }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setState(s => ({ ...s, status: 'active', conversation: data.conversation }));
    } catch {
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
          structured_output: structuredOutput,
        }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setState(s => ({ ...s, conversation: data.conversation, isSendingTurn: false }));
    } catch {
      setState(s => ({ ...s, isSendingTurn: false }));
    }
  };

  const handleDone = () => {
    fetch('/api/recommendation-conversation/finish', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ recommendation_date: targetDate, conversation: state.conversation }),
    }).catch(() => {});
    setState(s => ({ ...s, status: 'idle' }));
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); }
  };

  return (
    <div style={{ marginTop: '14px', paddingTop: '12px', borderTop: '1px solid rgba(125,156,184,0.1)' }}>
      {state.status === 'idle' && (
        <button
          onClick={handleWhyClick}
          style={{
            backgroundColor: 'transparent', color: BLUE,
            border: `1px solid ${BLUE}`, borderRadius: '4px',
            padding: '4px 12px', fontSize: '0.75rem', fontWeight: 600,
            cursor: 'pointer', fontFamily: FONT,
          }}
        >
          Why this recommendation?
        </button>
      )}

      {state.status === 'loading' && (
        <div style={{ fontSize: '0.75rem', color: MUTED, fontStyle: 'italic', fontFamily: FONT }}>
          Generating explanation...
        </div>
      )}

      {state.status === 'error' && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '0.75rem', color: RED_C, fontFamily: FONT }}>
            Could not load explanation.
          </span>
          <button
            onClick={() => setState(s => ({ ...s, status: 'idle' }))}
            style={{
              backgroundColor: 'transparent', color: BLUE, border: `1px solid ${BLUE}`,
              borderRadius: '4px', padding: '2px 8px', fontSize: '0.72rem', cursor: 'pointer', fontFamily: FONT,
            }}
          >
            Retry
          </button>
        </div>
      )}

      {state.status === 'active' && (
        <div style={{ marginTop: '8px' }}>
          <div style={{
            maxHeight: '300px', overflowY: 'auto',
            border: '1px solid rgba(125,156,184,0.18)', borderRadius: '6px',
            padding: '8px', background: 'rgba(27,46,75,0.7)',
            display: 'flex', flexDirection: 'column', gap: '8px',
          }}>
            {state.conversation.map((msg, idx) => (
              <div key={idx} style={{ display: 'flex', justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start' }}>
                <div style={{
                  maxWidth: '85%', padding: '8px 10px', borderRadius: '6px',
                  fontSize: '0.8rem', lineHeight: '1.55', textAlign: 'left',
                  background: msg.role === 'user' ? 'rgba(59,130,246,0.18)' : CARD,
                  color: TEXT, fontFamily: FONT,
                }}>
                  {msg.content}
                </div>
              </div>
            ))}
          </div>
          <div style={{ display: 'flex', gap: '6px', marginTop: '8px', alignItems: 'center' }}>
            <input
              type="text"
              value={state.inputText}
              onChange={e => setState(s => ({ ...s, inputText: e.target.value }))}
              onKeyDown={handleKeyDown}
              placeholder="Ask a follow-up question..."
              disabled={state.isSendingTurn}
              style={{
                flex: 1, padding: '5px 8px', fontSize: '0.8rem', fontFamily: FONT,
                background: 'rgba(27,46,75,0.8)', color: TEXT,
                border: '1px solid rgba(125,156,184,0.25)', borderRadius: '4px',
                opacity: state.isSendingTurn ? 0.6 : 1,
              }}
            />
            <button
              onClick={handleSend}
              disabled={state.isSendingTurn || !state.inputText.trim()}
              style={{
                background: BLUE, color: 'white', border: 'none', borderRadius: '4px',
                padding: '5px 12px', fontSize: '0.8rem', fontWeight: 600,
                cursor: (state.isSendingTurn || !state.inputText.trim()) ? 'not-allowed' : 'pointer',
                opacity: (state.isSendingTurn || !state.inputText.trim()) ? 0.6 : 1,
                fontFamily: FONT,
              }}
            >
              Send
            </button>
            <button
              onClick={handleDone}
              style={{
                background: MUTED, color: BG, border: 'none', borderRadius: '4px',
                padding: '5px 12px', fontSize: '0.8rem', fontWeight: 600,
                cursor: 'pointer', fontFamily: FONT,
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

interface DailyWorkout {
  date?: string;
  day_of_week?: string;
  workout_type: string;
  description: string;
  duration_estimate: string;
  intensity: string;
  key_focus: string;
}

interface WeeklyProgram {
  week_summary: string;
  daily_program: DailyWorkout[];
}

interface JournalContext {
  stage_name: string | null;
  weeks_to_race: number | null;
  race_name: string | null;
  today_session: { type: string; intensity: string } | null;
  sessions_completed: number;
  total_sessions: number;
  week_days: Array<{ date: string; miles: number; vert: number; is_actual: boolean }>;
  week_total_miles: number;
  week_total_vert: number;
  planned_week_miles: number;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function todayIso(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

function formatDateLong(): string {
  return new Date().toLocaleDateString('en-US', {
    weekday: 'long', month: 'long', day: 'numeric', year: 'numeric',
  });
}

function getWeekDates(): Array<{ iso: string; abbrev: string }> {
  const DAY_ABBREVS = ['S', 'M', 'Tu', 'W', 'Th', 'F', 'S'];
  const today = new Date();
  const dow = today.getDay(); // 0=Sunday
  // On Sunday the new week just started and has no activities yet.
  // Show the just-completed previous week (last Sun–Sat) so mileage is always visible.
  const offset = dow === 0 ? 7 : dow;
  const sunday = new Date(today);
  sunday.setDate(today.getDate() - offset);
  return Array.from({ length: 7 }, (_, i) => {
    const d = new Date(sunday);
    d.setDate(sunday.getDate() + i);
    // Use local date components — toISOString() converts to UTC and can shift the date
    // for users in negative-offset timezones (e.g. Pacific), matching todayIso() behaviour.
    const iso = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
    return { iso, abbrev: DAY_ABBREVS[i] };
  });
}

function dayOfWeekName(iso: string): string {
  return new Date(`${iso}T12:00:00`).toLocaleDateString('en-US', { weekday: 'long' });
}

function workoutAbbrev(type: string): string {
  if (!type) return '—';
  const t = type.toLowerCase();
  if (t.includes('rest') || t.includes('off')) return 'OFF';
  if (t.includes('run') || t.includes('trail') || t.includes('jog')) return 'R';
  if (t.includes('strength') || t.includes('weight') || t.includes('gym')) return 'S';
  if (t.includes('mobil') || t.includes('yoga') || t.includes('recover') || t.includes('stretch')) return 'M';
  if (t.includes('bike') || t.includes('cycle') || t.includes('swim') || t.includes('cross')) return 'X';
  return type.slice(0, 3).toUpperCase();
}

function acwrStatus(v: number): { color: string; label: string } {
  if (!v) return { color: MUTED, label: 'No data' };
  if (v < 0.8)  return { color: MUTED,  label: 'Undertrained' };
  if (v <= 1.3) return { color: GREEN,  label: 'Sweet spot' };
  if (v <= 1.5) return { color: AMBER,  label: 'Elevated' };
  return { color: RED_C, label: 'High risk' };
}

function divStatus(v: number): { color: string; label: string } {
  const abs = Math.abs(v);
  if (abs < 0.15) return { color: GREEN, label: 'On target' };
  if (abs < 0.35) return { color: AMBER, label: v > 0 ? 'Over plan' : 'Under plan' };
  return { color: RED_C, label: v > 0 ? 'Well over' : 'Well under' };
}

// ─── Primitive components ──────────────────────────────────────────────────────

const Label: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div style={{
    fontSize: '0.88rem', fontWeight: 700, letterSpacing: '0.10em',
    textTransform: 'uppercase', color: '#7D9CB8', fontFamily: FONT, marginBottom: '6px',
  }}>
    {children}
  </div>
);

const CardHeader: React.FC<{ label: string; title?: string }> = ({ label, title }) => (
  <div style={{
    background: DATA_HEADER_BG, padding: '0.5rem 1rem',
    borderBottom: '1px solid rgba(125,156,184,0.12)',
  }}>
    <div style={{ fontSize: '13px', letterSpacing: '0.15em', fontWeight: 700, textTransform: 'uppercase', color: MUTED, fontFamily: FONT }}>
      {label}
    </div>
    {title && <div style={{ fontSize: '16px', fontWeight: 700, color: TEXT, fontFamily: FONT, marginTop: '1px' }}>{title}</div>}
  </div>
);

// ─── TrainingReadinessCard ─────────────────────────────────────────────────────
// ANS-based readiness: z-score HRV+RHR against personal baselines.
// Four states: GREEN / YELLOW_SYMPATHETIC / YELLOW_PARASYMPATHETIC / RED / UNKNOWN

interface TrainingReadinessProps {
  readiness_state: WellnessData['readiness_state'];
  readiness_narrative: string | null;
  hrv_value: number | null;
  hrv_z: number | null;
  hrv_reading_count: number | null;
  resting_hr: number | null;
  rhr_z: number | null;
  rhr_reading_count: number | null;
  sleep_duration_secs: number | null;
  sleep_score: number | null;
}

// Stoplight segments — severity order: RED, CAUTION, DEEP HOLE, GREEN
const READINESS_SEGMENTS = [
  { key: 'RED',                    label: 'OVERREACHING', color: RED_C },
  { key: 'YELLOW_SYMPATHETIC',     label: 'CAUTION',      color: AMBER },
  { key: 'YELLOW_PARASYMPATHETIC', label: 'DEEP HOLE',    color: AMBER },
  { key: 'GREEN',                  label: 'GREEN',        color: GREEN },
];

const TrainingReadinessCard: React.FC<TrainingReadinessProps> = (p) => {
  const key = p.readiness_state ?? 'UNKNOWN';
  const isCalibrating = key === 'UNKNOWN' || p.readiness_state === null;
  const activeSeg = READINESS_SEGMENTS.find(s => s.key === key) ?? null;
  const activeColor = activeSeg?.color ?? MUTED;
  const activeLabel = activeSeg?.label ?? 'Calibrating';

  const fmtZ = (z: number | null) =>
    z !== null ? `${z >= 0 ? '+' : ''}${z.toFixed(1)}\u03c3` : null;
  const hrsSlept = p.sleep_duration_secs ? (p.sleep_duration_secs / 3600).toFixed(1) : null;

  const BASELINE_DAYS = 14;
  const hrvDaysLeft = isCalibrating ? Math.max(0, BASELINE_DAYS - (p.hrv_reading_count ?? 0)) : 0;
  const rhrDaysLeft = isCalibrating ? Math.max(0, BASELINE_DAYS - (p.rhr_reading_count ?? 0)) : 0;
  const daysLeft = Math.max(hrvDaysLeft, rhrDaysLeft);

  const subs = [
    {
      lbl: 'HRV',
      val: p.hrv_value !== null ? `${Math.round(p.hrv_value)}ms` : '—',
      annot: isCalibrating
        ? (p.hrv_reading_count !== null ? `${p.hrv_reading_count} of ${BASELINE_DAYS} days` : null)
        : fmtZ(p.hrv_z),
    },
    {
      lbl: 'RHR',
      val: p.resting_hr !== null ? `${Math.round(p.resting_hr)}bpm` : '—',
      annot: isCalibrating
        ? (p.rhr_reading_count !== null ? `${p.rhr_reading_count} of ${BASELINE_DAYS} days` : null)
        : fmtZ(p.rhr_z),
    },
    {
      lbl: 'SLEEP',
      val: hrsSlept ? `${hrsSlept}h` : '—',
      annot: p.sleep_score != null ? `score ${p.sleep_score}` : null,
    },
  ];

  return (
    <div style={{ marginBottom: '18px' }}>
      {/* Label — matches ZonedGauge label style */}
      <span style={{
        fontSize: '0.78rem', color: MUTED, fontFamily: FONT,
        letterSpacing: '0.06em', textTransform: 'capitalize',
        display: 'block', marginBottom: '6px',
      }}>
        Training Readiness
      </span>
      {/* Stoplight bar — active segment gets border + top/bottom arrows */}
      <div style={{ display: 'flex', gap: '2px', height: '12px', margin: '10px 0 18px 0' }}>
        {isCalibrating ? (
          <div style={{ flex: 1, borderRadius: '2px', background: MUTED, opacity: 0.25 }} />
        ) : (
          READINESS_SEGMENTS.map(seg => {
            const isActive = seg.key === key;
            return (
              <div key={seg.key} style={{
                flex: 1, borderRadius: '2px',
                background: seg.color,
                opacity: isActive ? 0.90 : 0.18,
                position: 'relative',
                boxShadow: isActive ? `0 0 8px 3px ${seg.color}` : undefined,
              }}>
                {isActive && (
                  <>
                    {/* Top arrow — glow color, points upward */}
                    <div style={{
                      position: 'absolute', top: '-10px', left: '50%',
                      transform: 'translateX(-50%)',
                      width: 0, height: 0,
                      borderLeft: '7px solid transparent',
                      borderRight: '7px solid transparent',
                      borderBottom: `8px solid ${seg.color}`,
                      filter: `drop-shadow(0 0 4px ${seg.color})`,
                      zIndex: 2,
                    }} />
                    {/* Bottom arrow — glow color, points downward */}
                    <div style={{
                      position: 'absolute', bottom: '-10px', left: '50%',
                      transform: 'translateX(-50%)',
                      width: 0, height: 0,
                      borderLeft: '7px solid transparent',
                      borderRight: '7px solid transparent',
                      borderTop: `8px solid ${seg.color}`,
                      filter: `drop-shadow(0 0 4px ${seg.color})`,
                      zIndex: 2,
                    }} />
                  </>
                )}
              </div>
            );
          })
        )}
      </div>
      {/* Narrative — matches ZonedGauge tick label area */}
      <div style={{
        fontSize: '0.72rem', color: MUTED, fontFamily: FONT,
        lineHeight: 1.4, marginTop: '6px', marginBottom: '12px', minHeight: '2.2em',
      }}>
        {isCalibrating
          ? (daysLeft > 0
              ? `Log morning HRV and resting HR daily — ${daysLeft} more day${daysLeft === 1 ? '' : 's'} needed.`
              : 'Baseline complete — readiness will update on next sync.')
          : (p.readiness_narrative ?? '')}
      </div>
      {/* Sub-values: HRV · RHR · SLEEP */}
      <div style={{ display: 'flex', gap: '16px', justifyContent: 'center' }}>
        {subs.map(({ lbl, val, annot }) => (
          <div key={lbl} style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
            <span style={{
              fontSize: '0.68rem', color: MUTED, fontFamily: FONT,
              textTransform: 'uppercase', letterSpacing: '0.06em',
            }}>
              {lbl}
            </span>
            <span style={{ fontSize: '1.05rem', fontWeight: 700, color: TEXT, fontFamily: FONT }}>
              {val}
            </span>
            {annot && (
              <span style={{ fontSize: '0.72rem', color: MUTED, fontFamily: FONT }}>
                {annot}
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

// ─── LoadGauges ────────────────────────────────────────────────────────────────
// Horizontal gauge bars — one per metric, colored zone bands, marker at current value.
// Much more readable than a radar triangle.

interface LoadGaugesProps {
  extAcwr: number | null;
  intAcwr: number | null;
  divergence: number | null;
}

interface ZonedGaugeProps {
  label: string;
  value: number | null;
  valueLabel: string;
  statusColor: string;
  min: number; max: number;
  zones: Array<{ from: number; to: number; color: string; opacity: number }>;
  ticks?: Array<{ value: number; label: string }>;
}

const ZonedGauge: React.FC<ZonedGaugeProps> = ({ label, value, valueLabel, statusColor, min, max, zones, ticks }) => {
  const W = 160, H = 12;
  const toX    = (v: number) => Math.max(0, Math.min(W, ((v - min) / (max - min)) * W));
  const toPct  = (v: number) => `${Math.max(0, Math.min(100, ((v - min) / (max - min)) * 100))}%`;
  const markerX = value !== null ? toX(value) : null;

  return (
    <div style={{ marginBottom: '18px' }}>
      <span style={{ fontSize: '0.78rem', color: MUTED, fontFamily: FONT, letterSpacing: '0.06em', textTransform: 'capitalize', display: 'block', marginBottom: '2px' }}>
        {label}
      </span>
      <div style={{ textAlign: 'center', marginBottom: '5px' }}>
        <span style={{ fontSize: '1.05rem', fontWeight: 700, color: TEXT, fontFamily: FONT, letterSpacing: '0.02em' }}>{valueLabel}</span>
      </div>
      {/* SVG: zone bands + marker only — tick labels rendered as HTML to avoid distortion */}
      <svg width="100%" height={H + 14} viewBox={`0 0 ${W} ${H + 14}`} preserveAspectRatio="none" style={{ display: 'block' }}>
        {zones.map((z, i) => (
          <rect key={i}
            x={toX(z.from)} y={4} width={Math.max(0, toX(z.to) - toX(z.from))} height={H}
            fill={z.color} opacity={z.opacity} rx="2"
          />
        ))}
        <rect x={0} y={4} width={W} height={H} fill="none"
          stroke="rgba(125,156,184,0.25)" strokeWidth="1" rx="2" />
        {markerX !== null && (
          <g>
            <line x1={markerX} y1={2} x2={markerX} y2={H + 5}
              stroke="rgba(255,255,255,0.92)" strokeWidth="1.5" strokeLinecap="square" />
            {/* Upward-pointing triangle — base below bar, tip touches bar bottom */}
            <polygon
              points={`${markerX - 3.5},${H + 12} ${markerX + 3.5},${H + 12} ${markerX},${H + 5}`}
              fill="rgba(255,255,255,0.88)"
            />
          </g>
        )}
      </svg>
      {/* Tick labels as HTML — immune to SVG non-uniform scaling distortion */}
      {ticks && ticks.length > 0 && (
        <div style={{ position: 'relative', height: '18px', marginTop: '2px' }}>
          {ticks.map(t => (
            <span key={t.value} style={{
              position: 'absolute', left: toPct(t.value), transform: 'translateX(-50%)',
              fontSize: '0.72rem', color: MUTED, fontFamily: FONT, whiteSpace: 'nowrap',
            }}>{t.label}</span>
          ))}
        </div>
      )}
    </div>
  );
};

const LoadGauges: React.FC<LoadGaugesProps> = ({ extAcwr, intAcwr, divergence }) => {
  const acwrZones = [
    { from: 0,   to: 0.8, color: MUTED,  opacity: 0.45 },
    { from: 0.8, to: 1.3, color: GREEN,  opacity: 0.70 },
    { from: 1.3, to: 1.5, color: AMBER,  opacity: 0.72 },
    { from: 1.5, to: 2.0, color: RED_C,  opacity: 0.72 },
  ];
  const divZones = [
    { from: -0.5,  to: -0.35, color: RED_C,  opacity: 0.72 },
    { from: -0.35, to: -0.15, color: AMBER,  opacity: 0.65 },
    { from: -0.15, to:  0.15, color: GREEN,  opacity: 0.65 },
    { from:  0.15, to:  0.35, color: AMBER,  opacity: 0.65 },
    { from:  0.35, to:  0.5,  color: RED_C,  opacity: 0.72 },
  ];
  const acwrTicks = [
    { value: 0.8, label: '0.8' }, { value: 1.3, label: '1.3' }, { value: 1.5, label: '1.5' },
  ];
  const divTicks = [
    { value: -0.35, label: '-.35' }, { value: -0.15, label: '-.15' },
    { value: 0,     label: '0'    },
    { value:  0.15, label: '.15'  }, { value:  0.35, label: '.35' },
  ];

  const ea = acwrStatus(extAcwr ?? 0);
  const ia = acwrStatus(intAcwr ?? 0);
  const ds = divStatus(divergence ?? 0);

  return (
    <div style={{ width: '100%' }}>
      <ZonedGauge
        label="External ACWR" value={extAcwr} min={0} max={2.0} zones={acwrZones}
        valueLabel={extAcwr != null ? extAcwr.toFixed(2) : '—'}
        statusColor={ea.color} ticks={acwrTicks}
      />
      <ZonedGauge
        label="Internal ACWR" value={intAcwr} min={0} max={2.0} zones={acwrZones}
        valueLabel={intAcwr != null ? intAcwr.toFixed(2) : '—'}
        statusColor={ia.color} ticks={acwrTicks}
      />
      <ZonedGauge
        label="Divergence" value={divergence} min={-0.5} max={0.5} zones={divZones}
        valueLabel={divergence != null ? divergence.toFixed(3) : '—'}
        statusColor={ds.color} ticks={divTicks}
      />
    </div>
  );
};

// ─── InjuryTrend ───────────────────────────────────────────────────────────────
// 7-day sparkline from journal observations.

interface InjuryTrendProps {
  entries: JournalEntry[];
}

const InjuryTrend: React.FC<InjuryTrendProps> = ({ entries }) => {
  const W = 210, H = 100, PL = 24, PR = 32, PT = 8, PB = 20;
  const CW = W - PL - PR; const CH = H - PT - PB;

  const today = new Date();
  const days = Array.from({ length: 7 }, (_, i) => {
    const d = new Date(today); d.setDate(today.getDate() - (6 - i));
    return d.toISOString().slice(0, 10);
  });

  const byDate: Record<string, JournalEntry> = {};
  entries.forEach(e => { byDate[e.date] = e; });

  const xPos = (i: number) => PL + (i / 6) * CW;
  const yPos = (v: number) => PT + CH * (1 - v / 100);

  const painPts = days.map((d, i) => ({
    x: xPos(i), y: yPos(byDate[d]?.observations?.pain_percentage ?? 0),
    v: byDate[d]?.observations?.pain_percentage ?? null,
  }));
  const sorePts = days.map((d, i) => ({
    x: xPos(i), y: yPos(byDate[d]?.observations?.morning_soreness ?? 0),
    v: byDate[d]?.observations?.morning_soreness ?? null,
  }));

  const toPath = (pts: typeof painPts) =>
    pts.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(' ');

  const lastPain = painPts[6].v; const lastSore = sorePts[6].v;
  const hasAny = entries.some(e =>
    e.observations?.pain_percentage != null || e.observations?.morning_soreness != null
  );

  const trendLabel = (() => {
    if (!hasAny) return null;
    if ((lastPain ?? 0) > 50 || (lastSore ?? 0) > 50) return { text: 'MONITOR', color: AMBER };
    const fp = painPts.find(p => p.v !== null)?.v ?? 0;
    const fs = sorePts.find(p => p.v !== null)?.v ?? 0;
    if ((lastPain ?? 0) <= fp && (lastSore ?? 0) <= fs && (lastPain ?? 0) < 30 && (lastSore ?? 0) < 30)
      return { text: 'TRENDING WELL', color: SAGE };
    return null;
  })();

  const dayAbbrevs = ['S', 'M', 'T', 'W', 'T', 'F', 'S'];
  const todayStr   = todayIso();
  const dayLabels  = days.map(d => dayAbbrevs[new Date(`${d}T12:00:00`).getDay()]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '6px' }}>
      <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`}>
        {/* Y-axis labels */}
        {[0, 50, 100].map(v => (
          <text key={v} x={PL - 4} y={yPos(v) + 3} textAnchor="end"
            fill={MUTED} fontSize="6.5" fontFamily={FONT}>{v}</text>
        ))}
        {/* Y-axis grid */}
        {[50].map(v => (
          <line key={v} x1={PL} y1={yPos(v)} x2={PL + CW} y2={yPos(v)}
            stroke="rgba(125,156,184,0.1)" strokeWidth="1" strokeDasharray="3,3" />
        ))}
        <line x1={PL} y1={PT + CH} x2={PL + CW} y2={PT + CH} stroke="rgba(125,156,184,0.18)" strokeWidth="1" />
        {/* Soreness line */}
        <path d={toPath(sorePts)} fill="none" stroke={AMBER} strokeWidth="1.5" opacity="0.8" strokeLinecap="round" strokeLinejoin="round" />
        {/* Pain line */}
        <path d={toPath(painPts)} fill="none" stroke={RED_C} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        {/* Endpoint dots + labels */}
        {lastPain !== null && (
          <>
            <circle cx={painPts[6].x} cy={painPts[6].y} r="3" fill={RED_C} />
            <text x={painPts[6].x + 5} y={painPts[6].y + 4} fill={RED_C} fontSize="7" fontFamily={FONT} fontWeight="700">
              {Math.round(lastPain)}
            </text>
          </>
        )}
        {lastSore !== null && (
          <>
            <circle cx={sorePts[6].x} cy={sorePts[6].y} r="3" fill={AMBER} />
            <text x={sorePts[6].x + 5} y={sorePts[6].y + 4} fill={AMBER} fontSize="7" fontFamily={FONT} fontWeight="700">
              {Math.round(lastSore)}
            </text>
          </>
        )}
        {/* X-axis day labels */}
        {days.map((d, i) => (
          <text key={d} x={xPos(i)} y={PT + CH + 12} textAnchor="middle"
            fill={d === todayStr ? TEXT : MUTED}
            fontSize={d === todayStr ? '8' : '6.5'}
            fontWeight={d === todayStr ? '700' : '400'}
            fontFamily={FONT}>
            {dayLabels[i]}
          </text>
        ))}
        {/* No-data message */}
        {!hasAny && (
          <text x={PL + CW / 2} y={PT + CH / 2 + 4} textAnchor="middle"
            fill={MUTED} fontSize="8" fontStyle="italic" fontFamily={FONT}>
            No injury data logged
          </text>
        )}
      </svg>

      <div style={{ display: 'flex', gap: '12px', alignItems: 'center', flexWrap: 'wrap', justifyContent: 'center' }}>
        {[{ color: RED_C, label: 'PAIN' }, { color: AMBER, label: 'SORENESS' }].map(({ color, label }) => (
          <div key={label} style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <div style={{ width: '12px', height: '2px', background: color, borderRadius: '1px' }} />
            <span style={{ fontSize: '0.52rem', color: MUTED, fontFamily: FONT, letterSpacing: '0.06em' }}>{label}</span>
          </div>
        ))}
        {trendLabel && (
          <span style={{ fontSize: '0.55rem', fontWeight: 700, color: trendLabel.color, letterSpacing: '0.08em', fontFamily: FONT }}>
            {trendLabel.text}
          </span>
        )}
      </div>
    </div>
  );
};

// ─── Intensity colors (matches WeeklyProgramDisplay) ─────────────────────────
const IC = { low: '#66BB6A', moderate: '#FFD54F', high: '#FF8A65' };

function getSessionChip(session: DailyWorkout | null): { color: string; label: string } | null {
  if (!session) return null;
  const t = (session.workout_type || '').trim();
  if (!t || /^(rest|day off|off)$/i.test(t)) return null;
  const i = (session.intensity || '').toLowerCase();
  const color = i === 'high' ? IC.high : i === 'moderate' ? IC.moderate : IC.low;
  const label = t.replace(/\brun\b/gi, '').replace(/\s+/g, ' ').trim();
  return { color, label };
}

// ─── DayCell ───────────────────────────────────────────────────────────────────

interface DayCellProps { abbrev: string; isToday: boolean; session: DailyWorkout | null; miles?: number; isActual?: boolean; }

const DayCell: React.FC<DayCellProps> = ({ abbrev, isToday, session, miles, isActual = true }) => {
  const chip     = getSessionChip(session);
  const isOff    = !session || (!chip && !(session.workout_type || '').toLowerCase().includes('rest'));
  const isRest   = session && !chip;
  const hasMiles = miles != null && miles > 0.05;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px', opacity: isOff ? 0.4 : 1 }}>
      {/* Actual or planned miles */}
      <div style={{
        fontSize: '0.82rem', fontWeight: isActual ? 600 : 400, height: '16px', lineHeight: '16px',
        color: hasMiles ? (isActual ? TEXT : MUTED) : 'rgba(0,0,0,0)',
        fontStyle: isActual ? 'normal' : 'italic',
        fontFamily: FONT,
      }}>
        {hasMiles ? miles!.toFixed(1) : '0'}
      </div>

      {/* Day letter */}
      <div style={{
        width: '32px', height: '32px', borderRadius: '4px',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        background: isToday ? '#FF5722' : 'rgba(125,156,184,0.08)',
        border: isToday ? 'none' : '1px solid rgba(125,156,184,0.18)',
        fontSize: '0.86rem', fontWeight: isToday ? 700 : 500,
        color: isToday ? 'white' : MUTED, fontFamily: FONT,
      }}>
        {abbrev}
      </div>

      {/* Session chip or Rest/blank */}
      <div style={{ height: '24px', display: 'flex', alignItems: 'center', justifyContent: 'center', maxWidth: '100%' }}>
        {chip ? (
          <div style={{
            background: `${chip.color}22`, border: `1px solid ${chip.color}60`,
            borderRadius: '3px', padding: '2px 5px',
            fontSize: '0.68rem', fontWeight: 700, color: chip.color,
            fontFamily: FONT, whiteSpace: 'nowrap',
            overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: '100%',
          }}>
            {chip.label}
          </div>
        ) : isRest ? (
          <span style={{ fontSize: '0.75rem', color: MUTED, fontFamily: FONT }}>Rest</span>
        ) : null}
      </div>

    </div>
  );
};

// ─── Main component ────────────────────────────────────────────────────────────

interface Props { onNavigateToTab: (tab: string) => void; }

const TodayPage: React.FC<Props> = ({ onNavigateToTab }) => {
  const [wellness,       setWellness]       = useState<WellnessData | null>(null);
  const [metrics,        setMetrics]        = useState<TrainingMetrics | null>(null);
  const [program,        setProgram]        = useState<WeeklyProgram | null>(null);
  const [context,        setContext]        = useState<JournalContext | null>(null);
  const [rec,              setRec]              = useState<string | null>(null);
  const [recTargetDate,    setRecTargetDate]    = useState<string | null>(null);
  const [structuredOutput, setStructuredOutput] = useState<any>({});
  const [journalEntries,   setJournalEntries]   = useState<JournalEntry[]>([]);
  const [loading,          setLoading]          = useState(true);
  const [programLoading,   setProgramLoading]   = useState(true);
  const [raceReadiness,    setRaceReadiness]    = useState<RaceReadiness | null>(null);

  useEffect(() => {
    // Fast endpoints — page renders as soon as these complete
    Promise.all([
      fetch('/api/readiness',                    { credentials: 'include' }).then(r => r.ok ? r.json() : null),
      fetch(`/api/training-data?t=${Date.now()}`, { credentials: 'include' }).then(r => r.ok ? r.json() : null),
      fetch('/api/journal/context',               { credentials: 'include' }).then(r => r.ok ? r.json() : null),
      fetch('/api/journal',                       { credentials: 'include' }).then(r => r.ok ? r.json() : null),
      fetch('/api/coach/race-readiness',          { credentials: 'include' }).then(r => r.ok ? r.json() : null),
    ]).then(([well, training, ctx, recData, readinessData]) => {
      if (well) setWellness(well);
      if (training?.data?.length) {
        const rows = [...training.data].sort((a: any, b: any) => b.date.localeCompare(a.date));
        const r  = rows[0];
        const cm = training.current_metrics || {};
        setMetrics({
          externalAcwr:         r.acute_chronic_ratio       || 0,
          internalAcwr:         r.trimp_acute_chronic_ratio || 0,
          normalizedDivergence: r.normalized_divergence     || 0,
          injuryRiskScore:      cm.injury_risk_score        || 0,
          injuryRiskLabel:      cm.injury_risk_label        || 'LOW',
          daysSinceRest:        cm.days_since_rest          || 0,
        });
      }
      if (readinessData?.success && readinessData?.readiness) setRaceReadiness(readinessData.readiness);
      if (ctx) setContext(ctx);
      if (recData?.data?.length) {
        const entries: JournalEntry[] = recData.data;
        setJournalEntries(entries);
        const matched = entries.find(e => e.is_next_incomplete) ||
          entries.find(e => e.is_today && e.todays_decision && !e.todays_decision.includes('No recommendation available')) ||
          null;
        const r = matched?.todays_decision || null;
        if (r) setRec(r);
        if (matched?.recommendation_target_date) setRecTargetDate(matched.recommendation_target_date);
        if (matched?.structured_output) setStructuredOutput(matched.structured_output);
      }
      setLoading(false);
    }).catch(() => setLoading(false));

    // Weekly program fetches independently — slow LLM call, ~60–90s
    // Page renders without it; week schedule populates when ready
    fetch('/api/coach/weekly-program', { credentials: 'include' })
      .then(r => r.ok ? r.json() : null)
      .then(prog => { if (prog?.program) setProgram(prog.program); })
      .catch(() => {})
      .finally(() => setProgramLoading(false));
  }, []);

  // Session lookup
  const sessionByDate: Record<string, DailyWorkout> = {};
  const sessionByDow:  Record<string, DailyWorkout> = {};
  program?.daily_program.forEach(s => {
    if (s.date)        sessionByDate[s.date] = s;
    if (s.day_of_week) sessionByDow[s.day_of_week] = s;
  });
  const weekDates    = getWeekDates();
  const todayDate    = todayIso();
  const getSession   = (iso: string): DailyWorkout | null =>
    sessionByDate[iso] || sessionByDow[dayOfWeekName(iso)] || null;
  // Use the Rx target date for the session title/badge — keeps title aligned with the narrative.
  // When the next incomplete workout is tomorrow (e.g. today's session is done), recTargetDate
  // will differ from todayDate and we want the session from the Rx date, not today's calendar slot.
  const todaySession = getSession(recTargetDate || todayDate);

  // Priority badge from load + injury signals
  const todayEntry  = journalEntries.find(e => e.is_today);
  const pain        = todayEntry?.observations?.pain_percentage ?? 0;
  const extAcwrVal  = metrics?.externalAcwr ?? 0;
  const divAbs      = Math.abs(metrics?.normalizedDivergence ?? 0);

  const priorityBadge = (() => {
    if (pain > 70 || extAcwrVal > 1.7 || divAbs > 0.5) return { label: 'Caution', color: RED_C };
    if (pain > 50 || extAcwrVal > 1.5 || divAbs > 0.35) return { label: 'Monitor', color: AMBER };
    return { label: 'Ready', color: GREEN };
  })();

  const hasWatchData = wellness?.hrv_source === 'intervals_icu';


  const activeFlags = wellness?.readiness_flags
    ? Object.entries(wellness.readiness_flags)
        .filter(([, v]) => v)
        .map(([k]) => ({
          hrv_suppressed: 'HRV suppressed', rhr_elevated: 'RHR elevated',
          sleep_deficit: 'Sleep deficit', sleep_poor_score: 'Poor sleep score',
          high_soreness: 'High soreness', deep_hole: 'Deep hole',
          is_overreaching: 'Overreaching',
        }[k] || k))
    : [];

  // Workout header for Rx
  const workoutLabel = (() => {
    if (!todaySession) return null;
    const type = todaySession.workout_type || '';
    const dur  = todaySession.duration_estimate || '';
    return type && dur ? `${type} · ${dur}` : type || dur || null;
  })();

  const dividerStyle: React.CSSProperties = {
    width: '1px', background: 'rgba(125,156,184,0.15)', alignSelf: 'stretch', margin: '0 4px',
  };

  return (
    <div style={{ minHeight: '100vh', background: BG, fontFamily: FONT, padding: '24px 24px 80px' }}>
      <style>{`
        @keyframes today-in {
          from { opacity: 0; transform: translateY(8px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        .t-card { animation: today-in 0.3s ease both; }
        .t-card:nth-child(2) { animation-delay: 0.07s; }
        .t-card:nth-child(3) { animation-delay: 0.14s; }
        @media (max-width: 640px) {
          .sig-cols { flex-direction: column !important; }
          .sig-div  { display: none !important; }
          .rx-prose { column-count: 1 !important; }
        }
      `}</style>

      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>

        {/* ── Page header ── */}
        <div style={{ marginBottom: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px', flexWrap: 'wrap' }}>
            <h1 style={{ margin: 0, fontSize: '1.4rem', fontWeight: 600, color: TEXT, fontFamily: FONT }}>Today</h1>
            <span style={{
              display: 'inline-flex', alignItems: 'center', gap: '6px',
              border: `1px solid ${priorityBadge.color}`, borderRadius: '4px',
              padding: '3px 10px', background: `${priorityBadge.color}18`,
            }}>
              <span style={{ width: '7px', height: '7px', borderRadius: '50%', background: priorityBadge.color, display: 'inline-block' }} />
              <span style={{ fontSize: '0.65rem', fontWeight: 700, color: priorityBadge.color, letterSpacing: '0.1em', textTransform: 'uppercase', fontFamily: FONT }}>
                {priorityBadge.label}
              </span>
            </span>
          </div>
          <div style={{ fontSize: '0.8rem', color: MUTED, marginTop: '4px', fontFamily: FONT, textAlign: 'left' }}>{formatDateLong()}</div>
        </div>

        {/* ── 1. Rx card (two-column prose) ── */}
        <div className="t-card" style={{ ...CARD_STYLE, marginBottom: '16px' }}>
          <CardHeader
            label="Training Prescription"
            title={recTargetDate
              ? new Date(recTargetDate + 'T12:00:00').toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })
              : undefined}
          />
          <div style={{ padding: '20px' }}>

            {/* Workout header */}
            {workoutLabel && (
              <div style={{
                fontSize: '1.05rem', fontWeight: 700, color: TEXT, fontFamily: FONT,
                marginBottom: '14px', paddingBottom: '12px',
                borderBottom: '1px solid rgba(125,156,184,0.12)',
                display: 'flex', alignItems: 'center', gap: '10px',
              }}>
                {workoutLabel}
                {todaySession?.intensity && (
                  <span style={{
                    fontSize: '0.62rem', fontWeight: 700, color: SAGE,
                    letterSpacing: '0.1em', textTransform: 'uppercase',
                    border: `1px solid ${SAGE}50`, borderRadius: '3px', padding: '2px 8px',
                  }}>
                    {todaySession.intensity}
                  </span>
                )}
              </div>
            )}

            {loading ? (
              <div style={{ height: '80px', background: 'rgba(125,156,184,0.08)', borderRadius: '4px' }} />
            ) : rec ? (
              <>
                {/* Two-column prose — text fills left column then wraps to right */}
                <div
                  className="rx-prose"
                  style={{ columnCount: 2, columnGap: '32px', columnRule: '1px solid rgba(125,156,184,0.12)',
                           fontSize: '0.92rem', lineHeight: '1.7', color: TEXT, fontFamily: FONT, textAlign: 'left' }}
                >
                  {rec.split(/\n+/).filter(l => l.trim()).length > 1
                    ? rec.split(/\n+/).filter(l => l.trim()).map((para, i) => (
                        <p key={i} style={{ margin: '0 0 10px' }}>{para}</p>
                      ))
                    : <p style={{ margin: 0 }}>{rec}</p>
                  }
                </div>

                {/* Why this Rx? */}
                <WhyRecommendationPanel
                  structuredOutput={structuredOutput}
                  targetDate={recTargetDate || todayDate}
                />
              </>
            ) : (
              <p style={{ margin: 0, color: MUTED, fontSize: '0.9rem', fontStyle: 'italic', fontFamily: FONT }}>
                No coaching recommendation yet. Visit the Coach tab to generate one.
              </p>
            )}
          </div>
        </div>

        {/* ── 2. Signal Panel ── */}
        <div className="t-card" style={{ ...CARD_STYLE, marginBottom: '16px' }}>
          <CardHeader label="Signal Panel" />
          <div className="sig-cols" style={{ display: 'flex', padding: '16px 20px', gap: 0, alignItems: 'flex-start' }}>

            {/* Training Status — injury risk + ANS readiness + volume + rest */}
            <div style={{ flex: 1, minWidth: 0, paddingRight: '20px' }}>
              <div style={{ textAlign: 'left', marginBottom: '10px' }}><Label>Training Status</Label></div>

              {/* Injury Risk gauge */}
              {metrics && (() => {
                const score = metrics.injuryRiskScore;
                const riskColor = score >= 60 ? RED_C : score >= 30 ? AMBER : GREEN;
                const riskZones = [
                  { from: 0,  to: 30,  color: GREEN, opacity: 0.65 },
                  { from: 30, to: 60,  color: AMBER, opacity: 0.68 },
                  { from: 60, to: 100, color: RED_C, opacity: 0.75 },
                ];
                return (
                  <ZonedGauge
                    label="Injury Risk" value={score} min={0} max={100} zones={riskZones}
                    valueLabel={`${Math.round(score)}`}
                    statusColor={riskColor}
                    ticks={[{ value: 30, label: '30' }, { value: 60, label: '60' }]}
                  />
                );
              })()}

              <TrainingReadinessCard
                readiness_state={wellness?.readiness_state ?? null}
                readiness_narrative={wellness?.readiness_narrative ?? null}
                hrv_value={wellness?.hrv_value ?? null}
                hrv_z={wellness?.hrv_z ?? null}
                hrv_reading_count={wellness?.hrv_reading_count ?? null}
                resting_hr={wellness?.resting_hr ?? null}
                rhr_z={wellness?.rhr_z ?? null}
                rhr_reading_count={wellness?.rhr_reading_count ?? null}
                sleep_duration_secs={wellness?.sleep_duration_secs ?? null}
                sleep_score={wellness?.sleep_score ?? null}
              />

              {/* Volume + rest */}
              {(context || metrics) && (
                <div style={{ fontSize: '0.88rem', color: MUTED, fontFamily: FONT, marginTop: '14px', display: 'flex', gap: '16px', flexWrap: 'wrap', justifyContent: 'center' }}>
                  {context && (
                    <span>
                      Week: <strong style={{ color: TEXT }}>{(context.week_total_miles ?? 0).toFixed(1)} mi</strong>
                      {(context.week_total_vert ?? 0) > 0 && (
                        <> · <strong style={{ color: TEXT }}>{Math.round(context.week_total_vert ?? 0).toLocaleString()} ft</strong></>
                      )}
                    </span>
                  )}
                  {metrics && (
                    <span>
                      Rest: <strong style={{ color: metrics.daysSinceRest >= 7 ? AMBER : TEXT }}>
                        {metrics.daysSinceRest === 0 ? 'today' : `${metrics.daysSinceRest}d ago`}
                      </strong>
                    </span>
                  )}
                </div>
              )}
            </div>

            <div className="sig-div" style={dividerStyle} />

            {/* Load — ACWR + divergence gauges */}
            <div style={{ flex: 1, minWidth: 0, padding: '0 20px' }}>
              <div style={{ textAlign: 'left' }}><Label>Load</Label></div>
              <LoadGauges
                extAcwr={metrics?.externalAcwr ?? null}
                intAcwr={metrics?.internalAcwr ?? null}
                divergence={metrics?.normalizedDivergence ?? null}
              />
            </div>

          </div>
        </div>

        {/* ── 3. Race Readiness ── */}
        <div className="t-card" style={{ marginBottom: '16px' }}>
          <RaceReadinessCard readiness={raceReadiness} dark={true} />
        </div>

        {/* ── 4. Week Context ── */}
        <div className="t-card" style={{ ...CARD_STYLE, marginBottom: '24px' }}>
          <CardHeader label="Week Context" title={context?.stage_name ? `PHASE: ${context.stage_name}` : undefined} />
          <div style={{ padding: '0.75rem 1rem' }}>
            {context && context.total_sessions > 0 && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '18px' }}>
                <div style={{ display: 'flex', gap: '3px' }}>
                  {Array.from({ length: context.total_sessions }).map((_, i) => (
                    <div key={i} style={{
                      width: '18px', height: '4px', borderRadius: '2px',
                      background: i < context.sessions_completed ? SAGE : 'rgba(125,156,184,0.22)',
                    }} />
                  ))}
                </div>
                <span style={{ fontSize: '0.75rem', color: MUTED, fontFamily: FONT }}>
                  {context.sessions_completed}/{context.total_sessions} sessions
                </span>
              </div>
            )}
            <div>
              <Label>Weekly Schedule</Label>
              {(() => {
                const milesMap = Object.fromEntries((context?.week_days ?? []).map(d => [d.date, d]));
                const totalMiles    = context?.week_total_miles   ?? 0;
                const totalVert     = context?.week_total_vert    ?? 0;
                const plannedMiles  = context?.planned_week_miles ?? 0;
                return (
                  <div style={{ display: 'flex', gap: '4px', marginTop: '10px', alignItems: 'stretch' }}>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: '4px', flex: 1 }}>
                      {weekDates.map(({ iso, abbrev }) => (
                        <DayCell
                          key={iso} abbrev={abbrev} isToday={iso === todayDate}
                          session={getSession(iso)}
                          miles={milesMap[iso]?.miles}
                          isActual={milesMap[iso]?.is_actual ?? true}
                        />
                      ))}
                    </div>
                    {/* Weekly totals */}
                    <div style={{ width: '1px', background: 'rgba(125,156,184,0.15)', margin: '0 8px', alignSelf: 'stretch' }} />
                    <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: '4px', minWidth: '52px' }}>
                      <div style={{ fontSize: '0.75rem', color: MUTED, fontFamily: FONT, textTransform: 'uppercase', letterSpacing: '0.06em' }}>Week</div>
                      <div style={{ fontSize: '1.05rem', fontWeight: 700, color: TEXT, fontFamily: FONT, whiteSpace: 'nowrap' }}>
                        {totalMiles > 0 ? totalMiles.toFixed(1) : '0'}
                        <span style={{ fontSize: '0.78rem', fontWeight: 400, color: MUTED }}> mi</span>
                      </div>
                      {plannedMiles > 0 && (
                        <div style={{ fontSize: '0.78rem', color: MUTED, fontFamily: FONT, whiteSpace: 'nowrap', fontStyle: 'italic' }}>
                          {plannedMiles.toFixed(0)} planned
                        </div>
                      )}
                      {totalVert > 0 && (
                        <div style={{ fontSize: '0.82rem', color: MUTED, fontFamily: FONT, whiteSpace: 'nowrap' }}>
                          {Math.round(totalVert).toLocaleString()} ft
                        </div>
                      )}
                    </div>
                  </div>
                );
              })()}
              {programLoading && (
                <p style={{ margin: '12px 0 0', color: MUTED, fontSize: '0.8rem', fontStyle: 'italic', fontFamily: FONT }}>
                  Loading weekly plan...
                </p>
              )}
              {!programLoading && !program && (
                <p style={{ margin: '12px 0 0', color: MUTED, fontSize: '0.8rem', fontStyle: 'italic', fontFamily: FONT }}>
                  No weekly program. Visit the Coach tab to generate one.
                </p>
              )}
            </div>
          </div>
        </div>

        {/* ── Nav ── */}
        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          <button onClick={() => onNavigateToTab('coach')} style={{ background: BLUE, color: 'white', border: 'none', borderRadius: '4px', padding: '6px 16px', fontSize: '0.8rem', fontWeight: 600, cursor: 'pointer', fontFamily: FONT }}>
            Open Coach
          </button>
          <button onClick={() => onNavigateToTab('journal')} style={{ background: 'white', color: '#6b7280', border: '1px solid #dee2e6', borderRadius: '4px', padding: '6px 16px', fontSize: '0.8rem', fontWeight: 600, cursor: 'pointer', fontFamily: FONT }}>
            View Journal
          </button>
        </div>

      </div>
    </div>
  );
};

export default TodayPage;
