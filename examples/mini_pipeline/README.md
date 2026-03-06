# Mini Pipeline - Apprendre par l'Exemple

**Objectif**: Apprendre le pipeline complet d'extraction → RDF en 3 étapes simples.

## Structure

```
mini_pipeline/
├── 1_sample_data.csv         # Entrée: 3 exemples de définitions forestières
├── 2_extract.py              # Étape 1: Extraction (basée sur regex)
├── 3_to_rdf.py               # Étape 2: Conversion en RDF/Turtle
├── 4_to_neo4j.py             # Étape 3: Import en Neo4j (optionnel)
├── extracted_definitions.csv # Sortie de 2_extract.py
├── forest_definitions.ttl    # Sortie de 3_to_rdf.py
└── README.md                 # Ce fichier
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

### Étape 5 (Optionnel): Importer en Neo4j
```bash
python 4_to_neo4j.py
```
Importe les données RDF dans une base de données Neo4j.

## Ce qu'on apprend

1. **Extraction**: Extraction basée sur regex à partir d'un CSV
2. **Structure**: CSV → dictionnaires Python → graphe RDF
3. **RDF/SKOS**: Conversion en format web sémantique (Turtle)
4. **Import graphique**: Charger une base de données Neo4j (optionnel)

## Fichiers de sortie

Après avoir exécuté le pipeline:
- `extracted_definitions.csv` - Définitions extraites et nettoyées
- `forest_definitions.ttl` - Graphe de connaissances RDF/Turtle (lisible dans n'importe quel éditeur de texte)

## Prochaines étapes (sur le projet complet)

- Adapter à l'ensemble du document (1 859+ définitions)
- Ajouter l'extraction par LLM pour les cas complexes
- Importer dans Neo4j ou Virtuoso
- Lier à l'ontologie ENVO pour les termes standardisés


