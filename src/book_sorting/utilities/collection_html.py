"""Generate a self-contained HTML catalog for a book collection."""

from __future__ import annotations

import html
from pathlib import Path

from book_sorting.utilities.collection_data import BookCollection, CollectionBook

_DEFAULT_TITLE = "My Book Collection"


def render_book_collection_html(collection: BookCollection) -> str:
    """Render the complete HTML document for a book collection."""
    author_sections = "\n".join(
        _render_author_section(author, collection.books_by_author[author])
        for author in collection.authors
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(_DEFAULT_TITLE)}</title>
  <style>
{_CSS}
  </style>
</head>
<body>
  <header class="page-header">
    <h1>{html.escape(_DEFAULT_TITLE)}</h1>
    <section class="summary">
      <p><strong>Authors:</strong> {len(collection.authors)}</p>
      <p><strong>Books:</strong> {collection.total_books}</p>
    </section>
  </header>
  <main>
{author_sections}
  </main>
  <script>
{_PATH_COPY_SCRIPT}
{_SORT_SCRIPT}
  </script>
</body>
</html>
"""


def write_book_collection_html(collection: BookCollection, output_path: Path) -> None:
    """Write a fully regenerated HTML catalog to ``output_path``."""
    output_path.write_text(render_book_collection_html(collection), encoding="utf-8")


def folder_path_for_display(path: Path) -> str:
    """Return a native path string for clipboard (backslashes on Windows)."""
    return str(path.resolve())


def _render_author_section(author: str, books: list[CollectionBook]) -> str:
    rows = "\n".join(_render_book_row(book) for book in books)
    return f"""    <section class="author-section">
      <h2>{html.escape(author)}</h2>
      <div class="table-wrap">
        <table class="book-table">
          <thead>
            <tr>
              <th>Cover</th>
              <th class="sortable" data-col="1">Title</th>
              <th class="sortable" data-col="2">Series</th>
              <th class="sortable" data-col="3">Media</th>
              <th>Description</th>
            </tr>
          </thead>
          <tbody>
{rows}
          </tbody>
        </table>
      </div>
    </section>"""


def _render_book_row(book: CollectionBook) -> str:
    folder_path = folder_path_for_display(book.path)
    folder_path_attr = html.escape(folder_path, quote=True)
    title_cell = f"""              <span class="book-title">{html.escape(book.title)}</span>
              <div class="book-actions" data-folder-path="{folder_path_attr}">
                <button type="button" class="btn-path btn-copy-path" onclick="copyBookPath(this)">Copy path</button>
              </div>"""
    cover_cell = ""
    if book.cover_data_uri:
        cover_cell = (
            f'<img src="{book.cover_data_uri}" alt="{html.escape(book.title)} cover">'
        )
    description = html.escape(book.description).replace("\n", "<br>")
    return f"""            <tr>
              <td class="cover">{cover_cell}</td>
              <td class="title-cell">{title_cell}</td>
              <td>{html.escape(book.series or "")}</td>
              <td>{html.escape(book.media_label)}</td>
              <td class="description">{description}</td>
            </tr>"""


_CSS = """
    :root {
      color-scheme: light dark;
      --bg: #f7f7f9;
      --card: #ffffff;
      --text: #1f2937;
      --muted: #6b7280;
      --border: #d1d5db;
      --accent: #2563eb;
      --row-alt: #f3f4f6;
    }
    @media (prefers-color-scheme: dark) {
      :root {
        --bg: #111827;
        --card: #1f2937;
        --text: #f9fafb;
        --muted: #9ca3af;
        --border: #374151;
        --accent: #60a5fa;
        --row-alt: #273244;
      }
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.5;
    }
    .page-header, main {
      max-width: 1200px;
      margin: 0 auto;
      padding: 1.5rem;
    }
    h1, h2 { margin: 0 0 1rem; }
    .summary {
      display: flex;
      gap: 2rem;
      color: var(--muted);
    }
    .author-section {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 1rem;
      margin-bottom: 1.5rem;
      box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
    }
    .table-wrap {
      overflow: auto;
      max-height: 70vh;
    }
    table {
      width: 100%;
      border-collapse: collapse;
    }
    thead th {
      position: sticky;
      top: 0;
      background: var(--card);
      border-bottom: 2px solid var(--border);
      text-align: left;
      padding: 0.75rem;
      z-index: 1;
    }
    th.sortable { cursor: pointer; }
    th.sortable:hover { color: var(--accent); }
    td {
      border-bottom: 1px solid var(--border);
      padding: 0.75rem;
      vertical-align: top;
    }
    tbody tr:nth-child(even) { background: var(--row-alt); }
    td.cover {
      width: 90px;
      text-align: center;
    }
    td.cover img {
      max-width: 72px;
      max-height: 108px;
      border-radius: 4px;
      object-fit: cover;
    }
    td.title-cell .book-title { display: block; font-weight: 600; margin-bottom: 0.35rem; }
    .book-actions { display: flex; flex-wrap: wrap; gap: 0.35rem; }
    .btn-path {
      font: inherit;
      font-size: 0.8rem;
      padding: 0.2rem 0.5rem;
      border: 1px solid var(--border);
      border-radius: 6px;
      background: var(--row-alt);
      color: var(--text);
      cursor: pointer;
    }
    .btn-path:hover { border-color: var(--accent); color: var(--accent); }
    .btn-path.copied { border-color: var(--accent); color: var(--accent); }
    td.description { max-width: 40rem; }
    a { color: var(--accent); text-decoration: none; }
    a:hover { text-decoration: underline; }
    @media (max-width: 800px) {
      .summary { flex-direction: column; gap: 0.5rem; }
      td.description { max-width: none; }
    }
