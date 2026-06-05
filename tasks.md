# Project Mnemonic — Senior Developer Task Breakdown
**35 Tasks across 8 Phases | Estimated Timeline: ~10–12 weeks (solo) / ~5–6 weeks (2 devs)**

---

## ⚠️ PRD Amendment Notes (Minor Changes Applied)

The following small additions were made to the original PRD before task breakdown. No major architectural or vision changes were introduced.

| # | Type | Change |
|---|------|--------|
| 1 | **Added** | **Redis + Celery** explicitly added to backend infrastructure. PRD described async pipeline behavior but left the queue mechanism unspecified. Celery + Redis is the standard Python solution. |
| 2 | **Added** | **3 missing database tables** added to schema: `plates` (cluster registry), `memory_plates` (junction table), `job_tracking` (pipeline status — required for SSE streaming). PRD described Plates functionality but had no backing schema for it. |
| 3 | **Added** | **`thumbnail_storage_path` column** added to `user_memories`. PRD wireframe showed cover images on cards but the schema had no column to store the thumbnail path. |
| 4 | **Clarified** | **Instagram `source_url` as explicit hyperlink** — `source_url` now stores the original Instagram post URL, rendered as a clickable Instagram icon on memory cards and detail panels. Mentioned in passing in PRD but now an explicit UI requirement. |
| 5 | **Added** | **`faster-whisper`** as the primary local Whisper engine (CTranslate2-optimized, near-zero cost, runs fully locally). OpenAI Whisper API remains as quality fallback. Controlled via `WHISPER_PROVIDER` env var. |
| 6 | **Added** | **Frame deduplication** step in keyframe OCR pipeline. Sampling 1 frame/1.5s on a 5-min video yields ~200 frames, many near-identical. Perceptual hash deduplication (`imagehash`) reduces vision API calls by ~60%. |
| 7 | **Clarified** | **Proxy rotation spec** made concrete: Instagram scraper reads a `PROXY_LIST` env var (comma-separated proxy URLs) and rotates on 429/403 responses. PRD mentioned it vaguely. |

---

## Legend

```
Priority:  🔴 Critical   🟠 High   🟡 Medium
Phase:     Foundation → Ingestion → AI Pipeline → Search → RAG → Frontend → Advanced → Deploy
```

---

## Phase 1 — Foundation & Infrastructure Setup
> Establish the monorepo, cloud services, database schema, and backend scaffolding before any feature work begins.

---

### Task 1 — Monorepo & Project Scaffolding
**Phase:** 1 — Foundation
**Priority:** 🔴 Critical
**Estimate:** 1 day
**Dependencies:** None

**Tech Stack:** `pnpm` `Turborepo` `Git` `GitHub Actions` `ESLint` `Prettier` `Black` `isort`

**Summary:**
Initialize the entire project as a pnpm/Turborepo monorepo with three workspace packages: React frontend, FastAPI backend, and Chrome extension. Establish code quality tooling and CI scaffolding before any feature development.

**Implementation Steps:**
- Create `pnpm-workspace.yaml` with three packages: `apps/frontend`, `apps/backend`, `apps/extension`
- Configure `turbo.json` with pipeline tasks: `build`, `dev`, `lint`, `test`, `type-check`
- Create shared `.env.example` documenting every required environment variable with descriptions: `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `OPENAI_API_KEY`, `REDIS_URL`, `WHISPER_PROVIDER`, `LLM_PROVIDER`, `PROXY_LIST`, `EMBEDDING_PROVIDER`
- Configure **ESLint + Prettier** for TypeScript/JavaScript with `@typescript-eslint` rules
- Configure **Black + isort + flake8 + mypy** for Python via `pyproject.toml`
- Add **Husky** pre-commit hooks running `lint-staged` (only lint staged files for speed)
- Create **GitHub Actions CI** workflow: `.github/workflows/ci.yml` — triggers on every PR, runs lint + type-check + tests for both frontend and backend
- Write comprehensive `README.md` with: architecture diagram reference, local dev setup instructions, environment variable reference, service dependency list

**Key Files:**
```
turbo.json
pnpm-workspace.yaml
.env.example
.github/workflows/ci.yml
README.md
apps/frontend/package.json
apps/backend/pyproject.toml
apps/extension/package.json
```

---

### Task 2 — Supabase Project Initialization & Auth Configuration
**Phase:** 1 — Foundation
**Priority:** 🔴 Critical
**Estimate:** 1.5 days
**Dependencies:** Task 1

**Tech Stack:** `Supabase` `PostgreSQL` `JWT` `Google OAuth` `supabase-js` `supabase-py`

**Summary:**
Create the Supabase project, configure authentication providers (email/password + Google OAuth), set up Storage buckets with access policies, and implement JWT validation middleware for FastAPI. All subsequent tasks depend on having auth working.

**Implementation Steps:**
- Create Supabase project in the nearest available region for latency
- **Auth setup**: Enable Email/Password provider in Supabase Auth dashboard
- **Google OAuth**: Create Google Cloud OAuth 2.0 credentials, configure authorized redirect URIs in both Google Console and Supabase dashboard
- Install `supabase-js` in frontend (`apps/frontend`)
- Install `supabase` Python client in backend (`apps/backend`)
- **FastAPI JWT middleware**: `backend/middleware/auth.py` — validates `Authorization: Bearer <token>` on every protected route using Supabase's public JWK endpoint. Extracts `user_id` from JWT claims and attaches to request state
- **Storage buckets**: Create 4 private buckets in Supabase Storage: `raw-media`, `thumbnails`, `pdfs`, `screenshots`
- **Bucket policies**: Authenticated users may only read/write files under their own `{user_id}/` path prefix
- **React AuthContext**: `frontend/src/contexts/AuthContext.tsx` — provides `useAuth()` hook returning `{ user, session, signIn, signOut, signInWithGoogle, isLoading }`
- Configure CORS in FastAPI: allow frontend origin, all standard HTTP methods, Authorization header
- Write backend utility `get_current_user(token)` dependency for route injection

**Key Files:**
```
apps/backend/middleware/auth.py
apps/backend/utils/dependencies.py
apps/frontend/src/contexts/AuthContext.tsx
apps/frontend/src/lib/supabase.ts
supabase/config.toml
```

---

### Task 3 — Database Schema Migrations
**Phase:** 1 — Foundation
**Priority:** 🔴 Critical
**Estimate:** 1 day
**Dependencies:** Task 2

**Tech Stack:** `PostgreSQL` `Supabase Migrations` `SQL`

**Summary:**
Implement all 6 database tables (3 from original PRD + 3 new additions), all indexes, and full Row Level Security policies as version-controlled SQL migration files. This includes the `plates`, `memory_plates`, and `job_tracking` tables that were missing from the original PRD schema.

**Implementation Steps:**

**Migration 001 — user_memories** (original PRD table + thumbnail column addition):
```sql
CREATE TABLE user_memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    content_type VARCHAR(50) NOT NULL,
    source_url TEXT,                          -- stores original Instagram post URL
    storage_path TEXT,
    thumbnail_storage_path TEXT,              -- NEW: cover/thumbnail image path
    creator_metadata JSONB DEFAULT '{}',
    raw_transcript TEXT,
    ocr_extracted_text TEXT,
    ai_summary JSONB DEFAULT '{}',
    indexed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Migration 002 — entity_relationships** (knowledge graph edges):
```sql
CREATE TABLE entity_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_asset_id UUID REFERENCES user_memories(id) ON DELETE CASCADE,
    target_asset_id UUID REFERENCES user_memories(id) ON DELETE CASCADE,
    relationship_type VARCHAR(100) NOT NULL,
    weight REAL DEFAULT 1.0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Migration 003 — generated_learning_paths** (original PRD table, unchanged)

**Migration 004 — plates** (NEW — was missing from PRD):
```sql
CREATE TABLE plates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    name VARCHAR(100) NOT NULL,
    centroid_ids JSONB DEFAULT '[]',          -- array of member memory IDs for centroid calc
    item_count INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Migration 005 — memory_plates** (NEW — junction table):
```sql
CREATE TABLE memory_plates (
    memory_id UUID REFERENCES user_memories(id) ON DELETE CASCADE,
    plate_id UUID REFERENCES plates(id) ON DELETE CASCADE,
    PRIMARY KEY (memory_id, plate_id)
);
```

