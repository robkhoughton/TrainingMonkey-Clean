import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom';
import styles from './TrainingLoadDashboard.module.css';

// ============================================================================
// INTERFACES
// ============================================================================

interface CrossTrainingDiscipline {
  discipline: string;
  enabled: boolean;
  allocation_type: 'hours' | 'percentage';
  allocation_value: number;
}

interface TrainingSchedule {
  schedule: {
    total_hours_per_week?: number;
    available_days?: string[];
    long_run_days?: string[];
    constraints?: string;
  } | null;
  include_strength: boolean;
  strength_hours: number;
  include_mobility: boolean;
  mobility_hours: number;
  cross_training_disciplines?: CrossTrainingDiscipline[];
  // Legacy fields for backward compatibility
  include_cross_training?: boolean;
  cross_training_type?: string | null;
  cross_training_hours?: number;
}

interface TrainingScheduleConfigProps {
  schedule: TrainingSchedule | null;
  onScheduleChange: () => void;
}

// ============================================================================
// CONSTANTS
// ============================================================================

const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

const AVAILABLE_DISCIPLINES = [
  { key: 'cycling', label: 'Cycling' },
  { key: 'swimming', label: 'Swimming' },
  { key: 'rowing', label: 'Rowing' },
  { key: 'backcountry_skiing', label: 'Backcountry Skiing' },
  { key: 'hiking', label: 'Hiking' },
  { key: 'other', label: 'Other' }
];

// ============================================================================
// COMPONENT
// ============================================================================

