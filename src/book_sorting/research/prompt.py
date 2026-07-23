"""Build prompts for AI book research."""

from __future__ import annotations

import json

from book_sorting.models.domain import BookGroup


def build_research_prompt(group: BookGroup) -> str:
    """Build the user prompt sent to the research agent.

    Args:
        group: Book group whose files and extracted metadata supply context.

    Returns:
        Instruction text followed by a JSON payload describing the group.
    """
    meta = group.metadata
    files = [str(f.path) for f in group.files]
    payload = {
        "group_id": group.group_id,
        "root_path": str(group.root_path) if group.root_path else None,
        "files": files,
        "extracted_metadata": {
            "title": meta.title if meta else None,
            "author": meta.author if meta else None,
            "series": meta.series if meta else None,
            "series_index": meta.series_index if meta else None,
            "description": meta.description if meta else None,
            "nfo_present": meta.nfo_present if meta else False,
            "field_sources": meta.field_sources if meta else {},
        },
    }
    return (
        "Identify this ebook or audiobook for library organization. "
        "Use web search when local metadata is incomplete or ambiguous. "
        "Return structured fields only.\n\n"
        f"Book group context JSON:\n{json.dumps(payload, indent=2)}"
    )
