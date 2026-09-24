from app.ui.theme import load_stylesheet, theme_tokens
from app.ui.theme.colors import ACCENT, BACKGROUND, DANGER, LIGHT


def test_stylesheet_uses_central_tokens() -> None:
    stylesheet = load_stylesheet()
    tokens = theme_tokens()

    assert BACKGROUND in stylesheet
    assert ACCENT in stylesheet
    assert DANGER in stylesheet
    assert 'QPushButton[variant="primary"]' in stylesheet
    assert 'QPushButton[variant="danger"]' in stylesheet
    assert "QLineEdit" in stylesheet
    assert "QScrollBar:vertical" in stylesheet
    assert "QDialog" in stylesheet
    assert "sidebar" in stylesheet
    assert 'QPushButton[role="star"]' in stylesheet
    assert 'QLabel[role="stat"]' in stylesheet
    assert tokens["BACKGROUND"] == BACKGROUND


def test_light_theme_uses_separate_palette() -> None:
    tokens = theme_tokens("light")
    stylesheet = load_stylesheet("light")

    assert tokens["BACKGROUND"] == LIGHT["BACKGROUND"]
    assert LIGHT["BACKGROUND"] in stylesheet
    assert BACKGROUND not in stylesheet
