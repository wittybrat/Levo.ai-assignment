# app/schemas.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class UploadResponse(BaseModel):
    application: str
    service: Optional[str] = None
    version: int
    file_path: str
    created_at: datetime

class SchemaInfo(BaseModel):
    application: str
    service: Optional[str] = None
    version: int
    file_path: str
    created_at: datetime

class VersionsList(BaseModel):
    application: str
    service: Optional[str] = None
    versions: List[int]
