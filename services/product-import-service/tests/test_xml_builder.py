from xml.etree import ElementTree as ET

from app.config import Settings
from app.models import MediaReference, ProductDraft, ProductImageInput, SpecRow
from app.services.xml_builder import build_product_xml, build_specs_table


def make_draft(**overrides):
    data = {
        "product_name": "Badestol",
        "product_number": "302040",
        "hmi_number": "43651",
        "price": "149,00",
        "category_id": "50",
        "title_tag": "Badestol titel",
        "meta_description": "Meta description",
        "meta_keywords": "badestol, hmi",
        "short_description": "<p>Kort tekst</p>",
        "long_description": "<p>Lang tekst</p>",
        "specs": [SpecRow(name="Farve", value="Hvid")],
        "images": [ProductImageInput(source_url="https://example.com/image.jpg", filename_base="badestol")],
    }
    data.update(overrides)
    return ProductDraft(**data)


def test_build_specs_table_puts_hmi_first():
    table = build_specs_table("43651", [SpecRow(name="Farve", value="Hvid")])

    assert table == '<table class="prodinfotable"><tbody><tr><td>HMI-nr.</td><td>43651</td></tr><tr><td>Farve</td><td>Hvid</td></tr></tbody></table>'


def test_build_product_xml_maps_required_fields():
    settings = Settings(data_dir="data")
    draft = make_draft()
    xml_text = build_product_xml(
        draft,
        [MediaReference(public_url="/images/products/badestol.jpg", alt_text="Badestol")],
        settings,
    )
    root = ET.fromstring(xml_text)
    product = root.find("ELEMENTS/PRODUCT")

    assert root.tag == "PRODUCT_EXPORT"
    assert root.attrib["type"] == "PRODUCTS"
    assert product.findtext("GENERAL/PROD_NUM") == "302040"
    assert product.findtext("GENERAL/LANGUAGE_ID") == "26"
    assert product.findtext("GENERAL/PROD_PHOTO_URL") == "/images/products/badestol.jpg"
    assert product.findtext("DESCRIPTION/PROD_SEARCHWORD") == "badestol, hmi"
    assert product.findtext("DESCRIPTION/META_DESCRIPTION") == "Meta description"
    assert product.findtext("DESCRIPTION/TITLE") == "Badestol titel"
    assert product.find("PRODUCT_CATEGORIES/PROD_CAT_ID").attrib["priority"] == "0"
    assert product.findtext("PRICES/PRICE/UNIT_PRICE") == "149,00"
    assert product.findtext("PRODUCT_MEDIA/MEDIA/MEDIA_URL") == "/images/products/badestol.jpg"


def test_build_product_xml_omits_desc_long_2_when_specs_and_hmi_are_empty():
    settings = Settings(data_dir="data")
    draft = make_draft(hmi_number=None, specs=[])
    xml_text = build_product_xml(draft, [MediaReference(public_url="/images/products/badestol.jpg")], settings)
    root = ET.fromstring(xml_text)

    assert root.find("ELEMENTS/PRODUCT/DESCRIPTION/DESC_LONG_2") is None
