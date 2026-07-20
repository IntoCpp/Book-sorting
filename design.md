# Design

## Overview

This document describes the implementation strategy for the Book Sorting Tool.

The project requirements are defined in [requirements.md](./requirements.md).

The project overview and intended workflow are described in [README.md](./README.md).

The AI runtime uses the [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/). The OpenAI API key is loaded from a `.env` file (see [`.env.example`](./.env.example)).

Core domain logic (classification, copy planning, file operations) remains independent from the AI platform. The SDK is an implementation detail accessed through a defined application boundary.

---

## Configuration

### Project YAML

User-facing paths are configured in [`config.yaml`](./config.yaml):

| Key | Description | Default (testing) |
|-----|-------------|-------------------|
| `source_folder` | Directory containing unsorted books | `./input_test_data` |
| `output_folder` | Destination for the organized library | `./output_test_data` |

The application loads this file at startup. Users copy and edit it for their own library paths.

### Environment

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | API key for the OpenAI Agents SDK (stored in `.env`, not committed) |

---

## High-Level Design

The application is organized as a sequence of processing stages.

Each stage has a clear responsibility and communicates through explicit data structures.

The main workflow is:

```text
File Discovery
      ↓
Exclude Previously Processed
      ↓
File Grouping
      ↓
Metadata Extraction
      ↓
AI-Assisted Research
      ↓
Book Classification
      ↓
Copy Planning
      ↓
Human Review
      ↓
File Execution
      ↓
Update Processing History
      ↓
Reporting
```

Processing history has two touch points in the pipeline:

