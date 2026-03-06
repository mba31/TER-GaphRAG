# Guide d'Extraction des Définitions Forestières

## Ce que fait ce projet

Ce script extrait automatiquement les définitions forestières depuis des documents (DOCX/PDF) et les structure en CSV.

## Étapes principales

### 1. Extraction (regex)
```bash
python scripts/extract_definitions.py
```
- Lit le document `docs/sources/forest_definitions.docx`
- Extrait les définitions avec regex (pays, année, critères techniques)
- Génère `csv/criteria.csv` et `csv/definition.csv`

## Support PDF (via Docling)
```bash
python scripts/extract_definitions.py --doc-path docs/sources/fichier.pdf --use-docling
```

## Fichiers générés
- `csv/criteria.csv` : critères techniques extraits
- `csv/definition.csv` : définitions complètes

## Configuration
Voir `config.py` pour chemins et options d'extraction.
