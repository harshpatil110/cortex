# flake8: noqa: E402
import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from middleware.request_id import RequestIDMiddleware
from routers import chat, graph, ingest, jobs, memories, plates, search, syllabus
from services.embedding_service import embedding_service
from utils.errors import AppError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cortex.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up Cortex Backend...")

    supabase_url = os.getenv("SUPABASE_URL")
    if supabase_url:
        logger.info("Supabase URL configured.")
    else:
        logger.warning("Supabase URL missing.")

    try:
        chroma_ping = embedding_service.ping()
        logger.info(f"ChromaDB ping: {chroma_ping}")
    except Exception as e:
        logger.error(f"ChromaDB connection error: {e}")

    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    logger.info(f"Redis configured at {redis_url}")

    yield

    logger.info("Shutting down Cortex Backend gracefully...")


app = FastAPI(title="Cortex API", lifespan=lifespan)

origins = [
    os.getenv("VITE_FRONTEND_URL", "http://localhost:5173"),
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(RequestIDMiddleware)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "HTTP_ERROR", "message": exc.detail},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422, content={"error": "VALIDATION_ERROR", "details": exc.errors()}
    )


@app.exception_handler(AppError)
async def app_error_exception_handler(request: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.error_code, "message": exc.message},
    )


app.include_router(ingest.router)
app.include_router(search.router)
app.include_router(memories.router)
app.include_router(graph.router)
app.include_router(chat.router)
app.include_router(syllabus.router)
app.include_router(jobs.router)
app.include_router(plates.router)


@app.get("/api/health")
async def health_check():
    chroma_status = "ok" if embedding_service.ping().get("status") == "ok" else "error"
    return {
        "api": "ok",
        "database": "ok" if os.getenv("SUPABASE_URL") else "error",
        "chromadb": chroma_status,
        "redis": "ok" if os.getenv("REDIS_URL") else "error",
        "celery_workers": 0,
    }


if __name__ == "__main__":
    import asyncio
    import sys

    import uvicorn

    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

        try:
            import uvicorn.loops.asyncio
            import uvicorn.loops.auto

            uvicorn.loops.auto.auto_loop_setup = lambda: None
            uvicorn.loops.asyncio.asyncio_setup = lambda: None
        except Exception:
            pass

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)
