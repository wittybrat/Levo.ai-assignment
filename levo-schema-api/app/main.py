# app/main.py
import os
from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from . import db, crud, utils, schemas as dto
from .db import SessionLocal
from typing import Optional
from datetime import datetime

app = FastAPI(title="Levo.ai - Schema Upload & Versioning API")

# Dependency to get DB session
def get_db():
    db_session = SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()

# Initialize DB tables if not present
db.init_db()

@app.post("/upload", response_model=dto.UploadResponse)
def upload_schema(
    application: str = Form(..., description="Application name (parent)"),
    service: Optional[str] = Form(None, description="Service name (optional)"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload an OpenAPI schema (JSON or YAML). The server validates basic structure and stores the file.
    Each upload creates a new version (incremental).
    """
    contents = file.file.read()
    parsed = utils.parse_schema_file(contents, file.filename)

    # Validate it's OpenAPI/Swagger
    utils.validate_openapi_schema(parsed)

    # Create/get application/service
    application_obj = crud.get_or_create_application(db, application)
    service_obj = None
    service_id = None
    if service:
        service_obj = crud.get_or_create_service(db, application_obj, service)
        service_id = service_obj.id

    # determine next version
    latest = crud.get_latest_version(db, application_obj.id, service_id)
    next_version = 1 if latest is None else latest + 1

    # save to storage (we store as pretty JSON)
    saved_path = utils.save_schema_file(application, service, next_version, parsed, file.filename)

    # persist metadata
    sv = crud.create_schema_version(
        db=db,
        application_id=application_obj.id,
        service_id=service_id,
        version=next_version,
        file_path=saved_path,
        original_filename=file.filename,
        content_type=file.content_type or "application/json"
    )

    return dto.UploadResponse(
        application=application,
        service=service,
        version=sv.version,
        file_path=sv.file_path,
        created_at=sv.created_at
    )

@app.get("/schema/latest", response_model=dto.SchemaInfo)
def get_latest_schema(application: str = Query(...), service: Optional[str] = Query(None), db: Session = Depends(get_db)):
    """
    Return latest schema file metadata (and file path). Use /download endpoint to fetch file content.
    """
    app_obj = db.query(db.Base.classes.applications).filter_by(name=application).first() if False else None
    # simpler: fetch application by name
    from .models import Application
    application_obj = db.query(Application).filter_by(name=application).first()
    if not application_obj:
        raise HTTPException(status_code=404, detail="Application not found")
    service_id = None
    if service:
        from .models import Service
        service_obj = db.query(Service).filter_by(name=service, application_id=application_obj.id).first()
        if not service_obj:
            raise HTTPException(status_code=404, detail="Service not found")
        service_id = service_obj.id

    sv = crud.get_schema_latest_record(db, application_obj.id, service_id)
    if not sv:
        raise HTTPException(status_code=404, detail="No schema versions found for target")

    return dto.SchemaInfo(
        application=application,
        service=service,
        version=sv.version,
        file_path=sv.file_path,
        created_at=sv.created_at
    )

@app.get("/schema/{version}")
def download_schema_version(version: int, application: str = Query(...), service: Optional[str] = Query(None), db: Session = Depends(get_db)):
    """
    Download the schema file for a specific version.
    """
    from .models import Application, Service
    application_obj = db.query(Application).filter_by(name=application).first()
    if not application_obj:
        raise HTTPException(status_code=404, detail="Application not found")

    service_id = None
    if service:
        service_obj = db.query(Service).filter_by(name=service, application_id=application_obj.id).first()
        if not service_obj:
            raise HTTPException(status_code=404, detail="Service not found")
        service_id = service_obj.id

    sv = crud.get_schema_by_version(db, application_obj.id, service_id, version)
    if not sv:
        raise HTTPException(status_code=404, detail="Schema version not found")

    # Return file as response
    if not os.path.exists(sv.file_path):
        raise HTTPException(status_code=500, detail="Schema file missing on server")
    return FileResponse(sv.file_path, media_type="application/json", filename=f"{application}-{service or 'app'}-{version}.json")

@app.get("/schema/versions", response_model=dto.VersionsList)
def list_versions(application: str = Query(...), service: Optional[str] = Query(None), db: Session = Depends(get_db)):
    from .models import Application, Service
    application_obj = db.query(Application).filter_by(name=application).first()
    if not application_obj:
        raise HTTPException(status_code=404, detail="Application not found")

    service_id = None
    if service:
        service_obj = db.query(Service).filter_by(name=service, application_id=application_obj.id).first()
        if not service_obj:
            raise HTTPException(status_code=404, detail="Service not found")
        service_id = service_obj.id

    versions = crud.list_versions(db, application_obj.id, service_id)
    return dto.VersionsList(
        application=application,
        service=service,
        versions=[v.version for v in versions]
    )

@app.get("/apps")
def list_applications(db: Session = Depends(get_db)):
    from .models import Application
    apps = db.query(Application).order_by(Application.name).all()
    return {"applications": [a.name for a in apps]}

@app.get("/services")
def list_services(application: str = Query(...), db: Session = Depends(get_db)):
    from .models import Application, Service
    application_obj = db.query(Application).filter_by(name=application).first()
    if not application_obj:
        raise HTTPException(status_code=404, detail="Application not found")
    services = db.query(Service).filter_by(application_id=application_obj.id).order_by(Service.name).all()
    return {"application": application, "services": [s.name for s in services]}
