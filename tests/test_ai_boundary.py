"""Tests for the AI agent boundary layer and domain-model isolation."""

import ast
from pathlib import Path

from book_sorting.ai.boundary import StubAgentBoundary
from book_sorting.discovery.media_types import MediaKind
from book_sorting.models.domain import BookGroup, DiscoveredFile


def test_stub_agent_boundary_returns_classification() -> None:
    """Verify the stub boundary returns a classification-shaped result.

    Goal: Confirm ``StubAgentBoundary.research_book`` returns a usable
    ``Classification`` without calling external AI services.
    Expected result: Result has ``author`` and ``confidence`` set to ``None``.
    On Failure: Stub boundary contract changed or ``research_book`` no longer
    returns a ``Classification`` instance.
    """
    boundary = StubAgentBoundary()
    group = BookGroup(
        group_id="g0",
        files=[
            DiscoveredFile(path=Path("sample.epub"), media_kind=MediaKind.EBOOK),
        ],
    )
    result = boundary.research_book(group)
    assert result.author is None
    assert result.confidence is None


def test_domain_models_have_no_openai_imports() -> None:
    """Ensure domain models remain free of OpenAI SDK dependencies.

    Goal: Enforce architectural separation by scanning model modules for
    any ``openai`` import statements.
    Expected result: No file under ``book_sorting/models`` imports
    ``openai`` directly or transitively via ``from`` clauses.
    On Failure: A model module gained an OpenAI import, breaking the
    intended AI boundary isolation.
    """
    root = Path(__file__).resolve().parents[1] / "src" / "book_sorting" / "models"
    for path in root.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert "openai" not in alias.name
            elif isinstance(node, ast.ImportFrom) and node.module:
                assert "openai" not in node.module
