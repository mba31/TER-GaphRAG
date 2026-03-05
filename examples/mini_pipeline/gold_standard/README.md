# Gold Standard & Quality Evaluation

This folder contains manual benchmarking tools for your extraction pipeline.

## Files

- **gold_standard_template.csv**: Hand-curated forest definitions (reference truth)
  - 3 sample rows with extended fields (numeric criteria, reviewer notes)
  - Edit this to add more manual examples from your source documents

- **gold_standard_sample.ttl**: Same data as SKOS/RDF triples
  - Shows how your CSV maps to semantic web format
  - Can be imported directly into graph databases

## Evaluating Extraction Quality

Use `compare_to_gold.py` to benchmark any automated extraction output:

```bash
# Compare regex variant
python compare_to_gold.py --automated extracted_definitions.csv

# Compare NLP variant
python compare_to_gold.py --automated extracted_definitions_nlp.csv

# Compare LLM variant
python compare_to_gold.py --automated extracted_definitions_llm.csv --gold_standard gold_standard/gold_standard_template.csv

# Use custom gold standard path
python compare_to_gold.py --automated extracted_definitions.csv --gold_standard my_gold.csv
```

## Reports Generated

- **Overall Match Score**: Weighted average of all fields (0–100%)
- **Field-Level Precision**: Breakdown by column (id, country, year, definition, source, criteria)
- **Low-Score Rows**: Details on rows that don't match well (< 80%)
- **Confidence Distribution**: Histogram of LLM confidence scores (if present)

## Building Your Gold Standard

1. Extract ~30–100 definitions using your automated pipeline
2. Manually review and correct entries in a spreadsheet
3. Save as `gold_standard/my_gold_standard.csv` (use `gold_standard_template.csv` columns)
4. Run `compare_to_gold.py` to measure pipeline accuracy against your curated data

## Key Metrics

- **id, country, year**: Must be 100% accurate (fuzzy match = fail)
- **definition**: Fuzzy match accepted (text may vary, but meaning should match)
- **source**: Format flexibility (e.g., "FAO FRA 2015" vs "FAO2015")
- **Numeric criteria** (canopy_min_pct, etc.): Optional, bonus points if extracted
