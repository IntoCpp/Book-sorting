# Book Sorting Tool

Sort mixed collections of e-books and audiobooks into a structured library using AI-assisted metadata discovery.

The tool scans a source folder, gathers information from filenames and file metadata, optionally performs web research, and builds a move plan that organizes the files into a consistent directory structure.

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
Exclude files previously sorted
        ↓
Group related files
        ↓
Extract metadata
        ↓
Research missing information
        ↓
Classify books
        ↓
Generate move plan
        ↓
Human review (optional)
        ↓
Execute moves
        ↓
Save changes for next run
        ↓
Generate report
```

Each stage is independent and can be tested separately.

Implementation details are described in [design.md](./design.md).

## Goals

* Support e-books and audiobooks.
* Work with badly named files whenever possible.
* Use AI and web research to determine author, series, and title.
* Avoid moving files when confidence is too low.
* Produce deterministic and repeatable results.
* Allow manual review before applying changes.
* Save files sorted to avoid duplicate work on future run.
* Generate a report describing all actions performed.
