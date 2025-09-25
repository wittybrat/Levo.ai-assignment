# app/models.py
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, UniqueConstraint
from sqlalchemy.orm import relationship
import datetime
from .db import Base

class Application(Base):
    __tablename__ = "applications"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)

    services = relationship("Service", back_populates="application")
    schemas = relationship("SchemaVersion", back_populates="application")


class Service(Base):
    __tablename__ = "services"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)

    application = relationship("Application", back_populates="services")
    schemas = relationship("SchemaVersion", back_populates="service")

    __table_args__ = (
        UniqueConstraint("name", "application_id", name="uq_service_per_app"),
    )


class SchemaVersion(Base):
    __tablename__ = "schema_versions"
    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=True)  # null => application-level API
    version = Column(Integer, nullable=False)
    file_path = Column(String, nullable=False)
    original_filename = Column(String, nullable=True)
    content_type = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    application = relationship("Application", back_populates="schemas")
    service = relationship("Service", back_populates="schemas")

    __table_args__ = (
        UniqueConstraint("application_id", "service_id", "version", name="uq_version_per_target"),
    )
