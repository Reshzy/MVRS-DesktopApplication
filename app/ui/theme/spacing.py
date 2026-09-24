from typing import Final

XS: Final[int] = 4
SM: Final[int] = 8
MD: Final[int] = 12
LG: Final[int] = 16
XL: Final[int] = 24
XXL: Final[int] = 32
RADIUS: Final[int] = 8
RADIUS_CARD: Final[int] = 12
SIDEBAR_WIDTH: Final[int] = 220


def as_dict() -> dict[str, str]:
    return {name: str(value) for name, value in globals().items() if name.isupper() and isinstance(value, int)}
