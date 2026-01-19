"""Auth service and helpers for CRM authentication."""

from __future__ import annotations

from typing import Optional
import logging

from flask_login import UserMixin
from werkzeug.security import check_password_hash

from .database_manager import DatabaseManager


class CRMUser(UserMixin):
    """Flask-Login compatible user wrapper."""

    def __init__(self, payload: dict):
        self._payload = payload

    def get_id(self) -> str:
        return str(self._payload['id'])

    @property
    def username(self) -> str:
        return self._payload.get('username')

    @property
    def role(self) -> str:
        return self._payload.get('role', 'admin')

    def is_active(self) -> bool:
        return bool(self._payload.get('active', True))

    @property
    def raw(self) -> dict:
        return self._payload


class AuthService:
    """Handles user lookup and authentication."""

    def __init__(self, db: Optional[DatabaseManager] = None):
        self.db = db or DatabaseManager()

    def load_user_by_id(self, user_id: int) -> Optional[CRMUser]:
        logging.debug("AuthService.load_user_by_id: user_id=%s", user_id)
        record = self.db.get_crm_user_by_id(user_id)
        if not record:
            logging.debug("AuthService.load_user_by_id: user not found")
            return None
        return CRMUser(record)

    def create_user(self, username: str, password: str, role: str = 'user') -> int:
        """Create a new CRM user with validation."""
        role_normalized = (role or 'user').strip().lower()
        if role_normalized not in {'admin', 'user'}:
            raise ValueError('Papel inválido')
        if not username or not password:
            raise ValueError('Usuário e senha são obrigatórios')
        if len(password) < 8:
            raise ValueError('Senha deve ter no mínimo 8 caracteres')
        if self.db.get_crm_user_by_username(username):
            raise ValueError('Usuário já existe')
        password_hash = self._generate_password_hash(password)
        return self.db.create_crm_user(username, password_hash, role_normalized, active=True)

    def list_users(self) -> list[dict]:
        return self.db.list_crm_users()

    def set_user_active(self, user_id: int, active: bool) -> None:
        self.db.set_crm_user_active(user_id, active)

    def update_password(self, user_id: int, new_password: str) -> None:
        if not new_password or len(new_password) < 8:
            raise ValueError('Senha deve ter no mínimo 8 caracteres')
        password_hash = self._generate_password_hash(new_password)
        self.db.update_crm_user_password(user_id, password_hash)

    @staticmethod
    def _generate_password_hash(password: str) -> str:
        from werkzeug.security import generate_password_hash as _generate

        return _generate(password)

    def authenticate(self, username: str, password: str) -> Optional[CRMUser]:
        logging.info("AuthService.authenticate: tentativa de login username=%s", username)
        if not username or not password:
            logging.warning("AuthService.authenticate: credenciais ausentes username=%s", username)
            return None
        record = self.db.get_crm_user_by_username(username)
        if not record or not record.get('active'):
            logging.warning(
                "AuthService.authenticate: usuário não encontrado ou inativo username=%s active=%s",
                username,
                record.get('active') if record else None
            )
            return None
        stored_hash = record.get('password_hash')
        if not stored_hash:
            logging.warning("AuthService.authenticate: missing password hash for username=%s", username)
            return None
        if not check_password_hash(stored_hash, password):
            logging.warning("AuthService.authenticate: senha inválida username=%s", username)
            return None
        self.db.update_crm_user_last_login(record['id'])
        logging.info("AuthService.authenticate: login sucesso username=%s", username)
        return CRMUser(record)
