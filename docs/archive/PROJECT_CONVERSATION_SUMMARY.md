# TER2026 Project - Conversation Summary

**Project:** Forest Definitions Knowledge Graph  
**Purpose:** Knowledge representation system for managing and comparing forest definitions from different organizations (FAO, UNFCCC, etc.)

---

## Initial Project State

### What It Does

This is a knowledge representation project that:
- **Captures** forest definitions from different entities/organizations
- **Compares** how different organizations define "forest" with varying technical criteria
- **Structures** the data as CSV files and RDF knowledge graphs
- **Stores** definitions with metadata (country, organization, year, criteria)

### Core Components

**Data Structure:**
- `csv/criteria.csv` - Main definitions with metadata
- `csv/definition.csv` - Technical criteria (area, height, canopy cover)
- `data/forest_definitions.ttl` - RDF/Turtle format knowledge graph
- Document processing from `docs/sources/forest_definitions.docx`

**Technical Criteria Extracted:**
- Minimum area (hectares)
- Canopy/crown cover (percentage)
- Tree height (meters)
- Width measurements

---

## Key Technical Implementations

### 1. Extraction Architecture

**Initial System:**
- Regex-based extraction from DOCX documents
- Country detection (90+ countries)
- Organization detection (FAO, UNFCCC, IPCC, etc.)
- Year parsing from definition text
- Criteria extraction with pattern matching

**Script:** `scripts/extract_definitions.py`
- Processes paragraphs sequentially
- Filters by concept keywords ("forest", "deforestation", etc.)
- Requires definition keywords ("means", "defined as", "refers to")
- Exports to structured CSV format

### 2. Audit Logging System

**Implementation:**
- Added comprehensive logging for data validation
- Tracks all paragraphs processed (not just successful extractions)
- Separate error log for skipped/failed paragraphs

**Log Files:**
- `outputs/extraction_audit.log` - All paragraph processing
- `outputs/extraction_errors.log` - Failures and skips
- `outputs/extraction.log` - General operation log

**Configuration Flags:**
```python
ENABLE_AUDIT_LOG = True
ENABLE_ERROR_LOG = True
```

### 3. SI Unit Normalization

**Problem:** Mixed units in source documents (acres, feet, etc.)

**Solution:** Automatic conversion to SI units
- Area: Convert acres → hectares
- Height: Convert feet → meters
- Percentage: Already standardized

**Implementation:**
```python
criteria['min_area_si'] = value * 0.404686  # acres to hectares
criteria['min_height_si'] = value * 0.3048  # feet to meters
```

### 4. Synonym Detection

**Country Aliases:**
- "United States of America" → "USA"
- "United Kingdom" → "UK"
- "U.S." / "U.S.A." → "USA"

**Organization Normalization:**
- "UN-FAO" / "FAO" → "UN-FAO"
- "UNFCCC" / "UN-FCCC" → "UNFCCC"
- Source tag parsing: `(UN-FCCC 2001)` → organization="UNFCCC"

### 5. RDF/SKOS Knowledge Graph

**Generation:** `scripts/csv_to_rdf.py`

**Structure:**
```turtle
@prefix ex: <http://ter2026-project.org/forest#>
@prefix skos: <http://www.w3.org/2004/02/skos/core#>

ex:Afforestation a skos:Concept ;
    skos:prefLabel "Afforestation"@en ;
    skos:definition "..." .

ex:def_brazil_2015_001 a ex:Definition ;
    ex:hasCountry "Brazil" ;
    ex:hasYear "2015" ;
    ex:definitionText "..." .
```

**Statistics:**
- 19,955 triples generated
- Multiple concepts: Forest, Deforestation, Afforestation, etc.
- ~1,859 definitions extracted per run

### 6. Neo4j Integration

**Script:** `scripts/rdf_to_neo4j.py`

**Node Types:**
- `Concept` - Forest definition concepts
- `Definition` - Individual definitions
- `Source` - Organizations/countries
- `TechnicalCriteria` - Extracted measurements

**Relationship Types:**
- `(:Concept)-[:HAS_DEFINITION]->(:Definition)`
- `(:Definition)-[:FROM_SOURCE]->(:Source)`
- `(:Definition)-[:HAS_CRITERIA]->(:TechnicalCriteria)`

**Connection:**
```python
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "umontpellier"
```

### 7. Data Integrity - Constraints

**Problem:** Duplicate nodes could be created on multiple imports

**Solution:** Unique constraints on URIs

**Constraints Created:**
```cypher
CREATE CONSTRAINT concept_uri IF NOT EXISTS
FOR (c:Concept) REQUIRE c.uri IS UNIQUE;

CREATE CONSTRAINT definition_uri IF NOT EXISTS
FOR (d:Definition) REQUIRE d.uri IS UNIQUE;

CREATE CONSTRAINT source_uri IF NOT EXISTS
FOR (s:Source) REQUIRE s.uri IS UNIQUE;

CREATE CONSTRAINT criteria_uri IF NOT EXISTS
FOR (tc:TechnicalCriteria) REQUIRE tc.uri IS UNIQUE;
```

**Configuration:**
```python
CREATE_CONSTRAINTS = True  # Prevent duplicates on import
CLEAR_DATABASE_ON_IMPORT = False  # Set to True to clear existing data
```

**Constraint Verification:**
- Created `scripts/check_neo4j_constraints.py`
- Verifies all 4 constraints exist
- Handles index-to-constraint migration
- Reports constraint status before import

**Issue Encountered:**
- Existing index on `concept_uri` needed to be dropped before creating constraint
- Script enhanced to detect and resolve this automatically

### 8. Idempotency Testing

**Script:** `tests/test_idempotency.py`

**Purpose:** Ensure extraction is deterministic and reproducible

