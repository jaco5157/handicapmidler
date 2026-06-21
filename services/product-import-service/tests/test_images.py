from app.models import ProductImageInput
from app.services.images import build_image_plan, compress_with_pillow
from app.utils import ensure_unique_filename_bases, suggest_image_name
from PIL import Image


def test_suggest_image_name_removes_number_suffixes_and_collapses_underscores():
    url = "https://mobilex.dk/images/vaegmonteret_badestol__hvid_ox5_5703_800x1000px.jpg"

    assert suggest_image_name(url) == "vaegmonteret-badestol-hvid"


def test_ensure_unique_filename_bases_adds_suffixes():
    values = ["same_name_123", "same name", "same-name"]

    assert ensure_unique_filename_bases(values) == ["same-name-123", "same-name", "same-name-2"]


def test_build_image_plan_creates_four_variants():
    plan = build_image_plan(
        [ProductImageInput(source_url="https://example.com/image.jpg", filename_base="product", alt_text="Alt")],
        "/images/products/",
    )

    assert plan[0].media_url == "/images/products/product.jpg"
    assert [variant.filename for variant in plan[0].variants] == [
        "product-p.jpg",
        "product.jpg",
        "product-r.jpg",
        "product-t.jpg",
    ]


def test_compress_with_pillow_writes_four_jpg_variants(tmp_path):
    source_path = tmp_path / "source.png"
    Image.new("RGBA", (700, 500), "white").save(source_path)

    output_paths = compress_with_pillow(source_path, tmp_path / "compressed", "badestol", jpeg_quality=85)

    assert sorted(output_paths) == ["badestol-p.jpg", "badestol-r.jpg", "badestol-t.jpg", "badestol.jpg"]
    for output_path in output_paths.values():
        assert output_path.exists()
        assert output_path.suffix == ".jpg"
