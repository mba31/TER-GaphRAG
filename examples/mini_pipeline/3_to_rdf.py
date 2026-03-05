#!/usr/bin/env python3
"""
Mini RDF Generator
==================
Reads extracted CSV, creates knowledge graph in RDF/Turtle format.

Input:  extracted_definitions.csv
Output: forest_definitions.ttl
"""

import csv
from pathlib import Path
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, RDFS, SKOS

def main():
    input_file = Path("extracted_definitions.csv")
    output_file = Path("forest_definitions.ttl")
    
    if not input_file.exists():
        print(f"❌ Missing {input_file}")
        print("   Run: python 2_extract.py first")
        return
    
    print(f"📖 Reading {input_file}...")
    
    # Create RDF graph
    graph = Graph()
    
    # Define namespaces
    EX = Namespace("http://ter2026.org/forest#")
    graph.bind("skos", SKOS)
    graph.bind("rdfs", RDFS)
    graph.bind("rdf", RDF)
    graph.bind("ex", EX)
    
    # Read CSV and add to graph
    with open(input_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Create URI for definition
            def_id = row["id"]
            def_uri = EX[def_id]
            
            # Add RDF triples
            graph.add((def_uri, RDF.type, SKOS.Concept))
            graph.add((def_uri, SKOS.prefLabel, Literal(row["concept"])))
            graph.add((def_uri, SKOS.definition, Literal(row["definition"])))
            graph.add((def_uri, SKOS.notation, Literal(row["id"])))
            
            # Add metadata
            if row["source"]:
                graph.add((def_uri, RDFS.comment, Literal(f"Source: {row['source']}")))
            if row["year"] != "unknown":
                graph.add((def_uri, EX.year, Literal(int(row["year"]))))
            if row["country"]:
                graph.add((def_uri, EX.country, Literal(row["country"])))
            
            print(f"  ✓ {row['country']} - {row['id']}")
    
    print(f"\n💾 Writing {output_file}...")
    graph.serialize(destination=output_file, format="turtle")
    
    print(f"✅ Done! Check {output_file}")
    print(f"\n📊 Graph stats:")
    print(f"   Triples: {len(graph)}")
    print(f"   Concepts: {len(list(graph.subjects(RDF.type, SKOS.Concept)))}")

if __name__ == "__main__":
    main()
