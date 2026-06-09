import glob
import logging
import os
import subprocess

from services.vision_service import VisionService

try:
    import imagehash
    from PIL import Image

    IMAGEHASH_AVAILABLE = True
except ImportError:
    IMAGEHASH_AVAILABLE = False

logger = logging.getLogger(__name__)


def process_video_frames(video_path: str, frames_dir: str) -> str:
    """
    Extracts frames at fps=2/3, deduplicates using pHash,
    and batches them to the Vision API.
    Returns concatenated extracted text.
    """
    if not os.path.exists(frames_dir):
        os.makedirs(frames_dir, exist_ok=True)

    logger.info(f"Extracting frames from {video_path} to {frames_dir}")

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        video_path,
        "-vf",
        "fps=2/3",
        "-q:v",
        "3",
        os.path.join(frames_dir, "frame_%04d.jpg"),
    ]

    try:
        subprocess.run(
            cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg frame extraction failed: {e}")
        raise RuntimeError("Failed to extract video frames using FFmpeg") from e

    frame_files = sorted(glob.glob(os.path.join(frames_dir, "frame_*.jpg")))

    if not frame_files:
        logger.warning(f"No frames extracted for {video_path}")
        return ""

    unique_frames = []

    if IMAGEHASH_AVAILABLE:
        prev_hash = None
        for frame in frame_files:
            try:
                img = Image.open(frame)
                current_hash = imagehash.phash(img)

                if prev_hash is not None and (current_hash - prev_hash) < 8:
                    img.close()
                    os.remove(frame)
                else:
                    unique_frames.append(frame)
                    prev_hash = current_hash
            except Exception as e:
                logger.error(f"Error processing frame hash {frame}: {e}")
                unique_frames.append(frame)
    else:
        logger.warning("imagehash not available. Skipping deduplication.")
        unique_frames = frame_files

    logger.info(
        f"Deduplication complete. {len(unique_frames)} unique frames remaining."
    )

    vision_service = VisionService()
    batch_size = 5
    all_extracted_text = []

    for i in range(0, len(unique_frames), batch_size):
        batch = unique_frames[i : i + batch_size]
        logger.info(f"Sending batch of {len(batch)} frames to Vision API...")
        text = vision_service.extract_from_frames(batch)
        if text.strip():
            all_extracted_text.append(text.strip())

    final_text = "\n\n---\n\n".join(all_extracted_text)
    return final_text
