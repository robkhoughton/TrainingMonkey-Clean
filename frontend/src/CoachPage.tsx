import React, { useState, useEffect } from 'react';
import styles from './TrainingLoadDashboard.module.css';
import { usePagePerformanceMonitoring, useComponentPerformanceMonitoring } from './usePerformanceMonitoring';
import WeeklyProgramDisplay from './WeeklyProgramDisplay';
import TimelineVisualization from './TimelineVisualization';
import RaceHistoryPage from './RaceHistoryPage';
import SeasonPage from './SeasonPage';
import YTMSpinner from './YTMSpinner';

// ============================================================================
// STRATEGIC CONTEXT DISPLAY COMPONENT (Collapsible Sections) — REMOVED
// strategic_context fields were display-only and consumed ~600 words of LLM
// output budget with no downstream use. week_summary covers the display need.
// ============================================================================

const StrategicContextDisplay: React.FC<{ strategicContext: Record<string, string> }> = ({ strategicContext }) => {
  const [expandedSection, setExpandedSection] = useState<string | null>(null);

  // Debug: log the strategic context to see what we're receiving
  console.log('Strategic Context Data:', strategicContext);

  const toggleSection = (section: string) => {
    setExpandedSection(expandedSection === section ? null : section);
  };

  const CollapsibleSection = ({ 
    id, 
    title, 
    emoji, 
    content, 
    bgColor, 
    borderColor, 
    textColor 
  }: { 
    id: string; 
    title: string; 
    emoji: string; 
    content: string; 
    bgColor: string; 
    borderColor: string; 
    textColor: string;
  }) => {
    const isExpanded = expandedSection === id;

    return (
      <div style={{
        marginBottom: '0.75rem',
        border: `1px solid ${borderColor}`,
        borderRadius: '8px',
        overflow: 'hidden'
      }}>
        <button
          onClick={() => toggleSection(id)}
          style={{
            width: '100%',
            padding: '1rem',
            backgroundColor: bgColor,
            border: 'none',
            cursor: 'pointer',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            textAlign: 'left'
          }}
        >
          <h3 style={{
            fontSize: '16px',
            fontWeight: '600',
            color: textColor,
            margin: 0,
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem'
          }}>
            {emoji} {title}
          </h3>
          <span style={{ fontSize: '18px', color: textColor }}>
            {isExpanded ? '▼' : '▶'}
          </span>
        </button>
        {isExpanded && (
          <div style={{
            padding: '1rem',
            backgroundColor: 'white',
            borderTop: `1px solid ${borderColor}`
          }}>
            <p style={{
              margin: 0,
              lineHeight: '1.7',
              color: '#374151',
              fontSize: '15px',
              whiteSpace: 'pre-wrap',
              textAlign: 'left'
            }}>
              {content}
            </p>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className={styles.card} style={{ marginBottom: '0.75rem', padding: '1rem', maxWidth: '1200px', margin: '0 auto 0.75rem auto' }}>
      <h2 style={{
        fontSize: '20px',
        fontWeight: '700',
        marginBottom: '1rem',
        color: '#1e293b',
        borderBottom: '2px solid #e1e8ed',
        paddingBottom: '0.5rem',
        textAlign: 'left'
      }}>
        Strategic Analysis & Context
      </h2>

      <CollapsibleSection
        id="race"
        title="Race Context & Periodization"
        emoji=""
        content={strategicContext.race_context_periodization}
        bgColor="#f0f9ff"
        borderColor="#3b82f6"
        textColor="#1e40af"
      />

      <CollapsibleSection
        id="load"
        title="Load Management & Pattern Analysis"
        emoji=""
        content={strategicContext.load_management_pattern_analysis}
        bgColor="#fef3c7"
        borderColor="#f59e0b"
        textColor="#92400e"
      />

      <CollapsibleSection
        id="rationale"
        title="Strategic Rationale & Training Science"
        emoji=""
        content={strategicContext.strategic_rationale}
        bgColor="#f0fdf4"
        borderColor="#10b981"
        textColor="#065f46"
      />

      {/* Integration Hint */}
      <div style={{
        marginTop: '1rem',
        padding: '0.75rem',
        backgroundColor: '#f8f9fa',
        borderRadius: '6px',
        fontSize: '13px',
        color: '#6b7280',
        fontStyle: 'italic',
        textAlign: 'center'
      }}>
        Visit the <a href="/dashboard?tab=journal" style={{ color: '#007bff', textDecoration: 'underline', fontWeight: '600' }}>Journal</a> page daily for today's specific guidance and post-workout analysis
      </div>
    </div>
  );
};

// ============================================================================
// TYPESCRIPT INTERFACES
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

export interface RaceReadiness {
  status: 'already_ready' | 'on_track' | 'not_achievable';
  message: string;
  race_name: string;
  race_date: string;
  race_total_load: number;
  current_7day_load: number;
  peak_7day_load: number;
  block_start: string;
  weeks_needed: number;
  weeks_available: number;
  acwr_ceiling_used: number;
  model_calibrated: boolean;
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
interface RaceHistory {
  id: number;
  race_date: string;
  race_name: string;
  distance_miles: number;
  finish_time_minutes: number;
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
interface TrainingSchedule {
  schedule: {
    total_hours_per_week?: number;
    available_days?: string[];
    time_blocks?: { [key: string]: string[] };
    constraints?: string;
  } | null;
  include_strength: boolean;
  strength_hours: number;
  include_mobility: boolean;
  mobility_hours: number;
  include_cross_training: boolean;
  cross_training_type: string | null;
  cross_training_hours: number;
}

export interface AthleteModel {
  avg_lifetime_alignment: number | null;
  recent_alignment_trend: string | null;
  total_autopsies: number;
  last_autopsy_date: string | null;
  typical_divergence_low: number | null;
  divergence_injury_threshold: number | null;
  journal_count: number;
  activity_count: number;
  journal_coverage_pct: number;
  model_confidence?: {
    composite: number;
    components: {
      athlete_profile:    { score: number; missing: string[] };
      hr_calibration:     { score: number; max_hr: boolean; resting_hr: boolean };
      coaching_prefs:     { score: number };
      season_plan:        { score: number; has_name_date: boolean; has_distance: boolean };
      weekly_schedule:    { score: number };
      activity_history:   { score: number; recent_count: number };
      journal_power:      { score: number; avg_power: number; coverage_pct: number; journal_count: number; activity_count: number; field_coverage?: Record<string, number> };
      aerobic_assessment: { score: number; count: number };
    };
  };
}

interface DailyWorkout {
  day: string;
  date: string;
  workout_type: string;
  description: string;
  duration_estimate: string;
  intensity: string;
  key_focus: string;
  terrain_notes?: string;
}

interface WeeklyProgram {
  week_start_date: string;
  week_summary: string;
  predicted_metrics: {
    acwr_estimate: number;
    divergence_estimate: number;
    total_weekly_miles: number;
  };
  daily_program: DailyWorkout[];
  key_workouts_this_week: string[];
  nutrition_reminder?: string;
  injury_prevention_note?: string;
  from_cache?: boolean;
}

interface TrainingSchedule {
  schedule: {
    total_hours_per_week?: number;
    available_days?: string[];
    long_run_days?: string[];
    constraints?: string | Array<{ description: string }>;
  } | null;
  include_strength: boolean;
  strength_hours: number;
  include_mobility: boolean;
  mobility_hours: number;
  cross_training_disciplines?: Array<{
    discipline: string;
    enabled: boolean;
    allocation_type: 'hours' | 'percentage';
    allocation_value: number;
  }>;
  include_cross_training?: boolean;
  cross_training_type?: string | null;
  cross_training_hours?: number;
}

interface TrainingStage {
  stage: string;
  weeks_to_race: number | null;
  race_name: string | null;
  priority?: string;
  details: string;
  timeline?: TimelineWeek[];
}

interface TimelineWeek {
  week_number: number;
  week_start: string;
  week_end: string;
  stage: string;
  is_current: boolean;
  races?: Array<{
    race_name: string;
    priority: string;
    date: string;
  }>;
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
interface RaceAnalysis {
  prs: Array<{
    distance_miles: number;
    finish_time_minutes: number;
    race_name: string;
    race_date: string;
    pace_per_mile: number;
  }>;
  trend: string;
  trend_description: string;
  base_fitness: string;
  total_races: number;
}

// ============================================================================
// RACE READINESS CARD
// ============================================================================

export const RaceReadinessCard: React.FC<{ readiness: RaceReadiness | null; dark?: boolean }> = ({ readiness, dark = false }) => {
  const statusConfig = {
    already_ready: { label: 'Race Ready',    accent: '#7D9CB8', light: '#E6F0FF', text: '#1B2E4B' },
    on_track:      { label: 'On Track',      accent: '#16a34a', light: '#f0fdf4', text: '#14532d' },
    not_achievable:{ label: 'Load Gap',      accent: '#dc2626', light: '#fef2f2', text: '#7f1d1d' },
  };
  const bodyBg    = dark ? '#243856' : 'white';
  const bodyText  = dark ? '#E6F0FF' : '#1F2937';
  const bodyMuted = dark ? '#7D9CB8' : '#6b7280';
  const bodyFaint = dark ? '#7D9CB8' : '#9ca3af';
  const tileBg    = dark ? '#1B2E4B' : 'white';
  const tileDiv   = dark ? 'rgba(125,156,184,0.15)' : '#e5e7eb';
  const peakColor = dark ? '#E6F0FF' : '#1B2E4B';
  const trackBg   = dark ? 'linear-gradient(180deg, #1B2E4B 0%, #152440 100%)' : 'linear-gradient(180deg, #f0f3f7 0%, #e5e9ef 100%)';
  const trackBorder = dark ? '1px solid rgba(125,156,184,0.20)' : '1px solid #d1d9e0';
  const tickColor = dark ? 'rgba(125,156,184,0.40)' : '#c5cdd6';

  const cfg = readiness ? statusConfig[readiness.status] : null;
  const fillPct = readiness
    ? Math.min(100, Math.round((readiness.current_7day_load / readiness.race_total_load) * 100))
    : 0;

  return (
    <div style={{
      width: '100%',
      borderRadius: '8px',
      overflow: 'hidden',
      boxShadow: '0 2px 4px rgba(0,0,0,0.10)',
    }}>
      {/* Header */}
      <div style={{
        background: 'linear-gradient(90deg, #1B2E4B 0%, #2d4a6e 100%)',
        padding: '0.5rem 1rem',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
      }}>
        <div>
          <div style={{ fontSize: '13px', letterSpacing: '0.15em', fontWeight: '700', color: '#7D9CB8', textTransform: 'uppercase', textAlign: 'left' }}>
            Race Readiness
          </div>
          <div style={{ fontSize: '16px', fontWeight: '700', color: '#ffffff', marginTop: '1px', textAlign: 'left' }}>
            {readiness ? readiness.race_name : 'A Race Projection'}
          </div>
        </div>
        {cfg && (
          <div style={{
            display: 'flex', alignItems: 'center', gap: '6px',
            padding: '4px 10px', borderRadius: '20px',
            backgroundColor: `${cfg.accent}22`,
            border: `1px solid ${cfg.accent}66`,
          }}>
            <div style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: cfg.accent }} />
            <span style={{ fontSize: '13px', fontWeight: '700', letterSpacing: '0.08em', color: cfg.accent, textTransform: 'uppercase' }}>
              {cfg.label}
            </span>
          </div>
        )}
      </div>

      {/* Body */}
      <div style={{ backgroundColor: bodyBg, padding: '0.75rem 1rem' }}>
        {!readiness ? (
          <p style={{ margin: 0, fontSize: '14px', color: bodyMuted, textAlign: 'left', lineHeight: '1.6' }}>
            Add distance to your A race goal to see your readiness projection.
          </p>
        ) : (
          <>
            {/* Verdict message */}
            <p style={{
              margin: '0 0 0.75rem 0',
              fontSize: '14px',
              color: bodyText,
              lineHeight: '1.65',
              textAlign: 'left',
              borderLeft: `3px solid ${cfg!.accent}`,
              paddingLeft: '0.75rem',
            }}>
              {readiness.message}
            </p>

            {/* Peak Week bar */}
            {(() => {
              const peakTarget = readiness.race_total_load;
              const currentMi = readiness.current_7day_load;
              const peakMi = readiness.peak_7day_load;
              const currentPct = Math.min(100, (currentMi / peakTarget) * 100);
              const peakPct = Math.min(100, (peakMi / peakTarget) * 100);
              const tickInterval = peakTarget <= 30 ? 5 : peakTarget <= 60 ? 10 : peakTarget <= 120 ? 25 : 50;
              const ticks: number[] = [];
              for (let t = 0; t <= peakTarget; t += tickInterval) ticks.push(t);
              if (ticks[ticks.length - 1] !== peakTarget) ticks.push(peakTarget);

              const TRACK_H = 10;
              const TICK_BELOW = 4;
              const PEAK_AREA_H = 20; // height reserved above track for peak marker

              return (
                <div style={{ marginBottom: '0.75rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '0.5rem' }}>
                    <span style={{ fontSize: '13px', fontWeight: '700', letterSpacing: '0.1em', color: '#6b7280', textTransform: 'uppercase' }}>
                      Peak Week
                    </span>
                    <span style={{ fontSize: '13px', color: bodyFaint, fontStyle: 'italic' }}>
                      Now: <strong style={{ color: cfg!.accent, fontStyle: 'normal' }}>{currentMi} mi</strong>
                      {peakMi > currentMi && (
                        <span style={{ marginLeft: '8px' }}>Block peak: <strong style={{ color: peakColor, fontStyle: 'normal' }}>{peakMi} mi</strong></span>
                      )}
                    </span>
                  </div>

                  {/* Peak marker area above the track */}
                  <div style={{ position: 'relative', height: `${PEAK_AREA_H}px` }}>
                    {peakMi > 0 && (
                      <div style={{
                        position: 'absolute',
                        left: `${peakPct}%`,
                        bottom: 0,
                        transform: 'translateX(-50%)',
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        gap: '1px',
                      }}>
                        <span style={{
                          fontSize: '12px',
                          fontWeight: '700',
                          color: peakColor,
                          fontVariantNumeric: 'tabular-nums',
                          whiteSpace: 'nowrap',
                          letterSpacing: '0.02em',
                        }}>
                          {peakMi} mi
                        </span>
                        {/* Inverted triangle */}
                        <div style={{
                          width: 0, height: 0,
                          borderLeft: '5px solid transparent',
                          borderRight: '5px solid transparent',
                          borderTop: `6px solid ${peakColor}`,
                        }} />
                      </div>
                    )}
                  </div>

                  {/* Track + ticks in overflow-visible wrapper */}
                  <div style={{ position: 'relative', paddingBottom: `${TICK_BELOW}px` }}>
                    <div style={{
                      position: 'relative',
                      height: `${TRACK_H}px`,
                      background: trackBg,
                      borderRadius: `${TRACK_H / 2}px`,
                      boxShadow: 'inset 0 2px 3px rgba(0,0,0,0.10), inset 0 1px 1px rgba(0,0,0,0.06)',
                      border: trackBorder,
                      overflow: 'hidden',
                    }}>
                      <div style={{
                        position: 'absolute', left: 0, top: 0, bottom: 0,
                        width: `${currentPct}%`,
                        background: `linear-gradient(90deg, ${cfg!.accent}bb 0%, ${cfg!.accent} 100%)`,
                        borderRadius: `${TRACK_H / 2}px`,
                        transition: 'width 0.7s cubic-bezier(0.4,0,0.2,1)',
                        boxShadow: 'inset 0 1px 2px rgba(255,255,255,0.25)',
                      }} />
                    </div>
                    {/* Tick stems extending below track */}
                    {ticks.slice(1, -1).map(t => {
                      const pct = (t / peakTarget) * 100;
                      return (
                        <div key={t} style={{
                          position: 'absolute',
                          left: `${pct}%`,
                          top: `${TRACK_H - 2}px`,
                          height: `${TICK_BELOW + 2}px`,
                          width: '1px',
                          backgroundColor: tickColor,
                          transform: 'translateX(-50%)',
                        }} />
                      );
                    })}
                  </div>

                  {/* Tick labels */}
                  <div style={{ position: 'relative', height: '14px', marginTop: '2px' }}>
                    {ticks.map((t, i) => {
                      const pct = (t / peakTarget) * 100;
                      const isFirst = i === 0;
                      const isLast = i === ticks.length - 1;
                      return (
                        <div key={t} style={{
                          position: 'absolute',
                          left: `${pct}%`,
                          transform: isFirst ? 'none' : isLast ? 'translateX(-100%)' : 'translateX(-50%)',
                          fontSize: '12px',
                          fontWeight: isLast ? '700' : '400',
                          color: isLast ? peakColor : bodyFaint,
                          fontVariantNumeric: 'tabular-nums',
                          whiteSpace: 'nowrap',
                          lineHeight: 1,
                        }}>
                          {t === 0 ? '0' : isLast ? `${t} mi` : `${t}`}
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })()}

            {/* Metric row */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '1px', backgroundColor: tileDiv }}>
              {[
                { label: 'WEEKS AVAILABLE', value: String(readiness.weeks_available) },
                { label: 'WEEKS TO PEAK', value: readiness.status === 'already_ready' ? '—' : String(readiness.weeks_needed) },
                { label: 'EXT ACWR CEILING', value: String(readiness.acwr_ceiling_used), sub: readiness.model_calibrated ? 'calibrated' : 'default' },
              ].map(m => (
                <div key={m.label} style={{ backgroundColor: tileBg, padding: '0.4rem 0.75rem', borderTop: `2px solid ${cfg!.accent}` }}>
                  <div style={{ fontSize: '11px', letterSpacing: '0.12em', fontWeight: '700', color: bodyMuted, textTransform: 'uppercase', marginBottom: '0.2rem', textAlign: 'left' }}>
                    {m.label}
                  </div>
                  <div style={{ fontSize: '20px', fontWeight: '700', color: bodyText, lineHeight: '1', fontVariantNumeric: 'tabular-nums', textAlign: 'left' }}>
                    {m.value}
                  </div>
                  {m.sub && (
                    <div style={{ fontSize: '11px', color: bodyFaint, marginTop: '0.15rem', textAlign: 'left' }}>{m.sub}</div>
                  )}
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
};

// ============================================================================
// WEEKLY SYNTHESIS CARD
// ============================================================================

interface WeeklySynthesisData {
  synthesis: string | null;
  week_start: string | null;
  generated_at: string | null;
  strategic_summary: string | null;
}

export const WeeklySynthesisCard: React.FC<{
  data: WeeklySynthesisData | null;
  loading?: boolean;
}> = ({ data, loading = false }) => {
  const [intentOpen, setIntentOpen] = useState(false);

  const formatWeekLabel = (iso: string | null) => {
    if (!iso) return '';
    const d = new Date(iso + 'T12:00:00');
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  const formatGeneratedAt = (iso: string | null) => {
    if (!iso) return '';
    const d = new Date(iso);
    return d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
  };

  return (
    <div style={{
      maxWidth: '1200px',
      margin: '0 auto 0.75rem auto',
      borderRadius: '8px',
      overflow: 'hidden',
      boxShadow: '0 2px 4px rgba(0,0,0,0.10)',
    }}>
      {/* Header */}
      <div style={{
        background: 'linear-gradient(90deg, #E6F0FF 0%, #7D9CB8 50%, #1B2E4B 100%)',
        padding: '0.75rem 1.25rem',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
      }}>
        <div style={{ fontSize: '10px', letterSpacing: '0.15em', fontWeight: '700', color: '#1B2E4B', textTransform: 'uppercase' }}>
          Weekly Synthesis
        </div>
        {data?.week_start && (
          <div style={{ fontSize: '11px', fontWeight: '600', color: '#1B2E4B', letterSpacing: '0.05em' }}>
            Week of {formatWeekLabel(data.week_start)}
          </div>
        )}
      </div>

      {/* Body */}
      <div style={{ backgroundColor: 'white', padding: '1.25rem' }}>
        {loading ? (
          /* Skeleton shimmer */
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <style>{`
              @keyframes ytm-shimmer {
                0%   { background-position: -400px 0; }
                100% { background-position: 400px 0; }
              }
              .ytm-skel {
                background: linear-gradient(90deg, #f0f2f5 25%, #e2e6ea 50%, #f0f2f5 75%);
                background-size: 800px 100%;
                animation: ytm-shimmer 1.4s infinite;
                border-radius: 4px;
              }
            `}</style>
            {[100, 85, 90, 60].map((w, i) => (
              <div key={i} className="ytm-skel" style={{ height: '14px', width: `${w}%` }} />
            ))}
          </div>
        ) : !data?.synthesis ? (
          /* Empty state */
          <p style={{
            margin: 0,
            fontSize: '14px',
            color: '#9ca3af',
            lineHeight: '1.6',
            textAlign: 'left',
            fontStyle: 'italic',
          }}>
            Weekly synthesis generates after each 7-day training window closes.
          </p>
        ) : (
          <>
            {/* Narrative */}
            <p style={{
              margin: '0 0 1rem 0',
              fontSize: '14.5px',
              lineHeight: '1.75',
              color: '#1F2937',
              textAlign: 'left',
              borderLeft: '3px solid #7D9CB8',
              paddingLeft: '0.875rem',
            }}>
              {data.synthesis}
            </p>

            {/* Planned intent disclosure */}
            {data.strategic_summary && (
              <div style={{
                borderTop: '1px solid #f0f2f4',
                paddingTop: '0.75rem',
                marginTop: '0.25rem',
              }}>
                <button
                  onClick={() => setIntentOpen(o => !o)}
                  style={{
                    background: 'none',
                    border: 'none',
                    padding: 0,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    fontSize: '11px',
                    fontWeight: '700',
                    letterSpacing: '0.1em',
                    color: '#9ca3af',
                    textTransform: 'uppercase',
                  }}
                >
                  <span style={{
                    display: 'inline-block',
                    width: '10px',
                    height: '10px',
                    borderRight: '1.5px solid #9ca3af',
                    borderBottom: '1.5px solid #9ca3af',
                    transform: intentOpen ? 'rotate(-135deg) translate(-2px,-2px)' : 'rotate(45deg)',
                    transition: 'transform 0.18s ease',
                    marginTop: intentOpen ? '4px' : '0',
                  }} />
                  {intentOpen ? 'Hide' : 'View'} planned intent
                </button>
                {intentOpen && (
                  <p style={{
                    margin: '0.625rem 0 0 0',
                    fontSize: '13px',
                    lineHeight: '1.65',
                    color: '#6b7280',
                    textAlign: 'left',
                    paddingLeft: '1rem',
                    borderLeft: '2px solid #e5e7eb',
                  }}>
                    {data.strategic_summary}
                  </p>
                )}
              </div>
            )}

            {/* Footer timestamp */}
            {data.generated_at && (
              <div style={{
                marginTop: '1rem',
                fontSize: '11px',
                color: '#d1d5db',
                textAlign: 'right',
                letterSpacing: '0.04em',
              }}>
                Generated {formatGeneratedAt(data.generated_at)}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

// ============================================================================
// ATHLETE MODEL PANEL
// ============================================================================

export const AthleteModelPanel: React.FC<{
  model: AthleteModel | null;
  onOpenGoalModal?: () => void;
  onOpenProfileModal?: () => void;
  onOpenPrefsModal?: () => void;
}> = ({ model, onOpenGoalModal, onOpenProfileModal, onOpenPrefsModal }) => {
  const autopsyCount = model?.total_autopsies ?? 0;
  const [jpExpanded, setJpExpanded] = useState(false);

  // Calibration state
  const divLow = model?.typical_divergence_low ?? null;
  const divThreshold = model?.divergence_injury_threshold ?? null;
  const hasEnvelope = divLow !== null && divLow !== -0.05;
  const hasThreshold = divThreshold !== null && divThreshold !== 0.15;
  const isCalibrated = hasEnvelope && hasThreshold && autopsyCount >= 10;
  const isLearning = autopsyCount >= 5;

  // Alignment
  const trend = model?.recent_alignment_trend ?? null;
  let trendLabel = 'Insufficient data';
  let trendColor = '#6b7280';
  if (trend === 'improving') { trendLabel = 'Improving ↑'; trendColor = '#16a34a'; }
  else if (trend === 'declining') { trendLabel = 'Declining ↓'; trendColor = '#dc2626'; }
  else if (trend === 'stable') { trendLabel = 'Stable'; trendColor = '#7D9CB8'; }

  const mc = model?.model_confidence;
  const composite = mc?.composite ?? 0;
  const c = mc?.components;

  const confLabel = composite >= 70 ? 'High' : composite >= 40 ? 'Building' : 'Low';
  const confColor = composite >= 70 ? '#16a34a' : composite >= 40 ? '#d97706' : '#9ca3af';

  const badgeStyle = {
    display: 'flex', alignItems: 'center', gap: '6px',
    padding: '4px 10px', borderRadius: '20px',
    backgroundColor: isCalibrated ? 'rgba(22,163,74,0.2)' : isLearning ? 'rgba(125,156,184,0.2)' : 'rgba(217,119,6,0.2)',
    border: `1px solid ${isCalibrated ? 'rgba(22,163,74,0.5)' : isLearning ? 'rgba(125,156,184,0.5)' : 'rgba(217,119,6,0.5)'}`,
  };
  const badgeDot = isCalibrated ? '#16a34a' : isLearning ? '#7D9CB8' : '#f59e0b';
  const badgeText = isCalibrated ? 'Calibrated' : isLearning ? 'Learning' : 'Getting Started';
  const badgeTextColor = isCalibrated ? '#4ade80' : isLearning ? '#7D9CB8' : '#fcd34d';

  // Full-width stat bar with glow on completion
  const StatBar: React.FC<{ pct: number; color: string }> = ({ pct, color }) => {
    const complete = pct >= 100;
    return (
      <div style={{
        height: '8px', borderRadius: '4px', width: '100%',
        background: 'linear-gradient(180deg, #edf0f4 0%, #e2e6ec 100%)',
        boxShadow: 'inset 0 1px 2px rgba(0,0,0,0.10)',
        overflow: 'hidden',
      }}>
        <div style={{
          height: '100%', width: `${Math.min(100, pct)}%`,
          background: complete
            ? `linear-gradient(90deg, ${color}cc 0%, ${color} 100%)`
            : `linear-gradient(90deg, ${color}77 0%, ${color}cc 100%)`,
          borderRadius: '4px',
          boxShadow: complete ? `0 0 6px ${color}88` : 'none',
          transition: 'width 0.5s cubic-bezier(0.4,0,0.2,1)',
        }} />
      </div>
    );
  };

  // Confidence component row — full-width bar layout
  const ConfRow: React.FC<{
    label: string;
    sublabel?: string;
    score: number;
    detail: string;
    action?: { href: string; label: string };
    onAction?: () => void;
    weight2x?: boolean;
    toggle?: { expanded: boolean; onToggle: () => void };
    children?: React.ReactNode;
  }> = ({ label, sublabel, score, detail, action, onAction, weight2x, toggle, children }) => {
    const complete = score >= 100;
    const rowColor = complete ? '#16a34a' : score >= 50 ? '#d97706' : '#9ca3af';
    const hasLink = !!(onAction || action);
    const linkStyle: React.CSSProperties = {
      fontSize: '10px', fontWeight: '600', color: '#7D9CB8',
      textDecoration: 'none', letterSpacing: '0.04em',
      background: 'none', border: 'none', padding: 0, cursor: 'pointer',
    };
    return (
      <div style={{ padding: '8px 0', borderBottom: '1px solid #f3f4f6' }}>
        {/* Label row */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '5px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', minWidth: 0 }}>
            {/* Completion dot */}
            <div style={{
              width: '14px', height: '14px', borderRadius: '50%', flexShrink: 0,
              backgroundColor: complete ? '#16a34a' : 'transparent',
              border: `2px solid ${complete ? '#16a34a' : '#d1d5db'}`,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: '8px', color: 'white', fontWeight: '900',
              boxShadow: complete ? '0 0 5px #16a34a66' : 'none',
            }}>
              {complete ? '✓' : ''}
            </div>
            <span style={{ fontSize: '12px', fontWeight: '600', color: '#1f2937', whiteSpace: 'nowrap' }}>{label}</span>
            {weight2x && (
              <span style={{
                fontSize: '9px', fontWeight: '800', color: '#FF5722',
                border: '1px solid #FF572244', borderRadius: '3px',
                padding: '0 3px', letterSpacing: '0.06em', flexShrink: 0,
              }}>2×</span>
            )}
            {sublabel && (
              <span style={{ fontSize: '10px', color: '#9ca3af', fontWeight: '400' }}>{sublabel}</span>
            )}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexShrink: 0, marginLeft: '8px' }}>
            {toggle && (
              <button onClick={toggle.onToggle} style={{
                background: toggle.expanded ? 'rgba(125,156,184,0.18)' : 'rgba(125,156,184,0.10)',
                border: '1px solid rgba(125,156,184,0.35)',
                borderRadius: '4px', cursor: 'pointer',
                fontSize: '9px', fontWeight: '700', color: '#7D9CB8',
                padding: '2px 6px', letterSpacing: '0.04em', lineHeight: 1.4,
              }}>
                {toggle.expanded ? '▾ hide' : '▸ detail'}
              </button>
            )}
            <span style={{
              fontSize: '13px', fontWeight: '800', color: rowColor,
              fontVariantNumeric: 'tabular-nums', letterSpacing: '-0.01em',
            }}>
              {score}%
            </span>
          </div>
        </div>
        {/* Full-width bar */}
        <StatBar pct={score} color={rowColor} />
        {/* Detail + link row: link left, detail centered */}
        <div style={{ display: 'flex', alignItems: 'baseline', marginTop: '3px' }}>
          {hasLink && (
            onAction
              ? <button onClick={onAction} style={linkStyle}>update / review →</button>
              : <a href={action!.href} style={linkStyle}>update / review →</a>
          )}
          <div style={{ flex: 1, textAlign: 'center', fontSize: '10px', color: '#9ca3af', lineHeight: 1.3 }}>{detail}</div>
        </div>
        {/* Expandable sub-rows */}
        {toggle?.expanded && children}
      </div>
    );
  };

  // Sub-row for Journal Power field breakdown
  const SubRow: React.FC<{
    label: string;
    pct: number;
    badge4x?: boolean;
    separator?: boolean;
  }> = ({ label, pct, badge4x, separator }) => {
    const subColor = pct >= 80 ? '#16a34a' : pct >= 50 ? '#d97706' : '#9ca3af';
    return (
      <div style={{
        padding: separator ? '5px 0 3px' : '3px 0',
        borderTop: separator ? '1px dashed #e5e7eb' : 'none',
        marginTop: separator ? '4px' : 0,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '3px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <span style={{ fontSize: '11px', color: '#4b5563', fontWeight: '500' }}>{label}</span>
            {badge4x && (
              <span style={{
                fontSize: '8px', fontWeight: '800', color: '#FF5722',
                border: '1px solid #FF572244', borderRadius: '3px',
                padding: '0 3px', letterSpacing: '0.06em',
              }}>4×</span>
            )}
          </div>
          <span style={{
            fontSize: '11px', fontWeight: '700', color: subColor,
            fontVariantNumeric: 'tabular-nums',
          }}>{pct}%</span>
        </div>
        {/* Bar — notes is 4× as wide as a 1-pt field bar; tick marks at each 1-pt interval */}
        <div style={{
          height: '5px', borderRadius: '3px',
          width: badge4x ? '100%' : '25%',
          background: '#edf0f4', overflow: 'hidden',
          position: 'relative',
        }}>
          <div style={{
            height: '100%', width: `${Math.min(100, pct)}%`,
            background: pct >= 80
              ? `linear-gradient(90deg, ${subColor}99 0%, ${subColor} 100%)`
              : `linear-gradient(90deg, ${subColor}66 0%, ${subColor}aa 100%)`,
            borderRadius: '3px',
            transition: 'width 0.4s cubic-bezier(0.4,0,0.2,1)',
          }} />
          {badge4x && [25, 50, 75].map(tick => (
            <div key={tick} style={{
              position: 'absolute', top: 0, bottom: 0,
              left: `${tick}%`, width: '1px',
              backgroundColor: 'rgba(0,0,0,0.18)', zIndex: 1,
            }} />
          ))}
        </div>
      </div>
    );
  };

  // Journal Power detail string
  const jpDetail = c?.journal_power
    ? `${c.journal_power.journal_count}/${c.journal_power.activity_count} activities · avg quality ${c.journal_power.avg_power}%`
    : '—';

  // Profile missing fields → readable labels
  const profileFieldLabels: Record<string, string> = {
    age: 'age', gender: 'gender', primary_sport: 'sport', training_experience: 'experience',
  };
  const profileDetail = c?.athlete_profile
    ? c.athlete_profile.missing.length === 0
      ? 'Complete'
      : `Missing: ${c.athlete_profile.missing.map(f => profileFieldLabels[f] ?? f).join(', ')}`
    : '—';

  const hrDetail = c?.hr_calibration
    ? [!c.hr_calibration.max_hr && 'max HR', !c.hr_calibration.resting_hr && 'resting HR']
        .filter(Boolean).join(', ') || 'Complete'
    : '—';

  return (
    <div id="athlete-model" style={{ width: '100%', borderRadius: '8px', overflow: 'hidden', boxShadow: '0 2px 4px rgba(0,0,0,0.10)' }}>

      {/* Header */}
      <div style={{
        background: 'linear-gradient(90deg, #1B2E4B 0%, #2d4a6e 100%)',
        padding: '0.75rem 1.25rem',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      }}>
        <div>
          <div style={{ fontSize: '10px', letterSpacing: '0.15em', color: '#7D9CB8', fontWeight: '700', textTransform: 'uppercase' }}>
            Athlete Model
          </div>
          <div style={{ fontSize: '15px', fontWeight: '700', color: '#ffffff', marginTop: '1px' }}>
            What Your Coach Has Learned
          </div>
        </div>
        <div style={badgeStyle}>
          <div style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: badgeDot }} />
          <span style={{ fontSize: '11px', fontWeight: '600', letterSpacing: '0.08em', color: badgeTextColor, textTransform: 'uppercase' }}>
            {badgeText}
          </span>
        </div>
      </div>

      <div style={{ backgroundColor: 'white' }}>

        {/* ── Section 1: Model Confidence ── */}
        <div style={{ padding: '1rem 1.25rem', borderBottom: '1px solid #f3f4f6' }}>

          {/* Composite score hero */}
          <div style={{
            borderRadius: '10px', backgroundColor: '#1B2E4B',
            padding: '16px 20px 14px', marginBottom: '16px',
            position: 'relative', overflow: 'hidden',
          }}>
            {/* Background glow when high */}
            {composite >= 70 && (
              <div style={{
                position: 'absolute', inset: 0, borderRadius: '10px',
                background: `radial-gradient(ellipse at 50% 0%, ${confColor}22 0%, transparent 70%)`,
                pointerEvents: 'none',
              }} />
            )}
            {/* Label row */}
            <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', marginBottom: '10px' }}>
              <div style={{ fontSize: '9px', letterSpacing: '0.14em', color: 'rgba(255,255,255,0.45)', textTransform: 'uppercase', fontWeight: '700' }}>
                Model Confidence
              </div>
              <div style={{
                fontSize: '11px', fontWeight: '700', letterSpacing: '0.06em',
                color: confColor, textTransform: 'uppercase',
                background: `${confColor}22`, borderRadius: '4px', padding: '1px 7px',
              }}>
                {confLabel}
              </div>
            </div>
            {/* Big number + game instructions on same row */}
            <div style={{ display: 'flex', alignItems: 'flex-end', gap: '8px', marginBottom: '10px' }}>
              <div style={{
                fontSize: '56px', fontWeight: '900', lineHeight: 1,
                color: confColor, fontVariantNumeric: 'tabular-nums',
                textShadow: composite >= 70 ? `0 0 24px ${confColor}66` : 'none',
                transition: 'color 0.4s ease',
                flexShrink: 0,
              }}>
                {composite}
              </div>
              <div style={{ fontSize: '22px', fontWeight: '700', color: confColor, paddingBottom: '8px', opacity: 0.8, flexShrink: 0 }}>%</div>
              <div style={{
                flex: 1, fontSize: '11px', lineHeight: 1.5,
                color: 'rgba(255,255,255,0.55)', paddingBottom: '6px',
              }}>
                {(() => {
                  if (!c) return null;
                  const notesCoverage = c.journal_power?.field_coverage?.notes ?? 100;
                  const journalCoverage = c.journal_power?.coverage_pct ?? 100;
                  const jpScore = c.journal_power?.score ?? 100;
                  const profileScore = c.athlete_profile?.score ?? 100;
                  const prefsScore = c.coaching_prefs?.score ?? 100;
                  const seasonScore = c.season_plan?.score ?? 100;
                  const scheduleScore = c.weekly_schedule?.score ?? 100;
                  const hrScore = c.hr_calibration?.score ?? 100;
                  const aerobicScore = c.aerobic_assessment?.score ?? 100;
                  const hi = (text: string) => (
                    <span style={{ color: 'rgba(255,255,255,0.85)', fontWeight: '600' }}>{text}</span>
                  );
                  if (notesCoverage < 50 && jpScore < 80)
                    return <>{hi('Highest ROI: add notes.')} You're logging {notesCoverage}% with notes — they're worth 4× any other field.</>;
                  if (journalCoverage < 50 && jpScore < 60)
                    return <>{hi('Log more, gain more.')} Journal coverage is {journalCoverage}% — each entry with notes moves the needle most.</>;
                  const zeroWins: string[] = [];
                  if (profileScore === 0) zeroWins.push('athlete profile');
                  if (prefsScore === 0) zeroWins.push('coaching preferences');
                  if (hrScore === 0) zeroWins.push('HR zones');
                  if (seasonScore === 0) zeroWins.push('race goal');
                  if (scheduleScore === 0) zeroWins.push('weekly schedule');
                  if (zeroWins.length >= 2)
                    return <>{hi('Quick wins available.')} {zeroWins.slice(0, 2).map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' and ')} {zeroWins.length > 2 ? `(+${zeroWins.length - 2} more) are` : 'are'} unset — each lifts a slider for free.</>;
                  if (zeroWins.length === 1)
                    return <>{hi('One free win left.')} Your {zeroWins[0]} is unset. Fill it and recommendations sharpen immediately.</>;
                  if (aerobicScore === 0)
                    return <>{hi('Unlock aerobic assessment.')} Log a steady run with HR data. Your coach needs HR drift to calibrate your aerobic baseline.</>;
                  if (notesCoverage < 70)
                    return <>{hi('Notes gap.')} {notesCoverage}% coverage. Notes are 4× any structured field — closing this raises signal fastest.</>;
                  if (journalCoverage < 70)
                    return <>{hi('Getting sharper.')} Journal at {journalCoverage}% — keep logging after each run, notes especially.</>;
                  return <>{hi('Strong signal, low noise.')} Your coach knows your patterns. Keep logging notes after each run.</>;
                })()}
              </div>
            </div>
            {/* Progress track */}
            <div style={{ height: '6px', borderRadius: '3px', backgroundColor: 'rgba(255,255,255,0.12)', overflow: 'hidden' }}>
              <div style={{
                height: '100%', width: `${composite}%`,
                background: `linear-gradient(90deg, ${confColor}99 0%, ${confColor} 100%)`,
                borderRadius: '3px',
                boxShadow: composite >= 70 ? `0 0 8px ${confColor}88` : 'none',
                transition: 'width 0.6s cubic-bezier(0.4,0,0.2,1)',
              }} />
            </div>
            {/* Milestone ticks */}
            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '4px' }}>
              {[0, 40, 70, 100].map(tick => (
                <div key={tick} style={{
                  fontSize: '9px', fontWeight: '600',
                  color: composite >= tick ? 'rgba(255,255,255,0.5)' : 'rgba(255,255,255,0.2)',
                }}>
                  {tick === 0 ? '' : `${tick}%`}
                </div>
              ))}
            </div>
          </div>

          {/* 8 component rows — ordered by significance */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
            <ConfRow
              label="Activity History"
              sublabel="last 60 days"
              score={c?.activity_history.score ?? 0}
              detail={c?.activity_history.score === 100
                ? `${c?.activity_history.recent_count} activities · ACWR window established`
                : `${c?.activity_history.recent_count ?? 0} activities · need data from 28+ days ago`}
            />
            <ConfRow
              label="Journal Power"
              sublabel="last 30 days"
              score={c?.journal_power.score ?? 0}
              detail={jpDetail}
              weight2x
              toggle={{ expanded: jpExpanded, onToggle: () => setJpExpanded(v => !v) }}
            >
              {c?.journal_power.field_coverage && (
                <div style={{ marginTop: '6px', paddingLeft: '20px', borderLeft: '2px solid #f0f2f5' }}>
                  <SubRow label="Energy level (1 pt)"    pct={c.journal_power.field_coverage['energy_level']     ?? 0} />
                  <SubRow label="RPE score (1 pt)"       pct={c.journal_power.field_coverage['rpe_score']        ?? 0} />
                  <SubRow label="Pain score (1 pt)"      pct={c.journal_power.field_coverage['pain_percentage']  ?? 0} />
                  <SubRow label="Sleep quality (1 pt)"   pct={c.journal_power.field_coverage['sleep_quality']    ?? 0} />
                  <SubRow label="Morning soreness (1 pt)"pct={c.journal_power.field_coverage['morning_soreness'] ?? 0} />
                  <SubRow label="HRV value (1 pt)"       pct={c.journal_power.field_coverage['hrv_value']        ?? 0} />
                  <SubRow label="Resting HR (1 pt)"      pct={c.journal_power.field_coverage['resting_hr']       ?? 0} />
                  <SubRow label="Notes signal (up to 4 pts)" pct={c.journal_power.field_coverage['notes'] ?? 0} badge4x separator />
                </div>
              )}
            </ConfRow>
            <ConfRow
              label="Athlete Profile"
              score={c?.athlete_profile.score ?? 0}
              detail={profileDetail}
              onAction={onOpenProfileModal}
              action={onOpenProfileModal ? undefined : { href: '/settings/hrzones', label: 'Settings' }}
            />
            <ConfRow
              label="HR Calibration"
              score={c?.hr_calibration.score ?? 0}
              detail={hrDetail}
              action={{ href: '/settings/hrzones', label: 'Settings' }}
            />
            <ConfRow
              label="Season Plan"
              score={c?.season_plan.score ?? 0}
              detail={c?.season_plan.score === 100 ? 'A-goal complete' : c?.season_plan.has_name_date ? 'Missing distance' : 'No A-goal set'}
              onAction={onOpenGoalModal}
              action={onOpenGoalModal ? undefined : { href: '/?tab=coach&subtab=season', label: 'Season' }}
            />
            <ConfRow
              label="Weekly Schedule"
              score={c?.weekly_schedule.score ?? 0}
              detail={c?.weekly_schedule.score === 100 ? 'Availability set' : 'Days not configured'}
              action={{ href: '/?tab=coach&subtab=week', label: 'Week' }}
            />
            <ConfRow
              label="Coaching Preferences"
              score={c?.coaching_prefs.score ?? 0}
              detail={c?.coaching_prefs.score === 100 ? 'Complete' : 'Not yet configured'}
              onAction={onOpenPrefsModal}
              action={onOpenPrefsModal ? undefined : { href: '/?tab=coach&subtab=season', label: 'Season' }}
            />
            <ConfRow
              label="Aerobic Assessment"
              sublabel="last 28 days"
              score={c?.aerobic_assessment.score ?? 0}
              detail={c?.aerobic_assessment.score === 100 ? 'Assessment on file' : 'No recent assessment'}
              action={{ href: '/?tab=coach&subtab=season', label: 'Season' }}
            />
          </div>
        </div>

        {/* ── Section 2: Training Envelope (shown when calibrated) ── */}
        <div style={{ padding: '1rem 1.25rem', borderBottom: '1px solid #f3f4f6' }}>
          <div style={{ fontSize: '10px', letterSpacing: '0.12em', fontWeight: '700', color: '#6b7280', textTransform: 'uppercase', marginBottom: '0.75rem' }}>
            Training Envelope
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1px', backgroundColor: '#f3f4f6', borderRadius: '6px', overflow: 'hidden' }}>

            {/* Productive window */}
            <div style={{ backgroundColor: 'white', padding: '0.75rem 1rem', borderLeft: '3px solid #7D9CB8' }}>
              <div style={{ fontSize: '10px', letterSpacing: '0.1em', fontWeight: '700', color: '#6b7280', textTransform: 'uppercase', marginBottom: '4px' }}>
                Productive Window
              </div>
              {hasEnvelope ? (
                <>
                  <div style={{ fontSize: '20px', fontWeight: '700', color: '#1B2E4B', fontVariantNumeric: 'tabular-nums' }}>
                    0.000 to {divLow!.toFixed(3)}
                  </div>
                  <div style={{ fontSize: '11px', color: '#9ca3af', marginTop: '2px' }}>Your personal training range</div>
                </>
              ) : (
                <>
                  <div style={{ fontSize: '14px', fontWeight: '600', color: '#9ca3af' }}>Calibrating…</div>
                  <div style={{ fontSize: '11px', color: '#9ca3af', marginTop: '2px' }}>Needs {Math.max(0, 5 - autopsyCount)} more autopsies</div>
                </>
              )}
            </div>

            {/* Breakdown threshold */}
            <div style={{ backgroundColor: 'white', padding: '0.75rem 1rem', borderLeft: '3px solid #ca8a04' }}>
              <div style={{ fontSize: '10px', letterSpacing: '0.1em', fontWeight: '700', color: '#6b7280', textTransform: 'uppercase', marginBottom: '4px' }}>
                Breakdown Threshold
              </div>
              {hasThreshold ? (
                <>
                  <div style={{ fontSize: '20px', fontWeight: '700', color: '#713f12', fontVariantNumeric: 'tabular-nums' }}>
                    -{divThreshold!.toFixed(3)}
                  </div>
                  <div style={{ fontSize: '11px', color: '#9ca3af', marginTop: '2px' }}>Beyond this, distress has followed</div>
                </>
              ) : (
                <>
                  <div style={{ fontSize: '14px', fontWeight: '600', color: '#9ca3af' }}>Not yet set</div>
                  <div style={{ fontSize: '11px', color: '#9ca3af', marginTop: '2px' }}>Needs 3 physical distress events</div>
                </>
              )}
            </div>

          </div>
        </div>

        {/* ── Section 3: Plan Execution ── */}
        <div style={{ padding: '1rem 1.25rem' }}>
          <div style={{ fontSize: '10px', letterSpacing: '0.12em', fontWeight: '700', color: '#6b7280', textTransform: 'uppercase', marginBottom: '0.75rem' }}>
            Plan Execution
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1px', backgroundColor: '#f3f4f6', borderRadius: '6px', overflow: 'hidden' }}>
            <div style={{ backgroundColor: 'white', padding: '0.75rem 1rem', borderLeft: '3px solid #1B2E4B' }}>
              <div style={{ fontSize: '10px', letterSpacing: '0.1em', fontWeight: '700', color: '#6b7280', textTransform: 'uppercase', marginBottom: '4px' }}>
                Avg Alignment
              </div>
              <div style={{ fontSize: '20px', fontWeight: '700', color: '#1B2E4B', fontVariantNumeric: 'tabular-nums' }}>
                {model?.avg_lifetime_alignment != null ? `${model.avg_lifetime_alignment}/10` : '—'}
              </div>
              <div style={{ fontSize: '11px', color: '#9ca3af', marginTop: '2px' }}>Lifetime plan adherence</div>
            </div>
            <div style={{ backgroundColor: 'white', padding: '0.75rem 1rem', borderLeft: `3px solid ${trendColor}` }}>
              <div style={{ fontSize: '10px', letterSpacing: '0.1em', fontWeight: '700', color: '#6b7280', textTransform: 'uppercase', marginBottom: '4px' }}>
                Alignment Trend
              </div>
              <div style={{ fontSize: '20px', fontWeight: '700', color: trendColor }}>
                {trendLabel}
              </div>
              <div style={{ fontSize: '11px', color: '#9ca3af', marginTop: '2px' }}>Last 5 autopsied workouts</div>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
};

// ============================================================================
// REVISION PROPOSAL TYPES + COMPONENT — Phase E (Plan Execution Loop)
// ============================================================================

interface DeviationLogEntry {
  date: string;
  reason?: string;
  tier?: number;
  note?: string;
}

interface RevisionProposal {
  note?: string;
  triggered_by?: string;
  tier2_reason?: string;
}

interface RevisionProposalData {
  pending: boolean;
  week_start: string;
  proposal: RevisionProposal | null;
  deviation_log: DeviationLogEntry[];
}

interface RevisionProposalCardProps {
  data: RevisionProposalData;
  onApprove: () => void;
  onDismiss: () => void;
}

const RevisionProposalCard: React.FC<RevisionProposalCardProps> = ({ data, onApprove, onDismiss }) => {
  const [actionState, setActionState] = useState<'idle' | 'approving' | 'dismissing' | 'approved' | 'dismissed'>('idle');
  const [actionError, setActionError] = useState<string | null>(null);

  const proposal = data.proposal || {};

  // Filter to tier-1/2 entries only (those with a tier field, or any entry with a reason)
  const significantEntries = (data.deviation_log || [])
    .filter(e => e.tier === 1 || e.tier === 2 || e.reason)
    .slice(-3);

  const handleApprove = async () => {
    setActionState('approving');
    setActionError(null);
    try {
      const res = await fetch('/api/coach/revision-proposal/approve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ week_start: data.week_start }),
      });
      const json = await res.json();
      if (!res.ok || !json.success) throw new Error(json.error || 'Approval failed');
      setActionState('approved');
      onApprove();
    } catch (e) {
      setActionError(e instanceof Error ? e.message : 'Something went wrong');
      setActionState('idle');
    }
  };

  const handleDismiss = async () => {
    setActionState('dismissing');
    setActionError(null);
    try {
      const res = await fetch('/api/coach/revision-proposal/dismiss', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ week_start: data.week_start }),
      });
      const json = await res.json();
      if (!res.ok || !json.success) throw new Error(json.error || 'Dismiss failed');
      setActionState('dismissed');
      onDismiss();
    } catch (e) {
      setActionError(e instanceof Error ? e.message : 'Something went wrong');
      setActionState('idle');
    }
  };

  if (actionState === 'approved') {
    return (
      <div style={{
        margin: '0.75rem 0',
        padding: '1rem 1.25rem',
        backgroundColor: '#f0fdf4',
        border: '2px solid #86efac',
        borderRadius: '8px',
        color: '#15803d',
        fontSize: '15px',
        fontWeight: '600',
        textAlign: 'left'
      }}>
        Plan adjustment acknowledged and logged.
      </div>
    );
  }

  if (actionState === 'dismissed') {
    return null;
  }

  return (
    <div style={{
      margin: '0.75rem 0',
      padding: '1.25rem',
      backgroundColor: '#fffbeb',
      border: '2px solid #f59e0b',
      borderRadius: '8px',
    }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.75rem' }}>
        <div style={{
          display: 'inline-block',
          padding: '2px 10px',
          backgroundColor: '#f59e0b',
          color: 'white',
          borderRadius: '12px',
          fontSize: '12px',
          fontWeight: '700',
          letterSpacing: '0.05em',
          textTransform: 'uppercase',
          flexShrink: 0
        }}>
          Plan Review
        </div>
        <h3 style={{
          margin: 0,
          fontSize: '16px',
          fontWeight: '700',
          color: '#92400e',
          textAlign: 'left'
        }}>
          Your training plan may need adjustment
        </h3>
      </div>

      {/* Summary note */}
      {(proposal.note || proposal.triggered_by) && (
        <p style={{
          margin: '0 0 0.75rem 0',
          fontSize: '14px',
          color: '#78350f',
          lineHeight: '1.6',
          textAlign: 'left'
        }}>
          {proposal.note || proposal.triggered_by}
          {proposal.tier2_reason && (
            <span style={{ display: 'block', marginTop: '0.25rem', color: '#92400e' }}>
              {proposal.tier2_reason}
            </span>
          )}
        </p>
      )}

      {/* Deviation log summary */}
      {significantEntries.length > 0 && (
        <div style={{
          marginBottom: '1rem',
          padding: '0.75rem',
          backgroundColor: '#fef3c7',
          borderRadius: '6px',
          border: '1px solid #fde68a'
        }}>
          <div style={{ fontSize: '12px', fontWeight: '700', color: '#92400e', marginBottom: '0.4rem', textAlign: 'left', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Recent deviations
          </div>
          <ul style={{ margin: 0, padding: '0 0 0 1.1rem', listStyle: 'disc' }}>
            {significantEntries.map((entry, idx) => (
              <li key={idx} style={{ fontSize: '13px', color: '#78350f', lineHeight: '1.5', textAlign: 'left' }}>
                <span style={{ fontWeight: '600' }}>{entry.date}</span>
                {' — '}
                {entry.reason || entry.note || ''}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Error */}
      {actionError && (
        <p style={{ margin: '0 0 0.75rem 0', fontSize: '13px', color: '#b91c1c', textAlign: 'left' }}>
          {actionError}
        </p>
      )}

      {/* Action buttons */}
      <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
        <button
          onClick={handleApprove}
          disabled={actionState === 'approving' || actionState === 'dismissing'}
          style={{
            padding: '9px 20px',
            backgroundColor: actionState === 'approving' ? '#d97706' : '#f59e0b',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: actionState === 'approving' || actionState === 'dismissing' ? 'not-allowed' : 'pointer',
            fontSize: '14px',
            fontWeight: '600',
            opacity: actionState === 'approving' || actionState === 'dismissing' ? 0.7 : 1
          }}
        >
          {actionState === 'approving' ? 'Saving...' : 'Approve changes'}
        </button>
        <button
          onClick={handleDismiss}
          disabled={actionState === 'approving' || actionState === 'dismissing'}
          style={{
            padding: '9px 20px',
            backgroundColor: 'transparent',
            color: '#92400e',
            border: '2px solid #f59e0b',
            borderRadius: '6px',
            cursor: actionState === 'approving' || actionState === 'dismissing' ? 'not-allowed' : 'pointer',
            fontSize: '14px',
            fontWeight: '600',
            opacity: actionState === 'approving' || actionState === 'dismissing' ? 0.7 : 1
          }}
        >
          {actionState === 'dismissing' ? 'Saving...' : 'Keep original plan'}
        </button>
      </div>
    </div>
  );
};

// ============================================================================
// MAIN COMPONENT
// ============================================================================

const CoachPage: React.FC = () => {
  // Performance monitoring
  usePagePerformanceMonitoring('coach');
  const perfMonitor = useComponentPerformanceMonitoring('CoachPage');

  // State management (only what's needed for Coach page display)
  const [raceGoals, setRaceGoals] = useState<RaceGoal[]>([]);
  const [weeklyProgram, setWeeklyProgram] = useState<WeeklyProgram | null>(null);
  const [trainingStage, setTrainingStage] = useState<TrainingStage | null>(null);
  
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [loadingMessage, setLoadingMessage] = useState<string>('Loading your coaching dashboard...');
  const [error, setError] = useState<string | null>(null);
  const [showOnboarding, setShowOnboarding] = useState<boolean>(false);
  
  // Secondary navigation state
  const getInitialSubTab = (): 'week' | 'season' | 'history' => {
    const p = new URLSearchParams(window.location.search).get('subtab');
    if (p === 'season' || p === 'history') return p;
    return 'week';
  };
  const [activeSubTab, setActiveSubTab] = useState<'week' | 'season' | 'history'>(getInitialSubTab);

  const [athleteModel, setAthleteModel] = useState<AthleteModel | null>(null);
  const [raceReadiness, setRaceReadiness] = useState<RaceReadiness | null>(null);
  const [weeklySynthesis, setWeeklySynthesis] = useState<WeeklySynthesisData | null>(null);

  const [trainingSchedule, setTrainingSchedule] = useState<TrainingSchedule | null>(null);

  // Schedule review state
  const [scheduleReviewStatus, setScheduleReviewStatus] = useState<{
    needs_review: boolean;
    week_start: string;
    is_sunday: boolean;
  } | null>(null);
  const [showScheduleReviewBanner, setShowScheduleReviewBanner] = useState<boolean>(false);

  // Phase E: revision proposal state
  const [revisionProposal, setRevisionProposal] = useState<RevisionProposalData | null>(null);

  // ============================================================================
  // DATA FETCHING
  // ============================================================================

  const fetchCoachData = async () => {
    const startTime = performance.now();
    setIsLoading(true);
    setLoadingMessage('Loading your coaching dashboard...');
    setError(null);

    // Show helpful message if loading takes a while (program generation)
    const longLoadTimer = setTimeout(() => {
      setLoadingMessage('Generating your personalized weekly program... This may take 30-90 seconds. ☕');
    }, 3000);

    try {
      // Fetch only data needed for Coach page display
      const [
        goalsRes,
        stageRes,
        programRes,
        reviewStatusRes,
        athleteModelRes,
        revisionRes,
        readinessRes,
        synthesisRes,
        scheduleRes
      ] = await Promise.all([
        fetch('/api/coach/race-goals'),
        fetch('/api/coach/training-stage'),
        fetch('/api/coach/weekly-program'),
        fetch('/api/coach/schedule-review-status'),
        fetch('/api/athlete-model'),
        fetch('/api/coach/revision-proposal', { credentials: 'include' }),
        fetch('/api/coach/race-readiness'),
        fetch('/api/coach/weekly-synthesis'),
        fetch('/api/coach/training-schedule')
      ]);

      // Check for critical errors (race goals is essential)
      if (!goalsRes.ok) throw new Error('Failed to fetch race goals');

      // Parse race goals (critical for countdown banner)
      const goalsData = await goalsRes.json();
      setRaceGoals(goalsData.goals || []);

      // Parse training stage (for timeline and countdown banner color)
      if (stageRes.ok) {
        const stageData = await stageRes.json();
        // API returns { current_stage: {...}, timeline: [...] }
        // Transform to match TrainingStage interface
        // Ensure races arrays are always arrays (not null)
        const transformedTimeline = (stageData.timeline || []).map((week: any) => ({
          ...week,
          races: Array.isArray(week.races) ? week.races : []
        }));
        
        setTrainingStage({
          stage: stageData.current_stage?.stage || null,
          weeks_to_race: stageData.current_stage?.weeks_to_race || null,
          race_name: stageData.current_stage?.race_name || null,
          priority: stageData.current_stage?.priority || null,
          details: stageData.current_stage?.stage_description || '',
          timeline: transformedTimeline
        });
      } else {
        console.warn('Failed to fetch training stage');
        setTrainingStage(null);
      }

      // Parse weekly program
      if (programRes.ok) {
        const programData = await programRes.json();
        setWeeklyProgram(programData.program || null);
      } else {
        console.warn('Failed to fetch weekly program');
        setWeeklyProgram(null);
      }

      // Parse schedule review status
      if (reviewStatusRes.ok) {
        const reviewData = await reviewStatusRes.json();
        if (reviewData.success) {
          setScheduleReviewStatus({
            needs_review: reviewData.needs_review,
            week_start: reviewData.week_start,
            is_sunday: reviewData.is_sunday
          });
          setShowScheduleReviewBanner(reviewData.needs_review);
        }
      }

      // Parse athlete model
      if (athleteModelRes.ok) {
        const modelData = await athleteModelRes.json();
        if (modelData.success) {
          setAthleteModel(modelData.model);
        }
      }

      // Parse race readiness
      if (readinessRes.ok) {
        const readinessData = await readinessRes.json();
        if (readinessData.success && readinessData.readiness) {
          setRaceReadiness(readinessData.readiness);
        }
      }

      // Parse weekly synthesis
      if (synthesisRes.ok) {
        const synthData = await synthesisRes.json();
        if (!synthData.error) {
          setWeeklySynthesis(synthData);
        }
      }

      // Parse training schedule
      if (scheduleRes.ok) {
        const scheduleData = await scheduleRes.json();
        setTrainingSchedule(scheduleData.schedule || null);
      }

      // Phase E: parse revision proposal
      if (revisionRes.ok) {
        const revisionData = await revisionRes.json();
        if (revisionData.pending) {
          setRevisionProposal(revisionData as RevisionProposalData);
        } else {
          setRevisionProposal(null);
        }
      }

      // Check if onboarding needed (no race goals)
      if (!goalsData.goals || goalsData.goals.length === 0) {
        setShowOnboarding(true);
      } else {
        setShowOnboarding(false);  // Hide onboarding if goals exist
      }

      // Report performance
      const loadTime = performance.now() - startTime;
      perfMonitor.reportMetrics(loadTime);

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load coach data';
      setError(errorMessage);
      perfMonitor.reportMetrics(0, errorMessage);
    } finally {
      clearTimeout(longLoadTimer);
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchCoachData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ============================================================================
  // HELPER FUNCTIONS
  // ============================================================================

  const calculateDaysToRace = (raceDate: string): number => {
    const today = new Date();
    const race = new Date(raceDate + 'T12:00:00');
    const diffTime = race.getTime() - today.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  const getPrimaryRace = (): RaceGoal | null => {
    // Find A race first, then B, then C, then first race
    const aRace = raceGoals.find(g => g.priority === 'A');
    if (aRace) return aRace;
    
    const bRace = raceGoals.find(g => g.priority === 'B');
    if (bRace) return bRace;
    
    const cRace = raceGoals.find(g => g.priority === 'C');
    if (cRace) return cRace;
    
    return raceGoals.length > 0 ? raceGoals[0] : null;
  };

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const formatTime = (minutes: number): string => {
    const hours = Math.floor(minutes / 60);
    const mins = Math.floor(minutes % 60);
    if (hours > 0) {
      return `${hours}h ${mins}m`;
    }
    return `${mins}m`;
  };

  const handleAcceptSchedule = async () => {
    try {
      const response = await fetch('/api/coach/schedule-review-accept', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (response.ok) {
        setShowScheduleReviewBanner(false);
        setScheduleReviewStatus(prev => prev ? { ...prev, needs_review: false } : null);
      }
    } catch (err) {
      console.error('Error accepting schedule:', err);
    }
  };

  const handleDismissBanner = () => {
    setShowScheduleReviewBanner(false);
  };

  // ============================================================================
  // RENDER: LOADING STATE
  // ============================================================================

  if (isLoading) {
    return (
      <div className={styles.dashboardContainer}>
        <div className={styles.card} style={{
          textAlign: 'center',
          padding: '60px 20px',
          backgroundColor: '#f8fafc'
        }}>
          <YTMSpinner />
          <p style={{ marginTop: '20px', color: '#7f8c8d', fontSize: '16px', lineHeight: '1.6' }}>
            {loadingMessage}
          </p>
          {loadingMessage.includes('30-90 seconds') && (
            <p style={{ marginTop: '10px', color: '#95a5a6', fontSize: '14px' }}>
              Your AI coach is analyzing your training data, race goals, and recent performance to create an optimized plan.
            </p>
          )}
        </div>
      </div>
    );
  }

  // ============================================================================
  // RENDER: ERROR STATE
  // ============================================================================

  if (error) {
    return (
      <div className={styles.dashboardContainer}>
        <div className={styles.card} style={{ textAlign: 'center', padding: '60px 20px' }}>
          <h2 style={{ color: '#e74c3c', marginBottom: '20px' }}>⚠️ Error Loading Coach Page</h2>
          <p style={{ color: '#7f8c8d', marginBottom: '30px' }}>{error}</p>
          <button
            onClick={() => window.location.reload()}
            style={{
              padding: '12px 24px',
              fontSize: '16px',
              backgroundColor: '#3498db',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  // ============================================================================
  // RENDER: ONBOARDING MODAL
  // ============================================================================

  if (showOnboarding) {
    return (
      <div className={styles.dashboardContainer}>
        <div className={styles.card} style={{ maxWidth: '600px', margin: '40px auto', padding: '40px' }}>
          <h1 style={{ fontSize: '32px', marginBottom: '20px', textAlign: 'center' }}>
            Welcome to Coach YTM! 🐵
          </h1>
          <p style={{ fontSize: '18px', color: '#7f8c8d', marginBottom: '30px', textAlign: 'center' }}>
            Let's set up your coaching profile to generate personalized training programs.
          </p>

          <div style={{ marginBottom: '30px' }}>
            <h3 style={{ marginBottom: '15px' }}>Quick Setup (3 steps):</h3>
            <ol style={{ fontSize: '16px', lineHeight: '1.8', paddingLeft: '20px' }}>
              <li>
                <strong>Add Your Race Goals</strong> - What races are you training for?
                (A races are your primary focus, B races help evaluate fitness, C races are training volume)
              </li>
              <li>
                <strong>Upload Race History</strong> - Past race results help assess your fitness trends
                (optional but recommended)
              </li>
              <li>
                <strong>Configure Training Schedule</strong> - Tell us your weekly availability
                so we can fit training into your life
              </li>
            </ol>
          </div>

          <div style={{ display: 'flex', gap: '15px', justifyContent: 'center' }}>
            <button
              onClick={() => {
                setShowOnboarding(false);
                setActiveSubTab('goals'); // Navigate to Race Goals tab
              }}
              style={{
                padding: '14px 28px',
                fontSize: '16px',
                backgroundColor: '#3498db',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontWeight: 'bold'
              }}
            >
              Let's Get Started! 🚀
            </button>
            <button
              onClick={() => setShowOnboarding(false)}
              style={{
                padding: '14px 28px',
                fontSize: '16px',
                backgroundColor: '#95a5a6',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
            >
              Skip for Now
            </button>
          </div>

          <p style={{ 
            marginTop: '30px', 
            fontSize: '14px', 
            color: '#95a5a6', 
            textAlign: 'center' 
          }}>
            Don't worry - you can set this up anytime. But the more we know,<br />
            the better your personalized training programs will be!
          </p>
        </div>
      </div>
    );
  }

  // ============================================================================
  // RENDER: MAIN COACH PAGE
  // ============================================================================

  const primaryRace = getPrimaryRace();
  const daysToRace = primaryRace ? calculateDaysToRace(primaryRace.race_date) : null;

  return (
    <div className={styles.dashboardContainer}>
      
      {/* ============================================================
          HEADER (matching Guide page style)
      ============================================================ */}
      <style>{`
        .coach-header {
          background: linear-gradient(90deg, #E6F0FF 0%, #7D9CB8 50%, #1B2E4B 100%);
          color: white;
          text-align: right;
          padding: 1.2rem 1.6rem; /* 80% of 1.5rem and 2rem */
          position: relative;
          overflow: hidden;
          min-height: 180px;
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 0;
        }
        .coach-header::before {
          content: '';
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: 
            radial-gradient(circle at 20% 30%, rgba(230, 240, 255, 0.3) 0%, transparent 50%),
            radial-gradient(circle at 80% 70%, rgba(125, 156, 184, 0.25) 0%, transparent 50%),
            radial-gradient(circle at 50% 50%, rgba(180, 200, 220, 0.2) 0%, transparent 60%),
            radial-gradient(circle at 10% 80%, rgba(27, 46, 75, 0.25) 0%, transparent 45%),
            radial-gradient(circle at 90% 20%, rgba(100, 130, 160, 0.2) 0%, transparent 50%);
          pointer-events: none;
          mix-blend-mode: multiply;
        }
        .coach-header::after {
          content: '';
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background-image: 
            repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(255, 255, 255, 0.03) 2px, rgba(255, 255, 255, 0.03) 4px),
            repeating-linear-gradient(90deg, transparent, transparent 2px, rgba(0, 0, 0, 0.02) 2px, rgba(0, 0, 0, 0.02) 4px);
          pointer-events: none;
          opacity: 0.4;
        }
        .coach-header-logo {
          flex-shrink: 0;
          width: 200px;
          height: 200px;
          margin-left: calc(25% - 350px);
          filter: drop-shadow(2px 4px 8px rgba(0,0,0,0.3));
        }
        .coach-header-logo img {
          width: 100%;
          height: 100%;
          object-fit: contain;
          display: block;
        }
        .coach-header-content {
          position: relative;
          z-index: 2;
          max-width: 500px;
          margin: 0;
          margin-right: calc(25% - 350px);
          display: flex;
          flex-direction: column;
          justify-content: center;
          height: 100%;
          text-align: right;
        }
        .coach-header-content h1 {
          font-size: 2.5rem;
          font-weight: 700;
          margin: 0.5rem 0;
          text-shadow: 2px 2px 4px rgba(0,0,0,0.4);
          white-space: nowrap;
          line-height: 1.2;
        }
        .coach-header-content .subtitle {
          font-size: 1.2rem;
          margin: 0.25rem 0;
          opacity: 0.95;
          font-weight: 300;
          text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
          line-height: 1.4;
        }
        @media (max-width: 768px) {
          .coach-header {
            min-height: 160px;
            padding: 0.8rem;
            flex-direction: column;
            text-align: center;
          }
          .coach-header-logo {
            width: 150px;
            height: 150px;
            margin-left: 0;
          }
          .coach-header-content {
            margin-right: 0;
            margin-left: 0;
            text-align: center;
          }
          .coach-header-content h1 {
            font-size: 2rem;
            white-space: nowrap;
          }
          .coach-header-content .subtitle {
            font-size: 1.1rem;
          }
        }
        @media (max-width: 480px) {
          .coach-header {
            padding: 1.2rem 0.8rem;
            min-height: 140px;
          }
          .coach-header-logo {
            width: 120px;
            height: 120px;
            margin-left: 0;
          }
          .coach-header-content h1 {
            font-size: 1.8rem;
            white-space: nowrap;
          }
        }
      `}</style>
      <div className="coach-header">
        {/* YTM Logo - Left Side */}
        <div className="coach-header-logo">
          <img 
            src="/static/images/YTM_waterColor_patch800x800_clean.webp" 
            alt="Your Training Monkey - YTM Logo"
          />
        </div>
        
        {/* Header Text - Right Side with Secondary Nav */}
        <div className="coach-header-content">
          <div style={{ textAlign: 'right', marginBottom: '1rem' }}>
            <h1>
              YTM Coach
            </h1>
            <p className="subtitle">Divergence-Optimized Training Programs for Ultrarunners</p>
          </div>
          
          {/* Secondary Navigation - Right side under header text with white border container */}
          <div style={{ 
            display: 'flex', 
            justifyContent: 'flex-end',
            marginTop: '1rem'
          }}>
            <div style={{
              border: '2px solid white',
              borderRadius: '10px',
              padding: '0.5rem',
              backgroundColor: 'rgba(255, 255, 255, 0.1)',
              backdropFilter: 'blur(10px)',
              display: 'inline-block'
            }}>
              <ul style={{
                display: 'flex',
                gap: '0.5rem',
                listStyle: 'none',
                alignItems: 'center',
                margin: 0,
                padding: 0,
                flexWrap: 'nowrap'
              }}>
                {[
                  { key: 'week', label: 'Week' },
                  { key: 'season', label: 'Season' },
                  { key: 'history', label: 'History' },
                ].map((tab) => (
                  <li key={tab.key} style={{ flexShrink: 0 }}>
                    <button
                      type="button"
                      onClick={() => {
                        setActiveSubTab(tab.key as 'week' | 'season' | 'history');
                      }}
                      style={{
                        display: 'inline-block',
                        padding: '0.6rem 1rem',
                        background: activeSubTab === tab.key 
                          ? 'rgba(255, 255, 255, 0.95)' 
                          : 'rgba(255, 255, 255, 0.7)',
                        color: activeSubTab === tab.key ? '#1B2E4B' : '#1f2937',
                        textDecoration: 'none',
                        fontWeight: activeSubTab === tab.key ? '700' : '500',
                        fontSize: activeSubTab === tab.key ? '0.95rem' : '0.9rem',
                        border: '2px solid',
                        borderColor: activeSubTab === tab.key 
                          ? 'rgba(27, 46, 75, 0.3)' 
                          : 'transparent',
                        borderRadius: '8px',
                        transition: 'all 0.3s ease',
                        boxShadow: activeSubTab === tab.key 
                          ? '0 2px 6px rgba(27, 46, 75, 0.2)' 
                          : '0 1px 3px rgba(0, 0, 0, 0.05)',
                        position: 'relative',
                        cursor: 'pointer',
                        textAlign: 'center',
                        whiteSpace: 'nowrap',
                        minWidth: 'auto'
                      }}
                      onMouseEnter={(e) => {
                        if (activeSubTab !== tab.key) {
                          e.currentTarget.style.color = '#667eea';
                          e.currentTarget.style.background = 'rgba(255, 255, 255, 0.95)';
                          e.currentTarget.style.borderColor = 'rgba(102, 126, 234, 0.3)';
                          e.currentTarget.style.transform = 'translateY(-2px)';
                          e.currentTarget.style.boxShadow = '0 4px 8px rgba(102, 126, 234, 0.15)';
                        }
                      }}
                      onMouseLeave={(e) => {
                        if (activeSubTab !== tab.key) {
                          e.currentTarget.style.color = '#1f2937';
                          e.currentTarget.style.background = 'rgba(255, 255, 255, 0.7)';
                          e.currentTarget.style.borderColor = 'transparent';
                          e.currentTarget.style.transform = 'translateY(0)';
                          e.currentTarget.style.boxShadow = '0 1px 3px rgba(0, 0, 0, 0.05)';
                        }
                      }}
                    >
                      {/* Top arrow for active tab - white */}
                      {activeSubTab === tab.key && (
                        <div style={{
                          position: 'absolute',
                          top: '-12px',
                          left: '50%',
                          transform: 'translateX(-50%)',
                          width: 0,
                          height: 0,
                          borderLeft: '10px solid transparent',
                          borderRight: '10px solid transparent',
                          borderBottom: '10px solid white',
                          filter: 'drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3))',
                          zIndex: 10
                        }}></div>
                      )}
                      {/* Center-aligned text */}
                      <span style={{ 
                        display: 'block', 
                        textAlign: 'center',
                        fontWeight: activeSubTab === tab.key ? '700' : '500',
                        fontSize: activeSubTab === tab.key ? '0.95rem' : '0.9rem',
                        letterSpacing: activeSubTab === tab.key ? '0.02em' : 'normal'
                      }}>
                        {tab.label}
                      </span>
                      {/* Bottom arrow for active tab - white */}
                      {activeSubTab === tab.key && (
                        <div style={{
                          position: 'absolute',
                          bottom: '-12px',
                          left: '50%',
                          transform: 'translateX(-50%)',
                          width: 0,
                          height: 0,
                          borderLeft: '10px solid transparent',
                          borderRight: '10px solid transparent',
                          borderTop: '10px solid white',
                          filter: 'drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3))',
                          zIndex: 10
                        }}></div>
                      )}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* ============================================================
          BOUNDARY BETWEEN HEADER AND COUNTDOWN (2px white gap)
      ============================================================ */}
      <div style={{
        height: '0.125rem', // 2px on desktop (16px base)
        backgroundColor: 'white',
        marginBottom: '0'
      }}></div>

      {/* ============================================================
          COUNTDOWN BANNER (two columns, matches phase color)
      ============================================================ */}
      {primaryRace && daysToRace !== null && (() => {
        // Get phase color for text based on training stage
        const getPhaseTextColor = (stage: string | null): string => {
          if (!stage) return '#ffffff';
          
          const stageColors: { [key: string]: string } = {
            'base': '#3498db',      // Blue (matches timeline)
            'build': '#2ecc71',     // Green (matches timeline)
            'specificity': '#f39c12', // Orange (matches timeline)
            'taper': '#e74c3c',     // Red (matches timeline)
            'peak': '#9b59b6',      // Purple (matches timeline)
            'recovery': '#95a5a6'   // Gray (matches timeline)
          };
          
          return stageColors[stage.toLowerCase()] || '#ffffff';
        };
        
        const textColor = trainingStage?.stage ? getPhaseTextColor(trainingStage.stage) : '#ffffff';
        
        return (
          <div className={styles.card} style={{ 
            marginBottom: '0 !important', // Override CSS class default margin
            padding: '1rem 1.25rem',
            background: 'radial-gradient(circle at center, #7D9CB8 0%, #4A5F7F 50%, #1B2E4B 100%)', // Radial gradient from center - medium center radiating out to darker
            display: 'flex',
            alignItems: 'center'
          }}>
            {/* 5-segment layout: 1=empty, 2=countdown, 3=empty, 4=race info, 5=empty */}
            
            {/* Segment 1: Empty (20% width) */}
            <div style={{ flex: '0 0 20%' }}></div>
            
            {/* Segment 2: Days Countdown (20% width) - Phase colored text on dark side */}
            <div style={{ flex: '0 0 20%', textAlign: 'center', color: textColor }}>
              <div style={{ fontSize: '48px', fontWeight: 'bold', lineHeight: '1' }}>
                {daysToRace}
              </div>
              <div style={{ fontSize: '16px', marginTop: '5px', opacity: 0.9 }}>
                {daysToRace === 1 ? 'day' : 'days'}
              </div>
            </div>
            
            {/* Segment 3: Empty (20% width) */}
            <div style={{ flex: '0 0 20%' }}></div>
            
            {/* Segment 4: Race Description (20% width) - Phase colored text matching countdown */}
            <div style={{ flex: '0 0 20%', color: textColor }}>
              <div style={{ fontSize: '20px', fontWeight: 'bold', marginBottom: '5px' }}>
                {primaryRace.race_name}
              </div>
              <div style={{ fontSize: '16px', opacity: 0.9 }}>
                {primaryRace.race_type} • {primaryRace.race_date} • Priority {primaryRace.priority}
              </div>
            </div>
            
            {/* Segment 5: Empty (20% width) */}
            <div style={{ flex: '0 0 20%' }}></div>
          </div>
        );
      })()}

      {/* ============================================================
          SCHEDULE REVIEW BANNER (Sunday only)
      ============================================================ */}
      {scheduleReviewStatus?.needs_review && showScheduleReviewBanner && (
        <div className={styles.card} style={{
          marginTop: '0.75rem',
          marginBottom: '0.75rem',
          padding: '1rem 1.25rem',
          backgroundColor: '#fff3cd',
          border: '2px solid #ffc107',
          borderRadius: '8px'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '1rem' }}>
            <div style={{ flex: 1 }}>
              <h3 style={{ margin: 0, marginBottom: '0.5rem', color: '#856404', fontSize: '18px', fontWeight: '600' }}>
                📅 Review Your Training Schedule for Next Week
              </h3>
              <p style={{ margin: 0, color: '#856404', fontSize: '14px' }}>
                Week of {scheduleReviewStatus.week_start ? new Date(scheduleReviewStatus.week_start).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : ''} - Confirm your availability before Sunday 6 PM
              </p>
            </div>
            <div style={{ display: 'flex', gap: '0.5rem', flexShrink: 0 }}>
              <button
                onClick={handleAcceptSchedule}
                style={{
                  padding: '10px 20px',
                  backgroundColor: '#28a745',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontSize: '14px',
                  fontWeight: '600',
                  whiteSpace: 'nowrap'
                }}
              >
                ✓ Keep Current Schedule
              </button>
              <button
                onClick={() => setActiveSubTab('schedule')}
                style={{
                  padding: '10px 20px',
                  backgroundColor: '#007bff',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontSize: '14px',
                  fontWeight: '600',
                  whiteSpace: 'nowrap'
                }}
              >
                ✏️ Update Schedule
              </button>
              <button
                onClick={handleDismissBanner}
                style={{
                  padding: '10px 15px',
                  backgroundColor: 'transparent',
                  color: '#856404',
                  border: '1px solid #856404',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontSize: '14px',
                  fontWeight: '600'
                }}
                title="Dismiss"
              >
                ✕
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ============================================================
          REVISION PROPOSAL CARD — Phase E
      ============================================================ */}
      {revisionProposal && revisionProposal.pending && (
        <div style={{ padding: '0 0.75rem' }}>
          <RevisionProposalCard
            data={revisionProposal}
            onApprove={() => {
              setRevisionProposal(null);
              fetchCoachData();
            }}
            onDismiss={() => setRevisionProposal(null)}
          />
        </div>
      )}

      {/* ============================================================
          TIMELINE VISUALIZATION (immediately below countdown with minimal gap)
      ============================================================ */}
      {trainingStage && trainingStage.timeline && trainingStage.timeline.length > 0 && (
        <>
          {/* Minimal white gap - reduced to absolute minimum */}
          <div style={{
            height: '1px', // Absolute minimum 1px
            backgroundColor: 'white',
            margin: '0',
            padding: '0',
            lineHeight: '0'
          }}></div>
          <div className={styles.card} style={{ 
            marginTop: '0 !important', 
            marginBottom: '0.125rem !important', 
            paddingTop: '0.5rem',
            paddingBottom: '0.5rem',
            paddingLeft: '1rem',
            paddingRight: '1rem'
          }}>
            <TimelineVisualization trainingStage={trainingStage} />
          </div>
        </>
      )}

      {/* ============================================================
          TAB CONTENT AREA - Route to separate pages
      ============================================================ */}
      {activeSubTab === 'week' && (
        <>
          <div className={styles.card} style={{ marginBottom: '0.75rem', padding: '0.75rem 1rem' }}>
            <WeeklyProgramDisplay
              program={weeklyProgram}
              onRefresh={fetchCoachData}
              trainingSchedule={trainingSchedule}
              weeklySynthesis={weeklySynthesis}
              onScheduleChange={() => {
                fetch('/api/coach/training-schedule')
                  .then(r => r.json())
                  .then(d => setTrainingSchedule(d.schedule || null))
                  .catch(() => {});
              }}
            />
          </div>
        </>
      )}
      {activeSubTab === 'season' && <SeasonPage />}
      {activeSubTab === 'history' && <RaceHistoryPage />}

    </div>
  );
};

export default CoachPage;

