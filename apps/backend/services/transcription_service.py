import logging
import os
import re
import time

logger = logging.getLogger(__name__)

try:
    from faster_whisper import WhisperModel
except ImportError:
    WhisperModel = None

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


class TranscriptionService:
    def __init__(self):
        self.provider = os.getenv("WHISPER_PROVIDER", "local").lower()
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.local_model_size = os.getenv("WHISPER_MODEL", "base.en")

    def transcribe(self, wav_path: str) -> str:
        """
        Transcribes a WAV file using the configured provider (Groq or local).
        Cleans the transcript, logs metrics, and deletes the temp WAV file.
        """
        if not os.path.exists(wav_path):
            raise FileNotFoundError(f"WAV file not found at {wav_path}")

        start_time = time.time()
        duration = self._get_audio_duration(wav_path)
        logger.info(
            f"Starting transcription. Audio duration: {duration:.2f}s, "
            f"Provider: {self.provider}"
        )

        try:
            if self.provider == "groq":
                raw_transcript = self._transcribe_groq(wav_path)
            else:
                raw_transcript = self._transcribe_local(wav_path)

            transcription_time = time.time() - start_time
            logger.info(
                f"Transcription complete. Time taken: {transcription_time:.2f}s"
            )

            cleaned_transcript = self._clean_transcript(raw_transcript)
            return cleaned_transcript

        finally:
            if os.path.exists(wav_path):
                os.remove(wav_path)
                logger.info(f"Cleaned up temporary audio file: {wav_path}")

    def _transcribe_groq(self, wav_path: str) -> str:
        if not OpenAI:
            raise RuntimeError(
                "openai package not installed. Cannot use Groq provider."
            )
        if not self.groq_api_key:
            raise ValueError("GROQ_API_KEY environment variable is not set.")

        client = OpenAI(
            api_key=self.groq_api_key, base_url="https://api.groq.com/openai/v1"
        )

        with open(wav_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-large-v3", file=audio_file, temperature=0
            )

        return transcription.text

    def _transcribe_local(self, wav_path: str) -> str:
        if not WhisperModel:
            raise RuntimeError(
                "faster-whisper package not installed. Cannot use local provider."
            )

        model = WhisperModel(self.local_model_size, compute_type="int8")
        segments, info = model.transcribe(wav_path, language="en")

        text_segments = []
        for segment in segments:
            text_segments.append(segment.text)

        return " ".join(text_segments)

    def _get_audio_duration(self, wav_path: str) -> float:
        import subprocess

        try:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-show_entries",
                    "format=duration",
                    "-of",
                    "default=noprint_wrappers=1:nokey=1",
                    wav_path,
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            return float(result.stdout)
        except Exception:
            return 0.0

    def _clean_transcript(self, text: str) -> str:
        fillers = [r"\bum\b", r"\buh\b", r"\blike\b", r"\byou know\b"]
        pattern = re.compile("|".join(fillers), flags=re.IGNORECASE)
        cleaned = pattern.sub("", text)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        replacements = {
            "Npm": "npm",
            "Github": "GitHub",
            "Postgres": "PostgreSQL",
            "Reactjs": "React.js",
        }

        for old, new in replacements.items():
            cleaned = cleaned.replace(old, new)

        return cleaned
