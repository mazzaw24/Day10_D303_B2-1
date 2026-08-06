# Baseline Pipeline Report

## Source and artifacts

- Acquisition mode: `live_crossref_api`
- Parsed records: **22**
- Raw response: `data\raw\crossref_response.json`
- Raw records: `data\raw\crossref_records.json`
- Frozen test-set SHA-256: `b7541a16c52d730f8ea62e286e4eb3cded2638c0f5bb2b1838ca0e6ce1825872`

## Evaluation metrics

| Metric | Value |
| --- | ---: |
| Samples | 24 |
| Retrieval hit rate | 1.0000 |
| Mean token F1 | 0.0710 |
| Judge accuracy | 0.8750 |
| Mean judge score | 4.7083 |

Ragas: `{'answer_relevancy': 0.9754103805522979, 'context_precision': 0.9479166665907987, 'context_recall': 1.0, 'faithfulness': 0.9791666666666666}`

## Data quality

Overall status: **PASS** (8 passed, 0 failed)

| Check | Dimension | Observed | Expectation | Result |
| --- | --- | ---: | --- | --- |
| minimum_row_count | volume | 22 | >= 8 | PASS |
| paper_id_complete | completeness | 22 | == 22 | PASS |
| paper_id_unique | uniqueness | 22 | == 22 | PASS |
| title_complete | completeness | 22 | == 22 | PASS |
| summary_complete | completeness | 22 | == 22 | PASS |
| summary_min_length | validity | 22 | == 22 | PASS |
| embedding_text_complete | completeness | 22 | == 22 | PASS |
| fresh_row_ratio | freshness | 1.0 | >= 0.80 | PASS |

## Freshness

- Status: **FRESH**
- Latest publication: `2028-06-15`
- Oldest publication: `2026-12-31`
- Stale rows: **0/22**
- Threshold: **180 days**
