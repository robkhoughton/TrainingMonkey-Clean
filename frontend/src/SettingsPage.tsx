import React, { useState, useEffect } from 'react';
import styles from './TrainingLoadDashboard.module.css'; // Use consistent styling
import CoachingStyleSpectrum from './CoachingStyleSpectrum';

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
  coaching_style_spectrum?: number;
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
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [zonesData, setZonesData] = useState<ZonesResponse | null>(null);
  const [editingZones, setEditingZones] = useState<{[key: string]: {min?: number, max?: number}}>({});
  const [showCalculations, setShowCalculations] = useState(true);
  const [activeSection, setActiveSection] = useState<string>('profile');
  const [spectrumValue, setSpectrumValue] = useState<number>(50);


  // Load settings on component mount
  useEffect(() => {
    loadSettings();
    loadHeartRateZones();
  }, []);


    const mapSpectrumToCoachingTone = (spectrum_value: number): string => {
      if (spectrum_value <= 25) return 'casual';
      if (spectrum_value <= 50) return 'supportive';
      if (spectrum_value <= 75) return 'motivational';
      return 'analytical';
    };

    const loadSettings = async () => {
      try {
        const [settingsResponse, spectrumResponse] = await Promise.all([
          fetch('/settings'),
          fetch('/api/user-settings')
        ]);

        if (settingsResponse.ok) {
          const data = await settingsResponse.json();
          setSettings(data.settings);
        }

        if (spectrumResponse.ok) {
          const spectrumData = await spectrumResponse.json();
          setSpectrumValue(spectrumData.coaching_style_spectrum || 50);
        } else {
          // If spectrum endpoint fails, try to derive from coaching_tone
          if (settings?.coaching_tone) {
            const derivedValue = settings.coaching_tone === 'casual' ? 12 :
                               settings.coaching_tone === 'supportive' ? 37 :
                               settings.coaching_tone === 'motivational' ? 62 :
                               settings.coaching_tone === 'analytical' ? 87 : 50;
            setSpectrumValue(derivedValue);
          }
        }
      } catch (err) {
        setError('Network error loading settings');
      } finally {
        setLoading(false);
      }
    };

