# Erastus

Upload audio recordings of your RPG sessions, automatically transcribe them with Whisper, and generate structured AI summaries with campaign context awareness.

## Features

- **Audio upload** — drag-and-drop support for `.mp3`, `.wav`, `.m4a`, `.flac`, single or multiple files, and `.zip` archives (extracted and flattened automatically)
- **GPU-accelerated transcription** — faster-whisper with configurable models (`medium`, `large-v3`, `large-v3-turbo`). Multi-file sessions are interleaved by timestamp into one chronological transcript with speaker labels
- **AI summarization** — OpenAI-compatible API (DeepSeek, OpenRouter, etc.) with campaign context injection
- **Campaign management** — persistent context that improves future summaries as sessions accumulate, with AI-generated campaign context and session reordering
- **Rich text editor** — TipTap-based editor for reviewing and refining summaries
- **Real-time status** — WebSocket updates during processing with polling fallback
- **Dark/light theme**

## Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI, SQLAlchemy 2 (async), PostgreSQL |
| Task Queue | Celery, Redis |
| Transcription | faster-whisper (CTranslate2, CUDA) |
| Summarization | OpenAI-compatible chat completions API |
| Frontend | Next.js 16, React 19, TailwindCSS 4, TipTap |
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

The `Makefile` wraps the common workflows:

```bash
make up            # Start Postgres + Redis
make migrate       # Run Alembic migrations
make migration msg="description"  # Generate a new migration
make dev           # FastAPI backend on :8000
make dev-frontend  # Next.js frontend on :3000
make dev-worker    # Celery worker (requires GPU + local deps)
make logs          # Tail Docker Compose logs
```

Manually, the same steps are:

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
| `DATABASE_URL` | PostgreSQL connection (asyncpg) | `postgresql+asyncpg://rpg:rpg@localhost:5432/rpgsummary` |
| `REDIS_URL` | Redis connection | `redis://localhost:6379/0` |
| `CELERY_BROKER_URL` | Celery broker | `redis://localhost:6379/1` |
| `CELERY_RESULT_BACKEND` | Celery result backend | `redis://localhost:6379/2` |
| `UPLOAD_DIR` | Audio file storage directory | `./data/uploads` |
| `WHISPER_MODEL` | Whisper model size | `large-v3` |
| `WHISPER_DEVICE` | `cuda` or `cpu` | `cuda` |
| `WHISPER_COMPUTE_TYPE` | Precision | `float16` |
| `WHISPER_LANGUAGE` | Language code | `pt` |
| `LLM_API_BASE_URL` | OpenAI-compatible API base URL | — |
| `LLM_API_KEY` | API key | — |
| `LLM_MODEL` | Model name | — |
| `LLM_MAX_TOKENS` | Max output tokens | `32768` |
| `LLM_TEMPERATURE` | Generation temperature | `0.3` |
| `MAX_AUDIO_SIZE_MB` | Upload size limit | `2048` |
| `NEXT_PUBLIC_API_URL` | Backend URL used by the frontend | `http://localhost:8000` |

## Processing Pipeline

Audio upload triggers a Celery task chain:

1. **`process_session`** dispatches `transcribe_session` → `_dispatch_summarize` → `summarize_session`
2. **Transcription** uses faster-whisper; for multi-file uploads, segments from all files are interleaved by timestamp with speaker labels so the transcript reads as one chronological conversation
3. **Summarization** calls the configured OpenAI-compatible LLM
4. **Campaign context** aggregates all session summaries into `campaign.general_context`, injected into each new summary — so summaries improve as the campaign grows

Sessions move through a status state machine: `pending` → `transcribing` → `summarizing` → `ready` (any step can go to `error`). Failed sessions can be retried — processing resumes from the failed step, skipping transcription that already completed. Summaries can also be regenerated on demand from the UI.

## API

The backend exposes a REST API at `http://localhost:8000` with Swagger docs at `/docs`.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/campaigns` | List campaigns |
| POST | `/api/campaigns` | Create campaign |
| GET | `/api/campaigns/{id}` | Campaign detail + sessions |
| PUT | `/api/campaigns/{id}` | Update campaign |
| DELETE | `/api/campaigns/{id}` | Delete campaign |
| PUT | `/api/campaigns/{id}/sessions/reorder` | Reorder sessions in campaign |
| POST | `/api/campaigns/{id}/regenerate-context` | AI-generate campaign context |
| GET | `/api/sessions` | List sessions |
| POST | `/api/sessions` | Create session |
| GET | `/api/sessions/{id}` | Session detail + logs |
| PUT | `/api/sessions/{id}` | Update session (title, summary) |
| DELETE | `/api/sessions/{id}` | Delete session |
| POST | `/api/sessions/{id}/upload` | Upload audio files |
| POST | `/api/sessions/{id}/retry` | Retry failed processing |
| POST | `/api/sessions/{id}/regenerate` | Regenerate summary |
| GET | `/api/health` | Health check |
| WS | `/api/ws/sessions/{id}` | Real-time processing updates |

## Project Structure

```
backend/
  app/
    api/          # FastAPI endpoints
    models/       # SQLAlchemy ORM models
    schemas/      # Pydantic request/response schemas
    services/     # Business logic (transcriber, summarizer, storage, zip handling)
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
