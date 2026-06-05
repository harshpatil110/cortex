import os

import pytest

from services.embedding_service import EmbeddingService


@pytest.fixture
def service():
    # Force local provider for testing
    os.environ["EMBEDDING_PROVIDER"] = "local"
    # Use an in-memory or temporary directory for ChromaDB
    os.environ["CHROMA_PERSIST_PATH"] = "./data/test_chromadb"

    svc = EmbeddingService()
    yield svc

    # Cleanup test data
    try:
        svc.chroma_client.delete_collection("mnemonic_memories")
    except Exception:
        pass


def test_embedding_lifecycle(service):
    test_id = "test_memory_1"
    user_1 = "user_123"
    user_2 = "user_456"

    metadata = {
        "user_id": user_1,
        "content_type": "text",
        "created_at": 1625097600,
        "plate_id": "plate_abc",
        "tags_csv": "test,pytest",
    }

    # 1. Upsert
    service.upsert_memory(
        id=test_id,
        text="This is a test memory about artificial intelligence.",
        metadata=metadata,
    )

    # Verify retrieval by ID
    fetched = service.get_by_ids([test_id])
    assert len(fetched) == 1
    assert fetched[0]["id"] == test_id
    assert fetched[0]["metadata"]["user_id"] == user_1

    # 2. Query (Valid User)
    results_user_1 = service.query_similar(
        "artificial intelligence", user_id=user_1, n=5
    )
    assert len(results_user_1) > 0
    assert results_user_1[0]["id"] == test_id

    # 3. Query (Cross-User Isolation Check)
    results_user_2 = service.query_similar(
        "artificial intelligence", user_id=user_2, n=5
    )
    assert len(results_user_2) == 0

    # 4. Delete
    service.delete_memory(id=test_id)

    # Verify deletion
    fetched_after = service.get_by_ids([test_id])
    assert len(fetched_after) == 0
