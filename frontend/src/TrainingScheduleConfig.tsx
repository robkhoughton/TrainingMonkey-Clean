import React, { useState, useEffect } from 'react';
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

  // ============================================================================
  // RENDER
  // ============================================================================

  return (
    <div>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h2 className={styles.cardHeader}>Training Schedule & Availability</h2>
        {!isEditing && hasSchedule && (
          <button
            onClick={handleEdit}
            style={{
              padding: '10px 20px',
              backgroundColor: '#3498db',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: '600'
            }}
          >
            ✏️ Edit Schedule
          </button>
        )}
      </div>

      {/* Success Message */}
      {successMessage && (
        <div style={{
          padding: '15px',
          backgroundColor: '#d4edda',
          border: '1px solid #c3e6cb',
          borderRadius: '4px',
          marginBottom: '15px',
          color: '#155724',
          fontWeight: '600'
        }}>
          ✅ {successMessage}
        </div>
      )}

      {/* Error Message */}
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

      {/* No Schedule - Show Setup Prompt */}
      {!hasSchedule && !isEditing && (
        <div style={{
          textAlign: 'center',
          padding: '40px 20px',
          backgroundColor: '#f8f9fa',
          borderRadius: '8px',
          border: '2px dashed #3498db'
        }}>
          <p style={{ fontSize: '18px', marginBottom: '15px', color: '#2c3e50' }}>
            📅 No training schedule configured
          </p>
          <p style={{ fontSize: '14px', marginBottom: '20px', color: '#7f8c8d' }}>
            Tell us your weekly availability so we can create realistic training programs that fit your life!
          </p>
          <button
            onClick={handleEdit}
            style={{
              padding: '12px 24px',
              backgroundColor: '#3498db',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '16px',
              fontWeight: '600'
            }}
          >
            Configure Training Schedule
          </button>
        </div>
      )}

      {/* Display Schedule (Read-Only) */}
      {hasSchedule && !isEditing && (
        <div>
          {/* Summary Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '15px', marginBottom: '20px' }}>
            <div style={{
              padding: '20px',
              backgroundColor: '#3498db',
              color: 'white',
              borderRadius: '8px',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '32px', fontWeight: 'bold', marginBottom: '5px' }}>
                {schedule?.schedule?.total_hours_per_week || 0}h
              </div>
              <div style={{ fontSize: '14px', opacity: 0.9 }}>Total Weekly Hours</div>
            </div>

            <div style={{
              padding: '20px',
              backgroundColor: '#2ecc71',
              color: 'white',
              borderRadius: '8px',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '32px', fontWeight: 'bold', marginBottom: '5px' }}>
                {availableDays.length}
              </div>
              <div style={{ fontSize: '14px', opacity: 0.9 }}>Training Days/Week</div>
            </div>

            <div style={{
              padding: '20px',
              backgroundColor: '#9b59b6',
              color: 'white',
              borderRadius: '8px',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '32px', fontWeight: 'bold', marginBottom: '5px' }}>
                {calculateRunningHours()}h
              </div>
              <div style={{ fontSize: '14px', opacity: 0.9 }}>Running/Walking</div>
            </div>
          </div>

          {/* Available Days */}
          <div style={{ marginBottom: '20px' }}>
            <h3 style={{ fontSize: '16px', marginBottom: '10px', color: '#2c3e50' }}>Available Training Days:</h3>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
              {DAYS.map(day => (
                <span
                  key={day}
                  style={{
                    padding: '8px 16px',
                    backgroundColor: availableDays.includes(day) ? '#2ecc71' : '#e1e8ed',
                    color: availableDays.includes(day) ? 'white' : '#95a5a6',
                    borderRadius: '20px',
                    fontSize: '14px',
                    fontWeight: '600'
                  }}
                >
                  {day.slice(0, 3)}
                </span>
              ))}
            </div>
          </div>

          {/* Supplemental Training */}
          {(includeStrength || includeMobility || crossTrainingDisciplines.length > 0) && (
            <div style={{ marginBottom: '20px' }}>
              <h3 style={{ fontSize: '16px', marginBottom: '10px', color: '#2c3e50' }}>Supplemental Training:</h3>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px' }}>
                {includeStrength && (
                  <div style={{
                    padding: '10px 15px',
                    backgroundColor: '#e8f4f8',
                    borderRadius: '6px',
                    fontSize: '14px'
                  }}>
                    <strong>💪 Strength:</strong> {strengthHours}h/week
                  </div>
                )}
                {includeMobility && (
                  <div style={{
                    padding: '10px 15px',
                    backgroundColor: '#e8f4f8',
                    borderRadius: '6px',
                    fontSize: '14px'
                  }}>
                    <strong>🧘 Mobility:</strong> {mobilityHours}h/week
                  </div>
                )}
                {crossTrainingDisciplines.filter(d => d.enabled).map(d => {
                  const disciplineInfo = AVAILABLE_DISCIPLINES.find(ad => ad.key === d.discipline);
                  const displayValue = d.allocation_type === 'hours'
                    ? `${d.allocation_value}h/week`
                    : `${d.allocation_value}% (${((d.allocation_value / 100) * (schedule?.schedule?.total_hours_per_week || 0)).toFixed(1)}h/week)`;
                  return (
                    <div key={d.discipline} style={{
                      padding: '10px 15px',
                      backgroundColor: '#e8f4f8',
                      borderRadius: '6px',
                      fontSize: '14px'
                    }}>
                      <strong>{disciplineInfo?.label}:</strong> {displayValue}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Constraints */}
          {constraints && (
            <div style={{ marginBottom: '20px' }}>
              <h3 style={{ fontSize: '16px', marginBottom: '10px', color: '#2c3e50' }}>Fixed Constraints:</h3>
              <div style={{
                padding: '15px',
                backgroundColor: '#f8f9fa',
                borderRadius: '6px',
                fontSize: '14px',
                color: '#555'
              }}>
                {constraints}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Edit Form */}
      {isEditing && (
        <div style={{
          backgroundColor: '#f8f9fa',
          padding: '20px',
          borderRadius: '8px',
          border: '2px solid #3498db'
        }}>
          <h3 style={{ marginTop: 0, marginBottom: '20px', color: '#2c3e50' }}>
            Configure Your Training Schedule
          </h3>

          {/* Total Weekly Hours */}
          <div style={{ marginBottom: '25px' }}>
            <label style={{ display: 'block', marginBottom: '10px', fontWeight: '600', fontSize: '15px' }}>
              Total Weekly Training Hours <span style={{ color: '#e74c3c' }}>*</span>
            </label>
            <input
              type="number"
              min="1"
              max="100"
              step="0.5"
              value={totalHours}
              onChange={(e) => setTotalHours(parseFloat(e.target.value))}
              style={{
                width: '200px',
                padding: '10px',
                border: '1px solid #ddd',
                borderRadius: '4px',
                fontSize: '16px',
                fontWeight: '600'
              }}
            />
            <div style={{ marginTop: '8px', fontSize: '13px', color: '#7f8c8d' }}>
              Includes all training: running, strength, mobility, cross-training, etc.
            </div>
          </div>

          {/* Available Days */}
          <div style={{ marginBottom: '25px' }}>
            <label style={{ display: 'block', marginBottom: '10px', fontWeight: '600', fontSize: '15px' }}>
              Available Training Days <span style={{ color: '#e74c3c' }}>*</span>
            </label>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: '10px' }}>
              {DAYS.map(day => (
                <label
                  key={day}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    padding: '10px',
                    backgroundColor: availableDays.includes(day) ? '#d4edda' : 'white',
                    border: availableDays.includes(day) ? '2px solid #2ecc71' : '1px solid #ddd',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    fontSize: '14px',
                    fontWeight: '600'
                  }}
                >
                  <input
                    type="checkbox"
                    checked={availableDays.includes(day)}
                    onChange={() => handleDayToggle(day)}
                    style={{ marginRight: '8px', width: '18px', height: '18px', cursor: 'pointer' }}
                  />
                  {day}
                </label>
              ))}
            </div>
          </div>

          {/* Long Run Days */}
          {availableDays.length > 0 && (
            <div style={{ marginBottom: '25px' }}>
              <label style={{ display: 'block', marginBottom: '10px', fontWeight: '600', fontSize: '15px' }}>
                Long Run Days <span style={{ color: '#e74c3c' }}>*</span>
              </label>
              <div style={{ fontSize: '13px', color: '#7f8c8d', marginBottom: '10px' }}>
                Which days work for long runs (90+ minutes)?
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: '10px' }}>
                {DAYS.map(day => {
                  const isDayAvailable = availableDays.includes(day);
                  const isSelected = longRunDays.includes(day);
                  return (
                    <label
                      key={day}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        padding: '10px',
                        backgroundColor: isSelected ? '#e3f2fd' : isDayAvailable ? 'white' : '#f5f5f5',
                        border: isSelected ? '2px solid #2196f3' : '1px solid #ddd',
                        borderRadius: '6px',
                        cursor: isDayAvailable ? 'pointer' : 'not-allowed',
                        fontSize: '14px',
                        fontWeight: isSelected ? '600' : 'normal',
                        opacity: isDayAvailable ? 1 : 0.5
                      }}
                    >
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => handleLongRunDayToggle(day)}
                        disabled={!isDayAvailable}
                        style={{ marginRight: '8px', width: '18px', height: '18px', cursor: isDayAvailable ? 'pointer' : 'not-allowed' }}
                      />
                      {day}
                    </label>
                  );
                })}
              </div>
            </div>
          )}

          {/* Fixed Constraints */}
          <div style={{ marginBottom: '25px' }}>
            <label style={{ display: 'block', marginBottom: '10px', fontWeight: '600', fontSize: '15px' }}>
              Fixed Constraints (Optional)
            </label>
            <textarea
              value={constraints}
              onChange={(e) => setConstraints(e.target.value)}
              style={{
                width: '100%',
                padding: '10px',
                border: '1px solid #ddd',
                borderRadius: '4px',
                fontSize: '14px',
                minHeight: '80px',
                fontFamily: 'inherit'
              }}
              placeholder="e.g., Tuesday max 30 minutes, Need rest day after long runs, Traveling week of March 10..."
            />
          </div>

          {/* Supplemental Training */}
          <div style={{ marginBottom: '25px' }}>
            <h3 style={{ fontSize: '16px', marginBottom: '15px', color: '#2c3e50' }}>
              Supplemental Training
            </h3>
            <div style={{ fontSize: '13px', color: '#7f8c8d', marginBottom: '15px' }}>
              Include other training activities in your weekly program
            </div>

            {/* Strength Training */}
            <div style={{ marginBottom: '15px', padding: '15px', backgroundColor: 'white', borderRadius: '6px' }}>
              <label style={{ display: 'flex', alignItems: 'center', marginBottom: '10px', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={includeStrength}
                  onChange={(e) => setIncludeStrength(e.target.checked)}
                  style={{ marginRight: '10px', width: '18px', height: '18px', cursor: 'pointer' }}
                />
                <span style={{ fontWeight: '600', fontSize: '14px' }}>💪 Strength Training</span>
              </label>
              {includeStrength && (
                <div style={{ paddingLeft: '28px' }}>
                  <label style={{ fontSize: '13px', color: '#555', display: 'block', marginBottom: '5px' }}>
                    Hours per week:
                  </label>
                  <input
                    type="number"
                    min="0.5"
                    max="20"
                    step="0.5"
                    value={strengthHours}
                    onChange={(e) => setStrengthHours(parseFloat(e.target.value))}
                    style={{
                      width: '100px',
                      padding: '6px',
                      border: '1px solid #ddd',
                      borderRadius: '4px',
                      fontSize: '14px'
                    }}
                  />
                </div>
              )}
            </div>

            {/* Mobility/Flexibility */}
            <div style={{ marginBottom: '15px', padding: '15px', backgroundColor: 'white', borderRadius: '6px' }}>
              <label style={{ display: 'flex', alignItems: 'center', marginBottom: '10px', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={includeMobility}
                  onChange={(e) => setIncludeMobility(e.target.checked)}
                  style={{ marginRight: '10px', width: '18px', height: '18px', cursor: 'pointer' }}
                />
                <span style={{ fontWeight: '600', fontSize: '14px' }}>🧘 Mobility/Yoga/Stretching</span>
              </label>
              {includeMobility && (
                <div style={{ paddingLeft: '28px' }}>
                  <label style={{ fontSize: '13px', color: '#555', display: 'block', marginBottom: '5px' }}>
                    Hours per week:
                  </label>
                  <input
                    type="number"
                    min="0.5"
                    max="10"
                    step="0.5"
                    value={mobilityHours}
                    onChange={(e) => setMobilityHours(parseFloat(e.target.value))}
                    style={{
                      width: '100px',
                      padding: '6px',
                      border: '1px solid #ddd',
                      borderRadius: '4px',
                      fontSize: '14px'
                    }}
                  />
                </div>
              )}
            </div>

            {/* Cross-Training Activities */}
            <div style={{ marginBottom: '25px' }}>
              <h3 style={{ fontSize: '16px', marginBottom: '15px', color: '#2c3e50' }}>
                Cross-Training Activities
              </h3>
              <p style={{ fontSize: '13px', color: '#7f8c8d', marginBottom: '15px' }}>
                Select multiple cross-training activities and specify hours per week OR percentage of total training time for each.
              </p>

              {AVAILABLE_DISCIPLINES.map(discipline => {
                const isEnabled = crossTrainingDisciplines.some(d => d.discipline === discipline.key && d.enabled);
                const config = crossTrainingDisciplines.find(d => d.discipline === discipline.key);

                return (
                  <div key={discipline.key} style={{
                    marginBottom: '15px',
                    padding: '15px',
                    backgroundColor: isEnabled ? '#e8f5e9' : 'white',
                    border: isEnabled ? '2px solid #4caf50' : '1px solid #ddd',
                    borderRadius: '6px'
                  }}>
                    <label style={{ display: 'flex', alignItems: 'center', marginBottom: '10px', cursor: 'pointer' }}>
                      <input
                        type="checkbox"
                        checked={isEnabled}
                        onChange={() => handleDisciplineToggle(discipline.key)}
                        style={{ marginRight: '10px', width: '18px', height: '18px', cursor: 'pointer' }}
                      />
                      <span style={{ fontWeight: '600', fontSize: '14px' }}>
                        {discipline.label}
                      </span>
                    </label>

                    {isEnabled && config && (
                      <div style={{ paddingLeft: '28px' }}>
                        {/* Allocation Type Toggle */}
                        <div style={{ marginBottom: '10px' }}>
                          <label style={{ marginRight: '15px', cursor: 'pointer' }}>
                            <input
                              type="radio"
                              name={`allocation-${discipline.key}`}
                              checked={config.allocation_type === 'hours'}
                              onChange={() => handleDisciplineUpdate(discipline.key, 'allocation_type', 'hours')}
                              style={{ marginRight: '5px' }}
                            />
                            Hours per week
                          </label>
                          <label style={{ cursor: 'pointer' }}>
                            <input
                              type="radio"
                              name={`allocation-${discipline.key}`}
                              checked={config.allocation_type === 'percentage'}
                              onChange={() => handleDisciplineUpdate(discipline.key, 'allocation_type', 'percentage')}
                              style={{ marginRight: '5px' }}
                            />
                            % of total training
                          </label>
                        </div>

                        {/* Allocation Value Input */}
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                          <input
                            type="number"
                            min="0"
                            max={config.allocation_type === 'percentage' ? 100 : 40}
                            step={config.allocation_type === 'percentage' ? 5 : 0.5}
                            value={config.allocation_value}
                            onChange={(e) => handleDisciplineUpdate(discipline.key, 'allocation_value', parseFloat(e.target.value) || 0)}
                            style={{
                              width: '80px',
                              padding: '6px',
                              border: '1px solid #ddd',
                              borderRadius: '4px',
                              fontSize: '14px'
                            }}
                          />
                          <span style={{ fontSize: '14px', color: '#555' }}>
                            {config.allocation_type === 'hours' ? 'hours/week' : '%'}
                          </span>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Summary */}
          <div style={{
            padding: '15px',
            backgroundColor: '#e8f4f8',
            borderRadius: '6px',
            marginBottom: '20px',
            fontSize: '14px'
          }}>
            <strong>Weekly Time Breakdown:</strong>
            <div style={{ marginTop: '8px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
              <div>Running/Walking: <strong>{calculateRunningHours()}h</strong></div>
              {includeStrength && <div>Strength: <strong>{strengthHours}h</strong></div>}
              {includeMobility && <div>Mobility: <strong>{mobilityHours}h</strong></div>}
              {crossTrainingDisciplines.filter(d => d.enabled).map(d => {
                const disciplineInfo = AVAILABLE_DISCIPLINES.find(ad => ad.key === d.discipline);
                const displayValue = d.allocation_type === 'hours'
                  ? `${d.allocation_value}h`
                  : `${d.allocation_value}% (${((d.allocation_value / 100) * totalHours).toFixed(1)}h)`;
                return (
                  <div key={d.discipline}>{disciplineInfo?.label}: <strong>{displayValue}</strong></div>
                );
              })}
              <div style={{ gridColumn: '1 / -1', borderTop: '1px solid #ccc', paddingTop: '8px', marginTop: '8px' }}>
                <strong>Total: {totalHours}h/week</strong>
              </div>
            </div>
          </div>

          {/* Form Actions */}
          <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
            <button
              onClick={handleCancel}
              disabled={isSaving}
              style={{
                padding: '12px 24px',
                backgroundColor: '#95a5a6',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: isSaving ? 'not-allowed' : 'pointer',
                fontSize: '14px',
                fontWeight: '600',
                opacity: isSaving ? 0.6 : 1
              }}
            >
              Cancel
            </button>
            <button
              onClick={handleSubmit}
              disabled={isSaving}
              style={{
                padding: '12px 24px',
                backgroundColor: '#10b981',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: isSaving ? 'not-allowed' : 'pointer',
                fontSize: '14px',
                fontWeight: '600',
                opacity: isSaving ? 0.6 : 1
              }}
            >
              {isSaving ? 'Saving...' : 'Save Schedule'}
            </button>
          </div>
        </div>
      )}

      {/* Help Text */}
      {!isEditing && hasSchedule && (
        <div style={{
          marginTop: '20px',
          padding: '15px',
          backgroundColor: '#e8f4f8',
          borderRadius: '6px',
          fontSize: '13px',
          color: '#555'
        }}>
          <strong>💡 How This Helps:</strong>
          <ul style={{ marginTop: '8px', marginBottom: 0, paddingLeft: '20px' }}>
            <li>Weekly training programs will respect your availability and time constraints</li>
            <li>Workouts will be scheduled on your available days</li>
            <li>Total weekly volume stays within your committed hours</li>
            <li>Supplemental training is integrated into your program</li>
          </ul>
        </div>
      )}
    </div>
  );
};

export default TrainingScheduleConfig;

