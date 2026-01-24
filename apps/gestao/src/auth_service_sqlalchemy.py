"""Auth service using SQLAlchemy for PostgreSQL/SQLite compatibility."""

from __future__ import annotations

from typing import Optional
import logging

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from .db import session_scope
from .models import CRMUser as CRMUserModel


class CRMUser(UserMixin):
    """Flask-Login compatible user wrapper."""

    def __init__(self, payload: dict):
        self._payload = payload

    def get_id(self) -> str:
        return str(self._payload['id'])

    @property
    def id(self) -> int:
        return self._payload['id']

    @property
    def username(self) -> str:
        return self._payload.get('username')

    @property
    def role(self) -> str:
        return self._payload.get('role', 'admin')

    @property
    def country(self) -> Optional[str]:
        return self._payload.get('country')

    @property
    def native_currency(self) -> str:
        """Return the native currency based on user's country."""
        country = self.country
        if country == 'PY':
            return 'PYG'
        return 'BRL'  # Default to BRL

    @property
    def is_seller(self) -> bool:
        return self.role == 'vendedor'

    @property
    def is_admin(self) -> bool:
        return self.role == 'admin'

    def is_active(self) -> bool:
        return bool(self._payload.get('active', True))

    @property
    def raw(self) -> dict:
        return self._payload


class AuthService:
    """Handles user lookup and authentication using SQLAlchemy."""

    def load_user_by_id(self, user_id: int) -> Optional[CRMUser]:
        logging.debug("AuthService.load_user_by_id: user_id=%s", user_id)

        with session_scope() as session:
            user = session.query(CRMUserModel).filter_by(id=user_id).first()

            if not user:
                logging.debug("AuthService.load_user_by_id: user not found")
                return None

            payload = {
                'id': user.id,
                'username': user.username,
                'password_hash': user.password_hash,
                'role': user.role,
                'country': user.country,
                'active': user.active,
                'last_login': user.last_login,
                'created_at': user.created_at,
                'updated_at': user.updated_at
            }

            return CRMUser(payload)

    def create_user(self, username: str, password: str, role: str = 'user', country: str = None) -> int:
        """Create a new CRM user with validation."""
        role_normalized = (role or 'user').strip().lower()
        if role_normalized not in {'admin', 'user', 'vendedor'}:
            raise ValueError('Papel inválido')
        if not username or not password:
            raise ValueError('Usuário e senha são obrigatórios')
        if len(password) < 8:
            raise ValueError('Senha deve ter no mínimo 8 caracteres')

        # Country is required for sellers
        if role_normalized == 'vendedor':
            if not country or country.upper() not in ('BR', 'PY'):
                raise ValueError('País é obrigatório para vendedores (BR ou PY)')
            country = country.upper()
        else:
            country = country.upper() if country else None

        with session_scope() as session:
            existing = session.query(CRMUserModel).filter_by(username=username).first()
            if existing:
                raise ValueError('Usuário já existe')

            password_hash = generate_password_hash(password)
            user = CRMUserModel(
                username=username,
                password_hash=password_hash,
                role=role_normalized,
                country=country,
                active=True
            )
            session.add(user)
            session.commit()
            return user.id

    def list_users(self) -> list[dict]:
        with session_scope() as session:
            users = session.query(CRMUserModel).all()
            return [
                {
                    'id': u.id,
                    'username': u.username,
                    'role': u.role,
                    'country': u.country,
                    'active': u.active,
                    'last_login': u.last_login,
                    'created_at': u.created_at
                }
                for u in users
            ]

    def get_sellers(self) -> list[dict]:
        """List all users with role 'vendedor'."""
        with session_scope() as session:
            users = session.query(CRMUserModel).filter_by(role='vendedor', active=True).all()
            return [
                {
                    'id': u.id,
                    'username': u.username,
                    'country': u.country,
                    'active': u.active
                }
                for u in users
            ]

    def get_all_active_users(self) -> list[dict]:
        """List all active users (for admin to select order owner)."""
        with session_scope() as session:
            users = session.query(CRMUserModel).filter_by(active=True).all()
            return [
                {
                    'id': u.id,
                    'username': u.username,
                    'role': u.role,
                    'country': u.country
                }
                for u in users
            ]

    def update_user(self, user_id: int, role: str = None, country: str = None, active: bool = None) -> None:
        """Update user attributes (role, country, active status)."""
        with session_scope() as session:
            user = session.query(CRMUserModel).filter_by(id=user_id).first()
            if not user:
                raise ValueError('Usuário não encontrado')

            if role is not None:
                role_normalized = role.strip().lower()
                if role_normalized not in {'admin', 'user', 'vendedor'}:
                    raise ValueError('Papel inválido')
                user.role = role_normalized

            if country is not None:
                user.country = country.upper() if country else None

            if active is not None:
                user.active = active

            # Validate country for sellers
            if user.role == 'vendedor' and not user.country:
                raise ValueError('País é obrigatório para vendedores')

            session.commit()

    def set_user_active(self, user_id: int, active: bool) -> None:
        with session_scope() as session:
            user = session.query(CRMUserModel).filter_by(id=user_id).first()
            if user:
                user.active = active
                session.commit()

    def update_password(self, user_id: int, new_password: str) -> None:
        if not new_password or len(new_password) < 8:
            raise ValueError('Senha deve ter no mínimo 8 caracteres')

        with session_scope() as session:
            user = session.query(CRMUserModel).filter_by(id=user_id).first()
            if user:
                user.password_hash = generate_password_hash(new_password)
                session.commit()

    def authenticate(self, username: str, password: str) -> Optional[CRMUser]:
        logging.info("AuthService.authenticate: tentativa de login username=%s", username)

        if not username or not password:
            logging.warning("AuthService.authenticate: credenciais ausentes username=%s", username)
            return None

        with session_scope() as session:
            user = session.query(CRMUserModel).filter_by(username=username).first()

            if not user or not user.active:
                logging.warning(
                    "AuthService.authenticate: usuário não encontrado ou inativo username=%s active=%s",
                    username,
                    user.active if user else None
                )
                return None

            stored_hash = user.password_hash
            if not stored_hash:
                logging.warning("AuthService.authenticate: missing password hash for username=%s", username)
                return None

            if not check_password_hash(stored_hash, password):
                logging.warning("AuthService.authenticate: senha inválida username=%s", username)
                return None

            # Update last login
            from datetime import datetime
            user.last_login = datetime.utcnow()
            session.commit()

            logging.info("AuthService.authenticate: login sucesso username=%s", username)

            payload = {
                'id': user.id,
                'username': user.username,
                'password_hash': user.password_hash,
                'role': user.role,
                'country': user.country,
                'active': user.active,
                'last_login': user.last_login,
                'created_at': user.created_at,
                'updated_at': user.updated_at
            }

            return CRMUser(payload)

    # Compatibility with existing code
    def update_crm_user_last_login(self, user_id: int) -> None:
        from datetime import datetime
        with session_scope() as session:
            user = session.query(CRMUserModel).filter_by(id=user_id).first()
            if user:
                user.last_login = datetime.utcnow()
                session.commit()

    def get_crm_user_by_id(self, user_id: int) -> Optional[dict]:
        with session_scope() as session:
            user = session.query(CRMUserModel).filter_by(id=user_id).first()
            if not user:
                return None
            return {
                'id': user.id,
                'username': user.username,
                'password_hash': user.password_hash,
                'role': user.role,
                'country': user.country,
                'active': user.active,
                'last_login': user.last_login,
                'created_at': user.created_at,
                'updated_at': user.updated_at
            }

    # Add db property for compatibility
    @property
    def db(self):
        return self
