import logging

import fitz  # PyMuPDF

try:
    import pytesseract
    from PIL import Image

    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

logger = logging.getLogger(__name__)


class PDFExtractionService:
    def __init__(self):
        # Configure tesseract path if on Windows and default path exists
        if TESSERACT_AVAILABLE:
            import os
            import sys

            if sys.platform == "win32":
                tess_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
                if os.path.exists(tess_path):
                    pytesseract.pytesseract.tesseract_cmd = tess_path
                else:
                    logger.warning(
                        f"Tesseract executable not found at {tess_path}. OCR may fail."
                    )

    def extract_text(self, filepath: str) -> str:
        """
        Extracts text from a PDF.
        Detects if a page is purely scanned imagery. If so, falls back to OCR.
        Preserves some structural markdown like Headers and Lists.
        """
        doc = fitz.open(filepath)
        full_text = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            blocks = page.get_text("blocks")

            # Check for text blocks. block_type 0 = text, 1 = image
            text_blocks = [b for b in blocks if b[6] == 0]

            # If text_blocks exist, we assume the page has a digital text layer
            if text_blocks:
                page_text = self._parse_digital_page(page)
                full_text.append(page_text)
            else:
                # Scanned PDF - Use OCR
                logger.info(
                    f"Page {page_num} appears to be scanned. Using OCR fallback."
                )
                if TESSERACT_AVAILABLE:
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    try:
                        text = pytesseract.image_to_string(img)
                        full_text.append(text)
                    except Exception as e:
                        logger.error(f"OCR failed on page {page_num}: {e}")
                else:
                    logger.warning("Tesseract not available. Skipping OCR.")

        doc.close()
        return "\n\n".join(full_text)

    def _parse_digital_page(self, page) -> str:
        page_dict = page.get_text("dict")
        blocks = page_dict.get("blocks", [])

        lines_output = []

        for block in blocks:
            if block.get("type") != 0:
                continue  # Skip images

            block_text = ""
            is_header = False

            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = span.get("text", "").strip()
                    if not text:
                        continue

                    # Heuristic for header detection: typical body font size is ~10-12
                    size = span.get("size", 10)
                    if size > 12.5:
                        is_header = True

                    block_text += text + " "
                block_text = block_text.strip() + "\n"

            block_text = block_text.strip()
            if not block_text:
                continue

            if is_header:
                lines_output.append(f"## {block_text}")
            elif block_text.startswith(("-", "•", "*")):
                lines_output.append(block_text)  # Bullet list
            elif (
                block_text[0].isdigit()
                and len(block_text) > 1
                and block_text[1] in (".", ")")
            ):
                lines_output.append(block_text)  # Numbered list
            else:
                lines_output.append(block_text)

        return "\n\n".join(lines_output)
