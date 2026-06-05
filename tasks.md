# Project Mnemonic — Senior Developer Task Breakdown

**Document Version:** 1.1  
**Date:** June 2026  
**Stack:** React 18 (JavaScript / JSX) · FastAPI (Python 3.11+) · Supabase · ChromaDB · Redis · Celery

---

## ⚠️ PRD Amendments (Minor Changes Applied)

The following small but critical gaps were identified and patched before task planning:

| # | Type | Change |
|---|------|--------|
| 1 | **Added** | **Redis + Celery** added explicitly to backend infrastructure. The PRD described async pipeline behavior without naming the mechanism. Celery + Redis is the standard Python solution for durable background job queues and SSE status streaming. |
| 2 | **Added** | **3 missing database tables** added to schema: `plates` (cluster registry), `memory_plates` (junction table for many-to-many), and `job_tracking` (required for real-time pipeline status updates). PRD described Plates as a feature but had no schema. |
| 3 | **Added** | **`thumbnail_storage_path` column** added to `user_memories`. The PRD wireframe clearly showed cover images on cards but the schema had no column for storing them. |
| 4 | **Clarified** | **Instagram post hyperlink** made an explicit UI requirement. PRD mentioned `source_url` vaguely — now explicit: stored as the original Instagram post URL, rendered as a clickable Instagram icon on every Reel card and detail panel. |
| 5 | **Added** | **`faster-whisper`** added as the default local Whisper engine (CTranslate2 optimized, near-zero cost). OpenAI Whisper API remains as the quality fallback. Controlled via `WHISPER_PROVIDER=local\|openai` env var. |
| 6 | **Added** | **Frame deduplication** step in video OCR pipeline. Sampling 1 frame/1.5s on a 5-minute reel = ~200 frames. Perceptual hash deduplication (skip frames with <5% pixel delta from prior) reduces vision API calls by ~60%. |
| 7 | **Changed** | **Frontend uses React 18 with JavaScript (JSX)** — not TypeScript. All frontend files use `.jsx` extension. |

---

## 📊 Project Summary

| Metric | Value |
|--------|-------|
| Total Tasks | 35 |
| Total Phases | 8 |
| Estimated Timeline | ~10–12 weeks (solo developer) |
| Frontend | React 18 · Vite · JavaScript JSX · Tailwind CSS |
| Backend | Python 3.11+ · FastAPI · Celery · Redis |
| Database | Supabase (PostgreSQL) · ChromaDB |
| Storage | Supabase Storage Buckets |
| AI Providers | OpenAI GPT-4o · faster-whisper · Ollama (Llama 3) |
| Deployment | Railway (backend) · Vercel (frontend) |

---

## Phase 1 — Foundation & Infrastructure Setup
> Estimated: ~6 developer days

---

### Task 01 — Monorepo & Project Scaffolding

**Priority:** 🔴 Critical  
**Estimate:** 1 day  
**Dependencies:** None

**Summary:**  
Initialize the entire project as a `pnpm` monorepo using Turborepo with three workspace packages: React frontend, FastAPI backend, and Chrome extension. Set up all tooling, linting, and CI skeleton before any feature work begins.

**Detailed Steps:**
- Create `pnpm-workspace.yaml` with packages: `apps/frontend`, `apps/backend`, `apps/extension`
- Configure `turbo.json` with `build`, `dev`, `lint`, `test` pipelines for parallel execution
- Create shared `.env.example` documenting every required environment variable:
  - `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`
  - `OPENAI_API_KEY`, `WHISPER_PROVIDER`, `WHISPER_MODEL`
  - `REDIS_URL`, `CHROMA_PERSIST_PATH`
  - `PROXY_LIST`, `OLLAMA_BASE_URL` (optional)
  - `VITE_API_BASE_URL`, `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`
- Configure **ESLint + Prettier** for JavaScript (no TypeScript) in `apps/frontend` and `apps/extension`
- Configure **Black + isort + flake8** for Python in `apps/backend` via `pyproject.toml`
- Add **Husky** pre-commit hooks with `lint-staged` (run linters only on staged files)
- Create **GitHub Actions CI** workflow: `.github/workflows/ci.yml` — runs lint + tests on every PR
- Write comprehensive `README.md` with architecture overview, local setup steps, env var reference

**Files Created:**
```
turbo.json
pnpm-workspace.yaml
.env.example
.gitignore
.github/workflows/ci.yml
README.md
apps/frontend/   (empty Vite scaffold)
apps/backend/    (empty FastAPI scaffold)
apps/extension/  (empty MV3 scaffold)
```

---

### Task 02 — Supabase Project Initialization & Auth

**Priority:** 🔴 Critical  
**Estimate:** 1.5 days  
**Dependencies:** Task 01

**Summary:**  
Configure the Supabase project with email/password and Google OAuth authentication, create all Storage buckets with correct policies, and wire up JWT validation middleware in FastAPI.

**Detailed Steps:**
- Create Supabase project, select nearest region for latency
- Enable **Email/Password** provider in Supabase Auth dashboard
- Configure **Google OAuth**: create Google Cloud OAuth 2.0 credentials, add authorized redirect URIs
- Install `@supabase/supabase-js` in frontend, `supabase` Python client in backend
- Write **FastAPI JWT middleware** (`backend/middleware/auth.py`):
  - Validate `Authorization: Bearer <token>` on every protected route
  - Use Supabase's public JWK endpoint to verify JWT signature
  - Extract `user_id` from `sub` claim, attach to `request.state.user_id`
- Create **Supabase Storage buckets** (all private):
  - `raw-media` — stores downloaded `.mp4` files
  - `thumbnails` — stores generated WebP cover images
  - `pdfs` — stores uploaded PDF files
  - `screenshots` — stores uploaded images
- Set bucket RLS policies: authenticated users can only read/write files under their own `{user_id}/` prefix
- Create frontend `src/contexts/AuthContext.jsx` with `useAuth()` hook: `{ user, session, signIn, signOut, signInWithGoogle }`
- Configure **CORS** in FastAPI: allow frontend origin, all standard HTTP methods and headers

**Files Created:**
```
apps/backend/middleware/auth.py
apps/frontend/src/contexts/AuthContext.jsx
apps/frontend/src/lib/supabase.js
supabase/config.toml
```

---

### Task 03 — Database Schema Migrations

**Priority:** 🔴 Critical  
**Estimate:** 1 day  
**Dependencies:** Task 02

**Summary:**  
Implement all six database tables (three from PRD + three new from PRD amendments) as version-controlled SQL migration files, with all required indexes and Row Level Security policies.

**Detailed Steps:**

**Migration 001 — `user_memories` table (extended from PRD):**
```sql
CREATE TABLE user_memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    content_type VARCHAR(50) NOT NULL,
    source_url TEXT,
    storage_path TEXT,
    thumbnail_storage_path TEXT,   -- NEW: cover image path
    creator_metadata JSONB DEFAULT '{}'::jsonb,
    raw_transcript TEXT,
    ocr_extracted_text TEXT,
    ai_summary JSONB DEFAULT '{}'::jsonb,
    indexed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Migration 002 — `entity_relationships` table (from PRD):**
```sql
CREATE TABLE entity_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_asset_id UUID REFERENCES user_memories(id) ON DELETE CASCADE,
    target_asset_id UUID REFERENCES user_memories(id) ON DELETE CASCADE,
    relationship_type VARCHAR(100) NOT NULL,
    weight REAL DEFAULT 1.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Migration 003 — `generated_learning_paths` table (from PRD):**
```sql
CREATE TABLE generated_learning_paths (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    topic_context VARCHAR(100) NOT NULL,
    syllabus_structure JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Migration 004 — `plates` table (NEW — PRD Amendment #2):**
```sql
CREATE TABLE plates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name VARCHAR(150) NOT NULL,
    centroid_member_ids JSONB DEFAULT '[]'::jsonb,
    item_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Migration 005 — `memory_plates` junction table (NEW):**
```sql
CREATE TABLE memory_plates (
    memory_id UUID REFERENCES user_memories(id) ON DELETE CASCADE,
    plate_id UUID REFERENCES plates(id) ON DELETE CASCADE,
    PRIMARY KEY (memory_id, plate_id)
);
```

