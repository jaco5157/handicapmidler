from pathlib import Path
from ftplib import FTP_TLS, error_perm

import pytest
import requests

from app.config import Settings
from app.services import import_client
from app.services.import_client import DanDomainImportError, FileUpload, save_xml, upload_product_import


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


class FakeDataSocket:
    def __init__(self):
        self.content = bytearray()
        self.closed = False

    def sendall(self, content: bytes):
        self.content.extend(content)

    def close(self):
        self.closed = True


class FakeFTPTLS(FTP_TLS):
    def __init__(self):
        self.commands: list[str] = []
        self.data_socket = FakeDataSocket()
        self.storbinary_called = False

    def cwd(self, path: str):
        return None

    def mkd(self, path: str):
        return None

    def voidcmd(self, command: str):
        self.commands.append(command)
        return "200 Type set to I."

    def transfercmd(self, command: str, rest=None):
        self.commands.append(command)
        return self.data_socket

    def voidresp(self):
        return "226 Transfer complete."

    def storbinary(self, command: str, file_handle, blocksize=8192, callback=None, rest=None):
        self.storbinary_called = True
        raise AssertionError("FTP_TLS.storbinary must not be used with this IIS server")


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
    xml_path = tmp_path / "document-request-id.xml"
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
        ("STOR document-request-id.xml", b'<PRODUCT_EXPORT type="PRODUCTS"/>'),
    ]
    assert captured_request == {
        "url": "https://shop.example.com/admin/modules/importexport/import_v6.aspx",
        "params": {
            "file": "Products/Updated/document-request-id.xml",
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
        "response_verified": True,
    }
    assert result["xml_upload"] == "/images/ImportExport/Products/Updated/document-request-id.xml"


def test_save_xml_uses_a_unique_file_for_each_request(tmp_path: Path):
    settings = make_settings(data_dir=tmp_path, xml_file_name="document.xml")

    first_path = save_xml("<FIRST/>", settings)
    second_path = save_xml("<SECOND/>", settings)

    assert first_path.parent == tmp_path / "xml"
    assert first_path.name.startswith("document-")
    assert first_path.suffix == ".xml"
    assert second_path.name.startswith("document-")
    assert first_path != second_path
    assert first_path.read_text(encoding="utf-8") == "<FIRST/>"
    assert second_path.read_text(encoding="utf-8") == "<SECOND/>"


def test_upload_file_retries_windows_file_lock_errors(monkeypatch, tmp_path: Path):
    upload_path = tmp_path / "document.xml"
    upload_path.write_bytes(b"xml")
    ftp = FakeFTP()
    attempts = 0
    delays = []

    def locked_then_success(command, file_handle):
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise error_perm("550 The process cannot access the file because it is being used by another process.")
        ftp.uploads.append((command, file_handle.read()))

    ftp.storbinary = locked_then_success
    monkeypatch.setattr(import_client.time, "sleep", delays.append)

    import_client._upload_file(ftp, FileUpload(upload_path, "/imports/", "document.xml"))

    assert attempts == 3
    assert delays == [1, 2]
    assert ftp.uploads == [("STOR document.xml", b"xml")]


def test_upload_file_closes_ftps_data_socket_without_unwrap(tmp_path: Path):
    upload_path = tmp_path / "product.jpg"
    upload_path.write_bytes(b"image-bytes")
    ftp = FakeFTPTLS()

    import_client._upload_file(ftp, FileUpload(upload_path, "/images/products/", "product.jpg"))

    assert ftp.commands == ["TYPE I", "STOR product.jpg"]
    assert bytes(ftp.data_socket.content) == b"image-bytes"
    assert ftp.data_socket.closed
    assert not ftp.storbinary_called


def test_upload_file_does_not_retry_unrelated_ftp_errors(monkeypatch, tmp_path: Path):
    upload_path = tmp_path / "document.xml"
    upload_path.write_bytes(b"xml")
    ftp = FakeFTP()
    attempts = 0

    def permission_denied(command, file_handle):
        nonlocal attempts
        attempts += 1
        raise error_perm("550 Permission denied")

    ftp.storbinary = permission_denied
    monkeypatch.setattr(import_client.time, "sleep", lambda delay: pytest.fail("must not retry"))

    with pytest.raises(DanDomainImportError, match=r"/imports/document\.xml: 550 Permission denied"):
        import_client._upload_file(ftp, FileUpload(upload_path, "/imports/", "document.xml"))

    assert attempts == 1


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


def test_upload_product_import_accepts_empty_success_response(monkeypatch, tmp_path: Path):
    xml_path = tmp_path / "document.xml"
    xml_path.write_text("<PRODUCT_EXPORT/>", encoding="utf-8")

    monkeypatch.setattr(import_client, "_ftp_client", lambda settings: FakeFTP())
    monkeypatch.setattr(
        import_client.requests,
        "post",
        lambda *args, **kwargs: FakeResponse(b"\r\n\t"),
    )

    result = upload_product_import(xml_path, [], make_settings())

    assert result["message"] == (
        "Images and XML were uploaded, and DanDomain accepted the import request "
        "but returned no result details."
    )
    assert result["import_result"]["status"] == "accepted"
    assert result["import_result"]["response_verified"] is False


def test_upload_product_import_extracts_xml_result_from_response_preamble(monkeypatch, tmp_path: Path):
    xml_path = tmp_path / "document.xml"
    xml_path.write_text("<PRODUCT_EXPORT/>", encoding="utf-8")
    response_with_preamble = b"DanDomain import response:\r\n" + SUCCESS_RESPONSE

    monkeypatch.setattr(import_client, "_ftp_client", lambda settings: FakeFTP())
    monkeypatch.setattr(
        import_client.requests,
        "post",
        lambda *args, **kwargs: FakeResponse(response_with_preamble),
    )

    result = upload_product_import(xml_path, [], make_settings())

    assert result["import_result"]["status"] == "1"
    assert result["import_result"]["response_verified"] is True


def test_dry_run_builds_encoded_import_url(tmp_path: Path):
    xml_path = tmp_path / "document-request-id.xml"
    settings = make_settings(
        upload_enabled=False,
        upload_endpoint="https://shop.example.com/import?existing=yes",
        xml_import_file_param="Products/New products/document.xml",
    )

    result = upload_product_import(xml_path, [], settings)

    assert result["planned_import_url"] == (
        "https://shop.example.com/import?existing=yes&file=Products%2FNew+products%2Fdocument-request-id.xml"
        "&response=1&updateonly=0"
    )