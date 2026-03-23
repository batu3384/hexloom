# Changelog

All notable changes to Hexloom are documented in this file.

## [0.1.2] - 2026-03-24

### Added

- `CONTRIBUTING.md`, `SECURITY.md`, issue templates, and pull request template for a complete public GitHub surface

### Fixed

- Aligned project and app version metadata with the active release line
- Opted GitHub Actions into the Node 24 runtime path to remove pending action-runtime drift

### Changed

- Expanded package metadata with keywords and project URLs
- Tightened repository community health and contribution guidance

## [0.1.1] - 2026-03-24

### Fixed

- Corrected `pyproject.toml` metadata so editable installs and GitHub Actions builds succeed
- Added package README metadata for clean source and wheel validation
- Limited CI execution to `main`, pull requests, and manual runs to avoid noisy tag-triggered workflows

### Changed

- Refined the README structure, badges, and deployment guidance for a more professional GitHub surface

## [0.1.0] - 2026-03-24

### Added

- FastAPI backend for 11 text transformation methods
- Single and batch transformation endpoints
- Built-in self-check endpoint for transformation reliability
- Professional Hexloom interface with local static assets
- Branded favicon, social preview card, and deployment-ready README
- Render deployment setup and live application URL

### Changed

- Product branding finalized as `Hexloom`
- GitHub repository metadata aligned with the live deployment
