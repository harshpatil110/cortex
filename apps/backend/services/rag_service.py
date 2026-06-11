import json
import logging
import os
import re
from typing import AsyncGenerator

import tiktoken
from openai import AsyncOpenAI

from services.embedding_service import embedding_service
from utils.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


class RagService:
    def __init__(self):
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.client = AsyncOpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=self.groq_api_key or "dummy",
        )
        self.tokenizer = tiktoken.get_encoding("cl100k_base")

    async def stream_chat(
        self, user_id: str, messages: list[dict], user_message: str
    ) -> AsyncGenerator[str, None]:
        supabase = get_supabase_client()
        if not supabase:
            yield f"data: {json.dumps({'error': 'Supabase client not available'})}\n\n"
            return

        try:
            query_vector = await embedding_service.embed_text(user_message)

            results = embedding_service.collection.query(
                query_embeddings=[query_vector],
                n_results=6,
                where={"user_id": user_id},
            )

            memory_ids = []
            if results and results.get("ids") and results["ids"][0]:
                memory_ids = results["ids"][0]

            memories = []
            if memory_ids:
                db_res = (
                    supabase.table("user_memories")
                    .select(
                        "id, title, ai_summary, raw_transcript, "
                        "code_blocks, thumbnail_path"
                    )
                    .in_("id", memory_ids)
                    .execute()
                )
                memories = db_res.data or []

            context_str = ""
            current_tokens = 0
            max_tokens = 4000

            cited_memories = {}

            for mem in memories:
                mem_id = mem.get("id")

                title = mem.get("title")
                if not title:
                    ai_summary = mem.get("ai_summary", {})
                    title = (
                        ai_summary.get("title", "Untitled")
                        if isinstance(ai_summary, dict)
                        else "Untitled"
                    )

                abstract = ""
                ai_summary = mem.get("ai_summary", {})
                if isinstance(ai_summary, dict):
                    abstract = ai_summary.get("abstract", "")

                code_blocks = mem.get("code_blocks") or ""
                if isinstance(code_blocks, list):
                    code_blocks = "\n".join(code_blocks)

                raw_transcript = mem.get("raw_transcript") or ""

                cited_memories[title] = {
                    "id": mem_id,
                    "thumbnail_path": mem.get("thumbnail_path"),
                }

                mem_header = (
                    f'<memory id="{mem_id}" title="{title}">\n'
                    f"Abstract: {abstract}\nCode: {code_blocks}\nTranscript: "
                )
                mem_footer = "\n</memory>\n"

                header_tokens = len(self.tokenizer.encode(mem_header + mem_footer))
                if current_tokens + header_tokens >= max_tokens:
                    break

                available_for_transcript = max_tokens - current_tokens - header_tokens
                transcript_tokens = self.tokenizer.encode(raw_transcript)

                if len(transcript_tokens) > available_for_transcript:
                    truncated_transcript = self.tokenizer.decode(
                        transcript_tokens[:available_for_transcript]
                    )
                    context_str += mem_header + truncated_transcript + mem_footer
                    current_tokens = max_tokens
                    break
                else:
                    context_str += mem_header + raw_transcript + mem_footer
                    current_tokens += header_tokens + len(transcript_tokens)

            system_prompt = (
                "You are the user's personal knowledge assistant. Answer questions "
                "using ONLY the memory sources provided below. "
                "After each factual claim, cite its source as [Memory Title]. "
                "If the answer cannot be found in the sources, say: 'I don't have "
                "that information in your saved memories.' When providing code "
                "or commands, format them in code blocks.\n\n"
                f"{context_str}"
            )

            api_messages = [{"role": "system", "content": system_prompt}]

            recent_history = messages[-8:]
            for msg in recent_history:
                api_messages.append({"role": msg["role"], "content": msg["content"]})

            api_messages.append({"role": "user", "content": user_message})

            stream = await self.client.chat.completions.create(
                model="llama3-8b-8192", messages=api_messages, stream=True
            )

            full_response = ""
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    token = chunk.choices[0].delta.content
                    full_response += token
                    yield f"data: {json.dumps({'token': token})}\n\n"

            citations = set(re.findall(r"\[(.*?)\]", full_response))

            sources = []
            for cited_title in citations:
                if cited_title in cited_memories:
                    mem_info = cited_memories[cited_title]
                    url = None
                    t_path = mem_info.get("thumbnail_path")
                    if t_path:
                        try:
                            signed_url_res = supabase.storage.from_(
                                "thumbnails"
                            ).create_signed_url(t_path, 3600)
                            url = signed_url_res.get("signedURL")
                        except Exception as e:
                            logger.warning(f"Signed URL failed for {t_path}: {e}")

                    sources.append(
                        {
                            "memory_id": mem_info["id"],
                            "title": cited_title,
                            "thumbnail_url": url,
                        }
                    )

            yield f"data: {json.dumps({'type': 'sources', 'data': sources})}\n\n"

        except Exception as e:
            logger.error(f"RAG chat failed: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"


rag_service = RagService()
