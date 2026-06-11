import asyncio
import logging
import os
from datetime import datetime, timezone
from typing import Any

import chromadb

try:
    import google.generativeai as genai

    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


CHROMA_PERSIST_PATH = os.getenv("CHROMA_PERSIST_PATH", "./data/chromadb")

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self):
        self.chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_PATH)

        self.collection = self.chroma_client.get_or_create_collection(
            name="mnemonic_memories", metadata={"hnsw:space": "cosine"}
        )

        self.api_key = os.getenv("GEMINI_API_KEY")
        if GENAI_AVAILABLE and self.api_key:
            genai.configure(api_key=self.api_key)
        else:
            logger.warning(
                "Gemini API is not configured or google-generativeai not installed."
            )

    async def embed_text(self, text: str) -> list[float]:
        """Generates a single vector embedding using Gemini API."""
        if not GENAI_AVAILABLE or not self.api_key:
            raise RuntimeError("Gemini API is not available for embedding.")

        def _call_embed():
            response = genai.embed_content(
                model="models/text-embedding-004", content=text
            )
            return response["embedding"]

        return await asyncio.to_thread(_call_embed)

    async def upsert_memory(
        self, memory_id: str, embedding_text: str, metadata: dict
    ) -> list[float]:
        """Inserts or updates a vector in ChromaDB with fault-tolerance."""
        # Note: Importing supabase inside the function to avoid circular imports if any
        from utils.supabase_client import get_supabase_client

        supabase = get_supabase_client()

        max_retries = 3
        for attempt in range(max_retries + 1):
            try:
                embedding = await self.embed_text(embedding_text)

                def _upsert():
                    self.collection.upsert(
                        ids=[memory_id],
                        embeddings=[embedding],
                        documents=[embedding_text],
                        metadatas=[metadata],
                    )

                await asyncio.to_thread(_upsert)

                if supabase:

                    def _update_db_success():
                        supabase.table("user_memories").update(
                            {
                                "indexed": True,
                                "updated_at": datetime.now(timezone.utc).isoformat(),
                            }
                        ).eq("id", memory_id).execute()

                    await asyncio.to_thread(_update_db_success)

                logger.info(f"Successfully embedded and upserted memory {memory_id}")
                return embedding

            except Exception as e:
                logger.warning(
                    f"Embedding/Upsert attempt {attempt + 1} failed "
                    f"for {memory_id}: {e}"
                )
                if attempt < max_retries:
                    await asyncio.sleep(5)
                else:
                    logger.error(
                        f"Failed to upsert memory {memory_id} after "
                        f"{max_retries} retries."
                    )
                    if supabase:

                        def _update_db_fail():
                            supabase.table("user_memories").update(
                                {"indexed": False}
                            ).eq("id", memory_id).execute()

                        try:
                            await asyncio.to_thread(_update_db_fail)
                        except Exception as inner_e:
                            logger.error(
                                f"Failed to set indexed=False for {memory_id}: "
                                f"{inner_e}"
                            )

    def query_similar(
        self, text: str, user_id: str, n: int = 20, filters: dict | None = None
    ) -> list[dict]:
        """Queries the collection with mandatory multi-tenant isolation (user_id)."""
        if not user_id:
            raise ValueError(
                "user_id is mandatory for querying to enforce data isolation."
            )

        # Synchronous wrapper for embed_text just for querying
        # since it's typically called from sync context or we can run an event loop
        loop = asyncio.get_event_loop()
        embedding = loop.run_until_complete(self.embed_text(text))

        where_clause: dict[str, Any] = {"user_id": user_id}

        if filters:
            where_clause = {"$and": [{"user_id": user_id}, filters]}

        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=n,
            where=where_clause,  # type: ignore
        )

        formatted_results = []
        if results and results["ids"] and len(results["ids"]) > 0:
            for i in range(len(results["ids"][0])):
                formatted_results.append(
                    {
                        "id": results["ids"][0][i],
                        "document": (
                            results["documents"][0][i] if results["documents"] else None
                        ),
                        "metadata": (
                            results["metadatas"][0][i] if results["metadatas"] else None
                        ),
                        "distance": (
                            results["distances"][0][i] if results["distances"] else None
                        ),
                    }
                )

        return formatted_results

    def delete_memory(self, id: str) -> None:
        """Removes the vector from ChromaDB by its ID string."""
        self.collection.delete(ids=[id])

    def get_by_ids(self, ids: list[str]) -> list[dict]:
        """Core batch fetch method to pull documents/metadata from ChromaDB by IDs."""
        results = self.collection.get(
            ids=ids, include=["embeddings", "documents", "metadatas"]
        )

        formatted_results = []
        if results and results.get("ids"):
            for i in range(len(results["ids"])):
                formatted_results.append(
                    {
                        "id": results["ids"][i],
                        "embedding": (
                            results["embeddings"][i]
                            if results.get("embeddings")
                            else None
                        ),
                        "document": (
                            results["documents"][i]
                            if results.get("documents")
                            else None
                        ),
                        "metadata": (
                            results["metadatas"][i]
                            if results.get("metadatas")
                            else None
                        ),
                    }
                )

        return formatted_results

    def ping(self) -> dict:
        """Status/ping method for ChromaDB health check."""
        try:
            heartbeat = self.chroma_client.heartbeat()
            return {"status": "ok", "heartbeat": heartbeat}
        except Exception as e:
            return {"status": "error", "message": str(e)}


# Singleton instance
embedding_service = EmbeddingService()
