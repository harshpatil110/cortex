import logging
import os
import shutil
import tempfile
import time
from datetime import datetime, timezone

from services.cache_service import cache_service
from services.clustering_service import clustering_service
from services.embedding_service import embedding_service
from services.graph_service import graph_service
from services.thumbnail_service import ThumbnailService
from utils.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


def update_job_stage(
    job_id: str,
    stage_name: str,
    status: str = "PROCESSING",
    error_message: str | None = None,
):
    """Writes the current pipeline stage to the job_tracking table."""
    supabase = get_supabase_client()
    if not supabase:
        logger.warning("Supabase client not configured. Cannot update job stage.")
        return
    update_data = {
        "current_stage": stage_name,
        "status": status,
    }
    if error_message:
        update_data["error_message"] = error_message

    try:
        supabase.table("job_tracking").update(update_data).eq("id", job_id).execute()
        logger.info(f"Job {job_id} updated: {stage_name} ({status})")
    except Exception as e:
        logger.error(f"Failed to update job {job_id}: {e}")


def mock_stage(stage_name: str):
    logger.info(f"Executing mock stage: {stage_name}")
    time.sleep(1)  # Simulate work


async def process_memory(job_id: str, memory_id: str, content_type: str):
    """
    FastAPI BackgroundTask orchestrator.

    Routes incoming memories through the processing pipeline based on content type.
    Runs inside the request lifecycle (no Celery/Redis). Writes every stage to
    job_tracking so the frontend stepper keeps working, and always ends the job in
    COMPLETE or FAILED so the UI never hangs.
    """
    logger.info(
        f"Starting process_memory for job {job_id}, "
        f"memory {memory_id}, type {content_type}"
    )
    supabase = get_supabase_client()
    try:
        update_job_stage(job_id, "QUEUED", "PROCESSING")

        # Pipeline routing based on content type
        if content_type in ["instagram_reel", "mp4", "video"]:
            stages = [
                "THUMBNAIL",
                "AUDIO_EXTRACT",
                "TRANSCRIBING",
                "OCR_FRAMES",
                "SYNTHESIZING",
                "EMBEDDING",
                "CLUSTERING",
                "MAPPING_RELATIONS",
            ]
        elif content_type == "pdf":
            stages = [
                "THUMBNAIL",
                "PDF_EXTRACT",
                "SYNTHESIZING",
                "EMBEDDING",
                "CLUSTERING",
                "MAPPING_RELATIONS",
            ]
        elif content_type == "image":
            stages = [
                "THUMBNAIL",
                "OCR_IMAGE",
                "SYNTHESIZING",
                "EMBEDDING",
                "CLUSTERING",
                "MAPPING_RELATIONS",
            ]
        elif content_type == "web_page":
            stages = [
                "THUMBNAIL",
                "SYNTHESIZING",
                "EMBEDDING",
                "CLUSTERING",
                "MAPPING_RELATIONS",
            ]
        else:
            raise ValueError(f"Unknown content_type: {content_type}")

        wav_temp_path = None

        for stage in stages:
            update_job_stage(job_id, stage, "PROCESSING")
            if stage == "THUMBNAIL":
                service = ThumbnailService()
                service.process_thumbnail(memory_id, content_type)
            elif stage == "PDF_EXTRACT":
                from services.processors.pdf_processor import PDFProcessor

                processor = PDFProcessor()
                if supabase:
                    mem_res = (
                        supabase.table("user_memories")
                        .select("storage_path")
                        .eq("id", memory_id)
                        .execute()
                    )
                    if mem_res.data and isinstance(mem_res.data[0], dict):
                        storage_path = mem_res.data[0].get("storage_path")
                        if storage_path:
                            bucket = storage_path.split("/")[0]
                            file_path_in_bucket = "/".join(storage_path.split("/")[1:])
                            temp_pdf = os.path.join(
                                tempfile.gettempdir(), f"source_{memory_id}.pdf"
                            )
                            try:
                                res = supabase.storage.from_(bucket).download(
                                    file_path_in_bucket
                                )
                                with open(temp_pdf, "wb") as f:
                                    f.write(res)
                                extracted_text = processor.process(temp_pdf)
                                supabase.table("user_memories").update(
                                    {"raw_transcript": extracted_text}
                                ).eq("id", memory_id).execute()
                            except Exception as e:
                                logger.error(
                                    f"PDF extraction failed for {memory_id}: {e}"
                                )
                            finally:
                                if os.path.exists(temp_pdf):
                                    os.remove(temp_pdf)
            elif stage == "AUDIO_EXTRACT":
                from services.processors.audio_processor import extract_audio

                if supabase:
                    mem_res = (
                        supabase.table("user_memories")
                        .select("storage_path")
                        .eq("id", memory_id)
                        .execute()
                    )
                    if mem_res.data:
                        storage_path = mem_res.data[0].get("storage_path")
                        if storage_path:
                            bucket = storage_path.split("/")[0]
                            file_path_in_bucket = "/".join(storage_path.split("/")[1:])

                            temp_mp4 = os.path.join(
                                tempfile.gettempdir(), f"source_{memory_id}.mp4"
                            )
                            wav_temp_path = os.path.join(
                                tempfile.gettempdir(), f"audio_{memory_id}.wav"
                            )

                            try:
                                res = supabase.storage.from_(bucket).download(
                                    file_path_in_bucket
                                )
                                with open(temp_mp4, "wb") as f:
                                    f.write(res)

                                extract_audio(temp_mp4, wav_temp_path)
                            except Exception as e:
                                logger.error(
                                    f"Audio extraction failed for {memory_id}: {e}"
                                )
                                wav_temp_path = None
                            finally:
                                if os.path.exists(temp_mp4):
                                    os.remove(temp_mp4)
            elif stage == "TRANSCRIBING":
                if wav_temp_path and os.path.exists(wav_temp_path):
                    from services.transcription_service import TranscriptionService

                    transcription_service = TranscriptionService()

                    try:
                        transcript = transcription_service.transcribe(wav_temp_path)
                        if supabase:
                            supabase.table("user_memories").update(
                                {"raw_transcript": transcript}
                            ).eq("id", memory_id).execute()
                    except Exception as e:
                        logger.error(f"Transcription failed for {memory_id}: {e}")
                else:
                    logger.warning(
                        f"Skipping TRANSCRIBING: No WAV file found for {memory_id}"
                    )
            elif stage == "OCR_FRAMES":
                from services.processors.video_processor import process_video_frames

                if supabase:
                    mem_res = (
                        supabase.table("user_memories")
                        .select("storage_path")
                        .eq("id", memory_id)
                        .execute()
                    )
                    if mem_res.data:
                        storage_path = mem_res.data[0].get("storage_path")
                        if storage_path:
                            bucket = storage_path.split("/")[0]
                            file_path_in_bucket = "/".join(storage_path.split("/")[1:])

                            temp_dir = tempfile.mkdtemp(prefix=f"cortex_{memory_id}_")
                            temp_mp4 = os.path.join(temp_dir, f"source_{memory_id}.mp4")
                            frames_dir = os.path.join(temp_dir, "frames")

                            try:
                                res = supabase.storage.from_(bucket).download(
                                    file_path_in_bucket
                                )
                                with open(temp_mp4, "wb") as f:
                                    f.write(res)

                                extracted_text = process_video_frames(
                                    temp_mp4, frames_dir
                                )

                                if extracted_text:
                                    supabase.table("user_memories").update(
                                        {"ocr_extracted_text": extracted_text}
                                    ).eq("id", memory_id).execute()

                            except Exception as e:
                                logger.error(
                                    f"Video OCR processing failed for {memory_id}: {e}"
                                )
                            finally:
                                shutil.rmtree(temp_dir, ignore_errors=True)
            elif stage == "OCR_IMAGE":
                from services.processors.image_processor import ImageProcessor

                if supabase:
                    mem_res = (
                        supabase.table("user_memories")
                        .select("storage_path")
                        .eq("id", memory_id)
                        .execute()
                    )
                    if mem_res.data:
                        storage_path = mem_res.data[0].get("storage_path")
                        if storage_path:
                            bucket = storage_path.split("/")[0]
                            file_path_in_bucket = "/".join(storage_path.split("/")[1:])

                            temp_dir = tempfile.mkdtemp(
                                prefix=f"cortex_{memory_id}_img_"
                            )

                            ext = os.path.splitext(file_path_in_bucket)[1] or ".jpg"
                            temp_img = os.path.join(
                                temp_dir, f"source_{memory_id}{ext}"
                            )

                            processor = ImageProcessor()

                            try:
                                res = supabase.storage.from_(bucket).download(
                                    file_path_in_bucket
                                )
                                with open(temp_img, "wb") as f:
                                    f.write(res)

                                extracted_text = processor.process(temp_img)

                                if extracted_text:
                                    supabase.table("user_memories").update(
                                        {"ocr_extracted_text": extracted_text}
                                    ).eq("id", memory_id).execute()

                            except Exception as e:
                                logger.error(
                                    f"Image OCR processing failed for {memory_id}: {e}"
                                )
                            finally:
                                shutil.rmtree(temp_dir, ignore_errors=True)
            elif stage == "SYNTHESIZING":
                from services.processors.synthesis_service import SynthesisService

                if supabase:
                    mem_res = (
                        supabase.table("user_memories")
                        .select("*")
                        .eq("id", memory_id)
                        .execute()
                    )
                    if mem_res.data and isinstance(mem_res.data[0], dict):
                        memory_data = mem_res.data[0]

                        payload = {
                            "content_type": memory_data.get("content_type"),
                            "source_url": memory_data.get("source_url"),
                            "creator_handle": memory_data.get(
                                "creator_handle", "unknown"
                            ),
                            "caption_or_title": memory_data.get("title", "unknown"),
                            "raw_transcript": memory_data.get("raw_transcript", ""),
                            "ocr_extracted_text": memory_data.get(
                                "ocr_extracted_text", ""
                            ),
                            "hashtags": "unknown",
                        }

                        synthesis_service = SynthesisService()
                        try:
                            validated_json = await synthesis_service.synthesize(payload)

                            supabase.table("user_memories").update(
                                {"ai_summary": validated_json}
                            ).eq("id", memory_id).execute()
                        except Exception as e:
                            logger.error(
                                f"Synthesis processing failed for {memory_id}: {e}"
                            )
            elif stage == "EMBEDDING":
                if supabase:
                    mem_res = (
                        supabase.table("user_memories")
                        .select("*")
                        .eq("id", memory_id)
                        .execute()
                    )
                    if mem_res.data and isinstance(mem_res.data[0], dict):
                        memory_data = mem_res.data[0]

                        ai_summary = memory_data.get("ai_summary")
                        if not ai_summary:
                            logger.warning(
                                f"No AI summary found for memory {memory_id}. "
                                "Cannot embed."
                            )
                            continue

                        class AISummaryWrapper:
                            def __init__(self, data):
                                self.title = data.get("title", "")
                                self.abstract = data.get("abstract", "")
                                self.takeaways = data.get("takeaways", [])
                                self.tech_stack = data.get("tech_stack", [])
                                self.tags = data.get("tags", [])

                        ai_sum = AISummaryWrapper(ai_summary)
                        creator_handle = memory_data.get("creator_handle", "unknown")
                        raw_transcript = memory_data.get("raw_transcript", "") or ""
                        ocr_extracted_text = (
                            memory_data.get("ocr_extracted_text", "") or ""
                        )

                        embedding_text = f"""
{ai_sum.title} {creator_handle}
SUMMARY ABSTRACT: {ai_sum.abstract}
EXTRACTED KEY TAKEAWAYS: {' | '.join(ai_sum.takeaways)}
TRANSCRIPT SYNTHESIS: {raw_transcript[:2000]}
VISUAL TEXT CONTEXT: {ocr_extracted_text[:1000]}
TECH STACK: {' '.join(ai_sum.tech_stack)}
"""
                        user_id = memory_data.get("user_id")
                        content_type = memory_data.get("content_type", "unknown")
                        try:
                            created_dt = datetime.fromisoformat(
                                memory_data.get("created_at", "").replace("Z", "+00:00")
                            )
                            created_ts = int(created_dt.timestamp())
                        except Exception:
                            created_ts = int(datetime.now(timezone.utc).timestamp())

                        metadata = {
                            "user_id": user_id,
                            "content_type": content_type,
                            "created_at": created_ts,
                            "tags_csv": ",".join(ai_sum.tags),
                            "tech_stack_csv": ",".join(ai_sum.tech_stack),
                            "plate_id": "",
                        }

                        try:
                            embedding = await embedding_service.upsert_memory(
                                memory_id, embedding_text, metadata
                            )
                            await clustering_service.cluster_new_memory(
                                memory_id,
                                user_id,
                                embedding,
                                ai_sum.tags + ai_sum.tech_stack,
                            )
                            await graph_service.map_relationships(
                                memory_id, user_id, embedding, metadata
                            )
                        except Exception as e:
                            logger.error(
                                "Embedding stage failed completely for "
                                f"{memory_id}: {e}"
                            )
            else:
                mock_stage(stage)

        user_id = None
        if supabase:
            res = (
                supabase.table("user_memories")
                .select("user_id")
                .eq("id", memory_id)
                .execute()
            )
            if res.data:
                user_id = res.data[0].get("user_id")

        update_job_stage(job_id, "COMPLETE", "COMPLETE")

        if user_id:
            # Flush cached search/memories results so fresh data is returned
            await cache_service.invalidate_search(user_id)
            await cache_service.invalidate_memories(user_id)

    except Exception as e:
        logger.error(f"process_memory failed for job {job_id}: {e}")
        update_job_stage(job_id, "FAILED", "FAILED", str(e))
