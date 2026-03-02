#!/usr/bin/env python3
"""Fix missing concept_uri_unique constraint."""

from neo4j import GraphDatabase
import config

driver = GraphDatabase.driver(config.NEO4J_URI, auth=(config.NEO4J_USER, config.NEO4J_PASSWORD))

try:
    with driver.session() as session:
        print("=" * 60)
        print("Fixing concept_uri_unique Constraint")
        print("=" * 60)
        
        # Step 1: Check current index
        print("\n[1] Checking for existing Concept indexes...")
        result = session.run("SHOW INDEXES WHERE entityType = 'NODE' AND labelsOrTypes CONTAINS 'Concept'")
        indexes = result.data()
        
        if indexes:
            for idx in indexes:
                print(f"    Found: {idx.get('name')} on {idx.get('description')}")
        else:
            print("    No Concept indexes found")
        
        # Step 2: Drop the conflicting index if it exists
        print("\n[2] Dropping concept_uri index (if exists)...")
        try:
            session.run("DROP INDEX concept_uri IF EXISTS")
            print("    [OK] Index dropped")
        except Exception as e:
            print(f"    [INFO] {e}")
        
        # Step 3: Create the constraint
        print("\n[3] Creating concept_uri_unique constraint...")
        try:
            session.run("CREATE CONSTRAINT concept_uri_unique IF NOT EXISTS FOR (c:Concept) REQUIRE c.uri IS UNIQUE")
            print("    [OK] Constraint created")
        except Exception as e:
            print(f"    [ERROR] {e}")
        
        # Step 4: Verify constraint was created
        print("\n[4] Verifying all constraints...")
        result = session.run("SHOW CONSTRAINTS")
        constraints = result.data()
        
        expected = ['concept_uri_unique', 'definition_uri_unique', 'source_uri_unique', 'country_uri_unique']
        created = [c.get('name', '') for c in constraints]
        
        print(f"    Expected: {expected}")
        print(f"    Found:    {created}")
        
        missing = set(expected) - set(created)
        if missing:
            print(f"\n    ✗ Missing constraints: {missing}")
        else:
            print(f"\n    ✓ All {len(expected)} constraints created successfully!")

finally:
    driver.close()
