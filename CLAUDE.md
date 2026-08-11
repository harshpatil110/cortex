# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Cortex** is a personal AI memory engine that cures scroll fatigue: it ingests internet content (web pages, PDFs, images, videos/Instagram reels), extracts text/audio/OCR, synthesizes structured AI summaries, embeds them into a vector DB, clusters them into "plates" (categories), and exposes hybrid search and RAG chat.

The architecture has been deliberately simplified to a lightweight single-user local prototype: **no Celery, no Redis, no Docker, no Sentry, no rate limiting, and no multi-user auth.** The backend is a single FastAPI process that runs the ingestion pipeline inline via `BackgroundTasks`.

Monorepo managed with **pnpm workspaces + Turborepo**. Three apps:

- `apps/frontend` — React 18 + Vite + Tailwind CSS v4 SPA
- `apps/backend` — Python 3.11+ FastAPI (no package.json; not part of turbo)
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
The backend is **not** started by `pnpm dev` — it must be launched separately (below). Note `pnpm lint` at the root currently fails because the extension app is an empty stub (no `.js/.jsx` files to lint) — this is pre-existing.

### Python backend (`apps/backend`)
```bash
# from apps/backend
# use the existing venv (apps/backend/venv) or create one, then:
pip install -e ".[dev]"          # installs app + isort/flake8/pytest (black not in venv)

uvicorn main:app --reload         # API server on http://127.0.0.1:8000 (or: python main.py)
# No Celery worker/beat needed — ingestion runs via FastAPI BackgroundTasks.

isort --check . && flake8 .       # Python lint (black --check also used by CI)
pytest                            # tests (tests/test_embedding_service.py is currently stale/broken)
```
Backend tests are **not** wired into turbo; run pytest directly. `apps/backend/.flake8` and root `.flake8` are identical (max-line-length 88, ignore E203). flake8 needs `--exclude=venv` locally because pyflakes hits a RecursionError on a sympy file inside the venv.

## Environment Variables

`.env` files are gitignored; `.env.example` is the inventory. Key ones by app:

**Backend** (`apps/backend/.env`): `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY` (Supabase storage/DB), `GEMINI_API_KEY` (embeddings, synthesis, vision, plate naming), `GROQ_API_KEY` (RAG chat + transcription), `CHROMA_PERSIST_PATH` (default `./chroma_data`), `WHISPER_PROVIDER`/`WHISPER_MODEL`, `LLM_PROVIDER` (`gemini` default, falls back to `ollama`), `OLLAMA_BASE_URL`, `OPENAI_API_KEY`.

**Frontend** (`apps/frontend/.env`): `VITE_API_BASE_URL` (default `http://localhost:8000`). The frontend no longer talks to Supabase directly (all DB/storage calls go through the backend).

## Architecture: the memory lifecycle

The core is one pipeline that every ingested item flows through:

**1. Ingest** — `routers/ingest.py`: `POST /api/ingest/file` (upload → Supabase Storage) or `/url` (scrape via `WebScraper`/`InstagramScraper`, download assets → Storage). Inserts a `user_memories` row + `job_tracking` row, then `background_tasks.add_task(process_memory, ...)` and returns `202` with `job_id`. The endpoint responds instantly; the pipeline runs after the response is sent.

**2. Processing pipeline** — `services/ingestion_service.py` `async def process_memory(job_id, memory_id, content_type)` is the orchestrator (replaced the old Celery worker): a linear list of named stages selected by `content_type` (video/reel: THUMBNAIL → AUDIO_EXTRACT → TRANSCRIBING → OCR_FRAMES → SYNTHESIZING → EMBEDDING → CLUSTERING → MAPPING_RELATIONS; pdf: …→ PDF_EXTRACT →…; image: …→ OCR_IMAGE →…; web_page: …→ SYNTHESIZING →…). Each stage writes its name to the `job_tracking` row so the frontend streams progress via SSE (`GET /api/jobs/{job_id}/stream`). The whole body is wrapped in try/except: success writes `COMPLETE`, failure logs and writes `FAILED` so the UI never hangs. Extraction uses `faster-whisper` (audio), `PyMuPDF` (PDF), Gemini vision (video frames/images), OCR via the processors in `services/processors/`.

**3. Synthesis** — `SYNTHESIZING` stage calls Gemini (`gemini-1.5-flash`, `LLM_PROVIDER=ollama` fallback) with `prompts/synthesis_prompt.txt` and Pydantic-validates the result into the `ai_summary` JSON: `title/abstract/takeaways/code_blocks/tags/difficulty/tech_stack`. On repeated JSON/validation failure it returns a safe fallback schema, never throws.

**4. Embedding** — `services/embedding_service.py`: `upsert_memory` builds a text blob (summary + transcript + OCR + creator) and embeds via Gemini `gemini-embedding-2` into ChromaDB collection `mnemonic_memories` (cosine, `chromadb.PersistentClient` at `CHROMA_PERSIST_PATH`), marks `indexed=true`, then awaits `clustering_service.cluster_new_memory(...)` and `graph_service.map_relationships(...)` inline.

