#!/usr/bin/env python3
"""
Mini Pipeline Step 4: RDF to Neo4j
==================================
Load RDF/Turtle data into Neo4j graph database.

Input:  forest_definitions.ttl (from 3_to_rdf.py)
Output: Data imported into Neo4j

Requirements:
  - Neo4j database running (see instructions below)
  - python-neo4j package

Neo4j Setup (local):
  Option 1: Docker
    docker run --name neo4j -p 7687:7687 -p 7474:7474 \\
      -e NEO4J_AUTH=neo4j/password123 neo4j:latest

  Option 2: Download from https://neo4j.com/download/
    Then use default bolt://localhost:7687 with neo4j/neo4j credentials

Configuration:
  Edit NEO4J_URL, NEO4J_USER, NEO4J_PASSWORD below to match your setup.
"""

from pathlib import Path
from rdflib import Graph, Namespace
from rdflib.namespace import RDF, RDFS, SKOS

# Neo4j configuration
NEO4J_URL = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "password123"  # Change this to your Neo4j password


def import_rdf_to_neo4j():
    """Load RDF/Turtle file into Neo4j."""
    ttl_file = Path("forest_definitions.ttl")

    if not ttl_file.exists():
        print(f"❌ Missing {ttl_file}")
        return

    try:
        from neo4j import GraphDatabase
    except ImportError:
        print("❌ neo4j package required. Install with:")
        print("   pip install neo4j")
        return

    print(f"📖 Loading {ttl_file}...")
    # Load RDF graph
    rdf_graph = Graph()
    rdf_graph.parse(ttl_file, format="turtle")
    num_triples = len(rdf_graph)
    print(f"   ✓ Loaded {num_triples} RDF triples")

    # Connect to Neo4j
    print(f"\n🔗 Connecting to Neo4j at {NEO4J_URL}...")
    try:
        driver = GraphDatabase.driver(NEO4J_URL, auth=(NEO4J_USER, NEO4J_PASSWORD))
        driver.verify_connectivity()
        print("   ✓ Connected to Neo4j")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        print(f"   Make sure Neo4j is running at {NEO4J_URL}")
        print(f"   Try: docker run --name neo4j -p 7687:7687 -e NEO4J_AUTH={NEO4J_USER}/password neo4j:latest")
        return

    # Define namespaces
    EX = Namespace("http://ter2026-project.org/forest#")

    # Extract core data from RDF
    concepts = set()
    definitions = set()
    sources = set()

    for s, p, o in rdf_graph:
        # Find concepts
        if p == RDF.type and o == SKOS.Concept:
            concepts.add(str(s))

        # Find definitions
        if str(p).endswith("Definition"):
            definitions.add(str(s))

        # Find sources
        if str(p).endswith("Source"):
            sources.add(str(o))

    print(f"\n📊 Data summary:")
    print(f"   Concepts: {len(concepts)}")
    print(f"   Definitions: {len(definitions)}")
    print(f"   Sources: {len(sources)}")

    # Import into Neo4j
    print(f"\n💾 Importing into Neo4j...")

    with driver.session() as session:
        # Create concept nodes
        for concept_uri in list(concepts)[:10]:  # Limit to first 10 for demo
            concept_name = concept_uri.split("#")[-1]
            session.run(
                "CREATE (:Concept {uri: $uri, name: $name})",
                uri=concept_uri,
                name=concept_name,
            )
            print(f"   ✓ Created Concept: {concept_name}")

        # Create definition nodes
        for def_uri in list(definitions)[:10]:  # Limit to first 10 for demo
            def_name = def_uri.split("#")[-1]
            session.run(
                "CREATE (:Definition {uri: $uri, id: $id})",
                uri=def_uri,
                id=def_name,
            )
            print(f"   ✓ Created Definition: {def_name}")

        # Create source nodes
        for source_uri in list(sources)[:5]:  # Limit to first 5 for demo
            source_name = str(source_uri)
            session.run(
                "CREATE (:Source {uri: $uri, name: $name})",
                uri=source_uri,
                name=source_name,
            )
            print(f"   ✓ Created Source: {source_name}")

    driver.close()
    print(f"\n✅ Import complete!")
    print(f"   Access Neo4j browser: http://localhost:7474")
    print(f"   Query example: MATCH (n) RETURN n LIMIT 10")


if __name__ == "__main__":
    import_rdf_to_neo4j()
