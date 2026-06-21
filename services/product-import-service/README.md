# Product Import Service

FastAPI service for creating webshop product import XML from a supplier product page. The first supplier implementation targets Mobilex product pages.

## What It Does

1. Scrapes title, HMI number, product number, and images from a Mobilex product URL.
2. Lets the user edit product fields, SEO fields, image filenames/alt text, descriptions, and specs.
3. Generates a webshop product XML file matching the existing `export.xml` structure.
4. Downloads renamed images and creates the four webshop variants used by `compress.sh`:
   - `name-p.jpg`
   - `name.jpg`
   - `name-r.jpg`
   - `name-t.jpg`
5. Uploads image variants to `/images/products/`, uploads XML to the import folder, and calls the import endpoint with `updateonly=0` when uploads are enabled.

By default the service runs in dry-run mode, so it generates files locally without FTP or import API calls.

## Local Setup

```bash
cd services/product-import-service
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000`.

## Docker

```bash
cd services/product-import-service
cp .env.example .env
docker compose up --build
```

Open `http://127.0.0.1:8000`.

Generated files are stored in `services/product-import-service/data` when using Docker Compose.

For Raspberry Pi/DietPi deployment, see [DEPLOY_DIETPI.md](DEPLOY_DIETPI.md).

## Access and Authentication

Do not expose this service directly to the public internet. It can download images, upload files by FTP, and trigger webshop imports.

The recommended production setup is:

1. Bind Docker to localhost only.
2. Use Tailscale Serve for private tailnet HTTPS access.
3. Enable app authentication with a strong password.

The Compose files bind port 8000 to `127.0.0.1`, so remote access should go through Tailscale Serve or another private reverse proxy running on the same host.

Generate an app password hash from this directory:

```bash
python3 -c 'from app.security import hash_password; import getpass; print(hash_password(getpass.getpass("App password: ")))'
```

Then set:

```env
AUTH_ENABLED=true
AUTH_USERNAME=admin
AUTH_PASSWORD_HASH=pbkdf2_sha256$...
```

When `UPLOAD_ENABLED=true`, the service refuses to start unless authentication is enabled and configured.

## Upload Configuration

Set these in `.env` before enabling upload:

```env
UPLOAD_ENABLED=true
FTP_HOST=ftp.example.com
FTP_USERNAME=...
FTP_PASSWORD=...
IMAGE_FTP_DIR=/images/products/
IMAGE_PUBLIC_URL_PREFIX=/images/products/
XML_FTP_DIR=/images/ImportExport/Products/Updated/
XML_IMPORT_FILE_PARAM=Products/Updated/document.xml
API_UPLOAD_ENDPOINT=https://example.com/import
API_USERNAME=...
API_PASSWORD=...
```

The import call is made as:

```text
POST API_UPLOAD_ENDPOINT?file=Products/Updated/document.xml&response=1&updateonly=0
```

with form fields `user` and `password`.

## Image Download Safety

Uploaded product drafts contain image URLs. The service only downloads `http` and `https` image URLs that resolve to public internet addresses, rejects unsupported content types, and limits image downloads with `IMAGE_DOWNLOAD_MAX_BYTES`.

## Image Compression

The default `COMPRESSION_BACKEND=pillow` mirrors the output naming and long-edge sizing from `compress.sh` without requiring ImageMagick or Caesium in local development.

Set `COMPRESSION_BACKEND=external` to run an external toolchain equivalent to `compress.sh`. In that mode, `MAGICK_COMMAND` and `CAESIUM_COMMAND` must be available in the container or host environment.

## Tests

```bash
cd services/product-import-service
pytest
```

The test suite covers filename suggestions, price validation, specs table generation, XML mapping, optional specs omission, image variant planning, authentication, and image download safety.
