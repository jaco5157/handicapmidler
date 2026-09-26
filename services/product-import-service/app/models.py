from __future__ import annotations

from pydantic import BaseModel, Field, ValidationInfo, field_validator, model_validator

from app.utils import normalize_filename_base, normalize_price


REQUIRED_FIELD_LABELS = {
    "product_name": "Title",
    "product_number": "Product number",
    "price": "Price",
    "category_id": "Product category",
    "title_tag": "Title tag",
    "meta_description": "Meta description",
    "meta_keywords": "Meta keywords",
}


class ScrapeRequest(BaseModel):
    url: str

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        value = value.strip()
        if not value.startswith(("http://", "https://")):
            raise ValueError("A supplier URL must start with http:// or https://")
        return value


class ScrapedImage(BaseModel):
    source_url: str
    filename_base: str
    alt_text: str = ""
    enabled: bool = True


class ScrapedProduct(BaseModel):
    source_url: str
    product_name: str = ""
    hmi_number: str | None = None
    product_number: str | None = None
    images: list[ScrapedImage] = Field(default_factory=list)


class SpecRow(BaseModel):
    name: str = ""
    value: str = ""

    @field_validator("name", "value", mode="before")
    @classmethod
    def strip_optional_string(cls, value: object) -> str:
        return str(value or "").strip()

    @property
    def has_content(self) -> bool:
        return bool(self.name or self.value)


class ProductImageInput(BaseModel):
    source_url: str
    filename_base: str
    alt_text: str = ""
    enabled: bool = True
    is_primary: bool = False

    @field_validator("source_url", "filename_base", "alt_text", mode="before")
    @classmethod
    def strip_string(cls, value: object) -> str:
        return str(value or "").strip()


class ProductDraft(BaseModel):
    source_url: str | None = None
    product_name: str
    product_number: str
    hmi_number: str | None = None
    price: str
    category_id: str
    title_tag: str
    meta_description: str
    meta_keywords: str
    short_description: str = ""
    long_description: str = ""
    specs: list[SpecRow] = Field(default_factory=list)
    images: list[ProductImageInput] = Field(default_factory=list)

    @field_validator(
        "product_name",
        "product_number",
        "price",
        "category_id",
        "title_tag",
        "meta_description",
        "meta_keywords",
        mode="before",
    )
    @classmethod
    def strip_required_strings(cls, value: object, info: ValidationInfo) -> str:
        stripped = str(value or "").strip()
        if not stripped:
            raise ValueError(f"{REQUIRED_FIELD_LABELS[info.field_name]} is required")
        return stripped

    @field_validator(
        "source_url",
        "hmi_number",
        "short_description",
        "long_description",
        mode="before",
    )
    @classmethod
    def strip_optional_strings(cls, value: object) -> str | None:
        if value is None:
            return None
        stripped = str(value).strip()
        return stripped or None

    @model_validator(mode="after")
    def validate_product(self) -> "ProductDraft":
        if self.hmi_number and not self.hmi_number.isdigit():
            raise ValueError("HMI number must contain only digits")

        if not self.product_number.isdigit():
            raise ValueError("Product number must contain only digits")

        if not self.category_id.isdigit():
            raise ValueError("Category ID must contain only digits")

        self.price = normalize_price(self.price)

        enabled_images = [image for image in self.images if image.enabled]
        if not enabled_images:
            raise ValueError("At least one image must be enabled")

        primary_images = [image for image in enabled_images if image.is_primary]
        if len(primary_images) > 1:
            raise ValueError("Only one enabled image can be the primary image")

        filename_bases = [normalize_filename_base(image.filename_base) for image in enabled_images]
        if len(filename_bases) != len(set(filename_bases)):
            raise ValueError("Image filenames must be unique")

        for image in enabled_images:
            if not image.source_url.startswith(("http://", "https://")):
                raise ValueError("Enabled image URLs must start with http:// or https://")
            if not image.filename_base:
                raise ValueError("Enabled images must have a filename")

        return self

    @property
    def non_empty_specs(self) -> list[SpecRow]:
        return [row for row in self.specs if row.has_content]

    @property
    def enabled_images(self) -> list[ProductImageInput]:
        enabled_images = [image for image in self.images if image.enabled]
        return sorted(enabled_images, key=lambda image: not image.is_primary)


class MediaReference(BaseModel):
    public_url: str
    alt_text: str = ""
