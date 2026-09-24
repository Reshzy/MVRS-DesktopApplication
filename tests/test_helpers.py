from datetime import datetime, timezone

from pydantic import ValidationError

from app.schemas.auth_schema import RegisterRequest
from app.utils.helpers import format_user_date, format_validation_error


def test_format_validation_error_handles_model_level_mismatch() -> None:
    try:
        RegisterRequest(
            name="Ada Lovelace",
            email="ada@example.com",
            password="password123",
            confirm_password="password456",
        )
    except ValidationError as exc:
        message = format_validation_error(exc)

    assert "match" in message.lower()
    assert message


def test_format_validation_error_maps_field_messages() -> None:
    try:
        RegisterRequest(
            name="   ",
            email="not-an-email",
            password="short",
            confirm_password="short",
        )
    except ValidationError as exc:
        message = format_validation_error(exc)

    assert "valid email" in message.lower()
    assert "8 characters" in message.lower()
    assert "name is required" in message.lower()


def test_format_user_date_accepts_naive_and_aware() -> None:
    naive = datetime(1999, 10, 15, 12, 0, 0)
    aware = datetime(1999, 10, 15, 12, 0, 0, tzinfo=timezone.utc)

    assert format_user_date(None) == "Unknown date"
    assert "Oct 15, 1999" in format_user_date(naive, "Watched ")
    assert "Oct 15, 1999" in format_user_date(aware, "Watched ")
