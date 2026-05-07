# ◈ DocQA — AI-Powered Document & Multimedia Q&A

A full-stack web application to upload PDFs, audio, and video files and chat with them using AI.

## Features

- **PDF Q&A** — Upload PDF documents and ask questions about their content
- **Audio & Video Transcription** — Powered by OpenAI Whisper for accurate speech-to-text
- **Timestamp Navigation** — AI responses reference exact timestamps; click to jump there
- **Real-time Streaming** — Chat responses stream token-by-token via SSE
- **Auto Summaries** — Documents are summarized automatically on upload
- **JWT Auth** — Secure multi-user authentication (Bearer token)
- **Containerized** — Full Docker Compose setup (FastAPI + React + MongoDB + Redis)
- **CI/CD** — GitHub Actions pipeline with 95%+ test coverage enforcement

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, FastAPI, Motor (async MongoDB) |
| AI | OpenAI GPT-4o (chat), Whisper (transcription) |
| Frontend | React 18, plain CSS |
| Database | MongoDB 7 |
| Cache | Redis 7 |
| Containers | Docker, Docker Compose |
| CI/CD | GitHub Actions |

## Project Structure

```
docqa/
├── backend/
│   ├── app/
│   │   ├── api/          # Route handlers (files, chat, health)
│   │   ├── core/         # Config, DB, security
│   │   ├── models/       # Pydantic schemas
│   │   ├── services/     # AI service, file processor
│   │   └── tests/        # Pytest test suite (95%+ coverage)
│   ├── Dockerfile
│   ├── requirements.txt
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── components/   # FileLibrary, ChatPanel, UploadModal
│   │   ├── services/     # API client
│   │   └── App.jsx
│   ├── Dockerfile
│   └── nginx.conf
├── .github/workflows/ci.yml
└── docker-compose.yml
```

## Quick Start

### Prerequisites
- Docker & Docker Compose
- OpenAI API key

### 1. Clone & configure

```bash
git clone https://github.com/your-username/docqa.git
cd docqa
cp .env.example .env
# Edit .env and set OPENAI_API_KEY
```

### 2. Run with Docker Compose

```bash
docker compose up --build
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |

### 3. Run backend locally (development)

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 4. Run frontend locally

```bash
cd frontend
npm install
npm start
```

## API Documentation

Interactive Swagger docs are available at `http://localhost:8000/docs`.

### Endpoints

#### Files

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/files/upload` | Upload PDF/audio/video |
| `GET` | `/api/v1/files/` | List all user files |
| `GET` | `/api/v1/files/{id}` | Get file details + transcript |
| `DELETE` | `/api/v1/files/{id}` | Delete file |

**Upload example:**
```bash
curl -X POST http://localhost:8000/api/v1/files/upload \
  -F "file=@document.pdf"
```

#### Chat

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/chat/` | Ask a question (single response) |
| `POST` | `/api/v1/chat/stream` | Ask with streaming SSE response |
| `GET` | `/api/v1/chat/sessions/{doc_id}` | Get chat history |

**Chat example:**
```bash
curl -X POST http://localhost:8000/api/v1/chat/ \
  -H "Content-Type: application/json" \
  -d '{"document_id": "DOC_ID", "message": "Summarize this document"}'
```

**Streaming example:**
```bash
curl -N -X POST http://localhost:8000/api/v1/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"document_id": "DOC_ID", "message": "What topics are covered?"}'
```

#### Health

```bash
curl http://localhost:8000/api/v1/health
```

### Authentication

The API uses optional JWT Bearer tokens. Anonymous requests are supported with a `guest` identity.

To use auth:
```bash
# Get token (implement /auth/login endpoint or use the guest flow)
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/files/
```

## Testing

```bash
cd backend

# Run all tests with coverage report
pytest --cov=app --cov-report=term-missing

# Enforce 95% minimum coverage
pytest --cov=app --cov-fail-under=95

# Run a specific test class
pytest app/tests/test_api.py::TestChat -v
```

Coverage targets:
- API routes: 95%+
- Services (AI, file processor): 95%+
- Core (config, DB, security): 95%+

## CI/CD Pipeline

GitHub Actions runs on every push to `main`/`develop`:

1. **Backend Tests** — pytest with MongoDB service container, fails if coverage < 95%
2. **Frontend Tests** — `npm test` + production build validation
3. **Docker Build & Push** — builds and pushes images to DockerHub (main branch only)

### Required GitHub Secrets

| Secret | Description |
|--------|-------------|
| `OPENAI_API_KEY` | Your OpenAI API key |
| `DOCKERHUB_USERNAME` | DockerHub username |
| `DOCKERHUB_TOKEN` | DockerHub access token |

## Bonus Features Implemented

- ✅ **Real-time streaming** via Server-Sent Events (SSE)
- ✅ **JWT authentication** (Bearer token)
- ✅ **Redis** in Docker Compose (ready for rate limiting / caching)
- ✅ **Timestamp extraction** for audio/video with playback jump

## Deployment (AWS/GCP/Azure)

### AWS ECS (recommended)

```bash
# Push images
docker compose push

# Use AWS ECS with Fargate, point to DockerHub images
# Use MongoDB Atlas for managed database
# Use ElastiCache for Redis
```

### Environment variables for production

```env
OPENAI_API_KEY=sk-...
SECRET_KEY=<strong-random-key>
MONGODB_URL=mongodb+srv://user:pass@cluster.mongodb.net/docqa
REDIS_URL=redis://your-elasticache-endpoint:6379
```

## License

MIT
