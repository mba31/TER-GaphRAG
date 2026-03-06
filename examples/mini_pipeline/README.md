# Mini Pipeline - Learning by Example

**Objectif**: Learn the complete extraction → RDF pipeline in 3 simple steps.

## Structure

```
mini_pipeline/
├── 1_sample_data.csv         # Input: 3 sample forest definitions
├── 2_extract.py              # Step 1: Extract (regex-based)
├── 3_to_rdf.py               # Step 2: Convert to RDF/Turtle
├── extracted_definitions.csv # Output from 2_extract.py
├── forest_definitions.ttl    # Output from 3_to_rdf.py
└── README.md                 # This file
```

## Exécution pas à pas

### Étape 1: Vérifier les données d'entrée
```bash
cat 1_sample_data.csv
```

### Étape 2: Extraire et nettoyer
```bash
python 2_extract.py
```
Génère `extracted_definitions.csv`

### Étape 3: Créer le graphe RDF
```bash
python 3_to_rdf.py
```
Génère `forest_definitions.ttl`

### Étape 4: Vérifier le TTL
```bash
cat forest_definitions.ttl
```

## What You Learn

1. **Extraction**: Regex-based extraction from CSV
2. **Structure**: CSV → Python dictionaries → RDF graph
3. **RDF/SKOS**: Convert to semantic web format (Turtle)

## Output Files

After running the pipeline:
- `extracted_definitions.csv` - Extracted and cleaned definitions
- `forest_definitions.ttl` - RDF/Turtle knowledge graph (readable in any text editor)

## Next Steps (on the full project)

- Scale to full document (1,859+ definitions)
- Add LLM extraction for complex cases
- Import into Neo4j or Virtuoso graph database
- Link to ENVO ontology for standardized terms

