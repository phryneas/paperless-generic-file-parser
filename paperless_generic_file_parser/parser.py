from __future__ import annotations
import shutil
import tempfile
from pathlib import Path
from types import TracebackType
from typing import TYPE_CHECKING
from typing import Self

from django.conf import settings
from documents.parsers import ParseError
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from paperless.parsers import MetadataEntry
from paperless.parsers import ParserContext

from paperless_generic_file_parser import __version__

if TYPE_CHECKING:
    import datetime

SUPPORTED_MIME_TYPES: dict[str, str] = {
    "text/html": ".html",
    "application/xhtml+xml": ".xhtml",
}


class GenericFileParser:
    name = "Generic File Archiver"
    version = __version__
    author = "OpenAI / local site customization"
    url = "https://github.com/paperless-ngx/paperless-ngx"

    @classmethod
    def supported_mime_types(cls) -> dict[str, str]:
        return SUPPORTED_MIME_TYPES

    @classmethod
    def score(
        cls,
        mime_type: str,
        filename: str,
        path: Path | None = None,
    ) -> int | None:
        if mime_type in SUPPORTED_MIME_TYPES:
            return 15
        return None

    @property
    def can_produce_archive(self) -> bool:
        return True

    @property
    def requires_pdf_rendition(self) -> bool:
        return True

    def __init__(self, logging_group: object = None) -> None:
        settings.SCRATCH_DIR.mkdir(parents=True, exist_ok=True)
        self._tempdir = Path(
            tempfile.mkdtemp(prefix="paperless-generic-", dir=settings.SCRATCH_DIR),
        )
        self._text: str = ""
        self._archive_path: Path | None = None
        self._document_name: str | None = None
        self._document_size_bytes: int | None = None
        self._context = ParserContext()

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        shutil.rmtree(self._tempdir, ignore_errors=True)

    def configure(self, context: ParserContext) -> None:
        self._context = context

    def parse(
        self,
        document_path: Path,
        mime_type: str,
        *,
        produce_archive: bool = True,
    ) -> None:
        try:
            path = Path(document_path)
            self._document_name = path.name
            self._document_size_bytes = path.stat().st_size
            self._text = self._build_search_text(path, mime_type)

            if produce_archive:
                archive_path = self._tempdir / "generic-preview.pdf"
                self._render_placeholder_pdf(path, mime_type, archive_path)
                self._archive_path = archive_path
        except Exception as exc:
            raise ParseError(f"Generic file parser failed for {document_path}: {exc}") from exc

    def get_text(self) -> str:
        return self._text

    def get_date(self) -> datetime.datetime | None:
        return None

    def get_archive_path(self) -> Path | None:
        return self._archive_path

    def get_thumbnail(self, document_path: Path, mime_type: str) -> Path:
        path = Path(document_path)
        thumbnail_path = self._tempdir / "thumb.webp"
        image = self._render_placeholder_image(path, mime_type, (500, 700))
        image.save(thumbnail_path, format="WEBP")
        return thumbnail_path

    def get_page_count(self, document_path: Path, mime_type: str) -> int | None:
        return 1

    def extract_metadata(
        self,
        document_path: Path,
        mime_type: str,
    ) -> list[MetadataEntry]:
        try:
            path = Path(document_path)
            return [
                MetadataEntry(
                    namespace="urn:paperless-generic-file-parser",
                    prefix="generic",
                    key="filename",
                    value=path.name,
                ),
                MetadataEntry(
                    namespace="urn:paperless-generic-file-parser",
                    prefix="generic",
                    key="mime_type",
                    value=mime_type,
                ),
                MetadataEntry(
                    namespace="urn:paperless-generic-file-parser",
                    prefix="generic",
                    key="extension",
                    value=path.suffix or "",
                ),
                MetadataEntry(
                    namespace="urn:paperless-generic-file-parser",
                    prefix="generic",
                    key="size_bytes",
                    value=str(path.stat().st_size),
                ),
            ]
        except Exception:
            return []

    def _build_search_text(self, path: Path, mime_type: str) -> str:
        extension = path.suffix or self._fallback_extension_label(mime_type)
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

    def _render_placeholder_pdf(
        self,
        path: Path,
        mime_type: str,
        output_path: Path,
    ) -> None:
        image = self._render_placeholder_image(path, mime_type, (1240, 1754))
        image.save(output_path, format="PDF", resolution=150.0)

    def _render_placeholder_image(
        self,
        path: Path,
        mime_type: str,
        size: tuple[int, int],
    ) -> Image.Image:
        width, height = size
        image = Image.new("RGB", (width, height), color=(246, 248, 251))
        draw = ImageDraw.Draw(image)

        title_font = self._load_font(max(28, width // 12))
        heading_font = self._load_font(max(18, width // 32))
        body_font = self._load_font(max(16, width // 38))

        extension_label = self._display_label(path, mime_type)
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

    def _display_label(self, path: Path, mime_type: str) -> str:
        if path.suffix:
            return path.suffix.lstrip(".").upper()[:12] or "FILE"
        return self._fallback_extension_label(mime_type)

    def _fallback_extension_label(self, mime_type: str) -> str:
        subtype = mime_type.split("/", 1)[-1]
        cleaned = subtype.replace("+xml", "").replace("x-", "")
        return cleaned.upper()[:12] or "FILE"

    def _load_font(self, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        try:
            return ImageFont.truetype(
                font=settings.THUMBNAIL_FONT_NAME,
                size=size,
                layout_engine=ImageFont.Layout.BASIC,
            )
        except Exception:
            return ImageFont.load_default()
