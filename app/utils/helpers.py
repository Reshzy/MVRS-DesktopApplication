from datetime import datetime

from pydantic import ValidationError


def format_validation_error(exc: ValidationError) -> str:
    messages: list[str] = []
    for error in exc.errors():
        field = error.get("loc", (None,))[0]
        raw = str(error.get("msg", "Invalid input"))
        if raw.startswith("Value error, "):
            raw = raw.removeprefix("Value error, ")

        if field == "email":
            messages.append("Enter a valid email address.")
        elif field == "password":
            messages.append("Password must be at least 8 characters.")
        elif field == "confirm_password":
            messages.append("Confirm your password.")
        elif field == "name":
            messages.append("Name is required.")
        else:
            messages.append(raw)

    unique = list(dict.fromkeys(messages))
    return " ".join(unique) if unique else "Please check your input."


def format_user_date(value: datetime | None, prefix: str = "") -> str:
    if value is None:
        return f"{prefix}unknown date" if prefix else "Unknown date"
    local = value.astimezone() if value.tzinfo is not None else value
    text = local.strftime("%b %d, %Y")
    return f"{prefix}{text}" if prefix else text
