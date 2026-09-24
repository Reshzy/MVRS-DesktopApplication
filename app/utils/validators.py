import re

EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


def normalize_email(email: str) -> str:
    value = (email or "").strip().lower()
    if not value or not EMAIL_PATTERN.fullmatch(value):
        raise ValueError("Invalid email address")
    return value
