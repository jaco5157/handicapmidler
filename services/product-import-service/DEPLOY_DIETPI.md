# Deploying to DietPi on Raspberry Pi

This service is easiest to run on the Raspberry Pi with Docker Compose. The Pi should use a 64-bit DietPi image so Docker can pull/build ARM64 images for Python, Chromium, and Pillow.

## 1. Check the Pi architecture

SSH into the Pi and run:

```bash
dpkg --print-architecture
```

Expected output for the recommended setup is:

```text
arm64
```

If it prints `armhf`, install the 64-bit DietPi image before deploying this service. Chromium/Selenium container support is much more reliable on ARM64.

## 2. Install Docker and Compose

DietPi can install Docker from its software menu:

```bash
sudo dietpi-software
```

Select Docker and Docker Compose, then install. After installation, allow your user to run Docker commands:

```bash
sudo usermod -aG docker "$USER"
exit
```

Log back in, then verify:

```bash
docker --version
docker compose version
```

## 3. Put the service on the Pi

Clone or copy this repository to the Pi. Example with Git:

```bash
mkdir -p ~/apps
cd ~/apps
git clone <your-repo-url> handicapmidler
cd handicapmidler/services/product-import-service
```

If the repository is private, configure SSH keys on the Pi first, or copy the `services/product-import-service` folder with `rsync`.

## 4. Create the environment file

```bash
cp .env.example .env
nano .env
```

For a first dry run, keep:

```env
UPLOAD_ENABLED=false
DATA_DIR=/app/data
COMPRESSION_BACKEND=pillow
CHROME_BIN=/usr/bin/chromium
SELENIUM_DRIVER_PATH=/usr/bin/chromedriver
```

When you are ready to upload products for real, set:

```env
UPLOAD_ENABLED=true
FTP_HOST=...
FTP_USERNAME=...
FTP_PASSWORD=...
API_UPLOAD_ENDPOINT=...
API_USERNAME=...
API_PASSWORD=...
```

Keep `.env` only on the server and do not commit it.

## 5. Build and start

From `services/product-import-service` on the Pi:

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

The first build can take several minutes on a Raspberry Pi because Python packages and image libraries may need to compile.

Check that it started:

```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f --tail=100
```

Open the service from your local network:

```text
http://<pi-ip-address>:8000
```

The generated XML and image files are persisted in:

```text
services/product-import-service/data
```

## 6. Update the deployment

```bash
cd ~/apps/handicapmidler/services/product-import-service
git pull
docker compose -f docker-compose.prod.yml up -d --build
docker image prune -f
```

## 7. Back up generated files

The important local state is the `data` folder and the server-only `.env` file:

```bash
tar -czf product-import-service-backup.tgz .env data
```

Store that archive somewhere other than the Pi.

## 8. Remote access

Do not expose port `8000` directly to the public internet. The app can contain FTP/API credentials and can trigger product imports.

Recommended options:

- Use Tailscale/WireGuard and access `http://<pi-vpn-ip>:8000`.
- Put Caddy or Nginx in front of it with HTTPS and authentication.
- Keep it LAN-only and access it from home.

## Useful commands

```bash
docker compose -f docker-compose.prod.yml restart
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml logs -f --tail=100
docker compose -f docker-compose.prod.yml exec product-import-service python -m pytest
```