from __future__ import annotations

from pathlib import Path

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

SUPPORTED_MIME_TYPES: dict[str, str] = {
    "text/html": ".html",
    "application/xhtml+xml": ".xhtml",
}


def build_search_text(path: Path, mime_type: str) -> str:
    extension = path.suffix or fallback_extension_label(mime_type)
    size_bytes = path.stat().st_size
    return "\n".join(
        [
            "Archived generic file",
            f"Filename: {path.name}",
            f"MIME type: {mime_type}",
            f"Extension: {extension}",
            f"Size: {size_bytes} bytes",
            "Content preserved unchanged as original download.",
        ],
    )


def render_placeholder_pdf(
    path: Path,
    mime_type: str,
    output_path: Path,
    font_name: str,
) -> None:
    image = render_placeholder_image(path, mime_type, (1240, 1754), font_name)
    image.save(output_path, format="PDF", resolution=150.0)


def render_placeholder_image(
    path: Path,
    mime_type: str,
    size: tuple[int, int],
    font_name: str,
) -> Image.Image:
    width, height = size
    image = Image.new("RGB", (width, height), color=(246, 248, 251))
    draw = ImageDraw.Draw(image)

    title_font = load_font(font_name, max(28, width // 12))
    heading_font = load_font(font_name, max(18, width // 32))
    body_font = load_font(font_name, max(16, width // 38))

    extension_label = display_label(path, mime_type)
    heading = "Generic archived file"
    body_lines = [
        f"Filename: {path.name}",
        f"MIME type: {mime_type}",
        f"Extension: {path.suffix or '(none)'}",
        f"Size: {path.stat().st_size} bytes",
        "Original content is preserved unchanged.",
        "Preview is intentionally synthetic and inert.",
    ]

    banner_height = max(140, height // 4)
    draw.rounded_rectangle(
        (40, 40, width - 40, banner_height),
        radius=36,
        fill=(31, 41, 55),
    )

    title_box = draw.textbbox((0, 0), extension_label, font=title_font)
    title_width = title_box[2] - title_box[0]
    title_height = title_box[3] - title_box[1]
    title_x = (width - title_width) / 2
    title_y = 40 + (banner_height - 40 - title_height) / 2
    draw.text((title_x, title_y), extension_label, fill=(255, 255, 255), font=title_font)

    heading_y = banner_height + 60
    draw.text((60, heading_y), heading, fill=(17, 24, 39), font=heading_font)

    current_y = heading_y + 70
    for line in body_lines:
        draw.text((60, current_y), line, fill=(55, 65, 81), font=body_font)
        current_y += body_font.size + 24

    return image


def metadata_entries(path: Path, mime_type: str) -> list[dict[str, str]]:
    return [
        {
            "namespace": "urn:paperless-generic-file-parser",
            "prefix": "generic",
            "key": "filename",
            "value": path.name,
        },
        {
            "namespace": "urn:paperless-generic-file-parser",
            "prefix": "generic",
            "key": "mime_type",
            "value": mime_type,
        },
        {
            "namespace": "urn:paperless-generic-file-parser",
            "prefix": "generic",
            "key": "extension",
            "value": path.suffix or "",
        },
        {
            "namespace": "urn:paperless-generic-file-parser",
            "prefix": "generic",
            "key": "size_bytes",
            "value": str(path.stat().st_size),
        },
    ]


def display_label(path: Path, mime_type: str) -> str:
    if path.suffix:
        return path.suffix.lstrip(".").upper()[:12] or "FILE"
    return fallback_extension_label(mime_type)


def fallback_extension_label(mime_type: str) -> str:
    subtype = mime_type.split("/", 1)[-1]
    cleaned = subtype.replace("+xml", "").replace("x-", "")
    return cleaned.upper()[:12] or "FILE"


def load_font(font_name: str, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    try:
        return ImageFont.truetype(
            font=font_name,
            size=size,
            layout_engine=ImageFont.Layout.BASIC,
        )
    except Exception:
        return ImageFont.load_default()
