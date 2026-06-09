import asyncio
import json
import logging
import os
from typing import List, Literal

import httpx
from pydantic import BaseModel, Field, ValidationError

logger = logging.getLogger(__name__)

try:
    import google.generativeai as genai

    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


class CodeBlock(BaseModel):
    language: str
    code: str
    description: str


class MemorySummary(BaseModel):
    title: str = Field(..., max_length=150)
    abstract: str
    takeaways: List[str]
    code_blocks: List[CodeBlock]
    tags: List[str]
    difficulty: Literal["beginner", "intermediate", "advanced", ""] = ""
    tech_stack: List[str]


class SynthesisService:
    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "gemini").lower()
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

        if self.provider == "gemini":
            if GENAI_AVAILABLE and self.gemini_api_key:
                genai.configure(api_key=self.gemini_api_key)
                self.model = genai.GenerativeModel("gemini-1.5-flash")
            else:
                logger.warning("Gemini API is not configured. Falling back to ollama.")
                self.provider = "ollama"
                self.model = None

        prompt_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "prompts", "synthesis_prompt.txt"
        )
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                self.system_prompt = f.read()
        except Exception as e:
            logger.error(f"Could not read synthesis prompt: {e}")
            self.system_prompt = """
            You are a technical knowledge extraction engine.
            Return ONLY a valid JSON object matching the requested schema.
            Required Schema:
            {
              "title": "...", "abstract": "...", "takeaways": [],
              "code_blocks": [], "tags": [], "difficulty": "beginner",
              "tech_stack": []
            }
            """

    async def synthesize(self, payload: dict) -> dict:
        """
        Takes raw extracted texts and returns a validated Pydantic JSON structure.
        """
        content_type = payload.get("content_type", "unknown")
        source_url = payload.get("source_url", "unknown")
        creator_handle = payload.get("creator_handle", "unknown")
        caption_or_title = payload.get("caption_or_title", "unknown")
        raw_transcript = payload.get("raw_transcript", "")
        ocr_extracted_text = payload.get("ocr_extracted_text", "")
        hashtags = payload.get("hashtags", "")

        synthesis_input = f"""
{self.system_prompt}

---

SOURCE: {content_type} from {source_url}
CREATOR: {creator_handle}
CAPTION/TITLE: {caption_or_title}
TRANSCRIPT: {raw_transcript}
VISUAL OCR: {ocr_extracted_text}
HASHTAGS: {hashtags}
"""

        max_retries = 1
        last_error = None
        current_input = synthesis_input

        for attempt in range(max_retries + 1):
            try:
                if self.provider == "gemini":
                    raw_response = await self._call_gemini(current_input)
                else:
                    raw_response = await self._call_ollama(current_input)

                json_str = self._clean_json_response(raw_response)

                data = json.loads(json_str)
                validated_model = MemorySummary(**data)

                logger.info("Successfully synthesized memory data.")
                return validated_model.model_dump()

            except (json.JSONDecodeError, ValidationError) as e:
                last_error = e
                logger.warning(
                    f"Synthesis validation failed on attempt {attempt + 1}: {e}"
                )

                if attempt < max_retries:
                    current_input += (
                        "\n\nReturn ONLY the raw JSON object. "
                        "No explanation. No markdown syntax."
                    )

        logger.error(
            "Synthesis failed completely. Falling back to error schema. "
            f"Last error: {last_error}"
        )
        return self._get_fallback_schema()

    async def _call_gemini(self, prompt: str) -> str:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, self.model.generate_content, prompt)
        return response.text

    async def _call_ollama(self, prompt: str) -> str:
        async with httpx.AsyncClient(timeout=120.0) as client:
            url = f"{self.ollama_base_url}/api/generate"
            payload = {"model": "llama3.1:8b", "prompt": prompt, "stream": False}
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")

    def _clean_json_response(self, raw_response: str) -> str:
        clean_text = raw_response.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        if clean_text.startswith("```"):
            clean_text = clean_text[3:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
        return clean_text.strip()

    def _get_fallback_schema(self) -> dict:
        return {
            "title": "Processing Error",
            "abstract": "Failed to synthesize memory structures safely.",
            "takeaways": [],
            "code_blocks": [],
            "tags": ["error"],
            "difficulty": "intermediate",
            "tech_stack": [],
        }
