from __future__ import annotations

import re
import unicodedata
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from urllib.parse import unquote, urlparse


def extract_first_number(value: str | None) -> str | None:
    if not value:
        return None

    match = re.search(r"\d+", value)
    return match.group(0) if match else None


def normalize_price(value: str) -> str:
    raw_value = value.strip().replace(" ", "")
    if not raw_value:
        raise ValueError("Price is required")

    if "," in raw_value and "." in raw_value:
        raw_value = raw_value.replace(".", "").replace(",", ".")
    elif "," in raw_value:
        raw_value = raw_value.replace(",", ".")

    try:
        decimal_value = Decimal(raw_value)
    except InvalidOperation as error:
        raise ValueError("Price must be a valid number") from error

    if decimal_value <= 0:
        raise ValueError("Price must be greater than zero")

    rounded = decimal_value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"{rounded:.2f}".replace(".", ",")


def normalize_filename_base(value: str) -> str:
    value = value.strip()
    if not value:
        return "product-image"

    value = (
        value.replace("æ", "ae")
        .replace("ø", "oe")
        .replace("å", "aa")
        .replace("Æ", "Ae")
        .replace("Ø", "Oe")
        .replace("Å", "Aa")
    )
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^A-Za-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-").lower()
    return value or "product-image"


def suggest_image_name(image_url: str) -> str:
    path = urlparse(image_url).path
    filename = unquote(path.rsplit("/", 1)[-1])
    stem = filename.rsplit(".", 1)[0] if "." in filename else filename
    parts = [part for part in re.split(r"_+", stem) if part]

    kept_parts: list[str] = []
    for part in parts:
        if re.search(r"\d", part):
            break
        kept_parts.append(part)

    return normalize_filename_base("-".join(kept_parts or [stem]))


def dedupe_preserving_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def ensure_unique_filename_bases(values: list[str]) -> list[str]:
    counts: dict[str, int] = {}
    result: list[str] = []
    for value in values:
        base = normalize_filename_base(value)
        count = counts.get(base, 0)
        counts[base] = count + 1
        result.append(base if count == 0 else f"{base}-{count + 1}")
    return result
