from pydantic import BaseModel


class IngestResponse(BaseModel):
    job_id: str
    memory_id: str
    status: str
