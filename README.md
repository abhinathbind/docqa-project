# 🔷 DocQA — AI-Powered Document & Multimedia Q&A

A full-stack web application to upload PDFs, audio, and video files and chat with them using AI.

## 🔗 Live Links

| Service | URL |
|---------|-----|
| 🌐 Frontend | https://docqa-project.netlify.app |
| ⚙️ Backend API | https://docqa-backend-s940.onrender.com |
| 📄 API Docs | https://docqa-backend-s940.onrender.com/docs |

## ✨ Features

- 📄 **PDF Q&A** — Upload PDF aur AI se sawal karo
- 🎵 **Audio & Video** — Whisper se transcription
- ⏱️ **Timestamp Navigation** — Exact time pe jump karo
- 🔴 **Real-time Streaming** — Token-by-token response
- 🔐 **JWT Auth** — Secure login system
- 🐳 **Docker** — Full containerized setup

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, Vite → Netlify |
| Backend | Python 3.11, FastAPI → Render |
| Database | MongoDB (Motor async) |
| Cache | Redis |
| AI | OpenAI GPT-4o + Whisper |

## 🚀 Local Setup

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```