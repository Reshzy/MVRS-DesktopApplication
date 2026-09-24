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

LIGHT: Final[dict[str, str]] = {
    "BACKGROUND": "#F3EFE6",
    "SURFACE": "#FFFCF6",
    "SURFACE_RAISED": "#F7F1E6",
    "BORDER": "#D8D0C2",
    "TEXT_PRIMARY": "#1C1914",
    "TEXT_SECONDARY": "#5C564C",
    "TEXT_MUTED": "#8A8478",
    "ACCENT": "#B08B52",
    "ACCENT_HOVER": "#C9A36A",
    "ACCENT_PRESSED": "#8F6E3E",
    "ACCENT_TEXT": "#FFFCF6",
    "SECONDARY": "#E8E1D4",
    "SECONDARY_HOVER": "#DDD4C4",
    "SECONDARY_PRESSED": "#D1C6B4",
    "DANGER": "#B94A4A",
    "DANGER_HOVER": "#C45C5C",
    "DANGER_PRESSED": "#9A3C3C",
    "MUTED": "#E2DACB",
    "MUTED_HOVER": "#D6CCBA",
    "FOCUS": "#B08B52",
    "SCROLL_TRACK": "#E8E1D4",
    "SCROLL_THUMB": "#C4BBA8",
}


def as_dict() -> dict[str, str]:
    return {name: value for name, value in globals().items() if name.isupper() and isinstance(value, str)}


def palette(theme: str = "dark") -> dict[str, str]:
    if theme == "light":
        return dict(LIGHT)
    return as_dict()
