# AI Research Landscape 2026

Map the evolution of AI research on arXiv from January 1, 2022 through October 31, 2026, focusing on methodological advances and scientific understanding of AI systems, with particular interest in AI safety.

Initial collection covers cs.AI, including cross-listed and application papers. Keep titles, abstracts, authors, IDs, dates, and categories. Classification into methodological, application, mixed, or uncertain contributions will be investigated later. Findings from this initial corpus describe cs.AI coverage, not all AI research.

## Project navigation

- [IMPLEMENTATION.md](IMPLEMENTATION.md): milestones, checklists, evidence, and open decisions.
- [HANDOFF.md](HANDOFF.md): current session state and next action; start here when resuming work.
- [AGENTS.md](AGENTS.md): repository-specific instructions for Codex, complementing global instructions.
- [PLAN.md](PLAN.md): original plan, preserved unchanged pending migration review.

The recorded collection contains 168,567 papers across 58 months; see [the run record](collection_runs/2026-11-12_cs-ai.json). The researcher runs code and reviews results. Notebook implementation does not imply execution or validated research findings.

| Path | Purpose |
|---|---|
| `arxiv_collection.py` | API queries, parsing, monthly collection, and validation |
| `tests/test_arxiv_collection.py` | 28 offline collection tests |
| `collection_runs/` | Small run records intended for Git |
| `data/raw/arxiv_cs_ai_2022_2026/` | Local raw records and monthly manifests, excluded from Git |

## Notebook order

1. [01_arxiv_sample.ipynb](notebooks/01_arxiv_sample.ipynb): exploratory multi-category sample and counts; this is broader than the final cs.AI-only collection.
2. [02_collect_cs_ai.ipynb](notebooks/02_collect_cs_ai.ipynb): full collection, validation, and seven-field run-record updates.
3. [03_describe_corpus.ipynb](notebooks/03_describe_corpus.ipynb): data checks, temporal counts/category shares, primary cs.AI/cs.LG comparison, and yearly author boxplots.
4. [04_compare_ai_lg_terms.ipynb](notebooks/04_compare_ai_lg_terms.ipynb): shared/distinctive abstract words and phrases for primary cs.AI versus cs.LG, January 2025–October 2026; awaiting researcher review.

For an existing local collection, start with the relevant analysis notebook rather than downloading again. Dependencies are Python, pandas, Seaborn, Matplotlib, and an IPython/Jupyter kernel; collection helpers and offline tests use only the standard library. No pinned dependency/environment file currently exists.

## Collection sample

Open [notebooks/01_arxiv_sample.ipynb](notebooks/01_arxiv_sample.ipynb), restart the kernel, and run the cells yourself. It retrieves one page of 20 records, not a representative sample or a complete corpus. Python, pandas, and an IPython/Jupyter kernel are needed.

The collection code uses only Python's standard library:

- `build_url()` constructs the category and submission-date query.
- `fetch_xml()` downloads one response, preserving network errors.
- `parse_feed()` turns the XML into records without cleaning or excluding papers.

The notebook keeps the settings, table display, and quality checks visible. Empty feeds stop the notebook; missing record fields remain visible for inspection. The API returns current metadata, so revisions can postdate the submission cutoff.

Run the offline tests yourself from the repository root:

```bash
python3 -m unittest discover -s tests -v
```

Tests use synthetic XML and mocked downloads. They check code behavior, not real API availability, corpus completeness, or scientific validity. No new dependencies are required for the tests.

## Full cs.AI collection

After running the tests, open [notebooks/02_collect_cs_ai.ipynb](notebooks/02_collect_cs_ai.ipynb). You run it and inspect the results; the assistant does not execute it.

- `month_ranges()` splits January 2022–October 2026 into 58 non-overlapping months.
- `collect_month()` retrieves pages of 500 records, pausing three seconds before requests. It stops on network errors, changing totals, incomplete results, duplicate IDs, invalid dates, or category mismatches. A window exceeding 30,000 matches stops with a request to split it further.
- `validate_records()` reports collection problems without modifying records. Blank titles and abstracts are kept and counted for cleaning.

Files go in `data/raw/arxiv_cs_ai_2022_2026/`, excluded from Git. Each month has a JSONL file (one record per line) and a manifest containing query URLs, timestamps, API and retrieved counts, validation results, and hashes of the data and collector code.

Rerunning checks and reuses completed months. The current interrupted month is downloaded again; there is no page-level resume or automatic retry. A completion marker is saved only after the full window passes validation. Missing or changed completed files cause an explicit error rather than silent replacement; use a separate output directory for a deliberate fresh collection.

The notebook rechecks saved files and duplicate IDs across months before showing a preview. Counts may differ from the earlier API count of 168,572; investigate differences instead of forcing that number. Matching counts and unique IDs are useful checks, not proof that the API returned every relevant paper. Current metadata can change, and records are not a historical snapshot of their submission versions.

## Background

The project was initially inspired by Kirchner et al. (2022), *Researching Alignment Research: Unsupervised Analysis*: https://doi.org/10.48550/arXiv.2206.02841.

The authors' collection repository was inspected: https://github.com/moirage/alignment-research-dataset, commit `0da2b0bd06499bb32b4757f8766e5958ff5543ed`. No upstream code has been copied.
