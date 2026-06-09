import logging
import os
import time

from celery import shared_task
from supabase import Client, create_client

from services.thumbnail_service import ThumbnailService

logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv(
    "SUPABASE_SERVICE_ROLE_KEY", os.getenv("SUPABASE_ANON_KEY", "")
)

supabase: Client = (
    create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None
)


def update_job_stage(
    job_id: str, stage_name: str, status: str = "PROCESSING", error_message: str = None
):
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


@shared_task(bind=True, autoretry_for=(Exception,), max_retries=3, retry_backoff=True)
def process_memory_task(self, job_id: str, memory_id: str, content_type: str):
    """
    Master Celery orchestrator task.
    Routes incoming memories through processing pipelines based on content type.
    """
    logger.info(
        f"Starting process_memory_task for job {job_id}, "
        f"memory {memory_id}, type {content_type}"
    )
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
                import tempfile

                from services.processors.pdf_processor import PDFProcessor

                processor = PDFProcessor()
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
                import tempfile

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
            else:
                mock_stage(stage)

        update_job_stage(job_id, "COMPLETE", "COMPLETE")

        if supabase:
            try:
                supabase.table("user_memories").update({"indexed": True}).eq(
                    "id", memory_id
                ).execute()
                logger.info(f"Memory {memory_id} marked as indexed.")
            except Exception as e:
                logger.error(f"Failed to mark memory {memory_id} as indexed: {e}")

    except Exception as e:
        logger.error(f"process_memory_task failed for job {job_id}: {e}")
        update_job_stage(job_id, "FAILED", "FAILED", str(e))
        raise e
