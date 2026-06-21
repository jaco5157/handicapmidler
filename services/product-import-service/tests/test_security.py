import base64
import importlib
import sys

import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.security import hash_password, verify_basic_auth_header, verify_password


def test_password_hash_verifies_password():
    password_hash = hash_password("correct horse", iterations=1_000)

    assert verify_password("correct horse", password_hash)
    assert not verify_password("wrong horse", password_hash)


def test_basic_auth_header_verifies_expected_credentials():
    password_hash = hash_password("secret", iterations=1_000)
    encoded_credentials = base64.b64encode(b"admin:secret").decode("ascii")

    assert verify_basic_auth_header(f"Basic {encoded_credentials}", "admin", password_hash)
    assert not verify_basic_auth_header(f"Basic {encoded_credentials}", "other", password_hash)
    assert not verify_basic_auth_header("Bearer token", "admin", password_hash)


def test_upload_enabled_requires_auth_config():
    settings = Settings(
        upload_enabled=True,
        ftp_host="ftp.example.com",
        ftp_username="ftp-user",
        ftp_password="ftp-pass",
        api_upload_endpoint="https://example.com/import",
        api_username="api-user",
        api_password="api-pass",
    )

    with pytest.raises(ValueError, match="Authentication is required"):
        settings.require_runtime_config()


def test_auth_middleware_protects_ui_docs_static_and_api(monkeypatch, tmp_path):
    main = _load_main_with_auth(monkeypatch, tmp_path)
    client = TestClient(main.app)

    assert client.get("/health").status_code == 200
    for path in ["/", "/docs", "/openapi.json", "/static/product_form.js"]:
        response = client.get(path)
        assert response.status_code == 401
        assert response.headers["www-authenticate"].startswith("Basic")

    assert client.post("/api/preview", json={}).status_code == 401
    assert client.get("/", auth=("admin", "secret")).status_code == 200
    assert client.get("/static/product_form.js", auth=("admin", "secret")).status_code == 200


def _load_main_with_auth(monkeypatch, tmp_path):
    for key in [
        "UPLOAD_ENABLED",
        "AUTH_ENABLED",
        "AUTH_USERNAME",
        "AUTH_PASSWORD_HASH",
        "DATA_DIR",
        "FTP_HOST",
        "FTP_USERNAME",
        "FTP_PASSWORD",
        "API_UPLOAD_ENDPOINT",
        "API_USERNAME",
        "API_PASSWORD",
    ]:
        monkeypatch.delenv(key, raising=False)

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("AUTH_ENABLED", "true")
    monkeypatch.setenv("AUTH_USERNAME", "admin")
    monkeypatch.setenv("AUTH_PASSWORD_HASH", hash_password("secret", iterations=1_000))

    get_settings.cache_clear()
    sys.modules.pop("app.main", None)
    return importlib.import_module("app.main")
