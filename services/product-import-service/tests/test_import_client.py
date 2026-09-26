from pathlib import Path

import pytest
import requests

from app.config import Settings
from app.services import import_client
from app.services.import_client import DanDomainImportError, FileUpload, upload_product_import


SUCCESS_RESPONSE = b"""\
<?xml version="1.0" encoding="iso-8859-1"?>
<IMPORT_RESULT>
  <TYPE>PRODUCTS</TYPE>
  <STATUS>1</STATUS>
  <TIME>0:1</TIME>
  <COUNT>1</COUNT>
  <COMPLETED>1</COMPLETED>
  <FAILED>0</FAILED>
  <CREATED>1</CREATED>
  <MODIFIED>0</MODIFIED>
</IMPORT_RESULT>
"""


class FakeResponse:
    def __init__(self, content: bytes, status_code: int = 200):
        self.content = content
        self.status_code = status_code
        self.text = content.decode("iso-8859-1")

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")


class FakeFTP:
    def __init__(self):
        self.uploads: list[tuple[str, bytes]] = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def cwd(self, path: str):
        return None

    def mkd(self, path: str):
        return None

    def storbinary(self, command: str, file_handle):
        self.uploads.append((command, file_handle.read()))


def make_settings(**overrides) -> Settings:
    values = {
        "upload_enabled": True,
        "ftp_host": "ftp.example.com",
        "ftp_username": "ftp-user",
        "ftp_password": "ftp-pass",
        "xml_ftp_dir": "/images/ImportExport/Products/Updated/",
        "xml_import_file_param": "Products/Updated/document.xml",
        "upload_endpoint": "https://shop.example.com/admin/modules/importexport/import_v6.aspx",
        "api_username": "api-user",
        "api_password": "api-pass",
        "request_timeout_seconds": 12,
    }
    values.update(overrides)
    return Settings(**values)


def test_upload_product_import_matches_dandomain_contract(monkeypatch, tmp_path: Path):
    xml_path = tmp_path / "document.xml"
    xml_path.write_bytes(b"<PRODUCT_EXPORT type=\"PRODUCTS\"/>")
    image_path = tmp_path / "product.jpg"
    image_path.write_bytes(b"image")
    fake_ftp = FakeFTP()
    captured_request = {}

    monkeypatch.setattr(import_client, "_ftp_client", lambda settings: fake_ftp)

    def fake_post(url, *, params, data, timeout):
        captured_request.update(url=url, params=params, data=data, timeout=timeout)
        return FakeResponse(SUCCESS_RESPONSE)

    monkeypatch.setattr(import_client.requests, "post", fake_post)

    result = upload_product_import(
        xml_path,
        [FileUpload(image_path, "/images/products/", "product.jpg")],
        make_settings(),
    )

    assert fake_ftp.uploads == [
        ("STOR product.jpg", b"image"),
        ("STOR document.xml", b'<PRODUCT_EXPORT type="PRODUCTS"/>'),
    ]
    assert captured_request == {
        "url": "https://shop.example.com/admin/modules/importexport/import_v6.aspx",
        "params": {
            "file": "Products/Updated/document.xml",
            "response": "1",
            "updateonly": "0",
        },
        "data": {"user": "api-user", "password": "api-pass"},
        "timeout": 12,
    }
    assert result["import_result"] == {
        "type": "PRODUCTS",
        "status": "1",
        "time": "0:1",
        "count": 1,
        "completed": 1,
        "failed": 0,
        "created": 1,
        "modified": 0,
        "errors": [],
    }


def test_upload_product_import_rejects_dandomain_failure(monkeypatch, tmp_path: Path):
    xml_path = tmp_path / "document.xml"
    xml_path.write_text("<PRODUCT_EXPORT/>", encoding="utf-8")
    failure_response = b"""\
<IMPORT_RESULT>
  <STATUS>0</STATUS><COUNT>0</COUNT><COMPLETED>0</COMPLETED><FAILED>0</FAILED>
  <CREATED>0</CREATED><MODIFIED>0</MODIFIED>
  <ERRORS><ERROR><TITLE>Import file</TITLE><MESSAGE>File not found</MESSAGE></ERROR></ERRORS>
</IMPORT_RESULT>
"""

    monkeypatch.setattr(import_client, "_ftp_client", lambda settings: FakeFTP())
    monkeypatch.setattr(
        import_client.requests,
        "post",
        lambda *args, **kwargs: FakeResponse(failure_response),
    )

    with pytest.raises(
        DanDomainImportError,
        match="DanDomain reported that the product import failed: Import file: File not found",
    ):
        upload_product_import(xml_path, [], make_settings())


def test_upload_product_import_rejects_non_xml_response(monkeypatch, tmp_path: Path):
    xml_path = tmp_path / "document.xml"
    xml_path.write_text("<PRODUCT_EXPORT/>", encoding="utf-8")

    monkeypatch.setattr(import_client, "_ftp_client", lambda settings: FakeFTP())
    monkeypatch.setattr(
        import_client.requests,
        "post",
        lambda *args, **kwargs: FakeResponse(b"<html>Login required</html>"),
    )

    with pytest.raises(DanDomainImportError, match="unexpected import response root element"):
        upload_product_import(xml_path, [], make_settings())


def test_dry_run_builds_encoded_import_url(tmp_path: Path):
    xml_path = tmp_path / "document.xml"
    settings = make_settings(
        upload_enabled=False,
        upload_endpoint="https://shop.example.com/import?existing=yes",
        xml_import_file_param="Products/New products/document.xml",
    )

    result = upload_product_import(xml_path, [], settings)

    assert result["planned_import_url"] == (
        "https://shop.example.com/import?existing=yes&file=Products%2FNew+products%2Fdocument.xml"
        "&response=1&updateonly=0"
    )