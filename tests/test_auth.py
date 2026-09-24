import pytest
from pydantic import ValidationError

from app.models.user import User
from app.services.auth_service import AuthService, DuplicateEmailError, InvalidCredentialsError
from app.state.app_state import AppState


VALID_REGISTER = {
    "name": "Ada Lovelace",
    "email": "ada@example.com",
    "password": "password123",
    "confirm_password": "password123",
}


def test_successful_registration(auth_service: AuthService, db_session, app_state: AppState) -> None:
    user = auth_service.register(**VALID_REGISTER)

    assert user.id is not None
    assert user.name == "Ada Lovelace"
    assert user.email == "ada@example.com"
    assert user.password_hash
    assert user.password_hash != VALID_REGISTER["password"]
    assert "password123" not in user.password_hash
    assert db_session.get(User, user.id) is not None
    assert app_state.current_user is not None
    assert app_state.current_user.id == user.id


def test_duplicate_email(auth_service: AuthService) -> None:
    auth_service.register(**VALID_REGISTER)

    with pytest.raises(DuplicateEmailError):
        auth_service.register(**VALID_REGISTER)


def test_invalid_email(auth_service: AuthService) -> None:
    with pytest.raises(ValidationError):
        auth_service.register(
            name="Ada Lovelace",
            email="not-an-email",
            password="password123",
            confirm_password="password123",
        )


def test_short_password(auth_service: AuthService) -> None:
    with pytest.raises(ValidationError):
        auth_service.register(
            name="Ada Lovelace",
            email="ada@example.com",
            password="short",
            confirm_password="short",
        )


def test_valid_login(auth_service: AuthService, app_state: AppState) -> None:
    registered = auth_service.register(**VALID_REGISTER)
    app_state.clear_current_user()

    user = auth_service.login(email="ada@example.com", password="password123")

    assert user.id == registered.id
    assert user.email == "ada@example.com"
    assert app_state.current_user is not None
    assert app_state.current_user.id == registered.id


def test_invalid_login(auth_service: AuthService) -> None:
    auth_service.register(**VALID_REGISTER)

    with pytest.raises(InvalidCredentialsError):
        auth_service.login(email="ada@example.com", password="wrongpassword")

    with pytest.raises(InvalidCredentialsError):
        auth_service.login(email="missing@example.com", password="password123")


def test_password_mismatch_is_rejected(auth_service: AuthService) -> None:
    with pytest.raises(ValidationError, match="match"):
        auth_service.register(
            name="Ada Lovelace",
            email="ada@example.com",
            password="password123",
            confirm_password="password456",
        )


def test_blank_name_is_rejected(auth_service: AuthService) -> None:
    with pytest.raises(ValidationError):
        auth_service.register(
            name="   ",
            email="ada@example.com",
            password="password123",
            confirm_password="password123",
        )


def test_email_is_normalized_for_register_and_login(
    auth_service: AuthService, db_session, app_state: AppState
) -> None:
    user = auth_service.register(
        name="Ada Lovelace",
        email="  Ada@Example.COM  ",
        password="password123",
        confirm_password="password123",
    )
    assert user.email == "ada@example.com"
    assert db_session.get(User, user.id).email == "ada@example.com"

    app_state.clear_current_user()
    logged_in = auth_service.login(email="ADA@example.com", password="password123")
    assert logged_in.id == user.id
    assert app_state.current_user is not None
    assert app_state.current_user.id == user.id


def test_password_hash_and_verify_roundtrip(auth_service: AuthService) -> None:
    hashed = auth_service.hash_password("password123")
    assert hashed != "password123"
    assert auth_service.verify_password("password123", hashed) is True
    assert auth_service.verify_password("wrongpassword", hashed) is False


def test_register_and_login_work_without_app_state(db_session) -> None:
    service = AuthService(db_session)
    user = service.register(**VALID_REGISTER)
    assert user.id is not None
    assert db_session.get(User, user.id) is not None

    logged_in = service.login(email="ada@example.com", password="password123")
    assert logged_in.id == user.id
