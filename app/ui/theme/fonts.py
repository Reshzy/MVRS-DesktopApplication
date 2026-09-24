from typing import Final

FAMILY: Final[str] = "Segoe UI"
TITLE_SIZE: Final[int] = 28
HEADING_SIZE: Final[int] = 20
SUBHEADING_SIZE: Final[int] = 16
BODY_SIZE: Final[int] = 14
CAPTION_SIZE: Final[int] = 12
TITLE_WEIGHT: Final[str] = "bold"
HEADING_WEIGHT: Final[str] = "bold"
BODY_WEIGHT: Final[str] = "normal"


def as_dict() -> dict[str, str]:
    tokens: dict[str, str] = {}
    for name, value in globals().items():
        if not name.isupper():
            continue
        tokens[name] = str(value)
    return tokens
