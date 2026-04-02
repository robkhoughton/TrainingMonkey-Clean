import React, { useState, useEffect } from 'react';

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
  readiness_state: 'GREEN' | 'AMBER' | 'RED' | null;
  readiness_flags: Record<string, boolean>;
  readiness_narrative: string | null;
  hrv_value: number | null;
  hrv_source: string | null;
  hrv_baseline_30d: number | null;
  resting_hr: number | null;
  rhr_baseline_7d: number | null;
  sleep_duration_secs: number | null;
  sleep_score: number | null;
  hrv_28d_low: number | null; hrv_28d_high: number | null;
  rhr_28d_low: number | null; rhr_28d_high: number | null;
  sleep_28d_low: number | null; sleep_28d_high: number | null;
}

interface TrainingMetrics {
  externalAcwr: number;
  internalAcwr: number;
  sevenDayAvgLoad: number;
  normalizedDivergence: number;
  injuryRiskScore: number;
  injuryRiskLabel: string;
}

// Matches the actual /api/journal response shape
interface JournalEntry {
  date: string;
  is_today: boolean;
  recommendation_target_date: string | null;
  todays_decision: string;
  observations: {
    pain_percentage: number | null;
    morning_soreness: number | null;
    energy_level: number | null;
    rpe_score: number | null;
    notes: string;
  };
}

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
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function todayIso(): string { return new Date().toISOString().slice(0, 10); }

function formatDateLong(): string {
  return new Date().toLocaleDateString('en-US', {
    weekday: 'long', month: 'long', day: 'numeric', year: 'numeric',
  });
}

