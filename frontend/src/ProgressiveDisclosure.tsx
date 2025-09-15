import React, { createContext, useContext, useState, useEffect } from 'react';

interface ProgressiveDisclosureContextType {
  showAdvancedFeatures: boolean;
  userExperienceLevel: 'beginner' | 'intermediate' | 'advanced';
  toggleAdvancedFeatures: () => void;
  setUserExperienceLevel: (level: 'beginner' | 'intermediate' | 'advanced') => void;
  hasInteractedWithBasicFeatures: boolean;
  markBasicFeatureInteraction: () => void;
}

const ProgressiveDisclosureContext = createContext<ProgressiveDisclosureContextType | undefined>(undefined);

export const useProgressiveDisclosure = () => {
  const context = useContext(ProgressiveDisclosureContext);
  if (!context) {
    throw new Error('useProgressiveDisclosure must be used within a ProgressiveDisclosureProvider');
  }
  return context;
};

interface ProgressiveDisclosureProviderProps {
  children: React.ReactNode;
}

export const ProgressiveDisclosureProvider: React.FC<ProgressiveDisclosureProviderProps> = ({ children }) => {
  const [showAdvancedFeatures, setShowAdvancedFeatures] = useState(false);
  const [userExperienceLevel, setUserExperienceLevel] = useState<'beginner' | 'intermediate' | 'advanced'>('beginner');
  const [hasInteractedWithBasicFeatures, setHasInteractedWithBasicFeatures] = useState(false);
  const [interactionCount, setInteractionCount] = useState(0);

  // Load user preferences from localStorage
  useEffect(() => {
    const savedLevel = localStorage.getItem('trainingmonkey-user-level');
    const savedAdvanced = localStorage.getItem('trainingmonkey-show-advanced');
    const savedInteractions = localStorage.getItem('trainingmonkey-interactions');
    
    if (savedLevel && ['beginner', 'intermediate', 'advanced'].includes(savedLevel)) {
      setUserExperienceLevel(savedLevel as 'beginner' | 'intermediate' | 'advanced');
    }
    
    if (savedAdvanced === 'true') {
      setShowAdvancedFeatures(true);
    }
    
    if (savedInteractions) {
      const count = parseInt(savedInteractions, 10);
      setInteractionCount(count);
      setHasInteractedWithBasicFeatures(count > 0);
    }
  }, []);

  // Auto-reveal advanced features based on user interactions
  useEffect(() => {
    if (interactionCount >= 5 && userExperienceLevel === 'beginner') {
      setUserExperienceLevel('intermediate');
      localStorage.setItem('trainingmonkey-user-level', 'intermediate');
    }
    
    if (interactionCount >= 15 && userExperienceLevel === 'intermediate') {
      setUserExperienceLevel('advanced');
      localStorage.setItem('trainingmonkey-user-level', 'advanced');
    }
  }, [interactionCount, userExperienceLevel]);

  const toggleAdvancedFeatures = () => {
    const newState = !showAdvancedFeatures;
    setShowAdvancedFeatures(newState);
    localStorage.setItem('trainingmonkey-show-advanced', newState.toString());
  };

  const setUserExperienceLevelWrapper = (level: 'beginner' | 'intermediate' | 'advanced') => {
    setUserExperienceLevel(level);
    localStorage.setItem('trainingmonkey-user-level', level);
    
    // Auto-show advanced features for advanced users
    if (level === 'advanced') {
      setShowAdvancedFeatures(true);
      localStorage.setItem('trainingmonkey-show-advanced', 'true');
    }
  };

  const markBasicFeatureInteraction = () => {
    const newCount = interactionCount + 1;
    setInteractionCount(newCount);
    setHasInteractedWithBasicFeatures(true);
    localStorage.setItem('trainingmonkey-interactions', newCount.toString());
  };

  const value: ProgressiveDisclosureContextType = {
    showAdvancedFeatures,
    userExperienceLevel,
    toggleAdvancedFeatures,
    setUserExperienceLevel: setUserExperienceLevelWrapper,
    hasInteractedWithBasicFeatures,
    markBasicFeatureInteraction
  };

  return (
    <ProgressiveDisclosureContext.Provider value={value}>
      {children}
    </ProgressiveDisclosureContext.Provider>
  );
};

// Progressive Disclosure Toggle Component
interface ProgressiveDisclosureToggleProps {
  className?: string;
  style?: React.CSSProperties;
}

