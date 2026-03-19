import React, { useState, useEffect } from 'react';

interface CoachingStyleSpectrumProps {
  initialValue?: number;
  onChange?: (value: number) => void;
  disabled?: boolean;
}

const STYLES = [
  {
    value: 12,
    label: 'Casual',
    description: 'Friendly, conversational — minimal jargon, training as enjoyment',
    range: [0, 25] as [number, number],
  },
  {
    value: 37,
    label: 'Supportive',
    description: 'Lead with affirmation — frame deviations as learning, build confidence',
    range: [26, 50] as [number, number],
  },
  {
    value: 62,
    label: 'Motivational',
    description: 'Action-oriented — performance challenges, push for improvement',
    range: [51, 75] as [number, number],
  },
  {
    value: 87,
    label: 'Analytical',
    description: 'Technical and precise — metrics, evidence-based, direct feedback',
    range: [76, 100] as [number, number],
  },
];

const getActiveStyle = (value: number) =>
  STYLES.find(s => value >= s.range[0] && value <= s.range[1]) || STYLES[1];

const CoachingStyleSpectrum: React.FC<CoachingStyleSpectrumProps> = ({
  initialValue = 50,
  onChange = () => {},
  disabled = false,
}) => {
  const [spectrumValue, setSpectrumValue] = useState(initialValue);

  useEffect(() => {
    setSpectrumValue(initialValue);
  }, [initialValue]);

  const active = getActiveStyle(spectrumValue);

  const handleSelect = (style: typeof STYLES[0]) => {
    if (disabled) return;
    setSpectrumValue(style.value);
    onChange(style.value);
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '10px' }}>
      {STYLES.map(style => {
        const isActive = active.value === style.value;
        return (
          <button
            key={style.label}
            type="button"
            onClick={() => handleSelect(style)}
            disabled={disabled}
            style={{
              padding: '14px 12px',
              backgroundColor: isActive ? 'rgba(255,87,34,0.1)' : '#162440',
              border: isActive ? '2px solid #FF5722' : '1px solid rgba(125,156,184,0.25)',
              borderRadius: '4px',
              cursor: disabled ? 'not-allowed' : 'pointer',
              textAlign: 'left',
              opacity: disabled ? 0.6 : 1,
              transition: 'all 0.15s ease',
            }}
          >
            <div style={{
              fontSize: '0.72rem',
              fontWeight: 700,
              color: isActive ? '#FF5722' : '#7D9CB8',
              textTransform: 'uppercase',
              letterSpacing: '0.08em',
              marginBottom: '6px',
            }}>
              {style.label}
            </div>
            <div style={{
              fontSize: '0.72rem',
              color: isActive ? 'rgba(230,240,255,0.85)' : 'rgba(125,156,184,0.6)',
              lineHeight: '1.4',
            }}>
              {style.description}
            </div>
          </button>
        );
      })}
    </div>
  );
};

export default CoachingStyleSpectrum;
