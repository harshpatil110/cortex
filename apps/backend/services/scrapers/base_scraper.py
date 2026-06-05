from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseScraper(ABC):
    @abstractmethod
    async def scrape(self, url: str) -> Dict[str, Any]:
        """
        Extracts content from a URL.
        Returns a dictionary with extracted data:
        - mp4_url (str)
        - thumbnail_url (str)
        - webpage_url (str)
        - description (str)
        - creator_metadata (dict)
        """
        pass
