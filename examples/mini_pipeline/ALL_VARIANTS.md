# All Extraction Variants (Mini Pipeline)

This folder now includes **all major extraction variants**:

1. **Regex**: `2_extract.py`
2. **NLP**: `2_extract_nlp.py`
3. **LLM**: `2_extract_llm.py`
4. **ML**: `2_extract_ml.py`
5. **Hybrid** (Regex → NLP → LLM): `2_extract_hybrid.py`

## Quick Run Commands

From `examples/mini_pipeline`:

```bash
python 2_extract.py
python 2_extract_nlp.py
python 2_extract_llm.py --provider ollama --model llama3.1:8b
python 2_extract_ml.py
python 2_extract_hybrid.py --model llama3.1:8b
```

## Output Files

- `extracted_definitions.csv`
- `extracted_definitions_nlp.csv`
- `extracted_definitions_llm.csv`
- `extracted_definitions_ml.csv`
- `extracted_definitions_hybrid.csv`

## Notes

- `2_extract_llm.py` uses local Ollama by default.
- `2_extract_ml.py` requires `scikit-learn`.
- `2_extract_hybrid.py` falls back to Ollama only if regex and NLP fail.
