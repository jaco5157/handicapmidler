from __future__ import annotations

import ipaddress
import shutil
import socket
import subprocess
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from PIL import Image, ImageChops

from app.config import Settings
from app.models import ProductImageInput
from app.utils import normalize_filename_base

MAX_IMAGE_DOWNLOAD_REDIRECTS = 3
ALLOWED_IMAGE_CONTENT_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


@dataclass
class ImageVariantPlan:
    kind: str
    filename: str
    public_url: str
    local_path: Path | None = None

    def to_dict(self) -> dict[str, str | None]:
        return {
            "kind": self.kind,
            "filename": self.filename,
            "public_url": self.public_url,
            "local_path": str(self.local_path) if self.local_path else None,
        }


@dataclass
class ProductImagePlan:
    source_url: str
    filename_base: str
    alt_text: str
    media_url: str
    variants: list[ImageVariantPlan]

    def to_dict(self) -> dict[str, object]:
        return {
            "source_url": self.source_url,
            "filename_base": self.filename_base,
            "alt_text": self.alt_text,
            "media_url": self.media_url,
            "variants": [variant.to_dict() for variant in self.variants],
        }


def build_image_plan(images: list[ProductImageInput], public_url_prefix: str) -> list[ProductImagePlan]:
    prefix = public_url_prefix.rstrip("/") + "/"
    plans: list[ProductImagePlan] = []
    for image in images:
        if not image.enabled:
            continue

        base = normalize_filename_base(image.filename_base)
        variants = [
            ImageVariantPlan("p", f"{base}-p.jpg", f"{prefix}{base}-p.jpg"),
            ImageVariantPlan("o", f"{base}.jpg", f"{prefix}{base}.jpg"),
            ImageVariantPlan("r", f"{base}-r.jpg", f"{prefix}{base}-r.jpg"),
            ImageVariantPlan("t", f"{base}-t.jpg", f"{prefix}{base}-t.jpg"),
        ]
        plans.append(ProductImagePlan(image.source_url, base, image.alt_text, f"{prefix}{base}.jpg", variants))
    return plans


def prepare_product_images(images: list[ProductImageInput], settings: Settings) -> list[ProductImagePlan]:
    settings.ensure_data_dirs()
    plans = build_image_plan(images, settings.image_public_url_prefix)
    originals_dir = settings.data_dir / "originals"
    compressed_dir = settings.data_dir / "compressed"

    for plan in plans:
        original_path = download_image(
            plan.source_url,
            originals_dir,
            plan.filename_base,
            settings.request_timeout_seconds,
            settings.image_download_max_bytes,
        )
        if settings.compression_backend == "external":
            generated_paths = compress_with_external_tools(original_path, compressed_dir, plan.filename_base, settings)
        else:
            generated_paths = compress_with_pillow(original_path, compressed_dir, plan.filename_base, settings.jpeg_quality)

        for variant in plan.variants:
            variant.local_path = generated_paths[variant.filename]

    return plans


def download_image(
    url: str,
    target_dir: Path,
    filename_base: str,
    timeout_seconds: int,
    max_download_bytes: int = 10_000_000,
) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    response = _get_public_image_response(url, timeout_seconds)
    try:
        response.raise_for_status()
        final_url = getattr(response, "url", None) or url
        extension = _supported_image_extension(final_url, response.headers.get("content-type"))
        target_path = target_dir / f"{normalize_filename_base(filename_base)}{extension}"
        _write_limited_response(response, target_path, max_download_bytes)
    finally:
        response.close()

    return target_path


def compress_with_pillow(source_path: Path, output_dir: Path, filename_base: str, jpeg_quality: int = 88) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    base = normalize_filename_base(filename_base)
    image = Image.open(source_path)
    image = _flatten_and_trim(image)

    variants = {
        f"{base}-p.jpg": image,
        f"{base}.jpg": _resize_long_edge(image, 525),
        f"{base}-r.jpg": _resize_long_edge(image, 320),
        f"{base}-t.jpg": _resize_long_edge(image, 320),
    }

    output_paths: dict[str, Path] = {}
    for filename, variant_image in variants.items():
        output_path = output_dir / filename
        variant_image.save(output_path, format="JPEG", quality=jpeg_quality, optimize=True, progressive=True)
        output_paths[filename] = output_path

    return output_paths


def compress_with_external_tools(source_path: Path, output_dir: Path, filename_base: str, settings: Settings) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    base = normalize_filename_base(filename_base)
    work_dir = output_dir / f"{base}-work"
    compress_dir = work_dir / "Compress"
    compressed_dir = work_dir / "Compressed"
    shutil.rmtree(work_dir, ignore_errors=True)
    for folder in [compress_dir / "p", compress_dir / "o", compress_dir / "r", compress_dir / "t", compressed_dir]:
        folder.mkdir(parents=True, exist_ok=True)

    converted_path = compress_dir / f"{base}.jpg"
    subprocess.run(
        [
            settings.magick_command,
            str(source_path),
            "-background",
            "white",
            "-alpha",
            "remove",
            "-alpha",
            "off",
            "-trim",
            "-bordercolor",
            "white",
            "-quality",
            "100",
            str(converted_path),
        ],
        check=True,
    )

    shutil.copy2(converted_path, compress_dir / "p" / f"{base}-p.jpg")
    shutil.copy2(converted_path, compress_dir / "o" / f"{base}.jpg")
    shutil.copy2(converted_path, compress_dir / "r" / f"{base}-r.jpg")
    shutil.copy2(converted_path, compress_dir / "t" / f"{base}-t.jpg")

    subprocess.run([settings.caesium_command, "-q", "0", "-o", str(compressed_dir), str(compress_dir / "p")], check=True)
    subprocess.run([settings.caesium_command, "--long-edge", "525", "-q", "0", "-o", str(compressed_dir), str(compress_dir / "o")], check=True)
    subprocess.run([settings.caesium_command, "--long-edge", "320", "-q", "0", "-o", str(compressed_dir), str(compress_dir / "r")], check=True)
    subprocess.run([settings.caesium_command, "--long-edge", "320", "-q", "0", "-o", str(compressed_dir), str(compress_dir / "t")], check=True)

    output_paths: dict[str, Path] = {}
    for filename in [f"{base}-p.jpg", f"{base}.jpg", f"{base}-r.jpg", f"{base}-t.jpg"]:
        final_path = output_dir / filename
        shutil.copy2(compressed_dir / filename, final_path)
        output_paths[filename] = final_path

    shutil.rmtree(work_dir, ignore_errors=True)
    return output_paths


