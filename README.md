# TER2026 - Forest Definitions Knowledge Graph

> Building a semantic knowledge graph from forest definitions to enhance LLM responses via GraphRAG

**Status:** ✅ Production Ready | **Last Updated:** March 2, 2026

---

## Quick Links

📚 **[Documentation Index](docs/INDEX.md)** — Start here!

- ⚡ [5-Minute Quick Start](docs/QUICKSTART.md)
- 🚀 [Production Deployment Guide](docs/DEPLOYMENT.md)
- ✨ [What's New & Features](docs/ENHANCEMENTS.md)
- 📊 [Neo4j Query Examples](docs/QUERIES.md)

---

## What Is This?

A Python pipeline that:
1. **Extracts** forest definitions from documents (DOCX → CSV)
2. **Structures** them as RDF/SKOS knowledge graph
3. **Stores** in Neo4j for GraphRAG integration
4. **Tracks** everything with audit logging for compliance

## Key Features

✅ **Extraction with Audit Logging** — All 3,308 paragraphs per concept logged  
✅ **Neo4j Constraints** — 4 unique constraints prevent duplicates  
✅ **SI-Normalized Criteria** — 1,532 technical properties normalized  
✅ **Environment Variables** — Portable across Docker/CI/CD  
✅ **Idempotency Tested** — Safe to re-run without duplication  

## Graph Statistics

```
┌─────────────────────┬────────┐
│ Concepts            │   18   │
│ Definitions         │ 1,859  │
│ Sources             │   87   │
│ Countries           │   75   │
│ Technical Criteria  │  793   │
│ Relationships       │ 5,794  │
└─────────────────────┴────────┘
```

## Architecture

```
Document (DOCX)
     ↓ extract_definitions.py
   CSV (structured data)
     ↓ csv_to_rdf.py
 RDF/Turtle (SKOS ontology)
     ↓ rdf_to_neo4j.py
  Neo4j (graph database)
     ↓ CYPHER queries
 GraphRAG responses
```

## Quick Start

```bash
# 0. Verify setup (first time only)
python tools/check_setup.py

# 1. Install dependencies
pip install -r requirements.txt

# 2. Run pipeline
python scripts/extract_definitions.py
python scripts/csv_to_rdf.py
python scripts/rdf_to_neo4j.py --clear-db

# 3. Verify with tests
python tests/test_constraints.py
python tests/test_idempotency.py

# 4. Open Neo4j Browser
# http://localhost:7474
# Run: MATCH (c:Concept)-[:HAS_DEFINITION]->(d:Definition) RETURN c, d LIMIT 10
```

**For detailed setup:** → [5-Minute Quick Start](docs/QUICKSTART.md)

## Production Deployment

For production environments, see [Deployment Guide](docs/DEPLOYMENT.md):

```bash
# Configure Neo4j connection
export NEO4J_URI="bolt://prod-server:7687"
export NEO4J_PASSWORD="secure-password"

# Run with constraints
python scripts/rdf_to_neo4j.py
```

**Docker:** See [Deployment Guide](docs/DEPLOYMENT.md#mode-3-docker-container)  
**CI/CD:** See [Deployment Guide](docs/DEPLOYMENT.md#mode-4-github-actions-cicd)

## Project Structure

```
TER2026/
├── config.py                        # Centralized configuration
├── requirements.txt                 # Python dependencies
├── README.md                        # You are here
│
├── docs/                            # Documentation (START HERE)
│   ├── INDEX.md                    # Navigation guide
│   ├── QUICKSTART.md               # 5-minute setup
│   ├── DEPLOYMENT.md               # Production guide
│   ├── ENHANCEMENTS.md             # Features & improvements
│   └── QUERIES.md                  # Neo4j query examples
│
├── scripts/                         # Main pipeline scripts
│   ├── extract_definitions.py      # Extract DOCX → CSV (with audit logging)
│   ├── csv_to_rdf.py               # CSV → RDF/Turtle (SKOS ontology)
│   └── rdf_to_neo4j.py             # RDF → Neo4j (with constraints)
│
├── tests/                           # Verification & testing scripts
│   ├── test_constraints.py         # Verify constraints exist
│   └── test_idempotency.py         # Test duplicate prevention
│
├── tools/                           # Maintenance utilities
│   └── check_setup.py              # Pre-flight verification
│
├── csv/                             # Extracted definitions (generated)
├── data/                            # RDF/Turtle files (generated)
├── logs/                            # Audit & error logs (generated)
├── diagrams/                        # Visualizations
└── outputs/                         # Generated outputs
```

## Features Implemented

### Extraction with Audit Logging
- All paragraphs logged: `logs/extraction_audit.log` (5.2 MB)
- Skip reasons tracked for debugging
- Statistics per concept

### Database Safety
- 4 unique constraints preventing duplicates
- Idempotency tested and verified
- Automatic constraint creation with index conflict resolution

### Production-Ready Configuration
- Environment variables for all credentials
- No hardcoded secrets
- Docker & CI/CD ready

### Enhanced Data
- SI-normalized technical criteria (1,532 values)
- SYNONYM_OF relationships for semantic equivalence
- Multilingual alt_labels for each concept

## Verification

All enhancements have been tested and verified:

```bash
# Check constraints in Neo4j
python check_constraints.py
# Output: ✓ Found 4 constraints

# Test duplicate prevention
python test_idempotency.py
# Output: ✓ PASS: No duplicates created!

# Review extraction audit trail
tail logs/extraction_audit.log
```

## Next Steps

1. **New to the project?** → Read [Documentation Index](docs/INDEX.md)
2. **Want to deploy?** → See [Deployment Guide](docs/DEPLOYMENT.md)
3. **Need examples?** → Check [Neo4j Queries](docs/QUERIES.md)
4. **Want to learn more?** → Browse [Features & Enhancements](docs/ENHANCEMENTS.md)

## Need Help?

- **Setup issues?** → [Quick Start](docs/QUICKSTART.md#troubleshooting)
- **Production concerns?** → [Deployment Guide](docs/DEPLOYMENT.md#troubleshooting)
- **Query questions?** → [Neo4j Examples](docs/QUERIES.md)

---

**For comprehensive documentation, start with [docs/INDEX.md](docs/INDEX.md)**

```
Project: TER2026 | Knowledge Graph for Forest Definitions  
Status: ✅ Production Ready | Build: March 2, 2026
```
