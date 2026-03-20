# Neo4j Cypher Query Guide

This guide provides comprehensive Cypher queries for exploring and retrieving information from the TER2026 forest definitions knowledge graph.

## Table of Contents
1. [Basic Exploration](#basic-exploration)
2. [Concept Relationship Queries](#concept-relationship-queries)
3. [Country-Specific Queries](#country-specific-queries)
4. [Technical Criteria Analysis](#technical-criteria-analysis)
5. [Deforestation Analysis](#deforestation-analysis)
6. [RAG Context Retrieval](#rag-context-retrieval)
7. [Advanced Comparative Queries](#advanced-comparative-queries)
8. [Full-Text Search](#full-text-search)

---

## Basic Exploration

### Count All Concepts
```cypher
MATCH (c:Concept)
RETURN c.name, count{(c)-[:HAS_DEFINITION]->()} as definition_count
ORDER BY definition_count DESC
```

### View Graph Structure
```cypher
MATCH (forest:Concept {name:"Forest"})
OPTIONAL MATCH (forest)<-[r1:AFFECTS|PART_OF|RELATED_TO|OPPOSITE_OF|MANAGES|MEASURES]-(related:Concept)
OPTIONAL MATCH (forest)-[:HAS_DEFINITION]->(d:Definition)-[:PROVIDED_BY]->(s:Source)
OPTIONAL MATCH (d)-[r2:APPLIES_TO]->(country:Country)
RETURN forest, related, r1, d, s, r2, country
LIMIT 300
```

### View Multi-Concept Graph (Connected via Semantic Relations)
```cypher
MATCH (c:Concept)
WHERE c.name IN ["Forest","Deforestation","Afforestation","Reforestation"]
OPTIONAL MATCH (c)-[:HAS_DEFINITION]->(d:Definition)-[:PROVIDED_BY]->(s:Source)
OPTIONAL MATCH (d)-[rc:APPLIES_TO]->(country:Country)
OPTIONAL MATCH (c)-[r:AFFECTS|PART_OF|RELATED_TO|OPPOSITE_OF|MANAGES|MEASURES|DERIVED_FROM]->(c2:Concept)
WHERE c2.name IN ["Forest","Deforestation","Afforestation","Reforestation"]
RETURN c, d, s, rc, country, r, c2
LIMIT 400
```

### Get All Definitions for a Specific Concept
```cypher
MATCH (c:Concept {name: "Forest"})-[:HAS_DEFINITION]->(d:Definition)-[:PROVIDED_BY]->(s:Source)
RETURN d.text as definition, d.country as country, d.geographicScope as scope, s.year as year, s.organization as organization
ORDER BY s.year DESC
LIMIT 20
```

### Count Definitions by Concept
```cypher
MATCH (c:Concept)-[:HAS_DEFINITION]->(d:Definition)
RETURN c.name as concept, count(d) as total_definitions
ORDER BY total_definitions DESC
```

---

## Concept Relationship Queries

### Show All Concept-to-Concept Relationships
```cypher
MATCH (c1:Concept)-[r]->(c2:Concept)
RETURN c1.name as source, type(r) as relationship, c2.name as target
ORDER BY source, relationship, target
```

### Show Concepts Affecting Forest
```cypher
MATCH (c:Concept)-[:AFFECTS]->(:Concept {name: "Forest"})
RETURN c.name as affecting_concept
ORDER BY affecting_concept
```

### Show Structural Components of Forest
```cypher
MATCH (c:Concept)-[:PART_OF]->(:Concept {name: "Forest"})
RETURN c.name as component
ORDER BY component
```

### Count Definitions by Relationship Type
```cypher
MATCH (c1:Concept)-[r]->(c2:Concept)
MATCH (c1)-[:HAS_DEFINITION]->(d:Definition)
RETURN type(r) as relationship, count(d) as definition_count
ORDER BY definition_count DESC
```

---

## Country-Specific Queries

### Get All Forest Definitions from a Specific Country
```cypher
MATCH (country:Country {name: "Brazil"})<-[:APPLIES_TO]-(d:Definition)<-[:HAS_DEFINITION]-(c:Concept {name: "Forest"})
MATCH (d)-[:PROVIDED_BY]->(s:Source)
RETURN d.text as definition, d.geographicScope as scope, s.year as year, s.organization as organization
ORDER BY s.year DESC
```

### Compare Definitions Across Countries
```cypher
MATCH (country:Country)<-[:APPLIES_TO]-(d:Definition)<-[:HAS_DEFINITION]-(c:Concept {name: "Forest"})
WHERE country.name IN ["Brazil", "United States", "India"]
RETURN country.name as country, collect(d.text)[0..3] as sample_definitions, count(d) as total
ORDER BY total DESC
```

### Find Countries with Most Definitions
```cypher
MATCH (country:Country)<-[:APPLIES_TO]-(d:Definition)
RETURN country.name as country, count(d) as definition_count
ORDER BY definition_count DESC
LIMIT 10
```

### UN-FAO Definitions by Country (Cleaned)
```cypher
MATCH (s:Source {organization: "UN-FAO"})<-[:PROVIDED_BY]-(d:Definition)
MATCH (d)-[:APPLIES_TO]->(country:Country)
RETURN country.name as country, count(*) as definitions
ORDER BY definitions DESC
```

---

## Technical Criteria Analysis

### Find Definitions with Area Criteria
```cypher
MATCH (d:Definition)-[:QUANTIFIED_BY]->(tc:TechnicalCriterion)
WHERE tc.criterion_name = "area"
RETURN d.text as definition, tc.value as area_value, tc.unit as unit
LIMIT 20
```

### Compare Canopy Cover Requirements
```cypher
MATCH (c:Concept {name: "Forest"})-[:HAS_DEFINITION]->(d:Definition)-[:QUANTIFIED_BY]->(tc:TechnicalCriterion)
WHERE tc.criterion_name = "canopy_cover"
RETURN d.text as definition, tc.value as canopy_percentage, tc.unit
ORDER BY tc.value DESC
LIMIT 10
```

### Find Definitions with Height Criteria
```cypher
MATCH (d:Definition)-[:QUANTIFIED_BY]->(tc:TechnicalCriterion)
MATCH (d)-[:PROVIDED_BY]->(s:Source)
WHERE tc.criterion_name = "height"
RETURN d.text as definition, tc.value as height, tc.unit, d.country as country
ORDER BY tc.value DESC
LIMIT 15
```

### Get All Criteria for a Specific Definition
```cypher
MATCH (d:Definition {id: "forest_def_1"})-[:QUANTIFIED_BY]->(tc:TechnicalCriterion)
RETURN d.text as definition, collect({
    criterion: tc.criterion_name, 
    value: tc.value, 
    unit: tc.unit
}) as criteria
```

---

## Deforestation Analysis

### Get All Deforestation Definitions
```cypher
MATCH (c:Concept {name: "Deforestation"})-[:HAS_DEFINITION]->(d:Definition)-[:PROVIDED_BY]->(s:Source)
RETURN d.text as definition, d.country as country, d.geographicScope as scope, s.year, s.organization
ORDER BY s.year DESC
```

### Compare Deforestation vs Afforestation Definitions
```cypher
MATCH (c:Concept)-[:HAS_DEFINITION]->(d:Definition)-[:PROVIDED_BY]->(s:Source)
WHERE c.name IN ["Deforestation", "Afforestation"]
RETURN c.name as concept, count(d) as total_definitions, collect(DISTINCT d.country)[0..5] as sample_countries
```

### Find Policy-Related Deforestation Definitions
```cypher
MATCH (c:Concept {name: "Deforestation"})-[:HAS_DEFINITION]->(d:Definition)
WHERE d.text CONTAINS "policy" OR d.text CONTAINS "regulation" OR d.text CONTAINS "law"
RETURN d.text as definition
LIMIT 10
```

---

## RAG Context Retrieval

### Retrieve Context for "What is a forest?"
```cypher
MATCH (c:Concept {name: "Forest"})-[:HAS_DEFINITION]->(d:Definition)-[:PROVIDED_BY]->(s:Source)
OPTIONAL MATCH (d)-[:QUANTIFIED_BY]->(tc:TechnicalCriterion)
RETURN d.text as definition, 
    d.country as country,
    d.geographicScope as scope,
       s.year, 
       s.organization,
       collect({criterion: tc.criterion_name, value: tc.value, unit: tc.unit}) as technical_criteria
ORDER BY s.year DESC
LIMIT 5
```

### Get Most Recent Definitions for RAG
```cypher
MATCH (c:Concept)-[:HAS_DEFINITION]->(d:Definition)-[:PROVIDED_BY]->(s:Source)
WHERE s.year >= 2010
RETURN c.name as concept, 
       d.text as definition, 
    d.country as country,
    d.geographicScope as scope,
       s.year,
       s.organization
ORDER BY s.year DESC, c.name
LIMIT 20
```

### Find Authoritative International Definitions
```cypher
MATCH (c:Concept)-[:HAS_DEFINITION]->(d:Definition)-[:PROVIDED_BY]->(s:Source)
WHERE s.organization CONTAINS "FAO" 
   OR s.organization CONTAINS "UN" 
   OR s.organization CONTAINS "IPCC"
RETURN c.name as concept, d.text as definition, s.organization, s.year
ORDER BY c.name, s.year DESC
```

### Retrieve Definitions with Technical Specifications
```cypher
MATCH (c:Concept {name: "Forest"})-[:HAS_DEFINITION]->(d:Definition)-[:PROVIDED_BY]->(s:Source)
MATCH (d)-[:QUANTIFIED_BY]->(tc:TechnicalCriterion)
WITH d, s, count(tc) as criteria_count, collect({
    criterion: tc.criterion_name, 
    value: tc.value, 
    unit: tc.unit
}) as criteria
WHERE criteria_count >= 2
RETURN d.text as definition, d.country as country, d.geographicScope as scope, s.year, criteria
ORDER BY criteria_count DESC
LIMIT 10
```

---

## Advanced Comparative Queries

### Compare Forest Definitions Over Time
```cypher
MATCH (c:Concept {name: "Forest"})-[:HAS_DEFINITION]->(d:Definition)-[:PROVIDED_BY]->(s:Source)
WHERE s.year IS NOT NULL
RETURN s.year as year, count(d) as definitions_published, collect(DISTINCT d.country)[0..5] as sample_countries
ORDER BY year DESC
LIMIT 20
```

### Find Similar Definitions Across Concepts
```cypher
MATCH (c:Concept)-[:HAS_DEFINITION]->(d:Definition)
WHERE d.text CONTAINS "tree"
RETURN c.name as concept, count(d) as mentions, collect(d.text)[0..2] as sample_definitions
ORDER BY mentions DESC
```

### Analyze Regional Definition Differences
```cypher
MATCH (c:Concept {name: "Forest"})-[:HAS_DEFINITION]->(d:Definition)-[:PROVIDED_BY]->(s:Source)
WHERE d.country IN ["Brazil", "Canada", "Russia", "Congo"]
OPTIONAL MATCH (d)-[:QUANTIFIED_BY]->(tc:TechnicalCriterion {criterion_name: "area"})
RETURN d.country as country,
       count(d) as total_definitions,
       collect(DISTINCT tc.value)[0..5] as area_requirements
ORDER BY total_definitions DESC
```

---

## Full-Text Search

### Search Definitions by Keyword
```cypher
MATCH (d:Definition)
WHERE d.text CONTAINS "biodiversity"
RETURN d.text as definition
LIMIT 10
```

### Find Definitions Mentioning Specific Criteria
```cypher
MATCH (d:Definition)-[:PROVIDED_BY]->(s:Source)
WHERE d.text CONTAINS "minimum" AND d.text CONTAINS "hectare"
RETURN d.text as definition, d.country as country, s.year
ORDER BY s.year DESC
LIMIT 15
```

### Search Across All Concepts
```cypher
MATCH (c:Concept)-[:HAS_DEFINITION]->(d:Definition)
WHERE d.text CONTAINS "carbon" OR d.text CONTAINS "climate"
RETURN c.name as concept, d.text as definition, count(*) as relevance
ORDER BY relevance DESC
LIMIT 10
```

---

## Tips for Query Optimization

1. **Use LIMIT**: Always limit results when exploring large datasets
2. **Index Properties**: Create indexes on frequently queried properties:
   ```cypher
   CREATE INDEX concept_name IF NOT EXISTS FOR (c:Concept) ON (c.name)
    CREATE INDEX definition_country IF NOT EXISTS FOR (d:Definition) ON (d.country)
    CREATE INDEX definition_scope IF NOT EXISTS FOR (d:Definition) ON (d.geographicScope)
   ```
3. **PROFILE Queries**: Use `PROFILE` prefix to analyze query performance:
   ```cypher
   PROFILE MATCH (c:Concept)-[:HAS_DEFINITION]->(d) RETURN count(d)
   ```
4. **Filter Early**: Apply WHERE clauses as early as possible in the query

---

## Integration with RAG Systems

### CLI helper (ready to use)
```powershell
python scripts/graphrag_query.py --question "What is afforestation?"
```

### LangChain Example Pattern
```python
from langchain.graphs import Neo4jGraph

graph = Neo4jGraph(
    url="bolt://localhost:7687",
    username="neo4j",
    password="umontpellier"
)

# Query for context
context_query = """
MATCH (c:Concept {name: $concept})-[:HAS_DEFINITION]->(d:Definition)-[:PROVIDED_BY]->(s:Source)
RETURN d.text as definition, d.country, d.geographicScope, s.year, s.organization
ORDER BY s.year DESC
LIMIT 3
"""

# Retrieve context
results = graph.query(context_query, params={"concept": "Forest"})

# Augment LLM prompt with graph context
context = "\n".join([r["definition"] for r in results])
prompt = f"Context from knowledge graph:\n{context}\n\nUser question: What is a forest?"
```

---

## Synonym Relationships (NEW)

### Find All Synonyms of a Concept
```cypher
MATCH (c:Concept {prefLabel: "Woodland"})-[:SYNONYM_OF]->(syn:Concept)
RETURN c.prefLabel AS concept, syn.prefLabel AS synonym
```

### Find Definitions Including Synonyms
```cypher
// Get definitions for "Woodland" AND its synonyms (e.g., "Woods")
MATCH (c:Concept {prefLabel: "Woodland"})-[:SYNONYM_OF*0..1]->(related:Concept)
MATCH (related)-[:HAS_DEFINITION]->(d:Definition)
RETURN related.prefLabel AS concept, 
       d.country, 
       count(d) AS definitionCount
ORDER BY definitionCount DESC
```

### Expand Search Across Synonym Network
```cypher
// Find all concepts related to "Forest" through synonyms (within 2 hops)
MATCH path = (c1:Concept {prefLabel: "Forest"})-[:SYNONYM_OF*0..2]-(c2:Concept)
MATCH (c2)-[:HAS_DEFINITION]->(d:Definition)
RETURN c1.prefLabel AS searchTerm, 
       c2.prefLabel AS foundConcept, 
       count(d) AS totalDefinitions
ORDER BY totalDefinitions DESC
```

### Visualize Synonym Network
```cypher
MATCH (c1:Concept)-[r:SYNONYM_OF]->(c2:Concept)
OPTIONAL MATCH (c1)-[:HAS_DEFINITION]->(d1:Definition)
OPTIONAL MATCH (c2)-[:HAS_DEFINITION]->(d2:Definition)
WITH c1, r, c2, count(DISTINCT d1) AS def1Count, count(DISTINCT d2) AS def2Count
RETURN c1, r, c2, def1Count, def2Count
```

---

## SI-Normalized Criteria Queries (NEW)

### Find Definitions by Minimum Height (SI units)
```cypher
// All definitions requiring trees >= 5 meters tall
MATCH (d:Definition)-[:QUANTIFIED_BY]->(tc:TechnicalCriteria)
WHERE tc.minHeightSI >= 5.0
RETURN d.country, 
       tc.minHeight AS originalValue, 
       tc.minHeightSI AS metersValue
ORDER BY tc.minHeightSI DESC
LIMIT 20
```

### Compare Area Thresholds Across Countries
```cypher
// Average, min, and max area requirements by country (hectares)
MATCH (d:Definition)-[:QUANTIFIED_BY]->(tc:TechnicalCriteria)
WHERE tc.minAreaSI IS NOT NULL
RETURN d.country, 
       avg(tc.minAreaSI) AS avgAreaHectares, 
       min(tc.minAreaSI) AS minAreaHectares,
       max(tc.minAreaSI) AS maxAreaHectares,
       count(tc) AS criteriaCount
ORDER BY avgAreaHectares DESC
```

### Find Strictest Canopy Cover Requirements
```cypher
// Top 20 jurisdictions with highest canopy cover thresholds
MATCH (d:Definition)-[:QUANTIFIED_BY]->(tc:TechnicalCriteria)
WHERE tc.minCanopyCoverSI IS NOT NULL
RETURN d.country AS jurisdiction,
       tc.minCanopyCoverSI AS canopyPercent,
       d.definitionType AS defType
ORDER BY canopyPercent DESC
LIMIT 20
```

### Multi-Criteria Filtering (SI-normalized)
```cypher
// Find definitions meeting minimum thresholds (SI units)
MATCH (c:Concept {name: "Forest"})-[:HAS_DEFINITION]->(d:Definition)
MATCH (d)-[:QUANTIFIED_BY]->(tc:TechnicalCriteria)
WHERE tc.minHeightSI >= 5.0 
  AND tc.minAreaSI >= 0.5 
  AND tc.minCanopyCoverSI >= 10.0
RETURN d.country,
       tc.minHeightSI AS height_m,
       tc.minAreaSI AS area_ha,
       tc.minCanopyCoverSI AS canopy_pct
ORDER BY d.country
```

### Compare Original vs SI-Normalized Values
```cypher
// Show unit conversions (e.g., acres to hectares, feet to meters)
MATCH (d:Definition)-[:QUANTIFIED_BY]->(tc:TechnicalCriteria)
WHERE tc.minHeight <> tc.minHeightSI OR tc.minArea <> tc.minAreaSI
RETURN d.country,
       tc.minHeight AS originalHeight, 
       tc.minHeightSI AS heightSI,
       tc.minArea AS originalArea,
       tc.minAreaSI AS areaSI
LIMIT 20
```

### Global Criteria Distribution (SI units)
```cypher
// Statistical summary of all technical criteria (normalized)
MATCH (tc:TechnicalCriteria)
RETURN 
  avg(tc.minHeightSI) AS avgHeight_m,
  min(tc.minHeightSI) AS minHeight_m,
  max(tc.minHeightSI) AS maxHeight_m,
  avg(tc.minAreaSI) AS avgArea_ha,
  min(tc.minAreaSI) AS minArea_ha,
  max(tc.minAreaSI) AS maxArea_ha,
  avg(tc.minCanopyCoverSI) AS avgCanopy_pct,
  min(tc.minCanopyCoverSI) AS minCanopy_pct,
  max(tc.minCanopyCoverSI) AS maxCanopy_pct
```

---

## Additional Resources

- **Neo4j Browser**: Access at http://localhost:7474
- **Cypher Manual**: https://neo4j.com/docs/cypher-manual/
- **Graph Data Science**: Consider using GDS library for advanced analytics
- **Vector Search**: Integrate with Neo4j Vector Index for semantic search
- **Enhancement Documentation**: See [ENHANCEMENTS.md](ENHANCEMENTS.md) for details on SYNONYM_OF and SI-normalized values

---

Last Updated: March 2, 2026
