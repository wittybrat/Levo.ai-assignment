# app/crud.py
from sqlalchemy.orm import Session
from . import models
from typing import Optional, Tuple

def get_or_create_application(db: Session, name: str) -> models.Application:
    app = db.query(models.Application).filter_by(name=name).first()
    if app:
        return app
    app = models.Application(name=name)
    db.add(app)
    db.commit()
    db.refresh(app)
    return app

def get_or_create_service(db: Session, application: models.Application, service_name: str) -> models.Service:
    service = db.query(models.Service).filter_by(name=service_name, application_id=application.id).first()
    if service:
        return service
    service = models.Service(name=service_name, application_id=application.id)
    db.add(service)
    db.commit()
    db.refresh(service)
    return service

def get_latest_version(db: Session, application_id: int, service_id: Optional[int]) -> Optional[int]:
    q = db.query(models.SchemaVersion).filter_by(application_id=application_id, service_id=service_id)
    latest = q.order_by(models.SchemaVersion.version.desc()).first()
    return latest.version if latest else None

def create_schema_version(db: Session, application_id: int, service_id: Optional[int], version: int, file_path: str, original_filename: str, content_type: str) -> models.SchemaVersion:
    sv = models.SchemaVersion(
        application_id=application_id,
        service_id=service_id,
        version=version,
        file_path=file_path,
        original_filename=original_filename,
        content_type=content_type
    )
    db.add(sv)
    db.commit()
    db.refresh(sv)
    return sv

def list_versions(db: Session, application_id: int, service_id: Optional[int]) -> list:
    q = db.query(models.SchemaVersion).filter_by(application_id=application_id, service_id=service_id).order_by(models.SchemaVersion.version.asc()).all()
    return q

def get_schema_by_version(db: Session, application_id: int, service_id: Optional[int], version: int):
    return db.query(models.SchemaVersion).filter_by(application_id=application_id, service_id=service_id, version=version).first()

def get_schema_latest_record(db: Session, application_id: int, service_id: Optional[int]):
    return db.query(models.SchemaVersion).filter_by(application_id=application_id, service_id=service_id).order_by(models.SchemaVersion.version.desc()).first()
