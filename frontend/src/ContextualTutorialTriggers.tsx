import React, { useState, useEffect, useCallback } from 'react';

interface TutorialTrigger {
  id: string;
  tutorialId: string;
  triggerType: 'interaction' | 'feature_access' | 'error' | 'inactivity' | 'scheduled';
  targetElement?: string;
  condition: () => boolean;
  message: string;
  priority: 'low' | 'medium' | 'high';
  cooldown?: number; // minutes
  maxTriggers?: number;
}

interface ContextualTutorialTriggersProps {
  onStartTutorial: (tutorialId: string) => void;
  userExperienceLevel: 'beginner' | 'intermediate' | 'advanced';
  onTriggerShown?: (triggerId: string) => void;
}

const ContextualTutorialTriggers: React.FC<ContextualTutorialTriggersProps> = ({
  onStartTutorial,
  userExperienceLevel,
  onTriggerShown
}) => {
  const [activeTriggers, setActiveTriggers] = useState<TutorialTrigger[]>([]);
  const [triggerHistory, setTriggerHistory] = useState<Map<string, { count: number; lastShown: Date }>>(new Map());
  const [currentTrigger, setCurrentTrigger] = useState<TutorialTrigger | null>(null);
  const [showTrigger, setShowTrigger] = useState<boolean>(false);

  // Define tutorial triggers based on user interactions and context
  const tutorialTriggers: TutorialTrigger[] = [
    // Chart interaction triggers
    {
      id: 'chart_hover_first_time',
      tutorialId: 'dashboard_tutorial',
      triggerType: 'interaction',
      targetElement: '.recharts-wrapper',
      condition: () => {
        const chartElements = document.querySelectorAll('.recharts-wrapper');
        return chartElements.length > 0 && userExperienceLevel === 'beginner';
      },
      message: '💡 Tip: Hover over chart elements to see detailed information. Want to learn more about reading these charts?',
      priority: 'medium',
      cooldown: 30,
      maxTriggers: 1
    },
    {
      id: 'legend_click_first_time',
      tutorialId: 'dashboard_tutorial',
      triggerType: 'interaction',
      targetElement: '.recharts-legend-item',
      condition: () => {
        const legendItems = document.querySelectorAll('.recharts-legend-item');
        return legendItems.length > 0 && userExperienceLevel === 'beginner';
      },
      message: '🎯 Great! You discovered the interactive legend. Click legend items to toggle data series on/off.',
      priority: 'low',
      cooldown: 60,
      maxTriggers: 1
    },
    {
      id: 'date_range_change',
      tutorialId: 'dashboard_advanced_tutorial',
      triggerType: 'interaction',
      targetElement: 'select[name="dateRange"]',
      condition: () => {
        const dateSelect = document.querySelector('select[name="dateRange"]');
        return dateSelect && userExperienceLevel === 'intermediate';
      },
      message: '📅 You\'re exploring different time periods! Learn about advanced date filtering and analysis techniques.',
      priority: 'medium',
      cooldown: 45,
      maxTriggers: 2
    },
    {
      id: 'progressive_disclosure_toggle',
      tutorialId: 'dashboard_advanced_tutorial',
      triggerType: 'interaction',
      targetElement: '[data-progressive-toggle]',
      condition: () => {
        const toggle = document.querySelector('[data-progressive-toggle]');
        return toggle && userExperienceLevel === 'intermediate';
      },
      message: '⚡ You found the advanced features toggle! Discover what other advanced features are available.',
      priority: 'high',
      cooldown: 30,
      maxTriggers: 1
    },
    {
      id: 'tooltip_freeze',
      tutorialId: 'dashboard_tutorial',
      triggerType: 'interaction',
      targetElement: '[data-tooltip-frozen]',
      condition: () => {
        const frozenTooltips = document.querySelectorAll('[data-tooltip-frozen]');
        return frozenTooltips.length > 0 && userExperienceLevel === 'beginner';
      },
      message: '🔍 Nice! You discovered frozen tooltips. Click chart elements to freeze tooltips for detailed analysis.',
      priority: 'medium',
      cooldown: 60,
      maxTriggers: 1
    },
    {
      id: 'help_button_click',
      tutorialId: 'features_tour',
      triggerType: 'interaction',
      targetElement: '[title*="help"]',
      condition: () => {
        return userExperienceLevel === 'beginner';
      },
      message: '❓ You\'re using the help system! Explore our comprehensive tutorial library to master all features.',
      priority: 'high',
      cooldown: 20,
      maxTriggers: 1
    },
    {
      id: 'metric_tooltip_hover',
      tutorialId: 'training_analysis_tutorial',
      triggerType: 'interaction',
      targetElement: '[data-metric-tooltip]',
      condition: () => {
        const metricTooltips = document.querySelectorAll('[data-metric-tooltip]');
        return metricTooltips.length > 0 && userExperienceLevel === 'intermediate';
      },
      message: '📊 You\'re exploring metric explanations! Learn about ACWR, TRIMP, and divergence analysis in detail.',
      priority: 'medium',
      cooldown: 45,
      maxTriggers: 2
    },
    {
      id: 'inactivity_trigger',
      tutorialId: 'dashboard_tutorial',
      triggerType: 'inactivity',
      condition: () => {
        return userExperienceLevel === 'beginner';
      },
      message: '🤔 Need help getting started? Take a quick tour of the dashboard features.',
      priority: 'low',
      cooldown: 10,
      maxTriggers: 1
    },
    {
      id: 'error_trigger',
      tutorialId: 'dashboard_tutorial',
      triggerType: 'error',
      condition: () => {
        // Check for common error states
        const errorElements = document.querySelectorAll('[data-error], .error, .alert-danger');
        return errorElements.length > 0 && userExperienceLevel === 'beginner';
      },
      message: '⚠️ Having trouble? Our tutorial can help you understand how to use the dashboard effectively.',
      priority: 'high',
      cooldown: 5,
      maxTriggers: 3
    }
  ];

  // Check if trigger should be shown based on cooldown and max triggers
  const shouldShowTrigger = useCallback((trigger: TutorialTrigger): boolean => {
    const history = triggerHistory.get(trigger.id);
    if (!history) return true;

    const now = new Date();
    const timeSinceLastShown = (now.getTime() - history.lastShown.getTime()) / (1000 * 60); // minutes

    if (trigger.cooldown && timeSinceLastShown < trigger.cooldown) {
      return false;
    }

    if (trigger.maxTriggers && history.count >= trigger.maxTriggers) {
      return false;
    }

    return true;
  }, [triggerHistory]);

  // Update trigger history
  const updateTriggerHistory = useCallback((triggerId: string) => {
    setTriggerHistory(prev => {
      const newHistory = new Map(prev);
      const existing = newHistory.get(triggerId);
      newHistory.set(triggerId, {
        count: existing ? existing.count + 1 : 1,
        lastShown: new Date()
      });
      return newHistory;
    });
  }, []);

  // Check for active triggers
  const checkTriggers = useCallback(() => {
    const activeTriggers = tutorialTriggers.filter(trigger => {
      if (!shouldShowTrigger(trigger)) return false;
      if (!trigger.condition()) return false;
      return true;
    });

    // Sort by priority (high > medium > low)
    const priorityOrder = { high: 3, medium: 2, low: 1 };
    activeTriggers.sort((a, b) => priorityOrder[b.priority] - priorityOrder[a.priority]);

    setActiveTriggers(activeTriggers);
  }, [tutorialTriggers, shouldShowTrigger]);

  // Show the highest priority trigger
  const showNextTrigger = useCallback(() => {
    if (activeTriggers.length > 0 && !showTrigger) {
      const nextTrigger = activeTriggers[0];
      setCurrentTrigger(nextTrigger);
      setShowTrigger(true);
      updateTriggerHistory(nextTrigger.id);
      onTriggerShown?.(nextTrigger.id);
    }
  }, [activeTriggers, showTrigger, updateTriggerHistory, onTriggerShown]);

  // Handle trigger dismissal
  const dismissTrigger = useCallback(() => {
    setShowTrigger(false);
    setCurrentTrigger(null);
  }, []);

  // Handle tutorial start from trigger
  const startTutorialFromTrigger = useCallback(() => {
    if (currentTrigger) {
      onStartTutorial(currentTrigger.tutorialId);
      dismissTrigger();
    }
  }, [currentTrigger, onStartTutorial, dismissTrigger]);

  // Set up event listeners for interaction-based triggers
  useEffect(() => {
    const handleInteraction = (event: Event) => {
      // Debounce trigger checking
      setTimeout(checkTriggers, 1000);
    };

    // Add event listeners for various interactions
    document.addEventListener('click', handleInteraction);
    document.addEventListener('mouseover', handleInteraction);
    document.addEventListener('change', handleInteraction);

    // Initial trigger check
    checkTriggers();

    return () => {
      document.removeEventListener('click', handleInteraction);
      document.removeEventListener('mouseover', handleInteraction);
      document.removeEventListener('change', handleInteraction);
    };
  }, [checkTriggers]);

  // Show triggers when they become available
  useEffect(() => {
    if (activeTriggers.length > 0 && !showTrigger) {
      // Delay showing trigger to avoid overwhelming the user
      const timer = setTimeout(showNextTrigger, 2000);
      return () => clearTimeout(timer);
    }
  }, [activeTriggers, showTrigger, showNextTrigger]);

  // Inactivity detection
  useEffect(() => {
    let inactivityTimer: NodeJS.Timeout;
    let lastActivity = Date.now();

    const resetTimer = () => {
      lastActivity = Date.now();
      clearTimeout(inactivityTimer);
      inactivityTimer = setTimeout(() => {
        const timeSinceActivity = (Date.now() - lastActivity) / (1000 * 60); // minutes
        if (timeSinceActivity > 5 && userExperienceLevel === 'beginner') {
          checkTriggers();
        }
      }, 5 * 60 * 1000); // 5 minutes
    };

    const handleActivity = () => {
      resetTimer();
    };

    document.addEventListener('mousemove', handleActivity);
    document.addEventListener('keypress', handleActivity);
    document.addEventListener('click', handleActivity);

    resetTimer();

    return () => {
      clearTimeout(inactivityTimer);
      document.removeEventListener('mousemove', handleActivity);
      document.removeEventListener('keypress', handleActivity);
      document.removeEventListener('click', handleActivity);
    };
  }, [checkTriggers, userExperienceLevel]);

  if (!showTrigger || !currentTrigger) {
    return null;
  }

  return (
    <div
      style={{
        position: 'fixed',
        bottom: '20px',
        right: '20px',
        backgroundColor: 'white',
        border: '1px solid #e5e7eb',
        borderRadius: '12px',
        boxShadow: '0 10px 25px rgba(0, 0, 0, 0.15)',
        padding: '1rem',
        maxWidth: '320px',
        zIndex: 1000,
        animation: 'slideInFromRight 0.3s ease-out'
      }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem' }}>
        <div style={{ flex: 1 }}>
          <p style={{ margin: 0, fontSize: '0.875rem', lineHeight: '1.4', color: '#374151' }}>
            {currentTrigger.message}
          </p>
        </div>
        <button
          onClick={dismissTrigger}
          style={{
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            padding: '0.25rem',
            borderRadius: '4px',
            color: '#6b7280',
            fontSize: '1rem',
            lineHeight: 1
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = '#f3f4f6';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = 'transparent';
          }}
        >
          ×
        </button>
      </div>
      
      <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.75rem' }}>
        <button
          onClick={startTutorialFromTrigger}
          style={{
            flex: 1,
            padding: '0.5rem 0.75rem',
            backgroundColor: '#3b82f6',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
            fontSize: '0.75rem',
            fontWeight: '500',
            transition: 'all 0.2s ease'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = '#2563eb';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = '#3b82f6';
          }}
        >
          Start Tutorial
        </button>
        <button
          onClick={dismissTrigger}
          style={{
            padding: '0.5rem 0.75rem',
            backgroundColor: 'transparent',
            color: '#6b7280',
            border: '1px solid #d1d5db',
            borderRadius: '6px',
            cursor: 'pointer',
            fontSize: '0.75rem',
            fontWeight: '500',
            transition: 'all 0.2s ease'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = '#f9fafb';
            e.currentTarget.style.borderColor = '#9ca3af';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = 'transparent';
            e.currentTarget.style.borderColor = '#d1d5db';
          }}
        >
          Maybe Later
        </button>
      </div>
    </div>
  );
};

export default ContextualTutorialTriggers;
