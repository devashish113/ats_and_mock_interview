import React, { useState, useCallback } from 'react';
import MockInterviewPage from './MockInterviewPage';
import './App.css';

// API Base URL
const API_URL = 'http://localhost:8000';

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
      {/* Header */}
      <header className="header">
        <div className="logo">
          <div className="logo-icon">📄</div>
          <div>
            <h1>ATS Resume Converter</h1>
            <span className="header-subtitle">AI-Powered Resume Optimization</span>
          </div>
        </div>
        
        {/* Navigation Tabs */}
        <nav className="nav-tabs">
          <button
            className={`nav-tab ${currentPage === 'resume' ? 'active' : ''}`}
            onClick={() => setCurrentPage('resume')}
          >
            📄 Resume Converter
          </button>
          <button
            className={`nav-tab ${currentPage === 'interview' ? 'active' : ''}`}
            onClick={() => setCurrentPage('interview')}
          >
            🎤 Mock Interview
          </button>
        </nav>
      </header>

      {/* Conditional Page Rendering */}
      {currentPage === 'interview' ? (
        <MockInterviewPage 
          fileId={fileId} 
          onBack={() => setCurrentPage('resume')} 
        />
      ) : (
      <>
      {/* Main Content */}
      <main className="main-content">
        {/* Hero */}
        <section className="hero">
          <h2>Transform Your Resume into an <span>ATS-Friendly</span> Format</h2>
          <p>Upload your resume, get instant ATS scoring, and download an optimized version that passes automated screening systems.</p>
        </section>

        {/* Upload Section */}
        <section className="upload-section">
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
          </div>
        </section>

        {/* Results Section */}
        {analysisResult && (
          <section className="results-section">
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
          </section>
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
      </main>
      </>
      )}
    </div>
  );
}

export default App;
