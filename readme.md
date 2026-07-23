# Book Sorting Tool

Sort mixed collections of e-books and audiobooks into a structured library using AI-assisted metadata discovery.

The tool scans a source folder, gathers information from filenames and file metadata, optionally performs web research, and builds a copy plan that organizes the files into a consistent directory structure.

## Developing This Project with Cursor

I used this project as an opportunity to learn and evaluate **Cursor**, the AI-powered code editor. I had been using GitHub Copilot with VS Code for some time and wanted to compare the experience.

Overall, I was genuinely impressed. Rather than simply asking Cursor to generate code, I wanted to see how well it could participate in an organized software development workflow.

### Development Process

My workflow was as follows:

1. I wrote the initial requirements myself.
2. I used ChatGPT to review and refine the requirements and to produce a `design.md` document containing a detailed implementation plan. I also created a minimal `README.md`.
3. After saving the project files, I asked Cursor to analyze the project.
  - I quickly learned that Cursor generally expects a dedicated *work plan* document. Instead, I instructed it to use `design.md` as the authoritative implementation plan.
  - I also discovered Cursor Rules. I created project-specific rules describing the development workflow, specifying that this project was intended to learn Cursor, requiring the use of `uv`, asking Cursor to explain implementation decisions, and defining what should be included in the completion reports after each implementation step.
4. I asked Cursor to implement the project one step at a time, reviewing every change before moving to the next step.
5. Once development was complete, I tested the application and it worked as expected.
6. Finally, I implemented several small improvements and utility features, which are documented in the project history.



### Overall Impression

This was a surprisingly enjoyable experience.

The development process was smooth, fast, and easy to follow. The biggest bottleneck was me—I deliberately took my time to understand Cursor's workflow and frequently paused to review its decisions.

With the experience I gained from this project, I believe I could complete a similar project in a single day. I am looking forward to using Cursor on future projects.

### Cost

This project cost approximately **US$10** in Cursor usage.

Although this is a relatively small project, I had expected the cost to be somewhat lower. I also exhausted the free usage very quickly and upgraded to the **Cursor Pro** subscription (approximately **CA$30 including taxes** at the time).

### What I Liked

- At the beginning, I carefully reviewed every report and every line of generated code. As my confidence in Cursor increased, my reviews became much faster, eventually focusing primarily on the implementation reports and the unit test results.
- Because I emphasized testing from the start, Cursor consistently created and maintained unit tests throughout the project.
- Cursor automatically executed the test suite after each implementation step. Early in the project, a couple of regressions were introduced, but Cursor immediately detected the failures, fixed the issues, and reran the tests before considering the step complete.
- I appreciated that simple requests such as **"Push the changes"** resulted in a sensible Git workflow, committing and pushing the appropriate files without additional instructions.

### What I Would Do Differently Next Time

If I were starting another project with Cursor, I would improve my project rules from the beginning.

- Define clear standards for docstrings and code comments, including where they should be used and the expected level of detail. I ended up adding proper documentation near the end of the project.
- Add more detailed testing guidelines, including expectations for happy-path tests, edge cases, invalid input, boundary conditions, and regression tests.
- Establish stronger rules for logging and user feedback. I prefer applications that provide detailed diagnostic information in a dedicated test or debug mode, which makes troubleshooting significantly easier.
- Experiment with specialized Cursor agents for different responsibilities (such as implementation, testing, documentation, and code review). This project was too small to fully explore that capability.

> ### What I Did Not Like
>
> - Now that the project is complete, I find the resulting code somewhat more complex than I would have written myself. Developing it manually would almost certainly have taken **5 to 10 times longer**, but I suspect my implementation would have been more compact, with fewer folders, files, and functions. On the other hand, Cursor produced code that follows **Clean Code** principles, with excellent separation of responsibilities and small components that each do one thing well. It is something I always try to do, I can certainly appreciate its maintainability.
> - I still found myself keeping VS Code open alongside Cursor for occasional file editing and code comparisons. Old habits die hard, I guess.

## Configuration

Input and output folders are set in a project YAML config file: `[config.yaml](./config.yaml)`.

Use `uv run book-sort --test` for test mode (`source_folder_test`, `output_folder_test`). Omit `--test` for production paths.


| Setting            | Test mode (`--test`)      | Production                |
| ------------------ | ------------------------- | ------------------------- |
| Source             | `source_folder_test`      | `source_folder_prod`      |
| Output             | `output_folder_test`      | `output_folder_prod`      |
| Processing history | `processing_history_test` | `processing_history_prod` |


Copy `[.env.example](./.env.example)` to `.env` and set your OpenAI API key. The application uses the [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/) as its AI runtime.

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

- File and directory names
- File metadata and audio tags
- `.nfo` **files** — some source folders contain a text file with the `.nfo` extension that provides an extensive description of the book or series. When present, this local description is preferred and web search is not required. The source folder is never modified; when AI research retrieves metadata, it is cached into an `.nfo` file in the output library after a successful copy.
- Web research (when local information is insufficient)
- Processing history from previous runs



## Agent-Reusable Tools

Where it makes sense, functionality is implemented as discrete, reusable tools (for example: scan files, extract metadata, search the web, write a report). These tools can be invoked by the workflow agent in this project or reused by agents in other projects.

When an external capability is available — via MCP or another integration — the project uses that tool rather than reimplementing it.

## Python Environment and Execution

- Python dependencies and the project environment are managed using uv.
- The project must be executed using uv run.
- Tests must be run using uv run.
- Do not introduce pip, venv, or alternative environment-management workflows unless explicitly requested.

For example:

`uv run pytest`

## Utilities


| Command                   | Description                                                       |
| ------------------------- | ----------------------------------------------------------------- |
| `uv run book-information` | List authors and books from the production output library folder. |




## Testing

The project supports incremental testing between each development step. Each design step includes validation criteria and instructions for how to test that step in isolation.

See the [Testing](./design.md#testing) section in [design.md](./design.md) for the current test procedures. This documentation is updated as development progresses.

## Goals

- Support e-books and audiobooks.
- Work with badly named files whenever possible.
- Use AI and web research to determine author, series, and title.
- Avoid moving files when confidence is too low.
- Produce deterministic and repeatable results.
- Allow manual review before applying changes.
- Save files sorted to avoid duplicate work on future run.
- Generate a report describing all actions performed.



## History

- **2026-07-23** — AI-assisted research caches retrieved metadata in output-library `.nfo` files after successful copy; the source folder is never modified.
- **2026-07-22** — Added `book-information` utility to list authors and books from the production output folder.
- **2026-07-21** — Added `--test` mode and separate test/production paths and processing history in `config.yaml`.
- **2026-07-21** — Run reports are appended to `run-report.txt` in the output folder to keep a history of each run.
- **2026-07-21** — Windows file copies use extended-length paths when destinations exceed the usual `MAX_PATH` limit.

