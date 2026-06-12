from __future__ import annotations

from pathlib import Path

from django.conf import settings
from documents.parsers import DocumentParser
from documents.parsers import ParseError

from paperless_generic_file_parser.common import build_search_text
from paperless_generic_file_parser.common import metadata_entries
from paperless_generic_file_parser.common import render_placeholder_image
from paperless_generic_file_parser.common import render_placeholder_pdf


class LegacyGenericFileParser(DocumentParser):
    def get_settings(self):
        return {}

    def parse(self, document_path: Path, mime_type: str, file_name=None):
        try:
            path = Path(document_path)
            self.text = build_search_text(path, mime_type)
            archive_path = self.tempdir / "generic-preview.pdf"
            render_placeholder_pdf(
                path,
                mime_type,
                archive_path,
                settings.THUMBNAIL_FONT_NAME,
            )
            self.archive_path = archive_path
        except Exception as exc:
            raise ParseError(f"Generic file parser failed for {document_path}: {exc}") from exc

    def get_thumbnail(self, document_path: Path, mime_type: str, file_name=None):
        path = Path(document_path)
        thumbnail_path = self.tempdir / "thumb.webp"
        image = render_placeholder_image(
            path,
            mime_type,
            (500, 700),
            settings.THUMBNAIL_FONT_NAME,
        )
        image.save(thumbnail_path, format="WEBP")
        return thumbnail_path

    def get_page_count(self, document_path, mime_type):
        return 1

    def extract_metadata(self, document_path, mime_type):
        try:
            return metadata_entries(Path(document_path), mime_type)
        except Exception:
            return []
