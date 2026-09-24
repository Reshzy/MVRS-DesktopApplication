from __future__ import annotations

import bcrypt
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.locks import session_lock
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth_schema import LoginRequest, RegisterRequest
from app.state.app_state import AppState


class AuthError(Exception):
    pass


class DuplicateEmailError(AuthError):
    pass


class InvalidCredentialsError(AuthError):
    pass


class AuthService:
    def __init__(self, session: Session, app_state: AppState | None = None) -> None:
        self._session = session
        self._repository = UserRepository(session)
        self._app_state = app_state

    def hash_password(self, password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def verify_password(self, password: str, password_hash: str) -> bool:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))

    def register(
        self,
        data: RegisterRequest | None = None,
        *,
        name: str | None = None,
        email: str | None = None,
        password: str | None = None,
        confirm_password: str | None = None,
    ) -> User:
        payload = data or RegisterRequest(
            name=name,
            email=email,
            password=password,
            confirm_password=confirm_password,
        )
        password_hash = self.hash_password(payload.password)
        try:
            with session_lock():
                if self._repository.get_by_email(payload.email) is not None:
                    raise DuplicateEmailError("An account with this email already exists.")
                user = self._repository.create(
                    name=payload.name,
                    email=payload.email,
                    password_hash=password_hash,
                )
                self._session.commit()
                self._session.refresh(user)
        except DuplicateEmailError:
            raise
        except IntegrityError as exc:
            with session_lock():
                self._session.rollback()
            raise DuplicateEmailError("An account with this email already exists.") from exc

        self._assign_current_user(user)
        return user

    def login(
        self,
        data: LoginRequest | None = None,
        *,
        email: str | None = None,
        password: str | None = None,
    ) -> User:
        payload = data or LoginRequest(email=email, password=password)
        with session_lock():
            user = self._repository.get_by_email(payload.email)
        if user is None or not self.verify_password(payload.password, user.password_hash):
            raise InvalidCredentialsError("Invalid email or password.")

        self._assign_current_user(user)
        return user

    def _assign_current_user(self, user: User) -> None:
        if self._app_state is not None:
            self._app_state.set_current_user(user)
