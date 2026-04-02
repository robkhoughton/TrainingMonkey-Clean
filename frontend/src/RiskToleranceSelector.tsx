import React from 'react';

interface RiskToleranceSelectorProps {
  value?: string;
  onChange?: (value: string) => void;
  disabled?: boolean;
}

const RISK_OPTIONS = [
  {
    value: 'conservative',
    label: 'Conservative',
    description: 'Earlier warnings, more recovery emphasis — ACWR ceiling 1.2',
    color: '#16a34a',
  },
  {
    value: 'balanced',
    label: 'Balanced',
    description: 'Evidence-based defaults — ACWR ceiling 1.3',
    color: '#eab308',
  },
  {
    value: 'adaptive',
    label: 'Adaptive',
    description: 'Adjusts to individual response patterns — ACWR ceiling 1.35',
    color: '#f97316',
  },
  {
    value: 'aggressive',
    label: 'Aggressive',
    description: 'High fatigue tolerance, hard progression push — ACWR ceiling 1.5',
    color: '#dc2626',
  },
];

const RiskToleranceSelector: React.FC<RiskToleranceSelectorProps> = ({
  value = 'balanced',
  onChange = () => {},
  disabled = false,
}) => {
  const active = RISK_OPTIONS.find(o => o.value === value) || RISK_OPTIONS[1];

  return (
    <div>
      {/* Axis labels */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        marginBottom: '6px',
        fontSize: '0.65rem',
        color: 'rgba(125,156,184,0.5)',
        letterSpacing: '0.06em',
        textTransform: 'uppercase',
      }}>
        <span>Low Risk / Low Return</span>
        <span>High Risk / High Return</span>
      </div>

      {/* Gradient arrow bar */}
      <div style={{ position: 'relative', marginBottom: '12px' }}>
        <div style={{
          height: '10px',
          borderRadius: '5px 0 0 5px',
          background: 'linear-gradient(to right, #16a34a, #eab308, #f97316, #dc2626)',
          position: 'relative',
        }}>
          {/* Arrow head */}
          <div style={{
            position: 'absolute',
            right: '-9px',
            top: '-3px',
            width: 0,
            height: 0,
            borderTop: '8px solid transparent',
            borderBottom: '8px solid transparent',
            borderLeft: '10px solid #dc2626',
          }} />
        </div>
      </div>

      {/* Option buttons positioned under the bar */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '14px' }}>
        {RISK_OPTIONS.map(option => {
          const isActive = option.value === active.value;
          return (
            <button
              key={option.value}
              type="button"
              onClick={() => !disabled && onChange(option.value)}
              disabled={disabled}
              style={{
                flex: 1,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: '6px',
                background: 'none',
                border: 'none',
                cursor: disabled ? 'not-allowed' : 'pointer',
                padding: '4px 0',
                opacity: disabled ? 0.6 : 1,
              }}
            >
              {/* Dot marker */}
              <div style={{
                width: isActive ? '14px' : '8px',
                height: isActive ? '14px' : '8px',
                borderRadius: '50%',
                backgroundColor: isActive ? option.color : 'rgba(125,156,184,0.35)',
                boxShadow: isActive ? `0 0 0 3px ${option.color}33` : 'none',
                transition: 'all 0.2s ease',
                flexShrink: 0,
              }} />
              {/* Label */}
              <div style={{
                fontSize: '0.68rem',
                fontWeight: isActive ? 700 : 500,
                color: isActive ? option.color : '#7D9CB8',
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
                whiteSpace: 'nowrap',
              }}>
                {option.label}
              </div>
            </button>
          );
        })}
      </div>

      {/* Active description */}
      <div style={{
        padding: '10px 14px',
        backgroundColor: '#162440',
        borderLeft: `3px solid ${active.color}`,
        borderTop: `1px solid ${active.color}33`,
        borderRight: `1px solid ${active.color}33`,
        borderBottom: `1px solid ${active.color}33`,
        borderRadius: '4px',
        fontSize: '0.78rem',
        color: 'rgba(230,240,255,0.75)',
        lineHeight: '1.4',
      }}>
        {active.description}
      </div>
    </div>
  );
};

export default RiskToleranceSelector;
