from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Product Import Service"
    upload_enabled: bool = False
    data_dir: Path = Path("data")

    ftp_host: str | None = None
    ftp_port: int = 21
    ftp_username: str | None = None
    ftp_password: str | None = None
    ftp_use_tls: bool = False

    image_ftp_dir: str = "/images/products/"
    image_public_url_prefix: str = "/images/products/"
    xml_ftp_dir: str = "/images/ImportExport/Products/Updated/"
    xml_file_name: str = "document.xml"
    xml_import_file_param: str = "Products/Updated/document.xml"

    api_upload_endpoint: str | None = None
    api_username: str | None = None
    api_password: str | None = None

    language_id: int = 26
    currency_code: str = "DKK"
    price_b2b_id: int = 0

    selenium_timeout_seconds: int = 15
    chromium_binary: str | None = Field(default=None, validation_alias="CHROME_BIN")
    selenium_driver_path: str | None = Field(default=None, validation_alias="SELENIUM_DRIVER_PATH")

    compression_backend: str = "pillow"
    magick_command: str = "magick"
    caesium_command: str = "caesiumclt"
    jpeg_quality: int = 88

    request_timeout_seconds: int = 30

    def ensure_data_dirs(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        (self.data_dir / "originals").mkdir(parents=True, exist_ok=True)
        (self.data_dir / "compressed").mkdir(parents=True, exist_ok=True)
        (self.data_dir / "xml").mkdir(parents=True, exist_ok=True)

    def require_upload_config(self) -> None:
        missing = []
        for name in ["ftp_host", "ftp_username", "ftp_password", "api_upload_endpoint", "api_username", "api_password"]:
            if not getattr(self, name):
                missing.append(name.upper())

        if missing:
            raise ValueError(f"Upload is enabled, but these settings are missing: {', '.join(missing)}")


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_data_dirs()
    return settings
