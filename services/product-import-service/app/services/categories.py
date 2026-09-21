from __future__ import annotations

from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.parse import urljoin, urlparse
from xml.etree import ElementTree as ET

import requests


MAX_CATEGORIES_XML_BYTES = 5_000_000


class CategoryRefreshError(RuntimeError):
    pass


class _ExportDownloadLinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        href = dict(attrs).get("href")
        if href:
            self.hrefs.append(href)


@dataclass(frozen=True)
class CategoryOption:
    id: str
    name: str
    parent_id: str
    depth: int

    @property
    def label(self) -> str:
        hierarchy_prefix = f"{'— ' * self.depth}" if self.depth else ""
        return f"{hierarchy_prefix}{self.name} ({self.id})"


@dataclass(frozen=True)
class _Category:
    id: str
    name: str
    parent_id: str


def load_category_options(xml_path: Path) -> list[CategoryOption]:
    """Load categories in parent-first order while preserving XML sibling order."""
    root = ET.parse(xml_path).getroot()
    if root.tag != "PRODUCT_CATEGORY_EXPORT":
        raise ValueError("The category export has an unexpected XML root element")

    categories: list[_Category] = []
    category_by_id: dict[str, _Category] = {}

    for element in root.findall("./ELEMENTS/PRODUCT_CATEGORY"):
        category_id = (element.findtext("PROD_CAT_ID") or "").strip()
        name = (element.findtext("PROD_CAT_NAME") or "").strip()
        if not category_id or not name:
            raise ValueError("Every product category must have an ID and a name")
        if category_id in category_by_id:
            raise ValueError(f"Duplicate product category ID: {category_id}")

        parent_elements = element.findall("./PARENT_CATEGORIES/PARENT_CAT_ID")
        parent_elements.sort(key=lambda item: int(item.get("priority", "0")))
        parent_id = ((parent_elements[0].text if parent_elements else None) or "0").strip()
        category = _Category(id=category_id, name=name, parent_id=parent_id)
        categories.append(category)
        category_by_id[category_id] = category

    if not categories:
        raise ValueError("The category export does not contain any categories")

    children_by_parent: dict[str, list[_Category]] = {}
    for category in categories:
        children_by_parent.setdefault(category.parent_id, []).append(category)

    options: list[CategoryOption] = []
    visited: set[str] = set()

    def add_branch(category: _Category, depth: int) -> None:
        if category.id in visited:
            return
        visited.add(category.id)
        options.append(CategoryOption(category.id, category.name, category.parent_id, depth))
        for child in children_by_parent.get(category.id, []):
            add_branch(child, depth + 1)

    for category in categories:
        if category.parent_id == "0" or category.parent_id not in category_by_id or category.parent_id == category.id:
            add_branch(category, 0)

    # Keep malformed cyclic groups visible instead of silently dropping them.
    for category in categories:
        add_branch(category, 0)

    return options


def fetch_category_options(
    endpoint: str,
    username: str | None,
    password: str | None,
    destination: Path,
    timeout_seconds: int,
) -> list[CategoryOption]:
    """Fetch, validate, and atomically replace the persisted category export."""
    if not username or not password:
        raise CategoryRefreshError("API_USERNAME and API_PASSWORD are required to fetch categories")

    try:
        response = requests.post(
            endpoint,
            data={"user": username, "password": password},
            timeout=timeout_seconds,
        )
        response.raise_for_status()
        content = response.content

        download_url = _find_export_download_url(content, endpoint)
        if download_url:
            response = requests.get(download_url, timeout=timeout_seconds)
            response.raise_for_status()
            content = response.content
    except requests.RequestException as error:
        raise CategoryRefreshError(f"Could not fetch categories: {error}") from error

    if not content:
        raise CategoryRefreshError("The category endpoint returned an empty response")
    if len(content) > MAX_CATEGORIES_XML_BYTES:
        raise CategoryRefreshError("The category export is larger than the allowed 5 MB")

    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with NamedTemporaryFile(dir=destination.parent, prefix="categories-", suffix=".xml", delete=False) as file:
            file.write(content)
            temporary_path = Path(file.name)

        options = load_category_options(temporary_path)
        temporary_path.replace(destination)
        return options
    except (ET.ParseError, OSError, ValueError) as error:
        raise CategoryRefreshError(f"The downloaded category export is invalid: {error}") from error
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def _find_export_download_url(content: bytes, endpoint: str) -> str | None:
    parser = _ExportDownloadLinkParser()
    try:
        parser.feed(content.decode("utf-8-sig"))
    except UnicodeDecodeError:
        return None

    endpoint_url = urlparse(endpoint)
    for href in parser.hrefs:
        download_url = urljoin(endpoint, href)
        parsed_url = urlparse(download_url)
        if (
            parsed_url.scheme == endpoint_url.scheme
            and parsed_url.netloc == endpoint_url.netloc
            and parsed_url.path.startswith("/images/ImportExport/")
            and parsed_url.path.lower().endswith(".xml")
        ):
            return download_url
    return None