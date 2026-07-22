"""Domain models for the Book Sorting Tool.

Defines core data structures for discovered files, book groups,
classifications, copy plans, and run reports.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class MediaKind(str, Enum):
    """Kind of media file discovered during scanning."""

    EBOOK = "ebook"
    AUDIOBOOK = "audiobook"


@dataclass(frozen=True)
class DiscoveredFile:
    """A single e-book or audiobook file found under the source folder.

    Attributes:
        path: Absolute path to the file on disk.
        media_kind: Whether the file is classified as an e-book or audiobook.
    """

    path: Path
    media_kind: MediaKind


@dataclass
class ExtractedMetadata:
    """Metadata fields extracted from file tags, sidecar files, or folder names.

    Attributes:
        title: Book title, if known.
        author: Author name, if known.
        series: Series name, if known.
        series_index: Position within a series, if known.
        description: Synopsis or description text, if available.
        nfo_present: True when an NFO sidecar file contributed metadata.
        field_sources: Maps each populated field name to its extraction source.
    """

    title: str | None = None
    author: str | None = None
    series: str | None = None
    series_index: str | None = None
    description: str | None = None
    nfo_present: bool = False
    field_sources: dict[str, str] = field(default_factory=dict)


@dataclass
class BookGroup:
    """A logical book unit comprising one or more discovered files.

    Attributes:
        group_id: Stable identifier derived from the grouping key.
        files: Member files belonging to this book.
        root_path: Common parent directory used for metadata extraction.
        metadata: Extracted metadata, populated by the metadata stage.
        research: External research results, populated by the research stage.
        classification: Final author/series/title assignment from classification.
    """

    group_id: str
    files: list[DiscoveredFile] = field(default_factory=list)
    root_path: Path | None = None
    metadata: ExtractedMetadata | None = None
    research: Classification | None = None
    classification: Classification | None = None


@dataclass
class Classification:
    """Author, series, and title assignment for a book group.

    Attributes:
        author: Resolved author name.
        series: Resolved series name, if applicable.
        series_order: Numeric position within the series.
        title: Resolved book title.
        confidence: Classifier confidence score between 0 and 1.
        research_notes: Free-text notes from the research stage.
        research_skipped: True when external research was not performed.
        low_confidence: True when the assignment needs human review.
    """

    author: str | None = None
    series: str | None = None
    series_order: int | None = None
    title: str | None = None
    confidence: float | None = None
    research_notes: str | None = None
    research_skipped: bool = False
    low_confidence: bool = False


@dataclass
class CopyPlanEntry:
    """A single planned file copy from source to destination.

    Attributes:
        source: Path of the file to copy.
        destination: Target path in the organized library.
        group_id: :class:`BookGroup` identifier this entry belongs to.
        requires_review: True when human approval is needed before copying.
        approved: True when the entry has been approved for execution.
    """

    source: Path
    destination: Path
    group_id: str
    requires_review: bool = False
    approved: bool = False


@dataclass
class CopyPlan:
    """Complete set of planned copy operations for a workflow run.

    Attributes:
        entries: Individual copy operations to perform.
        conflicts: Descriptions of destination path conflicts.
        warnings: Non-fatal issues detected during planning.
        review_group_ids: Group IDs flagged for human review.
    """

    entries: list[CopyPlanEntry] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    review_group_ids: list[str] = field(default_factory=list)


@dataclass
class CopyOperationResult:
    """Outcome of attempting to copy a single file.

    Attributes:
        source: Source path from the copy plan.
        destination: Intended destination path.
        copied: True when the file was copied successfully.
        skipped: True when the copy was intentionally skipped.
        error: Error message when the copy failed.
    """

    source: Path
    destination: Path
    copied: bool = False
    skipped: bool = False
    error: str | None = None


@dataclass
class RunReport:
    """Summary statistics and messages produced at the end of a workflow run.

    Attributes:
        discovered_count: Total files found during discovery.
        group_count: Number of book groups created.
        books_processed: Groups that were fully processed.
        books_skipped: Groups skipped during the run.
        files_copied: Files successfully copied to the output library.
        files_skipped_history: Files skipped because they appear in processing history.
        warnings: Warning messages collected across stages.
        errors: Error messages collected across stages.
        low_confidence: Group IDs with low-confidence classifications.
        message: Human-readable summary printed at the end of a run.
    """

    discovered_count: int = 0
    group_count: int = 0
    books_processed: int = 0
    books_skipped: int = 0
    files_copied: int = 0
    files_skipped_history: int = 0
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    low_confidence: list[str] = field(default_factory=list)
    message: str = ""
