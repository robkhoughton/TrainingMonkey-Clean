/**
 * Getting Started Resources Page JavaScript
 * Interactive functionality and smooth animations
 */

// Global configuration
const CONFIG = {
    animationDuration: 300,
    scrollOffset: 100,
    debounceDelay: 250
};

// Utility functions
const Utils = {
    /**
     * Debounce function to limit function calls
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    /**
     * Smooth scroll to element
     */
    smoothScrollTo(element, offset = CONFIG.scrollOffset) {
        const elementPosition = element.offsetTop - offset;
        window.scrollTo({
            top: elementPosition,
            behavior: 'smooth'
        });
    },

    /**
     * Check if element is in viewport
     */
    isInViewport(element) {
        const rect = element.getBoundingClientRect();
        return (
            rect.top >= 0 &&
            rect.left >= 0 &&
            rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
            rect.right <= (window.innerWidth || document.documentElement.clientWidth)
        );
    },

    /**
     * Add CSS class with animation
     */
    addClassWithAnimation(element, className, duration = CONFIG.animationDuration) {
        element.classList.add(className);
        setTimeout(() => {
            element.style.transition = `all ${duration}ms ease`;
        }, 10);
    },

    /**
     * Remove CSS class with animation
     */
    removeClassWithAnimation(element, className, duration = CONFIG.animationDuration) {
        element.style.transition = `all ${duration}ms ease`;
        element.classList.remove(className);
    }
};

// FAQ Management
const FAQManager = {
    /**
     * Toggle FAQ item
     */
    toggleFAQ(element) {
        const answer = element.nextElementSibling;
        const toggle = element.querySelector('.faq-toggle');
        
        if (answer.classList.contains('expanded')) {
            this.collapseFAQ(answer, toggle);
        } else {
            this.expandFAQ(answer, toggle);
        }
    },

    /**
     * Expand FAQ item
     */
    expandFAQ(answer, toggle) {
        answer.classList.add('expanded');
        toggle.classList.add('expanded');
        toggle.textContent = '−';
        
        // Track FAQ expansion
        const questionText = answer.parentElement.querySelector('.faq-question').textContent.trim();
        EngagementTracker.trackFAQExpansion(questionText);
    },

    /**
     * Collapse FAQ item
     */
    collapseFAQ(answer, toggle) {
        answer.classList.remove('expanded');
        toggle.classList.remove('expanded');
        toggle.textContent = '+';
    },

    /**
     * Initialize FAQ functionality
     */
    init() {
        const faqQuestions = document.querySelectorAll('.faq-question');
        faqQuestions.forEach(question => {
            question.addEventListener('click', () => this.toggleFAQ(question));
            
            // Add keyboard support
            question.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    this.toggleFAQ(question);
                }
            });
        });
    }
};

// Contextual Content Manager
const ContextualManager = {
    /**
     * Update contextual content based on source
     */
    updateContextualContent() {
        const urlParams = new URLSearchParams(window.location.search);
        const source = urlParams.get('source');
        const banner = document.getElementById('contextual-banner');
        const title = document.getElementById('contextual-title');
        const message = document.getElementById('contextual-message');

        if (!banner || !title || !message) return;

        const contextualData = {
            landing: {
                title: 'Welcome from our landing page!',
                message: 'You\'re about to discover how TrainingMonkey can transform your training analysis.'
            },
            onboarding: {
                title: 'Need help getting started?',
                message: 'We\'re here to guide you through the setup process and answer any questions.'
            },
            dashboard: {
                title: 'New to TrainingMonkey?',
                message: 'Let us show you how to make the most of your training analysis dashboard.'
            }
        };

        if (source && contextualData[source]) {
            title.textContent = contextualData[source].title;
            message.textContent = contextualData[source].message;
            Utils.addClassWithAnimation(banner, 'show');
        }
    },

    /**
     * Initialize contextual content
     */
    init() {
        this.updateContextualContent();
    }
};

