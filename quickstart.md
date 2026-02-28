# Quickstart Guide: ATS Resume Converter & AI Mock Interview

This guide will help you get the application up and running quickly on your machine.

## Prerequisites

- **Git**: To clone the repository
- **Option 1: Docker (Recommended)**: Docker and Docker Compose installed.
- **Option 2: Local Development**: Python 3.9+ and Node.js 16+ installed.
- **API Key**: A free Groq API key, which you can get at [console.groq.com](https://console.groq.com).

---

## 1. Get the Code & Set API Key

First, clone the repository and configure your Groq API key.

```bash
git clone https://github.com/devashish113/ats_and_mock_interview.git
cd ats_and_mock_interview

# Create a .env file and add your Groq API key
echo "GROQ_API_KEY=your_groq_api_key_here" > .env
```
*(Windows users: You can just create a new file named `.env` in the root folder and paste `GROQ_API_KEY=your_key` into it.)*

---

## Option A: Run with Docker (Recommended)

This is the fastest way to get everything running. It automatically handles all Python and Node.js dependencies in isolated containers.

```bash
docker-compose up --build
```

That's it! The application is now running.
- **Frontend App**: [http://localhost:3000](http://localhost:3000)
- **Backend API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

To stop the application, press `Ctrl+C` in the terminal, then run:
```bash
docker-compose down
```

---

## Option B: Run Locally (Development Setup)

If you want to modify the code, running the components locally in two separate terminals is best.

### Terminal 1: Backend Setup
```bash
cd backend

# Create and activate virtual environment
python -m venv venv
# Windows: .\venv\Scripts\activate
# Mac/Linux: source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Download required NLP model
python -m spacy download en_core_web_sm

# Add your API key to backend env
cp .env.example .env
# Edit backend/.env and set your GROQ_API_KEY

# Start backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
Backend is now running at `http://localhost:8000`.

### Terminal 2: Frontend Setup
Open a new terminal window in the project root:
```bash
cd frontend

# Install dependencies
npm install

# Start frontend development server
npm start
```
Your browser will automatically open `http://localhost:3000`.

---

## How to Use the App

1. **Upload Resume**: Go to to the main page and drag-and-drop a PDF or DOCX file.
2. **Analyze**: Click "Analyze Resume" to get an ATS score, feedback, and job description matching.
3. **Generate**: Click "Generate ATS Resume" to download a perfectly formatted, ATS-friendly `.docx` file.
4. **Mock Interview**: Click "Mock Interview", type the exact job role you are targeting, and practice answering role-specific questions from the AI using your microphone.
