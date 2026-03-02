## [*] Quick Setup (5 minutes)

### 1. Install Dependencies

```powershell
pip install python-docx rdflib neo4j pandas
```

### 2. Place Your Document

Put the forest definitions document here:
```
docs/sources/forest_definitions.docx
```

### 3. Run the Pipeline

**Step 1: Extract from document**
```powershell
python scripts/extract_definitions.py
```
[*] Creates `csv/criteria.csv` and `csv/definition.csv`

**Step 2: Convert to RDF**
```powershell
python scripts/csv_to_rdf.py
```
[*] Creates `data/forest_definitions.ttl`

**Step 3: Import to Neo4j** (optional)
```powershell
# First, install and start Neo4j
# Then run:
python scripts/rdf_to_neo4j.py
```

## [*] What Each Script Does

### `extract_definitions.py`
- **Input**: DOCX document with definitions
- **Output**: CSV files
- **Enhancements over V2**:
  - 50+ countries (vs 5)
  - Extracts technical criteria automatically
  - Better year parsing
  - More definition keywords

### `csv_to_rdf.py`
- **Input**: CSV files from Step 1
- **Output**: RDF/Turtle file
- **Creates**: SKOS-compliant knowledge graph

### `rdf_to_neo4j.py`
- **Input**: RDF file from Step 2
- **Output**: Neo4j graph database
- **Enables**: Graph queries and visualization

## [*] Check Your Output

After Step 1:
```powershell
# Should show definitions
Get-Content csv\criteria.csv | Select-Object -First 10
```

After Step 2:
```powershell
# Should show RDF triples
Get-Content data\forest_definitions.ttl | Select-Object -First 50
```

After Step 3:
- Open http://localhost:7474
- Run: `MATCH (c:Concept)-[:HAS_DEFINITION]->(d:Definition) RETURN c, d LIMIT 25`


## [*] Understanding the Output

### CSV Structure

**criteria.csv** (main definitions):
```csv
concept_id,definition_id,label,alt_labels,definition_type,texte,organisation,year
forest_001,def_bra_2009,Forest,,Land Use,"Brazil defines...",Brazil,2009
```

**definition.csv** (technical criteria):
```csv
definition_id,criteria_name,value,unit
def_bra_2009,min_area,1.0,hectare
def_bra_2009,min_canopy_cover,30.0,percent
def_bra_2009,min_height,5.0,meter
```

### RDF/Turtle Structure

```turtle
ex:Forest a skos:Concept ;
    skos:prefLabel "Forest"@en ;
    skos:definition ex:Def_Brazil_2009 .

ex:Def_Brazil_2009 a ex:Definition ;
    rdfs:label "Definition from Brazil" ;
    ex:hasSource ex:Source_Brazil_2009 ;
    ex:type "Land Use" ;
    skos:note "Brazil defines forest as..." ;
    ex:hasCriteria [
        ex:minArea "1.0"^^xsd:float ;
        ex:minCanopyCover "30.0"^^xsd:float ;
        ex:minHeight "5.0"^^xsd:float
    ] .
```


## [*] Common Issues

### "No module named 'docx'"
```powershell
pip install python-docx
```

### "Document not found"
- Check path: `docs/sources/forest_definitions.docx`
- Update `DOC_PATH` in script if different location

### "No definitions extracted"
- Your document needs keywords: "means", "defined as", "refers to"
- Check if country names match (case-insensitive)

### "Empty CSV files"
- Verify document contains the text you saw before
- Try with fewer countries first: `self.countries = ["Brazil", "India", "Canada"]`

## [*] Next Meeting Points

Questions to discuss:
1. Which countries should we prioritize?
2. Do we need more definition keywords?
3. Should we add Deforestation and Afforestation concepts?
4. Do we need Neo4j or is CSV/RDF enough?


## [*] Help

- Check `README.md` for full documentation
- Look at script docstrings for details
- Test data is in `data/test.ttl` as reference

---

**Ready to run?** Start with Step 1! [*]
