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

## 3. Install Tailscale

Install Tailscale on the Pi and sign it into your tailnet:

```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```

Also install Tailscale on the computers that should use the import service.

If a coworker needs access, invite them to Tailscale and restrict them with ACLs so they can reach only this service, not SSH or other apps on the Pi. If you use Tailscale Serve, users connect to the private HTTPS endpoint, so the policy should allow port `443` on the tagged Pi:

```json
{
	"tagOwners": {
		"tag:product-import": ["autogroup:admin"]
	},
	"groups": {
		"group:product-import-admins": ["you@example.com", "coworker@example.com"]
	},
	"acls": [
		{
			"action": "accept",
			"src": ["group:product-import-admins"],
			"dst": ["tag:product-import:443"]
		}
	]
}
```

After adding the tag policy, advertise the tag from the Pi:

```bash
sudo tailscale up --advertise-tags=tag:product-import
```

If you skip Tailscale Serve and access a direct tailnet port instead, restrict that exact port, for example `tag:product-import:8000`.

## 4. Put the service on the Pi

Clone or copy this repository to the Pi. Example with Git:

```bash
mkdir -p ~/apps
cd ~/apps
git clone <your-repo-url> handicapmidler
cd handicapmidler/services/product-import
```

If the repository is private, configure SSH keys on the Pi first, or copy the `services/product-import` folder with `rsync`.

## 5. Create the environment file

```bash
cp .env.example .env
nano .env
```

Generate a password hash for the app login:

```bash
python3 -c 'from app.security import hash_password; import getpass; print(hash_password(getpass.getpass("App password: ")))'
```

Set these values in `.env`:

```env
AUTH_ENABLED=true
AUTH_USERNAME=admin
AUTH_PASSWORD_HASH=pbkdf2_sha256$...
DATA_DIR=/app/data
COMPRESSION_BACKEND=pillow
CHROME_BIN=/usr/bin/chromium
SELENIUM_DRIVER_PATH=/usr/bin/chromedriver
```

For a first dry run, keep:

```env
UPLOAD_ENABLED=false
```

When you are ready to upload products for real, set:

```env
UPLOAD_ENABLED=true
FTP_HOST=...
FTP_USERNAME=...
FTP_PASSWORD=...
UPLOAD_ENDPOINT=...
API_USERNAME=...
API_PASSWORD=...
CATEGORY_EXPORT_ENDPOINT=https://www.handicapmidler.dk/admin/modules/export/RunExport?langid=26&exportid=5
```

Real uploads require `AUTH_ENABLED=true`, `AUTH_USERNAME`, and `AUTH_PASSWORD_HASH`. The service refuses to start with `UPLOAD_ENABLED=true` if authentication is missing.

Keep `.env` only on the server and do not commit it.

## 6. Build and start

From `services/product-import` on the Pi:

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

After deployment, open the service and use **Fetch latest** beside the product category field. This saves the current category export to the persistent `data/categories.xml` file. Repeat this after each deployment or whenever categories change; the last successful file remains active until it is fetched again.

The first build can take several minutes on a Raspberry Pi because Python packages and image libraries may need to compile.

Check that it started:

```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f --tail=100
```

The production Compose file binds the app to localhost only:

```text
127.0.0.1:8000
```

This means it is not reachable directly from the LAN or public internet.

## 7. Expose it privately with Tailscale Serve

Enable private tailnet HTTPS for the service:

```bash
sudo tailscale serve 8000
```

Tailscale prints a private URL like:

```text
https://product-import-pi.your-tailnet.ts.net
```

Use that URL from your own Tailscale device. After confirming it works, configure Serve in the background if your Tailscale client supports it:

```bash
sudo tailscale serve --bg 8000
sudo tailscale serve status
```

Use Tailscale Serve, not Tailscale Funnel. Serve is private to your tailnet; Funnel is public internet exposure.

Open the service from an allowed Tailscale device and log in with `AUTH_USERNAME` and the password used to generate `AUTH_PASSWORD_HASH`.

The generated XML and image files are persisted in:

```text
services/product-import/data
```

## 8. Update the deployment

```bash
cd ~/apps/handicapmidler/services/product-import
git pull
docker compose -f docker-compose.prod.yml up -d --build
docker image prune -f
```

### Existing-installation folder migration

Do this once, **before pulling the directory rename**, on each existing installation. Git does not relocate ignored `.env` or `data/`. Stop the old stack before changing its bind mount. Both new Compose files pin the default project name to `product-import-service`; retain any custom project name with `COMPOSE_PROJECT_NAME` or the same `-p` flag on every command.

From the repository root, with the old service still present:

```bash
cd ~/apps/handicapmidler
old=services/product-import-service
new=services/product-import
export COMPOSE_PROJECT_NAME="$(docker compose -f "$old/docker-compose.prod.yml" config --format json | python3 -c 'import json,sys; print(json.load(sys.stdin)["name"])')"
backup_dir="$HOME/backups/product-import-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$backup_dir"
chmod 700 "$backup_dir"
tar -czf "$backup_dir/state.tgz" -C "$old" .env data
chmod 600 "$backup_dir/state.tgz"
docker compose -f "$old/docker-compose.prod.yml" down
git pull --ff-only
test -d "$new"
test ! -e "$new/.env" && test ! -e "$new/data"
cp -p "$old/.env" "$new/.env"
cp -a "$old/data" "$new/data"
cd "$new"
docker compose -f docker-compose.prod.yml up -d --build
curl --fail http://127.0.0.1:8000/health
docker compose -f docker-compose.prod.yml ps
```

Run each command only after the preceding command succeeds. Do not overwrite a nonempty destination; reconcile it with the backup first. If `PRODUCT_IMPORT_ENV_FILE` points outside the service, back up that file separately and preserve its absolute path instead of copying a local `.env`. For development installations, use `docker-compose.yml` and port `8765` throughout this procedure.

Verify authentication, existing categories/generated files, the UI and a dry-run XML/image preview before enabling uploads. Keep the backup outside the checkout. For rollback, stop the renamed stack, restore the previous revision and state into its original directory, then start it using the same project identity. Never run both stacks against the same port or data.

For non-container installations, recreate `.venv` at the new path and reinstall `requirements.txt`; virtual environments contain absolute paths and cannot be moved reliably.

## 9. Back up generated files

The important local state is the `data` folder and the server-only `.env` file:

```bash
tar -czf product-import-service-backup.tgz .env data
```

Store that archive somewhere other than the Pi.

## 10. Remote access

Do not expose port `8000` directly to the public internet. The app can contain FTP/API credentials and can trigger product imports.

Recommended setup:

- Use Tailscale Serve and access the private `https://<pi-name>.<tailnet>.ts.net` URL.
- Keep Docker bound to `127.0.0.1:8000`.
- Keep app authentication enabled.
- Use ACLs to restrict coworkers to this app/port only.

Avoid:

- Router port forwarding to `8000`.
- Public DNS records pointing at this app.
- Tailscale Funnel for this service.

## Useful commands

```bash
docker compose -f docker-compose.prod.yml restart
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml logs -f --tail=100
docker compose -f docker-compose.prod.yml exec product-import-service python -m pytest
```