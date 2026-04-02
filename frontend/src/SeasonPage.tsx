import React, { useState, useEffect, useRef } from 'react';
import { RaceReadinessCard, AthleteModelPanel, RaceReadiness, AthleteModel } from './CoachPage';
import CoachingStyleSpectrum from './CoachingStyleSpectrum';
import RiskToleranceSelector from './RiskToleranceSelector';

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

interface GoalFormData {
  race_name: string;
  race_date: string;
  race_type: string;
  priority: 'A' | 'B' | 'C';
  target_time_h: string;
  target_time_m: string;
  target_time_s: string;
  notes: string;
  elevation_gain_feet: string;
  distance_miles: string;
}

const EMPTY_FORM: GoalFormData = {
  race_name: '',
  race_date: '',
  race_type: 'Trail',
  priority: 'A',
  target_time_h: '',
  target_time_m: '',
  target_time_s: '',
  notes: '',
  elevation_gain_feet: '',
  distance_miles: '',
};

// ============================================================================
// HELPERS
// ============================================================================

const minutesToHMS = (totalMinutes: number | null) => {
  if (!totalMinutes) return { h: '', m: '', s: '' };
  const h = Math.floor(totalMinutes / 60);
  const m = Math.floor(totalMinutes % 60);
  const s = Math.round((totalMinutes % 1) * 60);
  return { h: h.toString(), m: m.toString().padStart(2, '0'), s: s.toString().padStart(2, '0') };
};

const hmsToMinutes = (h: string, m: string, s: string): number | null => {
  if (!h && !m && !s) return null;
  return (parseInt(h || '0', 10) * 60) + parseInt(m || '0', 10) + (parseInt(s || '0', 10) / 60);
};

const formatDate = (iso: string) => {
  const d = new Date(iso + 'T12:00:00');
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
};


// ============================================================================
// TACTICAL FORM STYLES
// ============================================================================

const CARBON = {
  backgroundColor: '#1B2E4B',
  backgroundImage: [
    'linear-gradient(135deg, rgba(255,255,255,0.04) 25%, transparent 25%)',
    'linear-gradient(225deg, rgba(255,255,255,0.04) 25%, transparent 25%)',
    'linear-gradient(315deg, rgba(255,255,255,0.04) 25%, transparent 25%)',
    'linear-gradient(45deg,  rgba(255,255,255,0.04) 25%, transparent 25%)',
  ].join(', '),
  backgroundSize: '4px 4px',
};

const tacticalLabel: React.CSSProperties = {
  display: 'block',
  marginBottom: '6px',
  fontSize: '0.72rem',
  fontWeight: 700,
  color: '#7D9CB8',
  textTransform: 'uppercase',
  letterSpacing: '0.08em',
};

const tacticalInput: React.CSSProperties = {
  padding: '7px 10px',
  backgroundColor: '#162440',
  border: '1px solid #7D9CB8',
  borderRadius: '4px',
  color: '#E6F0FF',
  fontSize: '0.875rem',
  width: '100%',
  boxSizing: 'border-box',
  WebkitAppearance: 'none',
  MozAppearance: 'textfield',
} as React.CSSProperties;

// ============================================================================
// RACE GOAL MODAL
// ============================================================================

interface GoalModalProps {
  mode: 'add' | 'edit';
  initialData?: RaceGoal;
  onSave: () => void;
  onClose: () => void;
}

