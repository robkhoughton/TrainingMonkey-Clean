import React from 'react';
import ContextualTooltip from './ContextualTooltip';

interface LegendItem {
  value: string;
  type: string;
  color: string;
  dataKey?: string;
}

interface CustomLegendProps {
  payload?: LegendItem[];
  metricExplanations: Record<string, {
    title: string;
    description: string;
    interpretation?: string;
    warning?: string;
  }>;
}

const CustomLegend: React.FC<CustomLegendProps> = ({ payload, metricExplanations }) => {
  if (!payload || payload.length === 0) return null;

  return (
    <div style={{ 
      display: 'flex', 
      flexWrap: 'wrap', 
      gap: '1rem', 
      justifyContent: 'center',
      marginTop: '1rem',
      padding: '0.5rem'
    }}>
      {payload.map((entry, index) => {
        const explanation = metricExplanations[entry.value] || metricExplanations[entry.dataKey || ''] || {
          title: entry.value,
          description: `Information about ${entry.value}`,
          interpretation: 'This metric helps track your training progress.'
        };

        return (
          <ContextualTooltip
            key={index}
            content={
              <div>
                <div style={{ fontWeight: '600', marginBottom: '0.5rem' }}>
                  {explanation.title}
                </div>
                <div style={{ fontSize: '0.8rem', lineHeight: '1.4', marginBottom: '0.5rem' }}>
                  {explanation.description}
                </div>
                {explanation.interpretation && (
                  <div style={{ fontSize: '0.8rem', lineHeight: '1.4', marginBottom: '0.5rem', color: '#9ca3af', fontStyle: 'italic' }}>
                    💡 {explanation.interpretation}
                  </div>
                )}
                {explanation.warning && (
                  <div style={{ fontSize: '0.8rem', lineHeight: '1.4', color: '#fbbf24', fontWeight: '500' }}>
                    ⚠️ {explanation.warning}
                  </div>
                )}
              </div>
            }
            position="top"
            delay={300}
            maxWidth={280}
          >
            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: '0.5rem',
              cursor: 'help',
              padding: '0.25rem 0.5rem',
              borderRadius: '4px',
              transition: 'background-color 0.2s ease'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = '#f3f4f6';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = 'transparent';
            }}
            >
              <div
                style={{
                  width: '12px',
                  height: '12px',
                  backgroundColor: entry.color,
                  borderRadius: entry.type === 'line' ? '0' : '2px'
                }}
              />
              <span style={{ fontSize: '0.875rem', color: '#374151' }}>
                {entry.value}
              </span>
            </div>
          </ContextualTooltip>
        );
      })}
    </div>
  );
};

export default CustomLegend;