// Tutorial Integration Manager
const TutorialManager = {
    /**
     * Start tutorial
     */
    async startTutorial(tutorialId) {
        try {
            // Check if user is authenticated (this will be handled by the template)
            const isAuthenticated = document.body.dataset.userAuthenticated === 'true';
            
            if (!isAuthenticated) {
                this.showLoginPrompt();
                return;
            }

            // Show loading state
            this.showLoadingState(tutorialId);

            const response = await fetch('/api/start-tutorial', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    tutorial_id: tutorialId
                })
            });

            const data = await response.json();

            if (data.success) {
                // Track tutorial start
                this.trackTutorialStart(tutorialId);
                
                // Redirect to dashboard with tutorial active
                window.location.href = `/dashboard?tutorial=${tutorialId}`;
            } else {
                this.showError('Unable to start tutorial: ' + (data.error || 'Unknown error'));
            }
        } catch (error) {
            console.error('Error starting tutorial:', error);
            this.showError('Unable to start tutorial. Please try again.');
        }
    },

    /**
     * Show loading state for tutorial
     */
    showLoadingState(tutorialId) {
        const tutorialLinks = document.querySelectorAll(`[onclick*="${tutorialId}"]`);
        tutorialLinks.forEach(link => {
            link.style.opacity = '0.6';
            link.style.pointerEvents = 'none';
            link.textContent = 'Starting...';
        });
    },

    /**
     * Show login prompt
     */
    showLoginPrompt() {
        if (confirm('Please log in to access tutorials. Would you like to go to the login page?')) {
            window.location.href = '/auth/strava-signup';
        }
    },

    /**
     * Show error message
     */
    showError(message) {
        // Create error notification
        const notification = document.createElement('div');
        notification.className = 'error-notification';
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #ef4444;
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            z-index: 1000;
            animation: slideInRight 0.3s ease;
        `;

        document.body.appendChild(notification);

        // Remove notification after 5 seconds
        setTimeout(() => {
            notification.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, 5000);
    },

    /**
     * Track tutorial start
     */
    trackTutorialStart(tutorialId) {
        // Send analytics event
        if (typeof gtag !== 'undefined') {
            gtag('event', 'tutorial_started', {
                'tutorial_id': tutorialId,
                'page': 'getting_started'
            });
        }
    },

    /**
     * Get CSRF token
     */
    getCSRFToken() {
        const token = document.querySelector('meta[name="csrf-token"]');
        return token ? token.getAttribute('content') : '';
    },

    /**
     * Load tutorial completion status and update UI
     */
    async loadTutorialStatus() {
        try {
            // Only load tutorial status if user is logged in
            const response = await fetch('/api/tutorials/available');
            
            if (response.ok) {
                const data = await response.json();
                
                if (data.success) {
                    const completedTutorials = data.tutorials.filter(tutorial => tutorial.completed);
                    this.updateTutorialLinks(completedTutorials);
                }
            } else if (response.status === 401) {
                // User not logged in - this is expected on getting started page
                console.log('User not logged in - skipping tutorial status');
            } else {
                console.warn('Failed to load tutorial status:', response.status);
            }
        } catch (error) {
            console.warn('Could not load tutorial status:', error);
        }
    },

    /**
     * Update tutorial links to show replay options for completed tutorials
     */
    updateTutorialLinks(completedTutorials) {
        const tutorialLinks = document.querySelectorAll('.tutorial-link');
        tutorialLinks.forEach(link => {
            const tutorialId = link.getAttribute('data-tutorial-id');
            const isCompleted = completedTutorials.some(tutorial => tutorial.tutorial_id === tutorialId);
            
            if (isCompleted) {
                // Add replay indicator
                link.style.position = 'relative';
                link.innerHTML = `
                    <span style="color: #10b981; margin-right: 0.5rem;">✅</span>
                    ${link.textContent}
                    <span style="color: #10b981; margin-left: 0.5rem; font-size: 0.8em;">(Replay)</span>
                `;
                link.style.color = '#10b981';
                link.style.fontWeight = '500';
            }
        });
    },

    /**
     * Initialize tutorial functionality
     */
    init() {
        // Load tutorial completion status first
        this.loadTutorialStatus();
        
        // Add click handlers for tutorial links
        const tutorialLinks = document.querySelectorAll('.tutorial-link');
        tutorialLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const tutorialId = link.getAttribute('data-tutorial-id') || 
                                 link.textContent.toLowerCase().replace(/\s+/g, '_');
                
                // Track tutorial click
                EngagementTracker.trackTutorialClick(tutorialId);
                
                this.startTutorial(tutorialId);
            });
        });
    }
};

// Animation Manager
const AnimationManager = {
    /**
     * Initialize scroll animations
     */
    initScrollAnimations() {
        const animatedElements = document.querySelectorAll('.benefit-card, .timeline-step, .tutorial-category, .ai-recommendation-card, .explanation-card, .timeline-explanation, .science-explanation, .goal-card, .goals-connection-explanation, .goals-cta');
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    Utils.addClassWithAnimation(entry.target, 'animate-in');
                    
                    // Add staggered animations for timeline steps
                    if (entry.target.classList.contains('timeline-step')) {
                        const steps = document.querySelectorAll('.timeline-step');
                        const index = Array.from(steps).indexOf(entry.target);
                        setTimeout(() => {
                            entry.target.style.animation = `fadeInLeft 0.6s ease-out forwards`;
                        }, index * 200);
                    }
                    
                    // Add staggered animations for benefit cards
                    if (entry.target.classList.contains('benefit-card')) {
                        const cards = document.querySelectorAll('.benefit-card');
                        const index = Array.from(cards).indexOf(entry.target);
                        setTimeout(() => {
                            entry.target.style.animation = `fadeInUp 0.6s ease-out forwards`;
                        }, index * 150);
                    }
                }
            });
        }, {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        });

        animatedElements.forEach(element => {
            observer.observe(element);
        });
    },

    /**
     * Initialize hover animations
     */
    initHoverAnimations() {
        const hoverElements = document.querySelectorAll('.benefit-card, .tutorial-link, .btn');
        
        hoverElements.forEach(element => {
            element.addEventListener('mouseenter', () => {
                Utils.addClassWithAnimation(element, 'hover-active');
            });
            
            element.addEventListener('mouseleave', () => {
                Utils.removeClassWithAnimation(element, 'hover-active');
            });
        });
    },

    /**
     * Initialize page load animations
     */
    initPageLoadAnimations() {
        // Staggered animation for benefit cards
        const benefitCards = document.querySelectorAll('.benefit-card');
        benefitCards.forEach((card, index) => {
            setTimeout(() => {
                Utils.addClassWithAnimation(card, 'fade-in-up');
            }, index * 100);
        });

        // Staggered animation for setup steps
        const setupSteps = document.querySelectorAll('.setup-step');
        setupSteps.forEach((step, index) => {
            setTimeout(() => {
                Utils.addClassWithAnimation(step, 'fade-in-up');
            }, (index * 150) + 300);
        });
    },

    /**
     * Initialize all animations
     */
    init() {
        this.initScrollAnimations();
        this.initHoverAnimations();
        this.initPageLoadAnimations();
    }
};

// Navigation Manager
const NavigationManager = {
    /**
     * Initialize smooth scrolling for navigation links
     */
    initSmoothScrolling() {
        const navLinks = document.querySelectorAll('a[href^="#"]');
        
        navLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const targetId = link.getAttribute('href').substring(1);
                const targetElement = document.getElementById(targetId);
                
                if (targetElement) {
                    Utils.smoothScrollTo(targetElement);
                }
            });
        });
    },

    /**
     * Initialize navigation
     */
    init() {
        this.initSmoothScrolling();
    }
};

// Engagement Tracking Manager
const EngagementTracker = {
    // Engagement metrics
    metrics: {
        pageLoadTime: 0,
        timeOnPage: 0,
        scrollDepth: 0,
        maxScrollDepth: 0,
        sectionsViewed: new Set(),
        interactions: 0,
        demoInteractions: 0,
        tutorialClicks: 0,
        faqExpansions: 0,
        startTime: Date.now(),
        lastActivity: Date.now()
    },

    /**
     * Track page load time
     */
    trackPageLoad() {
        this.metrics.pageLoadTime = Date.now() - this.metrics.startTime;
        this.trackEngagementEvent('page_load', {
            load_time: this.metrics.pageLoadTime,
            source: this.getSourceFromURL()
        });
    },

    /**
     * Track scroll depth
     */
    trackScrollDepth() {
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        const documentHeight = document.documentElement.scrollHeight - window.innerHeight;
        const scrollPercent = Math.round((scrollTop / documentHeight) * 100);
        
        if (scrollPercent > this.metrics.maxScrollDepth) {
            this.metrics.maxScrollDepth = scrollPercent;
            
            // Track milestone scroll depths
            if (scrollPercent >= 25 && !this.metrics.sectionsViewed.has('25%')) {
                this.metrics.sectionsViewed.add('25%');
                this.trackEngagementEvent('scroll_milestone', { depth: 25 });
            }
            if (scrollPercent >= 50 && !this.metrics.sectionsViewed.has('50%')) {
                this.metrics.sectionsViewed.add('50%');
                this.trackEngagementEvent('scroll_milestone', { depth: 50 });
            }
            if (scrollPercent >= 75 && !this.metrics.sectionsViewed.has('75%')) {
                this.metrics.sectionsViewed.add('75%');
                this.trackEngagementEvent('scroll_milestone', { depth: 75 });
            }
            if (scrollPercent >= 90 && !this.metrics.sectionsViewed.has('90%')) {
                this.metrics.sectionsViewed.add('90%');
                this.trackEngagementEvent('scroll_milestone', { depth: 90 });
            }
        }
    },

    /**
     * Track section views
     */
    trackSectionView(sectionName) {
        if (!this.metrics.sectionsViewed.has(sectionName)) {
            this.metrics.sectionsViewed.add(sectionName);
            this.trackEngagementEvent('section_view', { section: sectionName });
        }
    },

    /**
     * Track user interactions
     */
    trackInteraction(type, data = {}) {
        this.metrics.interactions++;
        this.metrics.lastActivity = Date.now();
        
        this.trackEngagementEvent('interaction', {
            type: type,
            total_interactions: this.metrics.interactions,
            ...data
        });
    },

    /**
     * Track demo interactions
     */
    trackDemoInteraction(scenario) {
        this.metrics.demoInteractions++;
        this.trackEngagementEvent('demo_interaction', {
            scenario: scenario,
            total_demo_interactions: this.metrics.demoInteractions
        });
    },

    /**
     * Track tutorial clicks
     */
    trackTutorialClick(tutorialId) {
        this.metrics.tutorialClicks++;
        this.trackEngagementEvent('tutorial_click', {
            tutorial_id: tutorialId,
            total_tutorial_clicks: this.metrics.tutorialClicks
        });
    },

    /**
     * Track FAQ expansions
     */
    trackFAQExpansion(question) {
        this.metrics.faqExpansions++;
        this.trackEngagementEvent('faq_expansion', {
            question: question,
            total_faq_expansions: this.metrics.faqExpansions
        });
    },

    /**
     * Track time on page
     */
    trackTimeOnPage() {
        this.metrics.timeOnPage = Date.now() - this.metrics.startTime;
        
        // Track time milestones
        const minutes = Math.floor(this.metrics.timeOnPage / 60000);
        if (minutes >= 1 && !this.metrics.sectionsViewed.has('1min')) {
            this.metrics.sectionsViewed.add('1min');
            this.trackEngagementEvent('time_milestone', { minutes: 1 });
        }
        if (minutes >= 3 && !this.metrics.sectionsViewed.has('3min')) {
            this.metrics.sectionsViewed.add('3min');
            this.trackEngagementEvent('time_milestone', { minutes: 3 });
        }
        if (minutes >= 5 && !this.metrics.sectionsViewed.has('5min')) {
            this.metrics.sectionsViewed.add('5min');
            this.trackEngagementEvent('time_milestone', { minutes: 5 });
        }
    },

    /**
     * Track engagement event
     */
    trackEngagementEvent(eventType, eventData) {
        fetch('/api/landing/analytics', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                event_type: 'getting_started_engagement',
                event_data: {
                    event_subtype: eventType,
                    source: this.getSourceFromURL(),
                    timestamp: new Date().toISOString(),
                    ...eventData
                }
            })
        }).catch(e => console.log('Engagement tracking failed:', e));
    },

    /**
     * Get source from URL parameters
     */
    getSourceFromURL() {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get('source') || 'direct';
    },

    /**
     * Track page exit
     */
    trackPageExit() {
        this.metrics.timeOnPage = Date.now() - this.metrics.startTime;
        
        this.trackEngagementEvent('page_exit', {
            time_on_page: this.metrics.timeOnPage,
            max_scroll_depth: this.metrics.maxScrollDepth,
            total_interactions: this.metrics.interactions,
            demo_interactions: this.metrics.demoInteractions,
            tutorial_clicks: this.metrics.tutorialClicks,
            faq_expansions: this.metrics.faqExpansions,
            sections_viewed: Array.from(this.metrics.sectionsViewed)
        });
    },

    /**
     * Initialize engagement tracking
     */
    init() {
        // Track page load
        this.trackPageLoad();
        
        // Track scroll depth
        const debouncedScrollTrack = Utils.debounce(() => this.trackScrollDepth(), 100);
        window.addEventListener('scroll', debouncedScrollTrack);
        
        // Track time on page
        const timeTracker = setInterval(() => this.trackTimeOnPage(), 30000); // Every 30 seconds
        
        // Track page exit
        window.addEventListener('beforeunload', () => this.trackPageExit());
        
        // Track visibility changes
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.trackEngagementEvent('page_hidden', {
                    time_on_page: Date.now() - this.metrics.startTime
                });
            } else {
                this.trackEngagementEvent('page_visible', {
                    time_on_page: Date.now() - this.metrics.startTime
                });
            }
        });
        
        // Track section views using Intersection Observer
        this.setupSectionTracking();
        
        console.log('Engagement tracking initialized');
    },

    /**
     * Setup section tracking with Intersection Observer
     */
    setupSectionTracking() {
        const sections = document.querySelectorAll('section, .section, [data-section]');
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const sectionName = entry.target.getAttribute('data-section') || 
                                      entry.target.className || 
                                      entry.target.tagName.toLowerCase();
                    this.trackSectionView(sectionName);
                }
            });
        }, { threshold: 0.5 });
        
        sections.forEach(section => observer.observe(section));
    }
};

// Performance Manager
const PerformanceManager = {
    /**
     * Initialize performance optimizations
     */
    init() {
        // Lazy load images
        this.initLazyLoading();
        
        // Preload critical resources
        this.preloadCriticalResources();
        
        // Optimize scroll performance
        this.optimizeScrollPerformance();
    },

    /**
     * Initialize lazy loading for images
     */
    initLazyLoading() {
        const images = document.querySelectorAll('img[data-src]');
        
        const imageObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.classList.remove('lazy');
                    imageObserver.unobserve(img);
                }
            });
        });

        images.forEach(img => imageObserver.observe(img));
    },

    /**
     * Preload critical resources
     */
    preloadCriticalResources() {
        // Preload CSS for next page - only if dashboard.css exists
        // Note: dashboard.css doesn't exist yet, so skipping preload
        // TODO: Create dashboard.css or remove this preload
    },

    /**
     * Optimize scroll performance
     */
    optimizeScrollPerformance() {
        let ticking = false;
        
        const updateScrollPosition = Utils.debounce(() => {
            // Update any scroll-dependent elements
            const nav = document.querySelector('.nav');
            if (nav) {
                if (window.scrollY > 100) {
                    nav.classList.add('scrolled');
                } else {
                    nav.classList.remove('scrolled');
                }
            }
            ticking = false;
        }, CONFIG.debounceDelay);

        window.addEventListener('scroll', () => {
            if (!ticking) {
                requestAnimationFrame(updateScrollPosition);
                ticking = true;
            }
        });
    }
};

// Interactive Demo Manager
const InteractiveDemoManager = {
    /**
     * Demo scenarios configuration with enhanced data
     */
    scenarios: {
        'sweet-spot': {
            position: 50,
            status: 'Sweet Spot',
            color: 'status-sweet-spot',
            description: 'Perfect balance - train with confidence',
            externalLoad: 0.85,
            internalLoad: 0.82,
            divergence: 0.03,
            recommendation: 'Continue current training intensity',
            riskLevel: 'Low',
            aiRecommendation: {
                type: 'Training Decision',
                text: 'Continue current training intensity. Your external and internal loads are well-balanced, indicating optimal training adaptation. Maintain your current pace and intensity for the next 3-5 days.',
                confidence: 92,
                riskLevel: 'Low',
                nextCheck: 'Tomorrow',
                explanation: 'This recommendation is based on your current training load divergence analysis. When external and internal loads are balanced, it indicates your body is adapting well to training stress.'
            }
        },
        'overreaching': {
            position: 25,
            status: 'Caution',
            color: 'status-risk',
            description: 'External load too high - consider easier training',
            externalLoad: 1.15,
            internalLoad: 0.95,
            divergence: -0.20,
            recommendation: 'Reduce training intensity by 20%',
            riskLevel: 'Medium',
            aiRecommendation: {
                type: 'Caution Alert',
                text: 'Reduce training intensity by 20%. Your external load is significantly higher than your internal response, indicating potential overreaching. Consider easier training or additional recovery.',
                confidence: 88,
                riskLevel: 'Medium',
                nextCheck: 'In 2 hours',
                explanation: 'When external load exceeds internal load by this margin, it suggests your body is struggling to adapt to the training stress. This is a warning sign of potential overtraining.'
            }
        },
        'undertrained': {
            position: 75,
            status: 'Recovery Phase',
            color: 'status-sweet-spot',
            description: 'Good recovery - ready for harder training',
            externalLoad: 0.65,
            internalLoad: 0.70,
            divergence: 0.05,
            recommendation: 'Gradually increase training load',
            riskLevel: 'Low',
            aiRecommendation: {
                type: 'Recovery Complete',
                text: 'Gradually increase training load. Your recovery phase is complete and your body is ready for more challenging training. Start with 10-15% intensity increase.',
                confidence: 85,
                riskLevel: 'Low',
                nextCheck: 'After next session',
                explanation: 'When internal load slightly exceeds external load, it indicates good recovery and adaptation. Your body is ready to handle increased training stress.'
            }
        },
        'high-risk': {
            position: 15,
            status: 'High Risk',
            color: 'status-risk',
            description: 'Dangerous imbalance - rest recommended',
            externalLoad: 1.25,
            internalLoad: 0.85,
            divergence: -0.40,
            recommendation: 'Take 2-3 days complete rest',
            riskLevel: 'High',
            aiRecommendation: {
                type: 'High Risk Alert',
                text: 'Take 2-3 days complete rest immediately. Your training load divergence indicates severe overtraining risk. Any additional training could lead to injury or burnout.',
                confidence: 95,
                riskLevel: 'High',
                nextCheck: 'In 3 days',
                explanation: 'This level of divergence between external and internal loads is a strong indicator of overtraining syndrome. Immediate rest is essential to prevent injury and allow recovery.'
            }
        }
    },

    /**
     * Show a specific scenario with enhanced feedback
     */
    showScenario(scenarioKey) {
        const scenario = this.scenarios[scenarioKey];
        if (!scenario) return;

        const line = document.getElementById('divergenceLine');
        const point = document.getElementById('divergencePoint');
        const indicator = document.getElementById('statusIndicator');
        const buttons = document.querySelectorAll('.demo-btn');

        if (!line || !point || !indicator) return;

        // Update position with smooth animation
        line.style.left = scenario.position + '%';
        point.style.left = scenario.position + '%';

        // Update status with enhanced information
        indicator.className = `status-indicator ${scenario.color}`;
        indicator.innerHTML = `<span>●</span> ${scenario.status}`;

        // Update active button
        buttons.forEach(btn => btn.classList.remove('active'));
        const activeButton = Array.from(buttons).find(btn => 
            btn.textContent.toLowerCase().includes(scenarioKey.replace('-', ' ')) ||
            btn.onclick?.toString().includes(scenarioKey)
        );
        if (activeButton) {
            activeButton.classList.add('active');
        }

        // Update scenario description if element exists
        const descriptionElement = document.getElementById('scenarioDescription');
        if (descriptionElement) {
            descriptionElement.textContent = scenario.description;
        }

        // Update recommendation if element exists
        const recommendationElement = document.getElementById('scenarioRecommendation');
        if (recommendationElement) {
            recommendationElement.textContent = scenario.recommendation;
        }

        // Update metrics if elements exist
        const externalLoadElement = document.getElementById('externalLoadValue');
        const internalLoadElement = document.getElementById('internalLoadValue');
        const divergenceElement = document.getElementById('divergenceValue');
        
        if (externalLoadElement) externalLoadElement.textContent = scenario.externalLoad.toFixed(2);
        if (internalLoadElement) internalLoadElement.textContent = scenario.internalLoad.toFixed(2);
        if (divergenceElement) divergenceElement.textContent = scenario.divergence.toFixed(2);

        // Update AI recommendation display
        this.updateAIRecommendation(scenario.aiRecommendation);

        // Track analytics
        this.trackDemoInteraction(scenarioKey);
    },

    /**
     * Update AI recommendation display
     */
    updateAIRecommendation(aiRec) {
        if (!aiRec) return;

        const typeElement = document.getElementById('recommendationType');
        const textElement = document.getElementById('recommendationText');
        const confidenceElement = document.getElementById('confidenceValue');
        const riskElement = document.getElementById('riskLevelValue');
        const nextCheckElement = document.getElementById('nextCheckValue');

        if (typeElement) typeElement.textContent = aiRec.type;
        if (textElement) textElement.innerHTML = `<strong>${aiRec.text.split('.')[0]}.</strong> ${aiRec.text.split('.').slice(1).join('.').trim()}`;
        if (confidenceElement) confidenceElement.textContent = aiRec.confidence + '%';
        if (riskElement) riskElement.textContent = aiRec.riskLevel;
        if (nextCheckElement) nextCheckElement.textContent = aiRec.nextCheck;

        // Update risk level color
        if (riskElement) {
            riskElement.className = 'detail-value';
            if (aiRec.riskLevel === 'High') {
                riskElement.style.color = '#dc2626';
            } else if (aiRec.riskLevel === 'Medium') {
                riskElement.style.color = '#d97706';
            } else {
                riskElement.style.color = '#059669';
            }
        }
    },

    /**
     * Track demo interaction
     */
    trackDemoInteraction(scenario) {
        // Track with engagement tracker
        EngagementTracker.trackDemoInteraction(scenario);
        
        // Also track with legacy analytics
        fetch('/api/landing/analytics', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                event_type: 'demo_interaction',
                event_data: {
                    scenario: scenario,
                    page: 'getting_started',
                    timestamp: new Date().toISOString()
                }
            })
        }).catch(e => console.log('Analytics tracking failed:', e));
    },

    /**
     * Initialize auto-cycling
     */
    initAutoCycle() {
        let currentScenario = 0;
        const scenarioKeys = Object.keys(this.scenarios);
        let autoCycleInterval;

        const startAutoCycle = () => {
            autoCycleInterval = setInterval(() => {
                currentScenario = (currentScenario + 1) % scenarioKeys.length;
                const buttons = document.querySelectorAll('.demo-btn');

                if (buttons.length > 0) {
                    buttons.forEach(btn => btn.classList.remove('active'));
                    if (buttons[currentScenario]) {
                        buttons[currentScenario].classList.add('active');
                    }
                    this.showScenario(scenarioKeys[currentScenario]);
                }
            }, 4000); // Change every 4 seconds
        };

        const stopAutoCycle = () => {
            if (autoCycleInterval) {
                clearInterval(autoCycleInterval);
                autoCycleInterval = null;
            }
        };

        // Start auto-cycling
        startAutoCycle();

        // Stop auto-cycle when user interacts with demo
        const demoButtons = document.querySelectorAll('.demo-btn');
        demoButtons.forEach(btn => {
            btn.addEventListener('click', stopAutoCycle);
        });

        // Handle page visibility changes
        document.addEventListener('visibilitychange', function() {
            if (document.visibilityState === 'hidden') {
                stopAutoCycle();
            } else {
                startAutoCycle();
            }
        });
    },

    /**
     * Initialize interactive demo
     */
    init() {
        // Initialize auto-cycling
        this.initAutoCycle();
    }
};

// Main Application
const GettingStartedApp = {
    /**
     * Initialize the application
     */
    init() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.initializeModules());
        } else {
            this.initializeModules();
        }
    },

    /**
     * Initialize all modules
     */
    initializeModules() {
        try {
            FAQManager.init();
            ContextualManager.init();
            TutorialManager.init();
            AnimationManager.init();
            NavigationManager.init();
            PerformanceManager.init();
            InteractiveDemoManager.init();
            EngagementTracker.init();
            
            console.log('Getting Started App initialized successfully');
        } catch (error) {
            console.error('Error initializing Getting Started App:', error);
        }
    }
};

// Global functions for template compatibility
window.toggleFAQ = (element) => FAQManager.toggleFAQ(element);
window.startTutorial = (tutorialId) => TutorialManager.startTutorial(tutorialId);
window.showScenario = (scenarioKey) => InteractiveDemoManager.showScenario(scenarioKey);

// AI Recommendation functions
window.tryDifferentScenario = () => {
    const scenarios = Object.keys(InteractiveDemoManager.scenarios);
    const currentScenario = document.querySelector('.demo-btn.active');
    let currentIndex = 0;
    
    if (currentScenario) {
        const currentText = currentScenario.textContent.toLowerCase();
        currentIndex = scenarios.findIndex(scenario => 
            currentText.includes(scenario.replace('-', ' '))
        );
    }
    
    const nextIndex = (currentIndex + 1) % scenarios.length;
    InteractiveDemoManager.showScenario(scenarios[nextIndex]);
    
    // Track analytics
    fetch('/api/landing/analytics', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            event_type: 'ai_recommendation_interaction',
            event_data: {
                action: 'try_different_scenario',
                timestamp: new Date().toISOString()
            }
        })
    }).catch(e => console.log('Analytics tracking failed:', e));
};

window.explainRecommendation = () => {
    const explanationElement = document.getElementById('scenarioExplanation');
    const explanationText = document.getElementById('explanationText');
    
    if (explanationElement && explanationText) {
        const isVisible = explanationElement.style.display !== 'none';
        explanationElement.style.display = isVisible ? 'none' : 'block';
        
        // Get current scenario explanation
        const currentScenario = document.querySelector('.demo-btn.active');
        if (currentScenario) {
            const currentText = currentScenario.textContent.toLowerCase();
            const scenarios = InteractiveDemoManager.scenarios;
            const scenarioKey = Object.keys(scenarios).find(key => 
                currentText.includes(key.replace('-', ' '))
            );
            
            if (scenarioKey && scenarios[scenarioKey].aiRecommendation) {
                explanationText.textContent = scenarios[scenarioKey].aiRecommendation.explanation;
            }
        }
    }
    
    // Track analytics
    fetch('/api/landing/analytics', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            event_type: 'ai_recommendation_interaction',
            event_data: {
                action: 'explain_recommendation',
                timestamp: new Date().toISOString()
            }
        })
    }).catch(e => console.log('Analytics tracking failed:', e));
};

// Initialize the application
GettingStartedApp.init();