const GoalModal: React.FC<GoalModalProps> = ({ mode, initialData, onSave, onClose }) => {
  const [form, setForm] = useState<GoalFormData>(() => {
    if (mode === 'edit' && initialData) {
      const hms = minutesToHMS(initialData.target_time ? parseFloat(initialData.target_time) : null);
      return {
        race_name: initialData.race_name,
        race_date: initialData.race_date,
        race_type: initialData.race_type || 'Trail',
        priority: initialData.priority,
        target_time_h: hms.h,
        target_time_m: hms.m,
        target_time_s: hms.s,
        notes: initialData.notes || '',
        elevation_gain_feet: initialData.elevation_gain_feet != null ? String(initialData.elevation_gain_feet) : '',
        distance_miles: initialData.distance_miles != null ? String(initialData.distance_miles) : '',
      };
    }
    return EMPTY_FORM;
  });

  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const timeMRef = useRef<HTMLInputElement>(null);
  const timeSRef = useRef<HTMLInputElement>(null);

  const set = (field: keyof GoalFormData, value: string) =>
    setForm(f => ({ ...f, [field]: value }));

  const handleSubmit = async () => {
    if (!form.race_name.trim()) { setError('Race name is required'); return; }
    if (!form.race_date) { setError('Race date is required'); return; }

    setIsSaving(true);
    setError(null);

    const payload = {
      race_name: form.race_name.trim(),
      race_date: form.race_date,
      race_type: form.race_type || null,
      priority: form.priority,
      target_time: hmsToMinutes(form.target_time_h, form.target_time_m, form.target_time_s),
      notes: form.notes.trim() || null,
      elevation_gain_feet: form.elevation_gain_feet ? parseFloat(form.elevation_gain_feet) : null,
      distance_miles: form.distance_miles ? parseFloat(form.distance_miles) : null,
    };

    try {
      const url = mode === 'edit' ? `/api/coach/race-goals/${initialData!.id}` : '/api/coach/race-goals';
      const method = mode === 'edit' ? 'PUT' : 'POST';
      const res = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const d = await res.json();
        throw new Error(d.error || 'Failed to save');
      }
      onSave();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save race goal');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div
      style={{
        position: 'fixed', inset: 0, zIndex: 1000,
        backgroundColor: 'rgba(0,0,0,0.65)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        padding: '20px',
      }}
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div style={{
        ...CARBON,
        border: '1px solid rgba(255,87,34,0.7)',
        borderRadius: '8px',
        overflow: 'hidden',
        width: '100%',
        maxWidth: '560px',
        maxHeight: '90vh',
        overflowY: 'auto',
      }}>
        {/* Header */}
        <div style={{
          background: 'linear-gradient(90deg, #E6F0FF 0%, #7D9CB8 50%, #1B2E4B 100%)',
          padding: '12px 24px',
        }}>
          <span style={{ fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.12em', color: '#1B2E4B', textTransform: 'uppercase' }}>
            {mode === 'add' ? 'Add Race Goal' : 'Modify Goal'}
          </span>
        </div>

        <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '18px' }}>

          {error && (
            <div style={{ padding: '10px 14px', backgroundColor: 'rgba(220,38,38,0.08)', borderLeft: '3px solid #dc2626', borderRadius: '4px', fontSize: '0.8rem', color: '#dc2626' }}>
              {error}
            </div>
          )}

          {/* Race Name */}
          <div>
            <label style={tacticalLabel}>Race Name <span style={{ color: 'rgba(255,87,34,0.8)' }}>*</span></label>
            <input
              type="text"
              value={form.race_name}
              onChange={e => set('race_name', e.target.value)}
              style={tacticalInput}
              placeholder="Western States 100"
            />
          </div>

          {/* Date + Priority */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
            <div>
              <label style={tacticalLabel}>Race Date <span style={{ color: 'rgba(255,87,34,0.8)' }}>*</span></label>
              <input type="date" value={form.race_date} onChange={e => set('race_date', e.target.value)} style={tacticalInput} />
            </div>
            <div>
              <label style={tacticalLabel}>Priority</label>
              <select
                value={form.priority}
                onChange={e => set('priority', e.target.value as 'A' | 'B' | 'C')}
                style={{
                  ...tacticalInput,
                  appearance: 'none',
                  backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='6'%3E%3Cpath d='M0 0l5 6 5-6z' fill='%237D9CB8'/%3E%3C/svg%3E")`,
                  backgroundRepeat: 'no-repeat',
                  backgroundPosition: 'right 10px center',
                  paddingRight: '28px',
                } as React.CSSProperties}
              >
                <option value="A">"A" Race — Primary goal</option>
                <option value="B">B Race — Secondary</option>
                <option value="C">C Race — Training/tune-up</option>
              </select>
            </div>
          </div>

          {/* Type + Distance */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
            <div>
              <label style={tacticalLabel}>Race Type</label>
              <select
                value={form.race_type}
                onChange={e => set('race_type', e.target.value)}
                style={{
                  ...tacticalInput,
                  appearance: 'none',
                  backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='6'%3E%3Cpath d='M0 0l5 6 5-6z' fill='%237D9CB8'/%3E%3C/svg%3E")`,
                  backgroundRepeat: 'no-repeat',
                  backgroundPosition: 'right 10px center',
                  paddingRight: '28px',
                } as React.CSSProperties}
              >
                <option value="Trail">Trail</option>
                <option value="Road">Road</option>
                <option value="Other">Other</option>
              </select>
            </div>
            <div>
              <label style={tacticalLabel}>Distance (miles)</label>
              <input
                type="number"
                min="0"
                step="0.1"
                value={form.distance_miles}
                onChange={e => set('distance_miles', e.target.value)}
                style={tacticalInput}
                placeholder="100"
              />
            </div>
          </div>

          {/* Target Time */}
          <div>
            <label style={tacticalLabel}>Target Time</label>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              {[
                { field: 'target_time_h' as const, placeholder: 'H', max: 2, ref: undefined, nextRef: timeMRef },
                { field: 'target_time_m' as const, placeholder: 'MM', max: 2, ref: timeMRef, nextRef: timeSRef },
                { field: 'target_time_s' as const, placeholder: 'SS', max: 2, ref: timeSRef, nextRef: undefined },
              ].map((cfg, i) => (
                <React.Fragment key={cfg.field}>
                  <input
                    ref={cfg.ref}
                    type="number"
                    min="0"
                    max={i === 0 ? 99 : 59}
                    value={form[cfg.field]}
                    onChange={e => {
                      set(cfg.field, e.target.value);
                      if (e.target.value.length >= cfg.max && cfg.nextRef?.current) {
                        cfg.nextRef.current.focus();
                      }
                    }}
                    style={{ ...tacticalInput, width: i === 0 ? '70px' : '62px', textAlign: 'center' }}
                    placeholder={cfg.placeholder}
                  />
                  {i < 2 && <span style={{ color: '#7D9CB8', fontWeight: 700 }}>:</span>}
                </React.Fragment>
              ))}
              <span style={{ fontSize: '0.75rem', color: 'rgba(125,156,184,0.6)' }}>H : MM : SS</span>
            </div>
          </div>

          {/* Elevation */}
          <div>
            <label style={tacticalLabel}>Elevation Gain (feet)</label>
            <input
              type="number"
              min="0"
              value={form.elevation_gain_feet}
              onChange={e => set('elevation_gain_feet', e.target.value)}
              style={{ ...tacticalInput, width: '160px' }}
              placeholder="18,000"
            />
          </div>

          {/* Notes */}
          <div>
            <label style={tacticalLabel}>Notes <span style={{ color: 'rgba(125,156,184,0.5)', fontWeight: 400, textTransform: 'none', letterSpacing: 0 }}>— optional</span></label>
            <textarea
              value={form.notes}
              onChange={e => set('notes', e.target.value)}
              style={{ ...tacticalInput, minHeight: '70px', resize: 'vertical', fontFamily: 'inherit' }}
              placeholder="Course notes, crew access, key checkpoints..."
            />
          </div>

          {/* Actions */}
          <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
            <button
              onClick={onClose}
              disabled={isSaving}
              style={{
                padding: '8px 20px',
                backgroundColor: 'rgba(230,240,255,0.07)',
                color: '#E6F0FF',
                border: '1px solid rgba(125,156,184,0.4)',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '0.8rem',
                fontWeight: 600,
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
              {isSaving ? 'Saving...' : mode === 'add' ? 'Set Target' : 'Commit Changes'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// ============================================================================
// PREF MODAL
// ============================================================================

// ============================================================================
// ATHLETE PROFILE MODAL
// ============================================================================

interface AthleteProfileModalProps {
  primarySport: string;
  secondarySport: string;
  experienceLevel: string;
  onSave: (primarySport: string, secondarySport: string, experienceLevel: string) => void;
  onClose: () => void;
}

const AthleteProfileModal: React.FC<AthleteProfileModalProps> = ({
  primarySport, secondarySport, experienceLevel, onSave, onClose,
}) => {
  const [ps, setPs] = useState(primarySport);
  const [ss, setSs] = useState(secondarySport);
  const [el, setEl] = useState(experienceLevel);

  return (
    <div
      style={{
        position: 'fixed', inset: 0, zIndex: 1000,
        backgroundColor: 'rgba(0,0,0,0.65)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        padding: '20px',
      }}
      onClick={e => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div style={{
        ...CARBON,
        border: '1px solid rgba(255,87,34,0.7)',
        borderRadius: '8px',
        overflow: 'hidden',
        width: '100%',
        maxWidth: '480px',
      }}>
        <div style={{
          background: 'linear-gradient(90deg, #E6F0FF 0%, #7D9CB8 50%, #1B2E4B 100%)',
          padding: '12px 24px',
        }}>
          <span style={{ fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.12em', color: '#1B2E4B', textTransform: 'uppercase' }}>
            Athlete Profile
          </span>
        </div>

        <div style={{ padding: '20px 24px 24px' }}>
          <div style={{ marginBottom: '16px' }}>
            <label style={tacticalLabel}>Primary Sport</label>
            <select value={ps} onChange={e => setPs(e.target.value)} style={tacticalInput}>
              <option value="trail_running">Trail Running</option>
              <option value="running">Running (Road/Flat)</option>
              <option value="cycling">Cycling</option>
              <option value="swimming">Swimming</option>
              <option value="strength">Strength Training</option>
              <option value="other">Other</option>
            </select>
          </div>

          <div style={{ marginBottom: '16px' }}>
            <label style={tacticalLabel}>Secondary Sport (Cross-Training)</label>
            <select value={ss} onChange={e => setSs(e.target.value)} style={tacticalInput}>
              <option value="">None</option>
              <option value="running">Running</option>
              <option value="cycling">Cycling</option>
              <option value="swimming">Swimming</option>
              <option value="rowing">Rowing</option>
              <option value="backcountry_skiing">Backcountry Skiing</option>
              <option value="strength">Strength Training</option>
              <option value="other">Other</option>
            </select>
          </div>

          <div style={{ marginBottom: '8px' }}>
            <label style={tacticalLabel}>Year Began Trail Running</label>
            <select value={el} onChange={e => setEl(e.target.value)} style={tacticalInput}>
              {(() => {
                const currentYear = new Date().getFullYear();
                const options = [];
                for (let y = currentYear; y >= currentYear - 10; y--) {
                  options.push(<option key={y} value={String(y)}>{y}</option>);
                }
                return options;
              })()}
            </select>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '24px' }}>
            <button
              onClick={() => onSave(ps, ss, el)}
              style={{
                padding: '8px 24px',
                backgroundColor: '#FF5722',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '0.8rem',
                fontWeight: 700,
                letterSpacing: '0.06em',
              }}
            >
              Apply
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

interface PrefModalProps {
  pref: 'communication' | 'risk';
  coachingSpectrum: number;
  riskTolerance: string;
  onSpectrumChange: (v: number) => void;
  onRiskChange: (v: string) => void;
  onClose: () => void;
}

const PrefModal: React.FC<PrefModalProps> = ({
  pref, coachingSpectrum, riskTolerance, onSpectrumChange, onRiskChange, onClose,
}) => {
  const title = pref === 'communication' ? 'Communication Style' : 'Risk Tolerance';
  const description = pref === 'communication'
    ? 'How the AI communicates training advice and feedback'
    : 'How the AI balances risk vs. performance in recommendations';

  return (
    <div
      style={{
        position: 'fixed', inset: 0, zIndex: 1000,
        backgroundColor: 'rgba(0,0,0,0.65)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        padding: '20px',
      }}
      onClick={e => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div style={{
        ...CARBON,
        border: '1px solid rgba(255,87,34,0.7)',
        borderRadius: '8px',
        overflow: 'hidden',
        width: '100%',
        maxWidth: '560px',
        maxHeight: '90vh',
        overflowY: 'auto',
      }}>
        {/* Header */}
        <div style={{
          background: 'linear-gradient(90deg, #E6F0FF 0%, #7D9CB8 50%, #1B2E4B 100%)',
          padding: '12px 24px',
        }}>
          <span style={{ fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.12em', color: '#1B2E4B', textTransform: 'uppercase' }}>
            {title}
          </span>
        </div>

        <div style={{ padding: '20px 24px 24px' }}>
          <p style={{ margin: '0 0 20px', fontSize: '0.78rem', color: 'rgba(125,156,184,0.75)', lineHeight: '1.5' }}>
            {description}
          </p>

          {pref === 'communication' ? (
            <CoachingStyleSpectrum initialValue={coachingSpectrum} onChange={onSpectrumChange} />
          ) : (
            <RiskToleranceSelector value={riskTolerance} onChange={onRiskChange} />
          )}

          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '24px' }}>
            <button
              onClick={onClose}
              style={{
                padding: '8px 24px',
                backgroundColor: '#FF5722',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '0.8rem',
                fontWeight: 700,
                letterSpacing: '0.06em',
              }}
            >
              Apply
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// ============================================================================
// SEASON PAGE
// ============================================================================

const SeasonPage: React.FC = () => {
  const [goals, setGoals] = useState<RaceGoal[]>([]);
  const [checkedIds, setCheckedIds] = useState<Set<number>>(new Set());
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [modalMode, setModalMode] = useState<'add' | 'edit' | null>(null);
  const [editingGoal, setEditingGoal] = useState<RaceGoal | null>(null);

  const [raceReadiness, setRaceReadiness] = useState<RaceReadiness | null>(null);
  const [athleteModel, setAthleteModel] = useState<AthleteModel | null>(null);
  const [coachingSpectrum, setCoachingSpectrum] = useState<number>(50);
  const [riskTolerance, setRiskTolerance] = useState<string>('balanced');
  const [primarySport, setPrimarySport] = useState<string>('trail_running');
  const [secondarySport, setSecondarySport] = useState<string>('');
  const [experienceLevel, setExperienceLevel] = useState<string>(String(new Date().getFullYear()));

  const [isLoading, setIsLoading] = useState(true);
  const [isSavingStyle, setIsSavingStyle] = useState(false);
  const [editingPref, setEditingPref] = useState<'communication' | 'risk' | null>(null);
  const [editingProfile, setEditingProfile] = useState(false);

  // ──────────────────────────────────────────
  // FETCH
  // ──────────────────────────────────────────

  const fetchAll = async () => {
    try {
      const [goalsRes, readinessRes, modelRes, settingsRes] = await Promise.all([
        fetch('/api/coach/race-goals'),
        fetch('/api/coach/race-readiness'),
        fetch('/api/athlete-model'),
        fetch('/api/user-settings'),
      ]);

      if (goalsRes.ok) {
        const d = await goalsRes.json();
        const list: RaceGoal[] = d.goals || [];
        setGoals(list);
        // Default selection: nearest A race
        if (selectedId === null) {
          const aRace = list.find(g => g.priority === 'A');
          if (aRace) setSelectedId(aRace.id);
        }
      }

      if (readinessRes.ok) {
        const d = await readinessRes.json();
        if (d.success && d.readiness) setRaceReadiness(d.readiness);
      }

      if (modelRes.ok) {
        const d = await modelRes.json();
        if (d.success) setAthleteModel(d.model);
      }

      if (settingsRes.ok) {
        const d = await settingsRes.json();
        setCoachingSpectrum(d.coaching_style_spectrum ?? 50);
        setRiskTolerance(d.recommendation_style ?? 'balanced');
        setPrimarySport(d.primary_sport ?? 'trail_running');
        setSecondarySport(d.secondary_sport ?? '');
        const rawExp = d.training_experience ?? '';
        // If stored value is a legacy enum, default to current year
        const legacyEnums = ['beginner', 'intermediate', 'advanced', 'elite'];
        setExperienceLevel(legacyEnums.includes(rawExp) || !rawExp
          ? String(new Date().getFullYear())
          : rawExp
        );
      }
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => { fetchAll(); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // ──────────────────────────────────────────
  // HANDLERS — RACE LIST
  // ──────────────────────────────────────────

  const toggleCheck = (id: number, e: React.MouseEvent) => {
    e.stopPropagation();
    setCheckedIds(prev => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const toggleSelectAll = () => {
    if (checkedIds.size === goals.length) {
      setCheckedIds(new Set());
    } else {
      setCheckedIds(new Set(goals.map(g => g.id)));
    }
  };

  const handleDelete = async (ids: number[]) => {
    if (!window.confirm(`Delete ${ids.length} race goal${ids.length > 1 ? 's' : ''}?`)) return;
    await Promise.all(ids.map(id => fetch(`/api/coach/race-goals/${id}`, { method: 'DELETE' })));
    setCheckedIds(new Set());
    if (ids.includes(selectedId ?? -1)) setSelectedId(null);
    fetchAll();
  };

  const handleEdit = () => {
    const goal = goals.find(g => g.id === [...checkedIds][0]);
    if (goal) { setEditingGoal(goal); setModalMode('edit'); }
  };

  // ──────────────────────────────────────────
  // HANDLERS — STYLE SETTINGS
  // ──────────────────────────────────────────

  const saveStyle = async (spectrum: number, risk: string) => {
    setIsSavingStyle(true);
    try {
      await fetch('/api/user-settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ coaching_style_spectrum: spectrum, recommendation_style: risk }),
      });
    } finally {
      setIsSavingStyle(false);
    }
  };

  const handleSpectrumChange = (value: number) => {
    setCoachingSpectrum(value);
    saveStyle(value, riskTolerance);
  };

  const handleRiskChange = (value: string) => {
    setRiskTolerance(value);
    saveStyle(coachingSpectrum, value);
  };

  const handleProfileSave = async (ps: string, ss: string, el: string) => {
    setPrimarySport(ps);
    setSecondarySport(ss);
    setExperienceLevel(el);
    setEditingProfile(false);
    await fetch('/api/user-settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ primary_sport: ps, secondary_sport: ss || null, training_experience: el }),
    });
  };

  // ──────────────────────────────────────────
  // RENDER HELPERS
  // ──────────────────────────────────────────

  const sorted = [...goals].sort((a, b) => {
    const pri = { A: 0, B: 1, C: 2 };
    if (pri[a.priority] !== pri[b.priority]) return pri[a.priority] - pri[b.priority];
    return new Date(a.race_date + 'T12:00:00').getTime() - new Date(b.race_date + 'T12:00:00').getTime();
  });

  const priorityLabel = (p: 'A' | 'B' | 'C') =>
    p === 'A' ? '"A"' : p;

  const priorityColor = (p: 'A' | 'B' | 'C') =>
    p === 'A' ? '#FF5722' : p === 'B' ? '#7D9CB8' : 'rgba(125,156,184,0.5)';

  const communicationLabel = (v: number) => {
    if (v <= 25) return 'Casual';
    if (v <= 50) return 'Supportive';
    if (v <= 75) return 'Motivational';
    return 'Analytical';
  };

  const riskLabel = (v: string) => v.charAt(0).toUpperCase() + v.slice(1);

  const sportLabel = (v: string) => {
    const map: Record<string, string> = {
      trail_running: 'Trail Running', running: 'Running', road_running: 'Road Running',
      cycling: 'Cycling', swimming: 'Swimming', triathlon: 'Triathlon',
      rowing: 'Rowing', backcountry_skiing: 'Backcountry Skiing',
      strength: 'Strength', other: 'Other', '': 'None',
    };
    return map[v] ?? v;
  };

  const experienceLabel = (v: string) => {
    // Legacy enum values
    const legacy: Record<string, string> = {
      beginner: 'Beginner', intermediate: 'Intermediate', advanced: 'Advanced', elite: 'Elite',
    };
    if (legacy[v]) return legacy[v];
    // Year value — show as "Since YYYY"
    if (/^\d{4}$/.test(v)) return `Since ${v}`;
    return v;
  };

  if (isLoading) {
    return (
      <div style={{ padding: '40px', textAlign: 'center', color: '#7D9CB8', fontSize: '0.875rem' }}>
        Loading season data...
      </div>
    );
  }

  // ──────────────────────────────────────────
  // RENDER
  // ──────────────────────────────────────────

  return (
    <>
      {/* Race Goal Modal */}
      {modalMode && (
        <GoalModal
          mode={modalMode}
          initialData={editingGoal ?? undefined}
          onSave={() => { setModalMode(null); setEditingGoal(null); setCheckedIds(new Set()); fetchAll(); }}
          onClose={() => { setModalMode(null); setEditingGoal(null); }}
        />
      )}

      {/* Athlete Profile Modal */}
      {editingProfile && (
        <AthleteProfileModal
          primarySport={primarySport}
          secondarySport={secondarySport}
          experienceLevel={experienceLevel}
          onSave={handleProfileSave}
          onClose={() => setEditingProfile(false)}
        />
      )}

      {/* Coaching Pref Modal */}
      {editingPref && (
        <PrefModal
          pref={editingPref}
          coachingSpectrum={coachingSpectrum}
          riskTolerance={riskTolerance}
          onSpectrumChange={handleSpectrumChange}
          onRiskChange={handleRiskChange}
          onClose={() => setEditingPref(null)}
        />
      )}

      <div style={{ display: 'flex', gap: '20px', alignItems: 'flex-start', background: '#f0f4f8', borderRadius: '10px', padding: '16px' }}>

        {/* ── LEFT SIDEBAR COLUMN ── */}
        <div style={{ width: '280px', flexShrink: 0, display: 'flex', flexDirection: 'column', gap: '12px' }}>

        {/* Race Season card */}
        <div style={{
          backgroundColor: 'white',
          borderRadius: '8px',
          border: '1px solid #d1dce8',
          boxShadow: '0 2px 6px rgba(0,0,0,0.07)',
          overflow: 'hidden',
        }}>
          {/* Panel header */}
          <div style={{
            background: 'linear-gradient(90deg, #E6F0FF 0%, #7D9CB8 50%, #1B2E4B 100%)',
            padding: '10px 16px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}>
            <span style={{ fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.12em', color: '#1B2E4B', textTransform: 'uppercase' }}>
              Race Season
            </span>
            {goals.length > 0 && (
              <input
                type="checkbox"
                checked={checkedIds.size === goals.length && goals.length > 0}
                onChange={toggleSelectAll}
                title="Select all"
                style={{ accentColor: '#FF5722', cursor: 'pointer' }}
              />
            )}
          </div>

          {/* Action bar — visible when items checked */}
          {checkedIds.size > 0 && (
            <div style={{
              padding: '8px 16px',
              backgroundColor: '#1B2E4B',
              display: 'flex',
              gap: '8px',
              alignItems: 'center',
              borderBottom: '1px solid rgba(125,156,184,0.2)',
            }}>
              <span style={{ fontSize: '0.72rem', color: '#7D9CB8', flex: 1 }}>
                {checkedIds.size} selected
              </span>
              {checkedIds.size === 1 && (
                <button
                  onClick={handleEdit}
                  style={{
                    padding: '4px 12px',
                    backgroundColor: 'rgba(125,156,184,0.15)',
                    border: '1px solid rgba(125,156,184,0.4)',
                    borderRadius: '4px',
                    color: '#E6F0FF',
                    fontSize: '0.72rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                  }}
                >
                  Edit
                </button>
              )}
              <button
                onClick={() => handleDelete([...checkedIds])}
                style={{
                  padding: '4px 12px',
                  backgroundColor: 'rgba(220,38,38,0.15)',
                  border: '1px solid rgba(220,38,38,0.4)',
                  borderRadius: '4px',
                  color: '#fca5a5',
                  fontSize: '0.72rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                Delete
              </button>
            </div>
          )}

          {/* Race rows */}
          <div>
            {sorted.length === 0 ? (
              <div style={{ padding: '24px 16px', textAlign: 'center', color: '#9ca3af', fontSize: '0.8rem' }}>
                No races configured
              </div>
            ) : (
              sorted.map(goal => {
                const isSelected = selectedId === goal.id;
                const isChecked = checkedIds.has(goal.id);
                return (
                  <div
                    key={goal.id}
                    onClick={() => setSelectedId(goal.id)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '10px',
                      padding: '10px 16px',
                      backgroundColor: isSelected ? '#f0f7ff' : 'white',
                      borderLeft: isSelected ? '3px solid #3b82f6' : '3px solid transparent',
                      borderBottom: '1px solid #f3f4f6',
                      cursor: 'pointer',
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={isChecked}
                      onChange={() => {}}
                      onClick={e => toggleCheck(goal.id, e)}
                      style={{ accentColor: '#FF5722', cursor: 'pointer', flexShrink: 0 }}
                    />
                    {/* Priority badge */}
                    <span style={{
                      fontSize: '0.7rem',
                      fontWeight: 700,
                      color: priorityColor(goal.priority),
                      letterSpacing: '0.04em',
                      flexShrink: 0,
                      minWidth: '20px',
                    }}>
                      {priorityLabel(goal.priority)}
                    </span>
                    {/* Name + meta */}
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{
                        fontSize: '0.8rem',
                        fontWeight: 600,
                        color: '#1F2937',
                        whiteSpace: 'nowrap',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                      }}>
                        {goal.race_name}
                      </div>
                      <div style={{ fontSize: '0.7rem', color: '#9ca3af', marginTop: '2px' }}>
                        {formatDate(goal.race_date)}
                        {goal.distance_miles ? ` · ${goal.distance_miles}mi` : ''}
                        {goal.race_type ? ` · ${goal.race_type}` : ''}
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>

          {/* Add Race button */}
          <div style={{ padding: '12px 16px', borderTop: '1px solid #f3f4f6' }}>
            <button
              onClick={() => { setEditingGoal(null); setModalMode('add'); }}
              style={{
                width: '100%',
                padding: '8px',
                backgroundColor: '#FF5722',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '0.75rem',
                fontWeight: 700,
                letterSpacing: '0.06em',
              }}
            >
              + Add Race
            </button>
          </div>
        </div>{/* end Race Season card */}

        {/* Coaching Preferences card */}
        <div style={{
          backgroundColor: 'white',
          borderRadius: '8px',
          border: '1px solid #d1dce8',
          boxShadow: '0 2px 6px rgba(0,0,0,0.07)',
          overflow: 'hidden',
        }}>
          <div style={{
            background: 'linear-gradient(90deg, #E6F0FF 0%, #7D9CB8 50%, #1B2E4B 100%)',
            padding: '10px 16px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}>
            <span style={{ fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.12em', color: '#1B2E4B', textTransform: 'uppercase' }}>
              Coaching Preferences
            </span>
            {isSavingStyle && (
              <span style={{ fontSize: '0.62rem', color: '#1B2E4B', opacity: 0.6 }}>Saving...</span>
            )}
          </div>

          <div style={{ padding: '10px 16px', borderBottom: '1px solid #f3f4f6', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#1F2937' }}>Communication</div>
              <div style={{ fontSize: '0.7rem', color: '#6b7280', marginTop: '1px' }}>{communicationLabel(coachingSpectrum)}</div>
            </div>
            <button
              onClick={() => setEditingPref('communication')}
              style={{ padding: '4px 12px', backgroundColor: 'white', border: '1px solid #dee2e6', borderRadius: '4px', cursor: 'pointer', fontSize: '0.72rem', fontWeight: 600, color: '#6b7280', flexShrink: 0 }}
            >
              Edit
            </button>
          </div>

          <div style={{ padding: '10px 16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#1F2937' }}>Risk Tolerance</div>
              <div style={{ fontSize: '0.7rem', color: '#6b7280', marginTop: '1px' }}>{riskLabel(riskTolerance)}</div>
            </div>
            <button
              onClick={() => setEditingPref('risk')}
              style={{ padding: '4px 12px', backgroundColor: 'white', border: '1px solid #dee2e6', borderRadius: '4px', cursor: 'pointer', fontSize: '0.72rem', fontWeight: 600, color: '#6b7280', flexShrink: 0 }}
            >
              Edit
            </button>
          </div>
        </div>{/* end Coaching Preferences card */}

        {/* Athlete Profile card */}
        <div style={{
          backgroundColor: 'white',
          borderRadius: '8px',
          border: '1px solid #d1dce8',
          boxShadow: '0 2px 6px rgba(0,0,0,0.07)',
          overflow: 'hidden',
        }}>
          <div style={{
            background: 'linear-gradient(90deg, #E6F0FF 0%, #7D9CB8 50%, #1B2E4B 100%)',
            padding: '10px 16px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}>
            <span style={{ fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.12em', color: '#1B2E4B', textTransform: 'uppercase' }}>
              Athlete Profile
            </span>
          </div>

          <div style={{ padding: '10px 16px', borderBottom: '1px solid #f3f4f6', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#1F2937' }}>Primary Sport</div>
              <div style={{ fontSize: '0.7rem', color: '#6b7280', marginTop: '1px' }}>{sportLabel(primarySport)}</div>
            </div>
            <button
              onClick={() => setEditingProfile(true)}
              style={{ padding: '4px 12px', backgroundColor: 'white', border: '1px solid #dee2e6', borderRadius: '4px', cursor: 'pointer', fontSize: '0.72rem', fontWeight: 600, color: '#6b7280', flexShrink: 0 }}
            >
              Edit
            </button>
          </div>

          <div style={{ padding: '10px 16px', borderBottom: '1px solid #f3f4f6', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#1F2937' }}>Cross-Training</div>
              <div style={{ fontSize: '0.7rem', color: '#6b7280', marginTop: '1px' }}>{sportLabel(secondarySport)}</div>
            </div>
          </div>

          <div style={{ padding: '10px 16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#1F2937' }}>Experience</div>
              <div style={{ fontSize: '0.7rem', color: '#6b7280', marginTop: '1px' }}>{experienceLabel(experienceLevel)}</div>
            </div>
          </div>
        </div>{/* end Athlete Profile card */}

        </div>{/* end LEFT SIDEBAR COLUMN */}

        {/* ── RIGHT MAIN AREA ── */}
        <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <RaceReadinessCard readiness={raceReadiness} />
          <AthleteModelPanel model={athleteModel} />
        </div>

      </div>
    </>
  );
};

export default SeasonPage;
