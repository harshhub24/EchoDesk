"""Reusable repository helpers."""

from __future__ import annotations

from typing import Generic, TypeVar

from app.extensions import db

ModelType = TypeVar("ModelType")


class Repository(Generic[ModelType]):
    """Simple repository wrapper around SQLAlchemy session operations."""

    def __init__(self, model: type[ModelType]):
        self.model = model

    def add(self, instance: ModelType) -> ModelType:
        db.session.add(instance)
        return instance

    def delete(self, instance: ModelType) -> None:
        db.session.delete(instance)

    def get(self, primary_key: str) -> ModelType | None:
        return db.session.get(self.model, primary_key)