def _flatten_and_trim(image: Image.Image) -> Image.Image:
    rgba_image = image.convert("RGBA")
    white = Image.new("RGBA", rgba_image.size, "WHITE")
    flattened = Image.alpha_composite(white, rgba_image).convert("RGB")
    background = Image.new("RGB", flattened.size, "WHITE")
    diff = ImageChops.difference(flattened, background)
    bbox = diff.getbbox()
    return flattened.crop(bbox) if bbox else flattened


def _resize_long_edge(image: Image.Image, long_edge: int) -> Image.Image:
    width, height = image.size
    current_long_edge = max(width, height)
    if current_long_edge <= long_edge:
        return image.copy()

    scale = long_edge / current_long_edge
    new_size = (max(1, round(width * scale)), max(1, round(height * scale)))
    return image.resize(new_size, Image.Resampling.LANCZOS)


def _get_public_image_response(url: str, timeout_seconds: int) -> requests.Response:
    current_url = url
    for redirect_count in range(MAX_IMAGE_DOWNLOAD_REDIRECTS + 1):
        _ensure_public_http_url(current_url)
        response = requests.get(current_url, timeout=timeout_seconds, stream=True, allow_redirects=False)
        if not response.is_redirect:
            return response

        if redirect_count == MAX_IMAGE_DOWNLOAD_REDIRECTS:
            response.close()
            break

        redirect_location = response.headers.get("location")
        response.close()
        if not redirect_location:
            raise ValueError("Image URL redirected without a Location header.")
        current_url = urljoin(current_url, redirect_location)

    raise ValueError("Image URL redirected too many times.")


def _ensure_public_http_url(url: str) -> None:
    parsed_url = urlparse(url)
    if parsed_url.scheme not in {"http", "https"}:
        raise ValueError("Image URL must use http or https.")
    if not parsed_url.hostname:
        raise ValueError("Image URL must include a hostname.")

    try:
        port = parsed_url.port or (443 if parsed_url.scheme == "https" else 80)
    except ValueError as error:
        raise ValueError("Image URL contains an invalid port.") from error

    try:
        address_infos = socket.getaddrinfo(parsed_url.hostname, port, type=socket.SOCK_STREAM)
    except socket.gaierror as error:
        raise ValueError("Image URL hostname could not be resolved.") from error

    if not address_infos:
        raise ValueError("Image URL hostname did not resolve to an address.")

    for address_info in address_infos:
        ip_address = ipaddress.ip_address(address_info[4][0])
        if _is_blocked_download_ip(ip_address):
            raise ValueError("Image URL must resolve to a public internet address.")


def _is_blocked_download_ip(ip_address: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    return (
        not ip_address.is_global
        or ip_address.is_loopback
        or ip_address.is_link_local
        or ip_address.is_multicast
        or ip_address.is_private
        or ip_address.is_reserved
        or ip_address.is_unspecified
    )


def _supported_image_extension(url: str, content_type: str | None) -> str:
    normalized_content_type = _normalize_content_type(content_type)
    if normalized_content_type:
        extension = _extension_from_content_type(normalized_content_type)
        if not extension:
            raise ValueError("Downloaded file is not a supported image type.")
        return extension

    extension = _extension_from_url(url)
    if extension:
        return extension
    raise ValueError("Image response must include a supported image content type or file extension.")


def _write_limited_response(response: requests.Response, target_path: Path, max_download_bytes: int) -> None:
    content_length = response.headers.get("content-length")
    if content_length:
        try:
            declared_size = int(content_length)
        except ValueError:
            declared_size = 0
        if declared_size > max_download_bytes:
            raise ValueError(f"Image download exceeds the {max_download_bytes} byte limit.")

    bytes_written = 0
    try:
        with target_path.open("wb") as file_handle:
            for chunk in response.iter_content(chunk_size=64 * 1024):
                if not chunk:
                    continue
                bytes_written += len(chunk)
                if bytes_written > max_download_bytes:
                    raise ValueError(f"Image download exceeds the {max_download_bytes} byte limit.")
                file_handle.write(chunk)
    except Exception:
        target_path.unlink(missing_ok=True)
        raise


def _normalize_content_type(content_type: str | None) -> str | None:
    if not content_type:
        return None
    return content_type.split(";", 1)[0].strip().lower()


def _extension_from_url(url: str) -> str | None:
    suffix = Path(urlparse(url).path).suffix.lower()
    return suffix if suffix in {".jpg", ".jpeg", ".png", ".webp"} else None


def _extension_from_content_type(content_type: str | None) -> str | None:
    return ALLOWED_IMAGE_CONTENT_TYPES.get(_normalize_content_type(content_type) or "")
