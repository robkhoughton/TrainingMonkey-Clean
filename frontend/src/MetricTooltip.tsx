import React from 'react';
import ContextualTooltip from './ContextualTooltip';

interface MetricTooltipProps {
  metric: string;
  value: number | string;
  unit?: string;
  description: string;
  interpretation?: string;
  warning?: string;
  children: React.ReactNode;
  position?: 'top' | 'bottom' | 'left' | 'right';
}

const MetricTooltip: React.FC<MetricTooltipProps> = ({
  metric,
  value,
  unit = '',
  description,
  interpretation,
  warning,
  children,
  position = 'top'
}) => {
  const tooltipContent = (
    <div style={{ maxWidth: '280px' }}>
      <div style={{ 
        fontWeight: '600', 
        fontSize: '0.9rem', 
        marginBottom: '0.5rem',
        color: '#f9fafb'
      }}>
        {metric}
        {value !== undefined && (
          <span style={{ color: '#60a5fa', marginLeft: '0.5rem' }}>
            {value}{unit}
          </span>
        )}
      </div>
      
      <div style={{ 
        fontSize: '0.8rem', 
        lineHeight: '1.4', 
        marginBottom: '0.5rem',
        color: '#d1d5db'
      }}>
        {description}
      </div>
      
      {interpretation && (
        <div style={{ 
          fontSize: '0.8rem', 
          lineHeight: '1.4', 
          marginBottom: '0.5rem',
          color: '#9ca3af',
          fontStyle: 'italic'
        }}>
          💡 {interpretation}
        </div>
      )}
      
      {warning && (
        <div style={{ 
          fontSize: '0.8rem', 
          lineHeight: '1.4',
          color: '#fbbf24',
          fontWeight: '500'
        }}>
          ⚠️ {warning}
        </div>
      )}
    </div>
  );

  return (
    <ContextualTooltip
      content={tooltipContent}
      position={position}
      delay={300}
      maxWidth={300}
    >
      {children}
    </ContextualTooltip>
  );
};

export default MetricTooltip;
