# ATS Resume Converter & AI Mock Interview

An AI-powered web application that converts regular resumes into ATS-friendly format and provides AI-powered mock interviews. Built with FastAPI backend and React frontend, powered by Groq AI.

![ATS Resume Converter](https://img.shields.io/badge/ATS-Resume_Converter-667eea)
![Mock Interview](https://img.shields.io/badge/AI-Mock_Interview-f093fb)
![Python](https://img.shields.io/badge/Python-3.9+-blue)
![React](https://img.shields.io/badge/React-18-61dafb)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED)
![License](https://img.shields.io/badge/License-MIT-green)

## ✨ Features

### 📄 Resume Converter
- **📤 Resume Upload**: Support for PDF and DOCX formats
- **📊 ATS Scoring**: Rule-based scoring system with detailed breakdown
- **🔍 Section Detection**: AI-powered identification of resume sections
- **💡 AI Suggestions**: Groq-powered improvement recommendations
- **📋 Job Matching**: Compare resume against job descriptions
- **✨ ATS Resume Generation**: Create optimized, ATS-friendly DOCX

### 🎤 AI Mock Interview
- **🎯 Role-Based Questions**: Tailored interview questions for your target role
- **🗣️ Voice Input**: Speak your answers using browser speech recognition
- **📝 Real-Time Feedback**: AI evaluates your answers with scores and tips
- **💪 Strength Analysis**: Identifies what you did well
- **📈 Improvement Suggestions**: Actionable tips for better answers
- **📊 Final Report**: Comprehensive interview performance summary

## 🛠️ Tech Stack

- **Backend**: Python, FastAPI, uvicorn
- **Frontend**: React 18
- **AI**: Groq API (Llama 3.1)
- **NLP**: spaCy
- **File Processing**: python-docx, PyMuPDF
- **Containerization**: Docker, Docker Compose
- **CI/CD**: Jenkins

## 📁 Project Structure

```
ats_resume_maker/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── config.py            # Environment configuration
│   │   ├── routes/
│   │   │   ├── resume.py        # Resume API endpoints
│   │   │   └── mock_interview.py # Mock Interview API endpoints
│   │   └── services/
│   │       ├── parser.py        # PDF/DOCX extraction
│   │       ├── ats_engine.py    # Section detection & scoring
│   │       ├── ai_service.py    # Groq AI integration
│   │       └── resume_builder.py# DOCX generation
│   ├── uploads/                  # Uploaded resumes
│   ├── generated/                # Generated resumes
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── App.js               # Main application
│   │   ├── App.css              # Styles
│   │   ├── MockInterviewPage.js # Mock Interview component
│   │   └── index.js
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
├── docker-compose.yml
├── Jenkinsfile
└── README.md
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Node.js 16+
- Groq API Key (get one at [console.groq.com](https://console.groq.com))

### Option 1: Docker (Recommended)

1. **Clone the repository**:
   ```bash
   git clone https://github.com/devashish113/ats_and_mock_interview.git
   cd ats_and_mock_interview
   ```

2. **Set environment variables**:
   ```bash
   # Create .env file in project root
   echo "GROQ_API_KEY=your_groq_api_key_here" > .env
   ```

3. **Run with Docker Compose**:
   ```bash
   docker-compose up --build
   ```

4. **Access the application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Option 2: Local Development

#### Backend Setup

1. **Navigate to backend directory**:
   ```bash
   cd backend
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   
   # Windows
   .\venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Download spaCy model**:
   ```bash
   python -m spacy download en_core_web_sm
   ```

5. **Configure environment**:
   ```bash
   # Copy example and add your Groq API key
   copy .env.example .env
   
   # Edit .env file with your API key
   GROQ_API_KEY=your_groq_api_key_here
   ```

6. **Start the backend server**:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

#### Frontend Setup

1. **Navigate to frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Start development server**:
   ```bash
   npm start
   ```

4. **Open in browser**: http://localhost:3000

## 📡 API Endpoints

### Resume Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/upload_resume` | Upload PDF/DOCX resume |
| POST | `/analyze_resume` | Analyze and score resume |
| POST | `/generate_ats_resume` | Generate ATS-optimized DOCX |
| POST | `/match_job_description` | Match resume with job posting |
| GET | `/download/{filename}` | Download generated resume |
| GET | `/tips` | Get resume improvement tips |

### Mock Interview Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/mock/start` | Start a new mock interview session |
| POST | `/mock/answer` | Submit answer and get feedback |
| GET | `/mock/report` | Get final interview report |

## 🎯 ATS Scoring Categories

| Category | Max Score | Description |
|----------|-----------|-------------|
| Section Presence | 25 | Essential sections detected |
| Heading Standards | 15 | ATS-friendly section headings |
| Keyword Density | 20 | Relevant industry keywords |
| Bullet Formatting | 20 | Action verbs and metrics |
| Formatting | 20 | Clean, parseable format |

## 🤖 AI Features (Groq)

The application uses Groq's Llama 3.1 model for:

1. **Bullet Point Improvement**: Enhances bullet points with action verbs
2. **Resume Rewriting**: Full ATS-style rewrite
3. **Improvement Suggestions**: Personalized recommendations
4. **Job Matching**: Keyword comparison and gap analysis
5. **Mock Interview Questions**: Role-specific interview questions
6. **Answer Evaluation**: Real-time feedback on interview answers

## 🐳 Docker Deployment

### Build and Run

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Environment Variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
MAX_FILE_SIZE_MB=10
```

## 🔧 Jenkins CI/CD

The project includes a `Jenkinsfile` for automated CI/CD:

### Pipeline Stages

1. **Checkout**: Clone repository
2. **Validate**: Check required files exist
3. **Build**: Build Docker images for frontend and backend
4. **Test**: Run backend import tests
5. **Security Scan**: Check for hardcoded secrets
6. **Deploy**: Deploy with Docker Compose (main branch only)
7. **Health Check**: Verify services are running

### Jenkins Setup

1. Install required Jenkins plugins:
   - Docker Pipeline
   - Pipeline
   - Git

2. Create a new Pipeline job and point to your repository

3. Add credentials:
   - ID: `groq-api-key`
   - Type: Secret text
   - Value: Your Groq API key

## 📝 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GROQ_API_KEY` | Your Groq API key | Required |
| `MAX_FILE_SIZE_MB` | Max upload size | 10 |
| `HOST` | Server host | 0.0.0.0 |
| `PORT` | Server port | 8000 |

## 🔒 Security

- File type validation (PDF/DOCX only)
- File size limits
- No hardcoded API keys
- Secure file handling
- Docker container isolation

## 📄 License

MIT License - feel free to use and modify!

---

**Built with ❤️ for job seekers everywhere**
