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
    elevation_gain_feet: ''
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
      elevation_gain_feet: ''
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
      elevation_gain_feet: goal.elevation_gain_feet?.toString() || ''
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
      
      // Only include elevation if it has a value (for backwards compatibility)
      if (formData.elevation_gain_feet && formData.elevation_gain_feet.trim()) {
        payload.elevation_gain_feet = parseInt(formData.elevation_gain_feet);
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
    const race = new Date(raceDate);
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

      {/* Form */}
      {showForm && (
        <div style={{
          backgroundColor: '#f8f9fa',
          padding: '20px',
          borderRadius: '8px',
          marginBottom: '20px',
          border: '2px solid #3498db'
        }}>
          <h3 style={{ marginTop: 0, marginBottom: '20px', color: '#2c3e50' }}>
            {editingGoal ? 'Edit Race Goal' : 'Add New Race Goal'}
          </h3>

          {error && (
            <div style={{
              padding: '12px',
              backgroundColor: '#fee',
              border: '1px solid #fcc',
              borderRadius: '4px',
              marginBottom: '15px',
              color: '#c33',
              fontSize: '14px'
            }}>
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px', marginBottom: '15px' }}>
              {/* Race Name */}
              <div style={{ gridColumn: '1 / -1' }}>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: '600', fontSize: '14px' }}>
                  Race Name <span style={{ color: '#e74c3c' }}>*</span>
                </label>
                <input
                  type="text"
                  value={formData.race_name}
                  onChange={(e) => setFormData({ ...formData, race_name: e.target.value })}
                  required
                  style={{
                    width: '100%',
                    padding: '10px',
                    border: '1px solid #ddd',
                    borderRadius: '4px',
                    fontSize: '14px'
                  }}
                  placeholder="e.g., Western States 100"
                />
              </div>

              {/* Race Date */}
              <div>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: '600', fontSize: '14px' }}>
                  Race Date <span style={{ color: '#e74c3c' }}>*</span>
                </label>
                <input
                  type="date"
                  value={formData.race_date}
                  onChange={(e) => setFormData({ ...formData, race_date: e.target.value })}
                  required
                  style={{
                    width: '100%',
                    padding: '10px',
                    border: '1px solid #ddd',
                    borderRadius: '4px',
                    fontSize: '14px'
                  }}
                />
              </div>

              {/* Priority */}
              <div>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: '600', fontSize: '14px' }}>
                  Priority <span style={{ color: '#e74c3c' }}>*</span>
                </label>
                <select
                  value={formData.priority}
                  onChange={(e) => setFormData({ ...formData, priority: e.target.value as 'A' | 'B' | 'C' })}
                  required
                  style={{
                    width: '100%',
                    padding: '10px',
                    border: '1px solid #ddd',
                    borderRadius: '4px',
                    fontSize: '14px'
                  }}
                >
                  <option value="A">A - Primary Focus (only one allowed)</option>
                  <option value="B">B - Fitness Check</option>
                  <option value="C">C - Training Volume</option>
                </select>
              </div>

              {/* Race Type */}
              <div>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: '600', fontSize: '14px' }}>
                  Race Type/Distance
                </label>
                <input
                  type="text"
                  value={formData.race_type}
                  onChange={(e) => setFormData({ ...formData, race_type: e.target.value })}
                  style={{
                    width: '100%',
                    padding: '10px',
                    border: '1px solid #ddd',
                    borderRadius: '4px',
                    fontSize: '14px'
                  }}
                  placeholder="e.g., 100 Mile Trail"
                />
              </div>

              {/* Target Time */}
              <div>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: '600', fontSize: '14px' }}>
                  Target Time
                </label>
                <input
                  type="text"
                  value={formData.target_time}
                  onChange={(e) => setFormData({ ...formData, target_time: e.target.value })}
                  style={{
                    width: '100%',
                    padding: '10px',
                    border: '1px solid #ddd',
                    borderRadius: '4px',
                    fontSize: '14px'
                  }}
                  placeholder="e.g., 24:00 or Sub-24"
                />
              </div>

              {/* Elevation Gain */}
              <div>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: '600', fontSize: '14px' }}>
                  Elevation Gain (ft)
                </label>
                <input
                  type="number"
                  value={formData.elevation_gain_feet}
                  onChange={(e) => setFormData({ ...formData, elevation_gain_feet: e.target.value })}
                  style={{
                    width: '100%',
                    padding: '10px',
                    border: '1px solid #ddd',
                    borderRadius: '4px',
                    fontSize: '14px'
                  }}
                  placeholder="e.g., 18000"
                  min="0"
                />
              </div>

              {/* Notes */}
              <div style={{ gridColumn: '1 / -1' }}>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: '600', fontSize: '14px' }}>
                  Notes
                </label>
                <textarea
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  style={{
                    width: '100%',
                    padding: '10px',
                    border: '1px solid #ddd',
                    borderRadius: '4px',
                    fontSize: '14px',
                    minHeight: '80px',
                    fontFamily: 'inherit'
                  }}
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
                  padding: '10px 20px',
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
                type="submit"
                disabled={isSaving}
                style={{
                  padding: '10px 20px',
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
                {isSaving ? 'Saving...' : (editingGoal ? 'Update Goal' : 'Save Goal')}
              </button>
            </div>
          </form>
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
                      {goal.race_type && (
                        <div>
                          <strong>Type:</strong> {goal.race_type}
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

