import React, { useState, useRef, useEffect } from 'react';
import { ChatMessage, ChatResponse } from '../types/chat';
import { sendChatMessage, submitChatFeedback } from '../services/api';
import { Send, Mic, MicOff, Volume2, Sparkles, ThumbsUp, ThumbsDown, Shield, AlertTriangle } from './Icons';

interface ChatDrawerProps {
  currentLocation: string;
  latitude: number;
  longitude: number;
  selectedLanguage: string;
  userRole: string;
  isOpenAsFullPage?: boolean;
}

export const ChatDrawer: React.FC<ChatDrawerProps> = ({
  currentLocation,
  latitude,
  longitude,
  selectedLanguage,
  userRole,
  isOpenAsFullPage = false
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      sender: 'assistant',
      content: "Hello! I'm WeatherGPT, your meteorological intelligence and decision-support assistant.\nAsk me about forecasts, crop irrigation, pesticide spraying, severe storm warnings, or travel safety.",
      timestamp: 'Just now'
    }
  ]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [feedbackState, setFeedbackState] = useState<Record<string, boolean>>({});

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSend = async (queryText?: string) => {
    const text = (queryText || inputText).trim();
    if (!text || isLoading) return;

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      sender: 'user',
      content: text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputText('');
    setIsLoading(true);

    try {
      const resp: ChatResponse = await sendChatMessage({
        message: text,
        latitude,
        longitude,
        location_name: currentLocation,
        user_role: userRole,
        language: selectedLanguage
      });

      const aiMsg: ChatMessage = {
        id: resp.message_id,
        sender: 'assistant',
        content: resp.answer,
        data: resp,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };

      setMessages((prev) => [...prev, aiMsg]);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          sender: 'assistant',
          content: `Unable to complete weather intelligence query: ${err.message || 'Network error'}. Please retry.`,
          timestamp: 'Just now'
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  // Web Speech STT Recognition
  const handleVoiceInput = () => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert('Speech Recognition is not supported by this browser. Try Google Chrome or Edge.');
      return;
    }

    if (isRecording) {
      setIsRecording(false);
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = selectedLanguage === 'te' ? 'te-IN' : selectedLanguage === 'hi' ? 'hi-IN' : 'en-IN';
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onstart = () => setIsRecording(true);
    recognition.onend = () => setIsRecording(false);
    recognition.onerror = () => setIsRecording(false);

    recognition.onresult = (event: any) => {
      const transcript = event.results[0][0].transcript;
      setInputText(transcript);
      handleSend(transcript);
    };

    recognition.start();
  };

  // Web Speech TTS Synthesis
  const handleSpeak = (text: string) => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 0.95;
      utterance.lang = selectedLanguage === 'te' ? 'te-IN' : selectedLanguage === 'hi' ? 'hi-IN' : 'en-IN';
      window.speechSynthesis.speak(utterance);
    }
  };

  const handleFeedback = async (msgId: string, helpful: boolean) => {
    setFeedbackState((prev) => ({ ...prev, [msgId]: helpful }));
    try {
      await submitChatFeedback(msgId, helpful);
    } catch {
      // Non-blocking
    }
  };

  const quickPrompts = [
    { label: '🌧️ Rain tomorrow?', text: `Will it rain tomorrow in ${currentLocation}?` },
    { label: '🌾 Paddy Irrigation', text: 'Should I irrigate my paddy field tomorrow morning?' },
    { label: '⚠️ Active Warnings', text: 'Are there any severe weather warnings near me?' },
    { label: '🚗 Travel Safety', text: `How will the weather affect my travel in ${currentLocation}?` },
    { label: '📊 7-Day Rainfall Trend', text: 'Show rainfall trend for the last 7 days.' },
    { label: '🗣️ తెలుగులో అడగండి (Telugu)', text: `రేపు ${currentLocation} లో వర్షం పడుతుందా?` }
  ];

  return (
    <div className="glass-panel" style={{
      display: 'flex',
      flexDirection: 'column',
      height: isOpenAsFullPage ? 'calc(100vh - 140px)' : '620px',
      overflow: 'hidden'
    }}>
      
      {/* Header */}
      <div style={{
        padding: '1rem 1.25rem',
        borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        background: 'rgba(15, 23, 42, 0.6)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{
            background: 'linear-gradient(135deg, #0284c7, #38bdf8)',
            borderRadius: '8px',
            padding: '6px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <Sparkles size={16} color="#fff" />
          </div>
          <div>
            <h3 style={{ fontSize: '1rem', fontWeight: 800, color: '#f8fafc' }}>
              WeatherGPT Intelligence Assistant
            </h3>
            <div style={{ fontSize: '0.72rem', color: '#94a3b8' }}>
              Verified Data → Grounded Reasoning → Actionable Decision
            </div>
          </div>
        </div>

        <div style={{ fontSize: '0.75rem', color: '#38bdf8', background: 'rgba(56, 189, 248, 0.1)', padding: '3px 8px', borderRadius: '9999px', border: '1px solid rgba(56, 189, 248, 0.2)' }}>
          Active Sector: <strong>{userRole.toUpperCase()}</strong>
        </div>
      </div>

      {/* Messages Container */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        {messages.map((msg) => (
          <div
            key={msg.id}
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: msg.sender === 'user' ? 'flex-end' : 'flex-start',
              maxWidth: '100%'
            }}
          >
            <div style={{
              maxWidth: msg.sender === 'user' ? '75%' : '90%',
              background: msg.sender === 'user' ? '#0284c7' : 'rgba(30, 41, 59, 0.75)',
              color: '#f8fafc',
              padding: '0.85rem 1.15rem',
              borderRadius: msg.sender === 'user' ? '18px 18px 4px 18px' : '18px 18px 18px 4px',
              border: msg.sender === 'user' ? 'none' : '1px solid rgba(255, 255, 255, 0.08)',
              fontSize: '0.92rem',
              lineHeight: 1.5,
              whiteSpace: 'pre-wrap'
            }}>
              {msg.content}

              {/* Structured Response Card for Assistant */}
              {msg.data && (
                <div style={{
                  marginTop: '0.85rem',
                  paddingTop: '0.85rem',
                  borderTop: '1px solid rgba(255, 255, 255, 0.1)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.5rem',
                  fontSize: '0.8rem'
                }}>
                  {/* Weather Basis Chips */}
                  {msg.data.weather_summary && (
                    <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                      {msg.data.weather_summary.temperature_c !== undefined && (
                        <span style={{ background: 'rgba(0,0,0,0.3)', padding: '2px 8px', borderRadius: '6px' }}>
                          🌡️ {Math.round(msg.data.weather_summary.temperature_c)}°C
                        </span>
                      )}
                      {msg.data.weather_summary.rain_probability_pct !== undefined && (
                        <span style={{ background: 'rgba(56, 189, 248, 0.2)', color: '#38bdf8', padding: '2px 8px', borderRadius: '6px' }}>
                          🌧️ Rain: {msg.data.weather_summary.rain_probability_pct}%
                        </span>
                      )}
                      {msg.data.weather_summary.wind_kmh !== undefined && (
                        <span style={{ background: 'rgba(0,0,0,0.3)', padding: '2px 8px', borderRadius: '6px' }}>
                          💨 Wind: {Math.round(msg.data.weather_summary.wind_kmh)} km/h
                        </span>
                      )}
                      <span style={{
                        padding: '2px 8px',
                        borderRadius: '6px',
                        background: msg.data.risk_level === 'critical' ? 'rgba(239, 68, 68, 0.3)' : 'rgba(16, 185, 129, 0.2)',
                        color: msg.data.risk_level === 'critical' ? '#ef4444' : '#10b981',
                        fontWeight: 700
                      }}>
                        Risk: {msg.data.risk_level.toUpperCase()}
                      </span>
                    </div>
                  )}

                  {/* Sources and Confidence Attribution */}
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    flexWrap: 'wrap',
                    gap: '4px',
                    color: '#94a3b8',
                    fontSize: '0.72rem',
                    marginTop: '4px'
                  }}>
                    <span>Sources: {msg.data.sources.join(', ')}</span>
                    <span style={{ color: '#38bdf8' }}>Confidence: {msg.data.confidence}</span>
                  </div>
                </div>
              )}
            </div>

            {/* Assistant Action Buttons: Speak & Feedback */}
            {msg.sender === 'assistant' && msg.id !== 'welcome' && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '4px', paddingLeft: '4px' }}>
                <button
                  onClick={() => handleSpeak(msg.content)}
                  title="Listen (Text-to-Speech)"
                  style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.75rem' }}
                >
                  <Volume2 size={15} /> Listen
                </button>
                <div style={{ display: 'flex', alignItems: 'center', gap: '4px', marginLeft: '6px' }}>
                  <button
                    onClick={() => handleFeedback(msg.id, true)}
                    style={{
                      background: feedbackState[msg.id] === true ? 'rgba(16, 185, 129, 0.3)' : 'transparent',
                      border: 'none',
                      color: feedbackState[msg.id] === true ? '#10b981' : '#94a3b8',
                      cursor: 'pointer',
                      padding: '2px 4px',
                      borderRadius: '4px'
                    }}
                  >
                    <ThumbsUp size={14} />
                  </button>
                  <button
                    onClick={() => handleFeedback(msg.id, false)}
                    style={{
                      background: feedbackState[msg.id] === false ? 'rgba(239, 68, 68, 0.3)' : 'transparent',
                      border: 'none',
                      color: feedbackState[msg.id] === false ? '#ef4444' : '#94a3b8',
                      cursor: 'pointer',
                      padding: '2px 4px',
                      borderRadius: '4px'
                    }}
                  >
                    <ThumbsDown size={14} />
                  </button>
                </div>
              </div>
            )}
          </div>
        ))}

        {isLoading && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#38bdf8', fontSize: '0.85rem' }}>
            <span className="animate-pulse-glow">⚡</span> Retrieving verified weather tools & analyzing context...
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Quick Prompts Bar */}
      <div style={{
        padding: '0.5rem 1rem',
        borderTop: '1px solid rgba(255, 255, 255, 0.05)',
        display: 'flex',
        gap: '6px',
        overflowX: 'auto',
        background: 'rgba(11, 15, 25, 0.5)'
      }}>
        {quickPrompts.map((qp, i) => (
          <button
            key={i}
            onClick={() => handleSend(qp.text)}
            style={{
              flex: '0 0 auto',
              background: 'rgba(30, 41, 59, 0.6)',
              border: '1px solid rgba(255, 255, 255, 0.08)',
              color: '#e2e8f0',
              padding: '4px 10px',
              borderRadius: '9999px',
              fontSize: '0.75rem',
              cursor: 'pointer',
              whiteSpace: 'nowrap'
            }}
          >
            {qp.label}
          </button>
        ))}
      </div>

      {/* Input Form with Voice Button */}
      <div style={{
        padding: '0.75rem 1rem',
        borderTop: '1px solid rgba(255, 255, 255, 0.08)',
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        background: 'rgba(15, 23, 42, 0.8)'
      }}>
        <button
          onClick={handleVoiceInput}
          title={isRecording ? 'Stop Recording' : 'Voice Input (Speech-to-Text)'}
          style={{
            background: isRecording ? '#ef4444' : 'rgba(30, 41, 59, 0.8)',
            border: isRecording ? '1px solid #ef4444' : '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: '50%',
            width: '40px',
            height: '40px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#fff',
            cursor: 'pointer',
            flexShrink: 0,
            transition: 'all 0.2s'
          }}
          className={isRecording ? 'animate-pulse-glow' : ''}
        >
          {isRecording ? <MicOff size={18} /> : <Mic size={18} />}
        </button>

        <input
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder={`Ask WeatherGPT anything in ${selectedLanguage.toUpperCase()} (e.g. "Will it rain tomorrow?")...`}
          style={{
            flex: 1,
            background: 'rgba(30, 41, 59, 0.6)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: '12px',
            padding: '0.65rem 1rem',
            color: '#f8fafc',
            fontSize: '0.9rem',
            outline: 'none'
          }}
        />

        <button
          onClick={() => handleSend()}
          disabled={!inputText.trim() || isLoading}
          style={{
            background: inputText.trim() ? '#0284c7' : 'rgba(30, 41, 59, 0.4)',
            border: 'none',
            borderRadius: '12px',
            width: '40px',
            height: '40px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#fff',
            cursor: inputText.trim() ? 'pointer' : 'not-allowed',
            flexShrink: 0
          }}
        >
          <Send size={18} />
        </button>
      </div>

    </div>
  );
};