function getWeekDates(): Array<{ iso: string; abbrev: string }> {
  const DAY_ABBREVS = ['S', 'M', 'T', 'W', 'Th', 'F', 'S'];
  const today = new Date();
  const sunday = new Date(today);
  sunday.setDate(today.getDate() - today.getDay());
  return Array.from({ length: 7 }, (_, i) => {
    const d = new Date(sunday);
    d.setDate(sunday.getDate() + i);
    return { iso: d.toISOString().slice(0, 10), abbrev: DAY_ABBREVS[i] };
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

function norm(val: number | null, lo: number | null, hi: number | null, higherBetter = true): number | null {
  if (val === null || lo === null || hi === null || hi === lo) return null;
  const c = Math.max(0, Math.min(1, (val - lo) / (hi - lo)));
  return higherBetter ? c : 1 - c;
}

function scoreColor(s: number | null): string {
  if (s === null) return MUTED;
  if (s >= 0.55) return GREEN;
  if (s >= 0.30) return AMBER;
  return RED_C;
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
    fontSize: '0.65rem', fontWeight: 600, letterSpacing: '0.12em',
    textTransform: 'uppercase', color: MUTED, fontFamily: FONT, marginBottom: '6px',
  }}>
    {children}
  </div>
);

const CardHeader: React.FC<{ label: string; title?: string }> = ({ label, title }) => (
  <div style={{
    background: DATA_HEADER_BG, padding: '10px 20px',
    borderBottom: '1px solid rgba(125,156,184,0.12)',
  }}>
    <Label>{label}</Label>
    {title && <div style={{ fontSize: '0.9rem', fontWeight: 600, color: TEXT, fontFamily: FONT }}>{title}</div>}
  </div>
);

// ─── RecoveryDonut ─────────────────────────────────────────────────────────────
// 240° gauge arc — composite of HRV+RHR+sleep vs 28-day personal range.

interface RecoveryProps {
  hrv_value: number | null; resting_hr: number | null; sleep_duration_secs: number | null;
  hrv_28d_low: number | null; hrv_28d_high: number | null;
  rhr_28d_low: number | null; rhr_28d_high: number | null;
  sleep_28d_low: number | null; sleep_28d_high: number | null;
  sleep_score: number | null;
  hrv_baseline_30d: number | null; rhr_baseline_7d: number | null;
  hasWatchData: boolean;
}

const RecoveryDonut: React.FC<RecoveryProps> = (p) => {
  const hS = norm(p.hrv_value, p.hrv_28d_low, p.hrv_28d_high, true);
  const rS = norm(p.resting_hr, p.rhr_28d_low, p.rhr_28d_high, false);
  const sS = norm(p.sleep_duration_secs, p.sleep_28d_low, p.sleep_28d_high, true);
  const scores = [hS, rS, sS].filter((v): v is number => v !== null);
  const composite = scores.length ? scores.reduce((a, b) => a + b) / scores.length : null;
  const arcColor  = composite === null ? 'rgba(125,156,184,0.25)'
    : composite >= 0.5 ? GREEN : composite >= 0.2 ? AMBER : RED_C;

  const R = 36, CX = 52, CY = 52;
  const CIRC   = 2 * Math.PI * R;
  const ARC_LEN = CIRC * (240 / 360);
  const fill    = composite !== null ? Math.max(0, composite) * ARC_LEN : 0;
  const ROT     = `rotate(150, ${CX}, ${CY})`;

  const pct      = composite !== null ? Math.round(composite * 100) : null;
  const stateWord = composite === null ? '' : composite >= 0.5 ? 'GOOD' : composite >= 0.2 ? 'LOW' : 'POOR';
  const hrsSlept  = p.sleep_duration_secs ? (p.sleep_duration_secs / 3600).toFixed(1) : null;

  const subs = [
    { lbl: 'HRV',   val: p.hrv_value   !== null ? `${Math.round(p.hrv_value)}ms`   : '—', s: hS,
      sub: p.hrv_baseline_30d ? `avg ${Math.round(p.hrv_baseline_30d)}` : undefined },
    { lbl: 'RHR',   val: p.resting_hr  !== null ? `${Math.round(p.resting_hr)}bpm` : '—', s: rS,
      sub: p.rhr_baseline_7d  ? `avg ${Math.round(p.rhr_baseline_7d)}`  : undefined },
    { lbl: 'SLEEP', val: hrsSlept               ? `${hrsSlept}h`                   : '—', s: sS,
      sub: p.sleep_score != null ? `score ${p.sleep_score}` : undefined },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '10px' }}>
      <svg width="104" height="90" viewBox="0 0 104 90">
        {/* Track */}
        <circle cx={CX} cy={CY} r={R} fill="none"
          stroke="rgba(125,156,184,0.14)" strokeWidth="6"
          strokeDasharray={`${ARC_LEN} ${CIRC - ARC_LEN}`} strokeLinecap="round"
          transform={ROT} />
        {/* Fill */}
        {composite !== null && (
          <circle cx={CX} cy={CY} r={R} fill="none"
            stroke={arcColor} strokeWidth="6"
            strokeDasharray={`${fill} ${CIRC - fill}`} strokeLinecap="round"
            transform={ROT} style={{ transition: 'stroke-dasharray 0.7s ease' }} />
        )}
        {/* Center */}
        {p.hasWatchData ? (
          <>
            <text x={CX} y={CY + 5} textAnchor="middle" fill={arcColor} fontSize="17" fontWeight="700" fontFamily={FONT}>
              {pct ?? '—'}
            </text>
            {stateWord && (
              <text x={CX} y={CY + 17} textAnchor="middle" fill={MUTED} fontSize="6.5" fontFamily={FONT} letterSpacing="1">
                {stateWord}
              </text>
            )}
          </>
        ) : (
          <text x={CX} y={CY + 4} textAnchor="middle" fill={MUTED} fontSize="7.5" fontFamily={FONT}>
            No watch data
          </text>
        )}
      </svg>

      {/* Sub-values */}
      <div style={{ display: 'flex', gap: '12px' }}>
        {subs.map(({ lbl, val, s, sub }) => (
          <div key={lbl} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '2px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <div style={{ width: '5px', height: '5px', borderRadius: '50%', background: scoreColor(s), flexShrink: 0 }} />
              <span style={{ fontSize: '0.72rem', fontWeight: 700, color: p.hasWatchData ? TEXT : MUTED, fontFamily: FONT }}>{val}</span>
            </div>
            <span style={{ fontSize: '0.5rem', color: MUTED, textTransform: 'uppercase', letterSpacing: '0.08em', fontFamily: FONT }}>{lbl}</span>
            {sub && <span style={{ fontSize: '0.5rem', color: MUTED, fontFamily: FONT }}>{sub}</span>}
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
  statusLabel: string;
  statusColor: string;
  // gauge config
  min: number; max: number;
  zones: Array<{ from: number; to: number; color: string; opacity: number }>;
}

const ZonedGauge: React.FC<ZonedGaugeProps> = ({ label, value, valueLabel, statusLabel, statusColor, min, max, zones }) => {
  const W = 160, H = 12;
  const toX = (v: number) => Math.max(0, Math.min(W, ((v - min) / (max - min)) * W));
  const markerX = value !== null ? toX(value) : null;

  return (
    <div style={{ marginBottom: '14px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '4px' }}>
        <span style={{ fontSize: '0.65rem', color: MUTED, fontFamily: FONT, letterSpacing: '0.06em', textTransform: 'uppercase' }}>
          {label}
        </span>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px' }}>
          <span style={{ fontSize: '0.85rem', fontWeight: 700, color: TEXT, fontFamily: FONT }}>{valueLabel}</span>
          <span style={{ fontSize: '0.6rem', fontWeight: 700, color: statusColor, textTransform: 'uppercase', letterSpacing: '0.06em', fontFamily: FONT }}>
            {statusLabel}
          </span>
        </div>
      </div>
      <svg width={W} height={H + 8} viewBox={`0 0 ${W} ${H + 8}`} style={{ display: 'block' }}>
        {/* Zone bands */}
        {zones.map((z, i) => (
          <rect key={i}
            x={toX(z.from)} y={4} width={Math.max(0, toX(z.to) - toX(z.from))} height={H}
            fill={z.color} opacity={z.opacity} rx="2"
          />
        ))}
        {/* Track border */}
        <rect x={0} y={4} width={W} height={H} fill="none"
          stroke="rgba(125,156,184,0.15)" strokeWidth="1" rx="2" />
        {/* Marker */}
        {markerX !== null && (
          <>
            <line x1={markerX} y1={1} x2={markerX} y2={H + 7} stroke={statusColor} strokeWidth="2" strokeLinecap="round" />
            <circle cx={markerX} cy={H / 2 + 4} r="4" fill={statusColor} />
          </>
        )}
      </svg>
    </div>
  );
};

const LoadGauges: React.FC<LoadGaugesProps> = ({ extAcwr, intAcwr, divergence }) => {
  const acwrZones = [
    { from: 0,   to: 0.8, color: MUTED,  opacity: 0.25 },
    { from: 0.8, to: 1.3, color: GREEN,  opacity: 0.30 },
    { from: 1.3, to: 1.5, color: AMBER,  opacity: 0.35 },
    { from: 1.5, to: 2.0, color: RED_C,  opacity: 0.35 },
  ];
  const divZones = [
    { from: -0.5, to: -0.35, color: RED_C,  opacity: 0.35 },
    { from: -0.35, to: -0.15, color: AMBER, opacity: 0.30 },
    { from: -0.15, to:  0.15, color: GREEN, opacity: 0.30 },
    { from:  0.15, to:  0.35, color: AMBER, opacity: 0.30 },
    { from:  0.35, to:  0.5,  color: RED_C,  opacity: 0.35 },
  ];

  const ea = acwrStatus(extAcwr ?? 0);
  const ia = acwrStatus(intAcwr ?? 0);
  const ds = divStatus(divergence ?? 0);

  return (
    <div style={{ width: '100%' }}>
      <ZonedGauge
        label="Ext ACWR" value={extAcwr} min={0} max={2.0} zones={acwrZones}
        valueLabel={extAcwr != null ? extAcwr.toFixed(2) : '—'}
        statusLabel={ea.label} statusColor={ea.color}
      />
      <ZonedGauge
        label="Int ACWR" value={intAcwr} min={0} max={2.0} zones={acwrZones}
        valueLabel={intAcwr != null ? intAcwr.toFixed(2) : '—'}
        statusLabel={ia.label} statusColor={ia.color}
      />
      <ZonedGauge
        label="Divergence" value={divergence} min={-0.5} max={0.5} zones={divZones}
        valueLabel={divergence != null ? divergence.toFixed(3) : '—'}
        statusLabel={ds.label} statusColor={ds.color}
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

// ─── DayCell ───────────────────────────────────────────────────────────────────

interface DayCellProps { abbrev: string; isToday: boolean; session: DailyWorkout | null; }

const DayCell: React.FC<DayCellProps> = ({ abbrev, isToday, session }) => {
  const abbrevType = session ? workoutAbbrev(session.workout_type) : '—';
  const isOff = abbrevType === 'OFF' || !session;
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px', opacity: isOff ? 0.45 : 1 }}>
      <div style={{
        width: '26px', height: '26px', borderRadius: '3px',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        background: isToday ? '#FF5722' : 'transparent',
        border: isToday ? 'none' : '1px solid rgba(125,156,184,0.2)',
        fontSize: '0.65rem', fontWeight: isToday ? 700 : 500,
        color: isToday ? 'white' : MUTED, fontFamily: FONT,
      }}>
        {abbrev}
      </div>
      <div style={{
        width: '26px', height: '20px', borderRadius: '3px',
        background: isOff ? 'transparent' : 'rgba(125,156,184,0.1)',
        border: `1px solid ${isOff ? 'rgba(125,156,184,0.08)' : 'rgba(125,156,184,0.28)'}`,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: '0.58rem', fontWeight: 700, color: TEXT, fontFamily: FONT,
      }}>
        {abbrevType}
      </div>
      {session?.duration_estimate && (
        <div style={{ fontSize: '0.5rem', color: MUTED, fontFamily: FONT, textAlign: 'center', lineHeight: 1.2, maxWidth: '30px' }}>
          {session.duration_estimate.replace('minutes','min').replace('minute','min').replace('hours','hr').replace('hour','hr')}
        </div>
      )}
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
  const [rec,            setRec]            = useState<string | null>(null);
  const [journalEntries, setJournalEntries] = useState<JournalEntry[]>([]);
  const [loading,        setLoading]        = useState(true);
  const [showWhy,        setShowWhy]        = useState(false);

  useEffect(() => {
    Promise.all([
      fetch('/api/readiness',                    { credentials: 'include' }).then(r => r.ok ? r.json() : null),
      fetch(`/api/training-data?t=${Date.now()}`, { credentials: 'include' }).then(r => r.ok ? r.json() : null),
      fetch('/api/coach/weekly-program',          { credentials: 'include' }).then(r => r.ok ? r.json() : null),
      fetch('/api/journal/context',               { credentials: 'include' }).then(r => r.ok ? r.json() : null),
      fetch('/api/journal',                       { credentials: 'include' }).then(r => r.ok ? r.json() : null),
    ]).then(([well, training, prog, ctx, recData]) => {
      if (well) setWellness(well);
      if (training?.data?.length) {
        const rows = [...training.data].sort((a: any, b: any) => b.date.localeCompare(a.date));
        const r = rows[0];
        setMetrics({
          externalAcwr:         r.acute_chronic_ratio       || 0,
          internalAcwr:         r.trimp_acute_chronic_ratio || 0,
          sevenDayAvgLoad:      r.seven_day_avg_load        || 0,
          normalizedDivergence: r.normalized_divergence     || 0,
          injuryRiskScore:      r.injury_risk_score         || 0,
          injuryRiskLabel:      r.injury_risk_label         || 'LOW',
        });
      }
      if (prog?.program)         setProgram(prog.program);
      if (ctx)                   setContext(ctx);
      if (recData?.data?.length) {
        const entries: JournalEntry[] = recData.data;
        setJournalEntries(entries);

        // Find the recommendation targeted for today specifically.
        // After autopsy, the rec for tomorrow is stored in yesterday's entry
        // with recommendation_target_date = tomorrow.
        const todayStr = todayIso();
        const targetedForToday = entries.find(e =>
          e.recommendation_target_date === todayStr &&
          e.todays_decision &&
          !e.todays_decision.includes('No recommendation available')
        );
        const todayEntryRec = entries.find(e =>
          e.is_today &&
          e.todays_decision &&
          !e.todays_decision.includes('No recommendation available')
        );
        const r = targetedForToday?.todays_decision || todayEntryRec?.todays_decision || null;
        if (r) setRec(r);
      }
      setLoading(false);
    }).catch(() => setLoading(false));
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
  const todaySession = getSession(todayDate);

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

  const acwr  = acwrStatus(metrics?.externalAcwr ?? 0);
  const iacwr = acwrStatus(metrics?.internalAcwr ?? 0);
  const div   = divStatus(metrics?.normalizedDivergence ?? 0);

  const activeFlags = wellness?.readiness_flags
    ? Object.entries(wellness.readiness_flags)
        .filter(([, v]) => v)
        .map(([k]) => ({
          hrv_suppressed: 'HRV suppressed', rhr_elevated: 'RHR elevated',
          sleep_deficit: 'Sleep deficit', sleep_poor_score: 'Poor sleep score',
          high_soreness: 'High soreness',
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
          <div style={{ fontSize: '0.8rem', color: MUTED, marginTop: '4px', fontFamily: FONT }}>{formatDateLong()}</div>
        </div>

        {/* ── 1. Rx card (two-column prose) ── */}
        <div className="t-card" style={{ ...CARD_STYLE, marginBottom: '16px' }}>
          <CardHeader label="Training Prescription" />
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
                           fontSize: '0.92rem', lineHeight: '1.7', color: TEXT, fontFamily: FONT }}
                >
                  {rec.split(/\n+/).filter(l => l.trim()).length > 1
                    ? rec.split(/\n+/).filter(l => l.trim()).map((para, i) => (
                        <p key={i} style={{ margin: '0 0 10px' }}>{para}</p>
                      ))
                    : <p style={{ margin: 0 }}>{rec}</p>
                  }
                </div>

                {/* Why this Rx? */}
                <div style={{ marginTop: '14px', paddingTop: '12px', borderTop: '1px solid rgba(125,156,184,0.1)' }}>
                  <button
                    onClick={() => setShowWhy(v => !v)}
                    style={{
                      background: 'none', border: 'none', cursor: 'pointer',
                      color: MUTED, fontSize: '0.78rem', fontFamily: FONT,
                      padding: 0, display: 'flex', alignItems: 'center', gap: '5px',
                    }}
                  >
                    <span style={{ fontSize: '0.65rem' }}>{showWhy ? '▾' : '▸'}</span>
                    Why this recommendation?
                  </button>

                  {showWhy && (
                    <div style={{
                      marginTop: '12px', padding: '14px 16px',
                      background: 'rgba(27,46,75,0.6)',
                      border: '1px solid rgba(125,156,184,0.15)', borderRadius: '4px',
                    }}>
                      <div style={{ display: 'flex', gap: '32px', flexWrap: 'wrap' }}>
                        <div>
                          <Label>Load signals</Label>
                          <div style={{ fontSize: '0.8rem', color: TEXT, fontFamily: FONT, lineHeight: '1.9' }}>
                            <div>Ext ACWR: <strong style={{ color: acwr.color }}>{metrics?.externalAcwr.toFixed(2) ?? '—'}</strong> — {acwr.label}</div>
                            <div>Int ACWR: <strong style={{ color: iacwr.color }}>{metrics?.internalAcwr.toFixed(2) ?? '—'}</strong> — {iacwr.label}</div>
                            <div>Divergence: <strong style={{ color: div.color }}>{metrics?.normalizedDivergence.toFixed(3) ?? '—'}</strong> — {div.label}</div>
                          </div>
                        </div>
                        {(activeFlags.length > 0 || wellness?.readiness_narrative) && (
                          <div style={{ maxWidth: '320px' }}>
                            <Label>Readiness signals</Label>
                            {wellness?.readiness_narrative && (
                              <p style={{ fontSize: '0.8rem', color: TEXT, fontFamily: FONT, margin: '0 0 8px', lineHeight: '1.6' }}>
                                {wellness.readiness_narrative}
                              </p>
                            )}
                            {activeFlags.length > 0 && (
                              <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                                {activeFlags.map(f => (
                                  <span key={f} style={{
                                    fontSize: '0.62rem', color: AMBER,
                                    border: '1px solid rgba(217,119,6,0.3)',
                                    borderRadius: '3px', padding: '2px 7px', fontFamily: FONT,
                                  }}>{f}</span>
                                ))}
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
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

            {/* Recovery */}
            <div style={{ flex: 1, minWidth: 0, paddingRight: '20px', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
              <div style={{ alignSelf: 'flex-start', marginBottom: '10px' }}><Label>Recovery</Label></div>
              <RecoveryDonut
                hrv_value={wellness?.hrv_value ?? null}
                resting_hr={wellness?.resting_hr ?? null}
                sleep_duration_secs={wellness?.sleep_duration_secs ?? null}
                hrv_28d_low={wellness?.hrv_28d_low ?? null}   hrv_28d_high={wellness?.hrv_28d_high ?? null}
                rhr_28d_low={wellness?.rhr_28d_low ?? null}   rhr_28d_high={wellness?.rhr_28d_high ?? null}
                sleep_28d_low={wellness?.sleep_28d_low ?? null} sleep_28d_high={wellness?.sleep_28d_high ?? null}
                sleep_score={wellness?.sleep_score ?? null}
                hrv_baseline_30d={wellness?.hrv_baseline_30d ?? null}
                rhr_baseline_7d={wellness?.rhr_baseline_7d ?? null}
                hasWatchData={hasWatchData}
              />
            </div>

            <div className="sig-div" style={dividerStyle} />

            {/* Load */}
            <div style={{ flex: 1, minWidth: 0, padding: '0 20px' }}>
              <Label>Load</Label>
              <LoadGauges
                extAcwr={metrics?.externalAcwr ?? null}
                intAcwr={metrics?.internalAcwr ?? null}
                divergence={metrics?.normalizedDivergence ?? null}
              />
              {metrics && (
                <div style={{ fontSize: '0.7rem', color: MUTED, fontFamily: FONT, marginTop: '4px' }}>
                  7-day avg load: <strong style={{ color: TEXT }}>{metrics.sevenDayAvgLoad.toFixed(0)}</strong>
                  &nbsp;·&nbsp;
                  Injury risk: <strong style={{
                    color: metrics.injuryRiskScore >= 60 ? RED_C : metrics.injuryRiskScore >= 30 ? AMBER : GREEN
                  }}>{metrics.injuryRiskLabel}</strong>
                </div>
              )}
            </div>

            <div className="sig-div" style={dividerStyle} />

            {/* Injury Trend */}
            <div style={{ flex: 1, minWidth: 0, paddingLeft: '20px', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
              <div style={{ alignSelf: 'flex-start', marginBottom: '10px' }}><Label>Injury Trend · 7 days</Label></div>
              <InjuryTrend entries={journalEntries} />
            </div>

          </div>
        </div>

        {/* ── 3. Week context ── */}
        <div className="t-card" style={{ ...CARD_STYLE, marginBottom: '24px' }}>
          <CardHeader label="Week Context" title={context?.stage_name || undefined} />
          <div style={{ padding: '16px 20px' }}>
            {(context?.race_name || (context && context.total_sessions > 0) || todaySession) && (
              <div style={{ display: 'flex', gap: '24px', flexWrap: 'wrap', marginBottom: '18px' }}>
                {context?.race_name && (
                  <div>
                    <Label>Race Goal</Label>
                    <div style={{ fontSize: '0.85rem', fontWeight: 600, color: TEXT, fontFamily: FONT }}>
                      {context.race_name}
                      {context.weeks_to_race != null && (
                        <span style={{ fontWeight: 400, color: MUTED, marginLeft: '8px' }}>{context.weeks_to_race}w away</span>
                      )}
                    </div>
                  </div>
                )}
                {context && context.total_sessions > 0 && (
                  <div>
                    <Label>This Week</Label>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '2px' }}>
                      <div style={{ display: 'flex', gap: '3px' }}>
                        {Array.from({ length: context.total_sessions }).map((_, i) => (
                          <div key={i} style={{
                            width: '18px', height: '4px', borderRadius: '2px',
                            background: i < context.sessions_completed ? SAGE : 'rgba(125,156,184,0.22)',
                          }} />
                        ))}
                      </div>
                      <span style={{ fontSize: '0.75rem', color: MUTED, fontFamily: FONT }}>
                        {context.sessions_completed}/{context.total_sessions}
                      </span>
                    </div>
                  </div>
                )}
                {todaySession && (
                  <div>
                    <Label>Today</Label>
                    <div style={{ fontSize: '0.85rem', fontWeight: 600, color: TEXT, fontFamily: FONT }}>{todaySession.workout_type}</div>
                    {todaySession.intensity && <div style={{ fontSize: '0.75rem', color: MUTED, marginTop: '2px', fontFamily: FONT }}>{todaySession.intensity}</div>}
                  </div>
                )}
              </div>
            )}
            <div>
              <Label>Weekly Schedule</Label>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: '4px', marginTop: '10px' }}>
                {weekDates.map(({ iso, abbrev }) => (
                  <DayCell key={iso} abbrev={abbrev} isToday={iso === todayDate} session={getSession(iso)} />
                ))}
              </div>
              {!loading && !program && (
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
