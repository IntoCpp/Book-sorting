# Book Sorting Tool

Sort mixed collections of e-books and audiobooks into a structured library using AI-assisted metadata discovery.

The tool scans a source folder, gathers information from filenames and file metadata, optionally performs web research, and builds a copy plan that organizes the files into a consistent directory structure.

## Configuration

Input and output folders are set in a project YAML config file: [`config.yaml`](./config.yaml).

Default values are provided for testing:

| Setting | Default |
|---------|---------|
| `source_folder` | `./input_test_data` |
| `output_folder` | `./output_test_data` |

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

The application is implemented as a LangGraph workflow.

```text
Scan source folder
        ↓
Exclude files previously sorted (saved changes from last run)
        ↓
Group related files
        ↓
Extract metadata (including .nfo files when present)
        ↓
Research missing information
        ↓
Classify books
        ↓
Generate move plan
        ↓
Human review (optional)
        ↓
Execute copy
        ↓
Save changes for next run
        ↓
Generate report
```

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
