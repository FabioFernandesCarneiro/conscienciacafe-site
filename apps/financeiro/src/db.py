"""Database configuration and SQLAlchemy setup."""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session

Base = declarative_base()
_SessionFactory = None
_engine: Engine | None = None


def init_engine(url: str | None = None) -> Engine:
    """Initialize SQLAlchemy engine. Infer dialect when not provided."""
    global _engine, _SessionFactory

    if url is None:
        url = os.getenv('DATABASE_URL')
        # Debug: verificar se DATABASE_URL foi encontrada
        if url:
            print(f"✅ DATABASE_URL encontrada: {url[:20]}...")
        else:
            print("⚠️ DATABASE_URL não encontrada, usando SQLite local")

    if not url:
        # Default to SQLite file inside project data directory
        # Go up one level from src/ to reach Consciencia_Cafe/data/
        project_root = os.path.dirname(os.path.dirname(__file__))
        default_path = os.path.join(project_root, 'data', 'local_financeiro.db')
        # Ensure data directory exists
        os.makedirs(os.path.dirname(default_path), exist_ok=True)
        url = f'sqlite:///{default_path}'
    else:
        # Railway/Heroku provide postgres:// but SQLAlchemy requires postgresql://
        if url.startswith('postgres://'):
            url = url.replace('postgres://', 'postgresql+psycopg2://', 1)

    connect_args = {}
    if url.startswith('sqlite:///'):
        connect_args = {"check_same_thread": False}

    _engine = create_engine(url, echo=False, future=True, connect_args=connect_args)
    _SessionFactory = scoped_session(sessionmaker(bind=_engine, expire_on_commit=False))
    return _engine


def get_engine() -> Engine:
    if _engine is None:
        return init_engine()
    return _engine


def get_session():
    if _SessionFactory is None:
        init_engine()
    return _SessionFactory()


@contextmanager
def session_scope() -> Iterator:
    session = get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


__all__ = ['Base', 'init_engine', 'get_engine', 'get_session', 'session_scope']
