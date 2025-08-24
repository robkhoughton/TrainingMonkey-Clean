import React, { useState, useEffect } from 'react';
import './SettingsPage.css';

interface UserSettings {
  id: number;
  email: string;
  resting_hr: number;
  max_hr: number;
  gender: string;
  hr_zones_method: string;
  primary_sport: string;
  secondary_sport?: string;
  training_experience: string;
  current_phase: string;
  race_goal_date?: string;
  weekly_training_hours: number;
  acwr_alert_threshold: number;
  injury_risk_alerts: boolean;
  recommendation_style: string;
  coaching_tone: string;
  is_admin: boolean;
}

interface HeartRateZones {
  zone1: { min: number; max: number; name: string };
  zone2: { min: number; max: number; name: string };
  zone3: { min: number; max: number; name: string };
  zone4: { min: number; max: number; name: string };
  zone5: { min: number; max: number; name: string };
}

interface HeartRateZone {
  min: number;
  max: number;
  name: string;
  min_formula: string;
  max_formula: string;
  min_calculation: number;
  max_calculation: number;
  is_custom_min?: boolean;
  is_custom_max?: boolean;
}

interface HeartRateZones {
  zone1: HeartRateZone;
  zone2: HeartRateZone;
  zone3: HeartRateZone;
  zone4: HeartRateZone;
  zone5: HeartRateZone;
}

interface ZonesResponse {
  zones: HeartRateZones;
  calculated_zones: HeartRateZones;
  has_custom_zones: boolean;
  method: string;
  resting_hr: number;
  max_hr: number;
  hr_reserve?: number;
}

