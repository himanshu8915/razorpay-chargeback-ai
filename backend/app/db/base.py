"""
SQLAlchemy declarative base.
All ORM models will inherit from Base.
Models are defined in Phase 1 (dataset schema) and Phase 2+ (case/decision entities).
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
