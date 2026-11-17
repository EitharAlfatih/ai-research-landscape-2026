# Repository instructions

These instructions complement the user's global Codex instructions. Keep plans and writing brief; implement only approved changes.

## Project and ownership

This project aims to produce a scientific report on AI research directions and temporal changes, with particular interest in AI safety. The initial corpus is cs.AI-tagged arXiv metadata, January 2022–October 2026, including cross-listings and applications; it does not represent all AI research.

The researcher owns scope, methodology, interpretation, and conclusions. Do not turn implementation choices into research decisions. Propose simple alternatives when a method is undecided. The researcher runs tests, collection, and analysis notebooks; do not execute them unless explicitly asked.

## Start and finish a session

- Consult `IMPLEMENTATION.md` when planning implementation work, and read `HANDOFF.md` for session context. Inspect relevant files and reconcile discrepancies with the researcher.
- The researcher owns the roadmap and decides task and phase completion.
- Do not independently modify `IMPLEMENTATION.md`, change statuses, or update `HANDOFF.md`. This includes automatic end-of-session updates.
- Suggest tasks, progress updates, and roadmap changes in conversation. Obtain explicit approval before applying them.
- Approval to change implementation code does not authorize planning-document edits.
- Never mark a phase complete merely because code exists. Distinguish implementation completion, execution verification, and researcher acceptance; state the available evidence.
- Keep `README.md` as the project entry point and running guide. `PLAN.md` is the unchanged migration source; do not delete or replace it before the researcher reviews the migration and approves its disposition.

## Conventions

- `arxiv_collection.py`: collection helpers; `tests/`: offline `unittest` tests. Existing test command: `python3 -m unittest discover -s tests -v` from the repository root.
- `notebooks/`: numbered, researcher-run collection and exploratory analysis. Keep settings and text-handling rules visible. Use Seaborn with pink, purple, and green plots.
- Preserve `data/raw/`; derived text or analytical fields must not overwrite raw records. Keep `data/`, `artifacts/`, and secrets outside Git as configured in `.gitignore`.
- `collection_runs/`: track the agreed seven-field JSON records; richer monthly manifests stay beside raw data. Keep submission dates distinct from retrieval/revision dates.
- Preserve HTTPS verification. Review notebook outputs and tracked files before any approved GitHub publication.
- Keep testing requirements and security concerns within the relevant implementation milestone; do not create separate process documents unless requested.
