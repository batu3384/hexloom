# CipherDeck

CipherDeck is a FastAPI web application for encoding and decoding text with multiple transformation methods.

## Features

- Single and double Base64
- Bytearray payload templates
- HTML entities
- Math expression encoding
- ROT13
- URL encoding
- JSON payload wrapping
- Morse code
- Hexadecimal
- Binary
- Built-in health check for all transformations
- Rich terminal request logging
- Local static UI with no CDN dependency

## Local run

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open:

- `http://127.0.0.1:8000`
- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/health/transformations`

## Tests

```bash
.venv/bin/pytest
```

## Docker

```bash
docker build -t cipherdeck .
docker run --rm -p 8000:8000 cipherdeck
```

## Repository notes

- Project metadata lives in `pyproject.toml`
- Static frontend assets live in `static/`
- API and health endpoints live in `app/`
