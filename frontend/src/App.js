import React, { useState, useCallback, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Lenis from '@studio-freight/lenis';
import Particles, { initParticlesEngine } from '@tsparticles/react';
import { loadSlim } from '@tsparticles/slim';
import MockInterviewPage from './MockInterviewPage';
import './App.css';

// API Base URL
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function App() {
  // State management
  const [file, setFile] = useState(null);
  const [fileId, setFileId] = useState(null);
  const [jobDescription, setJobDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingAction, setLoadingAction] = useState('');
  const [error, setError] = useState('');
  const [analysisResult, setAnalysisResult] = useState(null);
  const [jobMatchResult, setJobMatchResult] = useState(null);
  const [downloadUrl, setDownloadUrl] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [currentPage, setCurrentPage] = useState('resume'); // 'resume' or 'interview'
  const [initialLoad, setInitialLoad] = useState(true);
  const [initParticles, setInitParticles] = useState(false);

  // Initialize Particles
  useEffect(() => {
    initParticlesEngine(async (engine) => {
      await loadSlim(engine);
    }).then(() => {
      setInitParticles(true);
    });
  }, []);

  // Initialize Lenis smooth scrolling
  useEffect(() => {
    const lenis = new Lenis({
      duration: 1.2,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      direction: 'vertical',
      gestureDirection: 'vertical',
      smooth: true,
      mouseMultiplier: 1,
      smoothTouch: false,
      touchMultiplier: 2,
      infinite: false,
    });

    function raf(time) {
      lenis.raf(time);
      requestAnimationFrame(raf);
    }

    requestAnimationFrame(raf);

    // Initial loader timeout
    const loadTimer = setTimeout(() => {
      setInitialLoad(false);
    }, 2500);

    return () => {
      lenis.destroy();
      clearTimeout(loadTimer);
    };
  }, []);

  // Handle file selection
  const handleFileSelect = useCallback((selectedFile) => {
    if (selectedFile) {
      const extension = selectedFile.name.split('.').pop().toLowerCase();
      if (!['pdf', 'docx'].includes(extension)) {
        setError('Please upload a PDF or DOCX file');
        return;
      }
      setFile(selectedFile);
      setFileId(null);
      setAnalysisResult(null);
      setJobMatchResult(null);
      setDownloadUrl(null);
      setError('');
    }
  }, []);

  // Handle drag events
  const handleDrag = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  // Handle drop
  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  }, [handleFileSelect]);

  // Upload file
  const uploadFile = async () => {
    if (!file) return null;

    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_URL}/upload_resume`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const data = await response.json();
      throw new Error(data.detail || 'Upload failed');
    }

    const data = await response.json();
    return data.file_id;
  };

  // Analyze resume
  const handleAnalyze = async () => {
    setLoading(true);
    setLoadingAction('Analyzing');
    setError('');

    try {
      // Upload if not already uploaded
      let currentFileId = fileId;
      if (!currentFileId) {
        setLoadingAction('Uploading');
        currentFileId = await uploadFile();
        setFileId(currentFileId);
      }

      setLoadingAction('Analyzing');
      
      const formData = new FormData();
      formData.append('file_id', currentFileId);

      const response = await fetch(`${API_URL}/analyze_resume`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Analysis failed');
      }

      const data = await response.json();
      setAnalysisResult(data);

      // If job description provided, also do job matching
      if (jobDescription.trim()) {
        await handleJobMatch(currentFileId);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
      setLoadingAction('');
    }
  };

  // Match job description
  const handleJobMatch = async (fId = fileId) => {
    if (!jobDescription.trim()) return;

    try {
      const response = await fetch(`${API_URL}/match_job_description`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          file_id: fId,
          job_description: jobDescription,
        }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Job matching failed');
      }

      const data = await response.json();
      setJobMatchResult(data);
    } catch (err) {
      console.error('Job match error:', err);
    }
  };

  // Generate ATS resume
  const handleGenerate = async () => {
    setLoading(true);
    setLoadingAction('Generating');
    setError('');

    try {
      // Upload if not already uploaded
      let currentFileId = fileId;
      if (!currentFileId) {
        setLoadingAction('Uploading');
        currentFileId = await uploadFile();
        setFileId(currentFileId);
      }

      setLoadingAction('Generating ATS Resume');

      const formData = new FormData();
      formData.append('file_id', currentFileId);

      const response = await fetch(`${API_URL}/generate_ats_resume`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Generation failed');
      }

      const data = await response.json();
      setDownloadUrl(`${API_URL}${data.download_url}`);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
      setLoadingAction('');
    }
  };

  // Get score status
  const getScoreStatus = (score) => {
    if (score >= 85) return { label: 'Excellent', class: 'excellent' };
    if (score >= 70) return { label: 'Good', class: 'good' };
    if (score >= 50) return { label: 'Fair', class: 'fair' };
    return { label: 'Needs Improvement', class: 'poor' };
  };

  // Calculate circumference and offset for score ring
  const getScoreRingStyle = (score) => {
    const radius = 80;
    const circumference = 2 * Math.PI * radius;
    const offset = circumference - (score / 100) * circumference;
    return { circumference, offset };
  };

  // Reset form
  const handleReset = () => {
    setFile(null);
    setFileId(null);
    setJobDescription('');
    setAnalysisResult(null);
    setJobMatchResult(null);
    setDownloadUrl(null);
    setError('');
  };

  return (
    <div className="app-container">
      {/* Cinematic Loader using Framer Motion */}
      <AnimatePresence>
        {initialLoad && (
          <motion.div
            className="premium-loader"
            initial={{ opacity: 1 }}
            exit={{ opacity: 0, y: -50, filter: 'blur(10px)' }}
            transition={{ duration: 0.8, ease: [0.76, 0, 0.24, 1] }}
          >
            <motion.div 
              className="loader-content"
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ duration: 0.5, delay: 0.2 }}
            >
              <div className="logo-icon loader-logo">📄</div>
              <motion.h2 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.5 }}
              >
                ATS SYSTEM
              </motion.h2>
              <div className="loader-progress-bar">
                <motion.div 
                  className="loader-progress-fill"
                  initial={{ width: "0%" }}
                  animate={{ width: "100%" }}
                  transition={{ duration: 1.5, ease: "easeInOut", delay: 0.2 }}
                />
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Video Background */}
      <video autoPlay loop muted playsInline className="app-video-bg">
        <source src="/background.mp4" type="video/mp4" />
      </video>

      {/* Particle Background Layer */}
      {initParticles && (
        <Particles
          id="tsparticles"
          options={{
            background: { color: { value: "transparent" } },
            fpsLimit: 120,
            interactivity: {
              events: {
                onHover: { enable: true, mode: "grab" },
                resize: true,
              },
              modes: {
                grab: { distance: 140, links: { opacity: 0.5 } }
              },
            },
            particles: {
              color: { value: "#667eea" },
              links: {
                color: "#764ba2",
                distance: 150,
                enable: true,
                opacity: 0.2,
                width: 1,
              },
              move: {
                direction: "none",
                enable: true,
                outModes: { default: "bounce" },
                random: true,
                speed: 1.5,
                straight: false,
              },
              number: { density: { enable: true, area: 800 }, value: 60 },
              opacity: { value: 0.3 },
              shape: { type: "circle" },
              size: { value: { min: 1, max: 3 } },
            },
            detectRetina: true,
          }}
          style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', zIndex: 0 }}
        />
      )}

      {/* Header */}
      <header className="header" style={{ position: 'relative', zIndex: 50 }}>
        <div className="logo">
          <motion.div 
            className="logo-icon"
            whileHover={{ scale: 1.05, rotate: 5 }}
            transition={{ type: "spring", stiffness: 300 }}
          >
            📄
          </motion.div>
          <div>
            <h1>CareerPrep AI</h1>
            <span className="header-subtitle">ATS Resumes & Mock Interviews</span>
          </div>
        </div>
      </header>

      {/* Conditional Page Rendering wrapped in AnimatePresence */}
      <AnimatePresence mode="wait">
        {currentPage === 'interview' ? (
          <motion.div
            key="interview-page"
            initial={{ opacity: 0, scale: 0.98, filter: 'blur(5px)' }}
            animate={{ opacity: 1, scale: 1, filter: 'blur(0px)' }}
            exit={{ opacity: 0, scale: 0.98, filter: 'blur(5px)' }}
            transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
          >
            <MockInterviewPage 
              fileId={fileId} 
              onBack={() => setCurrentPage('resume')} 
            />
          </motion.div>
        ) : (
          <motion.main 
            key="resume-page"
            className="main-content"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
          >
            {/* Hero */}
            <section className="hero">
              <motion.h2
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, delay: 0.2, ease: [0.22, 1, 0.36, 1] }}
                style={{
                  background: 'linear-gradient(to right, #ffffff, #a0aec0)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  marginBottom: '20px'
                }}
              >
                Optimize Your Resume & <br />
                <span>Master Your Interview</span>
              </motion.h2>
              <motion.p
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, delay: 0.3, ease: [0.22, 1, 0.36, 1] }}
              >
                Get instant ATS scoring for your resume and immediately practice with our voice-enabled AI Mock Interviewer—all in one place.
              </motion.p>
            </section>

        {/* Upload Section */}
        <motion.section 
          className="upload-section"
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
        >
          {/* Dropzone */}
          <div
            className={`dropzone ${dragActive ? 'drag-active' : ''}`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            onClick={() => document.getElementById('file-input').click()}
          >
            <input
              id="file-input"
              type="file"
              accept=".pdf,.docx"
              onChange={(e) => handleFileSelect(e.target.files[0])}
              style={{ display: 'none' }}
            />
            <span className="dropzone-icon">📤</span>
            <h3>Drop your resume here or click to browse</h3>
            <p>We'll analyze it and create an ATS-optimized version</p>
            <div className="file-types">
              <span className="file-type-badge">PDF</span>
              <span className="file-type-badge">DOCX</span>
            </div>
          </div>

          {/* Selected File */}
          {file && (
            <div className="selected-file">
              <div className="selected-file-info">
                <span className="selected-file-icon">📎</span>
                <span className="selected-file-name">{file.name}</span>
              </div>
              <button className="remove-file-btn" onClick={handleReset}>
                Remove
              </button>
            </div>
          )}

          {/* Job Description (Optional) */}
          <div className="job-description-section">
            <label htmlFor="job-description">
              Job Description (Optional - for keyword matching)
            </label>
            <textarea
              id="job-description"
              placeholder="Paste the job description here to get keyword match analysis..."
              value={jobDescription}
              onChange={(e) => setJobDescription(e.target.value)}
            />
          </div>

          {/* Error Message */}
          {error && (
            <div className="error-message">
              <span>⚠️</span>
              {error}
            </div>
          )}

          {/* Action Buttons */}
          <div className="action-buttons">
            <button
              className="btn btn-primary"
              onClick={handleAnalyze}
              disabled={!file || loading}
            >
              {loading && loadingAction.includes('Analyz') ? (
                <>
                  <span className="spinner"></span>
                  {loadingAction}...
                </>
              ) : (
                <>📊 Analyze Resume</>
              )}
            </button>
            <button
              className="btn btn-secondary"
              onClick={handleGenerate}
              disabled={!file || loading}
            >
              {loading && loadingAction.includes('Generat') ? (
                <>
                  <span className="spinner"></span>
                  {loadingAction}...
                </>
              ) : (
                <>✨ Generate ATS Resume</>
              )}
            </button>
            <button
              className="btn btn-interview"
              onClick={() => setCurrentPage('interview')}
              disabled={!fileId || loading}
            >
              🎤 Mock Interview
            </button>
          </div>
        </motion.section>

        {/* Results Section */}
        {analysisResult && (
          <motion.section 
            className="results-section"
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true, margin: "-50px" }}
            transition={{ duration: 0.6, ease: "easeOut" }}
          >
            {/* Score Card */}
            <div className="score-card">
              <div className="score-ring">
                <svg width="200" height="200" viewBox="0 0 200 200">
                  <defs>
                    <linearGradient id="gradientGreen" x1="0%" y1="0%" x2="100%" y2="100%">
                      <stop offset="0%" stopColor="#11998e" />
                      <stop offset="100%" stopColor="#38ef7d" />
                    </linearGradient>
                    <linearGradient id="gradientBlue" x1="0%" y1="0%" x2="100%" y2="100%">
                      <stop offset="0%" stopColor="#667eea" />
                      <stop offset="100%" stopColor="#764ba2" />
                    </linearGradient>
                    <linearGradient id="gradientYellow" x1="0%" y1="0%" x2="100%" y2="100%">
                      <stop offset="0%" stopColor="#f6d365" />
                      <stop offset="100%" stopColor="#fda085" />
                    </linearGradient>
                    <linearGradient id="gradientRed" x1="0%" y1="0%" x2="100%" y2="100%">
                      <stop offset="0%" stopColor="#f093fb" />
                      <stop offset="100%" stopColor="#f5576c" />
                    </linearGradient>
                  </defs>
                  <circle className="score-ring-bg" cx="100" cy="100" r="80" />
                  <circle
                    className={`score-ring-progress ${getScoreStatus(analysisResult.ats_score).class}`}
                    cx="100"
                    cy="100"
                    r="80"
                    strokeDasharray={getScoreRingStyle(analysisResult.ats_score).circumference}
                    strokeDashoffset={getScoreRingStyle(analysisResult.ats_score).offset}
                  />
                </svg>
                <div className="score-value">
                  <div className="score-number">{analysisResult.ats_score}</div>
                  <div className="score-label">ATS Score</div>
                </div>
              </div>

              <span className={`score-status ${getScoreStatus(analysisResult.ats_score).class}`}>
                {getScoreStatus(analysisResult.ats_score).label}
              </span>

              {/* Score Breakdown */}
              <div className="score-breakdown">
                {Object.entries(analysisResult.score_breakdown).map(([key, value]) => {
                  const maxScore = key === 'section_presence' ? 25 : 
                                   key === 'heading_standards' ? 15 : 20;
                  const percentage = (value / maxScore) * 100;
                  return (
                    <div key={key} className="breakdown-item">
                      <div className="breakdown-item-header">
                        <span className="breakdown-item-label">
                          {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                        </span>
                        <span className="breakdown-item-score">{value}/{maxScore}</span>
                      </div>
                      <div className="breakdown-bar">
                        <div
                          className="breakdown-bar-fill"
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Issues & Suggestions */}
            <div className="feedback-section">
              {/* Issues */}
              {analysisResult.issues && analysisResult.issues.length > 0 && (
                <div className="feedback-card">
                  <h3><span className="icon">⚠️</span> Issues Found</h3>
                  <ul className="feedback-list issues-list">
                    {analysisResult.issues.map((issue, index) => (
                      <li key={index}>
                        <span className="bullet"></span>
                        {issue}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Suggestions */}
              {analysisResult.suggestions && analysisResult.suggestions.length > 0 && (
                <div className="feedback-card">
                  <h3><span className="icon">💡</span> Suggestions</h3>
                  <ul className="feedback-list suggestions-list">
                    {analysisResult.suggestions.map((suggestion, index) => (
                      <li key={index}>
                        <span className="bullet"></span>
                        {suggestion}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            {/* Job Match Results */}
            {jobMatchResult && (
              <div className="job-match-card">
                <h3>📋 Job Description Match</h3>
                <div className="match-percentage">
                  <span className="number">{jobMatchResult.match_percentage}%</span>
                  <span className="label"> Match</span>
                </div>
                <div className="keywords-section">
                  <div className="keywords-column">
                    <h4>✅ Matching Keywords</h4>
                    <div className="keywords-list">
                      {jobMatchResult.matching_keywords.map((keyword, index) => (
                        <span key={index} className="keyword-badge matching">
                          {keyword}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div className="keywords-column">
                    <h4>❌ Missing Keywords</h4>
                    <div className="keywords-list">
                      {jobMatchResult.missing_keywords.map((keyword, index) => (
                        <span key={index} className="keyword-badge missing">
                          {keyword}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </motion.section>
        )}

        {/* Download Section */}
        {downloadUrl && (
          <section className="download-section">
            <h3>🎉 Your ATS-Optimized Resume is Ready!</h3>
            <a
              href={downloadUrl}
              className="btn btn-secondary"
              download
            >
              📥 Download ATS Resume
            </a>
          </section>
        )}
      </motion.main>
    )}
    </AnimatePresence>
    </div>
  );
}

export default App;
