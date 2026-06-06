from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class MemoryCard(BaseModel):
    id: str
    content_type: str
    source_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    summary: Optional[str] = None
    created_at: int


class MemoryDetail(MemoryCard):
    raw_transcript: Optional[str] = None
    ocr_extracted_text: Optional[str] = None
    creator_metadata: Dict[str, Any] = Field(default_factory=dict)
    ai_summary: Dict[str, Any] = Field(default_factory=dict)


class SearchResult(BaseModel):
    memory: MemoryCard
    distance: float


class JobStatus(BaseModel):
    id: str
    status: str
    current_stage: Optional[str] = None
    error_message: Optional[str] = None
    memory_id: Optional[str] = None
    user_id: Optional[str] = None


class ChatMessage(BaseModel):
    role: str
    content: str


class PlateSchema(BaseModel):
    id: str
    name: str
    item_count: int
    created_at: int


class SyllabusSchema(BaseModel):
    id: str
    title: str
    topic_context: str
    syllabus_structure: Dict[str, Any]
