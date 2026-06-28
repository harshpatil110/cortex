import json
import logging
import os

from openai import AsyncOpenAI

from utils.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


class SyllabusService:
    def __init__(self):
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.client = AsyncOpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=self.groq_api_key or "dummy",
        )

    async def generate_syllabus(
        self, user_id: str, memory_ids: list[str], topic_title: str
    ) -> dict:
        supabase = get_supabase_client()
        if not supabase:
            raise Exception("Supabase client not available")

        # Fetch memories
        db_res = (
            supabase.table("user_memories")
            .select("id, ai_summary")
            .in_("id", memory_ids)
            .eq("user_id", user_id)
            .execute()
        )
        memories = db_res.data or []
        if not memories:
            raise Exception("No memories found or access denied")

        # Build prompt context
        context_lines = []
        for m in memories:
            if not isinstance(m, dict):
                continue
            summary = m.get("ai_summary") or {}
            title = summary.get("title") if isinstance(summary, dict) else "Untitled"
            abstract = summary.get("abstract", "") if isinstance(summary, dict) else ""
            context_lines.append(
                f"ID: {m.get('id', 'unknown')} | Title: {title} | Summary: {abstract}"
            )

        context_str = "\n".join(context_lines)

        system_prompt = (
            f'You have {len(memories)} learning resources about "{topic_title}".\n'
            "Order them from foundational to advanced, "
            "grouping by prerequisite concept.\n"
            "For each step, write 2-3 learning objectives.\n"
            "Assign an estimated learning time in minutes.\n"
            "Return ONLY JSON matching exactly this structure:\n"
            "{\n"
            f'  "title": "{topic_title} Curriculum",\n'
            '  "steps": [\n'
            "    {\n"
            '      "order": 1,\n'
            '      "memory_id": "string",\n'
            '      "step_title": "string",\n'
            '      "objectives": ["string"],\n'
            '      "estimated_minutes": 10,\n'
            '      "concept_group": "string"\n'
            "    }\n"
            "  ]\n"
            "}"
        )

        user_prompt = f"Resources:\n{context_str}"

        try:
            response = await self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
            )

            result_json = response.choices[0].message.content
            if not result_json:
                raise Exception("LLM returned empty response")
            result = json.loads(result_json)
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            raise Exception("Failed to generate syllabus from AI")

        # Save to DB
        insert_data = {
            "user_id": user_id,
            "title": result.get("title", f"{topic_title} Curriculum"),
            "topic_context": topic_title,
            "syllabus_structure": result,
        }

        try:
            insert_res = (
                supabase.table("generated_learning_paths").insert(insert_data).execute()
            )
            if (
                insert_res.data
                and isinstance(insert_res.data, list)
                and len(insert_res.data) > 0
            ):
                data = insert_res.data[0]
                if isinstance(data, dict):
                    return data
            return {"id": "temp_id", **insert_data}
        except Exception as e:
            logger.error(f"Failed to save syllabus to Supabase: {e}")
            return {"id": "temp_id", **insert_data}

    async def get_syllabuses(self, user_id: str) -> list[dict]:
        supabase = get_supabase_client()
        if not supabase:
            return []
        res = (
            supabase.table("generated_learning_paths")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
        if res.data and isinstance(res.data, list):
            return [d for d in res.data if isinstance(d, dict)]
        return []

    async def get_syllabus(self, user_id: str, syllabus_id: str) -> dict:
        supabase = get_supabase_client()
        if not supabase:
            raise Exception("DB Error")
        res = (
            supabase.table("generated_learning_paths")
            .select("*")
            .eq("id", syllabus_id)
            .eq("user_id", user_id)
            .execute()
        )
        if not res.data or not isinstance(res.data, list) or len(res.data) == 0:
            raise Exception("Not found")
        data = res.data[0]
        if not isinstance(data, dict):
            raise Exception("Invalid data format")
        return data


syllabus_service = SyllabusService()