**Migration 006 — job_tracking** (NEW — required for SSE pipeline status):
```sql
CREATE TABLE job_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    memory_id UUID REFERENCES user_memories(id),
    status VARCHAR(30) DEFAULT 'QUEUED',
    current_stage VARCHAR(60),
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Indexes:**
- `GIN` index on `to_tsvector('english', raw_transcript || ' ' || ocr_extracted_text)` for full-text search
- `BTREE` index on `user_memories(user_id, created_at DESC)` for dashboard queries
- `BTREE` index on `user_memories(content_type)` for type filtering
- `BTREE` index on `job_tracking(user_id, status)` for active job polling

**Row Level Security:**
- Enable RLS on all 6 tables
- Policy on each: `USING (user_id = auth.uid())` for SELECT/UPDATE/DELETE
- Policy for INSERT: `WITH CHECK (user_id = auth.uid())`

**Key Files:**
```
supabase/migrations/001_user_memories.sql
supabase/migrations/002_entity_relationships.sql
supabase/migrations/003_learning_paths.sql
supabase/migrations/004_plates.sql
supabase/migrations/005_memory_plates.sql
supabase/migrations/006_job_tracking.sql
```

---

### Task 4 — ChromaDB Setup & Embedding Service Foundation
**Phase:** 1 — Foundation
**Priority:** 🔴 Critical
**Estimate:** 1 day
**Dependencies:** Task 1

**Tech Stack:** `ChromaDB` `Python` `sentence-transformers` `OpenAI Embeddings API`

**Summary:**
Configure a persistent ChromaDB instance and build the `EmbeddingService` class with provider abstraction supporting both OpenAI and local sentence-transformers. This service is used throughout the AI pipeline.

**Implementation Steps:**
- Install `chromadb` with `PersistentClient` configured to store data at `/data/chromadb` (will be a Docker volume in production)
- Create `mnemonic_memories` collection with **cosine distance** metric
- Define collection metadata schema enforced on every upsert: `user_id` (string), `content_type` (string), `created_at` (unix int), `plate_id` (string, nullable), `tags_csv` (string), `tech_stack_csv` (string)
- Build `EmbeddingService` class with these public methods:
  - `embed_text(text: str) -> list[float]` — generates embedding vector
  - `upsert_memory(id: str, text: str, metadata: dict) -> None`
  - `query_similar(query_text: str, user_id: str, n: int = 20, filters: dict = {}) -> list[dict]`
  - `delete_memory(id: str) -> None`
  - `get_by_ids(ids: list[str]) -> list[dict]`
- **Provider abstraction**: `EMBEDDING_PROVIDER=openai` → uses `text-embedding-3-small` (1536 dims, $0.02/1M tokens); `EMBEDDING_PROVIDER=local` → uses `sentence-transformers/all-MiniLM-L6-v2` (384 dims, free, runs locally)
- Batch embedding support: accept up to 100 texts per API call to reduce overhead
- ChromaDB **health check** function used by the `/api/health` endpoint
- Unit tests covering full cycle: upsert → query → verify result → delete → verify gone

**Key Files:**
```
apps/backend/services/embedding_service.py
apps/backend/tests/test_embedding_service.py
```

---

### Task 5 — FastAPI Backend Scaffolding & Celery/Redis Infrastructure
**Phase:** 1 — Foundation
**Priority:** 🔴 Critical
**Estimate:** 1.5 days
**Dependencies:** Tasks 2, 4

**Tech Stack:** `FastAPI` `Python 3.11+` `Celery` `Redis` `Pydantic v2`

**Summary:**
Build the complete FastAPI application structure: project layout, all routers, middleware stack, Celery task queue wired to Redis, global error handling, and all Pydantic v2 schema definitions. This is the backbone every other backend task plugs into.

**Implementation Steps:**
- **Project structure:**
  ```
  apps/backend/
  ├── main.py
  ├── celery_app.py
  ├── routers/          (ingest, search, memories, graph, chat, syllabus, jobs)
  ├── services/         (storage, embedding, search, rag, graph, clustering)
  ├── workers/          (process_memory, recluster)
  ├── processors/       (audio, video, image, pdf, synthesis)
  ├── scrapers/         (instagram, web)
  ├── schemas/          (all Pydantic models)
  ├── middleware/       (auth, request_id, logging)
  ├── utils/            (dependencies, logger, cache)
  └── tests/
  ```
- **FastAPI lifespan handler** (`@asynccontextmanager`): on startup → ping Supabase, ChromaDB, Redis; log service status. On shutdown → graceful cleanup of connections
- **Middleware stack** (applied in order): `CORSMiddleware`, `GZipMiddleware`, custom `RequestIDMiddleware` (attaches UUID to every request for log tracing)
- **Global exception handlers**: `HTTPException` → JSON error response; `RequestValidationError` → 422 with field details; custom `AppError` → structured error with `code`, `message`, `details`
- **Celery setup** (`celery_app.py`): broker = `REDIS_URL`, results backend = `REDIS_URL`, task serializer = `json`
- **Main Celery task**: `process_memory_task(job_id: str, memory_id: str, content_type: str)` — the orchestrator that routes to the correct processor chain
- **Celery Beat** scheduler: nightly re-clustering task at 03:00 UTC
- **Pydantic v2 schemas** (define all now to avoid refactoring later): `MemoryCard`, `MemoryDetail`, `SearchResult`, `JobStatus`, `ChatMessage`, `IngestURLRequest`, `IngestFileResponse`, `PlateCard`, `GraphNode`, `GraphEdge`, `SyllabusStep`
- **Router registration** under `/api/v1/` prefix: ingest, search, memories, graph, chat, syllabus, jobs
- `GET /api/health` returns `{ api: "ok", database: "ok", chromadb: "ok", redis: "ok", celery_workers: N }`

**Key Files:**
```
apps/backend/main.py
apps/backend/celery_app.py
apps/backend/routers/
apps/backend/schemas/models.py
apps/backend/middleware/
```

---

## Phase 2 — Ingestion Layer
> Build all the pathways through which content enters the system: file uploads, Instagram scraping, web article extraction, async job orchestration, thumbnail generation, and PDF parsing.

---

### Task 6 — File Upload & Storage Service
**Phase:** 2 — Ingestion
**Priority:** 🟠 High
**Estimate:** 1.5 days
**Dependencies:** Tasks 3, 5

**Tech Stack:** `FastAPI` `Supabase Storage` `python-magic` `Pydantic v2`

**Summary:**
Multi-part file upload endpoint that accepts PDF, image (PNG/JPG/WebP), and MP4 files. Validates MIME types (not just extensions), uploads raw files to Supabase Storage, creates database records, and dispatches the async processing pipeline.

**Implementation Steps:**
- `POST /api/v1/ingest/file` — accepts `multipart/form-data` with `UploadFile`
- **MIME validation** via `python-magic` (reads actual file bytes, not extension — prevents spoofing):
  - Allowed: `application/pdf`, `image/png`, `image/jpeg`, `image/webp`, `video/mp4`
  - Reject all others with `422 Unsupported Media Type`
- **File size enforcement**: PDF ≤ 50MB, Image ≤ 20MB, Video ≤ 500MB (checked before upload)
- **Filename sanitization**: `slugify(original_name) + "_" + uuid4()[:8] + ext` — strips special characters and prevents path traversal
- Upload raw file to correct Supabase Storage bucket:
  - `pdfs/{user_id}/{safe_filename}` for PDFs
  - `screenshots/{user_id}/{safe_filename}` for images
  - `raw-media/{user_id}/{safe_filename}` for MP4
- `INSERT` into `user_memories`: set `user_id`, `content_type`, `storage_path`, `status='PENDING'`
- `INSERT` into `job_tracking`: set `user_id`, `memory_id`, `status='QUEUED'`, `current_stage='UPLOADED'`
- Fire Celery task: `process_memory_task.delay(job_id, memory_id, content_type)`
- Return **202 Accepted immediately** (optimistic): `{ job_id, memory_id, status: "QUEUED" }`

**Key Files:**
```
apps/backend/routers/ingest.py
apps/backend/services/storage_service.py
apps/backend/schemas/models.py (IngestFileResponse)
```

---

### Task 7 — Instagram Reel Scraper Service
**Phase:** 2 — Ingestion
**Priority:** 🟠 High
**Estimate:** 2 days
**Dependencies:** Tasks 3, 5

**Tech Stack:** `yt-dlp` `Playwright` `Python` `Supabase Storage`

**Summary:**
Resilient Instagram Reel scraper that extracts the MP4 stream, cover thumbnail, creator handle, original post URL (for the hyperlink), and hashtags. Uses yt-dlp as primary with Playwright headless browser as fallback. Implements proxy rotation per the PRD safeguard requirement.

**Implementation Steps:**
- `POST /api/v1/ingest/url` with body `{ url: str, content_type: "instagram_reel" }`
- Validate URL matches pattern `instagram.com/reel/*` or `instagram.com/p/*`; reject others with `400`
- **Primary extraction — yt-dlp:**
  - Configure with `--cookies-from-browser chromium` or a saved `cookies.txt` file for auth bypass
  - `yt_dlp.YoutubeDL({'quiet': True}).extract_info(url, download=False)` to get metadata first
  - Fields to capture: `url` (mp4 stream), `thumbnail` (cover image URL), `uploader` (creator handle), `description` (caption + hashtags), `webpage_url` (original post URL — store in `source_url`)
  - Download `.mp4` stream to temp directory, then stream-upload to `raw-media/{user_id}/` Supabase bucket
  - Download thumbnail image to temp directory, then upload to `thumbnails/{user_id}/` Supabase bucket
- **Fallback — Playwright:**
  - Launch headless Chromium, navigate to Reel URL
  - Intercept network requests for `.mp4` content URL via `page.on("response", handler)`
  - Screenshot the thumbnail from the video element
- **Proxy rotation** (per PRD safeguard, now concrete): read `PROXY_LIST` env var (comma-separated proxies), rotate on `429`/`403` response, implement exponential backoff (1s, 2s, 4s)
- **Error handling**:
  - Private account → `DownloadError` → mark job `FAILED` with message "Account is private"
  - Deleted/404 post → mark job `FAILED` with message "Post no longer available"
  - Rate limit exhausted (all proxies blocked) → mark job `FAILED`, retry after 1 hour via Celery ETA
- Store `source_url = webpage_url` (the original Instagram post URL) in `user_memories` for frontend hyperlink
- Store `creator_metadata = { handle, platform: "instagram", profile_url }`
- Create `user_memories` + `job_tracking` records, fire `process_memory_task.delay(...)`

**Key Files:**
```
apps/backend/scrapers/instagram_scraper.py
apps/backend/scrapers/base_scraper.py
```

---

### Task 8 — Web Article Scraper Service
**Phase:** 2 — Ingestion
**Priority:** 🟡 Medium
**Estimate:** 1 day
**Dependencies:** Task 5

**Tech Stack:** `trafilatura` `Playwright` `BeautifulSoup4` `Python`

**Summary:**
Extract clean article body text and metadata from any web URL. Uses `trafilatura` as the primary extractor (best-in-class for main content extraction) with Playwright as fallback for JavaScript-rendered pages.

**Implementation Steps:**
- `POST /api/v1/ingest/url` with body `{ url: str, content_type: "web_page" }`
- **Primary extraction — trafilatura:**
  - `trafilatura.fetch_url(url)` with timeout 10s
  - `trafilatura.extract(downloaded, include_comments=False, include_tables=True)` for clean body text
  - `trafilatura.extract_metadata(downloaded)` for: `title`, `author`, `date`, `sitename`
- **Fallback — Playwright** (for SPA/JS-heavy pages where trafilatura returns empty):
  - Headless Chromium, `page.goto(url, wait_until="networkidle")`
  - `BeautifulSoup4` parse of `page.content()`, select `<article>` or `<main>` elements
- **OG image extraction**: parse `<meta property="og:image">` from page head; download image → upload to `thumbnails/{user_id}/` Supabase bucket
- Store article text in `raw_transcript`
- **Error handling**: 403 → log warning, store URL + metadata only; timeout → retry once; paywall detected (short content < 200 chars) → store what's available with a `paywall_detected: true` flag in `creator_metadata`
- Create `user_memories` + `job_tracking`, fire Celery task (no audio processing branch for web articles)

**Key Files:**
```
apps/backend/scrapers/web_scraper.py
```

---

### Task 9 — Async Background Worker & Job Status SSE
**Phase:** 2 — Ingestion
**Priority:** 🔴 Critical
**Estimate:** 1.5 days
**Dependencies:** Task 5

**Tech Stack:** `Celery` `Redis` `FastAPI` `Server-Sent Events`

**Summary:**
The async backbone of the entire system. The Celery worker orchestrates the ingestion pipeline and updates `job_tracking` at each stage. A FastAPI SSE endpoint streams live status updates to the frontend so the user sees real-time progress.

**Implementation Steps:**
- Celery worker process runs separately from FastAPI (different `CMD` in Docker)
- **`process_memory_task` orchestration**:
  - Reads `content_type` → routes to correct processor chain:
    - `instagram_reel` / `video`: thumbnail → audio extraction → transcription → OCR frames → synthesis → embedding → clustering
    - `pdf`: thumbnail → PDF text extraction → synthesis → embedding → clustering
    - `image`: thumbnail → image OCR → synthesis → embedding → clustering
    - `web_page`: (thumbnail already extracted by scraper) → synthesis → embedding → clustering
  - Each stage transition calls `update_job_stage(job_id, stage_name)` helper
- **`update_job_stage` helper**: `UPDATE job_tracking SET current_stage=:stage, updated_at=NOW() WHERE id=:job_id`
- **Pipeline stage names** (in order): `QUEUED` → `DOWNLOADING` → `GENERATING_THUMBNAIL` → `EXTRACTING_AUDIO` → `TRANSCRIBING` → `OCR_FRAMES` → `SYNTHESIZING` → `EMBEDDING` → `CLUSTERING` → `COMPLETE`
- **FastAPI SSE endpoint**: `GET /api/v1/jobs/{job_id}/stream` (auth required)
  - Returns `text/event-stream` content type
  - Every 1.5s: query `job_tracking` for current stage/status → emit `data: { stage, status, progress_pct }\n\n`
  - On `COMPLETE`: emit `data: { type: "complete", memory_id: "..." }\n\n` then close
  - On `FAILED`: emit `data: { type: "error", message: "..." }\n\n` then close
- **Progress percentage mapping**: `QUEUED`=0%, `DOWNLOADING`=10%, `GENERATING_THUMBNAIL`=20%, `EXTRACTING_AUDIO`=30%, `TRANSCRIBING`=45%, `OCR_FRAMES`=60%, `SYNTHESIZING`=75%, `EMBEDDING`=88%, `CLUSTERING`=95%, `COMPLETE`=100%
- `GET /api/v1/jobs/{job_id}` — one-time status poll (non-streaming alternative for reconnect scenarios)
- **Celery retry policy**: on transient failures (network timeout, API rate limit) → `autoretry_for=(Exception,), max_retries=3, retry_backoff=True`

**Key Files:**
```
apps/backend/workers/process_memory.py
apps/backend/routers/jobs.py
apps/backend/utils/job_helpers.py
```

---

### Task 10 — Thumbnail & Cover Image Extraction Pipeline
**Phase:** 2 — Ingestion
**Priority:** 🟠 High
**Estimate:** 1 day
**Dependencies:** Tasks 7, 8

**Tech Stack:** `ffmpeg` `PyMuPDF` `Pillow` `Supabase Storage`

**Summary:**
Generate cover images for every content type: Instagram Reel frame, PDF first-page render, article OG image, video keyframe, uploaded image thumbnail. All outputs converted to WebP for bandwidth efficiency. This is what powers the visual card UI on the dashboard.

**Implementation Steps:**
- **Instagram Reel**: thumbnail already downloaded by Task 7 scraper, skip to resize + convert step
- **Uploaded MP4**: `ffmpeg -ss 00:00:01.000 -i input.mp4 -frames:v 1 thumb.jpg` (grab 1-second frame)
- **PDF**: `fitz.open(path); page = doc[0]; pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))` → 2x scale for retina quality
- **Uploaded Image**: `Pillow.Image.open(path).thumbnail((600, 400))` maintaining aspect ratio
- **Web Article**: download `og:image` URL (already extracted by Task 8 scraper), resize with Pillow
- **WebP conversion** (all paths): `image.save(output_path, "WEBP", quality=85)` — typically 30–50% smaller than JPEG
- Upload to `thumbnails/{user_id}/{memory_id}.webp` in Supabase Storage
- `UPDATE user_memories SET thumbnail_storage_path = :path WHERE id = :memory_id`
- Generate **1-year signed URL** for the thumbnail; cache the URL in Redis (TTL = 1 year - 1 day)
- Handle failures gracefully: if thumbnail fails → log warning, continue pipeline (non-blocking)

**Key Files:**
```
apps/backend/processors/thumbnail_processor.py
```

---

### Task 11 — PDF Text Extraction Pipeline
**Phase:** 2 — Ingestion
**Priority:** 🟠 High
**Estimate:** 1 day
**Dependencies:** Task 9

**Tech Stack:** `PyMuPDF (fitz)` `pytesseract` `Python`

**Summary:**
Extract text from both digital PDFs (text layer extraction, fast) and scanned PDFs (pytesseract OCR fallback, slower). Preserve document structure: headers, code blocks, tables, numbered lists. Output feeds directly into the Structured Synthesizer.

**Implementation Steps:**
- `doc = fitz.open(storage_path)` to open PDF
- **Page type detection**: if `page.get_text("blocks")` returns content → digital PDF; if result is empty → scanned image PDF
- **Digital PDF path**:
  - Iterate all pages, `page.get_text("dict")` for structured blocks
  - Identify monospace font regions as code blocks (check `block["font"]` for Courier/monospace)
  - Preserve section headers (larger font size blocks)
  - **Table extraction** (PyMuPDF 1.23+): `page.find_tables()` for tabular data
- **Scanned PDF path**:
  - `pix = page.get_pixmap(dpi=300)` → convert to `PIL.Image`
  - `pytesseract.image_to_string(img, config='--psm 6')` for OCR
- **Large PDF handling** (> 100 pages): process in 20-page chunks, concatenate results sequentially
- **Cleaning**: remove detected headers/footers (heuristic: text appearing at same y-position on 3+ pages), normalize whitespace, remove page numbers
- Store complete extracted text in `user_memories.raw_transcript`
- Pass result forward to Synthesis stage (Task 15) — no audio processing branch for PDFs

**Key Files:**
```
apps/backend/processors/pdf_processor.py
```

---

## Phase 3 — AI Processing Pipeline
> The "brain" of the system: transcription, frame OCR, structured summarization, vector embedding, and auto-clustering.

---

### Task 12 — Audio Extraction & Whisper Transcription
**Phase:** 3 — AI Pipeline
**Priority:** 🔴 Critical
**Estimate:** 1.5 days
**Dependencies:** Tasks 9, 7

**Tech Stack:** `ffmpeg` `faster-whisper` `OpenAI Whisper API` `Python`

**Summary:**
Extract audio tracks from MP4 files and transcribe them to text. Uses `faster-whisper` locally as default (CTranslate2-optimized, near-zero cost) with OpenAI Whisper API as a quality fallback. Controlled by the `WHISPER_PROVIDER` environment variable.

**Implementation Steps:**
- **Audio extraction** via ffmpeg:
  ```
  ffmpeg -i input.mp4 -ar 16000 -ac 1 -f wav output.wav
  ```
  - `16000 Hz` sample rate + mono channel = optimal Whisper input format
  - Apply `loudnorm` filter to normalize audio levels (poor transcription on quiet tutorial voice-overs)
- **`WHISPER_PROVIDER=local`** (default):
  - `faster-whisper` with model size from `WHISPER_MODEL` env var: `base.en` (fast, less accurate), `medium.en` (recommended), `large-v3` (highest quality, slow)
  - `segments, info = model.transcribe(audio_path, beam_size=5, language="en")`
  - Concatenate segment texts into full transcript string
- **`WHISPER_PROVIDER=openai`** (quality fallback):
  - `openai.audio.transcriptions.create(model="whisper-1", file=audio_file, temperature=0)`
- **Post-processing**:
  - Strip filler words: `um`, `uh`, `like you know`, `so basically` using regex
  - Fix common tech term capitalization: `github` → `GitHub`, `npm` → `npm`, `api` → `API`, `cli` → `CLI`
- Store full transcript string in `user_memories.raw_transcript`
- Delete temp `.wav` file after processing to reclaim disk space
- Log `audio_duration` vs `transcription_duration` ratio for performance monitoring

**Key Files:**
```
apps/backend/processors/audio_processor.py
apps/backend/services/transcription_service.py
```

---

### Task 13 — Video Keyframe Sampling & Visual OCR
**Phase:** 3 — AI Pipeline
**Priority:** 🟠 High
**Estimate:** 2 days
**Dependencies:** Tasks 9, 7

**Tech Stack:** `ffmpeg` `imagehash` `GPT-4o Vision` `Python`

**Summary:**
Sample video frames at 1 frame/1.5s, deduplicate near-identical frames via perceptual hashing (reducing API costs ~60%), then batch-send frames to GPT-4o Vision to extract all on-screen code, terminal commands, package names, and technical text.

**Implementation Steps:**
- **Frame sampling** via ffmpeg:
  ```
  ffmpeg -i input.mp4 -vf fps=2/3 temp_frames/%04d.jpg -q:v 3
  ```
  Produces approximately 1 frame per 1.5 seconds
- **Frame deduplication** (PRD enhancement — reduces vision API calls ~60%):
  - Compute `imagehash.phash(Image.open(frame))` for each frame
  - Skip frame if Hamming distance to previous frame hash `< 8` (near-identical visual)
  - Typically eliminates 50–70% of frames in slow tutorial videos
- **Batch frames**: group 5 frames per vision API call (GPT-4o supports multi-image input)
- **Vision LLM system prompt** (stored in `prompts/frame_ocr_prompt.txt`):
  ```
  Analyze these video frames and extract all on-screen technical content.
  Return ONLY valid JSON with this schema:
  {
    "extractions": [
      {
        "frame_index": int,
        "code_blocks": [{"language": str, "code": str}],
        "terminal_commands": [str],
        "package_names": [str],
        "config_values": [str],
        "ui_text": str
      }
    ]
  }
  ```
- Parse response, collect all unique `code_blocks` and `terminal_commands` across all frame batches
- **Deduplication of code blocks**: remove entries with Levenshtein distance `< 10` from already-collected blocks
- Compile all extracted content into a single `ocr_extracted_text` string, structured as:
  ```
  TERMINAL COMMANDS:
  npm install ...
  
  CODE BLOCKS:
  [javascript]
  const client = ...
  ```
- Store in `user_memories.ocr_extracted_text`
- Clean up entire temp frames directory

**Key Files:**
```
apps/backend/processors/video_processor.py
apps/backend/services/vision_service.py
apps/backend/prompts/frame_ocr_prompt.txt
```

---

### Task 14 — Image & Screenshot OCR Service
**Phase:** 3 — AI Pipeline
**Priority:** 🟠 High
**Estimate:** 1 day
**Dependencies:** Task 9

**Tech Stack:** `GPT-4o Vision` `pytesseract` `Pillow` `Python`

**Summary:**
Process uploaded screenshots and images through GPT-4o Vision for structural OCR. Targets code snippets, error stack traces, terminal output, architecture diagrams, and config files. pytesseract handles simple text-only images as a cheaper fallback.

**Implementation Steps:**
- Load image with Pillow, check file size: if `> 4MB` → resize to max 2048px longest side (`Image.thumbnail((2048, 2048))`) to stay within GPT-4o vision payload limit
- Convert to base64 PNG string for API transmission
- **Heuristic for provider selection**:
  - If image contains visual complexity (diagrams, code editor screenshots, terminal output with colors) → GPT-4o Vision
  - If image is plain text document / whiteboard text → pytesseract (faster, free)
  - Heuristic: check image entropy (`ImageStat.Stat(img).stddev`) — high stddev suggests visual complexity
- **GPT-4o Vision prompt** (`prompts/image_ocr_prompt.txt`):
  ```
  Extract all technical content from this screenshot.
  Return ONLY valid JSON:
  {
    "description": str,
    "code_blocks": [{"language": str, "code": str}],
    "terminal_commands": [str],
    "error_messages": [str],
    "text_content": str
  }
  ```
- pytesseract path: `pytesseract.image_to_string(img, config='--psm 6 --oem 3')`
- Compile combined output into `ocr_extracted_text`
- Store in `user_memories.ocr_extracted_text`; pass to Synthesis (Task 15) with no audio processing branch

**Key Files:**
```
apps/backend/processors/image_processor.py
apps/backend/prompts/image_ocr_prompt.txt
```

---

### Task 15 — Structured Synthesizer (AI Summary Engine)
**Phase:** 3 — AI Pipeline
**Priority:** 🔴 Critical
**Estimate:** 2 days
**Dependencies:** Tasks 12, 13, 14, 11

**Tech Stack:** `GPT-4o` `Llama 3.1 via Ollama` `Pydantic v2` `Python`

**Summary:**
The core AI brain. Combines all extracted text (transcript + OCR output + source metadata) and calls an LLM to generate the structured `ai_summary` JSON stored in the database. Handles context window overflow, JSON validation failures, and provider switching.

**Implementation Steps:**
- **Input assembly**: combine `raw_transcript` + `ocr_extracted_text` + source metadata (creator handle, platform, URL, content_type, hashtags)
- **Context window management**: if combined input `> 8000` tokens → chunk `raw_transcript` into 2000-token sections; summarize each section with a lighter model call; then do a final meta-summarization pass over the section summaries
- **System prompt** (`prompts/synthesis_prompt.txt`):
  ```
  You are a knowledge extraction AI. Analyze the provided content and return ONLY valid JSON
  matching exactly this schema (no markdown fences, no preamble):
  {
    "abstract": "2-3 sentence summary",
    "takeaways": ["actionable insight 1", ...],
    "code_blocks": [{"language": "python", "code": "...", "description": "..."}],
    "tags": ["docker", "fastapi", ...],
    "difficulty": "beginner|intermediate|advanced",
    "tech_stack": ["Python", "FastAPI", ...]
  }
  ```
- **LLM provider**: `LLM_PROVIDER=openai` → `gpt-4o`; `LLM_PROVIDER=ollama` → `llama3.1:8b` via local Ollama endpoint
- **JSON validation**: parse response with Pydantic `AISummary` model. If `ValidationError` → retry **once** with stricter prompt: `"CRITICAL: Return ONLY raw JSON. No explanations. No markdown. Start with { and end with }"`
- On second failure → store partial data `{ abstract: raw_response[:500], ... }` with `synthesis_failed: true` flag; do not block the pipeline
- `UPDATE user_memories SET ai_summary = :summary_json WHERE id = :memory_id`
- Log `input_tokens`, `output_tokens` to a `cost_tracking` JSONB column for usage monitoring

**Key Files:**
```
apps/backend/processors/synthesis_service.py
apps/backend/prompts/synthesis_prompt.txt
apps/backend/schemas/models.py (AISummary Pydantic model)
```

---

### Task 16 — Vector Embedding Generation & ChromaDB Indexing
**Phase:** 3 — AI Pipeline
**Priority:** 🔴 Critical
**Estimate:** 1 day
**Dependencies:** Task 15

**Tech Stack:** `ChromaDB` `OpenAI Embeddings` `sentence-transformers` `Python`

**Summary:**
Build the embedding input string from compiled memory content per the PRD's specified format, generate the vector, upsert to ChromaDB with metadata, and mark the memory as indexed in Supabase.

**Implementation Steps:**
- **Build embedding input string** (per PRD vector content spec):
  ```
  [TITLE] [CREATOR_HANDLE]
  SUMMARY: {ai_summary.abstract}
  TAKEAWAYS: {'; '.join(ai_summary.takeaways)}
  TRANSCRIPT: {raw_transcript[:2000]}
  VISUAL TEXT: {ocr_extracted_text[:1000]}
  TAGS: {', '.join(ai_summary.tags)}
  TECH: {', '.join(ai_summary.tech_stack)}
  ```
- Cap total string at **6000 tokens** to stay within embedding API limits
- Call `EmbeddingService.embed_text(full_string)` → returns float vector
- `EmbeddingService.upsert_memory(id=memory_id, text=full_string, metadata={ user_id, content_type, created_at (unix int), tags_csv, tech_stack_csv })`
- `UPDATE user_memories SET indexed = TRUE, updated_at = NOW() WHERE id = :memory_id`
- **Failure handling**: if ChromaDB unavailable → retry 3x with 5s exponential backoff; if still failing → mark `indexed = FALSE`, log Sentry alert, continue (memory is still saved without vector search capability)
- **For updates/edits** (future-proof): call `delete_memory(id)` before `upsert_memory(id, new_text, metadata)` to avoid stale vectors

**Key Files:**
```
apps/backend/services/embedding_service.py (upsert_memory method)
apps/backend/workers/process_memory.py (indexing stage)
```

---

### Task 17 — Auto-Clustering (Plates) Engine
**Phase:** 3 — AI Pipeline
**Priority:** 🟠 High
**Estimate:** 2 days
**Dependencies:** Task 16

**Tech Stack:** `scikit-learn` `ChromaDB` `Supabase` `Celery Beat` `Python`

**Summary:**
Automatically assign each newly embedded memory to a semantic Plate by comparing it to existing plate centroids. Creates new plates with LLM-generated names when no existing plate is similar enough. A nightly Celery Beat job re-runs K-means to rebalance plates as the knowledge base grows.

**Implementation Steps:**
- Triggered as a chained Celery task immediately after Task 16 completes
- `SELECT * FROM plates WHERE user_id = :user_id` → fetch all existing plates
- If no plates exist → create a default "General" plate, assign memory to it
- For each existing plate: compute average cosine similarity between new memory's embedding and the embeddings of the plate's `centroid_ids` members (using `EmbeddingService.get_by_ids()`)
- **Assignment logic**:
  - If `max_similarity > 0.72` → assign to that plate: `INSERT INTO memory_plates`, `UPDATE plates SET item_count = item_count + 1`
  - If no plate meets threshold → create new plate (see naming logic below)
- **New plate naming**: send the new memory's `ai_summary.tech_stack + ai_summary.tags` (top 6 items) to LLM: `"Generate a 2-4 word category title for a knowledge cluster containing: {items}. Return ONLY the title, nothing else."` → store in `plates.name`
- **Centroid update**: append new `memory_id` to `plates.centroid_ids` JSONB array. If `item_count > 20`, keep only the most recent 20 IDs for centroid calculation
- **Nightly re-clustering** (Celery Beat, 03:00 UTC): 
  - Fetch all embeddings for a user
  - Run `sklearn.cluster.KMeans(n_clusters=int(sqrt(n_memories)), random_state=42)`
  - Rebuild `plates` and `memory_plates` tables from scratch using new cluster assignments
  - Re-generate plate names for any changed clusters
- `GET /api/v1/plates` endpoint returning all plates with `item_count` and top 3 thumbnail URLs for the plate card mosaic

**Key Files:**
```
apps/backend/services/clustering_service.py
apps/backend/workers/recluster_task.py
apps/backend/routers/memories.py (plates endpoint)
```

---

## Phase 4 — Organization & Search
> Implement the full hybrid search stack: lexical (PostgreSQL FTS), semantic (ChromaDB), RRF fusion, and knowledge graph edge mapping.

---

### Task 18 — Lexical Full-Text Search API
**Phase:** 4 — Search
**Priority:** 🟠 High
**Estimate:** 1 day
**Dependencies:** Tasks 3, 5

**Tech Stack:** `PostgreSQL` `Supabase` `FastAPI`

**Summary:**
PostgreSQL GIN-indexed full-text search for exact keyword, package name, and creator handle lookups with highlighted match snippets. First leg of the hybrid RRF search.

**Implementation Steps:**
- `GET /api/v1/search?q=&mode=lexical&page=1&limit=20`
- **Supabase query**:
  ```sql
  SELECT *,
    ts_rank(to_tsvector('english', COALESCE(raw_transcript,'') || ' ' || COALESCE(ocr_extracted_text,'')), query) AS rank,
    ts_headline('english', raw_transcript, query, 'MaxWords=30, MinWords=15') AS snippet
  FROM user_memories
  WHERE user_id = :user_id
    AND to_tsvector('english', COALESCE(raw_transcript,'') || ' ' || COALESCE(ocr_extracted_text,'')) @@ plainto_tsquery('english', :q)
  ORDER BY rank DESC, created_at DESC
  LIMIT :limit OFFSET :offset
  ```
- Optional filter params: `content_type`, `plate_id`, `date_from`, `date_to`
- **Return `MemoryCard` objects**: `{ id, title (from ai_summary), abstract, thumbnail_url (signed), source_url, content_type, tags, snippet, rank }`
- Generate signed URLs for `thumbnail_storage_path` on the fly (or use Redis cached URLs from Task 10)
- Response includes `{ results: [], total_count: int, page: int }` for pagination
- Target latency: `< 100ms` for typical queries (GIN index makes this achievable)

**Key Files:**
```
apps/backend/routers/search.py
apps/backend/services/search_service.py (lexical_search method)
```

---

### Task 19 — Semantic Vector Search API
**Phase:** 4 — Search
**Priority:** 🟠 High
**Estimate:** 1 day
**Dependencies:** Tasks 16, 5

**Tech Stack:** `ChromaDB` `FastAPI` `Python`

**Summary:**
Natural language semantic search using ChromaDB vector similarity. Finds conceptually related memories even when the user's query shares no exact keywords with the content — the core differentiator of the product.

**Implementation Steps:**
- `GET /api/v1/search?q=&mode=semantic`
- Call `EmbeddingService.embed_text(user_query)` → query vector
- `collection.query(query_embeddings=[qvec], n_results=25, where={"user_id": user_id})`
- Apply distance threshold: filter results where `distance > 0.65` (too dissimilar, discard)
- Fetch full `user_memories` records from Supabase for the returned IDs (ChromaDB only stores metadata, not full records)
- Enrich each result with thumbnail signed URLs
- Return `MemoryCard` objects with `similarity_score` field attached (for RRF input)
- **Optional metadata filters** passed to ChromaDB `where` clause:
  - `{"content_type": "instagram_reel"}` for type filtering
  - `{"created_at": {"$gte": unix_timestamp}}` for date range filtering

**Key Files:**
```
apps/backend/services/search_service.py (semantic_search method)
```

---

### Task 20 — Hybrid RRF Search Engine
**Phase:** 4 — Search
**Priority:** 🟠 High
**Estimate:** 1 day
**Dependencies:** Tasks 18, 19

**Tech Stack:** `Python` `FastAPI` `Redis` `asyncio`

**Summary:**
Combine lexical and semantic search results using Reciprocal Rank Fusion into a single optimally-ranked result list. This is the default search mode. Results are Redis-cached per user+query for 5 minutes to hit the PRD's <400ms latency target.

**Implementation Steps:**
- `GET /api/v1/search?q=` (mode defaults to `hybrid`)
- **Cache check**: compute `cache_key = sha256(f"{user_id}:{query}")`, check Redis. On hit → return cached results immediately (target: <50ms)
- **Parallel execution**: `results_lex, results_sem = await asyncio.gather(lexical_search(q), semantic_search(q))`
- **RRF scoring formula** (k=60 is standard):
  ```python
  rrf_scores = {}
  for rank, result in enumerate(results_lex):
      rrf_scores[result.id] = rrf_scores.get(result.id, 0) + 1 / (60 + rank + 1)
  for rank, result in enumerate(results_sem):
      rrf_scores[result.id] = rrf_scores.get(result.id, 0) + 1 / (60 + rank + 1)
  ```
- Sort all unique memory IDs by combined RRF score descending
- Fetch any missing memory details not already in either result set
- Return top 20 results as unified `SearchResult` objects
- **Cache result**: `redis.setex(cache_key, 300, json.dumps(results))` (5-minute TTL)
- **Cache invalidation**: when a new memory reaches `COMPLETE` for a user → delete all Redis keys matching `{user_id}:*`
- Target: `< 400ms` end-to-end via asyncio parallel execution + Redis cache

**Key Files:**
```
apps/backend/services/search_service.py (hybrid_search method)
apps/backend/services/cache_service.py
```

---

### Task 21 — Entity Relationship Mapper (Knowledge Graph Edges)
**Phase:** 4 — Search
**Priority:** 🟡 Medium
**Estimate:** 1.5 days
**Dependencies:** Tasks 16, 3

**Tech Stack:** `ChromaDB` `Supabase` `Python`

**Summary:**
After each memory is indexed, automatically detect and store semantic relationships to existing memories to build the knowledge graph edge data that powers the graph visualizer.

**Implementation Steps:**
- Triggered as chained Celery task after Task 17 (clustering) completes
- `EmbeddingService.query_similar(memory_embedding, user_id, n=15)` → get 15 nearest neighbors
- For each neighbor with `similarity > 0.75`:
  - **Determine `relationship_type`**:
    - `same_creator`: `creator_metadata.handle` matches between source and target
    - `shares_technology`: `len(intersection(tech_stack_a, tech_stack_b)) >= 2`
    - `conceptual_link`: default for all others above threshold
  - `weight = similarity_score` (float 0.0–1.0)
  - **Duplicate check**: `SELECT id FROM entity_relationships WHERE (source_asset_id=:a AND target_asset_id=:b) OR (source_asset_id=:b AND target_asset_id=:a)` → skip if exists
  - `INSERT INTO entity_relationships (source_asset_id, target_asset_id, relationship_type, weight)`
- **Graph data API** `GET /api/v1/graph`:
  - Fetch latest 200 memories for user (most recent, as node limit)
  - Fetch all edges involving those memory IDs
  - Build `GraphNode` objects: `{ id, title, content_type, thumbnail_url, plate_id, tags, connection_count }`
  - Build `GraphEdge` objects: `{ source, target, relationship_type, weight }`
  - Return `{ nodes: [], edges: [] }`

**Key Files:**
```
apps/backend/services/graph_service.py
apps/backend/routers/graph.py
```

---

## Phase 5 — RAG Chat Engine

---

### Task 22 — Conversational RAG Chat Backend
**Phase:** 5 — RAG
**Priority:** 🟠 High
**Estimate:** 2 days
**Dependencies:** Tasks 19, 15

**Tech Stack:** `FastAPI` `ChromaDB` `Supabase` `OpenAI API` `Server-Sent Events`

**Summary:**
Full RAG pipeline: retrieves the most relevant memories for the user's query, injects them as LLM context within the token budget, and streams a cited response. The LLM is constrained to answer only from the user's saved memories.

**Implementation Steps:**
- `POST /api/v1/chat` — body: `{ messages: [{role, content}], user_message: str }`
- **Step 1**: `EmbeddingService.embed_text(user_message)` → query vector
- **Step 2**: `EmbeddingService.query_similar(qvec, user_id, n=8)` → top 8 relevant memories
- **Step 3**: Fetch full records from Supabase for returned IDs (need `ai_summary`, `raw_transcript`, `code_blocks`)
- **Step 4 — Context budget management** (max 4000 tokens for context):
  - Rank memories by similarity score (highest first)
  - Include full `ai_summary` for all 8 (compact, ~200 tokens each)
  - Include truncated `raw_transcript` for top 3 only (up to 400 tokens each)
  - Include `code_blocks` JSON for top 5 (if present)
  - Stop adding when budget is exhausted
- **Step 5 — Build LLM request**:
  - System prompt: `"You are a personal knowledge assistant. Answer ONLY using the sources provided below. After each factual claim, cite the source using [Source: Memory Title]. If the answer cannot be found in the sources, say 'I don't have that in your saved memories.' Format code with markdown code fences."`
  - Append sources block: structured text of all context memories
  - Append last 4 conversation turns from `messages` array for follow-up capability
- **Step 6**: Call LLM with `stream=True`, pipe tokens to SSE response (`text/event-stream`)
  - Each SSE event: `data: {"type": "token", "content": "..."}\n\n`
- **Step 7**: On stream completion, parse `[Source: Memory Title]` citations from full response text; map titles to memory IDs
- **Step 8**: Emit final SSE event: `data: {"type": "sources", "items": [{memory_id, title, thumbnail_url}]}\n\n`
- `GET /api/v1/chat/history` (optional): returns session history (stored in Redis by session_id, 24h TTL)

**Key Files:**
```
apps/backend/routers/chat.py
apps/backend/services/rag_service.py
```

---

## Phase 6 — Frontend Development
> Build the complete React application: design system, auth, dashboard, ingestion UI, search, and the memory detail split-view panel.

---

### Task 23 — Frontend Setup, Design System & Routing
**Phase:** 6 — Frontend
**Priority:** 🔴 Critical
**Estimate:** 1.5 days
**Dependencies:** Task 1

**Tech Stack:** `React 18` `Vite` `TypeScript` `Tailwind CSS` `React Router v6` `React Query (TanStack)`

**Summary:**
Bootstrap the React frontend with the exact PRD design system: cream/off-white backgrounds, editorial typography, fine neutral borders, no dark mode, no saturated colors. Establish all routes, auth context, layout, and API client.

**Implementation Steps:**
- `React 18 + Vite + TypeScript (strict: true)` initialization
- **Tailwind CSS config** enforcing PRD color primitives:
  ```js
  // tailwind.config.ts
  darkMode: false,  // STRICTLY PROHIBITED per PRD
  theme: {
    extend: {
      colors: {
        paper: '#FAF9F6',
        'paper-alt': '#F5F5F0',
        accent: '#1A1A1A',
      }
    }
  }
  ```
- **Typography**: `Instrument Serif` (display/headings) + `DM Sans` (body) via Google Fonts — editorial pairing consistent with "warm editorial minimalism"
- **CSS variables** in `index.css`: `--bg`, `--surface`, `--border`, `--text-primary`, `--text-secondary`, `--text-muted`
- **Base component library** (built custom, no heavy UI library dependency):
  - `Button` (variants: primary/ghost/destructive)
  - `Input`, `Textarea`
  - `Badge` (content type, difficulty, tech stack)
  - `Spinner`
  - `Card`
  - `Sheet` (slide-in panel from right)
  - `Toast` (notification system)
  - `Skeleton` (loading placeholder)
- **React Router v6** routes: `/auth`, `/dashboard`, `/search`, `/memories/:id`, `/graph`, `/chat`, `/syllabus`, `/syllabus/:id`
- `AppLayout`: collapsible left sidebar (icon-only 64px, expanded 220px), main content area with persistent top search bar
- `AuthContext`: wraps Supabase session, exports `useAuth()` returning `{ user, session, signIn, signOut, signInWithGoogle, isLoading }`
- **API client** (`lib/api.ts`): Axios instance, `baseURL` from `VITE_API_URL` env, request interceptor injects `Authorization: Bearer {token}` from Supabase session
- **React Query**: `QueryClientProvider` globally, `staleTime=60000`, `retry=1`

**Key Files:**
```
apps/frontend/tailwind.config.ts
apps/frontend/src/router.tsx
apps/frontend/src/contexts/AuthContext.tsx
apps/frontend/src/lib/api.ts
apps/frontend/src/lib/supabase.ts
apps/frontend/src/components/ui/  (all base components)
apps/frontend/src/layouts/AppLayout.tsx
```

---

### Task 24 — Authentication Pages
**Phase:** 6 — Frontend
**Priority:** 🟠 High
**Estimate:** 0.5 day
**Dependencies:** Task 23

**Tech Stack:** `React` `Supabase Auth` `Tailwind CSS`

**Summary:**
Clean, minimal login and signup pages consistent with the editorial cream aesthetic. Email/password forms plus Google OAuth. No heavy decorations — just typography, fine borders, generous whitespace.

**Implementation Steps:**
- `AuthPage.tsx` with tab switcher between Login and Signup
- **Layout**: centered card (max-width 400px) on `#FAF9F6` background, `border border-neutral-200`, no box shadow
- Mnemonic wordmark at top (text-based logo, `Instrument Serif` italic)
- **Login form**: email input + password input + "Sign In" button (solid `bg-neutral-900 text-white`)
- **Google OAuth button**: "Continue with Google" with Google SVG icon, `border border-neutral-200`, hover `bg-neutral-50`
- **Signup form**: name + email + password
- **Inline validation**: error messages below fields in `text-red-600 text-xs`, no alert boxes
- **Loading states**: spinner inside button, button `disabled` during request
- Supabase callback handling: email confirmation redirect, OAuth callback → redirect to `/dashboard`
- Password reset flow: "Forgot password?" link → email with magic link → `ResetPasswordPage.tsx`

**Key Files:**
```
apps/frontend/src/pages/AuthPage.tsx
apps/frontend/src/pages/ResetPasswordPage.tsx
```

---

### Task 25 — Main Dashboard Page
**Phase:** 6 — Frontend
**Priority:** 🔴 Critical
**Estimate:** 2 days
**Dependencies:** Tasks 23, 17, 18

**Tech Stack:** `React` `Tailwind CSS` `React Query` `Intersection Observer`

**Summary:**
The primary interface after login. Plates cluster row at the top, followed by a responsive grid of memory cards. Instagram Reel cards display cover images prominently and include a clickable Instagram hyperlink. Supports infinite scroll and content type filtering.

**Implementation Steps:**
- **Plates row** (horizontal scrollable, `overflow-x-auto`): each `PlateCard` shows:
  - Plate name (bold, `Instrument Serif`)
  - Item count badge
  - 3-image mosaic of the most recent thumbnails in the plate
  - Click → sets `activePlate` state → filters memory grid
- **Memory card grid**: CSS grid, responsive columns (`grid-cols-1 sm:grid-cols-2 lg:grid-cols-3`)
- **`MemoryCard` component**:
  - Thumbnail/cover image (WebP, aspect-ratio `16/9`, object-fit cover)
  - Content type icon badge (top-left: reel icon, PDF icon, image icon, article icon)
  - **Instagram Reel cards specifically**: Instagram SVG icon (top-right corner) as `<a href={source_url} target="_blank" rel="noopener">` linking to the original post — **this is the hyperlink the user requested**
  - Title derived from `ai_summary.abstract` first sentence or `creator_metadata.handle`
  - 2-line abstract (`line-clamp-2`)
  - Tech stack badges (first 3, then "+N more")
  - Relative timestamp (`2 hours ago`)
  - Click card body → navigate to `/memories/:id`
- **Filter chips** below plates row: `All / Reels / PDFs / Images / Articles` — active chip has bottom border (editorial underline style, not filled background)
- **Infinite scroll**: `useInfiniteQuery` + `Intersection Observer` on a sentinel div at the bottom of the grid
- **Empty state**: centered illustration + headline "Your second brain is empty" + CTA "Save your first memory"
- **Loading skeleton**: exact card dimensions with `animate-pulse` grey placeholder blocks

**Key Files:**
```
apps/frontend/src/pages/DashboardPage.tsx
apps/frontend/src/components/MemoryCard.tsx
apps/frontend/src/components/PlateCard.tsx
apps/frontend/src/hooks/useMemories.ts
```

---

### Task 26 — Ingestion UI — Add Content Panel
**Phase:** 6 — Frontend
**Priority:** 🔴 Critical
**Estimate:** 1.5 days
**Dependencies:** Tasks 23, 6, 7, 9

**Tech Stack:** `React` `Tailwind CSS` `react-dropzone` `EventSource API`

**Summary:**
The content addition experience: URL paste for Instagram Reels or web articles, drag-and-drop file upload zone, and a real-time animated pipeline progress display that streams live stage updates via Server-Sent Events.

**Implementation Steps:**
- Trigger: floating `+` action button (bottom-right of dashboard) → opens `Sheet` component sliding in from right
- **Tab 1 — URL**: text input accepting Instagram Reel URL or web URL
  - Auto-detect type by URL pattern: `instagram.com/*` → `instagram_reel`, else → `web_page`
  - Show detected type badge below input
  - Submit → `POST /api/v1/ingest/url`
- **Tab 2 — File**: `react-dropzone` zone
  - Dashed border on cream background, file type icons (PDF/image/video)
  - Shows file name + size preview after selection
  - Submit → `POST /api/v1/ingest/file` as `multipart/form-data`
- **On successful POST**: receive `{ job_id }` → open `new EventSource(/api/v1/jobs/${job_id}/stream, { headers: { Authorization } })`
- **Progress UI** (vertical stepper, 8 stages):
  - Pending stages: hollow circle, gray text
  - Active stage: filled circle with `animate-pulse`, black text
  - Completed stages: checkmark icon, gray text with strikethrough
  - Stage label + elapsed time shown
- **On `type: "complete"` SSE event**: 
  - Flash a subtle checkmark animation
  - Wait 2 seconds, close Sheet
  - Show toast: "Memory saved & indexed ✓"
  - Trigger React Query cache invalidation → dashboard refreshes with new card
- **On `type: "error"` SSE event**: show error message in red + "Retry" button
- **Active jobs indicator**: small number badge on the `+` FAB showing count of in-progress jobs
- **Multiple concurrent ingestions**: each managed independently in `useIngestionJob(jobId)` hook

**Key Files:**
```
apps/frontend/src/components/AddContentPanel.tsx
apps/frontend/src/hooks/useIngestionJob.ts
```

---

### Task 27 — Search Page & Results Display
**Phase:** 6 — Frontend
**Priority:** 🟠 High
**Estimate:** 1.5 days
**Dependencies:** Tasks 20, 23

**Tech Stack:** `React` `Tailwind CSS` `React Query`

**Summary:**
Full-featured search page with the hybrid search bar, rich result cards (including Instagram cover images and hyperlinks), filter controls, and URL state persistence so searches are shareable.

**Implementation Steps:**
- **Search bar**: full-width, auto-focused on page load, `Cmd/Ctrl + K` global shortcut to focus from any page
- **Debounced input**: 300ms debounce before firing API query
- **Search mode toggle** (pill tabs): `Hybrid | Semantic | Keyword` — maps to `?mode=` URL param
- **Result cards** (`SearchResultCard` component):
  - Larger than dashboard cards — more detail visible
  - Thumbnail on left (120px), content details on right
  - Highlighted text snippet from `ts_headline` (lexical mode) or abstract (semantic mode)
  - Content type icon + badge
  - **Instagram Reel results**: reel cover image + Instagram icon → `<a href={source_url}>` to original post
  - Creator handle (if present), tech stack badges, relative timestamp
- **Filter panel** (collapsible sidebar on desktop, bottom sheet on mobile):
  - Content type multi-select
  - Date range (Last 7 days / 30 days / 90 days / All time)
  - Plate selector (dropdown of user's plates)
  - Difficulty filter (beginner / intermediate / advanced)
- **Loading state**: 3 skeleton result cards (exact dimensions of real cards)
- **No results state**: "No memories found for '{query}'" + "Try different keywords or add content about this topic"
- **URL state**: `q`, `mode`, `content_type`, `plate_id`, `date_range` synced to URL params via `useSearchParams()` hook. Browser back button works correctly

**Key Files:**
```
apps/frontend/src/pages/SearchPage.tsx
apps/frontend/src/components/SearchResultCard.tsx
apps/frontend/src/hooks/useSearch.ts
```

---

### Task 28 — Memory Detail Split-View Panel
**Phase:** 6 — Frontend
**Priority:** 🔴 Critical
**Estimate:** 2 days
**Dependencies:** Tasks 23, 25

**Tech Stack:** `React` `Tailwind CSS` `react-pdf` `Prism.js`

**Summary:**
The core content reading experience. A slide-in split panel with original media on the left and AI-generated summary, code blocks, and full transcript on the right. Instagram post hyperlink is prominently displayed. Responsive: stacks vertically on mobile.

**Implementation Steps:**
- Triggered by clicking a `MemoryCard` → router navigates to `/memories/:id` or opens as overlay `Sheet`
- Fetch `GET /api/v1/memories/:id` for full detail record
- **Left panel — Media Viewer** (content_type dependent):
  - `instagram_reel`: `<video controls src={signedStorageUrl} />` HTML5 video player + **prominent "View on Instagram" button** with Instagram SVG logo → `<a href={source_url} target="_blank">` (THE HYPERLINK — explicitly required)
  - `pdf`: `react-pdf` `<Document>` + `<Page>` components with prev/next page navigation and page count
  - `image`: full-resolution `<img>` with click-to-zoom overlay
  - `web_page`: article body text renderer (clean typography, `Instrument Serif` for body text)
- **Right panel — AI Summary**:
  - **Abstract**: subtle `bg-neutral-50 rounded` card with 2-3 sentence summary
  - **Key Takeaways**: bulleted list, each takeaway on its own line with `→` prefix
  - **Code Blocks**: `Prism.js` syntax highlighted code blocks (language auto-detected); language badge top-left; **one-click copy button** top-right (copies to clipboard, shows "Copied!" flash)
  - **Tech Stack**: pill badges `(bg-neutral-100 text-neutral-700)`
  - **Difficulty badge**: color-coded (beginner=green-100, intermediate=yellow-100, advanced=red-100)
- **Full Transcript section**: collapsible accordion below summary, monospace font, line breaks preserved
- **Top metadata bar**: creator handle (with `@` prefix), platform icon, date, `"Open Original →"` hyperlink
- **Smooth slide-in animation**: CSS `transform: translateX(100%)` → `translateX(0)`, 400ms `ease-out`
- **Mobile layout**: full-screen view with tab bar switching between `Media`, `Summary`, `Transcript` tabs

**Key Files:**
```
apps/frontend/src/pages/MemoryDetailPage.tsx
apps/frontend/src/components/MemoryDetailPanel.tsx
apps/frontend/src/components/CodeBlock.tsx
apps/frontend/src/components/MediaViewer.tsx
```

---

## Phase 7 — Advanced Features
> Knowledge graph visualization, conversational chat UI, generative learning paths, and the Chrome extension.

---

### Task 29 — Knowledge Graph Visualizer
**Phase:** 7 — Advanced
**Priority:** 🟡 Medium
**Estimate:** 2.5 days
**Dependencies:** Tasks 21, 23

**Tech Stack:** `D3.js v7` `React` `Tailwind CSS`

**Summary:**
Interactive force-directed graph rendering all memory nodes and their semantic relationship edges. Sized by connection count, color-coded by content type. Click any node to open the memory detail panel. Plate overlay mode highlights cluster groupings.

**Implementation Steps:**
- Fetch `GET /api/v1/graph` → `{ nodes: [], edges: [] }` on page load
- **D3.js v7 force simulation** inside a React `useRef` SVG container:
  - `d3.forceLink(edges).distance(120).strength(0.7)`
  - `d3.forceManyBody().strength(-300)` (repulsion)
  - `d3.forceCenter(width/2, height/2)`
  - `d3.forceCollide().radius(d => nodeRadius(d) + 8)` (prevent overlap)
- **Node rendering**: SVG `<circle>` elements
  - Radius: `6 + (connection_count * 1.5)`, capped at 20px
  - Fill by content_type: reel `#C4B5A5`, pdf `#A8B5C4`, image `#C4A8B5`, web `#B5C4A8` (muted editorial palette)
  - Hover: scale 1.3x, show tooltip with title + abstract preview
- **Node labels**: `<text>` elements, visible only at zoom level > 1.5x, 10px neutral-600, `text-anchor: middle`, truncated at 20 chars
- **Edge rendering**: `<line>` elements
  - `stroke-opacity = weight` (dim weak connections, bold strong ones)
  - `stroke-dasharray` by type: `shares_technology=solid`, `conceptual_link=5,5 dashed`, `same_creator=2,2 dotted`
- **Zoom + pan**: `d3.zoom().scaleExtent([0.3, 3])` on SVG element; smooth scroll-zoom, drag-pan
- **Node click**: call React callback → open `MemoryDetailPanel` for clicked `memory_id`
- **Plate overlay button**: toggle shows convex hull `<polygon>` shapes around plate member clusters with plate name labels
- **Performance**: if `nodes.length > 150` → switch to `d3-force-canvas` renderer (Canvas 2D instead of SVG DOM)
- **Filter controls** (top bar): content type checkboxes, plate dropdown, "Reset Layout" button

**Key Files:**
```
apps/frontend/src/pages/GraphPage.tsx
apps/frontend/src/components/KnowledgeGraph.tsx
```

---

### Task 30 — Conversational Chat UI
**Phase:** 7 — Advanced
**Priority:** 🟠 High
**Estimate:** 1.5 days
**Dependencies:** Tasks 22, 23

**Tech Stack:** `React` `Tailwind CSS` `EventSource API`

**Summary:**
Clean chat interface for the RAG engine. Streaming responses display token-by-token. Source citation chips below each response link back to the specific memories cited. Conversation history maintained for session.

**Implementation Steps:**
- **Layout**: full-height flex column — messages area (`flex-grow`, `overflow-y-auto`) + fixed input bar at bottom
- **Message bubbles**:
  - User: right-aligned, `bg-neutral-900 text-white rounded-2xl rounded-tr-sm px-4 py-3`
  - Assistant: left-aligned, `bg-white border border-neutral-200 rounded-2xl rounded-tl-sm px-4 py-3`
- **Streaming display**: open `EventSource` on send, update message content in `useState` as `token` events arrive; append each token character-by-character
- **Source citation chips**: rendered below each assistant message once `sources` SSE event received — each chip shows `{ thumbnail (24px), title (truncated 30 chars) }`, click → opens `MemoryDetailPanel`
- **Input area**: `<textarea>` auto-resize (1–4 rows via JS height adjustment), `Enter` = send, `Shift+Enter` = newline, `Send` icon button (disabled while streaming)
- **Loading indicator**: three animated dots (`...`) while waiting for first token stream event
- **Suggested starters** (empty state): clickable prompt cards:
  - "What terminal commands have I saved?"
  - "Summarize my Docker notes"
  - "Show me React patterns I bookmarked"
  - "What did I save last week about databases?"
- **Error handling**: `EventSource.onerror` → show "Connection lost. Retry?" toast with retry button
- **Clear conversation**: button in top bar; clears `messages` state array
- **`useChat` hook** encapsulates: message history state, send logic, SSE stream management, loading state

**Key Files:**
```
apps/frontend/src/pages/ChatPage.tsx
apps/frontend/src/components/ChatMessage.tsx
apps/frontend/src/hooks/useChat.ts
```

---

### Task 31 — Generative Learning Path (Syllabus) Feature
**Phase:** 7 — Advanced
**Priority:** 🟡 Medium
**Estimate:** 2 days
**Dependencies:** Tasks 15, 23

**Tech Stack:** `React` `Tailwind CSS` `FastAPI` `LLM API`

**Summary:**
Multi-select memories from the dashboard, provide a topic title, and generate an AI-ordered curriculum with learning objectives and estimated time per step. Displayed as a visual timeline with progress tracking.

**Implementation Steps:**
- **Multi-select mode**: `Select` toggle in dashboard toolbar → checkboxes appear on all `MemoryCard` components
- **Floating action bar** (appears when ≥2 cards selected): `{N} memories selected` + "Generate Learning Path" button + topic title text input
- `POST /api/v1/syllabus { memory_ids: string[], topic_title: string }`
- **Backend** (`syllabus_service.py`):
  - Fetch all selected memories' `ai_summary` objects from Supabase
  - **LLM prompt**: `"You are a curriculum designer. Given these {N} resources, create a learning path titled '{topic_title}'. Order them from foundational to advanced. Group by concept. For each step, write 2-3 clear learning objectives. Return ONLY JSON: { title, steps: [{ order, memory_id, title, concept_group, objectives: string[], estimated_minutes: int }] }"`
  - Validate response with Pydantic `SyllabusStructure` model
  - `INSERT INTO generated_learning_paths (user_id, title, topic_context, syllabus_structure)`
  - Return `{ syllabus_id, syllabus }`
- **`SyllabusPage`** (`/syllabus/:id`):
  - Vertical timeline with concept group separators
  - Each step card: memory thumbnail (left, 80px), step number, title, concept group badge, objectives list (checkboxes), estimated time, difficulty badge
  - Click step card → opens `MemoryDetailPanel` for that memory
  - **Progress tracking**: checkbox state stored in `localStorage` keyed by `syllabus_id` (persists across sessions)
  - Top bar: topic title, total estimated time, completion percentage
- `GET /api/v1/syllabus` — list all generated syllabuses on `/syllabus` index page

**Key Files:**
```
apps/backend/routers/syllabus.py
apps/backend/services/syllabus_service.py
apps/frontend/src/pages/SyllabusPage.tsx
apps/frontend/src/pages/SyllabusListPage.tsx
```

---

### Task 32 — Chrome Browser Extension (Manifest V3)
**Phase:** 7 — Advanced
**Priority:** 🟡 Medium
**Estimate:** 2 days
**Dependencies:** Tasks 6, 8

**Tech Stack:** `Chrome Extension MV3` `Vite + CRXJS` `TypeScript` `Tailwind CSS`

**Summary:**
Single-click browser extension for instantly saving the current tab URL or extracting its article text to Mnemonic without leaving the browsing session. Works in Chrome and Arc (same API).

**Implementation Steps:**
- `manifest.json` (V3):
  ```json
  {
    "manifest_version": 3,
    "permissions": ["activeTab", "storage", "scripting"],
    "background": { "service_worker": "background.js" },
    "action": { "default_popup": "popup.html" }
  }
  ```
- **`popup.tsx`**: React component in 360px × 480px popup
  - Shows current tab title + URL (truncated)
  - Two action buttons: `Save URL` and `Save Article Text`
  - If not authenticated: shows "Connect to Mnemonic" → opens `app_url/auth?return=extension`
  - If authenticated: shows user email + last 3 saved items
- **`Save URL` action**: sends `chrome.runtime.sendMessage({ type: "SAVE_URL", url, content_type })` to background worker
- **`Save Article Text` action**: injects content script via `chrome.scripting.executeScript`, extracts `document.body.innerText`, sends to background worker
- **`background.ts`** (service worker): handles all API fetch calls (popup context can't do network in MV3)
  - Reads JWT from `chrome.storage.local` (`{ token: string }`)
  - `POST` to `VITE_API_URL/api/v1/ingest/*`
  - Returns `job_id` to popup via `chrome.runtime.sendMessage`
  - Polls job status and updates extension badge count with in-progress jobs
- **Popup success state**: animated checkmark + "Processing in background..." + link to open dashboard
- **Build**: `Vite + @crxjs/vite-plugin` → outputs to `extension/dist/` with HMR during development
- **Package for store**: `zip extension/dist/* extension.zip` for Chrome Web Store upload

**Key Files:**
```
apps/extension/manifest.json
apps/extension/src/popup.tsx
apps/extension/src/background.ts
apps/extension/src/content.ts
apps/extension/vite.config.ts
```

---

## Phase 8 — Polish & Deployment
> Performance optimization, production error handling, and full CI/CD deployment pipeline.

---

### Task 33 — Performance Optimization & Caching Layer
**Phase:** 8 — Deploy
**Priority:** 🟡 Medium
**Estimate:** 1.5 days
**Dependencies:** All backend tasks

**Tech Stack:** `Redis` `FastAPI` `asyncpg` `React Query` `Vite`

**Summary:**
Hit the PRD's `<400ms` search latency requirement and ensure smooth UI via Redis caching, async DB connection pooling, image lazy loading, and frontend bundle optimization.

**Implementation Steps:**
- **Redis caching** (`cache_service.py`):
  - `GET /api/memories` list → cache per `(user_id, page, content_type, plate_id)`, TTL 5min
  - Hybrid search results → cache per `sha256(user_id + query)`, TTL 5min
  - Thumbnail signed URLs → TTL 1 year (set at generation time in Task 10)
  - Invalidation on new COMPLETE job: `redis.delete_pattern(f"{user_id}:*")`
- **PostgreSQL optimization**:
  - `EXPLAIN ANALYZE` on all primary queries; add composite indexes where needed
  - Replace synchronous `supabase-py` client on high-traffic endpoints with `asyncpg` connection pool
- **Rate limiting**: `slowapi` on FastAPI — `100 req/min` on `/search`, `10 req/hour` on `/ingest` per user
- **Frontend optimization**:
  - `React Query`: `staleTime=60000`, `gcTime=300000`, optimistic updates on mutation
  - Intersection Observer lazy loading on all `MemoryCard` thumbnail `<img>` elements
  - `loading="lazy"` + `decoding="async"` on all images
  - Vite code-splitting: `lazy()` import for `GraphPage`, `ChatPage`, `SyllabusPage` (heavy routes)
  - Bundle analysis: `vite-bundle-visualizer` to identify and eliminate large dependencies
  - Target: initial bundle `< 200KB` gzipped
- **API response compression**: `GZipMiddleware` (already in middleware stack from Task 5) — verify working

**Key Files:**
```
apps/backend/services/cache_service.py
apps/backend/middleware/rate_limit.py
apps/frontend/vite.config.ts (rollupOptions.output.manualChunks)
```

---

### Task 34 — Error Handling, Logging & Monitoring
**Phase:** 8 — Deploy
**Priority:** 🟡 Medium
**Estimate:** 1 day
**Dependencies:** All tasks

**Tech Stack:** `Sentry` `Loguru` `FastAPI` `React`

**Summary:**
Production-grade error observability: structured JSON logging on backend, Sentry error tracking on both frontend and backend, user-facing error states, and a health status endpoint.

**Implementation Steps:**
- **Backend logging** (`utils/logger.py`):
  - `Loguru` with structured JSON output: `{ timestamp, level, request_id, user_id, route, duration_ms, message }`
  - Request ID middleware (Task 5 already adds this) — attach to all log lines in the same request context
  - Log all ingestion pipeline stage transitions at `INFO` level
  - Log all failed jobs at `ERROR` level with full traceback
- **Sentry Python SDK**:
  - `sentry_sdk.init(dsn=SENTRY_DSN, traces_sample_rate=0.1, profiles_sample_rate=0.1)`
  - FastAPI integration: capture all unhandled exceptions, 500 responses
  - Custom fingerprinting for ingestion failures: group by `content_type + error_type`
- **Sentry React SDK**:
  - `Sentry.init({ dsn, integrations: [browserTracingIntegration(), replayIntegration()] })`
  - `ErrorBoundary` component wrapping all major route components
  - Fallback UI on boundary catch: "Something went wrong" + "Reload page" button + report ID
- **Toast notification system** (already built as component in Task 23):
  - Network timeout → `"Request timed out. Please try again."`
  - Rate limit hit → `"Slow down! Too many requests."`
  - Auth expired → `"Session expired. Please sign in again."` + redirect
- **Failed ingestion user notification**: after `FAILED` status → show inline card in dashboard with reason + "Retry" CTA button
- `GET /api/v1/health` (detailed version, admin-only): `{ api: "ok", database: { connected, latency_ms }, chromadb: { connected, collection_count }, redis: { connected, memory_used }, celery: { workers_online, pending_tasks } }`

**Key Files:**
```
apps/backend/utils/logger.py
apps/backend/middleware/request_id.py
apps/frontend/src/components/ErrorBoundary.tsx
apps/frontend/src/lib/sentry.ts
```

---

### Task 35 — Production Deployment & CI/CD Pipeline
**Phase:** 8 — Deploy
**Priority:** 🔴 Critical
**Estimate:** 1.5 days
**Dependencies:** All tasks

**Tech Stack:** `Railway` `Vercel` `Docker` `GitHub Actions`

**Summary:**
Deploy all services to production with Docker containers, automated CI/CD on merge to main, environment variable management via platform dashboards (never in code), and database backup configuration.

**Implementation Steps:**
- **`Dockerfile`** (FastAPI web service):
  ```dockerfile
  FROM python:3.11-slim
  RUN apt-get update && apt-get install -y ffmpeg tesseract-ocr libmagic1
  COPY requirements.txt .
  RUN pip install --no-cache-dir -r requirements.txt
  COPY . .
  CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
  ```
- **`Dockerfile.worker`** (Celery worker — same base image, different CMD):
  ```dockerfile
  FROM project-mnemonic-backend  # inherit from above
  CMD ["celery", "-A", "celery_app", "worker", "--loglevel=info", "--concurrency=4"]
  ```
- **`docker-compose.yml`** (local development only): `api`, `worker`, `redis`, `chromadb` services with volume mounts
- **Railway deployment** (4 services):
  - Service 1: FastAPI web (`Dockerfile`) → exposed as web service on Railway domain
  - Service 2: Celery worker (`Dockerfile.worker`) → no port exposure, connected to same Redis
  - Service 3: Redis → Railway addon plugin
  - Service 4: ChromaDB → custom service with persistent `/data/chromadb` volume mount
- **Vercel** (frontend): connect GitHub repo, set `apps/frontend` as root directory, configure `VITE_API_URL` environment variable to Railway backend URL
- **Environment variables**: all secrets configured in Railway and Vercel dashboards — `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `OPENAI_API_KEY`, `REDIS_URL`, `SENTRY_DSN`, `PROXY_LIST`, etc. Never committed to repository
- **GitHub Actions deploy workflow** (`.github/workflows/deploy.yml`):
  - Trigger: push to `main` branch
  - Step 1: run all tests (fail fast if tests fail)
  - Step 2: trigger Railway deploy via Railway deploy hook URL
  - Step 3: Vercel auto-deploys via GitHub integration (no manual step needed)
- **Supabase production**:
  - Upgrade to **Pro plan** for higher storage limits (raw MP4 files are large)
  - Enable **Point-in-Time Recovery** for automated database backups
  - Set Storage bucket CORS policies for production frontend domain
- **Custom domain**: configure DNS A record for API subdomain (Railway) and apex/www domain (Vercel)
- **railway.toml** for Railway service configuration (health check path, restart policy, scaling)

**Key Files:**
```
Dockerfile
Dockerfile.worker
docker-compose.yml
.github/workflows/deploy.yml
railway.toml
.vercelignore
```

---

## Summary Table

| # | Task | Phase | Priority | Estimate | Depends On |
|---|------|-------|----------|----------|------------|
| 1 | Monorepo & Project Scaffolding | Foundation | 🔴 Critical | 1 day | — |
| 2 | Supabase Init & Auth Configuration | Foundation | 🔴 Critical | 1.5 days | 1 |
| 3 | Database Schema Migrations | Foundation | 🔴 Critical | 1 day | 2 |
| 4 | ChromaDB Setup & Embedding Service | Foundation | 🔴 Critical | 1 day | 1 |
| 5 | FastAPI Scaffolding & Celery/Redis | Foundation | 🔴 Critical | 1.5 days | 2, 4 |
| 6 | File Upload & Storage Service | Ingestion | 🟠 High | 1.5 days | 3, 5 |
| 7 | Instagram Reel Scraper Service | Ingestion | 🟠 High | 2 days | 3, 5 |
| 8 | Web Article Scraper Service | Ingestion | 🟡 Medium | 1 day | 5 |
| 9 | Async Worker & Job Status SSE | Ingestion | 🔴 Critical | 1.5 days | 5 |
| 10 | Thumbnail & Cover Image Extraction | Ingestion | 🟠 High | 1 day | 7, 8 |
| 11 | PDF Text Extraction Pipeline | Ingestion | 🟠 High | 1 day | 9 |
| 12 | Audio Extraction & Transcription | AI Pipeline | 🔴 Critical | 1.5 days | 9, 7 |
| 13 | Video Keyframe Sampling & OCR | AI Pipeline | 🟠 High | 2 days | 9, 7 |
| 14 | Image & Screenshot OCR Service | AI Pipeline | 🟠 High | 1 day | 9 |
| 15 | Structured Synthesizer (AI Summary) | AI Pipeline | 🔴 Critical | 2 days | 12, 13, 14, 11 |
| 16 | Vector Embedding & ChromaDB Indexing | AI Pipeline | 🔴 Critical | 1 day | 15 |
| 17 | Auto-Clustering (Plates) Engine | AI Pipeline | 🟠 High | 2 days | 16 |
| 18 | Lexical Full-Text Search API | Search | 🟠 High | 1 day | 3, 5 |
| 19 | Semantic Vector Search API | Search | 🟠 High | 1 day | 16, 5 |
| 20 | Hybrid RRF Search Engine | Search | 🟠 High | 1 day | 18, 19 |
| 21 | Entity Relationship Mapper | Search | 🟡 Medium | 1.5 days | 16, 3 |
| 22 | Conversational RAG Chat Backend | RAG | 🟠 High | 2 days | 19, 15 |
| 23 | Frontend Setup & Design System | Frontend | 🔴 Critical | 1.5 days | 1 |
| 24 | Authentication Pages | Frontend | 🟠 High | 0.5 day | 23 |
| 25 | Main Dashboard Page | Frontend | 🔴 Critical | 2 days | 23, 17, 18 |
| 26 | Ingestion UI — Add Content Panel | Frontend | 🔴 Critical | 1.5 days | 23, 6, 7, 9 |
| 27 | Search Page & Results Display | Frontend | 🟠 High | 1.5 days | 20, 23 |
| 28 | Memory Detail Split-View Panel | Frontend | 🔴 Critical | 2 days | 23, 25 |
| 29 | Knowledge Graph Visualizer | Advanced | 🟡 Medium | 2.5 days | 21, 23 |
| 30 | Conversational Chat UI | Advanced | 🟠 High | 1.5 days | 22, 23 |
| 31 | Generative Learning Path Feature | Advanced | 🟡 Medium | 2 days | 15, 23 |
| 32 | Chrome Browser Extension (MV3) | Advanced | 🟡 Medium | 2 days | 6, 8 |
| 33 | Performance Optimization & Caching | Deploy | 🟡 Medium | 1.5 days | All backend |
| 34 | Error Handling, Logging & Monitoring | Deploy | 🟡 Medium | 1 day | All |
| 35 | Production Deployment & CI/CD | Deploy | 🔴 Critical | 1.5 days | All |

**Total estimated developer days: ~51 days**
**Solo developer: ~10–12 weeks**
**Two developers (backend + frontend split): ~5–6 weeks**

---

## Recommended Development Order

```
WEEK 1–2:  Tasks 1 → 5  (full infrastructure, can develop backend and frontend in parallel after this)
WEEK 3–4:  Tasks 6, 7, 9, 10  (core ingestion: file upload, Instagram scraper, job queue, thumbnails)
WEEK 4–5:  Tasks 12, 15, 16  (critical AI path: transcription → synthesis → embedding)
WEEK 5:    Tasks 18, 19, 20  (all three search modes — fast tasks, high ROI)
WEEK 6:    Tasks 23, 24, 25, 26  (React app foundation + dashboard + ingestion UI)
WEEK 7:    Tasks 27, 28  (search UI + memory detail panel — core user loop complete)
WEEK 8:    Tasks 11, 13, 14, 17  (remaining processors: PDF, image OCR, keyframes, clustering)
WEEK 9:    Tasks 8, 21, 22  (web scraper, graph edges, RAG backend)
WEEK 10:   Tasks 30, 31  (chat UI, syllabus)
WEEK 11:   Tasks 29, 32  (graph visualizer, extension)
WEEK 12:   Tasks 33, 34, 35  (optimization, monitoring, deploy)
```

> **Note:** The core user loop (save Instagram Reel → AI summary → search → view with cover image + Instagram hyperlink) is complete by end of Week 7. Advanced features (graph, syllabus, extension) can ship iteratively after the MVP loop is validated.