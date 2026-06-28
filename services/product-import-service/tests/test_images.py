import socket

import pytest
from app.models import ProductImageInput
from app.services import images
from app.services.images import build_image_plan, compress_with_pillow, download_image
from app.utils import ensure_unique_filename_bases, suggest_image_name
from PIL import Image


class FakeImageResponse:
    def __init__(self, chunks=None, headers=None, url="https://example.com/image.jpg"):
        self.chunks = chunks or [b"image-bytes"]
        self.headers = headers or {"content-type": "image/jpeg"}
        self.url = url
        self.is_redirect = False
        self.closed = False

    def raise_for_status(self):
        return None

    def iter_content(self, chunk_size=64 * 1024):
        yield from self.chunks

    def close(self):
        self.closed = True


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


def test_download_image_writes_supported_public_image(monkeypatch, tmp_path):
    _mock_dns(monkeypatch, "8.8.8.8")
    response = FakeImageResponse(chunks=[b"image", b"-bytes"], headers={"content-type": "image/jpeg"})
    monkeypatch.setattr(images.requests, "get", lambda *args, **kwargs: response)

    image_path = download_image("https://example.com/image", tmp_path, "Badestol", timeout_seconds=1, max_download_bytes=20)

    assert image_path.name == "badestol.jpg"
    assert image_path.read_bytes() == b"image-bytes"
    assert response.closed


def test_download_image_rejects_private_ip_addresses(monkeypatch, tmp_path):
    _mock_dns(monkeypatch, "127.0.0.1")
    monkeypatch.setattr(images.requests, "get", lambda *args, **kwargs: pytest.fail("request should not be sent"))

    with pytest.raises(ValueError, match="public internet address"):
        download_image("https://example.com/image.jpg", tmp_path, "Badestol", timeout_seconds=1)


def test_download_image_rejects_unsupported_content_type(monkeypatch, tmp_path):
    _mock_dns(monkeypatch, "8.8.8.8")
    response = FakeImageResponse(headers={"content-type": "text/html"})
    monkeypatch.setattr(images.requests, "get", lambda *args, **kwargs: response)

    with pytest.raises(ValueError, match="supported image type"):
        download_image("https://example.com/image.jpg", tmp_path, "Badestol", timeout_seconds=1)


def test_download_image_rejects_oversized_response(monkeypatch, tmp_path):
    _mock_dns(monkeypatch, "8.8.8.8")
    response = FakeImageResponse(headers={"content-type": "image/jpeg", "content-length": "21"})
    monkeypatch.setattr(images.requests, "get", lambda *args, **kwargs: response)

    with pytest.raises(ValueError, match="byte limit"):
        download_image("https://example.com/image.jpg", tmp_path, "Badestol", timeout_seconds=1, max_download_bytes=20)

    assert not (tmp_path / "badestol.jpg").exists()


def _mock_dns(monkeypatch, ip_address):
    monkeypatch.setattr(
        images.socket,
        "getaddrinfo",
        lambda host, port, type=socket.SOCK_STREAM: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip_address, port))],
    )
