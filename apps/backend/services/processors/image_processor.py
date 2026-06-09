import json
import logging
import os

from PIL import Image

try:
    import pytesseract
    from pytesseract import Output

    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

try:
    import google.generativeai as genai

    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

logger = logging.getLogger(__name__)


class ImageProcessor:
    def __init__(self):
        if TESSERACT_AVAILABLE:
            import sys

            if sys.platform == "win32":
                tess_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
                if os.path.exists(tess_path):
                    pytesseract.pytesseract.tesseract_cmd = tess_path
                else:
                    logger.warning(f"Tesseract not found at {tess_path}")

        self.api_key = os.getenv("GEMINI_API_KEY")
        if GENAI_AVAILABLE and self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel("gemini-1.5-flash")
        else:
            self.model = None

        self.gemini_prompt = """
Analyze this screenshot and extract all visible content with high structural fidelity:
- Error messages, logs, stack traces, and crash files
- Code snippets (with language tagging) and command-line inputs/outputs
- Configuration keys, environment variables, and parameters
- Architecture diagram flows, labels, text items, and component interactions
Return the result strictly as a clean, valid JSON block matching this structure:
{
  "description": "string",
  "code_blocks": ["string"],
  "commands": ["string"],
  "error_messages": ["string"],
  "text_content": "string"
}
"""

    def process(self, filepath: str) -> str:
        """
        Process the image: resize if needed, choose between Tesseract and Gemini,
        and return the extracted string.
        """
        self._resize_if_needed(filepath)

        try:
            img = Image.open(filepath)
            img.load()
        except Exception as e:
            logger.error(f"Failed to open image for OCR {filepath}: {e}")
            return ""

        use_tesseract = False
        if TESSERACT_AVAILABLE:
            try:
                osd = pytesseract.image_to_osd(img, output_type=Output.DICT)
                conf = osd.get("script_conf", 0)
                if conf >= 80.0:
                    use_tesseract = True
            except Exception as e:
                logger.info(f"OSD check failed, assuming non-document image: {e}")

        if use_tesseract:
            logger.info(
                f"High text confidence detected. Using Tesseract for {filepath}"
            )
            try:
                return pytesseract.image_to_string(img)
            except Exception as e:
                logger.error(f"Tesseract extraction failed: {e}")
                logger.info("Falling back to Gemini API.")

        logger.info(f"Using Gemini Vision API for {filepath}")
        if not self.model:
            logger.error("Gemini API not configured, returning empty string.")
            return ""

        try:
            response = self.model.generate_content([self.gemini_prompt, img])
            return self._parse_gemini_response(response.text)
        except Exception as e:
            logger.error(f"Gemini API call failed for image {filepath}: {e}")
            return ""

    def _resize_if_needed(self, filepath: str):
        size_bytes = os.path.getsize(filepath)
        max_size_bytes = 4 * 1024 * 1024  # 4MB

        if size_bytes > max_size_bytes:
            logger.info(f"Image {filepath} is {size_bytes} bytes (>4MB). Resizing.")
            try:
                with Image.open(filepath) as img:
                    width, height = img.size
                    max_dim = 2048
                    if width > max_dim or height > max_dim:
                        if width > height:
                            new_width = max_dim
                            new_height = int((height / width) * max_dim)
                        else:
                            new_height = max_dim
                            new_width = int((width / height) * max_dim)

                        img = img.resize(
                            (new_width, new_height), Image.Resampling.LANCZOS
                        )
                        img.save(filepath, quality=85)
            except Exception as e:
                logger.error(f"Failed to resize image {filepath}: {e}")

    def _parse_gemini_response(self, text: str) -> str:
        clean_text = text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        if clean_text.startswith("```"):
            clean_text = clean_text[3:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]

        try:
            data = json.loads(clean_text)

            output = []
            if data.get("description"):
                output.append(data["description"])

            if data.get("code_blocks"):
                for code in data["code_blocks"]:
                    output.append(f"```\n{code}\n```")

            if data.get("commands"):
                for cmd in data["commands"]:
                    output.append(f"`{cmd}`")

            if data.get("error_messages"):
                output.append("### Error Messages")
                for err in data["error_messages"]:
                    output.append(f"- {err}")

            if data.get("text_content"):
                output.append(data["text_content"])

            return "\n\n".join(output)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in image_processor: {e}\nRaw: {text}")
            return ""