**Migration 006 — `job_tracking` table (NEW — PRD Amendment #2):**
```sql
CREATE TABLE job_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    memory_id UUID REFERENCES user_memories(id) ON DELETE SET NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'QUEUED',
    current_stage VARCHAR(50),
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Indexes:**
```sql
-- Full-text search GIN index (from PRD)
CREATE INDEX idx_memories_text_search
  ON user_memories USING GIN(to_tsvector('english', COALESCE(raw_transcript,'') || ' ' || COALESCE(ocr_extracted_text,'')));

-- Performance indexes
CREATE INDEX idx_memories_user_created ON user_memories(user_id, created_at DESC);
CREATE INDEX idx_memories_content_type ON user_memories(content_type);
CREATE INDEX idx_memories_indexed ON user_memories(indexed);
CREATE INDEX idx_jobs_user_status ON job_tracking(user_id, status);
CREATE INDEX idx_plates_user ON plates(user_id);
```

**RLS Policies:**  
Enable RLS on all 6 tables. Each table gets a policy: `USING (user_id = auth.uid())`.

**Files Created:**
```
supabase/migrations/001_user_memories.sql
supabase/migrations/002_entity_relationships.sql
supabase/migrations/003_learning_paths.sql
supabase/migrations/004_plates.sql
supabase/migrations/005_memory_plates.sql
supabase/migrations/006_job_tracking.sql
```

---

### Task 04 — ChromaDB Setup & Embedding Service

**Priority:** 🔴 Critical  
**Estimate:** 1 day  
**Dependencies:** Task 01

**Summary:**  
Configure a persistent ChromaDB instance and build the `EmbeddingService` class used throughout the entire AI pipeline, supporting two interchangeable embedding providers.

**Detailed Steps:**
- Install `chromadb` package, configure `PersistentClient` pointing to `/data/chromadb` (Docker volume in production, local path in dev)
- Create `mnemonic_memories` collection with `cosine` distance metric
- Collection metadata schema: `user_id` (string), `content_type` (string), `created_at` (int unix timestamp), `plate_id` (string), `tags_csv` (string)
- Build `EmbeddingService` class (`backend/services/embedding_service.py`) with methods:
  - `embed_text(text: str) -> list[float]` — generate single embedding
  - `upsert_memory(id: str, text: str, metadata: dict)` — insert or update in ChromaDB
  - `query_similar(text: str, user_id: str, n: int = 20, filters: dict = {}) -> list[dict]`
  - `delete_memory(id: str)` — remove from ChromaDB
  - `get_by_ids(ids: list[str]) -> list[dict]` — batch fetch
- **Provider abstraction** via `EMBEDDING_PROVIDER` env var:
  - `openai` → `text-embedding-3-small` (1536 dimensions), batch up to 100 texts per API call
  - `local` → `sentence-transformers/all-MiniLM-L6-v2` (384 dims, runs fully local, free)
- Write unit tests for the full upsert → query → delete cycle
- Expose ChromaDB status in health check endpoint

**Files Created:**
```
apps/backend/services/embedding_service.py
apps/backend/tests/test_embedding_service.py
```

---

### Task 05 — FastAPI Backend Scaffolding & Middleware

**Priority:** 🔴 Critical  
**Estimate:** 1.5 days  
**Dependencies:** Tasks 02, 04

**Summary:**  
Build the complete FastAPI application skeleton: project structure, all middleware, Celery + Redis task queue setup, Pydantic v2 schemas, router registration, and health check endpoint.

**Detailed Steps:**
- **Project structure:**
  ```
  apps/backend/
  ├── main.py               # FastAPI app, lifespan, router registration
  ├── celery_app.py         # Celery app + Redis broker config
  ├── routers/
  │   ├── ingest.py         # /api/ingest/*
  │   ├── search.py         # /api/search
  │   ├── memories.py       # /api/memories/*
  │   ├── graph.py          # /api/graph
  │   ├── chat.py           # /api/chat
  │   ├── syllabus.py       # /api/syllabus
  │   └── jobs.py           # /api/jobs/*
  ├── services/             # Business logic
  ├── workers/              # Celery task definitions
  ├── schemas/              # Pydantic v2 models
  ├── middleware/           # Auth, request_id, logging
  └── utils/                # Helpers, constants
  ```
- **FastAPI lifespan handler**: startup — ping Supabase, ChromaDB, Redis; shutdown — graceful cleanup
- **Middleware stack** (in order): `CORSMiddleware`, `GZipMiddleware`, custom `RequestIDMiddleware` (generates UUID per request, attaches to logs)
- **Global exception handlers**: `HTTPException` → JSON, `RequestValidationError` → 422 with field details, custom `AppError` → structured error codes
- **Celery app** (`celery_app.py`): broker = `REDIS_URL`, result backend = `REDIS_URL`, task serializer = JSON
- **Main Celery task** (`workers/process_memory.py`): `process_memory_task(job_id, memory_id, content_type)` — master orchestrator that routes to correct processor chain
- **Celery Beat**: nightly re-clustering task registered in beat schedule
- **Pydantic v2 schemas**: `MemoryCard`, `MemoryDetail`, `SearchResult`, `JobStatus`, `ChatMessage`, `PlateSchema`, `SyllabusSchema`
- **Health check**: `GET /api/health` returns `{ api, database, chromadb, redis, celery_workers }` — used by Railway health probes

**Files Created:**
```
apps/backend/main.py
apps/backend/celery_app.py
apps/backend/routers/ (all 7 router files)
apps/backend/schemas/
apps/backend/middleware/request_id.py
```

---

## Phase 2 — Ingestion Layer
> Estimated: ~8 developer days

---

### Task 06 — File Upload & Storage Service

**Priority:** 🟠 High  
**Estimate:** 1.5 days  
**Dependencies:** Tasks 03, 05

**Summary:**  
Multi-part file upload endpoint accepting PDF, image (PNG/JPG/WebP), and raw MP4 files. Validates MIME type, uploads to Supabase Storage, creates database records, and dispatches the Celery pipeline.

**Detailed Steps:**
- `POST /api/ingest/file` — accept `multipart/form-data`, single field `file` (UploadFile)
- **MIME type validation** via `python-magic` (sniffs actual bytes, not file extension — prevents spoofing):
  - Allowed: `application/pdf`, `image/png`, `image/jpeg`, `image/webp`, `video/mp4`
- **File size limits**: PDF ≤ 50MB, Image ≤ 20MB, Video ≤ 500MB — reject with 413 if exceeded
- **Filename sanitization**: `slugify(original_name) + "_" + uuid4_short + ext`
- Upload raw file to correct Supabase bucket based on MIME type:
  - PDF → `pdfs/{user_id}/{sanitized_filename}`
  - Image → `screenshots/{user_id}/{sanitized_filename}`
  - Video → `raw-media/{user_id}/{sanitized_filename}`
- `INSERT` into `user_memories`: `user_id`, `content_type`, `storage_path`, `ai_summary={}`, `indexed=FALSE`
- `INSERT` into `job_tracking`: `user_id`, `memory_id`, `status='QUEUED'`, `current_stage='UPLOADED'`
- Fire Celery task: `process_memory_task.delay(job_id, memory_id, content_type)`
- Return **202 Accepted** immediately: `{ job_id, memory_id, status: "QUEUED" }` — do not wait for processing

**Files Created:**
```
apps/backend/routers/ingest.py
apps/backend/services/storage_service.py
apps/backend/schemas/ingest.py
```

---

### Task 07 — Instagram Reel Scraper Service

**Priority:** 🟠 High  
**Estimate:** 2 days  
**Dependencies:** Tasks 03, 05

**Summary:**  
Resilient Instagram Reel extractor using `yt-dlp` as the primary method and Playwright headless browser as fallback. Captures MP4 stream, cover thumbnail, creator handle, hashtags, and — critically — the **original post URL** for the frontend hyperlink.

**Detailed Steps:**
- `POST /api/ingest/url` — body: `{ url: str, content_type: "instagram_reel" }`
- Validate URL format via regex: must match `instagram.com/reel/` or `instagram.com/p/`
- **Primary extraction — yt-dlp:**
  ```python
  ydl_opts = {
      'format': 'best[height<=1080]',
      'quiet': True,
      'no_warnings': True,
      'cookiefile': INSTAGRAM_COOKIES_PATH,  # env-configured
  }
  ```
  Extract fields from `info_dict`:
  - `url` → direct MP4 stream URL
  - `thumbnail` → cover image URL
  - `uploader` / `uploader_id` → creator handle (`@handle`)
  - `description` → caption text (parse hashtags from this)
  - `webpage_url` → **original Instagram post URL** → stored in `source_url` (**PRD Amendment #4**)
- Download `.mp4` stream to temp file → upload to `raw-media/{user_id}/` Supabase bucket
- Download thumbnail image → upload to `thumbnails/{user_id}/` Supabase bucket
- Store `creator_metadata` JSONB: `{ "handle": "@...", "platform": "instagram", "profile_url": "..." }`
- **Fallback — Playwright**: if yt-dlp raises `DownloadError`, launch headless Chromium, load reel page, intercept XHR network requests to capture direct `.mp4` URL
- **Proxy rotation**: read `PROXY_LIST` env var (comma-separated proxy strings), rotate on HTTP 429 or 403 response using round-robin
- **Error handling**:
  - Private account → mark job FAILED with message "Account is private"
  - Deleted post → mark job FAILED with message "Content no longer available"
  - Rate limited (after all proxies exhausted) → retry with 60s backoff
- On success, fire `process_memory_task.delay(job_id, memory_id, "instagram_reel")`

**Files Created:**
```
apps/backend/services/scrapers/instagram_scraper.py
apps/backend/services/scrapers/base_scraper.py
```

---

### Task 08 — Web Article Scraper Service

**Priority:** 🟡 Medium  
**Estimate:** 1 day  
**Dependencies:** Task 05

**Summary:**  
Extract clean article body text and metadata from any web URL, with Playwright JS-rendering fallback for SPAs and React-based pages.

**Detailed Steps:**
- `POST /api/ingest/url` — body: `{ url: str, content_type: "web_page" }`
- **Primary extraction — `trafilatura`** (best-in-class main content extractor):
  ```python
  import trafilatura
  downloaded = trafilatura.fetch_url(url)
  text = trafilatura.extract(downloaded, include_comments=False, include_tables=True)
  metadata = trafilatura.extract_metadata(downloaded)
  ```
- **Fallback — Playwright + BeautifulSoup4**: launch headless Chromium, wait for `networkidle`, extract `document.body.innerHTML`, parse with BeautifulSoup, strip nav/footer/sidebar
- Metadata extraction: `og:title`, `og:author`, `article:published_time`, `og:image` URL
- Download `og:image` → upload to `thumbnails/{user_id}/` bucket
- Store clean article text in `raw_transcript` column
- **Failure modes**:
  - HTTP 403 → log warning, store URL + title only
  - Timeout (10s) → retry once with Playwright fallback
  - Paywall → store available teaser text with `[PAYWALL]` prefix
- Fire `process_memory_task.delay(job_id, memory_id, "web_page")`

**Files Created:**
```
apps/backend/services/scrapers/web_scraper.py
```

---

### Task 09 — Async Background Worker & Job Status SSE

**Priority:** 🔴 Critical  
**Estimate:** 1.5 days  
**Dependencies:** Task 05

**Summary:**  
The async backbone of the system. Celery worker orchestrates every processing stage, updating `job_tracking` at each step. A Server-Sent Events endpoint streams real-time progress to the frontend without polling.

**Detailed Steps:**

**Celery worker process** (`apps/backend/workers/process_memory.py`):
- `process_memory_task(job_id, memory_id, content_type)` — master task:
  1. Update `job_tracking.status = 'PROCESSING'`
  2. Route to sub-pipeline based on `content_type`:
     - `instagram_reel` / `mp4` → `[thumbnail, audio, transcription, ocr_video, synthesis, embedding, clustering, relationships]`
     - `pdf` → `[thumbnail, pdf_extract, synthesis, embedding, clustering, relationships]`
     - `image` → `[thumbnail, ocr_image, synthesis, embedding, clustering, relationships]`
     - `web_page` → `[thumbnail, synthesis, embedding, clustering, relationships]`
  3. Each stage calls `update_job_stage(job_id, stage_name)` before executing
  4. On `Exception`: mark `FAILED` + `error_message = str(e)`, trigger Sentry alert

**Job stages enum** (in order):
```
QUEUED → DOWNLOADING → THUMBNAIL → AUDIO_EXTRACT → TRANSCRIBING →
OCR_FRAMES → SYNTHESIZING → EMBEDDING → CLUSTERING → MAPPING_RELATIONS → COMPLETE
```

**SSE endpoint** (`routers/jobs.py`):
```python
@router.get("/api/jobs/{job_id}/stream")
async def stream_job_status(job_id: str, user=Depends(get_current_user)):
    async def event_generator():
        while True:
            job = await db.fetch_job(job_id, user.id)
            yield f"data: {job.model_dump_json()}\n\n"
            if job.status in ("COMPLETE", "FAILED"):
                break
            await asyncio.sleep(1.5)
    return EventSourceResponse(event_generator())
```

- On `COMPLETE`: emit final event including `memory_id` → frontend triggers card render
- On `FAILED`: emit error event with `error_message` → frontend shows retry button
- `GET /api/jobs/{job_id}` — one-time status poll (non-streaming fallback)
- **Celery retry policy**: `autoretry_for=(requests.Timeout, ConnectionError)`, `max_retries=3`, `retry_backoff=True`

**Files Created:**
```
apps/backend/workers/process_memory.py
apps/backend/routers/jobs.py
```

---

### Task 10 — Thumbnail & Cover Image Extraction

**Priority:** 🟠 High  
**Estimate:** 1 day  
**Dependencies:** Tasks 07, 08

**Summary:**  
Generate cover images for every content type to power the visual dashboard. All thumbnails are converted to WebP for bandwidth efficiency. This satisfies the PRD wireframe showing cover images on memory cards.

**Detailed Steps:**
- **Instagram Reel**: thumbnail already downloaded in Task 07 scraper — just convert to WebP
- **Uploaded MP4**: `ffmpeg -i input.mp4 -ss 00:00:01.000 -frames:v 1 thumb.jpg` (grab 1-second frame)
- **PDF**: `PyMuPDF (fitz)` — `page = doc[0]; pix = page.get_pixmap(matrix=fitz.Matrix(2,2)); pix.save("thumb.png")`
- **Uploaded Image**: `Pillow` — `img.thumbnail((600, 400), Image.LANCZOS)` (aspect ratio preserved)
- **Web Article**: download `og:image`, resize with Pillow to 600×400 max
- **WebP conversion** (applied to all): `img.save("output.webp", "WEBP", quality=85)`
- Upload to `thumbnails/{user_id}/{memory_id}.webp` in Supabase Storage
- `UPDATE user_memories SET thumbnail_storage_path = :path WHERE id = :memory_id`
- Generate **signed URL** (1-year expiry) and cache in Redis for frontend consumption

**Files Created:**
```
apps/backend/services/thumbnail_service.py
```

---

### Task 11 — PDF Text Extraction Pipeline

**Priority:** 🟠 High  
**Estimate:** 1 day  
**Dependencies:** Task 09

**Summary:**  
Extract text from both digital PDFs (text layer) and scanned PDFs (OCR fallback) with intelligent structure preservation for headers, code blocks, and numbered lists.

**Detailed Steps:**
- Open PDF with `fitz.open(filepath)`
- **Page type detection per page**:
  - `page.get_text("blocks")` returns content → digital PDF → use text layer extraction
  - Empty result → scanned page → render as Pixmap → `pytesseract.image_to_string()`
- **Digital PDF extraction**:
  - Extract `blocks` preserving reading order
  - Detect monospace font regions (by `fontname` containing "Mono", "Code", "Courier") → tag as code blocks
  - Detect tables via `fitz` v1.23+ `find_tables()` API → convert to pipe-separated text
  - Detect section headers (font size > body size threshold)
- **Large PDF handling** (>100 pages): process in 20-page chunks, concatenate results
- **Post-processing**: remove headers/footers (heuristic: very short text at page top/bottom edges), normalize whitespace, deduplicate blank lines
- Store full extracted text in `user_memories.raw_transcript`
- No audio processing for PDFs — pipeline continues directly to Synthesis (Task 15)

**Files Created:**
```
apps/backend/services/processors/pdf_processor.py
```

---

## Phase 3 — AI Processing Pipeline
> Estimated: ~9.5 developer days

---

### Task 12 — Audio Extraction & Whisper Transcription

**Priority:** 🔴 Critical  
**Estimate:** 1.5 days  
**Dependencies:** Tasks 09, 07

**Summary:**  
Extract audio from MP4 files and transcribe using `faster-whisper` locally (default, low-cost) or the OpenAI Whisper API (quality fallback). Stores a clean, timestamped transcript.

**Detailed Steps:**
- **Audio extraction via ffmpeg**:
  ```bash
  ffmpeg -i input.mp4 -ar 16000 -ac 1 -f wav output.wav
  ```
  `-ar 16000 -ac 1` = 16kHz mono WAV, optimal format for Whisper models
- Apply `loudnorm` ffmpeg filter for audio normalization (prevents poor accuracy on quiet recordings)
- **Provider routing** via `WHISPER_PROVIDER` env var:
  - `local` (default) → `faster-whisper` with model size from `WHISPER_MODEL=base.en|medium.en|large-v3`
    ```python
    from faster_whisper import WhisperModel
    model = WhisperModel(model_size, compute_type="int8")
    segments, info = model.transcribe(wav_path, language="en")
    ```
  - `openai` → `openai.audio.transcriptions.create(model="whisper-1", temperature=0)`
- **Post-processing**:
  - Join segments into a single string with space separators
  - Strip common filler words: "um", "uh", "like", "you know" (regex replacement)
  - Correct common tech term casing: `Npm` → `npm`, `Github` → `GitHub`, `Postgres` → `PostgreSQL`
- Store full transcript string in `user_memories.raw_transcript`
- Delete temp `.wav` file immediately after processing
- Log `audio_duration_seconds` vs `transcription_time_seconds` for performance monitoring

**Files Created:**
```
apps/backend/services/processors/audio_processor.py
apps/backend/services/transcription_service.py
```

---

### Task 13 — Video Keyframe Sampling & Visual OCR

**Priority:** 🟠 High  
**Estimate:** 2 days  
**Dependencies:** Tasks 09, 07

**Summary:**  
Sample one frame every 1.5 seconds from the video, apply perceptual hash deduplication to skip redundant frames (PRD Amendment #6), then batch-send to a vision LLM to extract on-screen code blocks, terminal commands, package names, and technical text.

**Detailed Steps:**
- **Frame extraction via ffmpeg**:
  ```bash
  ffmpeg -i input.mp4 -vf fps=2/3 frames/frame_%04d.jpg -q:v 3
  ```
  Produces ~1 frame per 1.5 seconds
- **Frame deduplication** (PRD Amendment #6):
  ```python
  import imagehash
  from PIL import Image
  prev_hash = None
  for frame_path in sorted(frame_files):
      h = imagehash.phash(Image.open(frame_path))
      if prev_hash and (h - prev_hash) < 8:   # hamming distance threshold
          os.remove(frame_path)                # skip near-identical frame
          continue
      prev_hash = h
  ```
  This reduces vision API calls by ~60% on typical screen-recording content
- **Batch vision API calls**: group 5 frames per API call (GPT-4o accepts multiple images per message)
- **Vision LLM system prompt**:
  ```
  You are an OCR engine specialized in technical content. For the provided video frames, extract:
  1. All code snippets (with language if identifiable)
  2. Terminal commands (npm, pip, docker, git, etc.)
  3. Package/library names and version numbers
  4. Configuration keys and values
  5. URLs visible on screen
  6. Function names, variable names, file paths
  Return ONLY valid JSON: { "extractions": [{ "frame_index": int, "code_blocks": [...], "commands": [...], "ui_text": string }] }
  ```
- Parse JSON response, collect and deduplicate code blocks + commands across all frames
- Merge all extracted text → compile `ocr_extracted_text` string
- Store in `user_memories.ocr_extracted_text`
- Cleanup entire temp frames directory after processing

**Files Created:**
```
apps/backend/services/processors/video_processor.py
apps/backend/services/vision_service.py
```

---

### Task 14 — Image & Screenshot OCR Service

**Priority:** 🟠 High  
**Estimate:** 1 day  
**Dependencies:** Task 09

**Summary:**  
Process uploaded screenshots and images through vision LLM for structural OCR targeting code, error messages, terminal output, and architecture diagrams. Uses `pytesseract` as a fast fallback for simple text-heavy images.

**Detailed Steps:**
- Load image with Pillow, check size: if file > 4MB → resize to 2048px on longest side (GPT-4o vision payload limit)
- Convert to base64 PNG for API transmission
- **Heuristic provider selection**:
  - If image appears to be an IDE/terminal screenshot, contains code-like patterns → **Vision LLM**
  - If image is mostly text (article screenshot, document photo) → **pytesseract** (faster, free)
  - Detection heuristic: run lightweight `pytesseract.image_to_osd()` to check orientation; if confidence > 80% → pytesseract; else → vision LLM
- **Vision LLM prompt** (when used):
  ```
  Analyze this screenshot and extract all visible content:
  - Error messages and stack traces
  - Code snippets and terminal commands
  - Configuration values and environment variables
  - Architecture diagram labels and descriptions
  Return JSON: { "description": str, "code_blocks": [...], "commands": [...], "error_messages": [...], "text_content": str }
  ```
- Merge all extracted text into `ocr_extracted_text` string
- No audio processing needed — pipeline routes directly to Synthesis

**Files Created:**
```
apps/backend/services/processors/image_processor.py
```

---

### Task 15 — Structured Synthesizer — AI Summary Engine

**Priority:** 🔴 Critical  
**Estimate:** 2 days  
**Dependencies:** Tasks 12, 13, 14, 11

**Summary:**  
The core AI brain. Combines all extracted text (transcript + OCR + metadata) and generates the structured `ai_summary` JSON containing abstract, takeaways, code blocks, tags, difficulty rating, and tech stack. This JSON powers every UI display.

**Detailed Steps:**
- **Input assembly**:
  ```python
  synthesis_input = f"""
  SOURCE: {content_type} from {source_url}
  CREATOR: {creator_handle}
  CAPTION/TITLE: {caption_or_title}
  TRANSCRIPT: {raw_transcript[:6000]}
  VISUAL OCR: {ocr_extracted_text[:2000]}
  HASHTAGS: {hashtags}
  """
  ```
- **Context window management**: if combined input > 8000 tokens → chunk transcript into 2000-token sections, summarize each with `gpt-4o-mini`, then meta-summarize all chunks with full model
- **System prompt** (stored in `prompts/synthesis_prompt.txt`):
  ```
  You are a technical knowledge extraction engine. Analyze the provided content and return ONLY valid JSON with no markdown fences.
  Required schema:
  {
    "title": "concise descriptive title (max 80 chars)",
    "abstract": "2-3 sentence summary focusing on core technical value",
    "takeaways": ["actionable bullet 1", "actionable bullet 2", ...],
    "code_blocks": [{"language": "bash", "code": "...", "description": "what it does"}],
    "tags": ["tag1", "tag2", ...],
    "difficulty": "beginner|intermediate|advanced",
    "tech_stack": ["React", "PostgreSQL", ...]
  }
  ```
- **LLM provider** via `LLM_PROVIDER` env var:
  - `openai` (default) → `gpt-4o` with `response_format={"type": "json_object"}`
  - `ollama` → `Llama3.1:8b` via local Ollama server at `OLLAMA_BASE_URL`
- **JSON validation**: parse with Pydantic model; if fails → retry once with stricter prompt `"Return ONLY the JSON object. No explanation. No markdown."`
- On second failure: store `{"title": "Processing Error", "abstract": "", ...}` with error flag, do NOT fail entire pipeline
- `UPDATE user_memories SET ai_summary = :validated_json, updated_at = NOW() WHERE id = :memory_id`
- Log `input_tokens + output_tokens` to cost monitoring

**Files Created:**
```
apps/backend/services/processors/synthesis_service.py
apps/backend/prompts/synthesis_prompt.txt
```

---

### Task 16 — Vector Embedding & ChromaDB Indexing

**Priority:** 🔴 Critical  
**Estimate:** 1 day  
**Dependencies:** Task 15

**Summary:**  
Generate vector embeddings from the compiled memory content and upsert to ChromaDB with full metadata. This is what makes semantic search possible.

**Detailed Steps:**
- **Build embedding input string** (per PRD ChromaDB spec, amended with title):
  ```python
  embedding_text = f"""
  {ai_summary.title} {creator_handle}
  SUMMARY ABSTRACT: {ai_summary.abstract}
  EXTRACTED KEY TAKEAWAYS: {' | '.join(ai_summary.takeaways)}
  TRANSCRIPT SYNTHESIS: {raw_transcript[:2000]}
  VISUAL TEXT CONTEXT: {ocr_extracted_text[:1000]}
  TECH STACK: {' '.join(ai_summary.tech_stack)}
  """
  ```
- Generate embedding via `EmbeddingService.embed_text(embedding_text)`
- **ChromaDB upsert**:
  ```python
  collection.upsert(
      ids=[memory_id],
      embeddings=[embedding_vector],
      documents=[embedding_text],
      metadatas=[{
          "user_id": user_id,
          "content_type": content_type,
          "created_at": int(created_at.timestamp()),
          "tags_csv": ",".join(ai_summary.tags),
          "tech_stack_csv": ",".join(ai_summary.tech_stack),
          "plate_id": ""  # filled in Task 17
      }]
  )
  ```
- `UPDATE user_memories SET indexed = TRUE, updated_at = NOW()`
- **Failure handling**: if ChromaDB unavailable → retry 3× with 5s backoff; if still failing → set `indexed = FALSE`, alert Sentry

**Files Created:**
```
apps/backend/services/embedding_service.py  (updated with upsert logic)
```

---

### Task 17 — Auto-Clustering (Plates) Engine

**Priority:** 🟠 High  
**Estimate:** 2 days  
**Dependencies:** Task 16

**Summary:**  
Automatically assign each newly indexed memory to a semantic Plate by comparing cosine similarity against existing plate centroids. Creates new plates when no match exceeds the threshold. Runs nightly re-clustering via Celery Beat.

**Detailed Steps:**
- **Triggered as chained Celery task** after Task 16 completes (`.si()` chain)
- Fetch all existing plates for this `user_id` from Supabase `plates` table
- For each plate: compute cosine similarity between new memory embedding and average of plate's `centroid_member_ids` embeddings
- **Assignment logic**:
  - If `max_similarity > 0.72` → assign to that plate
  - If no plate meets threshold → create new plate
- **New plate naming**: send top-5 `tech_stack` + `tags` of the new memory to LLM → return 2–3 word title (e.g., "React State Patterns", "Docker Networking")
- `INSERT INTO memory_plates (memory_id, plate_id)`
- `UPDATE plates SET item_count = item_count + 1`
- Update `centroid_member_ids` JSONB array (append new `memory_id`, keep max 50 most recent for centroid calculation)
- Update ChromaDB metadata for this memory: set `plate_id`
- **Nightly Celery Beat task** (`workers/recluster_task.py`):
  - For each user with >10 memories: fetch all user embeddings from ChromaDB
  - Run `sklearn.cluster.KMeans(n_clusters=int(sqrt(total_memories)))`
  - Reassign all memories to new cluster centroids
  - Update `plates` table names and `memory_plates` table assignments
  - Schedule: `0 2 * * *` (2am daily)

**Files Created:**
```
apps/backend/services/clustering_service.py
apps/backend/workers/recluster_task.py
```

---

## Phase 4 — Organization & Search
> Estimated: ~4.5 developer days

---

### Task 18 — Lexical Full-Text Search API

**Priority:** 🟠 High  
**Estimate:** 1 day  
**Dependencies:** Tasks 03, 05

**Summary:**  
PostgreSQL GIN-indexed full-text search for exact keyword, package name, and creator handle lookups. Returns match snippets with highlighted terms. Targets <100ms response time.

**Detailed Steps:**
- `GET /api/search?q=&mode=lexical&page=1&limit=20`
- **PostgreSQL query**:
  ```sql
  SELECT
    um.*,
    ts_rank(
      to_tsvector('english', COALESCE(raw_transcript,'') || ' ' || COALESCE(ocr_extracted_text,'')),
      plainto_tsquery('english', :q)
    ) AS rank,
    ts_headline(
      'english',
      COALESCE(raw_transcript,''),
      plainto_tsquery('english', :q),
      'MaxFragments=2,FragmentDelimiter=...'
    ) AS snippet
  FROM user_memories um
  WHERE user_id = :user_id
    AND indexed = TRUE
    AND to_tsvector('english', COALESCE(raw_transcript,'') || ' ' || COALESCE(ocr_extracted_text,''))
        @@ plainto_tsquery('english', :q)
  ORDER BY rank DESC, created_at DESC
  LIMIT :limit OFFSET :offset;
  ```
- Optional filter params: `content_type`, `plate_id`, `date_from`, `date_to`
- Return `MemoryCard` objects: `{ id, title (from ai_summary), abstract, thumbnail_url (signed URL), source_url, content_type, tags, snippet, rank }`
- Generate thumbnail signed URLs via Supabase Storage `create_signed_url(path, expires_in=3600)`
- Pagination: `LIMIT/OFFSET` + return `total_count` in `X-Total-Count` response header

**Files Created:**
```
apps/backend/routers/search.py
apps/backend/services/search_service.py
```

---

### Task 19 — Semantic Vector Search API

**Priority:** 🟠 High  
**Estimate:** 1 day  
**Dependencies:** Tasks 16, 05

**Summary:**  
Natural language semantic search using ChromaDB vector similarity. Finds conceptually related memories even when exact keywords are absent — e.g., "that video about plugging tools into AI" finds memories tagged `MCP`, `function calling`, `tool use`.

**Detailed Steps:**
- `GET /api/search?q=&mode=semantic`
- Generate query embedding: `EmbeddingService.embed_text(user_query)`
- ChromaDB query:
  ```python
  results = collection.query(
      query_embeddings=[query_vector],
      n_results=25,
      where={"user_id": user_id},
      include=["metadatas", "distances", "documents"]
  )
  ```
- Filter out results with `distance > 0.65` (cosine space — too dissimilar)
- Fetch full `user_memories` records from Supabase for returned IDs (batch fetch)
- Enrich with thumbnail signed URLs
- Return `MemoryCard` objects with `similarity_score = 1 - distance` attached
- Optional metadata filters passed to ChromaDB `where` clause: `content_type`, date range

**Files Created:**
```
apps/backend/services/search_service.py  (extended)
```

---

### Task 20 — Hybrid RRF Search Engine

**Priority:** 🟠 High  
**Estimate:** 1 day  
**Dependencies:** Tasks 18, 19

**Summary:**  
Combine lexical and semantic search results using Reciprocal Rank Fusion scoring into a single, optimally-ranked result list. This is the **default search mode**. Must meet the PRD's <400ms latency requirement.

**Detailed Steps:**
- `GET /api/search?q=` (mode defaults to `hybrid`)
- **Concurrent execution** using `asyncio.gather()` — both searches fire in parallel:
  ```python
  results_lex, results_sem = await asyncio.gather(
      lexical_search(q, user_id, limit=30),
      semantic_search(q, user_id, n=30)
  )
  ```
- **RRF scoring algorithm**:
  ```python
  k = 60  # constant per RRF paper
  rrf_scores = {}
  for rank, result in enumerate(results_lex):
      rrf_scores.setdefault(result.id, 0)
      rrf_scores[result.id] += 1 / (k + rank + 1)
  for rank, result in enumerate(results_sem):
      rrf_scores.setdefault(result.id, 0)
      rrf_scores[result.id] += 1 / (k + rank + 1)
  ```
- Sort all memory IDs by combined RRF score descending
- Fetch any memory details not already fetched in either result set
- Return top 20 unified `MemoryCard` results
- **Redis caching**: `SETEX search:{sha256(user_id+q)} 300 {json_results}` — 5 minute TTL
  - Invalidate on `COMPLETE` job for that user: `DEL search:{user_id}:*`
- **Response time target**: asyncio parallelism + Redis cache should hit <400ms consistently

**Files Created:**
```
apps/backend/services/search_service.py  (hybrid_search function)
```

---

### Task 21 — Entity Relationship Mapper (Knowledge Graph Edges)

**Priority:** 🟡 Medium  
**Estimate:** 1.5 days  
**Dependencies:** Tasks 16, 03

**Summary:**  
Automatically detect and store semantic relationships between memories to power the Knowledge Graph visualizer. Runs as the final step in every ingestion pipeline.

**Detailed Steps:**
- **Triggered as chained Celery task** after Task 17 (clustering) completes
- ChromaDB query: `collection.query(query_embeddings=[new_embedding], n_results=15, where={"user_id": user_id})`
- For each neighbor with `similarity > 0.75` (distance < 0.25):
  - **Determine `relationship_type`**:
    - `same_creator`: `creator_metadata.handle` matches exactly
    - `shares_technology`: `tech_stack` intersection count ≥ 2
    - `conceptual_link`: general semantic similarity (fallback)
  - `weight = round(1 - distance, 4)` (cosine similarity as float)
  - Prevent duplicates: `SELECT` both `(source→target)` and `(target→source)` before `INSERT`
  - `INSERT INTO entity_relationships (source_asset_id, target_asset_id, relationship_type, weight)`
- **Graph data endpoint**: `GET /api/graph`
  ```python
  # Returns:
  {
    "nodes": [{ "id", "title", "content_type", "thumbnail_url", "plate_id", "tags", "connection_count" }],
    "edges": [{ "source", "target", "relationship_type", "weight" }]
  }
  ```
- Limit initial load to 200 most-connected nodes (ordered by `connection_count DESC`)

**Files Created:**
```
apps/backend/services/graph_service.py
apps/backend/routers/graph.py
```

---

## Phase 5 — RAG Chat Engine
> Estimated: ~2 developer days

---

### Task 22 — Conversational RAG Chat Backend

**Priority:** 🟠 High  
**Estimate:** 2 days  
**Dependencies:** Tasks 19, 15

**Summary:**  
Full RAG pipeline with streaming. Retrieves the most relevant memories, injects them as context, streams the LLM response via SSE, and returns cited source memory IDs so the frontend can display clickable source chips.

**Detailed Steps:**
- `POST /api/chat` — body: `{ messages: [{ role, content }], user_message: str }`
- **Step 1 — Retrieval**: embed `user_message` → ChromaDB query top 6 memories (user-scoped)
- **Step 2 — Fetch full content**: batch fetch `user_memories` records from Supabase for top 6 IDs (include `ai_summary`, `raw_transcript`, `code_blocks`)
- **Step 3 — Context budget management**:
  - Token budget for context: 4000 tokens total
  - Allocation order: full `ai_summary` first (highest density info), then truncated `raw_transcript` sections
  - Use `tiktoken` to count tokens precisely; truncate to fit budget
- **Step 4 — Build system prompt**:
  ```
  You are the user's personal knowledge assistant. Answer questions using ONLY the memory sources provided below.
  After each factual claim, cite its source as [Memory Title].
  If the answer cannot be found in the sources, say: "I don't have that information in your saved memories."
  When providing code or commands, format them in code blocks.
  ```
- **Step 5 — Inject sources** as user message in structured XML-like format:
  ```xml
  <memory id="uuid-1" title="Docker Networking Reel">
    Abstract: ...
    Code: docker compose up -d ...
    Transcript: ...
  </memory>
  ```
- **Step 6 — Stream response via SSE**:
  ```python
  async def stream():
      async for chunk in openai_client.chat.completions.create(
          model="gpt-4o", messages=full_messages, stream=True
      ):
          token = chunk.choices[0].delta.content or ""
          yield f"data: {json.dumps({'token': token})}\n\n"
  ```
- **Step 7 — Source attribution**: on stream end, parse `[Memory Title]` citations from full response text, map titles back to memory IDs, emit final event: `{ "type": "sources", "data": [{ memory_id, title, thumbnail_url }] }`
- Conversation continuity: include last 4 message pairs in `messages` array for follow-up questions

**Files Created:**
```
apps/backend/routers/chat.py
apps/backend/services/rag_service.py
```

---

## Phase 6 — Frontend Development
> Estimated: ~9 developer days

---

### Task 23 — Frontend Setup, Design System & Routing

**Priority:** 🔴 Critical  
**Estimate:** 1.5 days  
**Dependencies:** Task 01

**Summary:**  
Bootstrap the React 18 + Vite + JavaScript (JSX) frontend with the exact PRD design system — cream backgrounds, editorial typography, fine borders, strictly no dark mode or saturated colors.

**Detailed Steps:**
- `npm create vite@latest frontend -- --template react` (JavaScript, not TypeScript)
- All files use `.jsx` extension — no `.tsx`, no TypeScript config
- **Tailwind CSS configuration** (`tailwind.config.js`):
  ```js
  module.exports = {
    content: ['./src/**/*.{js,jsx}'],
    darkMode: false,  // PRD: strictly prohibited
    theme: {
      extend: {
        colors: {
          'paper': '#FAF9F6',
          'paper-light': '#F5F5F0',
        },
        fontFamily: {
          sans: ['DM Sans', 'system-ui'],
          display: ['"DM Serif Display"', 'serif'],
        }
      }
    }
  }
  ```
- **CSS variables** in `src/index.css`: `--bg-primary`, `--bg-surface`, `--border-default`, `--text-primary`, `--text-secondary`, `--text-muted`
- **Typography**: DM Sans (body) + DM Serif Display (headings) from Google Fonts — strong editorial contrast per PRD
- **Base component library** (all custom, in `src/components/ui/`):
  - `Button.jsx` — variants: `primary` (black fill), `ghost` (transparent), `link`
  - `Input.jsx` — fine border, cream bg, focus ring
  - `Badge.jsx` — small pill, neutral-200 border
  - `Card.jsx` — white surface, border-neutral-200, no shadow
  - `Sheet.jsx` — slide-over panel, 550ms ease-out animation
  - `Spinner.jsx` — thin ring animation
  - `Toast.jsx` — minimal notification strip
- **React Router v6** routes:
  - `/` → redirect to `/dashboard`
  - `/auth` → `AuthPage.jsx`
  - `/dashboard` → `DashboardPage.jsx`
  - `/search` → `SearchPage.jsx`
  - `/memories/:id` → `MemoryDetailPage.jsx`
  - `/graph` → `GraphPage.jsx`
  - `/chat` → `ChatPage.jsx`
  - `/syllabus` → `SyllabusPage.jsx`
- **API client** (`src/lib/api.js`): Axios instance, `baseURL` from `VITE_API_BASE_URL`, request interceptor injects `Authorization: Bearer {supabase_session.access_token}`
- **React Query** `QueryClientProvider` with `staleTime: 60000`, `retry: 1`
- **Protected routes**: `ProtectedRoute.jsx` component — if no session, redirect to `/auth`

**Files Created:**
```
apps/frontend/tailwind.config.js
apps/frontend/src/router.jsx
apps/frontend/src/contexts/AuthContext.jsx
apps/frontend/src/lib/api.js
apps/frontend/src/lib/supabase.js
apps/frontend/src/components/ui/  (all base components)
apps/frontend/src/components/layout/AppLayout.jsx
apps/frontend/src/components/layout/Sidebar.jsx
```

---

### Task 24 — Authentication Pages

**Priority:** 🟠 High  
**Estimate:** 0.5 day  
**Dependencies:** Task 23

**Summary:**  
Clean minimal login and signup pages consistent with the cream editorial aesthetic. Supabase Auth handles all auth state.

**Detailed Steps:**
- `src/pages/AuthPage.jsx` — tab switch between Login and Signup
- **Design**: centered card on `#FAF9F6`, `border border-neutral-200`, zero box-shadow (per PRD)
- **Mnemonic wordmark** at top center — text-based, bold display font, no icon dependency
- **Login form**: email input, password input, "Sign In" button (`bg-neutral-900 text-white`)
- **Google OAuth button**: "Continue with Google" with inline Google SVG icon
- **Signup form**: display name + email + password
- **Form validation**: inline error messages below each field (`text-red-600 text-sm`), no alert boxes
- **Loading state**: replace button text with `Spinner` component, disable button during request
- **Supabase integration**:
  ```jsx
  const { error } = await supabase.auth.signInWithPassword({ email, password });
  const { error } = await supabase.auth.signInWithOAuth({ provider: 'google' });
  ```
- Handle email confirmation redirect URL (`VITE_SITE_URL + /auth/confirm`)
- Redirect to `/dashboard` after successful auth (React Router `useNavigate`)

**Files Created:**
```
apps/frontend/src/pages/AuthPage.jsx
```

---

### Task 25 — Main Dashboard Page

**Priority:** 🔴 Critical  
**Estimate:** 2 days  
**Dependencies:** Tasks 23, 17, 18

**Summary:**  
The primary interface: Plates cluster row, recent memory card grid with cover images, Instagram hyperlinks, content type filters, and infinite scroll pagination.

**Detailed Steps:**

**Plates Row:**
- Horizontally scrollable row, each `PlateCard.jsx` shows:
  - Plate name (bold, truncated at 24 chars)
  - Item count (`X items`)
  - Micro-thumbnail mosaic (3 tiny thumbnails from that plate's memories)
- Click plate → sets `activePlateId` state → filters memories grid
- `GET /api/plates` — fetched via React Query on mount

**MemoryCard Component** (`src/components/MemoryCard.jsx`):
- Thumbnail/cover image (WebP, `object-cover`, aspect-ratio 16/9)
- **Instagram Reel cards**: reel cover image prominently shown, small Instagram SVG icon in top-right corner of thumbnail → `href={memory.source_url}` → `target="_blank" rel="noopener"` (PRD Amendment #4 — explicit hyperlink requirement)
- Content type icon badge: reel (play icon), pdf (document icon), image (photo icon), article (globe icon)
- Title from `ai_summary.title` (bold, 2 lines max, truncate with ellipsis)
- Abstract from `ai_summary.abstract` (2 lines, text-neutral-600, small)
- Tech stack badges: first 3 tags shown, `+N more` if over 3
- Relative timestamp: "2 hours ago", "3 days ago"

**Grid Layout:**
- CSS Grid: `grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4`
- **Infinite scroll**: `useInfiniteQuery`, `IntersectionObserver` on last card — triggers next page fetch
- Content type filter chips (horizontal row): All / Reels / PDFs / Images / Articles
  - Active chip: `border-b-2 border-neutral-900 font-semibold` (underline style, not filled)

**Loading & Empty States:**
- Loading skeleton: exact card shape (`animate-pulse bg-neutral-200`) — 6 skeleton cards
- Empty state: clean illustration (SVG lines only) + "Add your first memory" CTA button

**Files Created:**
```
apps/frontend/src/pages/DashboardPage.jsx
apps/frontend/src/components/MemoryCard.jsx
apps/frontend/src/components/PlateCard.jsx
apps/frontend/src/hooks/useMemories.js
```

---

### Task 26 — Ingestion UI — Add Content Panel

**Priority:** 🔴 Critical  
**Estimate:** 1.5 days  
**Dependencies:** Tasks 23, 06, 07, 09

**Summary:**  
The content addition experience: a sliding Sheet panel with URL paste and drag-and-drop file upload, showing real-time SSE pipeline progress with animated stage indicators.

**Detailed Steps:**

**Trigger:**
- Floating `+` button (bottom-right of dashboard) → opens `Sheet` component from right
- Also accessible from Sidebar icon

**Tab 1 — URL Input:**
- Text input: "Paste an Instagram Reel or web article URL"
- Auto-detection on paste: if URL matches `instagram.com` → set `content_type = instagram_reel`; else → `web_page`
- Detected type shown as small badge below input

**Tab 2 — File Upload:**
- `react-dropzone` drop zone: dashed border, cream background, file type icons
- File type hints: PDF, PNG, JPG, MP4
- File size preview after selection
- Click or drag to select

**Submission flow:**
```jsx
const { job_id, memory_id } = await api.post('/ingest/url', { url, content_type });
// or
const { job_id, memory_id } = await api.post('/ingest/file', formData);
openJobStream(job_id);
```

**Job Progress UI** (`src/hooks/useIngestionJob.js`):
- Opens `EventSource('/api/jobs/{job_id}/stream')`
- `currentStage` state drives vertical stepper UI:
  - 8 stage indicators with labels
  - Stage states: `pending` (gray hollow circle), `active` (pulsing blue ring), `done` (black filled check)
- On `COMPLETE`: close sheet after 1.5s, show toast "Memory saved ✓", new card animates into dashboard
- On `FAILED`: show red error stage with message, "Retry" button re-fires the POST

**Concurrent jobs:**
- Each job tracked in a `jobs` Map keyed by `job_id`
- Small badge on `+` FAB: shows count of in-progress jobs
- Multiple concurrent `EventSource` connections allowed

**Files Created:**
```
apps/frontend/src/components/AddContentPanel.jsx
apps/frontend/src/hooks/useIngestionJob.js
```

---

### Task 27 — Search Page & Results Display

**Priority:** 🟠 High  
**Estimate:** 1.5 days  
**Dependencies:** Tasks 20, 23

**Summary:**  
Full-featured search interface with hybrid search results, rich result cards, Instagram cover image display with hyperlinks, filter controls, and URL state persistence.

**Detailed Steps:**

**Search Bar:**
- Full-width at top, auto-focused on page load
- Debounced input: 300ms before triggering query
- Clear button (×) when query present
- Keyboard shortcut: `Cmd/Ctrl+K` from any page → focus search (global `keydown` listener)

**Search Mode Toggle:**
- Pill tabs: `Hybrid` | `Semantic` | `Keyword`
- `Hybrid` pre-selected by default

**SearchResultCard Component** (`src/components/SearchResultCard.jsx`):
- Larger than dashboard card — full-width list item style
- Left side: thumbnail image (160px fixed width, cover fit)
- **Instagram Reel results**: reel cover image + Instagram icon hyperlink to `source_url` (PRD Amendment #4)
- Right side: title (bold), abstract, highlighted `snippet` text (from `ts_headline`), tech badges, similarity score badge (for semantic mode), content type icon, timestamp
- Creator handle shown for Instagram content: `@handle` in muted text

**Filters:**
- Left sidebar (desktop) / top chips (mobile): Content Type, Date Range (last 7d / 30d / 90d / All), Plate, Difficulty
- Active filters shown as removable chips in results header

**State Management:**
- All query params synced to URL: `?q=drizzle&mode=hybrid&type=instagram_reel`
- Browser back button restores search state

**Loading & Empty States:**
- Skeleton: 4 result card shapes with pulse animation
- No results: "No memories found for '[query]'" + suggestion to add content

**Files Created:**
```
apps/frontend/src/pages/SearchPage.jsx
apps/frontend/src/components/SearchResultCard.jsx
apps/frontend/src/hooks/useSearch.js
```

---

### Task 28 — Memory Detail Split-View Panel

**Priority:** 🔴 Critical  
**Estimate:** 2 days  
**Dependencies:** Tasks 23, 25

**Summary:**  
The core reading experience. A sliding split-view panel with the original media on the left and AI-generated structured summary + copyable code blocks on the right. Instagram post hyperlink is prominently displayed.

**Detailed Steps:**

**Trigger & Layout:**
- Click `MemoryCard` → `Sheet` component slides in from right (full-height, 70% viewport width on desktop)
- On mobile: full-screen with top tab bar (Media / Summary / Transcript)
- CSS transition: `translate-x-0` → `translate-x-full` → `translate-x-0` with `550ms ease-out`

**Left Panel — Media Viewer:**
- **Instagram Reel**: HTML5 `<video controls>` with signed URL from Supabase Storage. Below video: "View Original on Instagram" button with Instagram SVG icon → `href={source_url}` → `target="_blank"` (**critical PRD Amendment #4 requirement**)
- **PDF**: `react-pdf` `Document` + `Page` components, page up/down navigation, zoom controls
- **Image**: full-res `<img>` with CSS pinch-zoom (touch-action: pinch-zoom)
- **Web Article**: rendered article body text with inline `<code>` styling

**Right Panel — AI Summary:**
- **Top metadata bar**: creator handle + platform icon, original date, `source_url` as hyperlink text (e.g., "instagram.com/reel/..."), content type badge
- **Abstract block**: `bg-neutral-50` card, 2–3 sentence summary
- **Key Takeaways**: numbered list, each takeaway on its own line with a subtle left border accent
- **Code Blocks** (`CodeBlock.jsx`):
  - `Prism.js` syntax highlighting
  - Language badge (top-right of block)
  - One-click copy button (clipboard icon → checkmark on success, resets after 2s)
  - Monospace font (`font-mono text-sm`)
- **Tech Stack badges**: row of `Badge` components
- **Difficulty indicator**: text badge — `Beginner` (green) / `Intermediate` (amber) / `Advanced` (red)
- **Full Transcript**: collapsible accordion at bottom — raw `raw_transcript` text, readable line-height, muted color

**Files Created:**
```
apps/frontend/src/components/MemoryDetailPanel.jsx
apps/frontend/src/components/CodeBlock.jsx
apps/frontend/src/pages/MemoryDetailPage.jsx
```

---

## Phase 7 — Advanced Features
> Estimated: ~8 developer days

---

### Task 29 — Knowledge Graph Visualizer

**Priority:** 🟡 Medium  
**Estimate:** 2.5 days  
**Dependencies:** Tasks 21, 23

**Summary:**  
Interactive force-directed graph built with D3.js v7 showing all memories as nodes with relationship edges. Clicking any node opens the Memory Detail Panel.

**Detailed Steps:**
- Fetch `GET /api/graph` → `{ nodes, edges }`
- Mount D3 force simulation on `<svg>` element via `useRef` + `useEffect`
- **Force simulation setup**:
  ```js
  d3.forceSimulation(nodes)
    .force("link", d3.forceLink(edges).id(d => d.id).distance(120))
    .force("charge", d3.forceManyBody().strength(-300))
    .force("center", d3.forceCenter(width / 2, height / 2))
    .force("collide", d3.forceCollide(30))
  ```
- **Node rendering**:
  - SVG circles, radius = `6 + (connection_count * 0.8)` (capped at 22px)
  - Fill color by `content_type` (muted editorial palette: reels=`#C4B5A5`, pdf=`#A8B5C4`, image=`#C4A8B5`, web=`#B5C4A8`)
  - Stroke: `border-neutral-300`, weight 1px
- **Node labels**: visible at zoom > 1.5x — SVG `<text>` elements, 10px, neutral-600, truncated at 22 chars
- **Edge rendering**:
  - SVG `<line>` elements, stroke opacity = `weight` (range 0.2–0.8)
  - `strokeDasharray`: `shares_technology` = solid, `conceptual_link` = `4,4`, `same_creator` = `2,6`
- **Interactions**:
  - `d3.zoom()`: scroll to zoom (0.3×–3×), drag to pan
  - Double-click node: `d3.zoomTo` fit that node's cluster
  - Single-click node: `setSelectedMemoryId(d.id)` → opens `MemoryDetailPanel`
  - Hover node: show tooltip (title, content_type, connection_count)
- **Plate overlay toggle**: button to show labeled convex hull polygons around plate groups (D3 `d3.polygonHull`)
- **Filter controls**: content type checkboxes, plate selector dropdown, relationship type toggles
- **Performance**: if `nodes.length > 150` → switch to Canvas renderer (faster than SVG at scale)

**Files Created:**
```
apps/frontend/src/pages/GraphPage.jsx
apps/frontend/src/components/KnowledgeGraph.jsx
```

---

### Task 30 — Conversational Chat UI

**Priority:** 🟠 High  
**Estimate:** 1.5 days  
**Dependencies:** Tasks 22, 23

**Summary:**  
Clean chat interface for the RAG engine with streaming token-by-token response display, inline source citation chips that link to Memory Detail panels, and conversation history.

**Detailed Steps:**

**Layout:**
- Full-height flex column: `messages scroll area (flex-1)` + `fixed input bar at bottom`
- Cream background (`#FAF9F6`) with thin top border separator

**Message Bubbles** (`src/components/ChatMessage.jsx`):
- User messages: right-aligned, `bg-neutral-900 text-white`, rounded corners, max-width 70%
- Assistant messages: left-aligned, `bg-white border border-neutral-200`, max-width 80%
- Streaming display: update message `content` state token-by-token as SSE `{ token }` events arrive
  ```jsx
  const es = new EventSource(`/api/chat`, { method: 'POST', ... });
  es.onmessage = (e) => {
    const { token, type, data } = JSON.parse(e.data);
    if (type === 'sources') setSources(data);
    else setMessages(prev => appendToken(prev, token));
  };
  ```

**Source Citation Chips:**
- Displayed below each assistant message after stream completes
- `SourceChip.jsx`: small card with 32px thumbnail + memory title (truncated)
- Click chip → opens `MemoryDetailPanel` for that `memory_id`

**Input Bar:**
- `<textarea>` auto-resizing (1–4 rows max), `rows={1}` default
- Enter key = send message (prevents default); Shift+Enter = newline
- Send button: paper-plane icon SVG, black fill, disabled during streaming

**Empty State:**
- Show 3–4 suggested prompts as clickable chips:
  - "What terminal commands have I saved?"
  - "Summarize my Docker notes"
  - "Show me React patterns I bookmarked"
  - "What are the setup steps from my MCP reel?"

**Error & Loading States:**
- Three animated dots (`...`) while awaiting first token from SSE
- "Connection lost — Retry" banner if SSE stream errors
- Clear conversation button in top bar (resets `messages` state)

**Files Created:**
```
apps/frontend/src/pages/ChatPage.jsx
apps/frontend/src/components/ChatMessage.jsx
apps/frontend/src/components/SourceChip.jsx
apps/frontend/src/hooks/useChat.js
```

---

### Task 31 — Generative Learning Path (Syllabus) Feature

**Priority:** 🟡 Medium  
**Estimate:** 2 days  
**Dependencies:** Tasks 15, 23

**Summary:**  
Multi-select memories from the dashboard, then generate an AI-ordered learning curriculum from the selected content. Displays as a visual timeline with objectives, estimated time per step, and progress checkboxes.

**Detailed Steps:**

**Backend** (`backend/routers/syllabus.py`):
- `POST /api/syllabus` — body: `{ memory_ids: [str], topic_title: str }`
- Fetch `ai_summary` for all selected memory IDs
- Build LLM prompt:
  ```
  You have {N} learning resources about "{topic_title}".
  Order them from foundational to advanced, grouping by prerequisite concept.
  For each step, write 2-3 learning objectives.
  Assign an estimated learning time in minutes.
  Return ONLY JSON:
  {
    "title": str,
    "steps": [{
      "order": int, "memory_id": str, "step_title": str,
      "objectives": [str], "estimated_minutes": int, "concept_group": str
    }]
  }
  ```
- Store in `generated_learning_paths` table
- `GET /api/syllabus` — list all syllabuses for user
- `GET /api/syllabus/{id}` — fetch specific syllabus with full step details

**Frontend** (`apps/frontend/src/pages/SyllabusPage.jsx`):
- **Multi-select mode**: "Select" button in dashboard toolbar → checkboxes appear on cards
- Selected count shown in floating action bar: "3 selected — Generate Learning Path"
- Topic title input in modal → submit → POST to API → navigate to `/syllabus/{id}`
- **Syllabus view**: vertical timeline using CSS border-left trick
  - Each step: card with memory thumbnail, step title, concept_group badge, objectives list, estimated time chip
  - Checkbox per step stored in `localStorage` keyed by `syllabus_{id}_step_{order}`
  - Click card → opens `MemoryDetailPanel` for that memory
- `GET /api/syllabus` list → show all generated syllabuses in a sidebar or separate index page

**Files Created:**
```
apps/backend/routers/syllabus.py
apps/backend/services/syllabus_service.py
apps/frontend/src/pages/SyllabusPage.jsx
apps/frontend/src/components/SyllabusStep.jsx
```

---

### Task 32 — Chrome Browser Extension (Manifest V3)

**Priority:** 🟡 Medium  
**Estimate:** 2 days  
**Dependencies:** Tasks 06, 08

**Summary:**  
Single-click browser extension (Chrome + Arc) for instantly capturing any web page URL or article text content to Mnemonic without leaving the current tab.

**Detailed Steps:**

**Manifest** (`extension/manifest.json`):
```json
{
  "manifest_version": 3,
  "name": "Mnemonic — Save to Memory",
  "version": "1.0.0",
  "permissions": ["activeTab", "storage", "scripting"],
  "action": { "default_popup": "popup.html" },
  "background": { "service_worker": "background.js" }
}
```

**Popup** (`extension/src/popup.jsx`):
- Vite + `@crxjs/vite-plugin` build (enables HMR during development)
- Shows current tab title (truncated at 50 chars) + favicon
- Two action buttons: "Save URL" and "Extract & Save Article"
- Auth check on mount: `chrome.storage.local.get(['supabase_token'])` — if absent, show "Connect Account" button → opens `{APP_URL}/auth?return=extension` in new tab
- On success → show animated checkmark + "Processing..." text

**Background Service Worker** (`extension/src/background.js`):
- Handles all `fetch()` calls (popup context can't make cross-origin requests in MV3)
- Listens for `chrome.runtime.onMessage` from popup:
  - `{ action: "SAVE_URL", url, content_type }` → `fetch(API + '/ingest/url', ...)`
  - `{ action: "SAVE_ARTICLE", url, bodyText }` → `fetch(API + '/ingest/file', formData with text/plain)`
- Polls `GET /api/jobs/{job_id}` every 2s, updates `chrome.action.setBadgeText` with in-progress count

**Content Script** (`extension/src/content.js`):
- Injected on demand when user clicks "Extract & Save Article"
- Extracts `document.body.innerText` and sends to background worker

**Build output**: `extension/dist/` → zip for Chrome Web Store submission  
Arc browser: same extension works natively (Arc uses Chrome engine)

**Files Created:**
```
apps/extension/manifest.json
apps/extension/src/popup.jsx
apps/extension/src/background.js
apps/extension/src/content.js
apps/extension/vite.config.js
```

---

## Phase 8 — Polish & Deployment
> Estimated: ~4 developer days

---

### Task 33 — Performance Optimization & Caching Layer

**Priority:** 🟡 Medium  
**Estimate:** 1.5 days  
**Dependencies:** All prior tasks

**Summary:**  
Achieve the PRD's <400ms search latency target and smooth UI performance via Redis caching, async DB pooling, frontend code splitting, lazy loading, and rate limiting.

**Detailed Steps:**

**Backend:**
- **Redis caching layer** (`backend/services/cache_service.py`):
  - `GET /api/memories` list: `SETEX memories:{user_id} 300 {json}`; invalidate on new `COMPLETE` job
  - Hybrid search results: `SETEX search:{sha256(user_id+query)} 300 {json}` — 5min TTL
  - Thumbnail signed URLs: `SETEX thumb:{storage_path} 3600 {signed_url}` — 1hr TTL
- **PostgreSQL**: run `EXPLAIN ANALYZE` on all heavy queries, add composite indexes where query plan shows sequential scans
- **Async DB**: migrate hot endpoints from `supabase-py` sync client to `asyncpg` connection pool (10-20 concurrent connections)
- **Rate limiting** via `slowapi`:
  - `GET /api/search` → 100 req/min per user
  - `POST /api/ingest/*` → 10 req/hour per user
  - `POST /api/chat` → 30 req/hour per user

**Frontend:**
- React Query: `staleTime: 60000`, `gcTime: 300000`, optimistic updates on new ingestion
- Image lazy loading: `loading="lazy"` on all `<img>` tags + `IntersectionObserver` for custom implementation
- Route-based code splitting:
  ```jsx
  const GraphPage = lazy(() => import('./pages/GraphPage'));
  const ChatPage = lazy(() => import('./pages/ChatPage'));
  ```
- Bundle analysis: `vite-bundle-visualizer` → ensure initial bundle < 200KB gzipped
- Preload critical fonts in `<head>`: `<link rel="preload" as="font">`

**Files Created:**
```
apps/backend/services/cache_service.py
apps/frontend/vite.config.js  (updated)
```

---

### Task 34 — Error Handling, Logging & Monitoring

**Priority:** 🟡 Medium  
**Estimate:** 1 day  
**Dependencies:** All prior tasks

**Summary:**  
Production-grade error handling with structured logging, Sentry monitoring, user-facing error states, and a health dashboard.

**Detailed Steps:**

**Backend:**
- **Loguru** structured JSON logging (`backend/utils/logger.py`):
  ```python
  logger.bind(request_id=request_id, user_id=user_id, stage=stage).info("Processing started")
  ```
- Request ID middleware: generate `uuid4()` per request → attach to all log lines for traceability
- **Sentry Python SDK**: `sentry_sdk.init(dsn=SENTRY_DSN)` — captures unhandled exceptions, tracks ingestion failures by `content_type` tag
- Failed Celery tasks: auto-report to Sentry with job metadata, mark job `FAILED`, user sees error in UI

**Frontend:**
- **Sentry React SDK**: `ErrorBoundary` wrapping all major route components
  ```jsx
  <Sentry.ErrorBoundary fallback={<ErrorFallback />}>
    <RouterProvider router={router} />
  </Sentry.ErrorBoundary>
  ```
- `ErrorFallback.jsx`: clean page with "Something went wrong" + reload button (matches cream aesthetic)
- **Toast notification system** (`src/components/Toast.jsx`): non-critical errors shown as dismissible strips — network timeouts, rate limit messages
- Failed job notification: visible error state in `AddContentPanel` with retry button
- **Health status page** (`GET /api/health`):
  ```json
  {
    "api": "ok",
    "database": "ok",
    "chromadb": "ok",
    "redis": "ok",
    "celery_workers": 2
  }
  ```

**Files Created:**
```
apps/backend/utils/logger.py
apps/backend/middleware/request_id.py
apps/frontend/src/components/ErrorBoundary.jsx
apps/frontend/src/components/ErrorFallback.jsx
```

---

### Task 35 — Production Deployment & CI/CD Pipeline

**Priority:** 🔴 Critical  
**Estimate:** 1.5 days  
**Dependencies:** All tasks

**Summary:**  
Deploy all services to production via Docker + Railway (backend) + Vercel (frontend) with automated CI/CD, environment management, and database backup configuration.

**Detailed Steps:**

**Dockerization:**
- `Dockerfile` (API):
  ```dockerfile
  FROM python:3.11-slim
  RUN apt-get update && apt-get install -y ffmpeg tesseract-ocr libmagic1
  WORKDIR /app
  COPY requirements.txt .
  RUN pip install --no-cache-dir -r requirements.txt
  COPY . .
  CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
  ```
- `Dockerfile.worker` (Celery): same base image, different `CMD`:
  ```dockerfile
  CMD ["celery", "-A", "celery_app", "worker", "--loglevel=info", "--concurrency=4"]
  ```
- `docker-compose.yml` for **local development**: `api` + `worker` + `redis` + `chromadb` services with hot-reload mounts

**Railway Deployment** (4 services):
- `api` service: `Dockerfile`, PORT=8000, `START_COMMAND=uvicorn main:app ...`
- `worker` service: `Dockerfile.worker`, no port exposure
- `redis` service: Redis addon from Railway marketplace
- `chromadb` service: `chromadb/chroma` Docker image, persistent volume mount at `/chroma/chroma`
- All environment variables injected from Railway dashboard — never committed to repo

**Vercel Deployment** (frontend):
- Connect Vercel project to GitHub repository
- Root directory: `apps/frontend`
- Build command: `pnpm build`
- Environment variables: `VITE_API_BASE_URL`, `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`
- Auto-deploy on push to `main`; preview deployments on all PRs

**GitHub Actions CI/CD** (`.github/workflows/deploy.yml`):
```yaml
on:
  push:
    branches: [main]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pnpm install
      - run: pnpm lint
      - run: pnpm test
  deploy:
    needs: test
    steps:
      - name: Deploy to Railway
        uses: bervProject/railway-deploy@main
        with: { railway_token: ${{ secrets.RAILWAY_TOKEN }} }
      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v25
        with: { vercel_token: ${{ secrets.VERCEL_TOKEN }} }
```

**Database & Infrastructure:**
- Supabase: enable **Point-in-Time Recovery** for database backups (requires Pro plan)
- Supabase: upgrade to **Pro plan** for Storage capacity (5GB included, vs 500MB free)
- Custom domain: configure DNS for Vercel (frontend) and Railway (API subdomain `api.yourdomain.com`)
- Supabase `SITE_URL` + `ADDITIONAL_REDIRECT_URLS` updated to production domain for OAuth

**Files Created:**
```
Dockerfile
Dockerfile.worker
docker-compose.yml
.github/workflows/deploy.yml
railway.toml
apps/frontend/.vercelignore
```

---

## 📋 Full Task Index

| # | Task | Phase | Priority | Estimate | Dependencies |
|---|------|-------|----------|----------|-------------|
| 01 | Monorepo & Project Scaffolding | Foundation | 🔴 Critical | 1 day | None |
| 02 | Supabase Project Initialization & Auth | Foundation | 🔴 Critical | 1.5 days | 01 |
| 03 | Database Schema Migrations | Foundation | 🔴 Critical | 1 day | 02 |
| 04 | ChromaDB Setup & Embedding Service | Foundation | 🔴 Critical | 1 day | 01 |
| 05 | FastAPI Backend Scaffolding & Middleware | Foundation | 🔴 Critical | 1.5 days | 02, 04 |
| 06 | File Upload & Storage Service | Ingestion | 🟠 High | 1.5 days | 03, 05 |
| 07 | Instagram Reel Scraper Service | Ingestion | 🟠 High | 2 days | 03, 05 |
| 08 | Web Article Scraper Service | Ingestion | 🟡 Medium | 1 day | 05 |
| 09 | Async Background Worker & Job Status SSE | Ingestion | 🔴 Critical | 1.5 days | 05 |
| 10 | Thumbnail & Cover Image Extraction | Ingestion | 🟠 High | 1 day | 07, 08 |
| 11 | PDF Text Extraction Pipeline | Ingestion | 🟠 High | 1 day | 09 |
| 12 | Audio Extraction & Whisper Transcription | AI Pipeline | 🔴 Critical | 1.5 days | 09, 07 |
| 13 | Video Keyframe Sampling & Visual OCR | AI Pipeline | 🟠 High | 2 days | 09, 07 |
| 14 | Image & Screenshot OCR Service | AI Pipeline | 🟠 High | 1 day | 09 |
| 15 | Structured Synthesizer — AI Summary Engine | AI Pipeline | 🔴 Critical | 2 days | 12, 13, 14, 11 |
| 16 | Vector Embedding & ChromaDB Indexing | AI Pipeline | 🔴 Critical | 1 day | 15 |
| 17 | Auto-Clustering (Plates) Engine | AI Pipeline | 🟠 High | 2 days | 16 |
| 18 | Lexical Full-Text Search API | Search | 🟠 High | 1 day | 03, 05 |
| 19 | Semantic Vector Search API | Search | 🟠 High | 1 day | 16, 05 |
| 20 | Hybrid RRF Search Engine | Search | 🟠 High | 1 day | 18, 19 |
| 21 | Entity Relationship Mapper | Search | 🟡 Medium | 1.5 days | 16, 03 |
| 22 | Conversational RAG Chat Backend | RAG Engine | 🟠 High | 2 days | 19, 15 |
| 23 | Frontend Setup, Design System & Routing | Frontend | 🔴 Critical | 1.5 days | 01 |
| 24 | Authentication Pages | Frontend | 🟠 High | 0.5 day | 23 |
| 25 | Main Dashboard Page | Frontend | 🔴 Critical | 2 days | 23, 17, 18 |
| 26 | Ingestion UI — Add Content Panel | Frontend | 🔴 Critical | 1.5 days | 23, 06, 07, 09 |
| 27 | Search Page & Results Display | Frontend | 🟠 High | 1.5 days | 20, 23 |
| 28 | Memory Detail Split-View Panel | Frontend | 🔴 Critical | 2 days | 23, 25 |
| 29 | Knowledge Graph Visualizer | Advanced | 🟡 Medium | 2.5 days | 21, 23 |
| 30 | Conversational Chat UI | Advanced | 🟠 High | 1.5 days | 22, 23 |
| 31 | Generative Learning Path (Syllabus) | Advanced | 🟡 Medium | 2 days | 15, 23 |
| 32 | Chrome Browser Extension (MV3) | Advanced | 🟡 Medium | 2 days | 06, 08 |
| 33 | Performance Optimization & Caching | Polish | 🟡 Medium | 1.5 days | All backend |
| 34 | Error Handling, Logging & Monitoring | Polish | 🟡 Medium | 1 day | All |
| 35 | Production Deployment & CI/CD Pipeline | Polish | 🔴 Critical | 1.5 days | All |

---

## ⏱ Timeline Estimate

| Phase | Tasks | Developer Days |
|-------|-------|---------------|
| Phase 1 — Foundation | 01–05 | ~6 days |
| Phase 2 — Ingestion | 06–11 | ~8 days |
| Phase 3 — AI Pipeline | 12–17 | ~9.5 days |
| Phase 4 — Search | 18–21 | ~4.5 days |
| Phase 5 — RAG Engine | 22 | ~2 days |
| Phase 6 — Frontend | 23–28 | ~9 days |
| Phase 7 — Advanced | 29–32 | ~8 days |
| Phase 8 — Polish & Deploy | 33–35 | ~4 days |
| **Total** | **35 tasks** | **~51 developer days ≈ 10–11 weeks** |

> Note: Phases 3, 4, and 6 have significant parallelism potential — AI pipeline backend and frontend scaffolding can be developed simultaneously after Phase 2 is complete.

---

*Document prepared by: Senior Developer Review*  
*Based on PRD v1.0 with amendments noted above*