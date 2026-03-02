# Documentation Index

Welcome to TER2026 documentation. Choose your guide based on your needs:

---

## 🚀 Getting Started (New Users)

Start here if you're new to the project:

1. **[Quick Start (5 min)](QUICKSTART.md)** — One-click setup guide
   - Install dependencies
   - Run the pipeline
   - Verify output
   
2. **[README](../README.md)** — Project overview
   - Architecture diagram
   - Features and goals
   - What the project does

---

## 📦 Running the System

Choose based on your deployment scenario:

### For Local Development
→ [Quick Start](QUICKSTART.md) (5 minutes)

### For Production Deployment
→ [Deployment & Production Readiness](DEPLOYMENT.md)
- Environment variables and secrets management
- Multiple deployment modes (Docker, CI/CD, bare metal)
- Security checklist
- Monitoring and troubleshooting

---

## 🔧 Understanding the Code

Explore the enhancements and capabilities:

### What's New in This Version?
→ [Enhancements](ENHANCEMENTS.md)
- SI-normalized technical criteria (1,532 values)
- SYNONYM_OF relationships
- Improved extraction with audit logging
- Neo4j unique constraints for duplicate prevention

### Production Features
→ [Deployment & Production Readiness](DEPLOYMENT.md) — Detailed explanation:
- Extraction audit logging (all paragraphs tracked)
- Database constraints (prevent duplicates)
- Centralized configuration (environment variables)
- Idempotency testing (verified working)

---

## 📊 Querying the Graph

Learn how to query the Neo4j database:

→ [Neo4j Queries](QUERIES.md)
- Basic concept queries
- Finding definitions by country
- Searching for alternative labels
- Advanced relationship queries
- Graph statistics

---

## 📈 Current System Statistics

**Graph Size:**
- 18 Concepts
- 1,859 Definitions
- 87 Sources
- 75 Countries
- 793 Technical Criteria (SI-normalized)
- 5,794 Relationships

**Features:**
- ✅ Multilingual support (alt_labels)
- ✅ SI-normalized technical criteria
- ✅ Complete audit trail of extracted data
- ✅ Duplicate prevention via constraints
- ✅ Docker & CI/CD ready

---

## 📚 Document Structure

```
docs/
├── INDEX.md                      # You are here - Navigation guide
├── QUICKSTART.md                 # 5-minute setup
├── DEPLOYMENT.md                 # Production deployment & features
├── ENHANCEMENTS.md               # New features explained
├── QUERIES.md                    # Neo4j query examples
└── [root] README.md              # Project overview
```

---

## 🎯 Quick Reference

### Install & Run
```bash
pip install -r requirements.txt
python scripts/extract_definitions.py
python scripts/csv_to_rdf.py
python scripts/rdf_to_neo4j.py --clear-db
```

### Configure for Production
```bash
export NEO4J_URI="bolt://prod-server:7687"
export NEO4J_PASSWORD="your-secret"
python scripts/rdf_to_neo4j.py
```

### Check Constraints in Neo4j
```cypher
SHOW CONSTRAINTS
# Should show all 4 constraints:
# - concept_uri_unique
# - definition_uri_unique
# - source_uri_unique
# - country_uri_unique
```

### View Extraction Audit Trail
```bash
tail -100 logs/extraction_audit.log
grep "ERROR\|FAIL" logs/extraction_errors.log
```

---

## 🔗 Related Files

**Python Scripts:**
- `scripts/extract_definitions.py` — Extract from DOCX with audit logging
- `scripts/csv_to_rdf.py` — Convert to RDF/Turtle
- `scripts/rdf_to_neo4j.py` — Import to Neo4j with constraints
- `config.py` — Centralized configuration

**Data:**
- `csv/criteria.csv` — Main definitions
- `csv/definition.csv` — Technical criteria
- `data/forest_definitions.ttl` — RDF format
- `logs/` — Audit and error logs

---

## ❓ FAQ

**Q: How do I update the source document?**  
A: Replace `docs/sources/forest_definitions.docx`, then run the full pipeline.

**Q: Can I run on a remote Neo4j server?**  
A: Yes! Set `NEO4J_URI` environment variable: `export NEO4J_URI="bolt://remote-server:7687"`

**Q: What if the import fails?**  
A: Check `logs/extraction_errors.log` for details. See [Deployment.md](DEPLOYMENT.md#troubleshooting) troubleshooting section.

**Q: Will running the import twice create duplicates?**  
A: No! Constraints prevent duplicates. Verified with idempotency testing.

---

**Last Updated:** March 2, 2026  
**Status:** ✅ Production Ready

For detailed information, see the specific guides above.
