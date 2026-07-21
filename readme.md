# Book Sorting Tool

Sort mixed collections of e-books and audiobooks into a structured library using AI-assisted metadata discovery.

The tool scans a source folder, gathers information from filenames and file metadata, optionally performs web research, and builds a copy plan that organizes the files into a consistent directory structure.

## Configuration

Input and output folders are set in a project YAML config file: [`config.yaml`](./config.yaml).

Use `uv run book-sort --test` for test mode (`source_folder_test`, `output_folder_test`). Omit `--test` for production paths.

| Setting | Test mode (`--test`) | Production |
|---------|----------------------|------------|
| Source | `source_folder_test` | `source_folder_prod` |
| Output | `output_folder_test` | `output_folder_prod` |
| Processing history | `processing_history_test` | `processing_history_prod` |

Copy [`.env.example`](./.env.example) to `.env` and set your OpenAI API key. The application uses the [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/) as its AI runtime.

## Folder Structure

```text
Author/
    Series/
        01 - Book Title/
            ...
```

Standalone books are stored in a dedicated folder:

```text
Author/
    Standalone/
        Book Title/
            ...
```

## Workflow

The application is an AI-assisted, staged workflow for organizing ebook and audiobook files.

```text
Scan source folder
        ↓
Exclude files previously sorted (read processing history)
        ↓
Group related files
        ↓
Extract metadata (including .nfo files when present)
        ↓
Research missing information
        ↓
Classify books
        ↓
Generate copy plan
        ↓
Human review (optional)
        ↓
Execute copy
        ↓
Save changes for next run (update processing history)
        ↓
Generate report
```

Processing history is **read early** (exclude previously sorted files right after scanning) and **written late** (save records after successful copy). See [design.md](./design.md) for details.

Each stage is independent and can be tested separately.

Implementation details are described in [design.md](./design.md).

## Input Sources

Book identification may use:

* File and directory names
* File metadata and audio tags
* **`.nfo` files** — some source folders contain a text file with the `.nfo` extension that provides an extensive description of the book or series. When present, this local description is preferred and web search is not required.
* Web research (when local information is insufficient)
* Processing history from previous runs

## Agent-Reusable Tools

Where it makes sense, functionality is implemented as discrete, reusable tools (for example: scan files, extract metadata, search the web, write a report). These tools can be invoked by the workflow agent in this project or reused by agents in other projects.

When an external capability is available — via MCP or another integration — the project uses that tool rather than reimplementing it.


## Python Environment and Execution

* Python dependencies and the project environment are managed using uv.
* The project must be executed using uv run.
* Tests must be run using uv run.
* Do not introduce pip, venv, or alternative environment-management workflows unless explicitly requested.

For example:

`uv run pytest`


## Testing

The project supports incremental testing between each development step. Each design step includes validation criteria and instructions for how to test that step in isolation.

See the [Testing](./design.md#testing) section in [design.md](./design.md) for the current test procedures. This documentation is updated as development progresses.

## Goals

* Support e-books and audiobooks.
* Work with badly named files whenever possible.
* Use AI and web research to determine author, series, and title.
* Avoid moving files when confidence is too low.
* Produce deterministic and repeatable results.
* Allow manual review before applying changes.
* Save files sorted to avoid duplicate work on future run.
* Generate a report describing all actions performed.

## History

- **2026-07-21** — Added `--test` mode and separate test/production paths and processing history in `config.yaml`.
- **2026-07-21** — Run reports are appended to `run-report.txt` in the output folder to keep a history of each run.
- **2026-07-21** — Windows file copies use extended-length paths when destinations exceed the usual `MAX_PATH` limit.
