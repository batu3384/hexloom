# Contributing to Hexloom

Thanks for contributing to Hexloom.

## Development setup

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
```

Run the app locally:

```bash
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## Before opening a pull request

Run the local quality checks:

```bash
.venv/bin/pytest -q
python3 -m build
python3 -m twine check dist/*
```

## Pull request expectations

- Keep changes scoped and reviewable
- Preserve the existing product tone and visual quality
- Add or update tests when behavior changes
- Do not commit secrets, credentials, or generated noise
- Document user-facing changes in `CHANGELOG.md` when they are release-relevant

## Project conventions

- Backend uses FastAPI and centralizes transformation logic in `app/engine.py`
- User-facing UI copy is in English
- Error handling should stay explicit and safe for web contexts
- Prefer minimal dependencies and production-friendly defaults
