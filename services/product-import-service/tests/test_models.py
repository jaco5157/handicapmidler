import pytest
from pydantic import ValidationError

from app.models import ProductDraft, ProductImageInput


def make_draft(**overrides):
    data = {
        "product_name": "Badestol",
        "product_number": "302040",
        "hmi_number": "43651",
        "price": "149.5",
        "category_id": "50",
        "title_tag": "Badestol titel",
        "meta_description": "Meta description",
        "meta_keywords": "badestol, hmi",
        "images": [ProductImageInput(source_url="https://example.com/image.jpg", filename_base="badestol")],
    }
    data.update(overrides)
    return ProductDraft(**data)


def test_product_draft_normalizes_price():
    draft = make_draft(price="1.499,95")

    assert draft.price == "1499,95"


def test_product_draft_requires_numeric_category_id():
    with pytest.raises(ValidationError):
        make_draft(category_id="abc")


def test_product_draft_rejects_duplicate_image_filenames():
    with pytest.raises(ValidationError):
        make_draft(
            images=[
                ProductImageInput(source_url="https://example.com/1.jpg", filename_base="badestol"),
                ProductImageInput(source_url="https://example.com/2.jpg", filename_base="badestol"),
            ]
        )


def test_product_draft_places_primary_image_first():
    draft = make_draft(
        images=[
            ProductImageInput(source_url="https://example.com/1.jpg", filename_base="side"),
            ProductImageInput(source_url="https://example.com/2.jpg", filename_base="front", is_primary=True),
            ProductImageInput(source_url="https://example.com/3.jpg", filename_base="detail"),
        ]
    )

    assert [image.filename_base for image in draft.enabled_images] == ["front", "side", "detail"]


def test_product_draft_rejects_multiple_primary_images():
    with pytest.raises(ValidationError, match="Only one enabled image can be the primary image"):
        make_draft(
            images=[
                ProductImageInput(
                    source_url="https://example.com/1.jpg",
                    filename_base="front",
                    is_primary=True,
                ),
                ProductImageInput(
                    source_url="https://example.com/2.jpg",
                    filename_base="side",
                    is_primary=True,
                ),
            ]
        )