"""

_PATH_COPY_SCRIPT = """
    function folderPathFromButton(button) {
      const container = button.closest(".book-actions");
      return container ? container.dataset.folderPath : "";
    }

    async function copyBookPath(button) {
      const path = folderPathFromButton(button);
      if (!path) return;
      let copied = false;
      if (navigator.clipboard && navigator.clipboard.writeText) {
        try {
          await navigator.clipboard.writeText(path);
          copied = true;
        } catch (err) {
          copied = false;
        }
      }
      if (!copied) {
        const area = document.createElement("textarea");
        area.value = path;
        area.setAttribute("readonly", "");
        area.style.position = "fixed";
        area.style.left = "-9999px";
        document.body.appendChild(area);
        area.select();
        copied = document.execCommand("copy");
        document.body.removeChild(area);
      }
      if (copied) {
        const label = button.textContent;
        button.textContent = "Copied";
        button.classList.add("copied");
        window.setTimeout(() => {
          button.textContent = label;
          button.classList.remove("copied");
        }, 1500);
      }
    }
"""

_SORT_SCRIPT = """
    function sortKeyForCell(cell) {
      const title = cell.querySelector(".book-title");
      if (title) return title.textContent.trim().toLowerCase();
      return cell.textContent.trim().toLowerCase();
    }

    document.querySelectorAll("th.sortable").forEach((header) => {
      header.addEventListener("click", () => {
        const table = header.closest("table");
        const tbody = table.querySelector("tbody");
        const col = Number(header.dataset.col);
        const ascending = header.dataset.asc !== "true";
        const rows = Array.from(tbody.querySelectorAll("tr"));
        rows.sort((left, right) => {
          const a = sortKeyForCell(left.children[col]);
          const b = sortKeyForCell(right.children[col]);
          if (a < b) return ascending ? -1 : 1;
          if (a > b) return ascending ? 1 : -1;
          return 0;
        });
        rows.forEach((row) => tbody.appendChild(row));
        table.querySelectorAll("th.sortable").forEach((item) => delete item.dataset.asc);
        header.dataset.asc = ascending ? "true" : "false";
      });
    });
"""
