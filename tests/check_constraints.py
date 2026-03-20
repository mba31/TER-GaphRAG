#!/usr/bin/env python3
"""Check Neo4j constraints and indexes."""

import sys
from pathlib import Path

# Add parent directory to path for config import
sys.path.insert(0, str(Path(__file__).parent.parent))

from neo4j import GraphDatabase
import config

driver = GraphDatabase.driver(config.NEO4J_URI, auth=(config.NEO4J_USER, config.NEO4J_PASSWORD))

try:
    with driver.session() as session:
        # Check existing constraints
        print("\n" + "="*60)
        print("Neo4j Constraint Analysis")
        print("="*60)
        
        result = session.run('SHOW CONSTRAINTS')
        constraints = result.data()
        
        if constraints:
            print(f"\n✓ Found {len(constraints)} constraints:")
            for c in constraints:
                print(f"  - {c.get('name', 'unnamed')}: {c.get('description', '')}")
        else:
            print("\n✗ No constraints found")
        
        # Check existing indexes
        print("\n✓ Indexes in Neo4j:")
        result = session.run('SHOW INDEXES')
        indexes = result.data()
        for idx in indexes:
            print(f"  - {idx.get('name', 'unnamed')}: {idx.get('description', '')}")
        
        # Check some graph statistics
        print("\n✓ Graph Statistics:")
        queries = {
            "Concepts": "MATCH (c:Concept) RETURN count(c)",
            "Definitions": "MATCH (d:Definition) RETURN count(d)",
            "Sources": "MATCH (s:Source) RETURN count(s)",
            "Countries": "MATCH (c:Country) RETURN count(c)",
            "ENVO Terms": "MATCH (e:ENVOTerm) RETURN count(e)",
            "ENVO Match Links": "MATCH (:Concept)-[r:EXACT_MATCH|CLOSE_MATCH|BROAD_MATCH|NARROW_MATCH]->(:ENVOTerm) RETURN count(r)",
            "Relationships": "MATCH ()-[r]->() RETURN count(r)"
        }
        
        for label, query in queries.items():
            result = session.run(query)
            count = result.single()[0]
            print(f"  - {label}: {count}")

finally:
    driver.close()