**Tests:**
1. Run extraction twice on same input
2. Compare outputs byte-by-byte
3. Verify no randomness in processing
4. Confirm stable RDF generation

**Result:** Extraction is idempotent (same input → same output)

### 9. Schema Validation

**Script:** `tests/check_constraints.py`

**Validations:**
- Required fields present (country, organization, year)
- URI uniqueness
- Value ranges valid (years 1800-2100)
- SKOS compliance in RDF
- Relationship integrity

---

## Configuration Management

**Centralized Config:** `config.py`

Key settings:
```python
# Paths
DOCUMENT_PATH = DOCS_DIR / "forest_definitions.docx"
CRITERIA_CSV = CSV_DIR / "criteria.csv"
RDF_OUTPUT = RDF_DIR / "forest_definitions.ttl"

# Extraction
CONCEPTS_TO_EXTRACT = ["forest", "deforestation", ...]
DEFINITION_KEYWORDS = ["means", "defined as", ...]

# Logging
ENABLE_AUDIT_LOG = True
ENABLE_ERROR_LOG = True

# Neo4j
NEO4J_URI = "bolt://localhost:7687"
CREATE_CONSTRAINTS = True
```

**Environment Variables Support:**
- `NEO4J_URI` can be set via environment
- `NEO4J_PASSWORD` for security
- Portable across Docker/CI/CD

---

## Data Flow Pipeline

```
1. DOCX Document
   └─ docs/sources/forest_definitions.docx
   
2. Extraction (Regex)
   └─ python scripts/extract_definitions.py
   └─ Generates: csv/criteria.csv, csv/definition.csv
   └─ Logs: outputs/extraction_audit.log
   
3. RDF Generation
   └─ python scripts/csv_to_rdf.py
   └─ Generates: data/forest_definitions.ttl (19,955 triples)
   
4. Neo4j Import
   └─ python scripts/rdf_to_neo4j.py --clear-db
   └─ Creates: Concepts, Definitions, Sources, Criteria nodes
   └─ Enforces: 4 unique constraints
   
5. Validation
   └─ python tests/check_constraints.py
   └─ python tests/test_idempotency.py
```

---

## Key Statistics

**Extraction Performance:**
- **Paragraphs processed:** 3,308 per concept (multiple concepts)
- **Definitions extracted:** ~1,859 per full run
- **Skip rate:** 96.88% (legitimate filtering)
- **Runtime:** < 5 minutes for full extraction

**Knowledge Graph:**
- **Triples:** 19,955 in RDF graph
- **Concepts:** 18 (Forest, Deforestation, Afforestation, etc.)
- **Definitions:** 1,859
- **Sources:** 87 organizations/countries
- **Countries:** 75 represented
- **Technical Criteria:** 793 measurements

**Neo4j Database:**
- **Nodes:** ~2,700+ (Concepts + Definitions + Sources + Criteria)
- **Relationships:** ~5,794
- **Constraints:** 4 unique URI constraints
- **Indexes:** Automatic on constraint properties

---

## Technical Decisions

### Why Regex Over NLP?
- Definitions follow structured patterns
- Organizations use consistent terminology
- High precision with known keywords
- No GPU/model dependencies needed
- Fast processing (< 5 minutes vs hours)

### Why SKOS Ontology?
- Standard for concept schemes
- Semantic web interoperability
- Built-in vocabulary for definitions
- Easy to link with other ontologies

### Why Neo4j?
- Graph relationships are natural for definition networks
- Cypher queries intuitive for relationships
- GraphRAG integration ready
- Constraint enforcement prevents duplicates

### Why SI Units?
- International standard
- Consistent comparisons across definitions
- Original values preserved alongside normalized

---

## Constraint Implementation Details

**Challenge:** Neo4j constraints vs indexes

**Discovery:**
- Initial indexes created: `CREATE INDEX ON :Concept(uri)`
- Needed upgrade to constraints: `REQUIRE c.uri IS UNIQUE`
- Conflict: Can't have both index and constraint on same property

**Resolution:**
1. Check if constraint exists: `SHOW CONSTRAINTS`
2. If index exists: `DROP INDEX concept_uri`
3. Create constraint: `CREATE CONSTRAINT concept_uri ...`
4. Verify: 4 constraints operational

**Script Enhancement:**
- `check_neo4j_constraints.py` checks all constraints
- Reports status before import
- Handles migration automatically in import script

---

## Project State at Summary Point

✅ **Extraction:** Regex-based, audit-logged, SI-normalized  
✅ **RDF:** 19,955 triples, SKOS-compliant  
✅ **Neo4j:** Imported with 4 unique constraints  
✅ **Validation:** Idempotency tested, constraints verified  
✅ **Documentation:** Configuration centralized, logs detailed  
✅ **Performance:** < 5 minutes end-to-end  

**Next Steps (at time of summary):**
- Verify constraint creation in Neo4j ✓
- Run full import with constraints ✓
- Test duplicate prevention ✓
- Document query examples

---

## Key Files Reference

| File | Purpose | Lines |
|------|---------|-------|
| `scripts/extract_definitions.py` | Main extraction | ~800 |
| `scripts/csv_to_rdf.py` | RDF generation | ~250 |
| `scripts/rdf_to_neo4j.py` | Neo4j import | ~350 |
| `scripts/check_neo4j_constraints.py` | Constraint verification | ~80 |
| `tests/check_constraints.py` | Schema validation | ~150 |
| `tests/test_idempotency.py` | Reproducibility test | ~120 |
| `config.py` | Central configuration | ~160 |
| `data/forest_definitions.ttl` | Knowledge graph | 22,794 |

---

**End of Summary**

This represents the project state and conversation through the Neo4j constraints implementation and verification phase.
