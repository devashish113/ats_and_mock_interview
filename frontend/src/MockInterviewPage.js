import React, { useState, useCallback, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

// API Base URL
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Example roles for placeholder text
const ROLE_EXAMPLES = 'e.g., DevOps, Backend Developer, Cloud Engineer, Data Scientist...';

function MockInterviewPage({ fileId, onBack }) {
  // Interview state
  const [role, setRole] = useState('');
  const [sessionId, setSessionId] = useState(null);
  const [currentQuestion, setCurrentQuestion] = useState('');
  const [questionIndex, setQuestionIndex] = useState(0);
  const [totalQuestions, setTotalQuestions] = useState(5);
  const [isComplete, setIsComplete] = useState(false);
  const [report, setReport] = useState(null);

  // UI state
  const [loading, setLoading] = useState(false);
  const [loadingAction, setLoadingAction] = useState('');
  const [error, setError] = useState('');

  // Chat messages
  const [messages, setMessages] = useState([]);

  // Speech state
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [speechSupported, setSpeechSupported] = useState(true);

  // Refs
  const recognitionRef = useRef(null);
  const messagesEndRef = useRef(null);
  const textInputRef = useRef(null);
  const transcriptRef = useRef(''); // Track transcript across restarts
  const manualStopRef = useRef(false); // Track if user manually stopped
  const isRestartingRef = useRef(false); // Prevent overlapping restarts

  // Check speech recognition support
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setSpeechSupported(false);
    }
    
    // Cleanup on unmount
    return () => {
      manualStopRef.current = true;
      if (recognitionRef.current) {
        try {
          recognitionRef.current.abort();
        } catch (e) {}
        recognitionRef.current = null;
      }
    };
  }, []);

  // Auto-scroll to latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Text-to-Speech function
  const speak = useCallback((text) => {
    return new Promise((resolve) => {
      if (!window.speechSynthesis) {
        resolve();
        return;
      }

      // Cancel any ongoing speech
      window.speechSynthesis.cancel();

      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 0.9;
      utterance.pitch = 1;
      utterance.volume = 1;

      utterance.onstart = () => setIsSpeaking(true);
      utterance.onend = () => {
        setIsSpeaking(false);
        resolve();
      };
      utterance.onerror = () => {
        setIsSpeaking(false);
        resolve();
      };

      window.speechSynthesis.speak(utterance);
    });
  }, []);

  // Stop speaking
  const stopSpeaking = useCallback(() => {
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
    }
  }, []);

  // Add message to chat
  const addMessage = useCallback((type, content, extra = {}) => {
    setMessages((prev) => [
      ...prev,
      {
        id: Date.now(),
        type, // 'ai-question', 'ai-feedback', 'user', 'system'
        content,
        ...extra,
      },
    ]);
  }, []);

  // Start interview
  const startInterview = async () => {
    if (!fileId) {
      setError('Please upload a resume first on the main page.');
      return;
    }

    setLoading(true);
    setLoadingAction('Starting interview');
    setError('');
    setMessages([]);
    setIsComplete(false);
    setReport(null);

    try {
      const response = await fetch(`${API_URL}/mock/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ file_id: fileId, role }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to start interview');
      }

      const data = await response.json();
      setSessionId(data.session_id);
      setCurrentQuestion(data.question);
      setQuestionIndex(data.question_index);
      setTotalQuestions(data.total_questions);

      // Add welcome message
      addMessage('system', `🎯 ${role} Interview Started! Answer ${data.total_questions} questions.`);

      // Add and speak first question
      addMessage('ai-question', data.question);
      await speak(data.question);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
      setLoadingAction('');
    }
  };

  // Submit answer
  const submitAnswer = async (answerText) => {
    if (!answerText.trim() || !sessionId) return;

    const answer = answerText.trim();
    setTranscript('');
    transcriptRef.current = '';
    setLoading(true);
    setLoadingAction('Evaluating answer');

    // Add user message
    addMessage('user', answer);

    try {
      const response = await fetch(`${API_URL}/mock/answer`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, answer_text: answer }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to submit answer');
      }

      const data = await response.json();

      // Add feedback message
      addMessage('ai-feedback', data.feedback, {
        score: data.score,
        strengths: data.strengths,
        missingPoints: data.missing_points,
        tip: data.improvement_tip,
      });

      // Speak feedback
      await speak(data.feedback);

      if (data.is_complete) {
        setIsComplete(true);
        setCurrentQuestion('');
        addMessage('system', '🎉 Interview Complete! Loading your report...');
        // Fetch report
        await fetchReport();
      } else {
        // Add next question
        setCurrentQuestion(data.next_question);
        setQuestionIndex(data.question_index);
        addMessage('ai-question', data.next_question);
        await speak(data.next_question);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
      setLoadingAction('');
    }
  };

  // Fetch interview report
  const fetchReport = async () => {
    if (!sessionId) return;

    try {
      const response = await fetch(`${API_URL}/mock/report?session_id=${sessionId}`);
      if (!response.ok) {
        throw new Error('Failed to fetch report');
      }
      const data = await response.json();
      setReport(data);
    } catch (err) {
      setError(err.message);
    }
  };

  // Ref to accumulate all FINAL speech results across auto-restarts
  const finalWordsRef = useRef('');

  // Initialize speech recognition instance
  const initRecognition = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setError('Speech recognition not supported in this browser. Please use Chrome or Edge, or use the text input.');
      return null;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';
    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
      console.log('🎤 Speech recognition started');
      isRestartingRef.current = false;
      setIsListening(true);
    };

    recognition.onresult = (event) => {
      let sessionFinal = '';
      let sessionInterim = '';

      for (let i = 0; i < event.results.length; i++) {
        const result = event.results[i];
        if (result.isFinal) {
          sessionFinal += result[0].transcript + ' ';
        } else {
          sessionInterim += result[0].transcript;
        }
      }

      // Build the display text: all accumulated finals + current session text
      const displayText = (finalWordsRef.current + sessionFinal + sessionInterim).trim();
      transcriptRef.current = displayText;
      setTranscript(displayText);
    };

    recognition.onerror = (event) => {
      console.log('⚠️ Speech recognition error:', event.error);
      if (event.error === 'not-allowed' || event.error === 'service-not-allowed') {
        setError('Microphone access denied. Please allow microphone access and refresh.');
        setSpeechSupported(false);
        setIsListening(false);
        isRestartingRef.current = false;
      }
      // All other errors (network, no-speech, aborted) → let onend handle restart
    };

    recognition.onend = () => {
      console.log('🛑 Recognition ended. manualStop:', manualStopRef.current);
      
      // Capture final words from this session into the accumulator
      // transcriptRef has the latest display text; use it as the new base
      finalWordsRef.current = transcriptRef.current;

      if (manualStopRef.current) {
        setIsListening(false);
        isRestartingRef.current = false;
        return;
      }
      
      if (isRestartingRef.current) return;
      isRestartingRef.current = true;
      
      setTimeout(() => {
        if (manualStopRef.current) {
          setIsListening(false);
          isRestartingRef.current = false;
          return;
        }
        
        console.log('🔄 Auto-restarting recognition (new instance)...');
        const newRecognition = initRecognition();
        if (newRecognition) {
          recognitionRef.current = newRecognition;
          try {
            newRecognition.start();
          } catch (e) {
            console.error('Auto-restart failed:', e);
            setIsListening(false);
            isRestartingRef.current = false;
          }
        }
      }, 300);
    };

    return recognition;
  };

  // Start speech recognition (user clicks Speak)
  const startListening = () => {
    if (isRestartingRef.current) return;

    if (recognitionRef.current) {
      try { recognitionRef.current.abort(); } catch (e) {}
      recognitionRef.current = null;
    }

    stopSpeaking(); 
    manualStopRef.current = false;
    finalWordsRef.current = '';
    transcriptRef.current = '';
    setTranscript('');
    setError('');
    setIsListening(true);

    const recognition = initRecognition();
    if (recognition) {
      recognitionRef.current = recognition;
      try {
        recognition.start();
        console.log('🎤 Recognition.start() called');
      } catch (e) {
        console.error('Failed to start recognition:', e);
        setError('Failed to start microphone. Please refresh the page and try again.');
        setIsListening(false);
      }
    }
  };

  // Stop speech recognition and submit
  const stopListening = () => {
    console.log('⏹️ Stop listening called');
    manualStopRef.current = true;
    
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch (e) {
        console.log('Stop error:', e);
      }
      recognitionRef.current = null;
    }
    
    setIsListening(false);
    
    // Small delay to let any last onresult/onend fire and flush data
    setTimeout(() => {
      // Use the best transcript we have: transcriptRef (latest) or finalWordsRef (accumulated)
      const bestTranscript = (transcriptRef.current || finalWordsRef.current || '').trim();
      console.log('📤 Submitting transcript:', bestTranscript);
      if (bestTranscript) {
        submitAnswer(bestTranscript);
      } else {
        setError('No speech was detected. Please try again or use the text input.');
      }
    }, 150);
  };

  // Handle text input submit
  const handleTextSubmit = (e) => {
    e.preventDefault();
    const input = textInputRef.current;
    if (input && input.value.trim()) {
      submitAnswer(input.value);
      input.value = '';
    }
  };

  // Get score color class
  const getScoreClass = (score) => {
    if (score >= 8) return 'excellent';
    if (score >= 6) return 'good';
    if (score >= 4) return 'fair';
    return 'poor';
  };

  return (
    <div className="mock-interview-page">
      {/* Header */}
      <div className="interview-header">
        <button className="btn btn-outline back-btn" onClick={onBack}>
          ← Back to Resume
        </button>
        <h2>🎤 AI Mock Interview</h2>
      </div>

      {/* Pre-Interview Setup */}
      {!sessionId && !isComplete && (
        <motion.div 
          className="interview-setup"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
        >
          <div className="setup-card">
            <h3>Prepare for Your Mock Interview</h3>
            <p>Enter your target role and start your voice-based interview. The AI will ask questions based on your resume.</p>

            {!fileId && (
              <div className="warning-message">
                ⚠️ Please upload a resume on the main page first.
              </div>
            )}

            <div className="role-selector">
              <label htmlFor="role-input">Enter Interview Role:</label>
              <input
                id="role-input"
                type="text"
                value={role}
                onChange={(e) => setRole(e.target.value)}
                placeholder={ROLE_EXAMPLES}
                disabled={loading}
                className="role-input"
              />
            </div>

            <button
              className="btn btn-primary start-btn"
              onClick={startInterview}
              disabled={loading || !fileId}
            >
              {loading ? (
                <>
                  <span className="spinner"></span>
                  {loadingAction}...
                </>
              ) : (
                '🎙️ Start Interview'
              )}
            </button>

            {!speechSupported && (
              <p className="speech-note">
                ℹ️ Speech recognition not available. You'll type your answers.
              </p>
            )}
          </div>
        </motion.div>
      )}

      {/* Error Display */}
      {error && (
        <div className="error-message interview-error">
          <span>⚠️</span>
          {error}
          <button onClick={() => setError('')}>×</button>
        </div>
      )}

      {/* Interview Chat Interface */}
      {sessionId && (
        <motion.div 
          className="interview-chat"
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
        >
          {/* Progress Bar */}
          <div className="interview-progress">
            <div className="progress-label">
              Question {Math.min(questionIndex + 1, totalQuestions)} of {totalQuestions}
            </div>
            <div className="progress-bar">
              <div
                className="progress-fill"
                style={{ width: `${((questionIndex + 1) / totalQuestions) * 100}%` }}
              ></div>
            </div>
          </div>

          {/* Messages */}
          <div className="chat-messages">
            {messages.map((msg) => (
              <div key={msg.id} className={`chat-message ${msg.type}`}>
                {msg.type === 'ai-question' && (
                  <>
                    <div className="message-avatar">🤖</div>
                    <div className="message-content">
                      <div className="message-label">AI Interviewer</div>
                      <div className="message-text">{msg.content}</div>
                    </div>
                  </>
                )}
                {msg.type === 'ai-feedback' && (
                  <>
                    <div className="message-avatar">📋</div>
                    <div className="message-content feedback-content">
                      <div className="message-label">Feedback</div>
                      <div className={`score-badge ${getScoreClass(msg.score)}`}>
                        Score: {msg.score}/10
                      </div>
                      <div className="message-text">{msg.content}</div>
                      {msg.strengths && msg.strengths.length > 0 && (
                        <div className="feedback-detail">
                          <strong>✅ Strengths:</strong>
                          <ul>
                            {msg.strengths.map((s, i) => <li key={i}>{s}</li>)}
                          </ul>
                        </div>
                      )}
                      {msg.missingPoints && msg.missingPoints.length > 0 && (
                        <div className="feedback-detail">
                          <strong>💡 Could Improve:</strong>
                          <ul>
                            {msg.missingPoints.map((m, i) => <li key={i}>{m}</li>)}
                          </ul>
                        </div>
                      )}
                    </div>
                  </>
                )}
                {msg.type === 'user' && (
                  <>
                    <div className="message-content user-content">
                      <div className="message-label">You</div>
                      <div className="message-text">{msg.content}</div>
                    </div>
                    <div className="message-avatar">👤</div>
                  </>
                )}
                {msg.type === 'system' && (
                  <div className="system-message">{msg.content}</div>
                )}
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          {!isComplete && (
            <div className="chat-input-area">
              {/* Live Transcript */}
              {transcript && (
                <div className="live-transcript">
                  <span className="transcript-label">🎤 Hearing:</span>
                  <span className="transcript-text">{transcript}</span>
                </div>
              )}

              {/* Speaking Indicator */}
              {isSpeaking && (
                <div className="speaking-indicator">
                  🔊 AI is speaking...
                  <button className="skip-btn" onClick={stopSpeaking}>Skip</button>
                </div>
              )}

              {/* Input Controls */}
              <div className="input-controls">
                {speechSupported ? (
                  <button
                    className={`mic-btn ${isListening ? 'listening' : ''}`}
                    onClick={isListening ? stopListening : startListening}
                    disabled={loading || isSpeaking}
                  >
                    {isListening ? '⏹️ Stop' : '🎙️ Speak'}
                  </button>
                ) : null}

                {/* Text Input Fallback */}
                <form className="text-input-form" onSubmit={handleTextSubmit}>
                  <input
                    ref={textInputRef}
                    type="text"
                    placeholder={speechSupported ? "Or type your answer..." : "Type your answer..."}
                    disabled={loading || isListening}
                  />
                  <button type="submit" className="send-btn" disabled={loading || isListening}>
                    ➤
                  </button>
                </form>
              </div>

              {loading && (
                <div className="loading-indicator">
                  <span className="spinner"></span>
                  {loadingAction}...
                </div>
              )}
            </div>
          )}
        </motion.div>
      )}

      {/* Interview Report */}
      {isComplete && report && (
        <motion.div 
          className="interview-report"
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
        >
          <div className="report-card">
            <h3>📊 Interview Report</h3>

            <div className="final-score">
              <div className={`score-circle ${getScoreClass(report.final_score)}`}>
                <span className="score-value">{report.final_score}</span>
                <span className="score-max">/10</span>
              </div>
              <div className="performance-level">{report.performance_level}</div>
            </div>

            <p className="report-summary">{report.summary}</p>

            <div className="qa-history">
              <h4>Question-by-Question Breakdown</h4>
              {report.qa_history.map((qa, index) => (
                <div key={index} className="qa-item">
                  <div className="qa-question">
                    <strong>Q{index + 1}:</strong> {qa.question}
                  </div>
                  <div className="qa-answer">
                    <strong>Your Answer:</strong> {qa.answer}
                  </div>
                  <div className={`qa-score ${getScoreClass(qa.score)}`}>
                    Score: {qa.score}/10
                  </div>
                  <div className="qa-tip">
                    💡 {qa.improvement_tip}
                  </div>
                </div>
              ))}
            </div>

            <button className="btn btn-secondary" onClick={() => {
              setSessionId(null);
              setIsComplete(false);
              setReport(null);
              setMessages([]);
            }}>
              🔄 Start New Interview
            </button>
          </div>
        </motion.div>
      )}
    </div>
  );
}

export default MockInterviewPage;
