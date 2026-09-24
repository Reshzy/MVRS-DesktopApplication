from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ICONS = ROOT / "assets" / "icons"
IMAGES = ROOT / "assets" / "images"
PLACEHOLDERS = ROOT / "assets" / "placeholders"
FONTS = ROOT / "assets" / "fonts"


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for name in ("segoeui.ttf", "arial.ttf"):
        candidate = Path(r"C:\Windows\Fonts") / name
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


def _rounded_rect(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], radius: int, fill: str) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill)


def make_poster() -> None:
    PLACEHOLDERS.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (342, 513), "#20232B")
    draw = ImageDraw.ImageDraw(image)
    _rounded_rect(draw, (28, 36, 314, 476), 18, "#181A1F")
    draw.rectangle((48, 64, 294, 300), outline="#C9A36A", width=3)
    draw.line((48, 182, 294, 182), fill="#2C303A", width=2)
    font = _font(28)
    text = "No Poster"
    bbox = draw.textbbox((0, 0), text, font=font)
    x = (342 - (bbox[2] - bbox[0])) // 2
    draw.text((x, 340), text, fill="#A1A1AA", font=font)
    image.save(PLACEHOLDERS / "poster.png")


def make_app_icon() -> None:
    ICONS.mkdir(parents=True, exist_ok=True)
    sizes = (16, 32, 48, 64, 128, 256)
    frames: list[Image.Image] = []
    for size in sizes:
        image = Image.new("RGBA", (size, size), (16, 17, 20, 255))
        draw = ImageDraw.ImageDraw(image)
        pad = max(1, size // 10)
        _rounded_rect(draw, (pad, pad, size - pad, size - pad), max(2, size // 8), "#20232B")
        reel_r = max(2, size // 8)
        draw.ellipse((size * 0.22, size * 0.18, size * 0.22 + reel_r * 2, size * 0.18 + reel_r * 2), fill="#C9A36A")
        draw.ellipse((size * 0.58, size * 0.18, size * 0.58 + reel_r * 2, size * 0.18 + reel_r * 2), fill="#C9A36A")
        draw.rounded_rectangle(
            (size * 0.22, size * 0.42, size * 0.78, size * 0.82),
            radius=max(2, size // 12),
            outline="#C9A36A",
            width=max(1, size // 18),
        )
        frames.append(image)
    frames[0].save(ICONS / "app.ico", format="ICO", sizes=[(size, size) for size in sizes])
    frames[-1].save(ICONS / "app.png")


def make_mark() -> None:
    IMAGES.mkdir(parents=True, exist_ok=True)
    FONTS.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (512, 256), "#101114")
    draw = ImageDraw.ImageDraw(image)
    _rounded_rect(draw, (36, 36, 476, 220), 24, "#181A1F")
    draw.text((64, 88), "MVRS", fill="#C9A36A", font=_font(72))
    draw.text((68, 168), "Movie Recommendation System", fill="#A1A1AA", font=_font(20))
    image.save(IMAGES / "mark.png")


def main() -> None:
    make_poster()
    make_app_icon()
    make_mark()
    print("Generated packaging assets.")


if __name__ == "__main__":
    main()
