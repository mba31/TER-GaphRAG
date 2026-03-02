#!/usr/bin/env python3
"""Test idempotency by importing RDF twice without clearing database."""

import subprocess
import sys
from pathlib import Path

# Add parent directory to path for config import
sys.path.insert(0, str(Path(__file__).parent.parent))

from neo4j import GraphDatabase
import config

def get_stats():
    """Get current graph statistics."""
    driver = GraphDatabase.driver(config.NEO4J_URI, auth=(config.NEO4J_USER, config.NEO4J_PASSWORD))
    try:
        with driver.session() as session:
            stats = {}
            stats['concept_count'] = session.run("MATCH (c:Concept) RETURN count(c)").single()[0]
            stats['definition_count'] = session.run("MATCH (d:Definition) RETURN count(d)").single()[0]
            stats['relationship_count'] = session.run("MATCH ()-[r]->() RETURN count(r)").single()[0]
            return stats
    finally:
        driver.close()

print("\n" + "=" * 60)
print("Idempotency Test: Running RDF Import Twice")
print("=" * 60)

# Get baseline stats
print("\n[1] Getting baseline statistics...")
baseline = get_stats()
print(f"    Concepts: {baseline['concept_count']}")
print(f"    Definitions: {baseline['definition_count']}")
print(f"    Relationships: {baseline['relationship_count']}")

# Run import without clearing database
print("\n[2] Running second RDF import (WITHOUT clearing database)...")
print("    This should NOT create duplicates due to constraints...")
result = subprocess.run([
    sys.executable,
    'scripts/rdf_to_neo4j.py'
    # Note: NO --clear-db flag, so constraints should prevent duplicates
], capture_output=True, text=True)

# Check if import ran successfully
if result.returncode == 0:
    print("    [OK] Import completed")
else:
    print(f"    [WARN] Import returned code {result.returncode}")
    # Print any error output
    if result.stderr:
        print(f"    Errors: {result.stderr[:200]}")

# Get stats after second import
print("\n[3] Getting statistics after second import...")
after_second = get_stats()
print(f"    Concepts: {after_second['concept_count']}")
print(f"    Definitions: {after_second['definition_count']}")
print(f"    Relationships: {after_second['relationship_count']}")

# Verify idempotency
print("\n[4] Idempotency Verification:")
concept_changed = after_second['concept_count'] != baseline['concept_count']
definition_changed = after_second['definition_count'] != baseline['definition_count']
relationship_changed = after_second['relationship_count'] != baseline['relationship_count']

if not (concept_changed or definition_changed or relationship_changed):
    print("    ✓ PASS: No duplicates created!")
    print("    ✓ Constraints successfully prevented duplicate insertions")
else:
    print("    ✗ FAIL: Duplicates were created!")
    if concept_changed:
        print(f"      - Concepts changed: {baseline['concept_count']} → {after_second['concept_count']}")
    if definition_changed:
        print(f"      - Definitions changed: {baseline['definition_count']} → {after_second['definition_count']}")
    if relationship_changed:
        print(f"      - Relationships changed: {baseline['relationship_count']} → {after_second['relationship_count']}")

print("\n" + "=" * 60)
