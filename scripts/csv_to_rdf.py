"""
CSV to RDF Converter
====================
Converts extracted forest definitions from CSV format to RDF/Turtle format
following the SKOS vocabulary and project ontology.

Input:
- csv/criteria.csv (main definitions)
- csv/definition.csv (technical criteria)

Output:
- data/forest_definitions.ttl (RDF Turtle format)

Author: TER2026 Project
Date: March 2026
"""

import csv
import re
import sys
from pathlib import Path
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, RDFS, SKOS, XSD

# Import config
sys.path.insert(0, str(Path(__file__).parent.parent))
import config


class CSVToRDFConverter:
    """Converts CSV definitions to RDF/Turtle format."""
    
    def __init__(self):
        """Initialize converter with namespaces and graph."""
        # Create RDF graph
        self.graph = Graph()
        
        # Define namespaces
        self.EX = Namespace("http://ter2026-project.org/forest#")
        self.SKOS = SKOS
        self.RDF = RDF
        self.RDFS = RDFS
        self.XSD = XSD
        
        # Bind namespaces to graph
        self.graph.bind("skos", SKOS)
        self.graph.bind("rdf", RDF)
        self.graph.bind("rdfs", RDFS)
        self.graph.bind("ex", self.EX)
        self.graph.bind("xsd", XSD)
        
        # Storage for definitions and criteria
        self.definitions_data = []
        self.criteria_data = []

        # Concept relationships with semantic types
        self.concept_relations = {
            # Actions affecting forests
            "Deforestation": {"target": "Forest", "relation": "affects"},
            "Afforestation": {"target": "Forest", "relation": "affects"},
            "Reforestation": {"target": "Forest", "relation": "affects"},
            "Degradation": {"target": "Forest", "relation": "affects"},
            "Forestation": {"target": "Forest", "relation": "affects"},
            "Regeneration": {"target": "Forest", "relation": "affects"},
            
            # Components of forests
            "Tree": {"target": "Forest", "relation": "partOf"},
            "Stand": {"target": "Forest", "relation": "partOf"},
            "Grove": {"target": "Forest", "relation": "partOf"},
            "Thicket": {"target": "Forest", "relation": "partOf"},
            
            # Related land types
            "Woodland": {"target": "Forest", "relation": "relatedTo"},
            "Woods": {"target": "Forest", "relation": "relatedTo"},
            "Other wooded land": {"target": "Forest", "relation": "relatedTo"},
            "Non-forest": {"target": "Forest", "relation": "oppositeOf"},
            
            # Synonyms (bidirectional semantic equivalence)
            "Woodland": {"target": "Woods", "relation": "synonymOf"},
            "Woods": {"target": "Woodland", "relation": "synonymOf"},
            
            # Management and measurement
            "Forestry": {"target": "Forest", "relation": "manages"},
            "Stocking": {"target": "Forest", "relation": "measures"},
            
            # Products
            "Timber": {"target": "Tree", "relation": "derivedFrom"}
        }
    
    def load_csv_data(self, criteria_path, definition_path):
        """
        Load data from CSV files.
        
        Args:
            criteria_path: Path to criteria.csv
            definition_path: Path to definition.csv
        """
        # Load criteria.csv
        print(f"[*] Loading {criteria_path}...")
        with open(criteria_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            self.definitions_data = list(reader)
        
        print(f"   Found {len(self.definitions_data)} definitions")
        
        # Load definition.csv
        print(f"[*] Loading {definition_path}...")
        with open(definition_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            self.criteria_data = list(reader)
        
        print(f"   Found {len(self.criteria_data)} criteria entries")
    
    def create_concept(self, label, alt_labels=None):
        """
        Create a SKOS Concept for the main term (e.g., Forest).
        
        Args:
            label: Preferred label for the concept
            alt_labels: Alternative labels (optional)
            
        Returns:
            URIRef for the created concept
        """
        # Create concept URI
        concept_uri = self.EX[label.replace(" ", "")]
        
        # Add concept type
        self.graph.add((concept_uri, RDF.type, SKOS.Concept))
        
        # Add preferred labels
        self.graph.add((concept_uri, SKOS.prefLabel, Literal(label, lang="en")))
        
        # Add alternative labels if provided
        if alt_labels:
            for alt_label in alt_labels:
                if alt_label.strip():
                    self.graph.add((concept_uri, SKOS.altLabel, Literal(alt_label.strip(), lang="en")))
        
        return concept_uri
    
    def create_source(self, source_name, year=None, url=None, organization=None, country=None, geographic_scope=None):
        """
        Create a Source entity.
        
        Args:
            source_name: Display name for source identity
            year: Year of the definition (optional)
            url: URL reference (optional)
            organization: Organization name (optional)
            country: Country name (optional)
            geographic_scope: Geographic scope (International/National/Local) (optional)
            
        Returns:
            URIRef for the created source
        """
        # Create source URI (without year to merge by organization)
        source_id = re.sub(r'[^A-Za-z0-9_-]+', '_', source_name).strip('_')
        if not source_id:
            source_id = "Unknown"
        if len(source_id) > 80:
            source_id = source_id[:80]
        source_uri = self.EX[f"Source_{source_id}"]
        
        # Add source type
        self.graph.add((source_uri, RDF.type, self.EX.Source))
        
        # Add source display name
        self.graph.add((source_uri, RDFS.label, Literal(source_name)))

        # Add organization name
        if organization:
            self.graph.add((source_uri, self.EX.orgName, Literal(organization)))

        # Add country if provided
        if country:
            self.graph.add((source_uri, self.EX.country, Literal(country)))
        
        # Add geographic scope if provided
        if geographic_scope:
            self.graph.add((source_uri, self.EX.geographicScope, Literal(geographic_scope)))

        
        # Add URL if provided
        if url:
            self.graph.add((source_uri, self.EX.url, Literal(url, datatype=XSD.anyURI)))
        
        return source_uri

    def create_country(self, country_name):
        """
        Create a Country entity.

        Args:
            country_name: Country name

        Returns:
            URIRef for the created country
        """
        country_id = re.sub(r'[^A-Za-z0-9_-]+', '_', country_name).strip('_')
        if not country_id:
            country_id = "Unknown"

        country_uri = self.EX[f"Country_{country_id}"]
        self.graph.add((country_uri, RDF.type, self.EX.Country))
        self.graph.add((country_uri, RDFS.label, Literal(country_name)))

        return country_uri
    
    def create_definition(self, definition_id, text, def_type, source_uri, geographic_scope=None, country=None, country_uri=None):
        """
        Create a Definition entity.
        
        Args:
            definition_id: Unique identifier for the definition
            text: Definition text
            def_type: Type of definition (Land Use, Land Cover, etc.)
            source_uri: URI of the source
            geographic_scope: Geographic scope (International/National/Local) (optional)
            country: Country where this definition applies (optional)
            country_uri: URI of Country node (optional)
            
        Returns:
            URIRef for the created definition
        """
        # Create definition URI
        def_uri = self.EX[f"Def_{definition_id}"]
        
        # Add definition type
        self.graph.add((def_uri, RDF.type, self.EX.Definition))
        
        # Add label
        # Create meaningful label from definition text (first 80 chars) or use definition_id
        if text and len(text.strip()) > 0:
            label = text[:80] + "..." if len(text) > 80 else text
        else:
            label = f"Definition {definition_id}"
        self.graph.add((def_uri, RDFS.label, Literal(label)))
        
        # Add source reference
        self.graph.add((def_uri, self.EX.hasSource, source_uri))
        
        # Add definition type
        self.graph.add((def_uri, self.EX.definitionType, Literal(def_type)))
        
        # Add geographic scope if provided
        if geographic_scope:
            self.graph.add((def_uri, self.EX.geographicScope, Literal(geographic_scope)))
        
        # Add country if provided
        if country:
            self.graph.add((def_uri, self.EX.country, Literal(country)))

        # Link definition to Country node if provided
        if country_uri:
            self.graph.add((def_uri, self.EX.appliesTo, country_uri))
        
        # Add definition text as note
        self.graph.add((def_uri, SKOS.note, Literal(text, lang="en")))
        
        return def_uri
    
    def add_criteria_to_definition(self, def_uri, criteria_list):
        """
        Add technical criteria to a definition.
        
        Args:
            def_uri: URI of the definition
            criteria_list: List of criteria dictionaries
        """
        if not criteria_list:
            return
        
        # Create blank node for criteria
        criteria_node = URIRef(f"{def_uri}_criteria")
        
        # Add criteria to definition
        self.graph.add((def_uri, self.EX.hasCriteria, criteria_node))
        
        # Add each criterion
        for criterion in criteria_list:
            criterion_name = criterion['criteria_name']
            value = criterion['value']
            unit = criterion['unit']
            value_si = criterion.get('value_si', '')
            
            # Create property name (e.g., minHeight, minArea)
            prop_name = ''.join(word.capitalize() if i > 0 else word 
                               for i, word in enumerate(criterion_name.split('_')))
            prop_uri = self.EX[prop_name]
            
            # Add criterion value with datatype
            try:
                float_value = float(value)
                self.graph.add((criteria_node, prop_uri, Literal(float_value, datatype=XSD.float)))
            except ValueError:
                self.graph.add((criteria_node, prop_uri, Literal(value)))
            
            # Add SI-normalized value if available
            if value_si:
                try:
                    si_float_value = float(value_si)
                    si_prop_uri = self.EX[f"{prop_name}SI"]
                    self.graph.add((criteria_node, si_prop_uri, Literal(si_float_value, datatype=XSD.float)))
                except ValueError:
                    pass  # Skip if value_si is not a number

    def add_concept_relations(self, concepts):
        """Add semantic relationships between Concept nodes."""
        relation_links = 0

        for source_label, rel_info in self.concept_relations.items():
            source_uri = concepts.get(source_label)
            target_uri = concepts.get(rel_info["target"])

            if not source_uri or not target_uri:
                continue

            # Add appropriate relationship predicate
            relation_type = rel_info["relation"]
            if relation_type == "affects":
                self.graph.add((source_uri, self.EX.affects, target_uri))
                relation_links += 1
            elif relation_type == "partOf":
                self.graph.add((source_uri, self.EX.partOf, target_uri))
                relation_links += 1
            elif relation_type == "relatedTo":
                self.graph.add((source_uri, self.EX.relatedTo, target_uri))
                relation_links += 1
            elif relation_type == "oppositeOf":
                self.graph.add((source_uri, self.EX.oppositeOf, target_uri))
                relation_links += 1
            elif relation_type == "manages":
                self.graph.add((source_uri, self.EX.manages, target_uri))
                relation_links += 1
            elif relation_type == "measures":
                self.graph.add((source_uri, self.EX.measures, target_uri))
                relation_links += 1
            elif relation_type == "derivedFrom":
                self.graph.add((source_uri, self.EX.derivedFrom, target_uri))
                relation_links += 1
            elif relation_type == "synonymOf":
                self.graph.add((source_uri, self.EX.synonymOf, target_uri))
                relation_links += 1

        return relation_links
    
    def convert(self):
        """Convert CSV data to RDF graph."""
        print("\n[*] Converting CSV to RDF...")
        
        # Track unique concepts, sources, and countries
        concepts = {}
        sources = {}
        countries = {}
        
        # Group criteria by definition_id
        criteria_by_def = {}
        for criterion in self.criteria_data:
            def_id = criterion['definition_id']
            if def_id not in criteria_by_def:
                criteria_by_def[def_id] = []
            criteria_by_def[def_id].append(criterion)
        
        # Process each definition
        for idx, row in enumerate(self.definitions_data):
            # Extract data
            concept_label = row['label']
            definition_id = row['definition_id']
            alt_labels = [a.strip() for a in row['alt_labels'].split(',') if a.strip()]
            def_type = row['definition_type']
            text = row['texte']
            organization = row.get('organisation', 'Unknown')
            country = row.get('country', 'Unknown')
            year = row['year'] if row['year'] else None
            geographic_scope = row.get('geographic_scope', 'National')

            organization = organization.strip() if organization else 'Unknown'
            country = country.strip() if country else 'Unknown'
            geographic_scope = geographic_scope.strip() if geographic_scope else 'National'

            # Source identity is organization only (country is modeled separately)
            source_name = organization if organization != 'Unknown' else 'Unknown'
            
            # Create or get concept
            if concept_label not in concepts:
                concept_uri = self.create_concept(concept_label, alt_labels)
                concepts[concept_label] = concept_uri
            else:
                concept_uri = concepts[concept_label]
            
            # Create or get source (keyed by organization only)
            source_key = source_name
            if source_key not in sources:
                source_uri = self.create_source(
                    source_name,
                    year,
                    organization=organization if organization != 'Unknown' else None,
                    country=None,
                    geographic_scope=geographic_scope
                )
                sources[source_key] = source_uri
            else:
                source_uri = sources[source_key]

            # Create or get country node
            country_uri = None
            if country != 'Unknown':
                if country not in countries:
                    countries[country] = self.create_country(country)
                country_uri = countries[country]
            
            # Create definition
            def_uri = self.create_definition(definition_id, text, def_type, source_uri, geographic_scope, 
                                            country if country != 'Unknown' else None,
                                            country_uri)
            
            # Link concept to definition
            self.graph.add((concept_uri, SKOS.definition, def_uri))
            
            # Add technical criteria
            if definition_id in criteria_by_def:
                self.add_criteria_to_definition(def_uri, criteria_by_def[definition_id])
            
            if (idx + 1) % 10 == 0:
                print(f"   Processed {idx + 1} definitions...")
        
        # Add concept semantic relations after all concepts are known
        relation_links = self.add_concept_relations(concepts)
        print(f"   Concepts: {len(concepts)}")
        print(f"   Sources: {len(sources)}")
        print(f"   Countries: {len(countries)}")
        print(f"   Concept relation links: {relation_links}")
        print(f"   Total triples: {len(self.graph)}")
    
    def save_to_file(self, output_path):
        """
        Save RDF graph to Turtle file.
        
        Args:
            output_path: Path to output .ttl file
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        print(f"\n[*] Saving to {output_path}...")
        
        # Serialize to Turtle format
        self.graph.serialize(destination=str(output_file), format='turtle')
        
        print(f"[OK] Saved RDF to {output_path}")
        print(f"   File size: {output_file.stat().st_size / 1024:.2f} KB")


def main():
    """Main execution function."""
    
    # Configuration
    CRITERIA_CSV = "csv/criteria.csv"
    DEFINITION_CSV = "csv/definition.csv"
    OUTPUT_TTL = "data/forest_definitions.ttl"
    
    print("=" * 60)
    print("CSV to RDF Converter")
    print("=" * 60)
    
    # Check if input files exist
    if not Path(CRITERIA_CSV).exists():
        print(f"[ERROR] Error: {CRITERIA_CSV} not found")
        print("Please run extract_definitions.py first to generate CSV files")
        return
    
    if not Path(DEFINITION_CSV).exists():
        print(f"[ERROR] Error: {DEFINITION_CSV} not found")
        print("Please run extract_definitions.py first to generate CSV files")
        return
    
    # Initialize converter
    converter = CSVToRDFConverter()
    
    # Load CSV data
    converter.load_csv_data(CRITERIA_CSV, DEFINITION_CSV)
    
    # Convert to RDF
    converter.convert()
    
    # Save to file
    converter.save_to_file(OUTPUT_TTL)
    
    print("\n Conversion complete!")
    print(f"\nNext steps:")
    print(f"  1. Review the generated RDF file: {OUTPUT_TTL}")
    print(f"  2. Visualize with Protégé or similar tools")
    print(f"  3. Import to Neo4j using rdf_to_neo4j.py")


if __name__ == "__main__":
    main()
