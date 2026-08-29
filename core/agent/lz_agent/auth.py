from __future__ import annotations

import hashlib
import re
import secrets
import sqlite3
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError

from .database import Database, utc_now

USERNAME = re.compile(r"^[a-z0-9][a-z0-9._-]{2,63}$")


class AuthenticationError(ValueError):
    pass


class AuthService:
    def __init__(self, database: Database) -> None:
        self.database = database
        self.passwords = PasswordHasher()

    def has_users(self) -> bool:
        with self.database.connect() as connection:
            row = connection.execute("SELECT 1 FROM users LIMIT 1").fetchone()
        return row is not None

    def register(
        self, username: str, display_name: str, password: str, locale: str = "pt-BR"
    ) -> dict[str, Any]:
        normalized = username.strip().lower()
        if not USERNAME.fullmatch(normalized):
            raise AuthenticationError("Usuário deve ter 3–64 caracteres seguros")
        if len(password) < 12 or len(password) > 1024:
            raise AuthenticationError("A senha deve ter pelo menos 12 caracteres")
        user_id = str(uuid.uuid4())
        now = utc_now()
        try:
            with self.database.connect() as connection:
                connection.execute(
                    """INSERT INTO users
                    (id, username, display_name, password_hash, locale, active,
                     created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, 1, ?, ?)""",
                    (
                        user_id,
                        normalized,
                        display_name.strip() or normalized,
                        self.passwords.hash(password),
                        locale,
                        now,
                        now,
                    ),
                )
        except sqlite3.IntegrityError as error:
            raise AuthenticationError("Nome de usuário indisponível") from error
        return self._public_user(user_id)

    def login(self, username: str, password: str) -> dict[str, Any]:
        normalized = username.strip().lower()
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT * FROM users WHERE username = ? COLLATE NOCASE", (normalized,)
            ).fetchone()
        if row is None or not row["active"]:
            raise AuthenticationError("Credenciais inválidas")
        try:
            self.passwords.verify(row["password_hash"], password)
        except VerificationError as error:
            raise AuthenticationError("Credenciais inválidas") from error
        if self.passwords.check_needs_rehash(row["password_hash"]):
            with self.database.connect() as connection:
                connection.execute(
                    "UPDATE users SET password_hash = ?, updated_at = ? WHERE id = ?",
                    (self.passwords.hash(password), utc_now(), row["id"]),
                )
        return self._create_session(row["id"])

    def authenticate(self, token: str) -> dict[str, Any]:
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        with self.database.connect() as connection:
            row = connection.execute(
                """SELECT u.id FROM user_sessions s JOIN users u ON u.id = s.user_id
                WHERE s.token_hash = ? AND s.revoked_at IS NULL
                AND s.expires_at > ? AND u.active = 1""",
                (token_hash, utc_now()),
            ).fetchone()
        if row is None:
            raise AuthenticationError("Sessão inválida ou expirada")
        return self._public_user(row["id"])

    def logout(self, token: str) -> None:
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        with self.database.connect() as connection:
            connection.execute(
                "UPDATE user_sessions SET revoked_at = ? WHERE token_hash = ?",
                (utc_now(), token_hash),
            )

    def _create_session(self, user_id: str) -> dict[str, Any]:
        token = secrets.token_urlsafe(32)
        now = datetime.now(UTC)
        expires = now + timedelta(days=30)
        with self.database.connect() as connection:
            connection.execute(
                """INSERT INTO user_sessions
                (id, user_id, token_hash, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?)""",
                (
                    str(uuid.uuid4()),
                    user_id,
                    hashlib.sha256(token.encode()).hexdigest(),
                    now.isoformat(),
                    expires.isoformat(),
                ),
            )
        return {"access_token": token, "token_type": "bearer", "expires_at": expires.isoformat()}

    def _public_user(self, user_id: str) -> dict[str, Any]:
        with self.database.connect() as connection:
            row = connection.execute(
                """SELECT id, username, display_name, locale, created_at
                FROM users WHERE id = ?""",
                (user_id,),
            ).fetchone()
        if row is None:
            raise AuthenticationError("Usuário não encontrado")
        return dict(row)
