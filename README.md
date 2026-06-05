# Cortex: Personal AI Memory Engine

Cortex is a personal AI memory engine designed to cure scroll fatigue. It automatically ingests internet content, extracts text/audio/OCR data, synthesizes structured summaries, and groups them intelligently.

## Architecture

- **Frontend**: React 18 (JavaScript/JSX), Vite, Tailwind CSS. Focuses on Warm Editorial Minimalism.
- **Backend**: Python 3.11+, FastAPI. Handles asynchronous event routing, ingestion workflows, and processing.
- **Extension**: Chrome Extension (MV3), React.
- **Relational DB**: Supabase (PostgreSQL).
- **Vector DB**: ChromaDB.
- **AI Inference**: NVIDIA NIM API.

## Local Setup

This project uses `pnpm` and Turborepo for monorepo management.

### Prerequisites
- Node.js (v18+)
- pnpm (v8+)
- Python (3.11+)

### Installation

1. Install Node dependencies:
   ```bash
   pnpm install
   ```

2. Setup Environment Variables:
   Copy `.env.example` to `.env` and fill in the required keys.
   ```bash
   cp .env.example .env
   ```

### Running the Apps

Start all apps in development mode:
```bash
pnpm dev
```

### Linting & Formatting

Run linters across all projects:
```bash
pnpm lint
```

Run tests:
```bash
pnpm test
```
