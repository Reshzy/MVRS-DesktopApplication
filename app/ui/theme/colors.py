from typing import Final

BACKGROUND: Final[str] = "#101114"
SURFACE: Final[str] = "#181A1F"
SURFACE_RAISED: Final[str] = "#20232B"
BORDER: Final[str] = "#2C303A"
TEXT_PRIMARY: Final[str] = "#F3F4F6"
TEXT_SECONDARY: Final[str] = "#A1A1AA"
TEXT_MUTED: Final[str] = "#71717A"
ACCENT: Final[str] = "#C9A36A"
ACCENT_HOVER: Final[str] = "#D4B27E"
ACCENT_PRESSED: Final[str] = "#B08B52"
ACCENT_TEXT: Final[str] = "#16130D"
SECONDARY: Final[str] = "#2A2E38"
SECONDARY_HOVER: Final[str] = "#353A46"
SECONDARY_PRESSED: Final[str] = "#22262E"
DANGER: Final[str] = "#C45C5C"
DANGER_HOVER: Final[str] = "#D36B6B"
DANGER_PRESSED: Final[str] = "#A84C4C"
MUTED: Final[str] = "#3A3D46"
MUTED_HOVER: Final[str] = "#454854"
FOCUS: Final[str] = "#C9A36A"
SCROLL_TRACK: Final[str] = "#14161A"
SCROLL_THUMB: Final[str] = "#3A3D46"


def as_dict() -> dict[str, str]:
    return {name: value for name, value in globals().items() if name.isupper() and isinstance(value, str)}
