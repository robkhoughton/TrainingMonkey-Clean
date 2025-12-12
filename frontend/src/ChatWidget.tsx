/**
 * ChatWidget - Streaming chat interface for the Coach page
 *
 * Features:
 * - Universe selector for context switching
 * - Real-time streaming responses via SSE
 * - Session-based conversation (no persistence)
 * - Usage tracking display
 */

import React, { useState, useRef, useEffect, useCallback } from 'react';
import './ChatWidget.css';

// Types
interface Message {
  role: 'user' | 'assistant' | 'intro';
  content: string;
}

interface UsageStats {
  messages_used: number;
  messages_remaining: number;
  percentage_used: number;
}

type Universe = 'autopsy' | 'training_plan' | 'todays_workout' | 'progress' | 'general';

const UNIVERSE_OPTIONS: { value: Universe; label: string }[] = [
  { value: 'autopsy', label: 'AI Autopsy' },
  { value: 'training_plan', label: 'Training Plan' },
  { value: 'todays_workout', label: "Today's Workout" },
  { value: 'progress', label: 'My Progress' },
  { value: 'general', label: 'General Coaching' },
];

const ChatWidget: React.FC = () => {
  // State
  const [isExpanded, setIsExpanded] = useState(false);
  const [universe, setUniverse] = useState<Universe>('general');
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [usage, setUsage] = useState<UsageStats | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom (only within chat container, not whole page)
  const scrollToBottom = useCallback(() => {
    if (messagesEndRef.current) {
      const container = messagesEndRef.current.closest('.chat-messages');
      if (container) {
        container.scrollTop = container.scrollHeight;
      }
    }
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // Load usage stats
  const loadUsage = useCallback(async () => {
    try {
      const response = await fetch('/api/chat/usage');
      if (response.ok) {
        const data = await response.json();
        setUsage(data);
      }
    } catch (e) {
      console.error('Failed to load usage stats:', e);
    }
  }, []);

  // Load intro message for universe
  const loadIntro = useCallback(async (selectedUniverse: Universe) => {
    try {
      const response = await fetch(`/api/chat/intro/${selectedUniverse}`);
      if (response.ok) {
        const data = await response.json();
        setMessages([{ role: 'intro', content: data.intro }]);
      }
    } catch (e) {
      console.error('Failed to load intro:', e);
    }
  }, []);

  // Initialize on expand
  useEffect(() => {
    if (isExpanded) {
      loadUsage();
      loadIntro(universe);
      inputRef.current?.focus();
    }
  }, [isExpanded, loadUsage, loadIntro, universe]);

  // Handle universe change
  const handleUniverseChange = (newUniverse: Universe) => {
    setUniverse(newUniverse);
    setMessages([]);
    setError(null);
    loadIntro(newUniverse);
  };

  // Send message with streaming
  const sendMessage = async () => {
    if (!inputValue.trim() || isStreaming) return;

    const userMessage = inputValue.trim();
    setInputValue('');
    setError(null);

    // Add user message
    const newMessages: Message[] = [
      ...messages.filter(m => m.role !== 'intro'),
      { role: 'user', content: userMessage }
    ];
    setMessages(newMessages);

    // Prepare conversation history for API
    const conversationHistory = newMessages
      .filter(m => m.role !== 'intro')
      .map(m => ({ role: m.role, content: m.content }));

    setIsStreaming(true);

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          universe,
          message: userMessage,
          conversation: conversationHistory.slice(0, -1), // Exclude the message we just added
        }),
      });

      if (!response.ok) {
        throw new Error('Chat request failed');
      }

      // Handle SSE stream
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      // Add empty assistant message
      setMessages(prev => [...prev, { role: 'assistant', content: '' }]);

      while (reader) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));

              if (data.type === 'token') {
                // Append token to existing content using functional update
                setMessages(prev => {
                  const updated = [...prev];
                  updated[updated.length - 1] = {
                    role: 'assistant',
                    content: updated[updated.length - 1].content + data.content
                  };
                  return updated;
                });
              } else if (data.type === 'done') {
                loadUsage(); // Refresh usage stats
              } else if (data.type === 'error') {
                setError(data.message);
              }
            } catch (e) {
              // Ignore JSON parse errors for incomplete chunks
            }
          }
        }
      }
    } catch (e) {
      setError('Connection error. Please try again.');
      console.error('Chat error:', e);
    } finally {
      setIsStreaming(false);
    }
  };

  // Handle Enter key
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className={`chat-widget ${isExpanded ? 'expanded' : 'collapsed'}`}>
      {/* Header */}
      <button
        className="chat-header"
        onClick={() => setIsExpanded(!isExpanded)}
        aria-expanded={isExpanded}
      >
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', gap: '2px' }}>
          <span className="chat-title">Ask Your Coach</span>
          <span style={{ fontSize: '11px', opacity: 0.85, fontWeight: 400 }}>Powered by Claude 3.5 Haiku</span>
        </div>
        <span className="chat-toggle-icon">{isExpanded ? '−' : '+'}</span>
      </button>

      {/* Body - only render when expanded */}
      {isExpanded && (
        <div className="chat-body">
          {/* Universe selector */}
          <div className="chat-universe-selector">
            <label htmlFor="chat-universe">Ask about:</label>
            <select
              id="chat-universe"
              value={universe}
              onChange={(e) => handleUniverseChange(e.target.value as Universe)}
              disabled={isStreaming}
            >
              {UNIVERSE_OPTIONS.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>

          {/* Messages */}
          <div className="chat-messages">
            {messages.map((msg, idx) => (
              <div key={idx} className={`chat-message ${msg.role}`}>
                {msg.content}
              </div>
            ))}
            {isStreaming && <div className="chat-streaming-indicator">...</div>}
            {error && <div className="chat-message error">{error}</div>}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="chat-input-area">
            <input
              ref={inputRef}
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your question..."
              disabled={isStreaming}
            />
            <button
              onClick={sendMessage}
              disabled={isStreaming || !inputValue.trim()}
            >
              Send
            </button>
          </div>

          {/* Usage display */}
          {usage && (
            <div className={`chat-usage ${usage.percentage_used > 80 ? 'warning' : ''}`}>
              {usage.messages_remaining} messages remaining today
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ChatWidget;
