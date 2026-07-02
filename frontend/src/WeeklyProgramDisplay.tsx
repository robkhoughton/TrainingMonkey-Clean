import React, { useState, useEffect } from 'react';
import styles from './TrainingLoadDashboard.module.css';
import ChatWidget from './ChatWidget';
import TrainingScheduleConfig from './TrainingScheduleConfig';

// ============================================================================
// INTERFACES
// ============================================================================

interface DailyWorkout {
  day: string;
  date: string;
  workout_type: string;
  description: string;
  duration_estimate: string;
  intensity: string;
  key_focus: string;
  terrain_notes?: string;
  distance_miles?: number;
  elevation_gain_feet?: number;
}

interface AutopsyData {
  alignment_score: number;
  date: string;
}

interface WeeklySynthesisData {
  synthesis: string | null;
  week_start: string | null;
  generated_at: string | null;
  strategic_summary: string | null;
  alignment_score?: number | null;
  quality_score?: number | null;
  composite_score?: number | null;
  reflection?: string | null;
}

interface WeeklyProgram {
  week_start_date: string;
  week_summary: string;
  predicted_metrics: {
    acwr_estimate: number;
    internal_acwr_estimate?: number;
    external_acwr_estimate?: number;
    divergence_estimate: number;
    total_weekly_miles: number;
    total_weekly_elevation_feet?: number;
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

interface WeeklyProgramDisplayProps {
  program: WeeklyProgram | null;
  onRefresh: () => void;
  trainingSchedule?: TrainingSchedule | null;
  onScheduleChange?: () => void;
  weeklySynthesis?: WeeklySynthesisData | null;
}

// ── Week in Review helpers ──────────────────────────────────────────────────
// Lens accents: RX alignment in the app's blue-gray, productive work in brand sage.
const LENS = {
  alignment: { rule: '#7D9CB8', chip: '#7D9CB8' },
  quality: { rule: '#6B8F7F', chip: '#6B8F7F' },
};

/** Split the merged dual-track synthesis into its two narratives. Backend stores
 *  `<alignment>\n\n<productive work>`, each led by a section header. Falls back to a
 *  single narrative (older single-track rows) when the productive-work marker is absent. */
function splitTracks(text: string): { alignment: string; quality: string } {
  const idx = text.search(/PRODUCTIVE WORK/i);
  if (idx > 0) {
    return {
      alignment: text.slice(0, idx).replace(/ALIGNMENT ASSESSMENT:?/i, '').trim(),
      quality: text.slice(idx).replace(/PRODUCTIVE WORK:?/i, '').trim(),
    };
  }
  return { alignment: text.replace(/ALIGNMENT ASSESSMENT:?/i, '').trim(), quality: '' };
}

function formatWeekRange(weekStart: string | null): string {
  if (!weekStart) return '';
  const start = new Date(weekStart + 'T12:00:00');
  const end = new Date(start);
  end.setDate(end.getDate() + 6);
  const s = start.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  const e = end.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  return `${s} – ${e}`;
}

/** One verdict lens — colored rule, label + score chip, then the narrative. */
const ReviewLens: React.FC<{
  label: string;
  score?: number | null;
  accent: { rule: string; chip: string };
  body: string;
}> = ({ label, score, accent, body }) => (
  <div style={{ borderLeft: `3px solid ${accent.rule}`, paddingLeft: '0.85rem' }}>
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '0.5rem', marginBottom: '0.4rem' }}>
      <span style={{ fontSize: '0.72rem', fontWeight: 700, color: '#1B2E4B', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
        {label}
      </span>
      {score != null && (
        <span style={{ fontSize: '0.72rem', fontWeight: 700, color: 'white', background: accent.chip, borderRadius: '10px', padding: '2px 9px', lineHeight: 1.5, whiteSpace: 'nowrap' }}>
          {score}/10
        </span>
      )}
    </div>
    <p style={{ margin: 0, fontSize: '13px', lineHeight: 1.65, color: '#374151', textAlign: 'left' }}>
      {body}
    </p>
  </div>
);

// ============================================================================
// COMPONENT
// ============================================================================

const WeeklyProgramDisplay: React.FC<WeeklyProgramDisplayProps> = ({ program, onRefresh, trainingSchedule, onScheduleChange, weeklySynthesis }) => {
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [autopsyScores, setAutopsyScores] = useState<Record<string, number>>({});

  // Week in Review reflection state
  const [reflectionText, setReflectionText] = useState('');
  const [reflectionEditing, setReflectionEditing] = useState(false);
  const [reflectionSubmitting, setReflectionSubmitting] = useState(false);
  const [reflectionError, setReflectionError] = useState<string | null>(null);

  const handleSubmitReflection = async () => {
    const reflection = reflectionText.trim();
    if (!reflection) return;
    setReflectionSubmitting(true);
    setReflectionError(null);
    try {
      const res = await fetch('/api/coach/weekly-program/reflection', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reflection }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.error || 'Could not rebuild your week. Try again.');
      }
      setReflectionEditing(false);
      onRefresh();
    } catch (err) {
      setReflectionError(err instanceof Error ? err.message : 'Could not rebuild your week. Try again.');
    } finally {
      setReflectionSubmitting(false);
    }
  };

