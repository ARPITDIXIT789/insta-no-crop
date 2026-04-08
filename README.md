# 📸 Insta No Crop

Make any photo Instagram-ready without cropping. Blur or color the background, keep faces sharp (Remini-style), and export up to 4K — all on a CPU-friendly FastAPI backend.

## Highlights
- Classic blur, AI smart gradient blur, or solid color backgrounds.
- Face-only enhancement so subjects stay crisp.
- 1080p / 2K / 4K square exports.
- PWA with offline caching and drag-and-drop UI.
- Dockerized stack (Nginx + FastAPI) with health checks.

## Quick Start (Ubuntu / Docker)
```bash
# from repo root
docker compose up -d --build
```
- Nginx: ports 80/443 serve the frontend and proxy `/convert` to the backend.
- Backend health: `http://localhost:8000/health`
- Logs: `make logs`

## API
`POST /convert` (multipart/form-data)
- `file` (required): image
- `blur` (int 3-80): blur radius for classic mode
- `mode`: `blur` | `ai` | `color`
- `bgcolor`: hex (`#000000`) when `mode=color`
- `quality`: `normal` (1080) | `hd` (2160) | `ultra` (3840)
- `enhance_face`: `true` / `false`

Response: PNG image stream.

## Frontend
- Drag & drop or click to upload, live status, reset, copy preview URL.
- Smart default quality based on source resolution.
- PWA service worker caches core assets for offline use.

## Dev Tasks
- `make up` / `make down` to start/stop
- `make rebuild-backend` to rebuild only API container
- `make restart-backend` to hot-restart backend
- `make certbot-renew` to renew certificates (when mapped)

## Deployment Notes
- TLS served by Nginx; HSTS enabled.
- Backend runs 2 uvicorn workers; healthcheck wired for Compose.
- Limit uploads to 15 MB; Nginx `client_max_body_size` set to 20M.
