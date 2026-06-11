import json
import logging
import os
from typing import Any, List

from PIL import Image

logger = logging.getLogger(__name__)

try:
    import google.generativeai as genai

    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


class VisionService:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model: Any = None
        if GENAI_AVAILABLE and self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel("gemini-1.5-flash")
        else:
            if not GENAI_AVAILABLE:
                logger.error("google-generativeai package not installed.")
            elif not self.api_key:
                logger.error("GEMINI_API_KEY is not set.")

        self.system_prompt = """
You are an OCR engine specialized in technical content.
For the provided video frames, extract:
1. All code snippets (with language if identifiable)
2. Terminal commands (npm, pip, docker, git, etc.)
3. Package/library names and version numbers
4. Configuration keys and values
5. URLs visible on screen
Return ONLY valid JSON matching this schema:
{
  "extractions": [
    {
      "frame_index": 0,
      "code_blocks": [],
      "commands": [],
      "ui_text": ""
    }
  ]
}
"""

    def extract_from_frames(self, image_paths: List[str]) -> str:
        """
        Accepts a list of image paths (max 5), runs them through Gemini,
        and returns a compiled markdown string of the OCR text.
        """
        if not self.model:
            raise RuntimeError("Vision model is not configured properly.")

        if not image_paths:
            return ""

        if len(image_paths) > 5:
            logger.warning(
                f"VisionService received {len(image_paths)} images, "
                "taking only the first 5."
            )
            image_paths = image_paths[:5]

        images = []
        for path in image_paths:
            try:
                images.append(Image.open(path))
            except Exception as e:
                logger.error(f"Failed to open image {path}: {e}")

        if not images:
            return ""

        try:
            # We must instruct the model to return JSON structure securely
            prompt_content = [self.system_prompt] + images
            response = self.model.generate_content(prompt_content)

            # Extract JSON from response.text
            return self._parse_and_compile(response.text)
        except Exception as e:
            logger.error(f"Gemini API call failed: {e}")
            return ""

    def _parse_and_compile(self, raw_response: str) -> str:
        try:
            # Clean possible markdown block
            clean_text = raw_response.strip()
            if clean_text.startswith("```json"):
                clean_text = clean_text[7:]
            if clean_text.startswith("```"):
                clean_text = clean_text[3:]
            if clean_text.endswith("```"):
                clean_text = clean_text[:-3]

            data = json.loads(clean_text)
            extractions = data.get("extractions", [])

            compiled = []

            for ext in extractions:
                code_blocks = ext.get("code_blocks", [])
                commands = ext.get("commands", [])
                ui_text = ext.get("ui_text", "")

                if code_blocks:
                    for code in code_blocks:
                        compiled.append(f"```\n{code}\n```")

                if commands:
                    for cmd in commands:
                        compiled.append(f"`{cmd}`")

                if ui_text:
                    compiled.append(ui_text)

            return "\n\n".join(compiled)
        except json.JSONDecodeError as e:
            logger.error(
                f"Failed to parse Gemini response as JSON: {e}\n"
                f"Raw Response: {raw_response}"
            )
            return ""
