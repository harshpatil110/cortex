# Cortex Project Rules & Session Context (rule.md)

## Session Initialization Objective
This file serves as the core source of truth for the IDE and AI collaboration sessions. Read this document at the start of every session to establish absolute context regarding the architectural mandates, technical stack constraints, directory layout, and development standards for **Cortex**.

---

## 1. Technical Stack Configuration

| Layer | Technology | Operational Purpose |
| :--- | :--- | :--- |
| **Frontend** | React.js, Tailwind CSS (JS/JSX) | Single Page Application (SPA), state management, layout execution. **Strictly JavaScript (No TypeScript).** |
| **Backend** | Python 3.11+, FastAPI | Asynchronous event routing, ingestion workflows, scraping management. |
| **Relational DB** | Supabase (PostgreSQL) | Auth management, structured storage, JSONB data, full-text indexing. |
| **Vector DB** | ChromaDB | Localized high-dimensional vector space storage and semantic lookup. |
| **AI Inference** | NVIDIA NIM API keys | Execution of transcription, frame vision processing, summarization, and embedding vectors. |

---

## 2. Directory Architecture

The workspace is split into isolated root directories. Do not pollute or cross-contaminate codebases.

```text
/cortex-workspace
├── /apps
│   ├── /backend
│   │   ├── /routers      # FastAPI routing layers
│   │   ├── /services     # Video downloading, FFMPEG isolation, OCR processing
│   │   ├── /schemas      # Pydantic V2 definitions
│   │   ├── main.py       # Application entry point
│   │   └── /tests        # Comprehensive automated test suites
│   ├── /frontend
│   │   ├── /src
│   │   │   ├── /components   # UI elements (cards, text fields, layouts)
│   │   │   ├── /pages        # Main views (Dashboard, Graph Canvas, Chat Container)
│   │   │   ├── /hooks        # Custom React hooks
│   │   │   └── App.jsx       # Main interface routing (JSX)
│   │   ├── /public       # Static assets
│   │   └── package.json
│   └── /extension
│       ├── /src
│       │   ├── popup.jsx # Chrome extension React popup
│       │   └── background.js # MV3 Service worker
│       └── manifest.json
├── turbo.json
├── pnpm-workspace.yaml
└── rule.md               # Continuous memory marker
3. UI/UX Design Mandates
The frontend must adhere strictly to a Warm Editorial Minimalist visual footprint.

Color Primitives: Use strictly warm, paper-like backgrounds (bg-[#FAF9F6] or bg-[#F5F5F0]). Accent text and structural rules use crisp neutral stone variants (text-stone-900, border-stone-200).

Anti-Patterns: Dark Mode is strictly prohibited. High-saturation neon highlights, gradients, and heavy drop shadows are banned. Use fine 1px structural borders to separate components.

Typography: High-contrast editorial execution. Large, sharp headers (Instrument Serif or similar) paired with highly legible body copy (DM Sans or similar). Rely heavily on wide whitespace padding and clean layouts.

4. Development & Code Execution Rules
4.1. Core Coding Paradigms
Frontend (JavaScript Strictness): TypeScript is strictly prohibited in this project. All React frontend and Chrome extension code must be written in standard modern JavaScript (ES6+) using .js and .jsx extensions. Do not use @typescript-eslint or configure tsconfig.json. Use standard prop-types for component validation if necessary.

Backend (Python Strictness): All Python backend models must use strict Pydantic V2 definitions. Functional methods require full Python type-hint signatures (def my_func(user_id: str) -> dict:).

Asynchronous Bounds: All database connectivity, web scraping instances, file processing pipelines, and inference calls must utilize async def and non-blocking libraries to prevent thread blocking during background tasks.

4.2. Ingestion & Security Guardrails
Scraping Isolation: Isolate all custom extraction scrapers (yt-dlp or browser automation scripts) behind dedicated failure traps. Implement automatic fallback loops to handle unpredictable schema changes or rate limits gracefully.

User Space Separation: Every query targeting the Relational Database or ChromaDB must explicitly filter using the session's active, verified user ID (user_id). Data cross-contamination between different user profiles must be prevented at the system architecture level.

5. Testing & Verification Mandate
Every code update, endpoint insertion, or helper rewrite must accompany structured test validation instances before deployment.

Backend Validation: Maintain a mirroring structure inside /backend/tests. Implement integration verification tests using pytest and httpx.AsyncClient to validate:

API response structures and error status code branches.

Successful conversion of raw multi-format inputs into structured JSON outputs.

Accurate RRF (Reciprocal Rank Fusion) calculation loops across Supabase and ChromaDB search layers.

Frontend Validation: Place component test instances alongside views to verify that canvas rendering elements, graph node layouts, and data entry mutations operate efficiently without processing drops.