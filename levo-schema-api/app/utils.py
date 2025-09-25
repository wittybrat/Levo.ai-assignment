# app/utils.py
import os
import json
import yaml
from typing import Tuple, Dict, Any
from fastapi import HTTPException

STORAGE_DIR = os.path.join(os.getcwd(), "storage")

def ensure_storage():
    os.makedirs(STORAGE_DIR, exist_ok=True)

def parse_schema_file(contents: bytes, filename: str) -> Dict[str, Any]:
    """
    Accepts bytes from uploaded file. Tries JSON, then YAML.
    Returns parsed object (dict).
    Raises HTTPException(400) if parse fails.
    """
    # try JSON
    try:
        text = contents.decode('utf-8')
    except Exception:
        raise HTTPException(status_code=400, detail="File must be UTF-8 text (json/yaml).")

    try:
        data = json.loads(text)
        return data
    except Exception:
        # try YAML
        try:
            data = yaml.safe_load(text)
            if not isinstance(data, dict):
                raise HTTPException(status_code=400, detail="Parsed YAML content is not an object at top-level.")
            return data
        except Exception:
            raise HTTPException(status_code=400, detail="Uploaded file is neither valid JSON nor YAML.")

def validate_openapi_schema(data: dict):
    """
    Simple validation: Ensure top-level 'openapi' or 'swagger' and 'paths' exist.
    This is intentionally lightweight (could be expanded with openapi-spec-validator).
    """
    if not isinstance(data, dict):
        raise HTTPException(status_code=400, detail="Schema root must be an object.")

    if "openapi" not in data and "swagger" not in data:
        raise HTTPException(status_code=400, detail="Schema missing 'openapi' or 'swagger' field.")

    if "paths" not in data or not isinstance(data["paths"], dict):
        raise HTTPException(status_code=400, detail="Schema must contain 'paths' object.")

def save_schema_file(application: str, service: str or None, version: int, data: dict, original_filename: str) -> str:
    """
    Saves the given schema dict as pretty JSON in storage/<app>/<service_or__app>/<version>.json
    Returns the saved path.
    """
    ensure_storage()
    safe_app = application.replace("/", "_")
    safe_service = (service.replace("/", "_") if service else "_app")
    target_dir = os.path.join(STORAGE_DIR, safe_app, safe_service)
    os.makedirs(target_dir, exist_ok=True)
    out_path = os.path.join(target_dir, f"{version}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return out_path
