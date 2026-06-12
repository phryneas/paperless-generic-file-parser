from __future__ import annotations

from django.apps import AppConfig


def generic_file_consumer_declaration(sender, **kwargs):
    from paperless_generic_file_parser.common import SUPPORTED_MIME_TYPES
    from paperless_generic_file_parser.legacy import LegacyGenericFileParser

    return {
        "parser": LegacyGenericFileParser,
        "weight": 15,
        "mime_types": SUPPORTED_MIME_TYPES,
    }


class PaperlessGenericFileParserConfig(AppConfig):
    name = "paperless_generic_file_parser"

    def ready(self):
        from documents.signals import document_consumer_declaration

        document_consumer_declaration.connect(
            generic_file_consumer_declaration,
            dispatch_uid="paperless_generic_file_parser.consumer_declaration",
        )
