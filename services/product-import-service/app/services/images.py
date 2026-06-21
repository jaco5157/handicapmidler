from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import requests
from PIL import Image, ImageChops

from app.config import Settings
from app.models import ProductImageInput
from app.utils import normalize_filename_base


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
        original_path = download_image(plan.source_url, originals_dir, plan.filename_base, settings.request_timeout_seconds)
        if settings.compression_backend == "external":
            generated_paths = compress_with_external_tools(original_path, compressed_dir, plan.filename_base, settings)
        else:
            generated_paths = compress_with_pillow(original_path, compressed_dir, plan.filename_base, settings.jpeg_quality)

        for variant in plan.variants:
            variant.local_path = generated_paths[variant.filename]

    return plans


def download_image(url: str, target_dir: Path, filename_base: str, timeout_seconds: int) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    response = requests.get(url, timeout=timeout_seconds)
    response.raise_for_status()

    extension = _extension_from_url(url) or _extension_from_content_type(response.headers.get("content-type")) or ".jpg"
    target_path = target_dir / f"{normalize_filename_base(filename_base)}{extension}"
    target_path.write_bytes(response.content)
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


def _extension_from_url(url: str) -> str | None:
    suffix = Path(urlparse(url).path).suffix.lower()
    return suffix if suffix in {".jpg", ".jpeg", ".png", ".webp"} else None


def _extension_from_content_type(content_type: str | None) -> str | None:
    if not content_type:
        return None
    content_type = content_type.split(";", 1)[0].strip().lower()
    return {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
    }.get(content_type)
