# Guide d'Extraction des Définitions Forestières

## Ce que fait ce projet

Ce script extrait automatiquement les définitions forestières depuis des documents (DOCX/PDF) et les structure en CSV.

## Étapes principales

### 1. Extraction de base (regex)
```bash
python scripts/extract_definitions.py
```
- Lit le document `docs/sources/forest_definitions.docx`
- Extrait les définitions avec regex (pays, année, critères techniques)
- Génère `csv/criteria.csv` et `csv/definition.csv`
- Crée une file d'attente pour paragraphes non résolus

### 2. Extraction avancée (LLM optionnel)
```bash
python scripts/extraction_fallback.py --provider ollama --model llama3.1:8b --workers 6
```
- Traite les paragraphes non résolus avec un LLM local
- Résultats dans `outputs/llm_fallback_results.csv`

## Support PDF (via Docling)
```bash
python scripts/extract_definitions.py --doc-path docs/sources/fichier.pdf --use-docling
```

## Fichiers générés
- `csv/criteria.csv` : critères techniques extraits
- `csv/definition.csv` : définitions complètes
- `outputs/queue_for_llm.csv` : paragraphes à retraiter
- `outputs/llm_fallback_results.csv` : résultats LLM

## Configuration
Voir `config.py` pour chemins et options d'extraction.
