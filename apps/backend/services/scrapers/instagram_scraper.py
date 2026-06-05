import logging
import os
import re
from typing import Any, Dict

import yt_dlp
from playwright.async_api import async_playwright

from services.scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

PROXIES = [p.strip() for p in os.getenv("PROXY_LIST", "").split(",") if p.strip()]


class InstagramScraper(BaseScraper):
    def __init__(self):
        self.cookies_path = os.getenv("INSTAGRAM_COOKIES_PATH")
        self._proxy_index = 0

    def _get_next_proxy(self) -> str:
        if not PROXIES:
            return None
        proxy = PROXIES[self._proxy_index]
        self._proxy_index = (self._proxy_index + 1) % len(PROXIES)
        return proxy

    async def scrape(self, url: str) -> Dict[str, Any]:
        if not re.search(r"instagram\.com/(?:reel|p)/", url):
            raise ValueError("Invalid Instagram URL")

        proxy_url = self._get_next_proxy()

        ydl_opts = {
            "format": "best[height<=1080]",
            "quiet": True,
            "no_warnings": True,
        }
        if self.cookies_path and os.path.exists(self.cookies_path):
            ydl_opts["cookiefile"] = self.cookies_path
        if proxy_url:
            ydl_opts["proxy"] = proxy_url

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

                uploader = info.get("uploader_id") or info.get("uploader")
                return {
                    "mp4_url": info.get("url"),
                    "thumbnail_url": info.get("thumbnail"),
                    "webpage_url": info.get("webpage_url", url),
                    "description": info.get("description", ""),
                    "creator_metadata": {
                        "handle": f"@{uploader}",
                        "platform": "instagram",
                        "profile_url": f"https://instagram.com/{uploader}",
                    },
                }
        except yt_dlp.utils.DownloadError as e:
            error_msg = str(e).lower()
            if "private" in error_msg:
                raise ValueError("Account is private")
            elif "not available" in error_msg or "deleted" in error_msg:
                raise ValueError("Content no longer available")

            logger.warning(f"yt-dlp failed for {url}: {e}. Falling back to Playwright.")
            return await self._fallback_playwright(url, proxy_url)

    async def _fallback_playwright(self, url: str, proxy: str) -> Dict[str, Any]:
        async with async_playwright() as p:
            launch_args = {"headless": True}
            if proxy:
                launch_args["proxy"] = {"server": proxy}

            browser = await p.chromium.launch(**launch_args)
            context = await browser.new_context()
            page = await context.new_page()

            mp4_url = None

            async def handle_request(route, request):
                nonlocal mp4_url
                if request.resource_type == "media" or ".mp4" in request.url:
                    if not mp4_url:
                        mp4_url = request.url
                await route.continue_()

            await page.route("**/*", handle_request)

            try:
                await page.goto(url, wait_until="networkidle", timeout=15000)
            except Exception as e:
                logger.error(f"Playwright timeout or error: {e}")

            await browser.close()

            if not mp4_url:
                raise Exception("Failed to extract MP4 URL via Playwright")

            return {
                "mp4_url": mp4_url,
                "thumbnail_url": "",
                "webpage_url": url,
                "description": "",
                "creator_metadata": {
                    "handle": "@unknown",
                    "platform": "instagram",
                    "profile_url": "",
                },
            }
