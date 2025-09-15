import React, { useState, useEffect } from 'react';

interface HelpOverlayProps {
  isOpen: boolean;
  onClose: () => void;
  context?: 'dashboard' | 'charts' | 'metrics' | 'general';
  title?: string;
  content?: React.ReactNode;
  onStartTutorial?: (tutorialId: string) => void;
}

interface Tutorial {
  tutorial_id: string;
  name: string;
  description: string;
  tutorial_type: string;
  estimated_duration: number;
  difficulty_level: string;
  category: string;
  completed: boolean;
}

interface HelpSection {
  id: string;
  title: string;
  content: React.ReactNode;
  icon: string;
}

const HelpOverlay: React.FC<HelpOverlayProps> = ({
  isOpen,
  onClose,
  context = 'general',
  title,
  content,
  onStartTutorial
}) => {
  const [tutorials, setTutorials] = useState<Tutorial[]>([]);
  const [recommendedTutorials, setRecommendedTutorials] = useState<Tutorial[]>([]);
  const [tutorialsByCategory, setTutorialsByCategory] = useState<Record<string, Tutorial[]>>({});
  const [isLoadingTutorials, setIsLoadingTutorials] = useState(false);
  const [activeTab, setActiveTab] = useState<'help' | 'tutorials'>('help');
  const [activeSection, setActiveSection] = useState<string>('overview');

  // Close overlay on Escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden'; // Prevent background scrolling
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onClose]);

  // Load tutorials when overlay opens
  useEffect(() => {
    if (isOpen && activeTab === 'tutorials') {
      loadTutorials();
    }
  }, [isOpen, activeTab]);

  const loadTutorials = async () => {
    setIsLoadingTutorials(true);
    try {
      const response = await fetch('/api/tutorials/available');
      const data = await response.json();
      
      if (data.success) {
        setTutorials(data.tutorials || []);
        setRecommendedTutorials(data.recommended || []);
        setTutorialsByCategory(data.by_category || {});
      }
    } catch (error) {
      console.error('Error loading tutorials:', error);
    } finally {
      setIsLoadingTutorials(false);
    }
  };

  // Help sections based on context
  const getHelpSections = (): HelpSection[] => {
    const baseSections: HelpSection[] = [
      {
        id: 'overview',
        title: 'Getting Started',
        icon: '🚀',
        content: (
          <div>
            <h3>Welcome to TrainingMonkey!</h3>
            <p>TrainingMonkey provides patent-pending training load divergence analysis to help you prevent injuries and optimize performance.</p>
            
            <div style={{ marginTop: '1rem' }}>
              <h4>Key Features:</h4>
              <ul style={{ paddingLeft: '1.5rem' }}>
                <li><strong>Divergence Analysis:</strong> Compare external vs. internal training load</li>
                <li><strong>Injury Prevention:</strong> Early warning signals for overtraining</li>
                <li><strong>AI Recommendations:</strong> Personalized training guidance</li>
                <li><strong>Performance Optimization:</strong> Data-driven insights for improvement</li>
              </ul>
            </div>

            {onStartTutorial && (
              <div style={{ marginTop: '1.5rem', padding: '1rem', backgroundColor: '#f0f9ff', borderRadius: '8px', border: '1px solid #0ea5e9' }}>
                <h4 style={{ margin: '0 0 0.5rem 0', color: '#0369a1' }}>🚀 Ready to Learn More?</h4>
                <p style={{ margin: '0 0 1rem 0', color: '#0c4a6e' }}>
                  Take our interactive welcome tour to get the most out of TrainingMonkey!
                </p>
                <button
                  onClick={() => onStartTutorial('welcome_tour')}
                  style={{
                    padding: '0.5rem 1rem',
                    backgroundColor: '#0ea5e9',
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    fontSize: '0.875rem',
                    fontWeight: '500',
                    transition: 'all 0.2s ease'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = '#0284c7';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = '#0ea5e9';
                  }}
                >
                  Start Welcome Tour
                </button>
              </div>
            )}
          </div>
        )
      },
      {
        id: 'charts',
        title: 'Understanding Charts',
        icon: '📊',
        content: (
          <div>
            <h3>Training Load Charts</h3>
            <p>Your dashboard shows several key metrics to track your training progress:</p>
            
            <div style={{ marginTop: '1rem' }}>
              <h4>Chart Types:</h4>
              <ul style={{ paddingLeft: '1.5rem' }}>
                <li><strong>Training Load:</strong> Your daily training volume and intensity</li>
                <li><strong>Divergence:</strong> The difference between external and internal load</li>
                <li><strong>ACWR (Acute:Chronic Workload Ratio):</strong> Risk assessment metric</li>
                <li><strong>TRIMP:</strong> Training impulse based on heart rate zones</li>
              </ul>
            </div>

            <div style={{ marginTop: '1rem', padding: '1rem', backgroundColor: '#f8f9fa', borderRadius: '8px' }}>
              <h4>💡 Pro Tip:</h4>
              <p>Look for patterns where your divergence line moves away from zero - this indicates potential overtraining or undertraining.</p>
            </div>

            {onStartTutorial && (
              <div style={{ marginTop: '1.5rem', padding: '1rem', backgroundColor: '#fef3c7', borderRadius: '8px', border: '1px solid #f59e0b' }}>
                <h4 style={{ margin: '0 0 0.5rem 0', color: '#92400e' }}>📊 Interactive Chart Tutorial</h4>
                <p style={{ margin: '0 0 1rem 0', color: '#78350f' }}>
                  Learn how to read and interpret your training charts with our guided tutorial!
                </p>
                <button
                  onClick={() => onStartTutorial('chart_reading_tutorial')}
                  style={{
                    padding: '0.5rem 1rem',
                    backgroundColor: '#f59e0b',
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    fontSize: '0.875rem',
                    fontWeight: '500',
                    transition: 'all 0.2s ease'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = '#d97706';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = '#f59e0b';
                  }}
                >
                  Start Chart Tutorial
                </button>
              </div>
            )}
          </div>
        )
      },
      {
        id: 'metrics',
        title: 'Key Metrics',
        icon: '📈',
        content: (
          <div>
            <h3>Understanding Your Metrics</h3>
            
            <div style={{ marginTop: '1rem' }}>
              <h4>External Load:</h4>
              <p>What you did - distance, elevation, duration, and intensity of your training.</p>
              
              <h4>Internal Load:</h4>
              <p>How your body responded - heart rate zones, perceived effort, and recovery indicators.</p>
              
              <h4>Divergence:</h4>
              <p>The difference between external and internal load. Positive divergence means your body is working harder than expected, negative means it's easier than expected.</p>
            </div>

            <div style={{ marginTop: '1rem', padding: '1rem', backgroundColor: '#fff3cd', borderRadius: '8px', border: '1px solid #ffeaa7' }}>
              <h4>⚠️ Warning Signs:</h4>
              <ul style={{ paddingLeft: '1.5rem', margin: 0 }}>
                <li>Consistently high positive divergence</li>
                <li>ACWR above 1.5 for extended periods</li>
                <li>Declining performance despite increased training</li>
              </ul>
            </div>
          </div>
        )
      },
      {
        id: 'recommendations',
        title: 'AI Recommendations',
        icon: '🤖',
        content: (
          <div>
            <h3>AI-Powered Training Guidance</h3>
            <p>Our AI analyzes your training patterns and provides personalized recommendations:</p>
            
            <div style={{ marginTop: '1rem' }}>
              <h4>Recommendation Types:</h4>
              <ul style={{ paddingLeft: '1.5rem' }}>
                <li><strong>Training Adjustments:</strong> Modify intensity or volume</li>
                <li><strong>Recovery Suggestions:</strong> When to rest or do easy training</li>
                <li><strong>Goal Optimization:</strong> Adjust targets based on progress</li>
                <li><strong>Injury Prevention:</strong> Early warning recommendations</li>
              </ul>
            </div>

            <div style={{ marginTop: '1rem', padding: '1rem', backgroundColor: '#d1ecf1', borderRadius: '8px', border: '1px solid #bee5eb' }}>
              <h4>💡 How It Works:</h4>
              <p>Our AI considers your training history, current fitness level, goals, and recovery patterns to provide the most relevant recommendations.</p>
            </div>
          </div>
        )
      }
    ];

    // Add context-specific sections
    if (context === 'dashboard') {
      baseSections.push({
        id: 'navigation',
        title: 'Dashboard Navigation',
        icon: '🧭',
        content: (
          <div>
            <h3>Getting Around Your Dashboard</h3>
            <p>Your dashboard is organized into several key areas:</p>
            
            <div style={{ marginTop: '1rem' }}>
              <h4>Main Sections:</h4>
              <ul style={{ paddingLeft: '1.5rem' }}>
                <li><strong>Training Charts:</strong> Visual analysis of your training data</li>
                <li><strong>Metrics Cards:</strong> Key performance indicators at a glance</li>
                <li><strong>AI Recommendations:</strong> Personalized training guidance</li>
                <li><strong>Time Period Controls:</strong> Adjust the date range for analysis</li>
              </ul>
            </div>
          </div>
        )
      });
    }

    return baseSections;
  };

  const helpSections = getHelpSections();

  if (!isOpen) return null;

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.5)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000,
        padding: '1rem'
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) {
          onClose();
        }
      }}
    >
      <div
        style={{
          backgroundColor: 'white',
          borderRadius: '12px',
          boxShadow: '0 20px 60px rgba(0, 0, 0, 0.3)',
          maxWidth: '800px',
          width: '100%',
          maxHeight: '90vh',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div
          style={{
            padding: '1.5rem',
            borderBottom: '1px solid #e5e7eb',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            backgroundColor: '#f8f9fa'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ fontSize: '1.5rem' }}>❓</span>
            <h2 style={{ margin: 0, fontSize: '1.25rem', fontWeight: '600', color: '#374151' }}>
              {title || 'Help Center'}
            </h2>
          </div>
          
          {/* Tabs */}
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button
              onClick={() => setActiveTab('help')}
              style={{
                padding: '0.5rem 1rem',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                backgroundColor: activeTab === 'help' ? '#3b82f6' : 'transparent',
                color: activeTab === 'help' ? 'white' : '#6b7280',
                fontSize: '0.875rem',
                fontWeight: '500',
                transition: 'all 0.2s ease'
              }}
            >
              Help
            </button>
            <button
              onClick={() => setActiveTab('tutorials')}
              style={{
                padding: '0.5rem 1rem',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                backgroundColor: activeTab === 'tutorials' ? '#3b82f6' : 'transparent',
                color: activeTab === 'tutorials' ? 'white' : '#6b7280',
                fontSize: '0.875rem',
                fontWeight: '500',
                transition: 'all 0.2s ease'
              }}
            >
              Tutorials
            </button>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              fontSize: '1.5rem',
              cursor: 'pointer',
              color: '#6b7280',
              padding: '0.25rem',
              borderRadius: '4px',
              transition: 'all 0.2s ease'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = '#e5e7eb';
              e.currentTarget.style.color = '#374151';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = 'transparent';
              e.currentTarget.style.color = '#6b7280';
            }}
          >
            ×
          </button>
        </div>

        {/* Content */}
        <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
          {/* Sidebar */}
          <div
            style={{
              width: '250px',
              borderRight: '1px solid #e5e7eb',
              backgroundColor: '#f8f9fa',
              overflowY: 'auto'
            }}
          >
            <div style={{ padding: '1rem' }}>
              <h3 style={{ margin: '0 0 1rem 0', fontSize: '1rem', fontWeight: '600', color: '#374151' }}>
                Help Topics
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                {helpSections.map((section) => (
                  <button
                    key={section.id}
                    onClick={() => setActiveSection(section.id)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.5rem',
                      padding: '0.75rem',
                      border: 'none',
                      borderRadius: '6px',
                      cursor: 'pointer',
                      backgroundColor: activeSection === section.id ? '#3b82f6' : 'transparent',
                      color: activeSection === section.id ? 'white' : '#374151',
                      textAlign: 'left',
                      fontSize: '0.875rem',
                      fontWeight: '500',
                      transition: 'all 0.2s ease',
                      width: '100%'
                    }}
                    onMouseEnter={(e) => {
                      if (activeSection !== section.id) {
                        e.currentTarget.style.backgroundColor = '#e5e7eb';
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (activeSection !== section.id) {
                        e.currentTarget.style.backgroundColor = 'transparent';
                      }
                    }}
                  >
                    <span style={{ fontSize: '1rem' }}>{section.icon}</span>
                    {section.title}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Main Content */}
          <div
            style={{
              flex: 1,
              padding: '1.5rem',
              overflowY: 'auto'
            }}
          >
            {activeTab === 'help' ? (
              content ? (
                content
              ) : (
              <div>
                {helpSections.find(section => section.id === activeSection)?.content}
              </div>
            )
            ) : (
              <div>
                {isLoadingTutorials ? (
                  <div style={{ textAlign: 'center', padding: '2rem' }}>
                    <div style={{ fontSize: '1.5rem', marginBottom: '1rem' }}>⏳</div>
                    <p>Loading tutorials...</p>
                  </div>
                ) : (
                  <div>
                    {/* Recently Completed Tutorials */}
                    {tutorials.filter(t => t.completed).length > 0 && (
                      <div style={{ marginBottom: '2rem' }}>
                        <h3 style={{ margin: '0 0 1rem 0', color: '#374151' }}>🔄 Recently Completed</h3>
                        <p style={{ margin: '0 0 1rem 0', color: '#6b7280', fontSize: '0.875rem' }}>
                          Replay these tutorials to refresh your knowledge or share with others.
                        </p>
                        <div style={{ display: 'grid', gap: '0.75rem' }}>
                          {tutorials.filter(t => t.completed).slice(0, 3).map((tutorial) => (
                            <div
                              key={tutorial.tutorial_id}
                              style={{
                                border: '1px solid #d1fae5',
                                borderRadius: '6px',
                                padding: '0.75rem',
                                backgroundColor: '#f0fdf4',
                                display: 'flex',
                                justifyContent: 'space-between',
                                alignItems: 'center'
                              }}
                            >
                              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                <span style={{ fontSize: '0.875rem', color: '#10b981' }}>✅</span>
                                <div>
                                  <h5 style={{ margin: 0, color: '#374151', fontSize: '0.875rem' }}>{tutorial.name}</h5>
                                  <p style={{ margin: 0, color: '#6b7280', fontSize: '0.75rem' }}>
                                    Completed • {Math.round(tutorial.estimated_duration / 60)} min
                                  </p>
                                </div>
                              </div>
                              {onStartTutorial && (
                                <button
                                  onClick={() => onStartTutorial(tutorial.tutorial_id)}
                                  style={{
                                    padding: '0.375rem 0.75rem',
                                    backgroundColor: '#10b981',
                                    color: 'white',
                                    border: 'none',
                                    borderRadius: '4px',
                                    cursor: 'pointer',
                                    fontSize: '0.75rem',
                                    fontWeight: '500'
                                  }}
                                >
                                  Replay
                                </button>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Recommended Tutorials */}
                    {recommendedTutorials.length > 0 && (
                      <div style={{ marginBottom: '2rem' }}>
                        <h3 style={{ margin: '0 0 1rem 0', color: '#374151' }}>🌟 Recommended for You</h3>
                        <div style={{ display: 'grid', gap: '1rem' }}>
                          {recommendedTutorials.map((tutorial) => (
                            <div
                              key={tutorial.tutorial_id}
                              style={{
                                border: '1px solid #e5e7eb',
                                borderRadius: '8px',
                                padding: '1rem',
                                backgroundColor: '#f8f9fa'
                              }}
                            >
                              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
                                <h4 style={{ margin: 0, color: '#374151' }}>{tutorial.name}</h4>
                                <span style={{ 
                                  fontSize: '0.75rem', 
                                  padding: '0.25rem 0.5rem', 
                                  borderRadius: '4px',
                                  backgroundColor: tutorial.difficulty_level === 'beginner' ? '#d1ecf1' : 
                                                  tutorial.difficulty_level === 'intermediate' ? '#fff3cd' : '#f8d7da',
                                  color: tutorial.difficulty_level === 'beginner' ? '#0c5460' : 
                                         tutorial.difficulty_level === 'intermediate' ? '#856404' : '#721c24'
                                }}>
                                  {tutorial.difficulty_level}
                                </span>
                              </div>
                              <p style={{ margin: '0 0 1rem 0', color: '#6b7280', fontSize: '0.875rem' }}>
                                {tutorial.description}
                              </p>
                              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <span style={{ fontSize: '0.75rem', color: '#9ca3af' }}>
                                  ⏱️ {Math.round(tutorial.estimated_duration / 60)} min
                                </span>
                                {onStartTutorial && (
                                  <button
                                    onClick={() => onStartTutorial(tutorial.tutorial_id)}
                                    style={{
                                      padding: '0.5rem 1rem',
                                      backgroundColor: '#3b82f6',
                                      color: 'white',
                                      border: 'none',
                                      borderRadius: '6px',
                                      cursor: 'pointer',
                                      fontSize: '0.875rem',
                                      fontWeight: '500'
                                    }}
                                  >
                                    Start Tutorial
                                  </button>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* All Tutorials by Category */}
                    <div>
                      <h3 style={{ margin: '0 0 1rem 0', color: '#374151' }}>📚 All Tutorials</h3>
                      {Object.entries(tutorialsByCategory).map(([category, categoryTutorials]) => (
                        <div key={category} style={{ marginBottom: '2rem' }}>
                          <h4 style={{ 
                            margin: '0 0 1rem 0', 
                            color: '#374151',
                            textTransform: 'capitalize',
                            fontSize: '1rem'
                          }}>
                            {category.replace('_', ' ')}
                          </h4>
                          <div style={{ display: 'grid', gap: '0.75rem' }}>
                            {categoryTutorials.map((tutorial) => (
                              <div
                                key={tutorial.tutorial_id}
                                style={{
                                  border: '1px solid #e5e7eb',
                                  borderRadius: '6px',
                                  padding: '0.75rem',
                                  backgroundColor: 'white',
                                  display: 'flex',
                                  justifyContent: 'space-between',
                                  alignItems: 'center'
                                }}
                              >
                                <div style={{ flex: 1 }}>
                                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                                    <h5 style={{ margin: 0, color: '#374151', fontSize: '0.875rem' }}>{tutorial.name}</h5>
                                    {tutorial.completed && (
                                      <span style={{ fontSize: '0.75rem', color: '#10b981' }}>✅</span>
                                    )}
                                  </div>
                                  <p style={{ margin: 0, color: '#6b7280', fontSize: '0.75rem' }}>
                                    {tutorial.description}
                                  </p>
                                  <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem' }}>
                                    <span style={{ 
                                      fontSize: '0.625rem', 
                                      padding: '0.125rem 0.375rem', 
                                      borderRadius: '3px',
                                      backgroundColor: tutorial.difficulty_level === 'beginner' ? '#d1ecf1' : 
                                                      tutorial.difficulty_level === 'intermediate' ? '#fff3cd' : '#f8d7da',
                                      color: tutorial.difficulty_level === 'beginner' ? '#0c5460' : 
                                             tutorial.difficulty_level === 'intermediate' ? '#856404' : '#721c24'
                                    }}>
                                      {tutorial.difficulty_level}
                                    </span>
                                    <span style={{ fontSize: '0.625rem', color: '#9ca3af' }}>
                                      ⏱️ {Math.round(tutorial.estimated_duration / 60)} min
                                    </span>
                                  </div>
                                </div>
                                {onStartTutorial && (
                                  <button
                                    onClick={() => onStartTutorial(tutorial.tutorial_id)}
                                    style={{
                                      padding: '0.375rem 0.75rem',
                                      backgroundColor: tutorial.completed ? '#10b981' : '#3b82f6',
                                      color: 'white',
                                      border: 'none',
                                      borderRadius: '4px',
                                      cursor: 'pointer',
                                      fontSize: '0.75rem',
                                      fontWeight: '500',
                                      marginLeft: '1rem'
                                    }}
                                  >
                                    {tutorial.completed ? 'Replay' : 'Start'}
                                  </button>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div
          style={{
            padding: '1rem 1.5rem',
            borderTop: '1px solid #e5e7eb',
            backgroundColor: '#f8f9fa',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}
        >
          <div style={{ fontSize: '0.875rem', color: '#6b7280' }}>
            Need more help? Visit our{' '}
            <a
              href="/getting-started?source=dashboard"
              target="_blank"
              rel="noopener noreferrer"
              style={{ color: '#3b82f6', textDecoration: 'none' }}
            >
              Getting Started Guide
            </a>
          </div>
          <button
            onClick={onClose}
            style={{
              padding: '0.5rem 1rem',
              backgroundColor: '#3b82f6',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '0.875rem',
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
            Got it!
          </button>
        </div>
      </div>
    </div>
  );
};

export default HelpOverlay;