export const ProgressiveDisclosureToggle: React.FC<ProgressiveDisclosureToggleProps> = ({ 
  className = '', 
  style = {} 
}) => {
  const { showAdvancedFeatures, toggleAdvancedFeatures, userExperienceLevel } = useProgressiveDisclosure();

  return (
    <div 
      className={className}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '0.5rem',
        padding: '0.5rem',
        backgroundColor: '#f8f9fa',
        borderRadius: '6px',
        border: '1px solid #e9ecef',
        ...style
      }}
    >
      <span style={{ fontSize: '0.875rem', color: '#6c757d' }}>
        {userExperienceLevel === 'beginner' ? '👶' : 
         userExperienceLevel === 'intermediate' ? '🚀' : '⚡'} 
        {userExperienceLevel.charAt(0).toUpperCase() + userExperienceLevel.slice(1)} Mode
      </span>
      <button
        onClick={toggleAdvancedFeatures}
        style={{
          padding: '0.25rem 0.75rem',
          backgroundColor: showAdvancedFeatures ? '#28a745' : '#6c757d',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: 'pointer',
          fontSize: '0.75rem',
          fontWeight: '500',
          transition: 'all 0.2s ease'
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.backgroundColor = showAdvancedFeatures ? '#218838' : '#5a6268';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.backgroundColor = showAdvancedFeatures ? '#28a745' : '#6c757d';
        }}
      >
        {showAdvancedFeatures ? 'Hide Advanced' : 'Show Advanced'}
      </button>
    </div>
  );
};

// Progressive Disclosure Wrapper Component
interface ProgressiveDisclosureWrapperProps {
  children: React.ReactNode;
  feature: 'dateRange' | 'sportFilter' | 'frozenTooltips' | 'advancedInsights' | 'chartCustomization';
  minLevel?: 'beginner' | 'intermediate' | 'advanced';
  className?: string;
  style?: React.CSSProperties;
}

export const ProgressiveDisclosureWrapper: React.FC<ProgressiveDisclosureWrapperProps> = ({
  children,
  feature,
  minLevel = 'intermediate',
  className = '',
  style = {}
}) => {
  const { showAdvancedFeatures, userExperienceLevel } = useProgressiveDisclosure();

  const shouldShow = showAdvancedFeatures || 
    (minLevel === 'beginner') ||
    (minLevel === 'intermediate' && userExperienceLevel !== 'beginner') ||
    (minLevel === 'advanced' && userExperienceLevel === 'advanced');

  if (!shouldShow) {
    return null;
  }

  return (
    <div className={className} style={style}>
      {children}
    </div>
  );
};

// Feature Introduction Component
interface FeatureIntroductionProps {
  feature: string;
  description: string;
  onDismiss: () => void;
  onLearnMore?: () => void;
}

export const FeatureIntroduction: React.FC<FeatureIntroductionProps> = ({
  feature,
  description,
  onDismiss,
  onLearnMore
}) => {
  return (
    <div style={{
      position: 'fixed',
      top: '20px',
      right: '20px',
      backgroundColor: '#e3f2fd',
      border: '1px solid #2196f3',
      borderRadius: '8px',
      padding: '1rem',
      maxWidth: '300px',
      zIndex: 1000,
      boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)'
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
        <h4 style={{ margin: 0, fontSize: '0.9rem', color: '#1976d2' }}>
          ✨ New Feature: {feature}
        </h4>
        <button
          onClick={onDismiss}
          style={{
            background: 'none',
            border: 'none',
            fontSize: '1.2rem',
            cursor: 'pointer',
            color: '#666',
            padding: '0',
            lineHeight: '1'
          }}
        >
          ×
        </button>
      </div>
      <p style={{ margin: '0 0 0.75rem 0', fontSize: '0.8rem', color: '#424242', lineHeight: '1.4' }}>
        {description}
      </p>
      <div style={{ display: 'flex', gap: '0.5rem' }}>
        <button
          onClick={onDismiss}
          style={{
            padding: '0.25rem 0.75rem',
            backgroundColor: '#2196f3',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '0.75rem'
          }}
        >
          Got it!
        </button>
        {onLearnMore && (
          <button
            onClick={onLearnMore}
            style={{
              padding: '0.25rem 0.75rem',
              backgroundColor: 'transparent',
              color: '#2196f3',
              border: '1px solid #2196f3',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '0.75rem'
            }}
          >
            Learn More
          </button>
        )}
      </div>
    </div>
  );
};
