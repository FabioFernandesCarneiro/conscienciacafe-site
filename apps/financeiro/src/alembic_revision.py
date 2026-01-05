"""Utility to sync SQLite schema to SQLAlchemy models (temporary)."""

from __future__ import annotations

from sqlalchemy import inspect

from .db import init_engine, Base
from .models import *  # noqa: F401,F403


def sync_models(database_url: str | None = None) -> None:
    engine = init_engine(database_url)
    inspector = inspect(engine)
    Base.metadata.create_all(engine)
    tables = inspector.get_table_names()
    print(f"Sincronizado. Tabelas existentes: {tables}")


if __name__ == '__main__':
    sync_models()
