from __future__ import annotations

import re
from threading import Lock
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.config import Settings
from app.models import ScrapedImage, ScrapedProduct
from app.utils import (
    dedupe_preserving_order,
    ensure_unique_filename_bases,
    extract_first_number,
    extract_product_number,
    suggest_image_name,
)


class MobilexScrapeError(RuntimeError):
    pass


FULLSCREEN_ENDPOINT_PATTERN = re.compile(
    r"url:\s*['\"]([^'\"]*method=FullScreen[^'\"]*)['\"]",
    re.IGNORECASE,
)
_session_lock = Lock()


def _create_session() -> requests.Session:
    retries = Retry(
        total=2,
        connect=2,
        read=2,
        status=2,
        backoff_factor=0.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods={"GET"},
    )
    adapter = HTTPAdapter(max_retries=retries, pool_connections=2, pool_maxsize=2)
    session = requests.Session()
    session.headers["User-Agent"] = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36"
    )
    session.mount("https://", adapter)
    return session


_session = _create_session()


def scrape_mobilex_product_page(url: str, settings: Settings) -> ScrapedProduct:
    timeout = (settings.request_timeout_seconds, settings.request_timeout_seconds)
    try:
        # Mobilex associates its full-screen response with the product-page session.
        # Serializing both requests lets subsequent scrapes reuse the TLS connection.
        with _session_lock:
            page_response = _session.get(url, timeout=timeout)
            page_response.raise_for_status()
            page_html = page_response.text
            image_urls = _fetch_fullscreen_images(url, page_html, timeout)
    except requests.RequestException as error:
        raise MobilexScrapeError(f"Could not fetch Mobilex product page: {error}") from error

    page = BeautifulSoup(page_html, "html.parser")
    description = page.select_one(".description")
    if description is None:
        raise MobilexScrapeError("The Mobilex product page did not contain product details")

    title = _text_or_empty(description.select_one("h1"))
    if not title:
        raise MobilexScrapeError("The Mobilex product page did not contain a product title")

    if not image_urls:
        image_urls = _collect_image_urls(page, url, "#preview img, .thumbs img")

    hmi_text = _text_or_empty(description.select_one(".hmino"))
    product_code_text = _text_or_empty(description.select_one(".productcode"))
    suggested_names = ensure_unique_filename_bases([suggest_image_name(image_url) for image_url in image_urls])
    images = [
        ScrapedImage(source_url=image_url, filename_base=filename_base, alt_text=title)
        for image_url, filename_base in zip(image_urls, suggested_names, strict=False)
    ]

    return ScrapedProduct(
        source_url=url,
        product_name=title,
        hmi_number=extract_first_number(hmi_text),
        product_number=extract_product_number(product_code_text),
        images=images,
    )


def _fetch_fullscreen_images(url: str, page_html: str, timeout: tuple[int, int]) -> list[str]:
    match = FULLSCREEN_ENDPOINT_PATTERN.search(page_html)
    if match is None:
        return []

    endpoint = urljoin(url, match.group(1).replace("&amp;", "&"))
    response = _session.get(endpoint, timeout=timeout)
    response.raise_for_status()
    return _collect_image_urls(BeautifulSoup(response.text, "html.parser"), url, ".slick img")


def _collect_image_urls(page: BeautifulSoup, base_url: str, selector: str) -> list[str]:
    image_urls = []
    for image in page.select(selector):
        source = image.get("src") or image.get("data-src") or image.get("data-lazy")
        if isinstance(source, str) and source.strip():
            image_urls.append(urljoin(base_url, source.strip()))
    return dedupe_preserving_order(image_urls)


def _text_or_empty(element: object) -> str:
    get_text = getattr(element, "get_text", None)
    return get_text(" ", strip=True) if callable(get_text) else ""
