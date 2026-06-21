from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from app.config import get_settings
from app.models import MediaReference, ProductDraft, ScrapeRequest
from app.scraper.mobilex import MobilexScrapeError, scrape_mobilex_product_page
from app.services.images import build_image_plan, prepare_product_images
from app.services.import_client import FileUpload, save_xml, upload_product_import
from app.services.xml_builder import build_product_xml

BASE_DIR = Path(__file__).resolve().parent
settings = get_settings()

app = FastAPI(title=settings.app_name)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "upload_enabled": settings.upload_enabled,
            "image_public_url_prefix": settings.image_public_url_prefix,
        },
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/scrape")
def scrape_product(request: ScrapeRequest) -> dict[str, object]:
    try:
        product = scrape_mobilex_product_page(request.url, settings)
    except MobilexScrapeError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return product.model_dump()


@app.post("/api/preview")
def preview_product(draft: ProductDraft) -> dict[str, object]:
    image_plan = build_image_plan(draft.enabled_images, settings.image_public_url_prefix)
    media = [MediaReference(public_url=image.media_url, alt_text=image.alt_text) for image in image_plan]
    xml_text = build_product_xml(draft, media, settings)
    return {
        "xml": xml_text,
        "media": [image.to_dict() for image in image_plan],
        "upload_enabled": settings.upload_enabled,
    }


@app.post("/api/upload")
def upload_product(draft: ProductDraft) -> dict[str, object]:
    try:
        image_plan = prepare_product_images(draft.enabled_images, settings)
        media = [MediaReference(public_url=image.media_url, alt_text=image.alt_text) for image in image_plan]
        xml_text = build_product_xml(draft, media, settings)
        xml_path = save_xml(xml_text, settings)
        image_uploads = [
            FileUpload(variant.local_path, settings.image_ftp_dir, variant.filename)
            for image in image_plan
            for variant in image.variants
            if variant.local_path is not None
        ]
        upload_result = upload_product_import(xml_path, image_uploads, settings)
    except ValidationError as error:
        raise HTTPException(status_code=422, detail=error.errors()) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error

    return {
        "xml": xml_text,
        "media": [image.to_dict() for image in image_plan],
        "upload": upload_result,
    }
