from __future__ import annotations

import time
from dataclasses import dataclass
from ftplib import FTP, FTP_TLS, Error, error_perm, error_temp
from pathlib import Path, PurePosixPath
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
from uuid import uuid4
from xml.etree import ElementTree as ET

import requests

from app.config import Settings


@dataclass
class FileUpload:
    local_path: Path
    remote_dir: str
    remote_name: str

    def remote_path(self) -> str:
        return f"{self.remote_dir.rstrip('/')}/{self.remote_name}"


class DanDomainImportError(RuntimeError):
    pass


def save_xml(xml_text: str, settings: Settings) -> Path:
    settings.ensure_data_dirs()
    configured_path = Path(settings.xml_file_name)
    unique_name = f"{configured_path.stem}-{uuid4().hex}{configured_path.suffix}"
    xml_path = settings.data_dir / "xml" / unique_name
    xml_path.write_text(xml_text, encoding="utf-8")
    return xml_path


def upload_product_import(xml_path: Path, image_uploads: list[FileUpload], settings: Settings) -> dict[str, object]:
    xml_upload = FileUpload(xml_path, settings.xml_ftp_dir, xml_path.name)
    import_file_param = _import_file_param(settings, xml_upload.remote_name)
    if not settings.upload_enabled:
        return {
            "dry_run": True,
            "message": "Upload is disabled. Files were generated locally only.",
            "xml_path": str(xml_path),
            "planned_image_uploads": [upload.remote_path() for upload in image_uploads],
            "planned_xml_upload": xml_upload.remote_path(),
            "planned_import_url": _build_import_url(settings, import_file_param),
        }

    settings.require_upload_config()
    with _ftp_client(settings) as ftp:
        for upload in [*image_uploads, xml_upload]:
            _upload_file(ftp, upload)

    response = requests.post(
        settings.upload_endpoint,
        params=_import_params(import_file_param),
        data={"user": settings.api_username, "password": settings.api_password},
        timeout=settings.request_timeout_seconds,
    )
    try:
        response.raise_for_status()
    except requests.HTTPError as error:
        raise DanDomainImportError(
            f"DanDomain import endpoint returned HTTP {response.status_code}."
        ) from error

    import_result = _parse_import_response(response.content)

    return {
        "dry_run": False,
        "message": "Images and XML were uploaded, and the DanDomain import completed successfully.",
        "image_uploads": [upload.remote_path() for upload in image_uploads],
        "xml_upload": xml_upload.remote_path(),
        "import_response_status": response.status_code,
        "import_response_text": response.text,
        "import_result": import_result,
    }


def _ftp_client(settings: Settings) -> FTP:
    host = _normalize_ftp_host(settings.ftp_host or "")
    client: FTP = FTP_TLS() if settings.ftp_use_tls else FTP()
    client.connect(host, settings.ftp_port, timeout=settings.request_timeout_seconds)
    client.login(settings.ftp_username or "", settings.ftp_password or "")
    client.set_pasv(True)
    if isinstance(client, FTP_TLS):
        client.prot_p()
    return client


def _upload_file(ftp: FTP, upload: FileUpload) -> None:
    _ensure_remote_dir(ftp, upload.remote_dir)
    retry_delays = (1, 2, 4, 8, 16)
    for attempt in range(len(retry_delays) + 1):
        try:
            with upload.local_path.open("rb") as file_handle:
                _store_binary(ftp, f"STOR {upload.remote_name}", file_handle)
            return
        except (error_perm, error_temp) as error:
            if not _is_file_lock_error(error) or attempt == len(retry_delays):
                raise DanDomainImportError(f"FTP could not upload {upload.remote_path()}: {error}") from error
            time.sleep(retry_delays[attempt])


def _store_binary(ftp: FTP, command: str, file_handle) -> str:
    if not isinstance(ftp, FTP_TLS):
        return ftp.storbinary(command, file_handle)

    # IIS can omit TLS close_notify on FTPS data connections. FTP_TLS.storbinary()
    # waits in SSLSocket.unwrap() until IIS times out the data channel. Closing the
    # completed data socket directly lets IIS return its normal 226 response.
    ftp.voidcmd("TYPE I")
    data_socket = ftp.transfercmd(command)
    try:
        while block := file_handle.read(64 * 1024):
            data_socket.sendall(block)
    finally:
        data_socket.close()
    return ftp.voidresp()


def _is_file_lock_error(error: Error) -> bool:
    message = str(error).lower()
    return message.startswith(("450 ", "451 ", "550 ")) and any(
        phrase in message
        for phrase in ("being used by another process", "used by another process", "file is locked")
    )


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


def _import_file_param(settings: Settings, xml_file_name: str) -> str:
    configured_path = PurePosixPath(settings.xml_import_file_param)
    return str(configured_path.with_name(xml_file_name))


def _import_params(import_file_param: str) -> dict[str, str]:
    return {
        "file": import_file_param,
        "response": "1",
        # This service creates products. Per DanDomain, updateonly is enabled only by the value 1.
        "updateonly": "0",
    }


def _parse_import_response(content: bytes) -> dict[str, object]:
    try:
        root = ET.fromstring(content)
    except ET.ParseError as error:
        raise DanDomainImportError("DanDomain returned an invalid XML import response.") from error

    if root.tag != "IMPORT_RESULT":
        raise DanDomainImportError(
            f"DanDomain returned an unexpected import response root element: {root.tag}."
        )

    status = (root.findtext("STATUS") or "").strip()
    errors = [
        {
            "title": (error.findtext("TITLE") or "").strip(),
            "message": (error.findtext("MESSAGE") or "").strip(),
        }
        for error in root.findall("./ERRORS/ERROR")
    ]
    result: dict[str, object] = {
        "type": (root.findtext("TYPE") or "").strip(),
        "status": status,
        "time": (root.findtext("TIME") or "").strip(),
        "count": _parse_result_count(root, "COUNT"),
        "completed": _parse_result_count(root, "COMPLETED"),
        "failed": _parse_result_count(root, "FAILED"),
        "created": _parse_result_count(root, "CREATED"),
        "modified": _parse_result_count(root, "MODIFIED"),
        "errors": errors,
    }

    if status != "1":
        details = "; ".join(
            ": ".join(part for part in (error["title"], error["message"]) if part)
            for error in errors
        )
        message = "DanDomain reported that the product import failed"
        if details:
            message = f"{message}: {details}"
        raise DanDomainImportError(message)

    return result


def _parse_result_count(root: ET.Element, element_name: str) -> int:
    value = (root.findtext(element_name) or "0").strip()
    try:
        return int(value)
    except ValueError as error:
        raise DanDomainImportError(
            f"DanDomain returned a non-numeric {element_name} value: {value}."
        ) from error


def _build_import_url(settings: Settings, import_file_param: str | None = None) -> str | None:
    if not settings.upload_endpoint:
        return None
    parsed = urlparse(settings.upload_endpoint)
    query = [
        *parse_qsl(parsed.query, keep_blank_values=True),
        *_import_params(import_file_param or settings.xml_import_file_param).items(),
    ]
    return urlunparse(parsed._replace(query=urlencode(query)))
