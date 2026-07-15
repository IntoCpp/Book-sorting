# Design

## Overview

This document describes the implementation strategy for the Book Sorting Tool.

The project requirements are defined in [requirements.md](./requirements.md).

The project overview and intended workflow are described in [README.md](./README.md).

The system should remain as independent as possible from any specific AI agent platform or framework.

The initial implementation may use an AI agent platform such as PI. However, the core application design must not depend on platform-specific concepts wherever practical.

The AI runtime is considered an implementation detail.

---

## High-Level Design

The application is organized as a sequence of processing stages.

Each stage has a clear responsibility and communicates through explicit data structures.

The main workflow is:

```text
File Discovery
      ↓
File Grouping
      ↓
Metadata Extraction
      ↓
AI-Assisted Research
      ↓
Book Classification
      ↓
Move Planning
      ↓
Human Review
      ↓
File Execution
      ↓
Reporting
```

The workflow should separate:

* Information gathering.
* AI reasoning.
* Classification.
* Planning.
* File operations.

The system must generate a move plan before modifying files.

AI interaction should be isolated from the rest of the application as much as practical.

External capabilities such as web search and file metadata extraction should be exposed through well-defined interfaces.

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
* Move planning.
* File execution.
* Reporting.
* Tests.

The initial workflow should execute a minimal end-to-end path.

The AI platform must not be embedded into the domain model.

### Validation

The application starts and executes the initial workflow successfully.

---

## Step 2 - File Discovery

### Objective

Discover all relevant files in the source directory.

### Implementation

Recursively scan the source directory.

Collect the information required to identify and process files.

The discovery stage must not modify the source directory.

### Validation

The complete set of relevant files is discovered.

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

The result should represent partial information.

Missing information is expected.

### Validation

Available metadata is extracted and associated with the correct book group.

---

## Step 5 - AI-Assisted Research

### Objective

Complete missing or uncertain book information.

### Implementation

Use an AI agent to analyze the information collected for a book group.

The agent may use external services, including web search, when additional information is required.

The AI interaction should be performed through an abstraction that allows the underlying agent platform to be changed.

The AI should be able to use:

* File names.
* File lists.
* Extracted metadata.
* File content when appropriate.
* External research.

The result must be structured data rather than free-form text.

### Validation

Known books can be identified from incomplete or poor-quality input.

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

---

## Step 7 - Move Planning

### Objective

Generate a complete plan describing the future library structure.

### Implementation

Convert classifications into destination paths.

The move plan must be created without modifying files.

The plan should identify:

* Source files.
* Destination paths.
* Conflicts.
* Warnings.
* Items requiring review.

The move plan should be serializable so it can be inspected or persisted.

### Validation

A complete move plan is generated without file operations.

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

The move plan can be reviewed before execution.

---

## Step 9 - File Execution

### Objective

Apply an approved move plan.

### Implementation

Create missing destination directories.

Move the files according to the approved plan.

The execution layer must not perform AI reasoning.

Failures must be reported without hiding partially completed operations.

### Validation

Approved moves are applied correctly.

---

## Step 10 - Processing History

### Objective

Track files that have been successfully processed.

### Implementation

Maintain persistent processing history outside of the source directory.

For each successfully processed source file, record enough information to identify it during future executions.

The processing history must be updated only after the corresponding file operation has completed successfully.

During file discovery or an equivalent early workflow stage, previously processed files should be excluded from normal processing.

The tracking mechanism should be isolated from the file execution logic.

The design should allow the tracking strategy to evolve without changing the classification and planning stages.

### Validation

A successfully processed file is recorded.

A subsequent execution does not process the same file again.

A file that failed to be processed remains eligible for a future execution.


---

## Step 11 - Reporting

### Objective

Provide a clear summary of the operation.

### Implementation

Generate a report containing:

* Books processed.
* Books skipped.
* Files moved.
* Warnings.
* Errors.
* Low-confidence classifications.

Reporting should be independent from the AI platform.

### Validation

The report accurately describes the operation.

---

## Step 12 - Platform and Capability Isolation

### Objective

Keep the application independent from a specific AI platform.

### Implementation

AI agent execution must be accessed through a defined application boundary.

External capabilities such as web search, file inspection, and metadata extraction should be exposed through replaceable interfaces.

Platform-specific implementation must remain localized.

The system should be able to replace the initial AI platform without requiring changes to the core domain and file organization logic.

The use of MCP services may be considered for external capabilities where appropriate.

### Validation

The core workflow can be tested without requiring a specific AI platform.

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