* **Exclude Previously Processed** — runs early, immediately after file discovery. Reads the persistent processing history and removes already-sorted files from the working set before grouping and classification begin.
* **Update Processing History** — runs late, after file execution succeeds. Writes new records for successfully copied files. This corresponds to [Step 10](#step-10---processing-history) in the implementation plan.

On a subsequent run, the early exclusion stage prevents duplicate work even though the history was saved at the end of the previous run.

The workflow should separate:

* Information gathering.
* AI reasoning.
* Classification.
* Planning.
* File operations.

The system must generate a copy plan before modifying files.

AI interaction should be isolated from the rest of the application as much as practical.

External capabilities such as web search and file metadata extraction should be exposed through well-defined interfaces.

---

## Agent-Reusable Tools

Functionality is implemented as discrete tools that an agent can call. This supports reuse within this project and in other agent-based projects.

Examples of tool boundaries:

| Tool | Responsibility |
|------|----------------|
| `scan_source` | Discover files in the configured source folder |
| `extract_metadata` | Read filenames, tags, and `.nfo` descriptions |
| `search_web` | Look up missing book information |
| `classify_book` | Produce author, series, title, and confidence |
| `generate_copy_plan` | Build destination paths without modifying files |
| `execute_copy` | Apply an approved copy plan |
| `write_report` | Summarize actions, warnings, and errors |

### External Tools and MCP

When an external tool exists for a capability — via MCP or another integration — the project uses that tool instead of building a custom implementation. Examples:

* **File search / inspection** — use an MCP file-system or search tool when available.
* **Web search** — use an MCP web-search tool when available.
* **Report writing** — use an MCP or SDK report tool when available.

Custom implementations are reserved for domain-specific logic (grouping, classification, copy planning) that has no suitable external tool.

---

## Testing Requirements

* The project uses PyTest as its test framework.
* Tests must be executable through uv run pytest.
* Use the `show` fixture in tests to print useful context (paths, extracted fields) when running `uv run pytest -v`.
* New functionality must include appropriate automated tests.
* Tests must cover the deterministic/non-AI parts of the application.
* Tests should not require live external AI services unless explicitly designated as integration tests.
* The test suite must be runnable locally without manual setup beyond the documented uv environment.

The implementation plan must include tests as part of each feature implementation, not as a final project phase.

---

# Detailed Design

## Step 1 - Project Skeleton

### Objective

Create the initial project structure.

### Implementation

Create the core project areas for:

* Configuration.
* Domain models.
* Workflow orchestration.
* File discovery.
* Metadata extraction.
* AI interaction.
* Research.
* Classification.
* Copy planning.
* File execution.
* Reporting.
* Tests.

The initial workflow should execute a minimal end-to-end path.

Load `config.yaml` for source and output paths. Load `OPENAI_API_KEY` from `.env`.

The AI platform must not be embedded into the domain model.

### Validation

The application starts and executes the initial workflow successfully.

### How to Test

1. Copy `.env.example` to `.env` and set a valid `OPENAI_API_KEY`.
2. Place at least one test file in `./input_test_data`.
3. Run the application entry point.
4. Confirm it reads `config.yaml`, discovers the test file, and completes without error.

---

## Step 2 - File Discovery

### Objective

Discover all relevant files in the source directory.

### Implementation

Recursively scan the source directory configured in `config.yaml`.

Collect the information required to identify and process files.

The discovery stage must not modify the source directory.

### Validation

The complete set of relevant files is discovered.

### How to Test

1. Add several files (e-books, audiobooks, and non-book files) to `./input_test_data`.
2. Run the discovery stage in isolation.
3. Confirm all relevant media files are found and non-media files are excluded.

---

## Step 3 - File Grouping

### Objective

Identify files that belong to the same book.

### Implementation

Create logical book groups.

The grouping logic should support:

* Single-file books.
* Audiobooks composed of multiple files.
* Related files located in directories.

Grouping should initially rely on deterministic rules.

AI should not be required for basic file grouping.

### Validation

Known multi-file books are grouped together correctly.

### How to Test

1. Place a multi-file audiobook (several `.mp3` or `.m4b` files) in a single subdirectory of `./input_test_data`.
2. Run the grouping stage.
3. Confirm all files in the directory are assigned to one book group.

---

## Step 4 - Metadata Extraction

### Objective

Gather available book information before using AI.

### Implementation

Extract information from available sources, including:

* File names.
* Directory names.
* Ebook metadata.
* Audio metadata.
* **`.nfo` files** — text files with the `.nfo` extension found alongside book files. These often contain an extensive description of the book or series (author, title, series name, plot summary). When a `.nfo` file is present in a book folder, its content is parsed and used as a primary metadata source. Web search is not required when `.nfo` data is sufficient.

The result should represent partial information.

Missing information is expected.

### Validation

Available metadata is extracted and associated with the correct book group.

### How to Test

1. Create a test folder in `./input_test_data` with a book file and a companion `.nfo` file containing author, series, and title.
2. Run the metadata extraction stage.
3. Confirm the `.nfo` content is parsed and attached to the book group.
4. Confirm no web-search request is triggered for that group.

---

## Step 5 - AI-Assisted Research

### Objective

Complete missing or uncertain book information.

### Implementation

Use an OpenAI Agents SDK agent to analyze the information collected for a book group.

The agent may use external services, including web search via MCP tools, when additional information is required.

Skip web research when `.nfo` files or other local metadata already provide sufficient identification.

The AI interaction should be performed through an abstraction that allows the underlying agent platform to be changed.

The AI should be able to use:

* File names.
* File lists.
* Extracted metadata.
* `.nfo` descriptions.
* File content when appropriate.
* External research.

The result must be structured data rather than free-form text.

### Validation

Known books can be identified from incomplete or poor-quality input.

### How to Test

1. Place a poorly named book file (no `.nfo`) in `./input_test_data`.
2. Run the research stage.
3. Confirm the agent returns structured metadata (author, series, title) with a confidence score.

---

## Step 6 - Book Classification

### Objective

Determine the normalized identity and organization of each book.

### Implementation

Produce a classification containing the information required to organize the book.

The classification should include:

* Author.
* Series.
* Series order.
* Book title.
* Confidence.

The classification process should be independent from the AI runtime.

Low-confidence classifications must be explicitly identifiable.

### Validation

The same book information produces a consistent classification.

### How to Test

1. Feed a known book group (with complete metadata) into the classification stage twice.
2. Confirm both runs produce identical author, series, order, and title.

---

## Step 7 - Copy Planning

### Objective

Generate a complete plan describing the future library structure.

### Implementation

Convert classifications into destination paths under the configured `output_folder`.

The Copy plan must be created without modifying files.

The plan should identify:

* Source files.
* Destination paths.
* Conflicts.
* Warnings.
* Items requiring review.

The copy plan should be serializable so it can be inspected or persisted.

### Validation

A complete copy plan is generated without file operations.

### How to Test

1. Run the copy-planning stage against a classified book group.
2. Inspect the serialized plan.
3. Confirm destination paths follow `Author/Series/NN - Title/` (or `Author/Standalone/Title/`).
4. Confirm no files were created or moved in `./output_test_data`.

---

## Step 8 - Human Review

### Objective

Allow the user to review uncertain or potentially problematic results.

### Implementation

Provide a review mechanism independent from the AI platform and user interface.

The review process must expose:

* Classifications.
* Confidence.
* Planned destinations.
* Warnings.
* Conflicts.

The user must be able to approve or reject the proposed operation.

### Validation

The copy plan can be reviewed before execution.

### How to Test

1. Generate a copy plan that includes a low-confidence classification.
2. Present the plan for review.
3. Confirm the user can approve or reject individual items.

---

## Step 9 - File Execution

### Objective

Apply an approved copy plan.

### Implementation

Create missing destination directories under `output_folder`.

Copy the files according to the approved plan.

The execution layer must not perform AI reasoning.

Failures must be reported without hiding partially completed operations.

### Validation

Approved copies are applied correctly.

### How to Test

1. Approve a copy plan for one book group.
2. Run the execution stage.
3. Confirm files appear under `./output_test_data` in the expected structure.
4. Confirm source files in `./input_test_data` are unchanged.

---

## Step 10 - Processing History

### Objective

Track files that have been successfully processed.

### Implementation

Maintain persistent processing history outside of the source directory.

For each successfully processed source file, record enough information to identify it during future executions.

The processing history must be updated only after the corresponding file operation has completed successfully.

**Read vs write timing:** History is consulted early and updated late:

* **Read (exclude)** — During file discovery or immediately afterward, load the processing history and exclude previously processed files from the working set. This is the *Exclude Previously Processed* stage in the high-level workflow.
* **Write (save)** — After file execution completes successfully, append records for the copied files. This is the *Update Processing History* stage in the high-level workflow.

These are two stages in the pipeline, not a single step that runs only at the end.

The tracking mechanism should be isolated from the file execution logic.

The design should allow the tracking strategy to evolve without changing the classification and planning stages.

### Validation

A successfully processed file is recorded.

A subsequent execution does not process the same file again.

A file that failed to be processed remains eligible for a future execution.

### How to Test

1. Process and copy a file successfully.
2. Run the full workflow again on the same source folder.
3. Confirm the previously copied file is skipped.
4. Confirm a file that failed to copy on the first run is still eligible.

---

## Step 11 - Reporting

### Objective

Provide a clear summary of the operation.

### Implementation

Generate a report containing:

* Books processed.
* Books skipped.
* Files copied.
* Warnings.
* Errors.
* Low-confidence classifications.

Reporting should be independent from the AI platform. Use an external report tool via MCP when one is available.

### Validation

The report accurately describes the operation.

### How to Test

1. Run a full workflow that processes, skips, and warns on at least one item each.
2. Generate the report.
3. Confirm all three categories appear in the output.

---

## Step 12 - Platform and Capability Isolation

### Objective

Keep the application independent from a specific AI platform.

### Implementation

AI agent execution is provided by the OpenAI Agents SDK, accessed through a defined application boundary.

External capabilities such as web search, file inspection, and metadata extraction should be exposed through replaceable interfaces.

Prefer MCP tools for external capabilities (web search, file search, report writing) when they are available.

Platform-specific implementation must remain localized.

The system should be able to replace the OpenAI Agents SDK without requiring changes to the core domain and file organization logic.

### Validation

The core workflow can be tested without requiring a live AI call (mock the agent boundary).

---

## Step 13 - Quality Improvements

### Objective

Improve reliability and usability after the core workflow is stable.

### Possible Enhancements

* Dry-run mode.
* Caching.
* Duplicate detection.
* Cover extraction.
* OCR.
* Checkpoints.
* Resume after interruption.
* Parallel processing.

Enhancements should be added without changing the core workflow responsibilities.

---

## Testing

The project is developed incrementally. Each step above includes **Validation** criteria and a **How to Test** procedure.

### General Setup

1. Install dependencies with uv: `uv sync`
2. Copy [`.env.example`](./.env.example) to `.env` and set `OPENAI_API_KEY`.
3. Use the default test folders from [`config.yaml`](./config.yaml):
   * Source: `./input_test_data`
   * Output: `./output_test_data`

### Running Tests

Run the full test suite:

```text
uv run pytest
```

Run tests for a specific module:

```text
uv run pytest tests/test_config.py
```

As implementation progresses, each workflow stage should be runnable in isolation for development and debugging. The **How to Test** subsections in each step above are the authoritative test procedures.

Update this section and the per-step instructions whenever a new stage is implemented or its interface changes.

### End-to-End Smoke Test

Once all stages are implemented:

1. Place a small mixed collection (one e-book, one multi-file audiobook, one folder with a `.nfo` file) in `./input_test_data`.
2. Run the full workflow: `uv run book-sort`
3. Review the copy plan, approve it, and execute.
4. Confirm the organized library appears under `./output_test_data`.
5. Run the workflow again and confirm previously sorted files are skipped.
6. Read the generated report and confirm it matches the actions taken.
