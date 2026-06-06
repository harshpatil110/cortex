import logging
import os
import subprocess
import tempfile
from typing import Optional

import fitz  # PyMuPDF
from PIL import Image
from redis import Redis

from services.storage_service import supabase

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = Redis.from_url(REDIS_URL, decode_responses=True)


class ThumbnailService:
    def __init__(self):
        self.supabase = supabase

    def process_thumbnail(self, memory_id: str, content_type: str) -> Optional[str]:
        """
        Downloads source file, generates WebP thumbnail, uploads to Supabase,
        updates DB, and caches a signed URL in Redis.
        """
        if not self.supabase:
            logger.error("Supabase client not configured.")
            return None

        mem_res = (
            self.supabase.table("user_memories")
            .select("user_id, storage_path")
            .eq("id", memory_id)
            .execute()
        )
        if not mem_res.data:
            logger.error(f"Memory {memory_id} not found.")
            return None

        mem_data = mem_res.data[0]
        user_id = mem_data.get("user_id")
        storage_path = mem_data.get("storage_path")

        if not storage_path:
            logger.error("No storage_path found for memory.")
            return None

        bucket = storage_path.split("/")[0]
        file_path_in_bucket = "/".join(storage_path.split("/")[1:])

        if content_type in ["instagram_reel", "web_page"]:
            bucket = "thumbnails"
            base_name = os.path.splitext(file_path_in_bucket)[0]
            file_path_in_bucket = f"{base_name}.jpg"

        temp_dir = tempfile.gettempdir()
        source_ext = os.path.splitext(file_path_in_bucket)[1]
        source_path = os.path.join(temp_dir, f"source_{memory_id}{source_ext}")
        thumb_path = os.path.join(temp_dir, f"thumb_{memory_id}.webp")
        temp_jpg = os.path.join(temp_dir, f"temp_{memory_id}.jpg")

        try:
            res = self.supabase.storage.from_(bucket).download(file_path_in_bucket)
            with open(source_path, "wb") as f:
                f.write(res)

            if content_type in ["instagram_reel", "web_page", "image"]:
                with Image.open(source_path) as img:
                    if img.mode in ("RGBA", "P"):
                        img = img.convert("RGB")
                    img.thumbnail((600, 400), Image.LANCZOS)
                    img.save(thumb_path, "WEBP", quality=85)

            elif content_type in ["mp4", "video"]:
                cmd = [
                    "ffmpeg",
                    "-y",
                    "-i",
                    source_path,
                    "-ss",
                    "00:00:01.000",
                    "-frames:v",
                    "1",
                    temp_jpg,
                ]
                subprocess.run(
                    cmd,
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )

                with Image.open(temp_jpg) as img:
                    if img.mode in ("RGBA", "P"):
                        img = img.convert("RGB")
                    img.thumbnail((600, 400), Image.LANCZOS)
                    img.save(thumb_path, "WEBP", quality=85)

            elif content_type == "pdf":
                doc = fitz.open(source_path)
                page = doc[0]
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                pix.save(temp_jpg)
                doc.close()

                with Image.open(temp_jpg) as img:
                    if img.mode in ("RGBA", "P"):
                        img = img.convert("RGB")
                    img.thumbnail((600, 400), Image.LANCZOS)
                    img.save(thumb_path, "WEBP", quality=85)

            else:
                logger.warning(f"Thumbnail generation not supported for {content_type}")
                return None

            if not os.path.exists(thumb_path):
                raise Exception("Thumbnail was not generated")

            final_storage_path = f"{user_id}/{memory_id}.webp"
            with open(thumb_path, "rb") as f:
                self.supabase.storage.from_("thumbnails").upload(
                    final_storage_path,
                    f.read(),
                    file_options={"content-type": "image/webp"},
                )

            self.supabase.table("user_memories").update(
                {"thumbnail_storage_path": f"thumbnails/{final_storage_path}"}
            ).eq("id", memory_id).execute()

            signed_url_res = self.supabase.storage.from_(
                "thumbnails"
            ).create_signed_url(final_storage_path, 31536000)
            signed_url = signed_url_res.get("signedURL")

            if signed_url:
                redis_key = f"thumbnail_url:{memory_id}"
                redis_client.set(redis_key, signed_url, ex=31536000)

            logger.info(f"Successfully generated/cached thumbnail for {memory_id}")
            return final_storage_path

        except Exception as e:
            logger.error(f"Thumbnail generation failed for {memory_id}: {e}")
            raise e
        finally:
            if os.path.exists(source_path):
                os.remove(source_path)
            if os.path.exists(thumb_path):
                os.remove(thumb_path)
            if os.path.exists(temp_jpg):
                os.remove(temp_jpg)
