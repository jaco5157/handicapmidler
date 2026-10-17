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


def extract_product_number(value: str | None) -> str | None:
    if not value:
        return None

    match = re.search(r"\b(?=[A-Za-z0-9-]*\d)[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*\b", value)
    return match.group(0) if match else None


def normalize_price(value: str) -> str:
    raw_value = value.strip().replace(" ", "")
    if not raw_value:
        raise ValueError("Pris er påkrævet")

    if "," in raw_value and "." in raw_value:
        raw_value = raw_value.replace(".", "").replace(",", ".")
    elif "," in raw_value:
        raw_value = raw_value.replace(",", ".")

    try:
        decimal_value = Decimal(raw_value)
    except InvalidOperation as error:
        raise ValueError("Prisen skal være et gyldigt tal") from error

    if decimal_value <= 0:
        raise ValueError("Prisen skal være større end nul")

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
    for index, part in enumerate(parts):
        if index > 0 and re.search(r"\d", part):
            break
        kept_parts.append(part)

    return normalize_filename_base("-".join(kept_parts or [stem]))


def suggest_product_image_names(image_urls: list[str], product_number: str | None) -> list[str]:
    normalized_product_number = normalize_filename_base(product_number) if product_number else ""
    names: list[str] = []

    for image_url in image_urls:
        provider_name = suggest_image_name(image_url)
        if normalized_product_number and not _contains_slug_part(provider_name, normalized_product_number):
            provider_name = f"{provider_name}-{normalized_product_number}"
        names.append(provider_name)

    return ensure_unique_filename_bases(names)


def _contains_slug_part(value: str, part: str) -> bool:
    return re.search(rf"(?:^|-){re.escape(part)}(?:-|$)", value) is not None


def dedupe_preserving_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def ensure_unique_filename_bases(values: list[str]) -> list[str]:
    normalized_values = [normalize_filename_base(value) for value in values]
    reserved = set(normalized_values)
    used: set[str] = set()
    next_suffix: dict[str, int] = {}
    result: list[str] = []
    for base in normalized_values:
        candidate = base
        suffix = next_suffix.get(base, 2)
        while candidate in used:
            while (candidate := f"{base}-{suffix}") in used or candidate in reserved:
                suffix += 1
        next_suffix[base] = suffix
        used.add(candidate)
        result.append(candidate)
    return result
