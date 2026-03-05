#!/usr/bin/env python3
"""
LEARNING GUIDE - Mini Pipeline
==============================

This is a step-by-step walkthrough of the pipeline.
Run this file to understand each phase.

Usage:
  python TUTORIAL.py
"""

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def main():
    print_section("🎓 MINI PIPELINE TUTORIAL")
    
    print("This example shows the COMPLETE WORKFLOW in 3 steps:")
    print()
    
    # Phase 1
    print_section("PHASE 1: Data Input")
    print("File: 1_sample_data.csv")
    print()
    print("Contains raw definitions from different sources:")
    print("  - FAO (Food and Agriculture Organization)")
    print("  - UNFCCC (UN Climate Convention)")
    print("  - National governments")
    print()
    print("Fields: source, year, definition_text, country")
    print("This is YOUR raw data.")
    print()
    
    # Phase 2
    print_section("PHASE 2: Extraction (2_extract.py)")
    print("Input:  1_sample_data.csv")
    print("Output: extracted_definitions.csv")
    print()
    print("What it does:")
    print("  1. Read CSV file")
    print("  2. Extract years using REGEX: r'\\d{4}' (4 digits)")
    print("  3. Clean whitespace from definitions")
    print("  4. Generate unique IDs: def_{country}_{year}_{seq}")
    print("  5. Write structured CSV")
    print()
    print("Key lesson: Regex is simple but powerful!")
    print()
    
    # Phase 3
    print_section("PHASE 3: Knowledge Graph (3_to_rdf.py)")
    print("Input:  extracted_definitions.csv")
    print("Output: forest_definitions.ttl (RDF/Turtle)")
    print()
    print("What it does:")
    print("  1. Create RDF graph using rdflib")
    print("  2. Define namespaces (skos, rdfs, ex)")
    print("  3. For each row:")
    print("     - Create URI: ex:def_brazil_2015_001")
    print("     - Add RDF triples (subject-predicate-object)")
    print("     - Examples:")
    print("       · <def_brazil_2015_001> rdf:type skos:Concept")
    print("       · <def_brazil_2015_001> skos:definition \"...definition...\"")
    print("  4. Serialize to Turtle format")
    print()
    print("Key lesson: RDF is semantic - machines can understand it!")
    print()
    
    # Summary
    print_section("SUMMARY: The Complete Flow")
    print()
    print("  Raw CSV          Extraction         Structured        RDF Graph")
    print("  -------          ----------         ---------         ---------")
    print()
    print("  Raw text   -->   Regex cleanup  -->  Structured CSV  -->  Turtle TTL")
    print("  (messy)          (patterns)          (clean data)        (semantic)")
    print()
    print("This is exactly how TER2026 works, just more complex!")
    print()
    
    # Next steps
    print_section("NEXT STEPS: What to Learn")
    print()
    print("1. EXTRACTION (2_extract.py)")
    print("   - Try different REGEX patterns")
    print("   - Handle edge cases (missing data, weird formatting)")
    print("   - Extract more fields (organization, criteria)")
    print()
    print("2. RDF/SEMANTIC (3_to_rdf.py)")
    print("   - Learn SKOS vocabulary")
    print("   - Add more relationships between concepts")
    print("   - Query RDF graphs with SPARQL")
    print()
    print("3. ADVANCED (Main project)")
    print("   - Add LLM for complex cases")
    print("   - Process PDF instead of text")
    print("   - Import into knowledge graph database (Neo4j, Virtuoso)")
    print()
    
    print_section("RUN THE PIPELINE")
    print()
    print("  python 2_extract.py          # Generate extracted_definitions.csv")
    print("  python 3_to_rdf.py           # Generate forest_definitions.ttl")
    print()
    print("Then check the output files!")
    print()

if __name__ == "__main__":
    main()
