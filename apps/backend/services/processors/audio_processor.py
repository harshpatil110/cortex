import logging
import subprocess

logger = logging.getLogger(__name__)


def extract_audio(video_path: str, output_wav_path: str) -> str:
    """
    Extracts optimized audio from an MP4 file using FFmpeg.
    Optimized for Whisper: 16kHz, mono, loudnorm.
    """
    logger.info(f"Extracting audio from {video_path} to {output_wav_path}")

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        video_path,
        "-ar",
        "16000",
        "-ac",
        "1",
        "-af",
        "loudnorm",
        "-f",
        "wav",
        output_wav_path,
    ]

    try:
        subprocess.run(
            cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        return output_wav_path
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg audio extraction failed: {e}")
        raise RuntimeError("Failed to extract audio using FFmpeg") from e
