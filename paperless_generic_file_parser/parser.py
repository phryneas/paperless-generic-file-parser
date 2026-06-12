from __future__ import annotations
import shutil
import tempfile
from pathlib import Path
from types import TracebackType
from typing import TYPE_CHECKING
from typing import Self

from django.conf import settings
from documents.parsers import ParseError
from paperless.parsers import MetadataEntry
from paperless.parsers import ParserContext

from paperless_generic_file_parser.common import SUPPORTED_MIME_TYPES
from paperless_generic_file_parser.common import build_search_text
from paperless_generic_file_parser.common import metadata_entries
from paperless_generic_file_parser.common import render_placeholder_image
from paperless_generic_file_parser.common import render_placeholder_pdf
from paperless_generic_file_parser import __version__

if TYPE_CHECKING:
    import datetime

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
            self._text = build_search_text(path, mime_type)

            if produce_archive:
                archive_path = self._tempdir / "generic-preview.pdf"
                render_placeholder_pdf(
                    path,
                    mime_type,
                    archive_path,
                    settings.THUMBNAIL_FONT_NAME,
                )
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
        image = render_placeholder_image(
            path,
            mime_type,
            (500, 700),
            settings.THUMBNAIL_FONT_NAME,
        )
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
            return [
                MetadataEntry(**entry)
                for entry in metadata_entries(Path(document_path), mime_type)
            ]
        except Exception:
            return []
