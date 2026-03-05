# Mini Pipeline - Learning by Example

**But**: Apprendre les 3 étapes clés : extraction → CSV → RDF graph

## Structure

```
mini_pipeline/
├── 1_sample_data.csv          # Données d'entrée (simple)
├── 2_extract.py               # Extraction basique (regex)
├── 2_extract_nlp.py           # Extraction NLP (dateutil)
├── 2_extract_llm.py           # Extraction LLM (Ollama/OpenAI)
├── 2_extract_ml.py            # Extraction ML (scikit-learn)
├── 2_extract_hybrid.py        # Hybrid: regex → NLP → LLM
├── 3_to_rdf.py                # Conversion CSV → RDF
├── ALL_VARIANTS.md            # Tous les variants + commandes
└── README.md                  # Ce fichier
```

## Exécution pas à pas

### Étape 1: Vérifier les données d'entrée
```bash
cat 1_sample_data.csv
```

### Étape 2: Extraire et nettoyer

**Approach 1 - Regex (rapide, patterns rigides):**
```bash
python 2_extract.py
```
Génère `extracted_definitions.csv`

**Approach 2 - NLP (flexibilité, dateutil):**
```bash
python 2_extract_nlp.py
```
Génère `extracted_definitions_nlp.csv` (même résultat, méthode différente)

**Approach 3 - LLM (flexible, local ou API):**
```bash
python 2_extract_llm.py --provider ollama --model llama3.1:8b
```
Génère `extracted_definitions_llm.csv`

**Approach 4 - ML (classifieur supervisé):**
```bash
python 2_extract_ml.py
```
Génère `extracted_definitions_ml.csv`

**Approach 5 - Hybrid (production pattern):**
```bash
python 2_extract_hybrid.py --model llama3.1:8b
```
Génère `extracted_definitions_hybrid.csv`

Voir `EXTRACTION_METHODS.md` pour la comparaison complète.
Voir `ALL_VARIANTS.md` pour les commandes rapides.

### Étape 3: Créer le graphe RDF
```bash
python 3_to_rdf.py
```
Génère `forest_definitions.ttl`

### Étape 4: Vérifier le TTL
```bash
cat forest_definitions.ttl
```

## Données d'exemple

Le fichier `1_sample_data.csv` contient 3 définitions forestières simples:
- Pays
- Année
- Définition brute

## Étape 5 (optionnel): Benchmark & Contrôle de Qualité

Comparer vos extractions automatisées avec un "gold standard" manuel:

```bash
# Benchmark regex extraction
python compare_to_gold.py --automated extracted_definitions.csv

# Benchmark NLP extraction
python compare_to_gold.py --automated extracted_definitions_nlp.csv --gold_standard gold_standard/gold_standard_template.csv
```

Voir `gold_standard/README.md` pour créer vos propres exemples de référence.

## Ce qu'on apprend

1. **Extraction**: 5 variantes (Regex, NLP, LLM, ML, Hybrid)
2. **Méthodes**: Quand utiliser chaque approche (voir `EXTRACTION_METHODS.md`)
3. **Structure**: CSV → dictionnaire Python → RDF graph
4. **Sérialisation**: RDF/Turtle pour un knowledge graph SKOS-compliant
5. **Validation**: Benchmark d'extraction contre un gold standard manual (voir `gold_standard/`)

## Fichiers téléchargeable

- Vérifier `extracted_definitions.csv` après étape 2 (Regex)
- Vérifier `extracted_definitions_nlp.csv` (NLP)
- Vérifier `extracted_definitions_llm.csv` (LLM)
- Vérifier `extracted_definitions_ml.csv` (ML)
- Vérifier `extracted_definitions_hybrid.csv` (Hybrid)
- Vérifier `forest_definitions.ttl` après étape 3 (ouvrable dans n'importe quel éditeur)

## Prochaines étapes (sur le projet complet)

- Ajouter plus de champs (organisation, critères)
- Utiliser LLM pour cas complexes
- Importer en Neo4j ou Virtuoso
