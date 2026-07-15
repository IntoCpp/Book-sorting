# Requirements

## Purpose

The Book Sorting Tool shall organize mixed collections of e-books and audiobooks into a structured library.

The source collection may contain files and directories with inconsistent names and layouts.

The application shall determine the correct author, series, and book information and organize the files accordingly.

---

## Input Requirements

### Source Folder

The application shall accept a source directory.

The source directory may contain:

* Files directly under the root.
* Nested subdirectories.
* Single-file books.
* Books composed of multiple files.
* Mixed e-book and audiobook formats.
* Some books may be duplicate under an alternate folder name or an alternate format.

The source directory structure shall not be assumed to be meaningful.

### Supported Media

The application shall support:

* E-books.
* Audiobooks.

The application shall support collections containing both.

### Input Information

Book identification may rely on:

* File names.
* Directory names.
* File metadata.
* Audio tags.
* Contents of files.
* Information obtained from web searches.
* Result from previous run, to avoid sorting a file that was already sorted previously.

The system shall use whatever information is available.

---

## Classification Requirements

The application shall organize books according to:

```text
Author
    Series
        Book
```

Standalone books shall be separated from books belonging to a series.

The classification shall determine:

* Author.
* Series name.
* Series order.
* Book title.

The application shall normalize naming to ensure consistent output.

---

## AI Requirements

The application shall use AI to improve classification accuracy.

The AI may use:

* File names.
* Metadata.
* File contents.
* Web searches.

The AI shall be allowed to gather external information when required.

The AI shall provide a confidence score for classifications.

Low-confidence classifications shall be identifiable.

---

## File Handling Requirements

The application shall move files from the source directory to a target directory.

The resulting directory structure shall contain subdirectories organized by:

```text
Author/
    Series/
        Book/
```

The application shall support books represented by multiple files.

Related files belonging to the same book shall remain together.

The application shall not modify the original files themselves.

---
## Processing History

The application shall record when a source file has been successfully processed and copied to the sorted library.

The processing record shall allow the application to identify files that have already been successfully processed during future runs.

On subsequent executions, previously processed files shall be excluded from normal processing unless explicitly requested otherwise.

The processing history shall be updated only after the corresponding file operation has completed successfully.

The processing history shall remain available between application executions.

---

## Safety Requirements

The application shall avoid uncertain classifications.

Low-confidence results shall be reviewable.

The user shall have the option to approve changes before files are moved.

The system shall be capable of generating a move plan before executing changes.

The application shall generate reports describing the performed actions.

---

## Development Requirements

The project shall be implemented in Python.

The project shall use LangGraph.

The project shall be maintained in GitHub.

The project shall be developed using Visual Studio Code.

The implementation shall support incremental development.

The architecture shall favor independent and testable components.

Implementation details are described in [design.md](./design.md).

---

## Non-Functional Requirements

The implementation shall prioritize:

* Reliability.
* Maintainability.
* Deterministic behavior.
* Testability.

The architecture shall support future enhancements without requiring major redesign.

---

## Future Enhancements

The design should allow future support for:

* Save sorted books on a web-page for user reference.
* OCR.
* Duplicate detection.
* Dry-run execution.
* Execution resume after interruption.
* Parallel processing.

These enhancements are optional and shall not be required by the initial implementation.

---

## Exclusions

The initial implementation does not require:

* A graphical user interface.
* Real-time processing.
* Distributed execution.
* Database storage.
* Cloud deployment.

These capabilities may be added in future versions.
