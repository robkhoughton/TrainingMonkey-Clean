import React, { useState, useEffect } from 'react';
import styles from './TrainingLoadDashboard.module.css';

// ============================================================================
// INTERFACES
// ============================================================================

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

interface TrainingScheduleConfigProps {
  schedule: TrainingSchedule | null;
  onScheduleChange: () => void;
}

// ============================================================================
// CONSTANTS
// ============================================================================

const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
const TIME_BLOCKS = ['Early Morning', 'Morning', 'Midday', 'Afternoon', 'Evening', 'Night'];

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
  const [timeBlocks, setTimeBlocks] = useState<{ [key: string]: string[] }>({});
  const [constraints, setConstraints] = useState<string>('');
  
  // Supplemental training
  const [includeStrength, setIncludeStrength] = useState<boolean>(false);
  const [strengthHours, setStrengthHours] = useState<number>(2);
  const [includeMobility, setIncludeMobility] = useState<boolean>(false);
  const [mobilityHours, setMobilityHours] = useState<number>(1);
  const [includeCrossTraining, setIncludeCrossTraining] = useState<boolean>(false);
  const [crossTrainingType, setCrossTrainingType] = useState<string>('Cycling');
  const [crossTrainingHours, setCrossTrainingHours] = useState<number>(2);

  // ============================================================================
  // LOAD EXISTING SCHEDULE
  // ============================================================================

  useEffect(() => {
    if (schedule) {
      if (schedule.schedule) {
        setTotalHours(schedule.schedule.total_hours_per_week || 10);
        setAvailableDays(schedule.schedule.available_days || []);
        setTimeBlocks(schedule.schedule.time_blocks || {});
        
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
      setIncludeCrossTraining(schedule.include_cross_training);
      setCrossTrainingType(schedule.cross_training_type || 'Cycling');
      setCrossTrainingHours(schedule.cross_training_hours);
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
        setTimeBlocks(schedule.schedule.time_blocks || {});
        
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
      setIncludeCrossTraining(schedule.include_cross_training);
      setCrossTrainingType(schedule.cross_training_type || 'Cycling');
      setCrossTrainingHours(schedule.cross_training_hours);
    }
  };

  const handleDayToggle = (day: string) => {
    if (availableDays.includes(day)) {
      setAvailableDays(availableDays.filter(d => d !== day));
      // Remove time blocks for this day
      const newTimeBlocks = { ...timeBlocks };
      delete newTimeBlocks[day];
      setTimeBlocks(newTimeBlocks);
    } else {
      setAvailableDays([...availableDays, day]);
    }
  };

  const handleTimeBlockToggle = (day: string, block: string) => {
    const currentBlocks = timeBlocks[day] || [];
    let newBlocks;
    
    if (currentBlocks.includes(block)) {
      newBlocks = currentBlocks.filter(b => b !== block);
    } else {
      newBlocks = [...currentBlocks, block];
    }
    
    setTimeBlocks({
      ...timeBlocks,
      [day]: newBlocks
    });
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

    const totalSupplementalHours = 
      (includeStrength ? strengthHours : 0) +
      (includeMobility ? mobilityHours : 0) +
      (includeCrossTraining ? crossTrainingHours : 0);

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
          time_blocks: timeBlocks,
          constraints: constraintsList
        },
        include_strength_training: includeStrength,
        strength_hours_per_week: includeStrength ? strengthHours : 0,
        include_mobility: includeMobility,
        mobility_hours_per_week: includeMobility ? mobilityHours : 0,
        include_cross_training: includeCrossTraining,
        cross_training_type: includeCrossTraining ? crossTrainingType : null,
        cross_training_hours_per_week: includeCrossTraining ? crossTrainingHours : 0
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
    const supplementalHours = 
      (includeStrength ? strengthHours : 0) +
      (includeMobility ? mobilityHours : 0) +
      (includeCrossTraining ? crossTrainingHours : 0);
    
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
          {(includeStrength || includeMobility || includeCrossTraining) && (
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
                {includeCrossTraining && (
                  <div style={{
                    padding: '10px 15px',
                    backgroundColor: '#e8f4f8',
                    borderRadius: '6px',
                    fontSize: '14px'
                  }}>
                    <strong>🚴 {crossTrainingType}:</strong> {crossTrainingHours}h/week
                  </div>
                )}
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

          {/* Time Blocks (Optional) */}
          {availableDays.length > 0 && (
            <div style={{ marginBottom: '25px' }}>
              <label style={{ display: 'block', marginBottom: '10px', fontWeight: '600', fontSize: '15px' }}>
                Preferred Time Blocks (Optional)
              </label>
              <div style={{ fontSize: '13px', color: '#7f8c8d', marginBottom: '10px' }}>
                Select when you typically train on each day
              </div>
              {availableDays.map(day => (
                <div key={day} style={{ marginBottom: '15px' }}>
                  <div style={{ fontWeight: '600', fontSize: '14px', marginBottom: '8px', color: '#555' }}>
                    {day}:
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', paddingLeft: '15px' }}>
                    {TIME_BLOCKS.map(block => {
                      const isSelected = (timeBlocks[day] || []).includes(block);
                      return (
                        <button
                          key={block}
                          type="button"
                          onClick={() => handleTimeBlockToggle(day, block)}
                          style={{
                            padding: '6px 12px',
                            backgroundColor: isSelected ? '#3498db' : 'white',
                            color: isSelected ? 'white' : '#555',
                            border: isSelected ? '1px solid #3498db' : '1px solid #ddd',
                            borderRadius: '15px',
                            fontSize: '13px',
                            cursor: 'pointer',
                            fontWeight: isSelected ? '600' : 'normal'
                          }}
                        >
                          {block}
                        </button>
                      );
                    })}
                  </div>
                </div>
              ))}
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
              placeholder="e.g., Work 9-5 weekdays, family dinner 6pm, no early morning runs on weekends..."
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

            {/* Cross-Training */}
            <div style={{ marginBottom: '15px', padding: '15px', backgroundColor: 'white', borderRadius: '6px' }}>
              <label style={{ display: 'flex', alignItems: 'center', marginBottom: '10px', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={includeCrossTraining}
                  onChange={(e) => setIncludeCrossTraining(e.target.checked)}
                  style={{ marginRight: '10px', width: '18px', height: '18px', cursor: 'pointer' }}
                />
                <span style={{ fontWeight: '600', fontSize: '14px' }}>🚴 Cross-Training</span>
              </label>
              {includeCrossTraining && (
                <div style={{ paddingLeft: '28px' }}>
                  <label style={{ fontSize: '13px', color: '#555', display: 'block', marginBottom: '5px' }}>
                    Type:
                  </label>
                  <select
                    value={crossTrainingType}
                    onChange={(e) => setCrossTrainingType(e.target.value)}
                    style={{
                      width: '200px',
                      padding: '6px',
                      border: '1px solid #ddd',
                      borderRadius: '4px',
                      fontSize: '14px',
                      marginBottom: '10px'
                    }}
                  >
                    <option value="Cycling">Cycling</option>
                    <option value="Swimming">Swimming</option>
                    <option value="Rowing">Rowing</option>
                    <option value="Hiking">Hiking</option>
                    <option value="Skiing">Skiing</option>
                    <option value="Other">Other</option>
                  </select>
                  <label style={{ fontSize: '13px', color: '#555', display: 'block', marginBottom: '5px' }}>
                    Hours per week:
                  </label>
                  <input
                    type="number"
                    min="0.5"
                    max="20"
                    step="0.5"
                    value={crossTrainingHours}
                    onChange={(e) => setCrossTrainingHours(parseFloat(e.target.value))}
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
              {includeCrossTraining && <div>{crossTrainingType}: <strong>{crossTrainingHours}h</strong></div>}
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

