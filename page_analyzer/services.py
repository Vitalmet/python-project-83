import logging
from urllib.parse import urlparse

import requests
import validators
from bs4 import BeautifulSoup

from page_analyzer.config import Config

logger = logging.getLogger(__name__)


def normalize_url(url: str) -> str:
    url = url.strip()
    parsed = urlparse(url)
    normalized = f"{parsed.scheme}://{parsed.netloc}"
    return normalized.lower()


def validate_url(url: str) -> tuple[bool, str]:
    if not url or len(url) > Config.MAX_URL_LENGTH:
        return False, "URL превышает 255 символов"
    if not validators.url(url):
        return False, "Некорректный URL"
    return True, ""


def truncate_text(text: str | None, max_length: int = Config.MAX_TEXT_LENGTH) -> str:
    if text and len(text) > max_length:
        return text[:max_length] + "..."
    return text or ""


def fetch_page_data(url: str) -> dict:
    response = requests.get(url, timeout=Config.REQUEST_TIMEOUT)
    response.raise_for_status()

    response.encoding = response.apparent_encoding or "utf-8"
    soup = BeautifulSoup(response.text, "html.parser")

    h1_tag = soup.find("h1")
    h1 = truncate_text(h1_tag.get_text(strip=True)) if h1_tag else ""

    title_tag = soup.find("title")
    title = truncate_text(title_tag.get_text(strip=True)) if title_tag else ""

    desc_tag = soup.find("meta", attrs={"name": "description"})
    description = truncate_text(desc_tag.get("content", "").strip()) if desc_tag else ""

    return {
        "status_code": response.status_code,
        "h1": h1,
        "title": title,
        "description": description,
    }
