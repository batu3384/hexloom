# Hexloom

Hexloom is a professional FastAPI workspace for encoding, decoding, validating, and inspecting text transformations from a single interface.

It combines a polished web UI, JSON API endpoints, batch processing, health diagnostics, and production-ready deployment scaffolding for teams that work with payloads, signals, and encoded content.

## Live links

- Live app: [https://hexloom.onrender.com](https://hexloom.onrender.com)
- API docs: [https://hexloom.onrender.com/docs](https://hexloom.onrender.com/docs)
- Health check: [https://hexloom.onrender.com/health/transformations](https://hexloom.onrender.com/health/transformations)

![Hexloom overview](docs/assets/hexloom-overview.png)

## Why Hexloom

- Unified transformation workspace for Base64, Morse, Binary, Hex, JSON payloads, URL encoding, and more
- Single-record and batch processing flows from the same interface
- FastAPI backend with automatic OpenAPI and Swagger docs
- Built-in self-check endpoint to verify every supported transformation
- Rich terminal logging and tqdm-backed batch progress
- Static frontend assets with no Tailwind CDN dependency
- Ready for GitHub, Docker, and Render deployment

## Supported methods

- `base64`
- `base64_double`
- `bytearray`
- `html_entities`
- `math_expr`
- `rot13`
- `url_encode`
- `json_payload`
- `morse`
- `hex`
- `binary`

## Product walkthrough

### Main workspace

The main screen gives operators one place to choose a method, switch between `Text to Format` and `Format to Text`, run single or batch jobs, inspect the active workflow, and copy or reuse results.

![Hexloom workspace](docs/assets/hexloom-live-workspace.png)

### Diagnostics

Hexloom includes a built-in system check at `GET /health/transformations`. It runs encode, decode, and batch simulation coverage across the supported methods and returns an application health report that can also be used as a deployment probe.

## API contract

### Single transformation

`POST /encode`

`POST /decode`

Request:

```json
{
  "data": "Hello World",
  "method": "base64"
}
```

Success response:

```json
{
  "status": "success",
  "result": "SGVsbG8gV29ybGQ=",
  "clipboard_ready": true
}
```

Error response:

```json
{
  "status": "error",
  "result": null,
  "message": "Geçerli bir Base64 metni bekleniyordu.",
  "clipboard_ready": false
}
```

### Batch transformation

`POST /bulk/encode`

`POST /bulk/decode`

Request:

```json
{
  "method": "binary",
  "items": ["01001000 01101001", "01001000 01100101 01111000"]
}
```

## Tech stack

- FastAPI
- Pydantic
- Jinja2 templates
- Local CSS and JavaScript assets
- Rich
- tqdm
- pytest
- httpx

## Local development

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open:

- `http://127.0.0.1:8000`
- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/health/transformations`

If you want correct canonical and social-sharing URLs outside localhost, define:

```bash
export HEXLOOM_PUBLIC_URL="https://your-domain.example"
```

## CLI entry point

```bash
.venv/bin/hexloom
```

## Docker

```bash
docker build -t hexloom .
docker run --rm -p 8000:8000 hexloom
```

## Deployment

### Render

This repository includes `render.yaml`, so Render can bootstrap the service directly from GitHub.

### Other platforms

Use the included `Dockerfile` for Fly.io, Google Cloud Run, or any container-based VPS deployment.

## Testing

```bash
.venv/bin/pytest -q
```

Current local verification:

- `18 passed`

## Repository structure

```text
.
├── app/
├── docs/
│   └── assets/
├── static/
├── templates/
├── tests/
├── Dockerfile
├── pyproject.toml
└── render.yaml
```

## Notes

- The frontend copy is intentionally in English for a cleaner product surface.
- API and engine error messages remain explicit and machine-friendly.
- The health endpoint is suitable for basic uptime and readiness checks.