  // Fetch autopsy alignment scores for the week
  useEffect(() => {
    if (!program) return;

    const fetchAutopsyScores = async () => {
      try {
        // Calculate week date range
        const weekStart = new Date(program.week_start_date);
        const weekEnd = new Date(weekStart);
        weekEnd.setDate(weekEnd.getDate() + 6);

        // Fetch journal entries for the week (which contain autopsy data)
        const response = await fetch(`/api/journal?days=7&date_from=${program.week_start_date}`);
        if (!response.ok) return;

        const result = await response.json();
        if (!result.success) return;

        // Extract autopsy scores by date
        const scores: Record<string, number> = {};
        result.data.forEach((entry: { date: string; ai_autopsy?: AutopsyData }) => {
          if (entry.ai_autopsy?.alignment_score) {
            scores[entry.date] = entry.ai_autopsy.alignment_score;
          }
        });

        setAutopsyScores(scores);
      } catch (err) {
        console.error('Error fetching autopsy scores:', err);
      }
    };

    fetchAutopsyScores();
  }, [program]);

  // ============================================================================
  // HANDLERS
  // ============================================================================

  const handleRegenerate = async () => {
    if (!window.confirm('Generate a new weekly program? This will also refresh last week\'s synthesis.')) {
      return;
    }

    setIsRegenerating(true);
    setError(null);

    try {
      // Run plan generation and synthesis refresh in parallel
      const [programRes] = await Promise.all([
        fetch('/api/coach/weekly-program/generate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({})
        }),
        fetch('/api/coach/weekly-synthesis/generate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({})
        }).catch(() => null)  // synthesis failure is non-fatal
      ]);

      if (!programRes.ok) {
        const errorData = await programRes.json();
        throw new Error(errorData.error || 'Failed to generate program');
      }

      onRefresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate program');
    } finally {
      setIsRegenerating(false);
    }
  };

  // ============================================================================
  // HELPERS
  // ============================================================================

  const getIntensityColor = (intensity: string): string => {
    if (!intensity) return '#95a5a6';
    switch (intensity.toLowerCase()) {
      case 'low': return '#2ecc71'; // green
      case 'moderate': return '#f39c12'; // orange
      case 'high': return '#e74c3c'; // red
      default: return '#95a5a6';
    }
  };

  const getWorkoutTypeIcon = (workoutType: string): string => {
    if (!workoutType) return '🏃';
    const type = workoutType.toLowerCase();
    if (type.includes('long')) return '🏃‍♂️';
    if (type.includes('tempo')) return '⚡';
    if (type.includes('interval') || type.includes('speed')) return '🔥';
    if (type.includes('hill')) return '⛰️';
    if (type.includes('easy') || type.includes('recovery')) return '😌';
    if (type.includes('rest')) return '💤';
    if (type.includes('cross')) return '🚴';
    if (type.includes('strength')) return '💪';
    if (type.includes('race')) return '🏁';
    return '🏃';
  };

  const formatDate = (dateStr: string): string => {
    const date = new Date(dateStr + 'T12:00:00');
    return date.toLocaleDateString('en-US', {
      weekday: 'short', 
      month: 'short', 
      day: 'numeric' 
    });
  };

  const getACWRColor = (acwr: number): string => {
    if (acwr < 0.8) return '#3498db'; // blue - low load
    if (acwr <= 1.3) return '#2ecc71'; // green - optimal
    if (acwr <= 1.5) return '#f39c12'; // orange - moderate risk
    return '#e74c3c'; // red - high risk
  };

  const getDivergenceColor = (div: number): string => {
    if (Math.abs(div) <= 0.15) return '#2ecc71'; // green - optimal
    if (Math.abs(div) <= 0.30) return '#f39c12'; // orange - moderate
    return '#e74c3c'; // red - high
  };

  // ============================================================================
  // RENDER
  // ============================================================================

  if (!program) {
    return (
      <div>
        <h2 className={styles.cardHeader}>Workout Plan</h2>
        <div style={{ textAlign: 'center', padding: '40px 20px', color: '#95a5a6' }}>
          <p style={{ fontSize: '18px', marginBottom: '15px' }}>No weekly program loaded</p>
          <p style={{ fontSize: '14px', marginBottom: '20px' }}>
            Complete your profile (race goals, schedule) to generate your first program!
          </p>
        </div>
      </div>
    );
  }

  // Format date for header (e.g., "Dec 1, 2025")
  const formatHeaderDate = (dateStr: string): string => {
    const date = new Date(dateStr + 'T12:00:00');
    return date.toLocaleDateString('en-US', {
      month: 'short', 
      day: 'numeric',
      year: 'numeric'
    });
  };

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
      {/* Header - Prominent */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center', 
        marginBottom: '1rem',
        paddingBottom: '0.75rem',
        borderBottom: '2px solid #e1e8ed'
      }}>
        <div>
          <h2 style={{
            fontSize: '24px',
            fontWeight: '700',
            color: '#2c3e50',
            margin: 0,
            marginBottom: '0.25rem'
          }}>
            Your Next 7 Days — from {formatHeaderDate(program.week_start_date)}
          </h2>
          {program.from_cache && (
            <span style={{ 
              marginLeft: '0',
              padding: '2px 8px', 
              backgroundColor: '#e8f4f8', 
              borderRadius: '10px',
              fontSize: '11px',
              color: '#555'
            }}>
              Cached
            </span>
          )}
        </div>
        <button
          onClick={handleRegenerate}
          disabled={isRegenerating}
          style={{
            padding: '8px 16px',
            backgroundColor: '#9b59b6',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: isRegenerating ? 'not-allowed' : 'pointer',
            fontSize: '13px',
            fontWeight: '600',
            opacity: isRegenerating ? 0.6 : 1
          }}
        >
          {isRegenerating ? '⏳ Generating...' : '🔄 Regenerate Program'}
        </button>
      </div>

      {/* Error Display */}
      {error && (
        <div style={{
          padding: '15px',
          backgroundColor: '#fee',
          border: '1px solid #fcc',
          borderRadius: '4px',
          marginBottom: '15px',
          color: '#c33'
        }}>
          {error}
        </div>
      )}

      {/* Reflect & Plan — two columns: Last Week (dual-track review) | This Coming Week + reflection */}
      <div style={{
        borderRadius: '8px',
        marginBottom: '1rem',
        border: '1px solid #e1e8ed',
        overflow: 'hidden',
      }}>
        <div style={{
          background: 'linear-gradient(90deg, #E6F0FF 0%, #7D9CB8 50%, #1B2E4B 100%)',
          padding: '8px 16px',
        }}>
          <span style={{ fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.12em', color: '#1B2E4B', textTransform: 'uppercase' }}>
            Reflect &amp; Plan
          </span>
        </div>
        <div style={{ backgroundColor: 'white' }}>
          {/* Two columns: Last Week (dual-track review) | This Coming Week */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))' }}>
            {/* LAST WEEK — dual-track verdict */}
            <div style={{ padding: '1rem', borderRight: '1px solid #e1e8ed', minWidth: 0 }}>
              <div style={{ fontSize: '0.72rem', fontWeight: 700, color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '0.75rem' }}>
                Last Week
                {weeklySynthesis?.week_start && (
                  <span style={{ fontWeight: 400, marginLeft: '6px', textTransform: 'none', letterSpacing: 0 }}>
                    · {formatWeekRange(weeklySynthesis.week_start)}
                  </span>
                )}
                {weeklySynthesis?.composite_score != null && (
                  <span style={{ fontWeight: 400, marginLeft: '6px', textTransform: 'none', letterSpacing: 0, color: '#6b7280' }}>
                    · composite {weeklySynthesis.composite_score.toFixed(1)}
                  </span>
                )}
              </div>

              {weeklySynthesis?.synthesis ? (
                (() => {
                  const ws = weeklySynthesis!;
                  const { alignment, quality } = splitTracks(ws.synthesis || '');
                  return (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.9rem' }}>
                      <ReviewLens label="RX Alignment" score={ws.alignment_score} accent={LENS.alignment} body={alignment} />
                      {quality && (
                        <ReviewLens label="Productive Work" score={ws.quality_score} accent={LENS.quality} body={quality} />
                      )}
                    </div>
                  );
                })()
              ) : (
                <p style={{ margin: 0, fontSize: '13px', color: '#9ca3af', fontStyle: 'italic', lineHeight: '1.6' }}>
                  Your review unlocks Saturday evening, once the week closes and your coach reads it back.
                </p>
              )}
            </div>

            {/* THIS COMING WEEK + your reflection */}
            <div style={{ padding: '1rem', minWidth: 0 }}>
              <div style={{ fontSize: '0.72rem', fontWeight: 700, color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '0.75rem' }}>
                This Coming Week
              </div>
              <p style={{ margin: 0, fontSize: '13px', lineHeight: '1.65', color: '#374151', textAlign: 'left' }}>
                {program.week_summary}
              </p>

              {/* Your reflection — the athlete's reply, only when there's a review to react to */}
              {weeklySynthesis?.synthesis && (() => {
                const ws = weeklySynthesis!;
                const existing = (ws.reflection || '').trim();
                const showReadback = existing && !reflectionEditing;
                return (
                  <div style={{ marginTop: '1.5rem', paddingTop: '1.25rem', borderTop: '1px solid #e1e8ed' }}>
                    <label
                      htmlFor="week-reflection"
                      style={{ display: 'block', fontSize: '0.9rem', fontWeight: 700, color: '#2c3e50', marginBottom: '0.2rem', textAlign: 'left' }}
                    >
                      How did your week go?
                    </label>
                    <p style={{ margin: '0 0 0.65rem', fontSize: '13px', color: '#6b7280', textAlign: 'left', maxWidth: '70ch', lineHeight: 1.6 }}>
                      Tell me what the data misses — how sessions actually felt, life stress, niggles, and what you want from next week.
                    </p>

                    {showReadback ? (
                      <div style={{ borderLeft: '3px solid #7D9CB8', paddingLeft: '0.85rem', fontSize: '13px', lineHeight: 1.65, color: '#374151', textAlign: 'left', maxWidth: '75ch' }}>
                        <div style={{ fontSize: '0.7rem', fontWeight: 700, color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '0.35rem' }}>
                          Your review — shaped this week's plan
                        </div>
                        {existing}
                        <div>
                          <button
                            type="button"
                            onClick={() => { setReflectionText(existing); setReflectionEditing(true); }}
                            style={{ marginTop: '0.6rem', background: 'none', border: 'none', padding: 0, color: '#2563eb', fontSize: '13px', fontWeight: 600, cursor: 'pointer', textDecoration: 'underline' }}
                          >
                            Edit &amp; rebuild
                          </button>
                        </div>
                      </div>
                    ) : (
                      <>
                        <textarea
                          id="week-reflection"
                          value={reflectionText}
                          onChange={(e) => setReflectionText(e.target.value)}
                          disabled={reflectionSubmitting}
                          rows={4}
                          placeholder="e.g. Tuesday's tempo felt flat — work was brutal. Legs are good though; happy to push the long run if you want."
                          style={{ width: '100%', boxSizing: 'border-box', padding: '0.7rem 0.8rem', fontSize: '14px', lineHeight: 1.6, color: '#374151', fontFamily: 'inherit', border: '1px solid #e1e8ed', borderRadius: '8px', resize: 'vertical', minHeight: '92px' }}
                        />
                        {reflectionError && (
                          <p style={{ margin: '0.5rem 0 0', fontSize: '13px', color: '#c0392b', textAlign: 'left' }}>{reflectionError}</p>
                        )}
                        <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '0.7rem' }}>
                          <button
                            type="button"
                            onClick={handleSubmitReflection}
                            disabled={reflectionSubmitting || !reflectionText.trim()}
                            style={{ padding: '9px 18px', background: '#FF5722', color: 'white', border: 'none', borderRadius: '8px', fontSize: '14px', fontWeight: 700, cursor: reflectionSubmitting || !reflectionText.trim() ? 'not-allowed' : 'pointer', opacity: reflectionSubmitting || !reflectionText.trim() ? 0.55 : 1, transition: 'opacity 0.15s ease' }}
                          >
                            {reflectionSubmitting ? 'Rebuilding your week…' : 'Save & rebuild my week →'}
                          </button>
                        </div>
                      </>
                    )}
                  </div>
                );
              })()}
            </div>
          </div>
        </div>
      </div>

      {/* Predicted Metrics */}
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', 
        gap: '0.75rem', 
        marginBottom: '1rem' 
      }}>
        <div style={{
          padding: '0.75rem',
          backgroundColor: getACWRColor(program.predicted_metrics.acwr_estimate),
          color: 'white',
          borderRadius: '8px',
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '11px', opacity: 0.75, marginBottom: '4px', letterSpacing: '0.06em' }}>Predicted ACWR</div>
          {(program.predicted_metrics.external_acwr_estimate != null || program.predicted_metrics.internal_acwr_estimate != null) ? (
            <div style={{ display: 'flex', justifyContent: 'center', gap: '12px' }}>
              <div>
                <div style={{ fontSize: '18px', fontWeight: 'bold', lineHeight: 1 }}>
                  {(program.predicted_metrics.external_acwr_estimate ?? program.predicted_metrics.acwr_estimate).toFixed(2)}
                </div>
                <div style={{ fontSize: '10px', opacity: 0.75, marginTop: '2px' }}>External</div>
              </div>
              <div style={{ width: '1px', backgroundColor: 'rgba(255,255,255,0.3)' }} />
              <div>
                <div style={{ fontSize: '18px', fontWeight: 'bold', lineHeight: 1 }}>
                  {(program.predicted_metrics.internal_acwr_estimate ?? program.predicted_metrics.acwr_estimate).toFixed(2)}
                </div>
                <div style={{ fontSize: '10px', opacity: 0.75, marginTop: '2px' }}>Internal</div>
              </div>
            </div>
          ) : (
            <div style={{ fontSize: '20px', fontWeight: 'bold' }}>
              {program.predicted_metrics.acwr_estimate.toFixed(2)}
            </div>
          )}
        </div>

        <div style={{
          padding: '0.75rem',
          backgroundColor: getDivergenceColor(program.predicted_metrics.divergence_estimate),
          color: 'white',
          borderRadius: '8px',
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '20px', fontWeight: 'bold', marginBottom: '3px' }}>
            {program.predicted_metrics.divergence_estimate.toFixed(3)}
          </div>
          <div style={{ fontSize: '11px', opacity: 0.9 }}>Predicted Divergence</div>
        </div>

        <div style={{
          padding: '0.75rem',
          backgroundColor: '#3498db',
          color: 'white',
          borderRadius: '8px',
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '20px', fontWeight: 'bold', marginBottom: '3px' }}>
            {program.predicted_metrics.total_weekly_miles.toFixed(1)}
          </div>
          <div style={{ fontSize: '11px', opacity: 0.9 }}>Planned Miles</div>
          {program.predicted_metrics.total_weekly_elevation_feet != null && program.predicted_metrics.total_weekly_elevation_feet > 0 && (
            <div style={{ fontSize: '11px', opacity: 0.8, marginTop: '2px' }}>
              +{program.predicted_metrics.total_weekly_elevation_feet.toLocaleString()} ft vert
            </div>
          )}
        </div>
      </div>

      {/* 2-Column Layout: Workout Cards (Left) + Notes (Right) */}
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'minmax(0, 1fr) 380px',
        gap: '1.5rem',
        marginBottom: '1rem'
      }}>
        {/* LEFT COLUMN: Daily Workout Cards */}
        <div style={{ display: 'grid', gap: '0.75rem', minWidth: 0 }}>
          {program.daily_program.map((workout, index) => {
            // Use noon UTC to prevent UTC→local timezone shift on date-only strings.
            // Without this, '2026-03-24' parses as UTC midnight which becomes Mar 23 in Pacific time.
            const workoutDate = new Date(workout.date + 'T12:00:00');
            const today = new Date();
            today.setHours(0, 0, 0, 0);
            workoutDate.setHours(0, 0, 0, 0);
            
            const isToday = workoutDate.getTime() === today.getTime();
            const isPast = workoutDate < today;
            
            // Get autopsy score for past days
            const autopsyScore = autopsyScores[workout.date];
            const hasAutopsy = isPast && autopsyScore !== undefined;
            
            // Determine if this is a key workout (moderate or high intensity)
            const isKeyWorkout = workout.intensity && 
              (workout.intensity.toLowerCase() === 'moderate' || workout.intensity.toLowerCase() === 'high');
            
            return (
              <div
                key={index}
                style={{
                  border: isToday ? '3px solid #f39c12' : '1px solid #e1e8ed',
                  borderRadius: '8px',
                  padding: '0.75rem',
                  backgroundColor: isToday ? '#fff9e6' : isPast ? '#f8f9fa' : 'white',
                  position: 'relative',
                  opacity: isPast && !hasAutopsy ? 0.7 : 1
                }}
              >
              {/* Today Badge with Journal Link */}
              {isToday && (
                <a
                  href="/dashboard?tab=journal"
                  style={{
                    position: 'absolute',
                    top: '10px',
                    right: '10px',
                    padding: '6px 14px',
                    backgroundColor: '#f39c12',
                    color: 'white',
                    borderRadius: '12px',
                    fontSize: '12px',
                    fontWeight: 'bold',
                    textDecoration: 'none',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px'
                  }}
                  title="View today's detailed training decision on Journal page"
                >
                  TODAY → JOURNAL
                </a>
              )}
              
              {/* Key Workout Badge (for moderate/high intensity workouts) */}
              {isKeyWorkout && !isToday && !hasAutopsy && (
                <div style={{
                  position: 'absolute',
                  top: '10px',
                  right: '10px',
                  padding: '6px 12px',
                  backgroundColor: '#ffc107',
                  color: '#856404',
                  borderRadius: '12px',
                  fontSize: '11px',
                  fontWeight: 'bold',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  border: '1px solid #856404'
                }}
                title="Key workout this week"
              >
                ⭐ KEY WORKOUT
              </div>
              )}
              
              {/* Autopsy Alignment Badge for Past Days */}
              {hasAutopsy && (
                <div style={{
                  position: 'absolute',
                  top: '10px',
                  right: '10px',
                  padding: '6px 12px',
                  backgroundColor: autopsyScore >= 8 ? '#27ae60' : autopsyScore >= 6 ? '#f39c12' : '#e74c3c',
                  color: 'white',
                  borderRadius: '12px',
                  fontSize: '11px',
                  fontWeight: 'bold',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px'
                }}
                title={`Autopsy alignment score: ${autopsyScore}/10`}
              >
                📋 {autopsyScore}/10
                </div>
              )}

              {/* Workout Header: Day, Icon, Type, Intensity, Duration */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.75rem' }}>
                {/* Day of Week and Date */}
                <div style={{ 
                  minWidth: '70px',
                  textAlign: 'left'
                }}>
                  <div style={{
                    fontSize: '14px',
                    fontWeight: '700',
                    color: '#2c3e50',
                    lineHeight: '1.2'
                  }}>
                    {new Date(workout.date + 'T12:00:00').toLocaleDateString('en-US', { weekday: 'long' })}
                  </div>
                  <div style={{
                    fontSize: '12px',
                    color: '#7f8c8d',
                    lineHeight: '1.2'
                  }}>
                    {formatDate(workout.date)}
                  </div>
                </div>
                
                <div style={{ fontSize: '28px' }}>
                  {getWorkoutTypeIcon(workout.workout_type)}
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{
                    fontSize: '15px',
                    fontWeight: '600',
                    color: '#555',
                    textAlign: 'left'
                  }}>
                    {workout.workout_type}
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{
                    padding: '3px 8px',
                    backgroundColor: getIntensityColor(workout.intensity),
                    color: 'white',
                    borderRadius: '12px',
                    fontSize: '11px',
                    fontWeight: 'bold',
                    marginBottom: '3px'
                  }}>
                    {workout.intensity.toUpperCase()}
                  </div>
                  <div style={{ fontSize: '11px', color: '#7f8c8d' }}>
                    {workout.duration_estimate}
                  </div>
                  {(workout.distance_miles != null && workout.distance_miles > 0) && (
                    <div style={{ fontSize: '11px', color: '#7f8c8d', marginTop: '2px' }}>
                      {workout.distance_miles.toFixed(1)} mi
                      {workout.elevation_gain_feet != null && workout.elevation_gain_feet > 0
                        ? ` · +${workout.elevation_gain_feet.toLocaleString()} ft`
                        : ''}
                    </div>
                  )}
                </div>
              </div>

              {/* Description */}
              <div style={{
                fontSize: '14px',
                color: '#555',
                marginBottom: '0.75rem',
                lineHeight: '1.6',
                textAlign: 'left'
              }}>
                {workout.description}
              </div>

              {/* Key Focus */}
              <div style={{
                padding: '0.75rem',
                backgroundColor: '#e8f4f8',
                borderRadius: '6px',
                fontSize: '13px',
                color: '#555',
                marginBottom: workout.terrain_notes ? '0.5rem' : 0,
                textAlign: 'left',
                lineHeight: '1.6'
              }}>
                <strong>Focus:</strong> {workout.key_focus}
              </div>

              {/* Terrain Notes */}
              {workout.terrain_notes && (
                <div style={{
                  fontSize: '13px',
                  color: '#7f8c8d',
                  fontStyle: 'italic',
                  textAlign: 'left'
                }}>
                  🗺️ {workout.terrain_notes}
                </div>
              )}
            </div>
          );
        })}
        </div>

        {/* RIGHT COLUMN: Weekly Notes (Sticky) */}
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '0.75rem',
          position: 'sticky',
          top: '20px',
          alignSelf: 'start'
        }}>
          {/* Chat Widget */}
          <ChatWidget />

          {/* Nutrition Reminder */}
          {program.nutrition_reminder && (
            <div style={{
              padding: '0.75rem',
              backgroundColor: '#d1f2eb',
              border: '1px solid #a8e6cf',
              borderRadius: '8px'
            }}>
              <h3 style={{ marginTop: 0, marginBottom: '0.5rem', fontSize: '13px', color: '#0e6655', fontWeight: '600' }}>
                Nutrition Reminder
              </h3>
              <p style={{ margin: 0, fontSize: '13px', color: '#0e6655', lineHeight: '1.6', textAlign: 'left' }}>
                {program.nutrition_reminder}
              </p>
            </div>
          )}

          {/* Injury Prevention Note */}
          {program.injury_prevention_note && (
            <div style={{
              padding: '0.75rem',
              backgroundColor: '#fce4ec',
              border: '1px solid #f8bbd0',
              borderRadius: '8px'
            }}>
              <h3 style={{ marginTop: 0, marginBottom: '0.5rem', fontSize: '13px', color: '#c2185b', fontWeight: '600' }}>
                Injury Prevention
              </h3>
              <p style={{ margin: 0, fontSize: '13px', color: '#c2185b', lineHeight: '1.6', textAlign: 'left' }}>
                {program.injury_prevention_note}
              </p>
            </div>
          )}

          {/* Training Availability */}
          <TrainingScheduleConfig
            schedule={trainingSchedule ?? null}
            onScheduleChange={onScheduleChange ?? (() => {})}
          />

          {/* Helper Note */}
          <div style={{
            padding: '0.75rem',
            backgroundColor: '#f8f9fa',
            borderRadius: '6px',
            fontSize: '12px',
            color: '#7f8c8d',
            textAlign: 'left',
            lineHeight: '1.5'
          }}>
            This program is optimized for your{' '}
            <a 
              href="/dashboard?tab=coach&subtab=goals" 
              style={{ color: '#007bff', textDecoration: 'underline', cursor: 'pointer' }}
            >
              race goals
            </a>
            , current fitness, and{' '}
            <a 
              href="/dashboard?tab=coach&subtab=schedule" 
              style={{ color: '#007bff', textDecoration: 'underline', cursor: 'pointer' }}
            >
              weekly schedule
            </a>
            . Adjust as needed based on how you feel!
          </div>
        </div>
      </div>
    </div>
  );
};

export default WeeklyProgramDisplay;

