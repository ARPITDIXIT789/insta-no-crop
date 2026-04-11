# Insta No Crop

Instagram-ready square exports without cropping. The app keeps your full image, generates an aesthetic background, and can auto-tune settings using an AI API.

## Highlights
- No-crop output with blur, smart AI-style blur, or solid color background.
- Face enhancement for sharper subjects.
- 1080 / 2160 / 3840 square export options.
- AI Auto Tune endpoint to suggest mode, blur, color, quality, and face enhancement.
- Multi-stage Docker backend image for faster rebuilds and smaller runtime image.

## Run with Docker
Use whichever command exists on your server:

```bash
# Docker Compose plugin
docker compose up -d --build

# Legacy binary
docker-compose up -d --build
```

Frontend: `http://<server-ip>/`  
Backend health: `http://<server-ip>:8000/health`

## API Endpoints
### 1) Convert image
`POST /convert` (multipart/form-data)
- `file` (required): image
- `blur`: int (3-80)
- `mode`: `blur` | `ai` | `color`
- `bgcolor`: `#RRGGBB` (used in `color` mode)
- `quality`: `normal` | `hd` | `ultra`
- `enhance_face`: `true` / `false`

Returns PNG stream.

### 2) AI setting recommendation
`POST /ai/suggest-settings` (multipart/form-data)
- `file` (required): image
- `goal` (optional): text like `clean look`, `dramatic`, `bright feed`

Returns:
- `source`: `ai` or `fallback`
- `settings`: mode, blur, quality, bgcolor, enhance_face, reason
- `signals`: image metadata used for recommendation

## AI API Configuration
Set env vars on backend service:

- `OPENAI_API_KEY`: required for live AI recommendations.
- `OPENAI_MODEL`: optional, default `gpt-4.1-mini`.
- `OPENAI_API_URL`: optional, default `https://api.openai.com/v1/chat/completions`.

If `OPENAI_API_KEY` is not set, app uses local heuristic fallback.

## Docker Build Optimizations Included
- Multi-stage backend Dockerfile (builder + slim runtime).
- Dependency layer cached separately from app code.
- Runtime image excludes compile toolchain.
- Backend-level `.dockerignore` for smaller build context.

## Ops Notes
- Keep public inbound ports to `80`, `443`, and restricted `22`.
- Avoid exposing `8000` publicly in production.
- If using old `docker-compose` and seeing `ContainerConfig` errors, run:

```bash
docker-compose down
docker rm -f $(docker ps -aq --filter "name=insta-no-crop")
docker-compose up -d --build
```
