"""File discovery stage exports.

Re-exports the scan stage and media-type classification helper.
"""

from book_sorting.discovery.media_types import classify_media_path
from book_sorting.discovery.scan import discover_source_files

__all__ = ["classify_media_path", "discover_source_files"]