export const SettingsPage: React.FC = () => {
  const [settings, setSettings] = useState<UserSettings | null>(null);
  const [zones, setZones] = useState<HeartRateZones | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'profile' | 'training' | 'alerts'>('profile');
  const [zonesData, setZonesData] = useState<ZonesResponse | null>(null);
  const [editingZones, setEditingZones] = useState<{[key: string]: {min?: number, max?: number}}>({});
  const [showCalculations, setShowCalculations] = useState(true);

  // Load settings on component mount
  useEffect(() => {
    loadSettings();
    loadHeartRateZones();
  }, []);

  const loadSettings = async () => {
    try {
      const response = await fetch('/settings');
      if (response.ok) {
        const data = await response.json();
        setSettings(data.settings);
      } else {
        setError('Failed to load settings');
      }
    } catch (err) {
      setError('Network error loading settings');
    } finally {
      setLoading(false);
    }
  };

  const loadHeartRateZones = async () => {
    try {
      const response = await fetch('/api/settings/heart-rate-zones');
      if (response.ok) {
        const data = await response.json();
        setZonesData(data);
        // setZones(data.zones); // Removed - using zonesData instead
      }
    } catch (err) {
      console.error('Error loading heart rate zones:', err);
    }
  };

    // Enhanced save function that sends incremental changes
    const saveCustomZones = async () => {
      if (!editingZones || Object.keys(editingZones).length === 0) {
        setError('No changes to save');
        return;
      }

      setSaving(true);
      setError(null);
      setSuccess(null);

      try {
        const response = await fetch('/api/settings/heart-rate-zones', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ custom_zones: editingZones })
        });

        if (response.ok) {
          await response.json(); // Don't store if not using
          setSuccess(`Custom heart rate zones saved successfully! Updated: ${Object.keys(editingZones).join(', ')}`);
          setEditingZones({}); // Clear editing state
          await loadHeartRateZones(); // Reload zones to show merged result
        } else {
          const errorData = await response.json();
          setError(errorData.errors ? errorData.errors.join(', ') : 'Failed to save custom zones');
        }
      } catch (err) {
        setError('Network error saving custom zones');
      } finally {
        setSaving(false);
      }
    };

    const handleZoneEdit = (zoneKey: string, boundary: 'min' | 'max', value: string) => {
      const numValue = parseInt(value);
      if (isNaN(numValue) || numValue < 40 || numValue > 220) {
        return; // Invalid input
      }

      setEditingZones(prev => {
        const newEditing = { ...prev };

        // Update the current zone boundary
        if (!newEditing[zoneKey]) {
          newEditing[zoneKey] = {};
        }
        newEditing[zoneKey][boundary] = numValue;

        // Automatic boundary synchronization
        const zoneNumbers = ['zone1', 'zone2', 'zone3', 'zone4', 'zone5'];
        const currentZoneIndex = zoneNumbers.indexOf(zoneKey);

        if (boundary === 'max' && currentZoneIndex < 4) {
          // When setting zone max, update next zone's min
          const nextZone = zoneNumbers[currentZoneIndex + 1];
          if (!newEditing[nextZone]) {
            newEditing[nextZone] = {};
          }
          newEditing[nextZone]['min'] = numValue;
        }

        if (boundary === 'min' && currentZoneIndex > 0) {
          // When setting zone min, update previous zone's max
          const prevZone = zoneNumbers[currentZoneIndex - 1];
          if (!newEditing[prevZone]) {
            newEditing[prevZone] = {};
          }
          newEditing[prevZone]['max'] = numValue;
        }

        return newEditing;
      });
    };

    // Add this function to reset a zone to calculated values
    const resetZoneToCalculated = (zoneKey: string) => {
      setEditingZones(prev => {
        const newEditing = { ...prev };
        delete newEditing[zoneKey];
        return newEditing;
      });
    };

  const updateSettings = async (updates: Partial<UserSettings>) => {
    setSaving(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await fetch('/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates)
      });

      if (response.ok) {
        setSuccess('Settings updated successfully!');
        await loadSettings(); // Reload to get updated data

        // If heart rate changed, reload zones
        if (updates.resting_hr || updates.max_hr || updates.hr_zones_method) {
          await loadHeartRateZones();
        }
      } else {
        const errorData = await response.json();
        setError(errorData.errors ? errorData.errors.join(', ') : 'Failed to update settings');
      }
    } catch (err) {
      setError('Network error updating settings');
    } finally {
      setSaving(false);
    }
  };

  const handleInputChange = (field: keyof UserSettings, value: any) => {
    if (settings) {
      const updatedSettings = { ...settings, [field]: value };
      setSettings(updatedSettings);
    }
  };

  const handleSave = () => {
    if (settings) {
      // Only send changed fields (you could implement a diff here)
      updateSettings(settings);
    }
  };

  if (loading) {
    return <div className="settings-loading">Loading settings...</div>;
  }

  if (!settings) {
    return <div className="settings-error">Failed to load settings</div>;
  }

  return (
    <div className="settings-page">
      <div className="settings-header">
        <h1>⚙️ Training Settings</h1>
        <p>Customize your training analysis and recommendations</p>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {success && <div className="alert alert-success">{success}</div>}

      <div className="settings-tabs">
        <button
          className={`tab ${activeTab === 'profile' ? 'active' : ''}`}
          onClick={() => setActiveTab('profile')}
        >
          👤 Profile
        </button>
        <button
          className={`tab ${activeTab === 'training' ? 'active' : ''}`}
          onClick={() => setActiveTab('training')}
        >
          🏃 Training
        </button>
        <button
          className={`tab ${activeTab === 'alerts' ? 'active' : ''}`}
          onClick={() => setActiveTab('alerts')}
        >
          🚨 Coaching Style
        </button>
      </div>

      <div className="settings-content">
        {activeTab === 'profile' && (
          <div className="settings-section">
            <h2>Profile Settings</h2>

            <div className="form-grid">
              <div className="form-group">
                <label htmlFor="email">Email</label>
                <input
                  type="email"
                  id="email"
                  value={settings.email}
                  disabled
                  className="readonly"
                />
              </div>

              <div className="form-group">
                <label htmlFor="gender">Gender</label>
                <select
                  id="gender"
                  value={settings.gender || 'male'}
                  onChange={(e) => handleInputChange('gender', e.target.value)}
                >
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                  <option value="other">Other</option>
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="resting_hr">Resting Heart Rate (bpm)</label>
                <input
                  type="number"
                  id="resting_hr"
                  min="30"
                  max="100"
                  value={settings.resting_hr}
                  onChange={(e) => handleInputChange('resting_hr', parseInt(e.target.value))}
                />
                <small>Typically measured first thing in the morning</small>
              </div>

              <div className="form-group">
                <label htmlFor="max_hr">Maximum Heart Rate (bpm)</label>
                <input
                  type="number"
                  id="max_hr"
                  min="120"
                  max="220"
                  value={settings.max_hr}
                  onChange={(e) => handleInputChange('max_hr', parseInt(e.target.value))}
                />
                <small>Your highest recorded heart rate during exercise</small>
              </div>

              <div className="form-group">
                <label htmlFor="hr_zones_method">Heart Rate Zone Method</label>
                <select
                  id="hr_zones_method"
                  value={settings.hr_zones_method || 'percentage'}
                  onChange={(e) => handleInputChange('hr_zones_method', e.target.value)}
                >
                  <option value="percentage">Percentage of Max HR</option>
                  <option value="reserve">Heart Rate Reserve (Karvonen)</option>
                </select>
              </div>
            </div>

            {zonesData && (
              <div className="heart-rate-zones">
                <div className="zones-header">
                  <h3>Your Heart Rate Zones</h3>
                  <div className="zones-controls">
                    <button
                      type="button"
                      className="btn-toggle"
                      onClick={() => setShowCalculations(!showCalculations)}
                    >
                      {showCalculations ? 'Hide' : 'Show'} Calculations
                    </button>
                    {Object.keys(editingZones).length > 0 && (
                      <div className="zones-actions">
                        <button
                          type="button"
                          className="btn btn-primary btn-sm"
                          onClick={saveCustomZones}
                          disabled={saving}
                        >
                          {saving ? 'Saving...' : 'Save Custom Zones'}
                        </button>
                        <button
                          type="button"
                          className="btn btn-secondary btn-sm"
                          onClick={() => setEditingZones({})}
                        >
                          Cancel Changes
                        </button>
                      </div>
                    )}
                  </div>
                </div>

                <div className="zones-method-info">
                  <strong>Method:</strong> {zonesData.method === 'percentage' ? 'Percentage of Max HR' : 'Heart Rate Reserve (Karvonen)'}
                  {zonesData.hr_reserve && (
                    <span className="hr-reserve"> | HR Reserve: {zonesData.hr_reserve} bpm</span>
                  )}
                </div>

                <div className="zones-grid-enhanced">
                  {Object.entries(zonesData.zones).map(([zoneKey, zone]) => {
                    const zoneNumber = zoneKey.replace('zone', '');
                    const editingZone = editingZones[zoneKey] || {};
                    const displayMin = editingZone.min !== undefined ? editingZone.min : zone.min;
                    const displayMax = editingZone.max !== undefined ? editingZone.max : zone.max;
                    const hasCustomMin = zone.is_custom_min || editingZone.min !== undefined;
                    const hasCustomMax = zone.is_custom_max || editingZone.max !== undefined;
                    const hasEdits = editingZone.min !== undefined || editingZone.max !== undefined;

                    return (
                      <div key={zoneKey} className={`zone-card-enhanced zone-${zoneKey} ${hasEdits ? 'editing' : ''}`}>
                        <div className="zone-header">
                          <div className="zone-number">Zone {zoneNumber}</div>
                          <div className="zone-name">{zone.name}</div>
                          {(hasCustomMin || hasCustomMax) && (
                            <div className="custom-indicator">Custom</div>
                          )}
                        </div>

                        <div className="zone-boundaries">
                          {/* Minimum Boundary */}
                          <input
                              type="number"
                              className={`boundary-input ${hasCustomMin ? 'custom' : 'calculated'} ${
                                // Check if this min boundary was automatically synchronized
                                (zoneKey === 'zone2' && editingZones.zone1?.max !== undefined) ||
                                (zoneKey === 'zone3' && editingZones.zone2?.max !== undefined) ||
                                (zoneKey === 'zone4' && editingZones.zone3?.max !== undefined) ||
                                (zoneKey === 'zone5' && editingZones.zone4?.max !== undefined)
                                ? 'synchronized' : ''
                              }`}
                              value={displayMin}
                              min="40"
                              max="220"
                              onChange={(e) => handleZoneEdit(zoneKey, 'min', e.target.value)}
                            />

                          {/* Maximum Boundary */}
                          <input
                              type="number"
                              className={`boundary-input ${hasCustomMax ? 'custom' : 'calculated'} ${
                                // Check if this max boundary was automatically synchronized
                                (zoneKey === 'zone1' && editingZones.zone2?.min !== undefined) ||
                                (zoneKey === 'zone2' && editingZones.zone3?.min !== undefined) ||
                                (zoneKey === 'zone3' && editingZones.zone4?.min !== undefined) ||
                                (zoneKey === 'zone4' && editingZones.zone5?.min !== undefined)
                                ? 'synchronized' : ''
                              }`}
                              value={displayMax}
                              min="40"
                              max="220"
                              onChange={(e) => handleZoneEdit(zoneKey, 'max', e.target.value)}
                            />
                        </div>

                        {hasEdits && (
                          <div className="zone-actions">
                            <button
                              type="button"
                              className="btn-reset"
                              onClick={() => resetZoneToCalculated(zoneKey)}
                              title="Reset to calculated values"
                            >
                              ↺ Reset
                            </button>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>

                <div className="zones-legend">
                  <div className="legend-item">
                    <span className="legend-color calculated"></span>
                    <span>Calculated values</span>
                  </div>
                  <div className="legend-item">
                    <span className="legend-color custom"></span>
                    <span>Custom values</span>
                  </div>
                  <div className="legend-note">
                    💡 Edit any boundary to create custom zones. Changes are highlighted and saved separately.
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'training' && (
          <div className="settings-section">
            <h2>Training Focus</h2>

            <div className="form-grid">
              <div className="form-group">
                <label htmlFor="primary_sport">Primary Sport</label>
                <select
                  id="primary_sport"
                  value={settings.primary_sport || 'running'}
                  onChange={(e) => handleInputChange('primary_sport', e.target.value)}
                >
                  <option value="running">Running</option>
                  <option value="cycling">Cycling</option>
                  <option value="swimming">Swimming</option>
                  <option value="triathlon">Triathlon</option>
                  <option value="other">Other</option>
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="training_experience">Training Experience</label>
                <select
                  id="training_experience"
                  value={settings.training_experience || 'intermediate'}
                  onChange={(e) => handleInputChange('training_experience', e.target.value)}
                >
                  <option value="beginner">Beginner (less than 1 year)</option>
                  <option value="intermediate">Intermediate (1-3 years)</option>
                  <option value="advanced">Advanced (3-5 years)</option>
                  <option value="expert">Expert (5+ years)</option>
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="current_phase">Current Training Phase</label>
                <select
                  id="current_phase"
                  value={settings.current_phase || 'base'}
                  onChange={(e) => handleInputChange('current_phase', e.target.value)}
                >
                  <option value="base">Base Building</option>
                  <option value="build">Build/Intensity</option>
                  <option value="peak">Peak/Race Prep</option>
                  <option value="recovery">Recovery/Transition</option>
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="weekly_training_hours">Weekly Training Hours</label>
                <input
                  type="number"
                  id="weekly_training_hours"
                  min="1"
                  max="40"
                  value={settings.weekly_training_hours || 8}
                  onChange={(e) => handleInputChange('weekly_training_hours', parseInt(e.target.value))}
                />
              </div>

              <div className="form-group">
                  <label htmlFor="race_goal_date">Next "A" Race Date</label>
                  <input
                    type="date"
                    id="race_goal_date"
                    value={settings.race_goal_date || ''}
                    onChange={(e) => {
                      const dateValue = e.target.value;
                      console.log('Date input changed to:', dateValue); // Debug logging
                      handleInputChange('race_goal_date', dateValue);
                    }}
                  />
                  <small>Set a target race date to focus your training</small>
                </div>
            </div>
          </div>
        )}

        {activeTab === 'alerts' && (
          <div className="settings-section">
            <h2>Coaching Style & AI Preferences</h2>

            <div className="form-grid">
              <div className="form-group">
                <label htmlFor="acwr_alert_threshold">ACWR Alert Threshold</label>
                <input
                  type="number"
                  id="acwr_alert_threshold"
                  min="1.0"
                  max="2.0"
                  step="0.1"
                  value={settings.acwr_alert_threshold || 1.30}
                  onChange={(e) => handleInputChange('acwr_alert_threshold', parseFloat(e.target.value))}
                />
                <small>Alert when ACWR exceeds this value (recommended: 1.30)</small>
              </div>

              <div className="form-group checkbox-group">
                <label>
                  <input
                    type="checkbox"
                    checked={settings.injury_risk_alerts}
                    onChange={(e) => handleInputChange('injury_risk_alerts', e.target.checked)}
                  />
                  Enable injury risk alerts
                </label>
              </div>

              <div className="form-group">
                <label htmlFor="recommendation_style">AI Recommendation Style</label>
                <select
                  id="recommendation_style"
                  value={settings.recommendation_style || 'balanced'}
                  onChange={(e) => handleInputChange('recommendation_style', e.target.value)}
                >
                  <option value="conservative">Conservative</option>
                  <option value="balanced">Balanced</option>
                  <option value="aggressive">Aggressive</option>
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="coaching_tone">AI Coaching Tone</label>
                <select
                  id="coaching_tone"
                  value={settings.coaching_tone || 'supportive'}
                  onChange={(e) => handleInputChange('coaching_tone', e.target.value)}
                >
                  <option value="supportive">Supportive</option>
                  <option value="motivational">Motivational</option>
                  <option value="analytical">Analytical</option>
                  <option value="casual">Casual</option>
                </select>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="form-actions">
        <button
          className="btn btn-primary"
          onClick={handleSave}
          disabled={saving}
        >
          {saving ? 'Saving...' : 'Save Settings'}
        </button>

        <button
          className="btn btn-secondary"
          onClick={loadSettings}
          disabled={saving}
        >
          Reset Changes
        </button>
      </div>

      <div className="save-note">
        <p>💡 Settings are automatically applied to existing activities and future AI recommendations.</p>
      </div>
    </div>
  );
};

export default SettingsPage;