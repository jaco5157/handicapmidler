from __future__ import annotations

from html import escape
from xml.dom import minidom
from xml.etree import ElementTree as ET

from app.config import Settings
from app.models import MediaReference, ProductDraft, SpecRow


def build_specs_table(hmi_number: str | None, specs: list[SpecRow]) -> str | None:
    rows: list[tuple[str, str]] = []
    if hmi_number:
        rows.append(("HMI-nr.", hmi_number))

    for spec in specs:
        if spec.has_content:
            rows.append((spec.name, spec.value))

    if not rows:
        return None

    row_markup = "".join(
        f"<tr><td>{escape(name)}</td><td>{escape(value)}</td></tr>" for name, value in rows
    )
    return f'<table class="prodinfotable"><tbody>{row_markup}</tbody></table>'


def build_product_xml(draft: ProductDraft, media: list[MediaReference], settings: Settings) -> str:
    primary_image_url = media[0].public_url if media else ""
    root = ET.Element("PRODUCT_EXPORT", {"type": "PRODUCTS"})
    elements = ET.SubElement(root, "ELEMENTS")
    product = ET.SubElement(elements, "PRODUCT")

    general = ET.SubElement(product, "GENERAL")
    _sub_element(general, "PROD_NUM", draft.product_number)
    _sub_element(general, "LANGUAGE_ID", str(settings.language_id))
    _sub_element(general, "PROD_NAME", draft.product_name)
    _sub_element(general, "PROD_PHOTO_URL", primary_image_url)

    description = ET.SubElement(product, "DESCRIPTION")
    _sub_element(description, "DESC_SHORT", draft.short_description or "")
    _sub_element(description, "DESC_LONG", draft.long_description or "")
    specs_table = build_specs_table(draft.hmi_number, draft.non_empty_specs)
    if specs_table:
        _sub_element(description, "DESC_LONG_2", specs_table)
    _sub_element(description, "PROD_SEARCHWORD", draft.meta_keywords)
    _sub_element(description, "META_DESCRIPTION", draft.meta_description)
    _sub_element(description, "TITLE", draft.title_tag)

    categories = ET.SubElement(product, "PRODUCT_CATEGORIES")
    category = ET.SubElement(categories, "PROD_CAT_ID", {"priority": "0"})
    category.text = draft.category_id

    prices = ET.SubElement(product, "PRICES")
    price = ET.SubElement(prices, "PRICE")
    _sub_element(price, "CURRENCY_CODE", settings.currency_code)
    _sub_element(price, "PRICE_B2B_ID", str(settings.price_b2b_id))
    _sub_element(price, "AMOUNT", "1")
    _sub_element(price, "UNIT_PRICE", draft.price)

    media_container = ET.SubElement(product, "PRODUCT_MEDIA")
    for media_item in media:
        media_element = ET.SubElement(media_container, "MEDIA")
        _sub_element(media_element, "MEDIA_URL", media_item.public_url)
        _sub_element(media_element, "MEDIA_ALT_TEXT", media_item.alt_text)

    return _format_xml(root)


def _sub_element(parent: ET.Element, tag: str, text: str) -> ET.Element:
    element = ET.SubElement(parent, tag)
    element.text = text
    return element


def _format_xml(root: ET.Element) -> str:
    rough_string = ET.tostring(root, encoding="utf-8")
    parsed = minidom.parseString(rough_string)
    return parsed.toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")
