import React, { useState } from 'react';
import styles from './TrainingLoadDashboard.module.css';

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

interface RaceGoalsManagerProps {
  goals: RaceGoal[];
  onGoalsChange: () => void;
}

// ============================================================================
// COMPONENT
// ============================================================================

const RaceGoalsManager: React.FC<RaceGoalsManagerProps> = ({ goals, onGoalsChange }) => {
  const [showForm, setShowForm] = useState(false);
  const [editingGoal, setEditingGoal] = useState<RaceGoal | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form state
  const [formData, setFormData] = useState({
    race_name: '',
    race_date: '',
    race_type: '',
    priority: 'B' as 'A' | 'B' | 'C',
    target_time: '',
    notes: '',
    elevation_gain_feet: '',
    distance_miles: ''
  });

  // ============================================================================
  // HANDLERS
  // ============================================================================

  const handleAddNew = () => {
    setEditingGoal(null);
    setFormData({
      race_name: '',
      race_date: '',
      race_type: '',
      priority: 'B',
      target_time: '',
      notes: '',
      elevation_gain_feet: '',
      distance_miles: ''
    });
    setShowForm(true);
    setError(null);
  };

  const handleEdit = (goal: RaceGoal) => {
    setEditingGoal(goal);
    setFormData({
      race_name: goal.race_name,
      race_date: goal.race_date,
      race_type: goal.race_type || '',
      priority: goal.priority,
      target_time: goal.target_time || '',
      notes: goal.notes || '',
      elevation_gain_feet: goal.elevation_gain_feet?.toString() || '',
      distance_miles: goal.distance_miles?.toString() || ''
    });
    setShowForm(true);
    setError(null);
  };

  const handleCancel = () => {
    setShowForm(false);
    setEditingGoal(null);
    setError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setError(null);

    try {
      const payload: any = {
        race_name: formData.race_name.trim(),
        race_date: formData.race_date,
        race_type: formData.race_type.trim() || null,
        priority: formData.priority,
        target_time: formData.target_time.trim() || null,
        notes: formData.notes.trim() || null
      };
      
      // Only include elevation/distance if they have values (backwards compatibility)
      if (formData.elevation_gain_feet && formData.elevation_gain_feet.trim()) {
        payload.elevation_gain_feet = parseInt(formData.elevation_gain_feet);
      }
      if (formData.distance_miles && formData.distance_miles.trim()) {
        payload.distance_miles = parseFloat(formData.distance_miles);
      }

      const url = editingGoal
        ? `/api/coach/race-goals/${editingGoal.id}`
        : '/api/coach/race-goals';

      const method = editingGoal ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to save race goal');
      }

      // Success
      console.log('[RaceGoalsManager] Goal saved successfully, refreshing data...');
      setShowForm(false);
      setEditingGoal(null);
      
      // Small delay to ensure database transaction completes
      await new Promise(resolve => setTimeout(resolve, 100));
      onGoalsChange();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save race goal');
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async (goalId: number) => {
    if (!window.confirm('Are you sure you want to delete this race goal?')) {
      return;
    }

    try {
      const response = await fetch(`/api/coach/race-goals/${goalId}`, {
        method: 'DELETE'
      });

      if (!response.ok) {
        throw new Error('Failed to delete race goal');
      }

      onGoalsChange();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete race goal');
    }
  };

  // ============================================================================
  // HELPERS
  // ============================================================================

  const calculateDaysAway = (raceDate: string): number => {
    const today = new Date();
    const race = new Date(raceDate + 'T12:00:00');
    const diffTime = race.getTime() - today.getTime();
    return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  };

  const getPriorityColor = (priority: string): string => {
    switch (priority) {
      case 'A': return '#e74c3c'; // red
      case 'B': return '#f39c12'; // orange
      case 'C': return '#3498db'; // blue
      default: return '#95a5a6';
    }
  };

  // Sort goals by date
  const sortedGoals = [...goals].sort((a, b) => 
    new Date(a.race_date).getTime() - new Date(b.race_date).getTime()
  );

  // ============================================================================
  // RENDER
  // ============================================================================

  return (
    <div>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h2 className={styles.cardHeader}>Race Goals ({goals.length})</h2>
        <button
          onClick={handleAddNew}
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
          + Add Race Goal
        </button>
      </div>

      {/* Error Display */}
      {error && !showForm && (
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

      {/* Form — Tactical Modal */}
      {showForm && (
        <div
          onClick={(e) => { if (e.target === e.currentTarget) handleCancel(); }}
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.65)',
            zIndex: 1000,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '20px',
          }}
        >
        <div style={{
          backgroundColor: '#1B2E4B',
          backgroundImage: 'linear-gradient(135deg, rgba(255,255,255,0.04) 25%, transparent 25%), linear-gradient(225deg, rgba(255,255,255,0.04) 25%, transparent 25%), linear-gradient(315deg, rgba(255,255,255,0.04) 25%, transparent 25%), linear-gradient(45deg, rgba(255,255,255,0.04) 25%, transparent 25%)',
          backgroundSize: '4px 4px',
          border: '1px solid rgba(255,87,34,0.7)',
          borderRadius: '6px',
          overflow: 'hidden',
          width: '100%',
          maxWidth: '560px',
          maxHeight: '90vh',
          overflowY: 'auto',
        }}>
          {/* Header strip */}
          <div style={{
            background: 'linear-gradient(90deg, #E6F0FF 0%, #7D9CB8 50%, #1B2E4B 100%)',
            padding: '0.75rem 1.25rem',
            fontSize: '10px',
            letterSpacing: '0.15em',
            fontWeight: '700',
            color: '#1B2E4B',
            textTransform: 'uppercase',
          }}>
            {editingGoal ? 'Modify Goal' : 'Configure Target'}
          </div>

          <div style={{ padding: '20px' }}>
            {error && (
              <div style={{
                padding: '10px 14px',
                background: 'rgba(239,68,68,0.15)',
                border: '1px solid rgba(239,68,68,0.4)',
                borderRadius: '4px',
                marginBottom: '16px',
                color: '#fca5a5',
                fontSize: '13px',
              }}>
                {error}
              </div>
            )}

            <style>{`
              .ytm-form-input {
                width: 100%;
                padding: 8px 10px;
                background: #162440;
                border: 1px solid rgba(125,156,184,0.3);
                border-radius: 4px;
                font-size: 0.875rem;
                color: #E6F0FF;
                box-sizing: border-box;
              }
              .ytm-form-input::placeholder { color: rgba(230,240,255,0.25); }
              .ytm-form-input:focus {
                outline: none;
                border-color: #7D9CB8;
                background: #1a2d4e;
                box-shadow: 0 0 0 2px rgba(125,156,184,0.2);
              }
              .ytm-form-select {
                appearance: none;
                background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='6'%3E%3Cpath d='M0 0l5 6 5-6z' fill='%237D9CB8'/%3E%3C/svg%3E");
                background-repeat: no-repeat;
                background-position: right 10px center;
                padding-right: 28px;
              }
              .ytm-form-select option { background: #1B2E4B; color: #E6F0FF; }
              .ytm-form-input[type=number]::-webkit-inner-spin-button,
              .ytm-form-input[type=number]::-webkit-outer-spin-button { -webkit-appearance: none; margin: 0; }
              .ytm-form-input[type=number] { -moz-appearance: textfield; }
            `}</style>

            <form onSubmit={handleSubmit}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px', marginBottom: '20px' }}>

                {/* Race Name */}
                <div style={{ gridColumn: '1 / -1' }}>
                  <label style={{ display: 'block', marginBottom: '5px', fontSize: '0.7rem', fontWeight: '700', letterSpacing: '0.12em', textTransform: 'uppercase', color: '#7D9CB8' }}>
                    Race Name <span style={{ color: '#FF5722' }}>*</span>
                  </label>
                  <input
                    type="text"
                    value={formData.race_name}
                    onChange={(e) => setFormData({ ...formData, race_name: e.target.value })}
                    required
                    className="ytm-form-input"
                    placeholder="e.g., Western States 100"
                  />
                </div>

                {/* Race Date */}
                <div>
                  <label style={{ display: 'block', marginBottom: '5px', fontSize: '0.7rem', fontWeight: '700', letterSpacing: '0.12em', textTransform: 'uppercase', color: '#7D9CB8' }}>
                    Race Date <span style={{ color: '#FF5722' }}>*</span>
                  </label>
                  <input
                    type="date"
                    value={formData.race_date}
                    onChange={(e) => setFormData({ ...formData, race_date: e.target.value })}
                    required
                    className="ytm-form-input"
                  />
                </div>

                {/* Priority */}
                <div>
                  <label style={{ display: 'block', marginBottom: '5px', fontSize: '0.7rem', fontWeight: '700', letterSpacing: '0.12em', textTransform: 'uppercase', color: '#7D9CB8' }}>
                    Priority <span style={{ color: '#FF5722' }}>*</span>
                  </label>
                  <select
                    value={formData.priority}
                    onChange={(e) => setFormData({ ...formData, priority: e.target.value as 'A' | 'B' | 'C' })}
                    required
                    className="ytm-form-input ytm-form-select"
                  >
                    <option value="A">A — Primary Focus</option>
                    <option value="B">B — Fitness Check</option>
                    <option value="C">C — Training Volume</option>
                  </select>
                </div>

                {/* Race Type */}
                <div>
                  <label style={{ display: 'block', marginBottom: '5px', fontSize: '0.7rem', fontWeight: '700', letterSpacing: '0.12em', textTransform: 'uppercase', color: '#7D9CB8' }}>
                    Type
                  </label>
                  <select
                    value={formData.race_type}
                    onChange={(e) => setFormData({ ...formData, race_type: e.target.value })}
                    className="ytm-form-input ytm-form-select"
                  >
                    <option value="">—</option>
                    <option value="Trail">Trail</option>
                    <option value="Road">Road</option>
                    <option value="Other">Other</option>
                  </select>
                </div>

                {/* Distance */}
                <div>
                  <label style={{ display: 'block', marginBottom: '5px', fontSize: '0.7rem', fontWeight: '700', letterSpacing: '0.12em', textTransform: 'uppercase', color: '#7D9CB8' }}>
                    Distance <span style={{ color: 'rgba(125,156,184,0.6)', fontWeight: '400', textTransform: 'none', letterSpacing: 0 }}>mi</span>
                  </label>
                  <input
                    type="number"
                    value={formData.distance_miles}
                    onChange={(e) => setFormData({ ...formData, distance_miles: e.target.value })}
                    className="ytm-form-input"
                    placeholder="50"
                    min="0"
                    step="0.1"
                  />
                </div>

                {/* Elevation Gain */}
                <div>
                  <label style={{ display: 'block', marginBottom: '5px', fontSize: '0.7rem', fontWeight: '700', letterSpacing: '0.12em', textTransform: 'uppercase', color: '#7D9CB8' }}>
                    Elevation <span style={{ color: 'rgba(125,156,184,0.6)', fontWeight: '400', textTransform: 'none', letterSpacing: 0 }}>ft</span>
                  </label>
                  <input
                    type="number"
                    value={formData.elevation_gain_feet}
                    onChange={(e) => setFormData({ ...formData, elevation_gain_feet: e.target.value })}
                    className="ytm-form-input"
                    placeholder="18000"
                    min="0"
                  />
                </div>

                {/* Target Time */}
                <div>
                  <label style={{ display: 'block', marginBottom: '5px', fontSize: '0.7rem', fontWeight: '700', letterSpacing: '0.12em', textTransform: 'uppercase', color: '#7D9CB8' }}>
                    Target Time
                  </label>
                  <input
                    type="text"
                    value={formData.target_time}
                    onChange={(e) => setFormData({ ...formData, target_time: e.target.value })}
                    className="ytm-form-input"
                    placeholder="24:00 or Sub-24"
                  />
                </div>

                {/* Notes */}
                <div style={{ gridColumn: '1 / -1' }}>
                  <label style={{ display: 'block', marginBottom: '5px', fontSize: '0.7rem', fontWeight: '700', letterSpacing: '0.12em', textTransform: 'uppercase', color: '#7D9CB8' }}>
                    Notes
                  </label>
                  <textarea
                    value={formData.notes}
                    onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                    className="ytm-form-input"
                    style={{ minHeight: '72px', fontFamily: 'inherit', resize: 'vertical' }}
                    placeholder="Course notes, goals, strategy..."
                  />
                </div>
              </div>

              {/* Form Actions */}
              <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
                <button
                  type="button"
                  onClick={handleCancel}
                  disabled={isSaving}
                  style={{
                    padding: '10px 16px',
                    background: 'transparent',
                    color: '#7D9CB8',
                    border: '1px solid rgba(125,156,184,0.3)',
                    borderRadius: '4px',
                    cursor: isSaving ? 'not-allowed' : 'pointer',
                    fontSize: '0.8rem',
                    fontWeight: '600',
                    letterSpacing: '0.05em',
                    opacity: isSaving ? 0.5 : 1,
                  }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSaving}
                  style={{
                    padding: '10px 24px',
                    background: isSaving ? 'rgba(255,87,34,0.5)' : '#FF5722',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: isSaving ? 'not-allowed' : 'pointer',
                    fontSize: '0.8rem',
                    fontWeight: '700',
                    letterSpacing: '0.08em',
                    textTransform: 'uppercase',
                  }}
                >
                  {isSaving ? 'Working...' : (editingGoal ? 'Commit Changes' : 'Set Target')}
                </button>
              </div>
            </form>
          </div>
        </div>
        </div>
      )}

      {/* Goals List */}
      {sortedGoals.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '40px 20px', color: '#95a5a6' }}>
          <p style={{ fontSize: '18px', marginBottom: '10px' }}>No race goals yet</p>
          <p style={{ fontSize: '14px' }}>Add your first race goal to unlock personalized training programs!</p>
        </div>
      ) : (
        <div style={{ display: 'grid', gap: '15px' }}>
          {sortedGoals.map(goal => {
            const daysAway = calculateDaysAway(goal.race_date);
            const isPast = daysAway < 0;

            return (
              <div
                key={goal.id}
                style={{
                  border: '1px solid #e1e8ed',
                  borderRadius: '8px',
                  padding: '15px',
                  backgroundColor: isPast ? '#f5f5f5' : 'white',
                  opacity: isPast ? 0.7 : 1
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div style={{ flex: 1 }}>
                    {/* Race Name & Priority Badge */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
                      <h3 style={{ margin: 0, fontSize: '18px', color: '#2c3e50' }}>
                        {goal.race_name}
                      </h3>
                      <span style={{
                        padding: '4px 10px',
                        backgroundColor: getPriorityColor(goal.priority),
                        color: 'white',
                        borderRadius: '12px',
                        fontSize: '12px',
                        fontWeight: 'bold'
                      }}>
                        {goal.priority}
                      </span>
                      {isPast && (
                        <span style={{
                          padding: '4px 10px',
                          backgroundColor: '#95a5a6',
                          color: 'white',
                          borderRadius: '12px',
                          fontSize: '12px'
                        }}>
                          Past
                        </span>
                      )}
                    </div>

                    {/* Date & Days Away */}
                    <div style={{ marginBottom: '8px', color: '#7f8c8d', fontSize: '14px' }}>
                      📅 {new Date(goal.race_date).toLocaleDateString('en-US', { 
                        weekday: 'long', 
                        year: 'numeric', 
                        month: 'long', 
                        day: 'numeric' 
                      })}
                      {!isPast && (
                        <span style={{ marginLeft: '10px', fontWeight: '600', color: '#2c3e50' }}>
                          ({daysAway} {daysAway === 1 ? 'day' : 'days'} away)
                        </span>
                      )}
                    </div>

                    {/* Race Type, Target Time & Elevation */}
                    <div style={{ display: 'flex', gap: '20px', fontSize: '14px', color: '#7f8c8d' }}>
                      {(goal.race_type || goal.distance_miles) && (
                        <div>
                          <strong>Type:</strong>{' '}
                          {[
                            goal.distance_miles ? `${goal.distance_miles}mi` : null,
                            goal.race_type || null
                          ].filter(Boolean).join(' ')}
                        </div>
                      )}
                      {goal.target_time && (
                        <div>
                          <strong>Target:</strong> {goal.target_time}
                        </div>
                      )}
                      {goal.elevation_gain_feet != null && goal.elevation_gain_feet > 0 && (
                        <div>
                          <strong>Vert:</strong> {goal.elevation_gain_feet.toLocaleString()} ft
                        </div>
                      )}
                    </div>

                    {/* Notes */}
                    {goal.notes && (
                      <div style={{
                        marginTop: '10px',
                        padding: '10px',
                        backgroundColor: '#f8f9fa',
                        borderRadius: '4px',
                        fontSize: '14px',
                        color: '#555'
                      }}>
                        {goal.notes}
                      </div>
                    )}
                  </div>

                  {/* Action Buttons */}
                  <div style={{ display: 'flex', gap: '8px', marginLeft: '15px' }}>
                    <button
                      onClick={() => handleEdit(goal)}
                      style={{
                        padding: '6px 12px',
                        backgroundColor: '#3498db',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        fontSize: '13px'
                      }}
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDelete(goal.id)}
                      style={{
                        padding: '6px 12px',
                        backgroundColor: '#e74c3c',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        fontSize: '13px'
                      }}
                    >
                      Delete
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Help Text */}
      <div style={{
        marginTop: '20px',
        padding: '15px',
        backgroundColor: '#e8f4f8',
        borderRadius: '6px',
        fontSize: '13px',
        color: '#555'
      }}>
        <strong>💡 Priority Guide:</strong>
        <ul style={{ marginTop: '8px', marginBottom: 0, paddingLeft: '20px' }}>
          <li><strong>A Race:</strong> Your primary season focus. Only one A race allowed at a time. Training programs optimize for this race.</li>
          <li><strong>B Race:</strong> Secondary races used to evaluate fitness and fine-tune race-day execution.</li>
          <li><strong>C Race:</strong> Training volume races. Good for testing gear, nutrition, or pacing strategies.</li>
        </ul>
      </div>
    </div>
  );
};

export default RaceGoalsManager;

