# Implementation roadmap

Map AI research from January 2022–October 2026, focusing on methodological advances, scientific understanding, and AI safety. Produce a scientific report with reproducible collection and analysis.

The initial corpus contains cs.AI-tagged arXiv papers, including cross-listings and applications—not all AI research. Metadata reflects retrieval-time versions.

**Status:** ✅ Completed · ⏳ In progress/awaiting verification · ⬚ Not started · ⚠️ Blocked

## Phase 1: Collection baseline ✅ COMPLETED

Collect and validate cs.AI-tagged papers and preserve their provenance.

| Task | Description | Status |
|------|-------------|--------|
| 1.1 | Implement monthly collection, pagination, resume, and validation | ✅ |
| 1.2 | Collect and validate the baseline corpus | ✅ |
| 1.3 | Provide 28 offline tests; researcher reported passing tests | ✅ |
| 1.4 | Record the completed collection’s scope, dates, and total | ✅ |

**Deliverable:** Raw monthly files, manifests, collection code/tests, and seven-field run record.

**Notes:**
- 168,567 unique papers across 58 months; researcher reported zero duplicates or blank titles/abstracts. Manifests corroborate the total; raw hashes were not independently rechecked during documentation review.
- The earlier API count was 168,572; the five-record discrepancy remains unexplained.
- Later automatic run-record cells are implemented but execution remains unconfirmed. Verify before relying on them for future runs.
- Broader category collection remains optional.

**Acceptance criteria:** Collection counts reconcile, IDs/dates/categories pass validation, and provenance is recorded. Preserve raw data and HTTPS verification; future run records must complete only after validation.

## Phase 2: Describe the corpus and temporal changes ✅ COMPLETED

Describe submission volume, categories, and author counts over time.

| Task | Description | Status |
|------|-------------|--------|
| 2.1 | Implement data-quality and integrity checks | ✅ |
| 2.2 | Implement monthly volume and category counts/shares | ✅ |
| 2.3 | Implement primary/cross-listed and cs.AI/cs.LG comparisons | ✅ |
| 2.4 | Implement author summaries and yearly boxplots | ✅ |


**Deliverable:** Researcher-reviewed notebook 03.

**Acceptance criteria:** Researcher approves current outputs, cleaning, and scope. Counts reconcile; category overlap and denominators are clear. Comparisons account for the October 2026 cutoff. Author counts represent listed entries, not unique researcher identities.

## Phase 3: Explore changing language ✅ COMPLETED

Investigate distinctive/shared terms and their temporal development, focusing on comparing primary cs.AI versus cs.LG abstracts.

| Task | Description | Status |
|------|-------------|--------|
| 3.1 | Implement the approved abstract-term comparison | ✅ |
| 3.2 | Provide counts, percentages, rankings, plots, and examples | ✅ |
| 3.3 | Run and review notebook 04 and counting checks | ✅ |
| 3.4 | Inspect example abstracts and tokenization limitations | ✅ |
| 3.5 | Decide subsequent temporal comparisons and text methods | ✅ |

**Deliverable:** Researcher-reviewed notebook 04 and decisions about further text exploration.



**Acceptance criteria:** Researcher verifies counting, denominators, tokenization, thresholds, and examples before interpretation. Agree on further methods. Distinctive terms must not automatically be described as new technologies or explanations for the category shift.

## Phase 4: Distinguish contribution types ⬚ PLANNED

Distinguish methodological advances/scientific understanding, applications, mixed contributions, and uncertain cases.

| Task | Description | Status |
|------|-------------|--------|
| 4.1 | Agree on contribution-type definitions | ⬚ |
| 4.2 | Select and manually review a small sample | ⬚ |
| 4.3 | Choose a classification approach | ⬚ |
| 4.4 | Evaluate errors and uncertainty | ⬚ |

**Deliverable:** Reviewed definitions, sample, and classification evaluation.

**Notes:**
- No implementation or validated classifications exist.
- Definitions, sampling, method, and evaluation remain undecided.
- No model/service is selected; review any proposed external data sharing.

**Acceptance criteria:** Researcher approves definitions and evaluates classification errors and uncertainty before labels support temporal comparisons.

## Phase 5: Map research directions and AI safety ⬚ PLANNED

Investigate research directions, relationships, emerging areas, publication attention, and AI safety’s development.

| Task | Description | Status |
|------|-------------|--------|
| 5.1 | Agree on methods for identifying research directions | ⬚ |
| 5.2 | Investigate temporal changes and relationships | ⬚ |
| 5.3 | Define and validate AI safety relevance | ⬚ |
| 5.4 | Investigate emerging areas and possible gaps | ⬚ |

**Deliverable:** Researcher-reviewed maps and temporal comparisons.

**Notes:**
- No implementation or validated results exist.
- Embeddings/clustering remain undecided.
- Sparse publication coverage raises questions; it does not establish research gaps.

**Acceptance criteria:** Researcher approves methods, relevant validation, and interpretations. Claims state corpus limitations and uncertainty; AI safety relevance is validated before conclusions.

## Phase 6: Scientific report and reproducibility ⬚ PLANNED

Produce a scientific report and a repository supporting reproduction.

| Task | Description | Status |
|------|-------------|--------|
| 6.1 | Document environment and reproduction instructions | ⬚ |
| 6.2 | Set up commits and GitHub with researcher approval | ⬚ |
| 6.3 | Assemble reviewed findings, figures, and methods | ⬚ |
| 6.4 | Review reproduction evidence and publication contents | ⬚ |

**Deliverable:** Researcher-approved scientific report and reproducible repository.

**Notes:**
- Existing code, tests, notebooks, run records, and documentation provide a foundation; no completed report or verified end-to-end reproduction is recorded.
- No pinned environment exists. GitHub setup and report preparation remain pending.
- Document scope, retrieval dates, cleaning, classification, and sampling choices.

**Acceptance criteria:** Researcher approves the report and reproduction evidence. Separate observations from interpretations. Review tracked files and notebook outputs for secrets, unintended raw data, and local details before approved publication.
