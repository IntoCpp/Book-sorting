# Change requests

Version: 1

This file is used to contain change request(s) to do. It is a great way to work on the text before starting to implement a change.

Workflow of change requests:

- Read this file to understand the change request.
- Do an analysis and edit this file to write you work plan.
- Do not start changing code until the work plan is reviewed and approved.
- If you have questions or detect ambiguities you can ask them in this file. They will be answered in this file. On restart you must read the answers and only do the work if satisfied. If not ask more clarifications.

When all requests are done, the text is removed, except for this section.

---

## Completed: Goodreads cover images for `my_books.html` (2026-08-07)

**Implemented:** When a book folder has no local cover image, `create-book-collection` looks up cover art on Goodreads (series page first when a series name is known, then book search), downloads the image, saves it as `cover.jpg` in the output-library book folder, and embeds it in `my_books.html` as a Base64 data URI.

**CLI:** `--no-cover-fetch` disables online lookup and local cover saving.

**Files:** `utilities/goodreads_covers.py`, updates to `cover_images.py`, `collection_data.py`, and `create_book_collection.py`.
