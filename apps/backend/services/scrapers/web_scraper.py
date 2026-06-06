import asyncio
import logging
from typing import Any, Dict

import httpx
import trafilatura
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

from services.scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class WebScraper(BaseScraper):
    async def scrape(self, url: str) -> Dict[str, Any]:
        """
        Primary extraction using trafilatura, fallback to Playwright + BeautifulSoup4.
        """
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                response = await client.get(url)

                if response.status_code == 403:
                    logger.warning(f"HTTP 403 Forbidden for {url}")
                    title = ""
                    try:
                        soup = BeautifulSoup(response.text, "html.parser")
                        if soup.title and soup.title.string:
                            title = soup.title.string.strip()
                    except Exception:
                        pass
                    return self._build_result(
                        mp4_url="",
                        thumbnail_url="",
                        webpage_url=url,
                        description="",
                        creator_metadata={
                            "title": title,
                            "status": "403_forbidden",
                            "platform": "web",
                        },
                        raw_transcript=title,
                    )

                response.raise_for_status()
                html = response.text

                return await asyncio.to_thread(self._parse_with_trafilatura, html, url)

        except httpx.TimeoutException:
            logger.warning(f"Timeout fetching {url}. Falling back to Playwright.")
            return await self._fallback_playwright(url)
        except Exception as e:
            logger.warning(f"Error fetching {url}: {e}. Falling back to Playwright.")
            return await self._fallback_playwright(url)

    def _parse_with_trafilatura(self, html: str, url: str) -> Dict[str, Any]:
        metadata = trafilatura.extract_metadata(html, default_url=url)

        text = trafilatura.extract(
            html, include_comments=False, include_tables=True, url=url
        )

        if not text:
            raise ValueError("Trafilatura failed to extract content")

        return self._format_extraction(text, metadata, url)

    async def _fallback_playwright(self, url: str) -> Dict[str, Any]:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

            try:
                response = await page.goto(url, wait_until="networkidle", timeout=10000)

                if response and response.status == 403:
                    logger.warning(f"Playwright got HTTP 403 Forbidden for {url}")
                    title = await page.title()
                    await browser.close()
                    return self._build_result(
                        mp4_url="",
                        thumbnail_url="",
                        webpage_url=url,
                        description="",
                        creator_metadata={
                            "title": title,
                            "status": "403_forbidden",
                            "platform": "web",
                        },
                        raw_transcript=title,
                    )

                html = await page.content()
                await browser.close()

                return await asyncio.to_thread(self._parse_with_bs4, html, url)

            except Exception as e:
                logger.error(f"Playwright fallback failed for {url}: {e}")
                await browser.close()
                raise ValueError(f"Both Trafilatura and Playwright failed for {url}")

    def _parse_with_bs4(self, html: str, url: str) -> Dict[str, Any]:
        soup = BeautifulSoup(html, "html.parser")

        for element in soup(
            [
                "nav",
                "footer",
                "header",
                "sidebar",
                "aside",
                "script",
                "style",
                "noscript",
            ]
        ):
            element.decompose()

        title = soup.title.string.strip() if soup.title and soup.title.string else ""
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            title = og_title.get("content")

        og_author = soup.find("meta", property="og:author")
        author = og_author.get("content", "") if og_author else ""

        og_image = soup.find("meta", property="og:image")
        image_url = og_image.get("content", "") if og_image else ""

        article_pub = soup.find("meta", property="article:published_time")
        published_time = article_pub.get("content", "") if article_pub else ""

        body = soup.find("body")
        text = body.get_text(separator="\n", strip=True) if body else ""

        if "paywall" in html.lower() or "subscribe to read" in html.lower():
            text = f"[PAYWALL]\n{text}"

        creator_metadata = {
            "title": title,
            "author": author,
            "published_time": published_time,
            "platform": "web",
        }

        return self._build_result(
            mp4_url="",
            thumbnail_url=image_url,
            webpage_url=url,
            description="",
            creator_metadata=creator_metadata,
            raw_transcript=text,
        )

    def _format_extraction(self, text: str, metadata: Any, url: str) -> Dict[str, Any]:
        title = (
            metadata.title
            if metadata and hasattr(metadata, "title") and metadata.title
            else ""
        )
        author = (
            metadata.author
            if metadata and hasattr(metadata, "author") and metadata.author
            else ""
        )
        image_url = (
            metadata.image
            if metadata and hasattr(metadata, "image") and metadata.image
            else ""
        )
        published_time = (
            metadata.date
            if metadata and hasattr(metadata, "date") and metadata.date
            else ""
        )

        lower_text = text.lower()
        if (
            "subscribe to read" in lower_text
            or "log in to continue" in lower_text
            or "paywall" in lower_text
        ):
            text = f"[PAYWALL]\n{text}"

        creator_metadata = {
            "title": title,
            "author": author,
            "published_time": published_time,
            "platform": "web",
        }

        return self._build_result(
            mp4_url="",
            thumbnail_url=image_url,
            webpage_url=url,
            description="",
            creator_metadata=creator_metadata,
            raw_transcript=text,
        )

    def _build_result(
        self,
        mp4_url: str,
        thumbnail_url: str,
        webpage_url: str,
        description: str,
        creator_metadata: dict,
        raw_transcript: str,
    ) -> Dict[str, Any]:
        return {
            "mp4_url": mp4_url,
            "thumbnail_url": thumbnail_url,
            "webpage_url": webpage_url,
            "description": description,
            "creator_metadata": creator_metadata,
            "raw_transcript": raw_transcript,
        }