const TrainingScheduleConfig: React.FC<TrainingScheduleConfigProps> = ({ schedule, onScheduleChange }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Form state
  const [totalHours, setTotalHours] = useState<number>(10);
  const [availableDays, setAvailableDays] = useState<string[]>(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']);
  const [longRunDays, setLongRunDays] = useState<string[]>(['Saturday', 'Sunday']);
  const [constraints, setConstraints] = useState<string>('');

  // Supplemental training
  const [includeStrength, setIncludeStrength] = useState<boolean>(false);
  const [strengthHours, setStrengthHours] = useState<number>(2);
  const [includeMobility, setIncludeMobility] = useState<boolean>(false);
  const [mobilityHours, setMobilityHours] = useState<number>(1);
  const [crossTrainingDisciplines, setCrossTrainingDisciplines] = useState<CrossTrainingDiscipline[]>([]);

  // ============================================================================
  // LOAD EXISTING SCHEDULE
  // ============================================================================

  useEffect(() => {
    if (schedule) {
      if (schedule.schedule) {
        setTotalHours(schedule.schedule.total_hours_per_week || 10);
        setAvailableDays(schedule.schedule.available_days || []);
        setLongRunDays(schedule.schedule.long_run_days || ['Saturday', 'Sunday']);

        // Convert constraints array to text (one per line)
        const constraintsArray = schedule.schedule.constraints;
        if (Array.isArray(constraintsArray)) {
          const constraintsText = constraintsArray
            .map((c: any) => c.description || c)
            .filter((line: string) => line)
            .join('\n');
          setConstraints(constraintsText);
        } else {
          setConstraints(constraintsArray || '');
        }
      }

      setIncludeStrength(schedule.include_strength);
      setStrengthHours(schedule.strength_hours);
      setIncludeMobility(schedule.include_mobility);
      setMobilityHours(schedule.mobility_hours);

      // Load multi-discipline cross-training
      if (schedule.cross_training_disciplines && schedule.cross_training_disciplines.length > 0) {
        setCrossTrainingDisciplines(schedule.cross_training_disciplines);
      } else if (schedule.include_cross_training && schedule.cross_training_type) {
        // Migrate legacy single discipline
        setCrossTrainingDisciplines([{
          discipline: schedule.cross_training_type.toLowerCase().replace(' ', '_'),
          enabled: true,
          allocation_type: 'hours',
          allocation_value: schedule.cross_training_hours || 2
        }]);
      } else {
        setCrossTrainingDisciplines([]);
      }
    }
  }, [schedule]);

  // ============================================================================
  // HANDLERS
  // ============================================================================

  const handleEdit = () => {
    setIsEditing(true);
    setError(null);
    setSuccessMessage(null);
  };

  const handleCancel = () => {
    setIsEditing(false);
    setError(null);
    setSuccessMessage(null);
    // Reset to existing values
    if (schedule) {
      if (schedule.schedule) {
        setTotalHours(schedule.schedule.total_hours_per_week || 10);
        setAvailableDays(schedule.schedule.available_days || []);
        setLongRunDays(schedule.schedule.long_run_days || ['Saturday', 'Sunday']);

        // Convert constraints array to text
        const constraintsArray = schedule.schedule.constraints;
        if (Array.isArray(constraintsArray)) {
          const constraintsText = constraintsArray
            .map((c: any) => c.description || c)
            .filter((line: string) => line)
            .join('\n');
          setConstraints(constraintsText);
        } else {
          setConstraints(constraintsArray || '');
        }
      }
      setIncludeStrength(schedule.include_strength);
      setStrengthHours(schedule.strength_hours);
      setIncludeMobility(schedule.include_mobility);
      setMobilityHours(schedule.mobility_hours);

      // Reset cross-training disciplines
      if (schedule.cross_training_disciplines && schedule.cross_training_disciplines.length > 0) {
        setCrossTrainingDisciplines(schedule.cross_training_disciplines);
      } else if (schedule.include_cross_training && schedule.cross_training_type) {
        // Migrate legacy single discipline
        setCrossTrainingDisciplines([{
          discipline: schedule.cross_training_type.toLowerCase().replace(' ', '_'),
          enabled: true,
          allocation_type: 'hours',
          allocation_value: schedule.cross_training_hours || 2
        }]);
      } else {
        setCrossTrainingDisciplines([]);
      }
    }
  };

  const handleDayToggle = (day: string) => {
    if (availableDays.includes(day)) {
      setAvailableDays(availableDays.filter(d => d !== day));
      // Also remove from long run days if it was selected
      setLongRunDays(longRunDays.filter(d => d !== day));
    } else {
      setAvailableDays([...availableDays, day]);
    }
  };

  const handleLongRunDayToggle = (day: string) => {
    if (longRunDays.includes(day)) {
      setLongRunDays(longRunDays.filter(d => d !== day));
    } else {
      setLongRunDays([...longRunDays, day]);
    }
  };

  const handleDisciplineToggle = (disciplineKey: string) => {
    setCrossTrainingDisciplines(prev => {
      const existing = prev.find(d => d.discipline === disciplineKey);
      if (existing) {
        // Toggle off - remove from list
        return prev.filter(d => d.discipline !== disciplineKey);
      } else {
        // Toggle on - add with defaults
        return [...prev, {
          discipline: disciplineKey,
          enabled: true,
          allocation_type: 'hours',
          allocation_value: 2
        }];
      }
    });
  };

  const handleDisciplineUpdate = (disciplineKey: string, field: 'allocation_type' | 'allocation_value', value: any) => {
    setCrossTrainingDisciplines(prev =>
      prev.map(d =>
        d.discipline === disciplineKey
          ? { ...d, [field]: value }
          : d
      )
    );
  };

  const handleSubmit = async () => {
    setIsSaving(true);
    setError(null);
    setSuccessMessage(null);

    // Validation
    if (totalHours <= 0 || totalHours > 100) {
      setError('Total weekly hours must be between 1 and 100');
      setIsSaving(false);
      return;
    }

    if (availableDays.length === 0) {
      setError('Please select at least one training day');
      setIsSaving(false);
      return;
    }

    // Calculate total supplemental hours including cross-training
    let crossTrainingHoursTotal = 0;
    crossTrainingDisciplines.forEach(d => {
      if (d.enabled) {
        if (d.allocation_type === 'hours') {
          crossTrainingHoursTotal += d.allocation_value;
        } else {
          // Convert percentage to hours
          crossTrainingHoursTotal += (d.allocation_value / 100) * totalHours;
        }
      }
    });

    const totalSupplementalHours =
      (includeStrength ? strengthHours : 0) +
      (includeMobility ? mobilityHours : 0) +
      crossTrainingHoursTotal;

    if (totalSupplementalHours > totalHours) {
      setError('Supplemental training hours cannot exceed total weekly hours');
      setIsSaving(false);
      return;
    }

    try {
      // Convert constraints text to array of constraint objects
      const constraintsList = constraints.trim()
        ? constraints.trim().split('\n').filter(line => line.trim()).map(line => ({
            description: line.trim()
          }))
        : [];

      const payload = {
        training_schedule: {
          total_hours_per_week: totalHours,
          available_days: availableDays,
          long_run_days: longRunDays,
          constraints: constraintsList
        },
        include_strength_training: includeStrength,
        strength_hours_per_week: includeStrength ? strengthHours : 0,
        include_mobility: includeMobility,
        mobility_hours_per_week: includeMobility ? mobilityHours : 0,
        cross_training_disciplines: crossTrainingDisciplines.filter(d => d.enabled)
      };

      const response = await fetch('/api/coach/training-schedule', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to save training schedule');
      }

      setSuccessMessage('Training schedule saved successfully!');
      setIsEditing(false);
      onScheduleChange();

      // Clear success message after 3 seconds
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save training schedule');
    } finally {
      setIsSaving(false);
    }
  };

  // ============================================================================
  // RENDER HELPERS
  // ============================================================================

  const calculateRunningHours = () => {
    let crossTrainingHoursTotal = 0;
    crossTrainingDisciplines.forEach(d => {
      if (d.enabled) {
        if (d.allocation_type === 'hours') {
          crossTrainingHoursTotal += d.allocation_value;
        } else {
          // Convert percentage to hours
          crossTrainingHoursTotal += (d.allocation_value / 100) * totalHours;
        }
      }
    });

    const supplementalHours =
      (includeStrength ? strengthHours : 0) +
      (includeMobility ? mobilityHours : 0) +
      crossTrainingHoursTotal;

    return Math.max(0, totalHours - supplementalHours);
  };

  const hasSchedule = schedule && schedule.schedule && schedule.schedule.total_hours_per_week;

  // Shared inline styles
  const tacticalLabel: React.CSSProperties = {
    display: 'block',
    marginBottom: '8px',
    fontSize: '0.75rem',
    fontWeight: 600,
    color: '#7D9CB8',
    textTransform: 'uppercase',
    letterSpacing: '0.08em'
  };

  const tacticalInput: React.CSSProperties = {
    padding: '7px 10px',
    backgroundColor: '#162440',
    border: '1px solid #7D9CB8',
    borderRadius: '4px',
    color: '#E6F0FF',
    fontSize: '0.875rem',
    WebkitAppearance: 'none',
    MozAppearance: 'textfield'
  };

  // ============================================================================
  // RENDER
  // ============================================================================

  const displayLabel: React.CSSProperties = {
    fontSize: '0.72rem',
    fontWeight: 600,
    color: '#9ca3af',
    textTransform: 'uppercase',
    letterSpacing: '0.06em',
  };

  return (
    <>
      {/* ── WHITE CARD — always visible ── */}
      <div style={{
        backgroundColor: 'white',
        borderRadius: '8px',
        border: '1px solid #d1dce8',
        boxShadow: '0 2px 6px rgba(0,0,0,0.07)',
        overflow: 'hidden',
      }}>
        {/* Gradient header */}
        <div style={{
          background: 'linear-gradient(90deg, #E6F0FF 0%, #7D9CB8 50%, #1B2E4B 100%)',
          padding: '10px 16px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}>
          <span style={{ fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.12em', color: '#1B2E4B', textTransform: 'uppercase' }}>
            Training Availability
          </span>
          {hasSchedule && (
            <button
              onClick={handleEdit}
              style={{
                padding: '3px 10px',
                backgroundColor: 'rgba(255,87,34,0.85)',
                color: 'white',
                border: 'none',
                borderRadius: '3px',
                cursor: 'pointer',
                fontSize: '0.65rem',
                fontWeight: 700,
                letterSpacing: '0.08em',
                textTransform: 'uppercase',
              }}
            >
              Edit
            </button>
          )}
        </div>

        {/* Success toast */}
        {successMessage && (
          <div style={{
            padding: '8px 16px',
            backgroundColor: 'rgba(22,163,74,0.06)',
            borderBottom: '1px solid rgba(22,163,74,0.2)',
            color: '#16A34A',
            fontSize: '0.8rem',
            fontWeight: 600,
          }}>
            {successMessage}
          </div>
        )}

        {/* No schedule — empty state */}
        {!hasSchedule && (
          <div style={{ padding: '28px 20px', textAlign: 'center' }}>
            <p style={{ margin: '0 0 6px', fontSize: '0.875rem', fontWeight: 600, color: '#1F2937' }}>
              No schedule configured
            </p>
            <p style={{ margin: '0 0 18px', fontSize: '0.78rem', color: '#6b7280' }}>
              Define your weekly availability so the AI can build programs that fit your life.
            </p>
            <button
              onClick={handleEdit}
              style={{
                padding: '7px 20px',
                backgroundColor: '#3b82f6',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '0.78rem',
                fontWeight: 600,
              }}
            >
              Configure Schedule
            </button>
          </div>
        )}

        {/* Read-only data rows */}
        {hasSchedule && (
          <div>
            {/* Stat row */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr 1fr',
              borderBottom: '1px solid #f3f4f6',
            }}>
              {[
                { value: `${schedule?.schedule?.total_hours_per_week || 0}h`, label: 'Weekly' },
                { value: `${availableDays.length}d`, label: 'Days' },
                { value: `${calculateRunningHours()}h`, label: 'Running' },
              ].map((stat, i) => (
                <div key={i} style={{
                  padding: '12px 8px',
                  textAlign: 'center',
                  borderRight: i < 2 ? '1px solid #f3f4f6' : undefined,
                }}>
                  <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#1F2937', lineHeight: 1 }}>
                    {stat.value}
                  </div>
                  <div style={{ ...displayLabel, marginTop: '3px' }}>{stat.label}</div>
                </div>
              ))}
            </div>

            {/* Training days */}
            <div style={{ padding: '10px 16px', borderBottom: '1px solid #f3f4f6' }}>
              <div style={{ ...displayLabel, marginBottom: '7px' }}>Training Days</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '5px' }}>
                {DAYS.map(day => (
                  <span key={day} style={{
                    padding: '3px 8px',
                    backgroundColor: availableDays.includes(day) ? '#f0f7ff' : '#f9fafb',
                    border: `1px solid ${availableDays.includes(day) ? '#3b82f6' : '#e5e7eb'}`,
                    color: availableDays.includes(day) ? '#1d4ed8' : '#d1d5db',
                    borderRadius: '4px',
                    fontSize: '0.72rem',
                    fontWeight: 700,
                    letterSpacing: '0.06em',
                  }}>
                    {day.slice(0, 3).toUpperCase()}
                  </span>
                ))}
              </div>
            </div>

            {/* Long run days */}
            {longRunDays.length > 0 && (
              <div style={{ padding: '10px 16px', borderBottom: '1px solid #f3f4f6' }}>
                <div style={{ ...displayLabel, marginBottom: '7px' }}>Long Run Days</div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '5px' }}>
                  {longRunDays.map(day => (
                    <span key={day} style={{
                      padding: '3px 8px',
                      backgroundColor: '#f0fdf4',
                      border: '1px solid #86efac',
                      color: '#15803d',
                      borderRadius: '4px',
                      fontSize: '0.72rem',
                      fontWeight: 700,
                      letterSpacing: '0.06em',
                    }}>
                      {day.slice(0, 3).toUpperCase()}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Supplemental */}
            {(includeStrength || includeMobility || crossTrainingDisciplines.some(d => d.enabled)) && (
              <div style={{ padding: '10px 16px', borderBottom: '1px solid #f3f4f6' }}>
                <div style={{ ...displayLabel, marginBottom: '7px' }}>Supplemental</div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  {includeStrength && (
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem' }}>
                      <span style={{ color: '#6b7280' }}>Strength</span>
                      <span style={{ fontWeight: 600, color: '#1F2937' }}>{strengthHours}h/wk</span>
                    </div>
                  )}
                  {includeMobility && (
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem' }}>
                      <span style={{ color: '#6b7280' }}>Mobility</span>
                      <span style={{ fontWeight: 600, color: '#1F2937' }}>{mobilityHours}h/wk</span>
                    </div>
                  )}
                  {crossTrainingDisciplines.filter(d => d.enabled).map(d => {
                    const info = AVAILABLE_DISCIPLINES.find(ad => ad.key === d.discipline);
                    const val = d.allocation_type === 'hours' ? `${d.allocation_value}h/wk` : `${d.allocation_value}%`;
                    return (
                      <div key={d.discipline} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem' }}>
                        <span style={{ color: '#6b7280' }}>{info?.label}</span>
                        <span style={{ fontWeight: 600, color: '#1F2937' }}>{val}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Constraints */}
            {constraints && (
              <div style={{ padding: '10px 16px' }}>
                <div style={{ ...displayLabel, marginBottom: '5px' }}>Constraints</div>
                <div style={{ fontSize: '0.78rem', color: '#6b7280', lineHeight: 1.5 }}>{constraints}</div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* ── CARBON MODAL — edit overlay (portalled to body to escape sticky context) ── */}
      {isEditing && ReactDOM.createPortal(
        <div
          style={{
            position: 'fixed', inset: 0, zIndex: 1000,
            backgroundColor: 'rgba(0,0,0,0.65)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            padding: '20px',
          }}
          onClick={e => { if (e.target === e.currentTarget) handleCancel(); }}
        >
          <div style={{
            backgroundColor: '#1B2E4B',
            backgroundImage: [
              'linear-gradient(135deg, rgba(255,255,255,0.04) 25%, transparent 25%)',
              'linear-gradient(225deg, rgba(255,255,255,0.04) 25%, transparent 25%)',
              'linear-gradient(315deg, rgba(255,255,255,0.04) 25%, transparent 25%)',
              'linear-gradient(45deg,  rgba(255,255,255,0.04) 25%, transparent 25%)',
            ].join(', '),
            backgroundSize: '4px 4px',
            border: '1px solid rgba(255,87,34,0.7)',
            borderRadius: '8px',
            overflow: 'hidden',
            width: '100%',
            maxWidth: '560px',
            maxHeight: '90vh',
            overflowY: 'auto',
          }}>
            {/* Modal header */}
            <div style={{
              background: 'linear-gradient(90deg, #E6F0FF 0%, #7D9CB8 50%, #1B2E4B 100%)',
              padding: '12px 24px',
            }}>
              <span style={{ fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.12em', color: '#1B2E4B', textTransform: 'uppercase' }}>
                {hasSchedule ? 'Modify Training Schedule' : 'Configure Training Schedule'}
              </span>
            </div>

            {/* Modal error */}
            {error && (
              <div style={{
                margin: '16px 24px 0',
                padding: '10px 14px',
                backgroundColor: 'rgba(220,38,38,0.06)',
                border: '1px solid rgba(220,38,38,0.3)',
                borderLeft: '3px solid #dc2626',
                borderRadius: '4px',
                color: '#dc2626',
                fontSize: '0.8rem',
              }}>
                {error}
              </div>
            )}

            <div style={{ padding: '20px 24px 24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>

              {/* Total Weekly Hours */}
              <div>
                <label style={tacticalLabel}>
                  Total Weekly Training Hours <span style={{ color: 'rgba(255,87,34,0.8)' }}>*</span>
                </label>
                <input
                  type="number"
                  min="1"
                  max="100"
                  step="0.5"
                  value={totalHours}
                  onChange={(e) => setTotalHours(parseFloat(e.target.value))}
                  style={{ ...tacticalInput, width: '110px', fontWeight: 600 }}
                />
                <div style={{ marginTop: '6px', fontSize: '0.75rem', color: 'rgba(125,156,184,0.65)' }}>
                  Includes all training: running, strength, mobility, cross-training
                </div>
              </div>

              {/* Training Days */}
              <div>
                <label style={tacticalLabel}>
                  Training Days <span style={{ color: 'rgba(255,87,34,0.8)' }}>*</span>
                </label>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                  {DAYS.map(day => (
                    <button
                      key={day}
                      type="button"
                      onClick={() => handleDayToggle(day)}
                      style={{
                        padding: '8px 14px',
                        backgroundColor: availableDays.includes(day) ? 'rgba(255,87,34,0.15)' : '#162440',
                        border: availableDays.includes(day) ? '1px solid #FF5722' : '1px solid rgba(125,156,184,0.35)',
                        color: availableDays.includes(day) ? '#FF5722' : '#7D9CB8',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        fontSize: '0.75rem',
                        fontWeight: 700,
                        letterSpacing: '0.08em',
                      }}
                    >
                      {day.slice(0, 3).toUpperCase()}
                    </button>
                  ))}
                </div>
              </div>

              {/* Long Run Days */}
              {availableDays.length > 0 && (
                <div>
                  <label style={tacticalLabel}>
                    Long Run Days <span style={{ color: 'rgba(255,87,34,0.8)' }}>*</span>
                  </label>
                  <div style={{ marginBottom: '10px', fontSize: '0.75rem', color: 'rgba(125,156,184,0.65)' }}>
                    Which days work for long runs (90+ min)?
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                    {DAYS.map(day => {
                      const isDayAvailable = availableDays.includes(day);
                      const isLongRunDay = longRunDays.includes(day);
                      return (
                        <button
                          key={day}
                          type="button"
                          onClick={() => isDayAvailable && handleLongRunDayToggle(day)}
                          disabled={!isDayAvailable}
                          style={{
                            padding: '8px 14px',
                            backgroundColor: isLongRunDay ? 'rgba(125,156,184,0.18)' : '#162440',
                            border: isLongRunDay ? '1px solid #7D9CB8' : '1px solid rgba(125,156,184,0.22)',
                            color: isLongRunDay ? '#E6F0FF' : '#7D9CB8',
                            borderRadius: '4px',
                            cursor: isDayAvailable ? 'pointer' : 'default',
                            fontSize: '0.75rem',
                            fontWeight: isLongRunDay ? 700 : 500,
                            letterSpacing: '0.08em',
                            opacity: isDayAvailable ? 1 : 0.3,
                          }}
                        >
                          {day.slice(0, 3).toUpperCase()}
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Constraints */}
              <div>
                <label style={tacticalLabel}>
                  Constraints{' '}
                  <span style={{ color: 'rgba(125,156,184,0.5)', fontWeight: 400, textTransform: 'none', letterSpacing: 0 }}>— optional</span>
                </label>
                <textarea
                  value={constraints}
                  onChange={(e) => setConstraints(e.target.value)}
                  style={{
                    ...tacticalInput,
                    width: '100%',
                    minHeight: '80px',
                    fontFamily: 'inherit',
                    resize: 'vertical',
                    boxSizing: 'border-box',
                  } as React.CSSProperties}
                  placeholder="e.g., Tuesday max 30 minutes, Need rest day after long runs..."
                />
              </div>

              {/* Supplemental Training */}
              <div style={{ borderTop: '1px solid rgba(125,156,184,0.25)', paddingTop: '20px' }}>
                <div style={{ fontSize: '0.7rem', fontWeight: 700, color: '#7D9CB8', textTransform: 'uppercase', letterSpacing: '0.12em', marginBottom: '6px' }}>
                  Supplemental Training
                </div>
                <div style={{ fontSize: '0.75rem', color: 'rgba(125,156,184,0.65)', marginBottom: '16px' }}>
                  Include other activities in your weekly program
                </div>

                {[
                  { label: 'Strength Training', checked: includeStrength, setChecked: setIncludeStrength, hours: strengthHours, setHours: setStrengthHours, min: 0.5, max: 20 },
                  { label: 'Mobility / Yoga / Stretching', checked: includeMobility, setChecked: setIncludeMobility, hours: mobilityHours, setHours: setMobilityHours, min: 0.5, max: 10 },
                ].map(item => (
                  <div key={item.label} style={{
                    marginBottom: '10px',
                    padding: '14px',
                    backgroundColor: '#162440',
                    border: '1px solid rgba(125,156,184,0.22)',
                    borderRadius: '4px',
                  }}>
                    <label style={{ display: 'flex', alignItems: 'center', marginBottom: item.checked ? '12px' : 0, cursor: 'pointer' }}>
                      <input
                        type="checkbox"
                        checked={item.checked}
                        onChange={(e) => item.setChecked(e.target.checked)}
                        style={{ marginRight: '10px', width: '15px', height: '15px', cursor: 'pointer', accentColor: '#FF5722' }}
                      />
                      <span style={{ fontSize: '0.875rem', fontWeight: 600, color: '#E6F0FF' }}>{item.label}</span>
                    </label>
                    {item.checked && (
                      <div style={{ paddingLeft: '25px' }}>
                        <label style={{ ...tacticalLabel, marginBottom: '6px' }}>Hours / Week</label>
                        <input
                          type="number"
                          min={item.min}
                          max={item.max}
                          step="0.5"
                          value={item.hours}
                          onChange={(e) => item.setHours(parseFloat(e.target.value))}
                          style={{ ...tacticalInput, width: '90px' }}
                        />
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {/* Cross-Training */}
              <div>
                <div style={{ fontSize: '0.7rem', fontWeight: 700, color: '#7D9CB8', textTransform: 'uppercase', letterSpacing: '0.12em', marginBottom: '6px' }}>
                  Cross-Training Activities
                </div>
                <p style={{ fontSize: '0.75rem', color: 'rgba(125,156,184,0.65)', margin: '0 0 14px 0' }}>
                  Hours per week or percentage of total training time.
                </p>
                {AVAILABLE_DISCIPLINES.map(discipline => {
                  const isEnabled = crossTrainingDisciplines.some(d => d.discipline === discipline.key && d.enabled);
                  const config = crossTrainingDisciplines.find(d => d.discipline === discipline.key);
                  return (
                    <div key={discipline.key} style={{
                      marginBottom: '10px',
                      padding: '14px',
                      backgroundColor: isEnabled ? 'rgba(125,156,184,0.08)' : '#162440',
                      border: isEnabled ? '1px solid rgba(125,156,184,0.45)' : '1px solid rgba(125,156,184,0.2)',
                      borderRadius: '4px',
                    }}>
                      <label style={{ display: 'flex', alignItems: 'center', marginBottom: isEnabled ? '12px' : 0, cursor: 'pointer' }}>
                        <input
                          type="checkbox"
                          checked={isEnabled}
                          onChange={() => handleDisciplineToggle(discipline.key)}
                          style={{ marginRight: '10px', width: '15px', height: '15px', cursor: 'pointer', accentColor: '#FF5722' }}
                        />
                        <span style={{ fontSize: '0.875rem', fontWeight: 600, color: '#E6F0FF' }}>{discipline.label}</span>
                      </label>
                      {isEnabled && config && (
                        <div style={{ paddingLeft: '25px' }}>
                          <div style={{ display: 'flex', gap: '18px', marginBottom: '10px' }}>
                            {(['hours', 'percentage'] as const).map(type => (
                              <label key={type} style={{ display: 'flex', alignItems: 'center', cursor: 'pointer', fontSize: '0.8rem', color: '#7D9CB8' }}>
                                <input
                                  type="radio"
                                  name={`allocation-${discipline.key}`}
                                  checked={config.allocation_type === type}
                                  onChange={() => handleDisciplineUpdate(discipline.key, 'allocation_type', type)}
                                  style={{ marginRight: '6px', accentColor: '#FF5722' }}
                                />
                                {type === 'hours' ? 'Hours / week' : '% of total'}
                              </label>
                            ))}
                          </div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                            <input
                              type="number"
                              min="0"
                              max={config.allocation_type === 'percentage' ? 100 : 40}
                              step={config.allocation_type === 'percentage' ? 5 : 0.5}
                              value={config.allocation_value}
                              onChange={(e) => handleDisciplineUpdate(discipline.key, 'allocation_value', parseFloat(e.target.value) || 0)}
                              style={{ ...tacticalInput, width: '80px' }}
                            />
                            <span style={{ fontSize: '0.8rem', color: '#7D9CB8' }}>
                              {config.allocation_type === 'hours' ? 'hrs/week' : '%'}
                            </span>
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>

              {/* Weekly Breakdown */}
              <div style={{
                padding: '14px 16px',
                backgroundColor: 'rgba(22,36,64,0.8)',
                border: '1px solid rgba(125,156,184,0.3)',
                borderRadius: '4px',
              }}>
                <div style={{ fontSize: '0.7rem', fontWeight: 700, color: '#7D9CB8', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '10px' }}>
                  Weekly Breakdown
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px', fontSize: '0.8rem', color: '#E6F0FF' }}>
                  <div>Running / Walking: <strong>{calculateRunningHours()}h</strong></div>
                  {includeStrength && <div>Strength: <strong>{strengthHours}h</strong></div>}
                  {includeMobility && <div>Mobility: <strong>{mobilityHours}h</strong></div>}
                  {crossTrainingDisciplines.filter(d => d.enabled).map(d => {
                    const info = AVAILABLE_DISCIPLINES.find(ad => ad.key === d.discipline);
                    const val = d.allocation_type === 'hours' ? `${d.allocation_value}h` : `${d.allocation_value}% (${((d.allocation_value / 100) * totalHours).toFixed(1)}h)`;
                    return <div key={d.discipline}>{info?.label}: <strong>{val}</strong></div>;
                  })}
                  <div style={{ gridColumn: '1 / -1', borderTop: '1px solid rgba(125,156,184,0.25)', paddingTop: '8px', marginTop: '4px' }}>
                    <strong>Total: {totalHours}h/week</strong>
                  </div>
                </div>
              </div>

              {/* Actions */}
              <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
                <button
                  onClick={handleCancel}
                  disabled={isSaving}
                  style={{
                    padding: '8px 20px',
                    backgroundColor: 'rgba(230,240,255,0.07)',
                    color: '#E6F0FF',
                    border: '1px solid rgba(125,156,184,0.4)',
                    borderRadius: '4px',
                    cursor: isSaving ? 'not-allowed' : 'pointer',
                    fontSize: '0.8rem',
                    fontWeight: 600,
                    opacity: isSaving ? 0.6 : 1,
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
                  {isSaving ? 'Applying...' : 'Apply'}
                </button>
              </div>
            </div>
          </div>
        </div>,
        document.body
      )}
    </>
  );
};

export default TrainingScheduleConfig;
