# RPG Session Summary

Upload audio recordings of your RPG sessions, automatically transcribe them with Whisper, and generate structured AI summaries with campaign context awareness.

## Features

- **Audio upload** — drag-and-drop support for `.mp3`, `.wav`, `.m4a`, `.flac`, and `.zip` archives
- **GPU-accelerated transcription** — faster-whisper with configurable models (medium, large-v3, large-v3-turbo)
- **AI summarization** — OpenAI-compatible API (DeepSeek, OpenRouter, etc.) with campaign context injection
- **Rich text editor** — TipTap-based editor for reviewing and refining summaries
- **Campaign management** — persistent context that improves future summaries as sessions accumulate
- **Real-time status** — WebSocket updates during processing with polling fallback
- **Dark/light theme**

## Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI, SQLAlchemy 2 (async), PostgreSQL |
| Task Queue | Celery, Redis |
| Transcription | faster-whisper (CTranslate2, CUDA) |
| Summarization | OpenAI-compatible chat completions API |
| Frontend | Next.js 16, React 19, TailwindCSS, TipTap |
| Deployment | Docker Compose |

## Quick Start

### Prerequisites

- Docker & Docker Compose
- NVIDIA GPU + [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html) (for GPU transcription)
- An OpenAI-compatible API key (DeepSeek, OpenRouter, etc.)

### Setup

1. Clone and configure:
```bash
cp .env.example .env
# Edit .env — fill in LLM_API_BASE_URL, LLM_API_KEY, LLM_MODEL
```

2. Build and start:
```bash
docker compose up -d --build
```

3. Run database migrations:
```bash
docker compose exec backend alembic upgrade head
```

4. Open http://localhost:3000

### Without Docker (local development)

```bash
# Start infrastructure
docker compose up -d postgres redis

# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev

# Celery worker (separate terminal, requires local GPU + faster-whisper)
cd backend
source .venv/bin/activate
celery -A app.workers.celery_app worker --loglevel=info --concurrency=1
```

## Configuration

All settings are in `.env` (see `.env.example`):

| Variable | Description | Default |
|----------|-------------|---------|
| `WHISPER_MODEL` | Whisper model size | `large-v3` |
| `WHISPER_DEVICE` | `cuda` or `cpu` | `cuda` |
| `WHISPER_COMPUTE_TYPE` | Precision | `float16` |
| `WHISPER_LANGUAGE` | Language code | `pt` |
| `LLM_API_BASE_URL` | OpenAI-compatible API base URL | — |
| `LLM_API_KEY` | API key | — |
| `LLM_MODEL` | Model name | — |
| `LLM_MAX_TOKENS` | Max output tokens | `4096` |
| `LLM_TEMPERATURE` | Generation temperature | `0.3` |
| `MAX_AUDIO_SIZE_MB` | Upload size limit | `2048` |

## API

The backend exposes a REST API at `http://localhost:8000` with Swagger docs at `/docs`.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/campaigns` | List campaigns |
| POST | `/api/campaigns` | Create campaign |
| GET | `/api/campaigns/{id}` | Campaign detail + sessions |
| PUT | `/api/campaigns/{id}` | Update campaign |
| DELETE | `/api/campaigns/{id}` | Delete campaign |
| POST | `/api/campaigns/{id}/regenerate-context` | AI-generate campaign context |
| GET | `/api/sessions` | List sessions |
| POST | `/api/sessions` | Create session |
| GET | `/api/sessions/{id}` | Session detail + logs |
| PUT | `/api/sessions/{id}` | Update session (title, summary) |
| DELETE | `/api/sessions/{id}` | Delete session |
| POST | `/api/sessions/{id}/upload` | Upload audio files |
| POST | `/api/sessions/{id}/retry` | Retry failed processing |
| GET | `/api/health` | Health check |
| WS | `/api/ws/sessions/{id}` | Real-time processing updates |

## Project Structure

```
backend/
  app/
    api/          # FastAPI endpoints
    models/       # SQLAlchemy ORM models
    schemas/      # Pydantic request/response schemas
    services/     # Business logic (transcriber, summarizer, storage)
    workers/      # Celery tasks and event publishing
  alembic/        # Database migrations
  tests/          # pytest test suite

frontend/
  src/
    app/          # Next.js App Router pages
    components/   # React components (ui/, campaign/, session/, layout/)
    lib/          # API client, hooks, types
    providers/    # Theme provider
```

## License

MIT
