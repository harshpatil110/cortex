import logging

import fitz  # PyMuPDF

try:
    import pytesseract
    from PIL import Image

    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

logger = logging.getLogger(__name__)


class PDFProcessor:
    def __init__(self):
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

    def process(self, filepath: str) -> str:
        doc = fitz.open(filepath)
        total_pages = len(doc)

        full_text = []

        # Chunking for large PDFs (>100 pages, chunk size 20)
        chunk_size = 20

        for chunk_start in range(0, total_pages, chunk_size):
            chunk_end = min(chunk_start + chunk_size, total_pages)
            for page_num in range(chunk_start, chunk_end):
                page = doc[page_num]
                page_text = self._process_page(page, page_num)
                if page_text:
                    full_text.append(page_text.strip())

        doc.close()

        # Clean up excessive blank lines
        raw_output = "\n\n".join(full_text)
        cleaned_output = []
        for line in raw_output.split("\n"):
            if not line.strip() and (cleaned_output and not cleaned_output[-1].strip()):
                continue  # deduplicate blank lines
            cleaned_output.append(line)

        return "\n".join(cleaned_output).strip()

    def _process_page(self, page: fitz.Page, page_num: int) -> str:
        blocks = page.get_text("blocks")
        text_blocks = [b for b in blocks if b[6] == 0]

        if not text_blocks:
            # Scanned PDF fallback
            return self._perform_ocr(page, page_num)

        page_dict = page.get_text("dict")
        return self._parse_digital_page(page, page_dict)

    def _perform_ocr(self, page: fitz.Page, page_num: int) -> str:
        logger.info(f"Page {page_num} appears to be scanned. Using OCR fallback.")
        if not TESSERACT_AVAILABLE:
            logger.warning("Tesseract not available. Skipping OCR.")
            return ""

        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        try:
            return pytesseract.image_to_string(img)
        except Exception as e:
            logger.error(f"OCR failed on page {page_num}: {e}")
            return ""

    def _parse_digital_page(self, page: fitz.Page, page_dict: dict) -> str:
        # 1. Process tables first
        tables_markdown = {}
        if hasattr(page, "find_tables"):
            tabs = page.find_tables()
            if tabs:
                for tab in tabs.tables:
                    try:
                        df = tab.to_pandas()
                        if not df.empty:
                            md_table = df.to_markdown(index=False)
                            tables_markdown[tab.bbox] = md_table
                    except Exception as e:
                        logger.warning(f"Failed to parse table: {e}")

        page_height = page_dict.get("height", 0)
        blocks = page_dict.get("blocks", [])

        # Calculate body text size threshold
        font_sizes = []
        for block in blocks:
            if block.get("type") != 0:
                continue
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    font_sizes.append(span.get("size", 10))

        if font_sizes:
            # roughly estimate mode
            body_size = max(set(font_sizes), key=font_sizes.count)
        else:
            body_size = 10.0

        header_threshold = body_size * 1.2

        lines_output = []

        for block in blocks:
            if block.get("type") != 0:
                continue

            bbox = block.get("bbox")
            x0, y0, x1, y1 = bbox

            # Strip headers/footers (top/bottom 5% with minimal length)
            if y0 < page_height * 0.05 or y1 > page_height * 0.95:
                block_text = "".join(
                    [
                        span.get("text", "")
                        for line in block.get("lines", [])
                        for span in line.get("spans", [])
                    ]
                )
                if len(block_text.strip()) < 50:
                    continue

            # Check if this block intersects with a table
            in_table = False
            for t_bbox, t_md in tables_markdown.items():
                tx0, ty0, tx1, ty1 = t_bbox
                if not (x1 < tx0 or x0 > tx1 or y1 < ty0 or y0 > ty1):
                    in_table = True
                    break

            if in_table:
                continue

            block_content = []
            is_header = False
            is_code = False

            for line in block.get("lines", []):
                line_text = ""
                for span in line.get("spans", []):
                    text = span.get("text", "").strip()
                    if not text:
                        continue

                    size = span.get("size", 10)
                    font = span.get("font", "").lower()

                    if size >= header_threshold:
                        is_header = True

                    if "mono" in font or "code" in font or "courier" in font:
                        is_code = True

                    line_text += text + " "

                if line_text.strip():
                    block_content.append(line_text.strip())

            if not block_content:
                continue

            merged_text = "\n".join(block_content)

            if is_code:
                lines_output.append(f"```\n{merged_text}\n```")
            elif is_header:
                header_text = merged_text.replace("\n", " ")
                lines_output.append(f"## {header_text}")
            elif merged_text.startswith(("-", "•", "*")):
                lines_output.append(merged_text)
            elif (
                merged_text[0].isdigit()
                and len(merged_text) > 1
                and merged_text[1] in (".", ")")
            ):
                lines_output.append(merged_text)
            else:
                lines_output.append(merged_text)

        # Append tables that were found
        for t_bbox, t_md in tables_markdown.items():
            lines_output.append(t_md)

        return "\n\n".join(lines_output)
