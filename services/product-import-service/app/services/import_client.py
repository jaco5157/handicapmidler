from __future__ import annotations

from dataclasses import dataclass
from ftplib import FTP, FTP_TLS
from pathlib import Path
from urllib.parse import urlparse

import requests

from app.config import Settings


@dataclass
class FileUpload:
    local_path: Path
    remote_dir: str
    remote_name: str

    def remote_path(self) -> str:
        return f"{self.remote_dir.rstrip('/')}/{self.remote_name}"


def save_xml(xml_text: str, settings: Settings) -> Path:
    settings.ensure_data_dirs()
    xml_path = settings.data_dir / "xml" / settings.xml_file_name
    xml_path.write_text(xml_text, encoding="utf-8")
    return xml_path


def upload_product_import(xml_path: Path, image_uploads: list[FileUpload], settings: Settings) -> dict[str, object]:
    if not settings.upload_enabled:
        return {
            "dry_run": True,
            "message": "Upload is disabled. Files were generated locally only.",
            "xml_path": str(xml_path),
            "planned_image_uploads": [upload.remote_path() for upload in image_uploads],
            "planned_xml_upload": f"{settings.xml_ftp_dir.rstrip('/')}/{settings.xml_file_name}",
            "planned_import_url": _build_import_url(settings),
        }

    settings.require_upload_config()
    xml_upload = FileUpload(xml_path, settings.xml_ftp_dir, settings.xml_file_name)
    with _ftp_client(settings) as ftp:
        for upload in [*image_uploads, xml_upload]:
            _upload_file(ftp, upload)

    response = requests.post(
        settings.api_upload_endpoint,
        params={"file": settings.xml_import_file_param, "response": "1", "updateonly": "0"},
        data={"user": settings.api_username, "password": settings.api_password},
        timeout=settings.request_timeout_seconds,
    )
    response.raise_for_status()

    return {
        "dry_run": False,
        "message": "Images and XML were uploaded, and the import endpoint was called.",
        "image_uploads": [upload.remote_path() for upload in image_uploads],
        "xml_upload": xml_upload.remote_path(),
        "import_response_status": response.status_code,
        "import_response_text": response.text,
    }


def _ftp_client(settings: Settings) -> FTP:
    host = _normalize_ftp_host(settings.ftp_host or "")
    client: FTP = FTP_TLS() if settings.ftp_use_tls else FTP()
    client.connect(host, settings.ftp_port)
    client.login(settings.ftp_username or "", settings.ftp_password or "")
    if isinstance(client, FTP_TLS):
        client.prot_p()
    return client


def _upload_file(ftp: FTP, upload: FileUpload) -> None:
    _ensure_remote_dir(ftp, upload.remote_dir)
    with upload.local_path.open("rb") as file_handle:
        ftp.storbinary(f"STOR {upload.remote_name}", file_handle)


def _ensure_remote_dir(ftp: FTP, remote_dir: str) -> None:
    parts = [part for part in remote_dir.strip("/").split("/") if part]
    if remote_dir.startswith("/"):
        ftp.cwd("/")
    for part in parts:
        try:
            ftp.cwd(part)
        except Exception:
            ftp.mkd(part)
            ftp.cwd(part)


def _normalize_ftp_host(host: str) -> str:
    if "://" not in host:
        return host.strip("/")
    parsed = urlparse(host)
    return parsed.hostname or host


def _build_import_url(settings: Settings) -> str | None:
    if not settings.api_upload_endpoint:
        return None
    separator = "&" if "?" in settings.api_upload_endpoint else "?"
    return f"{settings.api_upload_endpoint}{separator}file={settings.xml_import_file_param}&response=1&updateonly=0"
