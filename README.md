# Levo.ai - Schema Upload & Versioning API

This project implements a small API service to upload OpenAPI (JSON/YAML) schemas, validate them, version and persist them (SQLite + filesystem), and fetch versions.

## Features

- Upload OpenAPI v2/v3 (JSON or YAML)
- Basic validation (presence of `openapi` or `swagger`, and `paths`)
- Versioning: every upload creates a new version (1, 2, 3, ...)
- Stores schemas on filesystem (in `storage/`) and metadata in SQLite (`levo.db`)
- Endpoints to get latest/older versions and list versions
- Unit tests with pytest

## Quickstart (Linux/macOS)

1. Create a virtualenv & install dependencies
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
