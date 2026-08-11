# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Cortex** is a personal AI memory engine that cures scroll fatigue: it ingests internet content (web pages, PDFs, images, videos/Instagram reels), extracts text/audio/OCR, synthesizes structured AI summaries, embeds them into a vector DB, clusters them into "plates" (categories), and exposes hybrid search and RAG chat.

Monorepo managed with **pnpm workspaces + Turborepo**. Three apps:

- `apps/frontend` — React 18 + Vite + Tailwind CSS v4 SPA
- `apps/backend` — Python 3.11+ FastAPI + Celery (no package.json; not part of turbo)
- `apps/extension` — Chrome MV3 extension (stub: only `manifest.json` + `package.json` exist; `src/` and `index.html` referenced in the manifest don't exist yet)

## Commands

### JS apps (root, via turbo)
```bash
pnpm install        # install JS deps
pnpm dev            # frontend (Vite, http://localhost:5173) + extension dev servers
pnpm build          # build all JS apps
pnpm lint           # eslint on frontend + extension (uses --max-warnings 0)
pnpm test           # runs turbo test — NO JS tests exist yet, effectively a no-op
```
The backend is **not** started by `pnpm dev` — it must be launched separately (below).

### Python backend (`apps/backend`)
```bash
# from apps/backend
# use the existing venv (apps/backend/venv) or create one, then:
pip install -e ".[dev]"          # installs app + black/isort/flake8/pytest

uvicorn main:app --reload         # API server on http://127.0.0.1:8000 (or: python main.py)
celery -A celery_app worker --loglevel=info   # ingestion worker (pool=solo)
celery -A celery_app beat --loglevel=info     # scheduler (nightly reclustering, 2am UTC)

black --check . && isort --check . && flake8 .   # Python lint (CI runs these)
pytest                                          # tests (only tests/test_embedding_service.py)
```
Backend tests are **not** wired into turbo; run pytest directly. `apps/backend/.flake8` and root `.flake8` are identical (max-line-length 88, ignore E203).

## Environment Variables

`.env` files are gitignored; `.env.example` is the inventory. Key ones by app:

**Backend** (`apps/backend/.env`): `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET` (local JWT decode), `GEMINI_API_KEY` (embeddings, synthesis, vision, plate naming), `GROQ_API_KEY` (RAG chat), `REDIS_URL`, `CHROMA_PERSIST_PATH` (default `./data/chromadb`), `WHISPER_PROVIDER`/`WHISPER_MODEL`, `LLM_PROVIDER` (`gemini` default, falls back to `ollama`), `OLLAMA_BASE_URL`, `SENTRY_DSN`, `OPENAI_API_KEY`.

**Frontend** (`apps/frontend/.env`): `VITE_API_BASE_URL` (default `http://localhost:8000`), `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`, `VITE_SENTRY_DSN`.

## Architecture: the memory lifecycle

The core is one pipeline that every ingested item flows through, spanning all subsystems:

**1. Ingest** — `routers/ingest.py`: `POST /api/ingest/file` (upload → Supabase Storage) or `/url` (scrape via `WebScraper`/`InstagramScraper`, download assets → Storage). Inserts a `user_memories` row + `job_tracking` row, queues Celery `process_memory_task`, returns `202` with `job_id`. Rate-limited `10/hour`.

**2. Processing pipeline** — `workers/process_memory.py` is the master orchestrator: a linear list of named stages selected by `content_type` (video/reel: THUMBNAIL → AUDIO_EXTRACT → TRANSCRIBING → OCR_FRAMES → SYNTHESIZING → EMBEDDING → CLUSTERING → MAPPING_RELATIONS; pdf: …→ PDF_EXTRACT →…; image: …→ OCR_IMAGE →…; web_page: …→ SYNTHESIZING →…). Each stage writes its name to the `job_tracking` row so the frontend streams progress via SSE (`GET /api/jobs/{job_id}/stream`). Extraction uses `faster-whisper` (audio), `PyMuPDF` (PDF), Gemini vision (video frames/images), OCR via the processors in `services/processors/`.

**3. Synthesis** — `SYNTHESIZING` stage calls Gemini (`gemini-1.5-flash`, `LLM_PROVIDER=ollama` fallback) with `prompts/synthesis_prompt.txt` and Pydantic-validates the result into the `ai_summary` JSON: `title/abstract/takeaways/code_blocks/tags/difficulty/tech_stack`. On repeated JSON/validation failure it returns a safe fallback schema, never throws.

**4. Embedding** — `services/embedding_service.py`: `upsert_memory` builds a text blob (summary + transcript + OCR + creator) and embeds via Gemini `gemini-embedding-2` into ChromaDB collection `mnemonic_memories` (cosine, persistent at `CHROMA_PERSIST_PATH`), marks `indexed=true`, then fires `cluster_single_memory_task`.

**5. Clustering into "Plates"** — `services/clustering_service.py`: a memory is compared (cosine sim) against each plate's centroid (mean of its `centroid_member_ids` embeddings); if sim > **0.72** it joins that plate, else a new plate is created with a Gemini-generated 2–3 word name. `workers/recluster_task.py` runs nightly (Celery beat, 2am UTC) and does per-user KMeans re-clustering (`n_clusters = sqrt(n)`), but only for users with > 10 memories.

**6. Search** — `routers/search.py` + `services/search_service.py`: `mode=hybrid` (default) runs lexical (Supabase RPC `lexical_search_memories`) and semantic (ChromaDB vector query, `distance ≤ 0.65`) in parallel and merges with **Reciprocal Rank Fusion**. Results cached in Redis 5 min keyed by SHA-256 of params. `100/minute` rate limit; `X-Total-Count` header.

**7. Chat / RAG** — `routers/chat.py` + `services/rag_service.py`: embeds the question, pulls top-6 memories from ChromaDB, builds a ~4000-token context window (truncating per-memory transcripts), streams from Groq (`llama-3.1-8b-instant`) over SSE. Citations are parsed from `[Title]` markers in the response and resolved to signed thumbnail URLs. `30/hour` rate limit.

**8. Graph** — `routers/graph.py`: returns the top-200 most-connected memories + `entity_relationships` edges (fetched in 500-id chunks) for the D3 visualization on `/graph`.

## Multi-tenancy & auth

Every cross-user query is user-scoped: ChromaDB queries **require** a `user_id` where-clause (enforced by `embedding_service.query_similar`), and Supabase storage RLS keys on the `user_id` first path segment (`supabase/setup_notes.sql`). Auth is Supabase JWT: the frontend (`src/lib/api.js` axios interceptor) attaches the session access token as a Bearer header; backend `middleware/auth.py` verifies by local HS256 decode using `SUPABASE_JWT_SECRET`, falling back to the Supabase Auth API.

## Backend middleware order matters

FastAPI runs middleware **last-added → first**. Current order (`main.py`): CORSMiddleware → `CORSSafeSlowAPIMiddleware` (custom SlowAPI subclass that passes OPTIONS through — a previous CORS-400 fix) → GZip → RequestID. Add new middleware with the comment block at `main.py:87-101` in mind, and keep the OPTIONS pass-through or preflight will break.

## Frontend structure

Routes live in `src/router.jsx` (React Router 7 `createBrowserRouter`): public `/` (LandingPage) and `/auth`; protected routes under `AppLayout` — `/dashboard`, `/search`, `/memory/:id`, `/graph` (lazy), `/chat` (lazy), `/syllabus`. `AuthProvider` wraps the app; data fetching via TanStack Query + the shared axios `api` instance. Backend interactions happen through `src/hooks/` (`useSearch`, `useChat`, `useMemories`, `usePlates`, `useIngestionJob`).

## Design system

**"Warm Editorial Minimalism"** — authoritative spec in `Antigravity/design.md`, encoded as Tailwind v4 `@theme` tokens in `src/index.css`. Warm beige canvas `#F7F5F0`, stone text colors, soft blue accents (`blue-200/300`) used sparingly, sharp `rounded-sm` corners. Hard prohibitions: no dark mode as default, no neon/glow/gradients, no glassmorphism/backdrop-blur, no `rounded-full` primary buttons, no emoji-heavy UI (use SVG line icons from `lucide-react`). Follow this aesthetic for any frontend work.

## Gotchas & conventions

- **`apps/backend/data/chromadb/chroma.sqlite3` is committed to git** (gitignore only covers the root `data/chromadb/` path). It appears as a modified file after backend runs — don't include unrelated Chroma data churn in commits.
- **Extension is a stub** — don't assume `src/` exists; build it out if extension work is requested.
- `pnpm-workspace.yaml` has a literal placeholder `allowBuilds: esbuild: set this to true or false` — set it to `true` if the esbuild postinstall fails during `pnpm install`.
- Celery tasks are sync and drive async services via `asyncio.run(...)` — keep that pattern when adding task stages.
- AI provider split is deliberate: Gemini (`gemini-1.5-flash`, `gemini-embedding-2`) for synthesis/vision/clustering/embeddings, Groq (`llama-3.1-8b-instant`) for chat RAG, faster-whisper for transcription.
- `instagram_cookies.txt`, `graphify-out/`, and `venv/` are gitignored local/scratch state.
- `tasks.md` is a large in-repo planning doc (task history); not required reading for code changes.