//   const updateSpectrumValue = async (newSpectrumValue: number) => {
//       try {
//         const response = await fetch('/api/user-settings', {
//           method: 'POST',
//           headers: { 'Content-Type': 'application/json' },
//           body: JSON.stringify({ coaching_style_spectrum: newSpectrumValue })
//         });
//
//         if (response.ok) {
//           setSpectrumValue(newSpectrumValue);
//
//           // Also update the equivalent coaching_tone for consistency
//           const equivalentTone = newSpectrumValue <= 25 ? 'casual' :
//                                 newSpectrumValue <= 50 ? 'supportive' :
//                                 newSpectrumValue <= 75 ? 'motivational' : 'analytical';
//
//           if (settings) {
//             handleInputChange('coaching_tone', equivalentTone);
//           }
//
//           setSuccess('Coaching style updated successfully!');
//         } else {
//           setError('Failed to update coaching style');
//         }
//       } catch (err) {
//         setError('Network error updating coaching style');
//       }
//     };

  const updateSpectrumValue = async (newSpectrumValue: number) => {
      try {
        const response = await fetch('/api/user-settings', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ coaching_style_spectrum: newSpectrumValue })
        });

        if (response.ok) {
          setSpectrumValue(newSpectrumValue);
          setSuccess('Coaching style updated successfully!');
        } else {
          setError('Failed to update coaching style');
        }
      } catch (err) {
        setError('Network error updating coaching style');
      }
    };

    // And in your spectrum component:
    <CoachingStyleSpectrum
      initialValue={spectrumValue}
      onChange={updateSpectrumValue}  // Make sure this is connected
      disabled={saving}
    />

  const loadHeartRateZones = async () => {
    try {
      const response = await fetch('/api/settings/heart-rate-zones');
      if (response.ok) {
        const data = await response.json();
        setZonesData(data);
      }
    } catch (err) {
      console.error('Error loading heart rate zones:', err);
    }
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
        await loadSettings();

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
        setSuccess(`Heart rate zones updated successfully! Updated: ${Object.keys(editingZones).join(', ')}`);
        setEditingZones({});
        await loadHeartRateZones();
      } else {
        const errorData = await response.json();
        setError(errorData.errors ? errorData.errors.join(', ') : 'Failed to save zones');
      }
    } catch (err) {
      setError('Network error saving zones');
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
      updateSettings(settings);
    }
  };

  const handleZoneEdit = (zoneKey: string, field: 'min' | 'max', value: number) => {
    setEditingZones(prev => {
      const newZones = { ...prev };

      if (!newZones[zoneKey]) {
        newZones[zoneKey] = {};
      }

      newZones[zoneKey][field] = value;

      // Synchronize adjacent zones
      if (field === 'max' && zonesData) {
        const zoneNumber = parseInt(zoneKey.replace('zone', ''));
        const nextZoneKey = `zone${zoneNumber + 1}`;

        if (zonesData.zones[nextZoneKey as keyof HeartRateZones] && zoneNumber < 5) {
          if (!newZones[nextZoneKey]) {
            newZones[nextZoneKey] = {};
          }
          newZones[nextZoneKey].min = value;
        }
      }

      if (field === 'min' && zonesData) {
        const zoneNumber = parseInt(zoneKey.replace('zone', ''));
        const prevZoneKey = `zone${zoneNumber - 1}`;

        if (zonesData.zones[prevZoneKey as keyof HeartRateZones] && zoneNumber > 1) {
          if (!newZones[prevZoneKey]) {
            newZones[prevZoneKey] = {};
          }
          newZones[prevZoneKey].max = value;
        }
      }

      return newZones;
    });
  };

  if (loading) {
    return (
      <div className={styles.container}>
        <div style={{ textAlign: 'center', padding: '2rem' }}>
          <div style={{ fontSize: '1.2rem', color: '#6b7280' }}>Loading settings...</div>
        </div>
      </div>
    );
  }

  if (!settings) {
    return (
      <div className={styles.container}>
        <div style={{ textAlign: 'center', padding: '2rem' }}>
          <div style={{ fontSize: '1.2rem', color: '#dc2626' }}>Failed to load settings</div>
        </div>
      </div>
    );
  }

  const sectionOptions = [
    { key: 'profile', label: '👤 Profile & Heart Rate', icon: '👤' },
    { key: 'training', label: '🏃 Training Goals', icon: '🏃' },
    { key: 'alerts', label: '🔔 Coaching Style', icon: '🔔' }
  ];

  return (
    <div className={styles.container}>
      {/* Compact Header */}
      <div className={styles.header}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <h1 className={styles.title}>⚙️ Settings</h1>
          {/* Settings Section Dropdown - moved next to header */}
          <select
            value={activeSection}
            onChange={(e) => setActiveSection(e.target.value)}
            style={{
              padding: '0.5rem 1rem',
              borderRadius: '0.375rem',
              border: '1px solid #d1d5db',
              backgroundColor: 'white',
              fontSize: '0.9rem',
              fontWeight: '500',
              color: '#374151',
              cursor: 'pointer',
              minWidth: '200px'
            }}
          >
            {sectionOptions.map(option => (
              <option key={option.key} value={option.key}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        {/* Save Button - Always Visible */}
        <button
          onClick={handleSave}
          disabled={saving}
          className={saving ? styles.refreshButton : styles.generateButton}
          style={{
            opacity: saving ? 0.7 : 1,
            minWidth: '120px'
          }}
        >
          {saving ? (
            <>
              <span className={styles.spinner}>⟳</span>
              Saving...
            </>
          ) : (
            <>
              💾 Save Settings
            </>
          )}
        </button>
      </div>

      {/* Alert Messages - Always visible near save button */}
      {(error || success) && (
        <div style={{ marginBottom: '1rem' }}>
          {error && (
            <div style={{
              padding: '0.75rem',
              backgroundColor: '#fef2f2',
              border: '1px solid #fecaca',
              borderRadius: '0.5rem',
              color: '#dc2626',
              fontSize: '0.9rem'
            }}>
              {error}
            </div>
          )}
          {success && (
            <div style={{
              padding: '0.75rem',
              backgroundColor: '#d1fae5',
              border: '1px solid #a7f3d0',
              borderRadius: '0.5rem',
              color: '#065f46',
              fontSize: '0.9rem'
            }}>
              {success}
            </div>
          )}
        </div>
      )}

      {/* Profile & Heart Rate Section */}
      {activeSection === 'profile' && (
        <div className={styles.chartContainer}>
          <h2 className={styles.chartTitle}>Profile & Heart Rate Configuration</h2>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
            gap: '1.5rem',
            justifyItems: 'center'
          }}>
            {/* Basic Profile */}
            <div style={{
              backgroundColor: '#f8fafc',
              padding: '1.25rem',
              borderRadius: '0.5rem',
              border: '1px solid #e2e8f0',
              maxWidth: '350px',
              width: '100%'
            }}>
              <h3 style={{
                fontSize: '1rem',
                fontWeight: '600',
                color: '#374151',
                marginBottom: '1rem',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem'
              }}>
                👤 Basic Profile
              </h3>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <div>
                  <label style={{
                    display: 'block',
                    fontSize: '0.875rem',
                    fontWeight: '500',
                    color: '#374151',
                    marginBottom: '0.25rem'
                  }}>
                    Email
                  </label>
                  <input
                    type="email"
                    value={settings.email}
                    onChange={(e) => handleInputChange('email', e.target.value)}
                    style={{
                      width: '100%',
                      padding: '0.5rem',
                      border: '1px solid #d1d5db',
                      borderRadius: '0.375rem',
                      fontSize: '0.875rem'
                    }}
                  />
                </div>

                <div>
                  <label style={{
                    display: 'block',
                    fontSize: '0.875rem',
                    fontWeight: '500',
                    color: '#374151',
                    marginBottom: '0.25rem'
                  }}>
                    Gender
                  </label>
                  <select
                    value={settings.gender || 'M'}
                    onChange={(e) => handleInputChange('gender', e.target.value)}
                    style={{
                      width: '100%',
                      padding: '0.5rem',
                      border: '1px solid #d1d5db',
                      borderRadius: '0.375rem',
                      fontSize: '0.875rem',
                      backgroundColor: 'white'
                    }}
                  >
                    <option value="M">Male</option>
                    <option value="F">Female</option>
                    <option value="O">Other</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Heart Rate Zone Configuration */}
            <div style={{
              backgroundColor: '#f8fafc',
              padding: '1.25rem',
              borderRadius: '0.5rem',
              border: '1px solid #e2e8f0',
              maxWidth: '350px',
              width: '100%'
            }}>
              <h3 style={{
                fontSize: '1rem',
                fontWeight: '600',
                color: '#374151',
                marginBottom: '1rem',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem'
              }}>
                ❤️ Heart Rate Zone Configuration
              </h3>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                  <div>
                    <label style={{
                      display: 'block',
                      fontSize: '0.875rem',
                      fontWeight: '500',
                      color: '#374151',
                      marginBottom: '0.25rem'
                    }}>
                      Resting HR (bpm)
                    </label>
                    <input
                      type="number"
                      min="30"
                      max="100"
                      value={settings.resting_hr}
                      onChange={(e) => handleInputChange('resting_hr', parseInt(e.target.value))}
                      style={{
                        width: '100%',
                        padding: '0.5rem',
                        border: '1px solid #d1d5db',
                        borderRadius: '0.375rem',
                        fontSize: '0.875rem'
                      }}
                    />
                  </div>

                  <div>
                    <label style={{
                      display: 'block',
                      fontSize: '0.875rem',
                      fontWeight: '500',
                      color: '#374151',
                      marginBottom: '0.25rem'
                    }}>
                      Max HR (bpm)
                    </label>
                    <input
                      type="number"
                      min="120"
                      max="220"
                      value={settings.max_hr}
                      onChange={(e) => handleInputChange('max_hr', parseInt(e.target.value))}
                      style={{
                        width: '100%',
                        padding: '0.5rem',
                        border: '1px solid #d1d5db',
                        borderRadius: '0.375rem',
                        fontSize: '0.875rem'
                      }}
                    />
                  </div>
                </div>

                <div>
                  <label style={{
                    display: 'block',
                    fontSize: '0.875rem',
                    fontWeight: '500',
                    color: '#374151',
                    marginBottom: '0.25rem'
                  }}>
                    HR Zone Calculation Method
                  </label>
                  <select
                    value={settings.hr_zones_method || 'percentage'}
                    onChange={(e) => handleInputChange('hr_zones_method', e.target.value)}
                    style={{
                      width: '100%',
                      padding: '0.5rem',
                      border: '1px solid #d1d5db',
                      borderRadius: '0.375rem',
                      fontSize: '0.875rem',
                      backgroundColor: 'white'
                    }}
                  >
                    <option value="percentage">Percentage of Max HR</option>
                    <option value="karvonen">Karvonen (Heart Rate Reserve)</option>
                  </select>
                  <small style={{ color: '#6b7280', fontSize: '0.75rem', marginTop: '0.25rem', display: 'block' }}>
                    Changes will recalculate ALL your past training data.
                  </small>
                </div>
              </div>
            </div>

            {/* Why Heart Rate Zones Matter */}
            <div style={{
              backgroundColor: '#eff6ff',
              padding: '1.25rem',
              borderRadius: '0.5rem',
              border: '1px solid #bfdbfe',
              maxWidth: '450px',
              width: '100%'
            }}>
              <h3 style={{
                fontSize: '1rem',
                fontWeight: '600',
                color: '#1e40af',
                marginBottom: '1rem',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem'
              }}>
                🎯 Why Heart Rate Zones Matter
              </h3>

              <div style={{ fontSize: '0.875rem', lineHeight: '1.5', color: '#1e40af' }}>
                <p style={{ margin: '0 0 0.75rem 0', textAlign: 'left' }}>
                  Your heart rate zones form the foundation of all training calculations in Your Training Monkey. These zones determine how your Training Impulse (TRIMP) is calculated, which directly impacts your internal Acute:Chronic Workload Ratio (ACWR), injury risk assessments, and AI recommendations.
                </p>

                <div style={{ marginBottom: '0.75rem' }}>
                  <strong style={{ fontSize: '0.85rem', textAlign: 'left', display: 'block', marginBottom: '0.5rem' }}>Impact on Your Training Analysis:</strong>
                  <ul style={{ margin: '0.25rem 0 0 1rem', paddingLeft: '0', textAlign: 'left' }}>
                    <li style={{ fontSize: '0.8rem', marginBottom: '0.25rem', textAlign: 'left' }}>
                      <strong>TRIMP Calculations:</strong> Higher intensity zones receive exponentially more weight in training load calculations. TRIMP (Training Impulse) combines workout duration with heart rate intensity to create a single training stress score.
                    </li>
                    <li style={{ fontSize: '0.8rem', marginBottom: '0.25rem', textAlign: 'left' }}>
                      <strong>Historical Data:</strong> Changing these settings recalculates ALL your past training data
                    </li>
                    <li style={{ fontSize: '0.8rem', marginBottom: '0.25rem', textAlign: 'left' }}>
                      <strong>AI Recommendations:</strong> Your zones influence how the AI interprets workout intensity and prescribes future training
                    </li>
                    <li style={{ fontSize: '0.8rem', textAlign: 'left' }}>
                      <strong>Injury Prevention:</strong> Accurate zones are critical for proper ACWR calculations and overtraining detection
                    </li>
                  </ul>
                </div>
              </div>
            </div>

            {/* Choosing the Right Method */}
            <div style={{
              backgroundColor: '#f0fdf4',
              padding: '1.25rem',
              borderRadius: '0.5rem',
              border: '1px solid #bbf7d0',
              maxWidth: '350px',
              width: '100%'
            }}>
              <h3 style={{
                fontSize: '1rem',
                fontWeight: '600',
                color: '#059669',
                marginBottom: '1rem',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem'
              }}>
                💡 Choosing the Right Method
              </h3>

              <div style={{ fontSize: '0.875rem', lineHeight: '1.4', color: '#374151' }}>
                <div style={{ marginBottom: '0.75rem' }}>
                  <strong style={{ fontSize: '0.85rem', color: '#374151' }}>Use Karvonen Method if:</strong>
                  <ul style={{ margin: '0.25rem 0 0 1rem', paddingLeft: '0', textAlign: 'left' }}>
                    <li style={{ fontSize: '0.8rem', marginBottom: '0.2rem', textAlign: 'left' }}>You know your true resting HR</li>
                    <li style={{ fontSize: '0.8rem', marginBottom: '0.2rem', textAlign: 'left' }}>You want physiologically accurate zones</li>
                    <li style={{ fontSize: '0.8rem', textAlign: 'left' }}>Large difference between resting/max HR</li>
                  </ul>
                </div>

                <div style={{ marginBottom: '0.75rem' }}>
                  <strong style={{ fontSize: '0.85rem', color: '#374151' }}>Use Percentage Method if:</strong>
                  <ul style={{ margin: '0.25rem 0 0 1rem', paddingLeft: '0', textAlign: 'left' }}>
                    <li style={{ fontSize: '0.8rem', marginBottom: '0.2rem', textAlign: 'left' }}>Unsure about resting HR</li>
                    <li style={{ fontSize: '0.8rem', marginBottom: '0.2rem', textAlign: 'left' }}>You prefer simplicity</li>
                    <li style={{ fontSize: '0.8rem', textAlign: 'left' }}>New to heart rate training</li>
                  </ul>
                </div>

                <div>
                  <strong style={{ fontSize: '0.85rem', color: '#374151' }}>Use Custom Zones if:</strong>
                  <ul style={{ margin: '0.25rem 0 0 1rem', paddingLeft: '0', textAlign: 'left' }}>
                    <li style={{ fontSize: '0.8rem', marginBottom: '0.2rem', textAlign: 'left' }}>You've done lab testing</li>
                    <li style={{ fontSize: '0.8rem', textAlign: 'left' }}>Want to fine-tune zones</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>

          {/* Heart Rate Zones Comparison Table */}
          {zonesData && (
            <div className={styles.chartContainer} style={{ marginTop: '1.5rem' }}>
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '1rem'
              }}>
                <h3 style={{
                  fontSize: '1rem',
                  fontWeight: '600',
                  color: '#374151',
                  margin: 0,
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem'
                }}>
                  🎯 Your Heart Rate Zones Comparison
                </h3>
                <div style={{
                  display: 'flex',
                  gap: '0.75rem',
                  alignItems: 'center',
                  height: '40px'
                }}>
                  <button
                    onClick={() => setShowCalculations(!showCalculations)}
                    style={{
                      padding: '0.5rem 1rem',
                      backgroundColor: '#f3f4f6',
                      border: '1px solid #d1d5db',
                      borderRadius: '0.375rem',
                      fontSize: '0.8rem',
                      cursor: 'pointer',
                      color: '#374151',
                      height: '36px'
                    }}
                  >
                    {showCalculations ? 'Hide' : 'Show'} Formulas
                  </button>
                  <button
                    onClick={() => {
                      setEditingZones({});
                      loadHeartRateZones();
                    }}
                    style={{
                      padding: '0.5rem 1rem',
                      backgroundColor: '#f3f4f6',
                      border: '1px solid #d1d5db',
                      borderRadius: '0.375rem',
                      fontSize: '0.8rem',
                      cursor: 'pointer',
                      color: '#374151',
                      height: '36px'
                    }}
                  >
                    Reset Zones
                  </button>
                  {Object.keys(editingZones).length > 0 && (
                    <button
                      onClick={saveCustomZones}
                      disabled={saving}
                      className={styles.generateButton}
                      style={{
                        fontSize: '0.8rem',
                        padding: '0.5rem 1rem',
                        height: '36px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.5rem'
                      }}
                    >
                      {saving ? 'Saving...' : 'Save Zone Changes'}
                    </button>
                  )}
                </div>
              </div>

              {/* Zone Comparison Table */}
              <div style={{
                backgroundColor: 'white',
                borderRadius: '0.5rem',
                border: '1px solid #e5e7eb',
                overflow: 'hidden'
              }}>
                <table style={{
                  width: '100%',
                  borderCollapse: 'collapse',
                  fontSize: '0.875rem'
                }}>
                  <thead>
                    <tr style={{ backgroundColor: '#f8fafc' }}>
                      <th style={{
                        padding: '0.75rem',
                        textAlign: 'left',
                        fontWeight: '600',
                        color: '#374151',
                        borderBottom: '1px solid #e5e7eb',
                        width: '15%'
                      }}>
                        Zone
                      </th>
                      <th style={{
                        padding: '0.75rem',
                        textAlign: 'left',
                        fontWeight: '600',
                        color: '#374151',
                        borderBottom: '1px solid #e5e7eb',
                        width: '15%'
                      }}>
                        Purpose
                      </th>
                      <th style={{
                        padding: '0.75rem',
                        textAlign: 'center',
                        fontWeight: '600',
                        color: '#374151',
                        borderBottom: '1px solid #e5e7eb',
                        width: '20%'
                      }}>
                        Percentage Method
                        <div style={{ fontSize: '0.75rem', fontWeight: '400', color: '#6b7280' }}>
                          (% of Max HR)
                        </div>
                      </th>
                      <th style={{
                        padding: '0.75rem',
                        textAlign: 'center',
                        fontWeight: '600',
                        color: '#374151',
                        borderBottom: '1px solid #e5e7eb',
                        width: '20%'
                      }}>
                        Karvonen Method
                        <div style={{ fontSize: '0.75rem', fontWeight: '400', color: '#6b7280' }}>
                          (HR Reserve)
                        </div>
                      </th>
                      <th style={{
                        padding: '0.75rem',
                        textAlign: 'center',
                        fontWeight: '600',
                        color: '#374151',
                        borderBottom: '1px solid #e5e7eb',
                        backgroundColor: '#fef3c7', // Always yellow for now to test
                        width: '15%',
                        border: '2px solid #dc2626'
                      }}>
                        Your Active Zones
                        <div style={{ fontSize: '0.75rem', fontWeight: '400' }}>
                          Custom
                        </div>
                      </th>
                      <th style={{
                        padding: '0.75rem',
                        textAlign: 'center',
                        fontWeight: '600',
                        color: '#374151',
                        borderBottom: '1px solid #e5e7eb',
                        width: '15%'
                      }}>
                        Custom
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(zonesData.zones).map(([zoneKey, zone], index) => {
                      const zoneNumber = parseInt(zoneKey.replace('zone', ''));
                      const zoneColors = ['#22c55e', '#84cc16', '#eab308', '#f97316', '#ef4444'];
                      const zoneColor = zoneColors[index];

                      // Calculate percentage method zones for comparison
                      const maxHR = settings.max_hr;
                      const percentageZones = {
                        1: { min: Math.round(maxHR * 0.50), max: Math.round(maxHR * 0.60) },
                        2: { min: Math.round(maxHR * 0.60), max: Math.round(maxHR * 0.70) },
                        3: { min: Math.round(maxHR * 0.70), max: Math.round(maxHR * 0.80) },
                        4: { min: Math.round(maxHR * 0.80), max: Math.round(maxHR * 0.90) },
                        5: { min: Math.round(maxHR * 0.90), max: maxHR }
                      };

                      // Calculate Karvonen method zones for comparison
                      const restingHR = settings.resting_hr;
                      const hrReserve = maxHR - restingHR;
                      const karvonenZones = {
                        1: { min: Math.round(restingHR + hrReserve * 0.50), max: Math.round(restingHR + hrReserve * 0.60) },
                        2: { min: Math.round(restingHR + hrReserve * 0.60), max: Math.round(restingHR + hrReserve * 0.70) },
                        3: { min: Math.round(restingHR + hrReserve * 0.70), max: Math.round(restingHR + hrReserve * 0.80) },
                        4: { min: Math.round(restingHR + hrReserve * 0.80), max: Math.round(restingHR + hrReserve * 0.90) },
                        5: { min: Math.round(restingHR + hrReserve * 0.90), max: maxHR }
                      };

                      const isEditing = editingZones[zoneKey];
                      const displayMin = isEditing?.min ?? zone.min;
                      const displayMax = isEditing?.max ?? zone.max;

                      // Check if this zone has custom values (different from calculated)
                      const hasCustomValues = (displayMin !== zone.min) || (displayMax !== zone.max);

                      return (
                        <tr key={zoneKey} style={{
                          borderBottom: index < 4 ? '1px solid #f3f4f6' : 'none',
                          backgroundColor: index % 2 === 0 ? '#fafafa' : 'white'
                        }}>
                          {/* Zone */}
                          <td style={{
                            padding: '0.75rem',
                            fontWeight: '600',
                            color: zoneColor
                          }}>
                            Zone {zoneNumber}
                          </td>

                          {/* Purpose */}
                          <td style={{
                            padding: '0.75rem',
                            color: '#374151'
                          }}>
                            {zone.name}
                          </td>

                          {/* Percentage Method */}
                          <td style={{
                            padding: '0.75rem',
                            textAlign: 'center',
                            color: '#374151'
                          }}>
                            <div style={{ fontWeight: '600' }}>
                              {percentageZones[zoneNumber as keyof typeof percentageZones].min} - {percentageZones[zoneNumber as keyof typeof percentageZones].max}
                            </div>
                            {showCalculations && (
                              <div style={{ fontSize: '0.75rem', color: '#6b7280', marginTop: '0.25rem' }}>
                                {zoneNumber === 1 && '50-60%'}
                                {zoneNumber === 2 && '60-70%'}
                                {zoneNumber === 3 && '70-80%'}
                                {zoneNumber === 4 && '80-90%'}
                                {zoneNumber === 5 && '90-100%'}
                              </div>
                            )}
                          </td>

                          {/* Karvonen Method */}
                          <td style={{
                            padding: '0.75rem',
                            textAlign: 'center',
                            color: '#374151'
                          }}>
                            <div style={{ fontWeight: '600' }}>
                              {karvonenZones[zoneNumber as keyof typeof karvonenZones].min} - {karvonenZones[zoneNumber as keyof typeof karvonenZones].max}
                            </div>
                            {showCalculations && (
                              <div style={{ fontSize: '0.75rem', color: '#6b7280', marginTop: '0.25rem' }}>
                                {restingHR} + {zoneNumber === 1 && '50-60%'}
                                {zoneNumber === 2 && '60-70%'}
                                {zoneNumber === 3 && '70-80%'}
                                {zoneNumber === 4 && '80-90%'}
                                {zoneNumber === 5 && '90-100%'} × {hrReserve}
                              </div>
                            )}
                          </td>

                          {/* Your Active Zones (Current Method or Custom) */}
                          <td style={{
                            padding: '0.75rem',
                            textAlign: 'center',
                            backgroundColor: '#fef3c7', // Always yellow for now to test
                            color: '#374151',
                            fontWeight: '600',
                            border: '2px solid #dc2626',
                            borderTop: 'none'
                          }}>
                            {displayMin} - {displayMax}
                          </td>

                          {/* Custom Zones */}
                          <td style={{
                            padding: '0.5rem',
                            textAlign: 'center'
                          }}>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                              <input
                                type="number"
                                value={displayMin}
                                onChange={(e) => handleZoneEdit(zoneKey, 'min', parseInt(e.target.value))}
                                style={{
                                  width: '60px',
                                  padding: '0.25rem',
                                  border: '1px solid #d1d5db',
                                  borderRadius: '0.25rem',
                                  fontSize: '0.75rem',
                                  textAlign: 'center'
                                }}
                                placeholder="Min"
                              />
                              <input
                                type="number"
                                value={displayMax}
                                onChange={(e) => handleZoneEdit(zoneKey, 'max', parseInt(e.target.value))}
                                style={{
                                  width: '60px',
                                  padding: '0.25rem',
                                  border: '1px solid #d1d5db',
                                  borderRadius: '0.25rem',
                                  fontSize: '0.75rem',
                                  textAlign: 'center'
                                }}
                                placeholder="Max"
                              />
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              {/* Removed duplicate content - guidance now in 4-card layout above */}
            </div>
          )}
        </div>
      )}

      {/* Training Goals Section */}
      {activeSection === 'training' && (
        <div className={styles.chartContainer}>
          <h2 className={styles.chartTitle}>Training Goals & Experience</h2>

          <div style={{
            display: 'flex',
            justifyContent: 'center',
            gap: '1.5rem',
            flexWrap: 'wrap'
          }}>
            {/* Sports & Experience */}
            <div style={{
              backgroundColor: '#f8fafc',
              padding: '1.25rem',
              borderRadius: '0.5rem',
              border: '1px solid #e2e8f0',
              maxWidth: '350px',
              width: '100%'
            }}>
              <h3 style={{
                fontSize: '1rem',
                fontWeight: '600',
                color: '#374151',
                marginBottom: '1rem',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem'
              }}>
                🏃 Sports & Experience
              </h3>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <div>
                  <label style={{
                    display: 'block',
                    fontSize: '0.875rem',
                    fontWeight: '500',
                    color: '#374151',
                    marginBottom: '0.25rem'
                  }}>
                    Primary Sport
                  </label>
                  <select
                    value={settings.primary_sport || 'running'}
                    onChange={(e) => handleInputChange('primary_sport', e.target.value)}
                    style={{
                      width: '100%',
                      padding: '0.5rem',
                      border: '1px solid #d1d5db',
                      borderRadius: '0.375rem',
                      fontSize: '0.875rem',
                      backgroundColor: 'white'
                    }}
                  >
                    <option value="running">Running</option>
                    <option value="cycling">Cycling</option>
                    <option value="triathlon">Triathlon</option>
                    <option value="hiking">Hiking</option>
                    <option value="other">Other</option>
                  </select>
                </div>

                <div>
                  <label style={{
                    display: 'block',
                    fontSize: '0.875rem',
                    fontWeight: '500',
                    color: '#374151',
                    marginBottom: '0.25rem'
                  }}>
                    Secondary Sport (Optional)
                  </label>
                  <select
                    value={settings.secondary_sport || ''}
                    onChange={(e) => handleInputChange('secondary_sport', e.target.value || null)}
                    style={{
                      width: '100%',
                      padding: '0.5rem',
                      border: '1px solid #d1d5db',
                      borderRadius: '0.375rem',
                      fontSize: '0.875rem',
                      backgroundColor: 'white'
                    }}
                  >
                    <option value="">None</option>
                    <option value="running">Running</option>
                    <option value="cycling">Cycling</option>
                    <option value="swimming">Swimming</option>
                    <option value="hiking">Hiking</option>
                    <option value="strength">Strength Training</option>
                  </select>
                </div>

                <div>
                  <label style={{
                    display: 'block',
                    fontSize: '0.875rem',
                    fontWeight: '500',
                    color: '#374151',
                    marginBottom: '0.25rem'
                  }}>
                    Training Experience
                  </label>
                  <select
                    value={settings.training_experience || 'intermediate'}
                    onChange={(e) => handleInputChange('training_experience', e.target.value)}
                    style={{
                      width: '100%',
                      padding: '0.5rem',
                      border: '1px solid #d1d5db',
                      borderRadius: '0.375rem',
                      fontSize: '0.875rem',
                      backgroundColor: 'white'
                    }}
                  >
                    <option value="beginner">Beginner (less than 1 year)</option>
                    <option value="intermediate">Intermediate (1-3 years)</option>
                    <option value="advanced">Advanced (3-5 years)</option>
                    <option value="expert">Expert (more than 5 years)</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Training Phase & Goals */}
            <div style={{
              backgroundColor: '#f8fafc',
              padding: '1.25rem',
              borderRadius: '0.5rem',
              border: '1px solid #e2e8f0',
              maxWidth: '350px',
              width: '100%'
            }}>
              <h3 style={{
                fontSize: '1rem',
                fontWeight: '600',
                color: '#374151',
                marginBottom: '1rem',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem'
              }}>
                🎯 Current Training Phase
              </h3>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <div>
                  <label style={{
                    display: 'block',
                    fontSize: '0.875rem',
                    fontWeight: '500',
                    color: '#374151',
                    marginBottom: '0.25rem'
                  }}>
                    Current Phase
                  </label>
                  <select
                    value={settings.current_phase || 'base'}
                    onChange={(e) => handleInputChange('current_phase', e.target.value)}
                    style={{
                      width: '100%',
                      padding: '0.5rem',
                      border: '1px solid #d1d5db',
                      borderRadius: '0.375rem',
                      fontSize: '0.875rem',
                      backgroundColor: 'white'
                    }}
                  >
                    <option value="base">Base Building</option>
                    <option value="build">Build Phase</option>
                    <option value="peak">Peak Training</option>
                    <option value="taper">Taper</option>
                    <option value="recovery">Recovery</option>
                    <option value="off_season">Off Season</option>
                  </select>
                </div>

                <div>
                  <label style={{
                    display: 'block',
                    fontSize: '0.875rem',
                    fontWeight: '500',
                    color: '#374151',
                    marginBottom: '0.25rem'
                  }}>
                    Race Goal Date (Optional)
                  </label>
                  <input
                    type="date"
                    value={settings.race_goal_date || ''}
                    onChange={(e) => handleInputChange('race_goal_date', e.target.value || null)}
                    style={{
                      width: '100%',
                      padding: '0.5rem',
                      border: '1px solid #d1d5db',
                      borderRadius: '0.375rem',
                      fontSize: '0.875rem'
                    }}
                  />
                </div>

                <div>
                  <label style={{
                    display: 'block',
                    fontSize: '0.875rem',
                    fontWeight: '500',
                    color: '#374151',
                    marginBottom: '0.25rem'
                  }}>
                    Weekly Training Hours
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="40"
                    value={settings.weekly_training_hours}
                    onChange={(e) => handleInputChange('weekly_training_hours', parseInt(e.target.value))}
                    style={{
                      width: '100%',
                      padding: '0.5rem',
                      border: '1px solid #d1d5db',
                      borderRadius: '0.375rem',
                      fontSize: '0.875rem'
                    }}
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Alerts & AI Style Section */}
      {activeSection === 'alerts' && (
        <div className={styles.chartContainer}>
          <h2 className={styles.chartTitle}>Coaching Style</h2>

          <div style={{
            display: 'flex',
            justifyContent: 'center',
            gap: '1.5rem',
            flexWrap: 'wrap'
          }}>
            {/* Training Alerts */}
            <div style={{
              backgroundColor: '#f8fafc',
              padding: '1.25rem',
              borderRadius: '0.5rem',
              border: '1px solid #e2e8f0',
              maxWidth: '350px',
              width: '100%'
            }}>
              <h3 style={{
                fontSize: '1rem',
                fontWeight: '600',
                color: '#374151',
                marginBottom: '1rem',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem'
              }}>
                🔔 Training Alerts
              </h3>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <div>
                  <label style={{
                    display: 'block',
                    fontSize: '0.875rem',
                    fontWeight: '500',
                    color: '#374151',
                    marginBottom: '0.25rem'
                  }}>
                    ACWR Alert Threshold
                  </label>
                  <input
                    type="number"
                    min="1.0"
                    max="2.0"
                    step="0.1"
                    value={settings.acwr_alert_threshold}
                    onChange={(e) => handleInputChange('acwr_alert_threshold', parseFloat(e.target.value))}
                    style={{
                      width: '100%',
                      padding: '0.5rem',
                      border: '1px solid #d1d5db',
                      borderRadius: '0.375rem',
                      fontSize: '0.875rem'
                    }}
                  />
                  <small style={{ color: '#6b7280', fontSize: '0.75rem', marginTop: '0.25rem', display: 'block' }}>
                    Alert when ACWR exceeds this value (recommended: 1.3)
                  </small>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <input
                    type="checkbox"
                    id="injury_risk_alerts"
                    checked={settings.injury_risk_alerts}
                    onChange={(e) => handleInputChange('injury_risk_alerts', e.target.checked)}
                    style={{
                      width: '1rem',
                      height: '1rem'
                    }}
                  />
                  <label
                    htmlFor="injury_risk_alerts"
                    style={{
                      fontSize: '0.875rem',
                      fontWeight: '500',
                      color: '#374151',
                      cursor: 'pointer'
                    }}
                  >
                    Enable injury risk alerts
                  </label>
                </div>
              </div>
            </div>

            {/* AI Coaching Style */}
            <div style={{
              backgroundColor: '#f8fafc',
              padding: '1.25rem',
              borderRadius: '0.5rem',
              border: '1px solid #e2e8f0',
              maxWidth: '350px',
              width: '100%'
            }}>
              <h3 style={{
                fontSize: '1rem',
                fontWeight: '600',
                color: '#374151',
                marginBottom: '1rem',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem'
              }}>
                🤖 AI Coaching Style
              </h3>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <div>
                  <label style={{
                    display: 'block',
                    fontSize: '0.875rem',
                    fontWeight: '500',
                    color: '#374151',
                    marginBottom: '0.25rem'
                  }}>
                    Recommendation Style
                  </label>
                  <select
                    value={settings.recommendation_style || 'balanced'}
                    onChange={(e) => handleInputChange('recommendation_style', e.target.value)}
                    style={{
                      width: '100%',
                      padding: '0.5rem',
                      border: '1px solid #d1d5db',
                      borderRadius: '0.375rem',
                      fontSize: '0.875rem',
                      backgroundColor: 'white'
                    }}
                  >
                    <option value="conservative">Conservative - Play it safe</option>
                    <option value="balanced">Balanced - Moderate push</option>
                    <option value="aggressive">Aggressive - Push limits</option>
                  </select>
                </div>

                <div>
                  <label style={{
                    display: 'block',
                    fontSize: '0.875rem',
                    fontWeight: '500',
                    color: '#374151',
                    marginBottom: '0.75rem'
                  }}>
                    Coaching Tone
                  </label>
                  <CoachingStyleSpectrum
                    initialValue={spectrumValue}
                    onChange={updateSpectrumValue}
                    disabled={saving}
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SettingsPage;