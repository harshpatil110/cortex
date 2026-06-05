import os

import chromadb
from openai import OpenAI
from sentence_transformers import SentenceTransformer

# Load environment variables
CHROMA_PERSIST_PATH = os.getenv("CHROMA_PERSIST_PATH", "./data/chromadb")
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "local")  # "openai" or "local"


class EmbeddingService:
    def __init__(self):
        # Initialize ChromaDB PersistentClient
        self.chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_PATH)

        # Get or create the collection with cosine distance metric
        self.collection = self.chroma_client.get_or_create_collection(
            name="mnemonic_memories", metadata={"hnsw:space": "cosine"}
        )

        # Initialize Provider
        self.provider = EMBEDDING_PROVIDER
        if self.provider == "openai":
            self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            self.model = None
        elif self.provider == "local":
            self.model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
            self.openai_client = None
        else:
            raise ValueError(f"Unsupported embedding provider: {self.provider}")

    def embed_text(self, text: str) -> list[float]:
        """Generates a single vector embedding based on the provider."""
        if self.provider == "openai":
            response = self.openai_client.embeddings.create(
                input=[text], model="text-embedding-3-small"
            )
            return response.data[0].embedding
        elif self.provider == "local":
            embedding = self.model.encode(text)
            return embedding.tolist()

    def upsert_memory(self, id: str, text: str, metadata: dict) -> None:
        """Inserts or updates a vector in ChromaDB with strictly enforced metadata."""
        # Enforce metadata schema
        required_keys = {
            "user_id",
            "content_type",
            "created_at",
            "plate_id",
            "tags_csv",
        }
        for key in required_keys:
            if key not in metadata:
                raise ValueError(f"Missing required metadata key: {key}")

        # Validate types
        if not isinstance(metadata["user_id"], str):
            raise TypeError("user_id must be a string")
        if not isinstance(metadata["created_at"], int):
            raise TypeError("created_at must be an integer (unix timestamp)")

        embedding = self.embed_text(text)

        self.collection.upsert(
            ids=[id], embeddings=[embedding], documents=[text], metadatas=[metadata]
        )

    def query_similar(
        self, text: str, user_id: str, n: int = 20, filters: dict = None
    ) -> list[dict]:
        """Queries the collection with mandatory multi-tenant isolation (user_id)."""
        if not user_id:
            raise ValueError(
                "user_id is mandatory for querying to enforce data isolation."
            )

        embedding = self.embed_text(text)

        # Enforce user_id isolation in the where clause
        where_clause = {"user_id": user_id}

        # If additional filters are provided, combine them using $and
        if filters:
            where_clause = {"$and": [{"user_id": user_id}, filters]}

        results = self.collection.query(
            query_embeddings=[embedding], n_results=n, where=where_clause
        )

        # Format results
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
        results = self.collection.get(ids=ids)

        formatted_results = []
        if results and results["ids"]:
            for i in range(len(results["ids"])):
                formatted_results.append(
                    {
                        "id": results["ids"][i],
                        "document": (
                            results["documents"][i] if results["documents"] else None
                        ),
                        "metadata": (
                            results["metadatas"][i] if results["metadatas"] else None
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
