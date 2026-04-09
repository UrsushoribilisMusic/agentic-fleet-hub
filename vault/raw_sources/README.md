# Raw Sources

This directory is for local, potentially large or sensitive source material that should feed LLM-maintained knowledge bases without being committed to git.

Current planned use:
- `robotross/mexico_wood_marking/` for production logs and related artifacts from the Mexico wood-marking runs

Rules:
- Treat files here as immutable raw evidence.
- Do not edit source files in place.
- Build parsed summaries, wiki pages, and ledgers elsewhere in the repository.
- Keep filenames descriptive and preserve original timestamps where possible.