**5. Clustering into "Plates"** — `services/clustering_service.py`: a memory is compared (cosine sim) against each plate's centroid (mean of its `centroid_member_ids` embeddings); if sim > **0.72** it joins that plate, else a new plate is created with a Gemini-generated 2–3 word name. (The old nightly Celery-beat KMeans re-cluster in `workers/recluster_task.py` was removed along with Celery.)

**6. Search** — `routers/search.py` + `services/search_service.py`: `mode=hybrid` (default) runs lexical (Supabase RPC `lexical_search_memories`) and semantic (ChromaDB vector query, `distance ≤ 0.65`) in parallel and merges with **Reciprocal Rank Fusion**. Results cached in-process 5 min keyed by SHA-256 of params (`services/cache_service.py` is now a simple in-memory TTL dict). `X-Total-Count` header.

**7. Chat / RAG** — `routers/chat.py` + `services/rag_service.py`: embeds the question, pulls top-6 memories from ChromaDB, builds a ~4000-token context window (truncating per-memory transcripts), streams from Groq (`llama-3.1-8b-instant`) over SSE. Citations are parsed from `[Title]` markers in the response and resolved to signed thumbnail URLs.

**8. Graph** — `routers/graph.py`: returns the top-200 most-connected memories + `entity_relationships` edges (fetched in 500-id chunks) for the D3 visualization on `/graph`.

## Single-user auth (bypassed)

Auth is hardcoded for local single-user mode. The backend dependency `middleware/auth.py` `get_current_user` just returns the constant string `"local-cortex-user-001"`; the frontend `contexts/AuthContext.jsx` ships a permanent mock user/session with that same ID. Every DB query and storage path stays scoped to this one user (ChromaDB `where={"user_id": ...}`, Supabase `user_id` columns, storage folder prefix `{user_id}/...`). If you change the ID, change it in **both** files — and note existing data in Supabase under any previous real user UUID will not be visible.

## Backend middleware

`main.py` keeps only CORS (first) and GZip. RequestID, SlowAPI, and Sentry were removed.

## Frontend structure

Routes live in `src/router.jsx` (React Router 7 `createBrowserRouter`): `/` redirects to `/dashboard`; all pages live under `AppLayout` — `/dashboard`, `/search`, `/memory/:id`, `/graph` (lazy), `/chat` (lazy), `/syllabus`. There is no login page. `AuthProvider` still wraps the app (mocked); data fetching via TanStack Query + the shared axios `api` instance. Backend interactions happen through `src/hooks/` (`useSearch`, `useChat`, `useMemories`, `usePlates`, `useIngestionJob`). `src/pages/LandingPage.jsx` still exists but is no longer routed (was the pre-auth marketing page).

## Design system

**"Warm Editorial Minimalism"** — authoritative spec in `Antigravity/design.md`, encoded as Tailwind v4 `@theme` tokens in `src/index.css`. Warm beige canvas `#F7F5F0`, stone text colors, soft blue accents (`blue-200/300`) used sparingly, sharp `rounded-sm` corners. Hard prohibitions: no dark mode as default, no neon/glow/gradients, no glassmorphism/backdrop-blur, no `rounded-full` primary buttons, no emoji-heavy UI (use SVG line icons from `lucide-react`). Follow this aesthetic for any frontend work.

## Gotchas & conventions

- **Stale tracked Chroma file**: `apps/backend/data/chromadb/chroma.sqlite3` was committed to git before the switch to `./chroma_data`; it's now stale and shows as a modified file after backend runs. The active DB lives at `apps/backend/chroma_data/` (gitignored). Consider `git rm --cached` on the old file if its churn bothers you.
- **Extension is a stub** — don't assume `src/` exists; build it out if extension work is requested.
- `pnpm-workspace.yaml` has a literal placeholder `allowBuilds: esbuild: set this to true or false` — set it to `true` if the esbuild postinstall fails during `pnpm install`.
- The ingestion pipeline runs **inside the request process** via `BackgroundTasks` — it's synchronous/blocking in the threadpool and holds up one worker slot; don't rely on it for heavy parallel load.
- The `services/cache_service.py` in-memory cache is per-process; it resets on restart and doesn't survive multiple workers.
- AI provider split is deliberate: Gemini (`gemini-1.5-flash`, `gemini-embedding-2`) for synthesis/vision/clustering/embeddings, Groq (`llama-3.1-8b-instant`) for chat RAG, faster-whisper for transcription.
- `tests/test_embedding_service.py` is stale (calls `upsert_memory(id=, text=, metadata=)` against the current `(memory_id, embedding_text, metadata)` signature) and fails — it predates this refactor.
- `instagram_cookies.txt`, `graphify-out/`, and `venv/` are gitignored local/scratch state.
- `tasks.md` is a large in-repo planning doc (task history); not required reading for code changes.
