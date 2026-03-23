# Hexloom

[![CI](https://github.com/batu3384/hexloom/actions/workflows/ci.yml/badge.svg)](https://github.com/batu3384/hexloom/actions/workflows/ci.yml)
[![Live App](https://img.shields.io/badge/live-hexloom.onrender.com-1f6feb?style=flat-square)](https://hexloom.onrender.com)
[![License: MIT](https://img.shields.io/badge/license-MIT-0f172a?style=flat-square)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-2563eb?style=flat-square)](pyproject.toml)

Hexloom is a FastAPI-powered text transformation studio for encoding, decoding, validating, and inspecting structured text payloads through a single professional interface.

It combines a polished browser workspace, JSON API endpoints, bulk-processing support, built-in diagnostics, and deployment-ready packaging for teams working with Base64, Morse, Binary, Hex, JSON wrappers, and related formats.

## Live links

- Live app: [https://hexloom.onrender.com](https://hexloom.onrender.com)
- API docs: [https://hexloom.onrender.com/docs](https://hexloom.onrender.com/docs)
- Health check: [https://hexloom.onrender.com/health/transformations](https://hexloom.onrender.com/health/transformations)

![Hexloom overview](docs/assets/hexloom-overview.png)

## Highlights

- Eleven supported transformation methods, including single and double Base64
- Single-item and batch workflows from the same interface
- FastAPI backend with OpenAPI and Swagger documentation
- Built-in self-check endpoint for transformation reliability
- Rich terminal request logging and tqdm-backed batch progress
- Local static frontend assets with no Tailwind CDN dependency
- Docker, Render, and GitHub-ready project structure

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

## Product surface

### Workspace

Hexloom gives operators a single workspace to:

- select a transformation method
- switch between `Text to Format` and `Format to Text`
- run single or batch jobs
- inspect the active workflow
- reuse or copy output safely

![Hexloom workspace](docs/assets/hexloom-live-workspace.png)

### Diagnostics

Hexloom exposes `GET /health/transformations`, which runs encode, decode, and batch simulation checks across the supported methods. This makes the application easy to monitor and practical to use as a readiness probe in production.

## API

### Single transform

- `POST /encode`
- `POST /decode`

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

### Batch transform

- `POST /bulk/encode`
- `POST /bulk/decode`

Request:

```json
{
  "method": "binary",
  "items": ["01001000 01101001", "01001000 01100101 01111000"]
}
```

## Quick start

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

The repository includes [`render.yaml`](render.yaml), so Render can provision the web service directly from GitHub.

### Other platforms

Use the included [`Dockerfile`](Dockerfile) for Fly.io, Google Cloud Run, or any container-based VPS deployment.

## Quality checks

```bash
.venv/bin/pytest -q
python3 -m build
python3 -m twine check dist/*
```

Current local verification:

- `18 passed`

## Tech stack

- FastAPI
- Pydantic
- Jinja2
- Rich
- tqdm
- pytest
- httpx

## Repository layout

```text
.
├── app/
├── docs/
│   └── assets/
├── static/
├── templates/
├── tests/
├── CHANGELOG.md
├── Dockerfile
├── LICENSE
├── pyproject.toml
└── render.yaml
```

## License

Hexloom is released under the [MIT License](LICENSE).

## Releases

User-facing changes are tracked in [CHANGELOG.md](CHANGELOG.md), and GitHub releases are published from tags such as [`v0.1.2`](https://github.com/batu3384/hexloom/releases/tag/v0.1.2).

## Contributing

Contribution workflow and local expectations are documented in [CONTRIBUTING.md](CONTRIBUTING.md).

## Security

Security reporting guidance and supported release expectations are documented in [SECURITY.md](SECURITY.md).
