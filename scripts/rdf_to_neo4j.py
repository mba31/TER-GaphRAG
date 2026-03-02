"""
RDF to Neo4j Importer
=====================
Imports forest definitions from RDF/Turtle format into Neo4j graph database.

Features:
- Parses RDF triples and converts to Neo4j nodes and relationships
- Creates indexed nodes for Concepts, Definitions, Sources, and Criteria
- Supports SKOS vocabulary relationships
- Handles technical criteria as properties

Requirements:
- Neo4j database running (default: localhost:7687)
- neo4j-driver Python package

Author: TER2026 Project
Date: March 2026
"""

from pathlib import Path
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, SKOS, XSD
from neo4j import GraphDatabase
import sys

# Import config
sys.path.insert(0, str(Path(__file__).parent.parent))
import config


class RDFToNeo4jImporter:
    """Imports RDF data into Neo4j graph database."""
    
    def __init__(self, neo4j_uri, neo4j_user, neo4j_password):
        """
        Initialize importer with Neo4j connection.
        
        Args:
            neo4j_uri: Neo4j database URI (e.g., bolt://localhost:7687)
            neo4j_user: Username for Neo4j
            neo4j_password: Password for Neo4j
        """
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password
        self.driver = None
        
        # Define namespaces
        self.EX = Namespace("http://ter2026-project.org/forest#")
        self.SKOS = SKOS
        self.RDF = RDF
        self.RDFS = RDFS
        
        # Statistics
        self.stats = {
            'concepts': 0,
            'definitions': 0,
            'sources': 0,
            'countries': 0,
            'criteria': 0,
            'relationships': 0
        }
    
    def connect(self):
        """Connect to Neo4j database."""
        print(f"[*] Connecting to Neo4j at {self.neo4j_uri}...")
        try:
            self.driver = GraphDatabase.driver(
                self.neo4j_uri,
                auth=(self.neo4j_user, self.neo4j_password)
            )
            # Test connection
            with self.driver.session() as session:
                result = session.run("RETURN 1")
                result.single()
            print("[OK] Connected to Neo4j successfully")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to connect to Neo4j: {e}")
            print("\nTroubleshooting:")
            print("  1. Ensure Neo4j is running")
            print("  2. Check connection URI (default: bolt://localhost:7687)")
            print("  3. Verify username and password")
            return False
    
    def close(self):
        """Close Neo4j connection."""
        if self.driver:
            self.driver.close()
            print("[*] Disconnected from Neo4j")
    
    def clear_database(self):
        """Clear all nodes and relationships from database."""
        print("\n[*] Clearing existing data...")
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        print("[OK] Database cleared")
    
    def create_indexes(self):
        """Create indexes for faster lookups."""
        print("\n[*] Creating indexes...")
        with self.driver.session() as session:
            indexes = [
                "CREATE INDEX concept_uri IF NOT EXISTS FOR (c:Concept) ON (c.uri)",
                "CREATE INDEX definition_id IF NOT EXISTS FOR (d:Definition) ON (d.id)",
                "CREATE INDEX source_name IF NOT EXISTS FOR (s:Source) ON (s.name)",
                "CREATE INDEX country_name IF NOT EXISTS FOR (c:Country) ON (c.name)",
            ]
            for index in indexes:
                session.run(index)
        print("[OK] Indexes created")

    def create_constraints(self):
        """Create unique constraints to prevent duplicate nodes."""
        print("\n[*] Creating unique constraints...")
        with self.driver.session() as session:
            # First, drop any existing indexes that conflict with constraints
            # Neo4j requires dropping indexes before creating constraints on the same field
            conflicting_indexes = [
                "concept_uri",  # Old index that conflicts with constraint
            ]
            
            for idx_name in conflicting_indexes:
                try:
                    drop_query = f"DROP INDEX IF EXISTS {idx_name}"
                    session.run(drop_query)
                except Exception as e:
                    # Ignore if index doesn't exist
                    pass
            
            # Now create the constraints
            constraints = [
                "CREATE CONSTRAINT concept_uri_unique IF NOT EXISTS FOR (c:Concept) REQUIRE c.uri IS UNIQUE",
                "CREATE CONSTRAINT definition_uri_unique IF NOT EXISTS FOR (d:Definition) REQUIRE d.uri IS UNIQUE",
                "CREATE CONSTRAINT source_uri_unique IF NOT EXISTS FOR (s:Source) REQUIRE s.uri IS UNIQUE",
                "CREATE CONSTRAINT country_uri_unique IF NOT EXISTS FOR (c:Country) REQUIRE c.uri IS UNIQUE",
            ]
            for constraint in constraints:
                try:
                    session.run(constraint)
                except Exception as e:
                    print(f"[WARN] Constraint creation warning: {e}")
        print("[OK] Unique constraints created")

    def import_countries(self, rdf_graph):
        """
        Import Country entities to Neo4j.

        Args:
            rdf_graph: rdflib Graph containing RDF data
        """
        print("\n[*] Importing Countries...")

        with self.driver.session() as session:
            for country_uri in rdf_graph.subjects(RDF.type, self.EX.Country):
                uri_str = str(country_uri)

                labels = list(rdf_graph.objects(country_uri, RDFS.label))
                name = self.get_literal_value(labels[0]) if labels else "Unknown"

                query = """
                CREATE (c:Country {
                    uri: $uri,
                    name: $name
                })
                """
                session.run(query, uri=uri_str, name=name)
                self.stats['countries'] += 1

        print(f"[OK] Imported {self.stats['countries']} Countries")
    
    def load_rdf(self, rdf_file):
        """
        Load RDF file into memory.
        
        Args:
            rdf_file: Path to RDF Turtle file
            
        Returns:
            rdflib.Graph object
        """
        print(f"\n[*] Loading RDF from {rdf_file}...")
        graph = Graph()
        graph.parse(rdf_file, format='turtle')
        print(f"[OK] Loaded {len(graph)} triples")
        return graph
    
    def get_literal_value(self, obj):
        """Extract value from Literal object."""
        if isinstance(obj, Literal):
            return str(obj)
        return str(obj)
    
    def import_concepts(self, rdf_graph):
        """
        Import SKOS Concepts to Neo4j.
        
        Args:
            rdf_graph: rdflib Graph containing RDF data
        """
        print("\n[*] Importing Concepts...")
        
        with self.driver.session() as session:
            # Find all Concepts
            for concept_uri in rdf_graph.subjects(RDF.type, SKOS.Concept):
                uri_str = str(concept_uri)
                
                # Extract labels
                pref_labels = list(rdf_graph.objects(concept_uri, SKOS.prefLabel))
                alt_labels = list(rdf_graph.objects(concept_uri, SKOS.altLabel))
                
                pref_label = self.get_literal_value(pref_labels[0]) if pref_labels else "Unknown"
                alt_label_list = [self.get_literal_value(l) for l in alt_labels]
                
                # Create Concept node
                query = """
                CREATE (c:Concept {
                    uri: $uri,
                    name: $pref_label,
                    prefLabel: $pref_label,
                    altLabels: $alt_labels
                })
                """
                session.run(query, uri=uri_str, pref_label=pref_label, alt_labels=alt_label_list)
                self.stats['concepts'] += 1
        
        print(f"[OK] Imported {self.stats['concepts']} Concepts")
    
    def import_sources(self, rdf_graph):
        """
        Import Source entities to Neo4j.
        
        Args:
            rdf_graph: rdflib Graph containing RDF data
        """
        print("\n[*] Importing Sources...")
        
        with self.driver.session() as session:
            # Find all Sources
            for source_uri in rdf_graph.subjects(RDF.type, self.EX.Source):
                uri_str = str(source_uri)
                
                # Extract properties
                labels = list(rdf_graph.objects(source_uri, RDFS.label))
                org_names = list(rdf_graph.objects(source_uri, self.EX.orgName))
                countries = list(rdf_graph.objects(source_uri, self.EX.country))
                years = list(rdf_graph.objects(source_uri, self.EX.year))
                urls = list(rdf_graph.objects(source_uri, self.EX.url))
                geographic_scopes = list(rdf_graph.objects(source_uri, self.EX.geographicScope))
                
                label = self.get_literal_value(labels[0]) if labels else "Unknown"
                org_name = self.get_literal_value(org_names[0]) if org_names else None
                country = self.get_literal_value(countries[0]) if countries else None
                year = self.get_literal_value(years[0]) if years else None
                url = self.get_literal_value(urls[0]) if urls else None
                geographic_scope = self.get_literal_value(geographic_scopes[0]) if geographic_scopes else None
                
                # Create Source node
                query = """
                CREATE (s:Source {
                    uri: $uri,
                    name: $name,
                    organization: $organization,
                    country: $country,
                    year: $year,
                    url: $url,
                    geographicScope: $geographic_scope
                })
                """
                session.run(
                    query,
                    uri=uri_str,
                    name=label,
                    organization=org_name,
                    country=country,
                    year=year,
                    url=url,
                    geographic_scope=geographic_scope
                )
                self.stats['sources'] += 1
        
        print(f"[OK] Imported {self.stats['sources']} Sources")
    
    def import_definitions(self, rdf_graph):
        """
        Import Definition entities to Neo4j.
        
        Args:
            rdf_graph: rdflib Graph containing RDF data
        """
        print("\n[*] Importing Definitions...")
        
        with self.driver.session() as session:
            # Find all Definitions
            for def_uri in rdf_graph.subjects(RDF.type, self.EX.Definition):
                uri_str = str(def_uri)
                
                # Extract properties
                labels = list(rdf_graph.objects(def_uri, RDFS.label))
                types = list(rdf_graph.objects(def_uri, self.EX.definitionType))
                notes = list(rdf_graph.objects(def_uri, SKOS.note))
                sources = list(rdf_graph.objects(def_uri, self.EX.hasSource))
                geographic_scopes = list(rdf_graph.objects(def_uri, self.EX.geographicScope))
                countries = list(rdf_graph.objects(def_uri, self.EX.country))
                
                label = self.get_literal_value(labels[0]) if labels else "Unknown"
                def_type = self.get_literal_value(types[0]) if types else "Unknown"
                note = self.get_literal_value(notes[0]) if notes else ""
                geographic_scope = self.get_literal_value(geographic_scopes[0]) if geographic_scopes else None
                country = self.get_literal_value(countries[0]) if countries else None
                
                # Create Definition node
                query = """
                CREATE (d:Definition {
                    uri: $uri,
                    id: $id,
                    name: $label,
                    label: $label,
                    type: $type,
                    text: $text,
                    geographicScope: $geographic_scope,
                    country: $country
                })
                """
                def_id = uri_str.split('_')[-1] if '_' in uri_str else uri_str
                session.run(query, uri=uri_str, id=def_id, label=label, type=def_type, text=note, 
                          geographic_scope=geographic_scope, country=country)
                self.stats['definitions'] += 1
                
                # Create relationship to Source
                if sources:
                    source_uri_str = str(sources[0])
                    query = """
                    MATCH (d:Definition {uri: $def_uri})
                    MATCH (s:Source {uri: $source_uri})
                    CREATE (d)-[:PROVIDED_BY]->(s)
                    """
                    session.run(query, def_uri=uri_str, source_uri=source_uri_str)
                    self.stats['relationships'] += 1
        
        print(f"[OK] Imported {self.stats['definitions']} Definitions")
    
    def import_criteria(self, rdf_graph):
        """
        Import Technical Criteria to Neo4j.
        
        Args:
            rdf_graph: rdflib Graph containing RDF data
        """
        print("\n[*] Importing Technical Criteria...")
        
        with self.driver.session() as session:
            # Find all definitions with criteria
            for def_uri in rdf_graph.subjects(self.EX.hasCriteria, None):
                def_uri_str = str(def_uri)
                
                # Get criteria node
                criteria_nodes = list(rdf_graph.objects(def_uri, self.EX.hasCriteria))
                if not criteria_nodes:
                    continue
                
                criteria_node = criteria_nodes[0]
                
                # Extract all criteria properties
                criteria_props = {}
                for pred, obj in rdf_graph.predicate_objects(criteria_node):
                    prop_name = str(pred).split('#')[-1]
                    if prop_name not in ['hasCriteria']:
                        try:
                            criteria_props[prop_name] = float(self.get_literal_value(obj))
                        except ValueError:
                            criteria_props[prop_name] = self.get_literal_value(obj)
                
                if criteria_props:
                    # Create Criteria node with SI-normalized values
                    query = """
                    CREATE (c:TechnicalCriteria {
                        uri: $uri,
                        minArea: $min_area,
                        minCanopyCover: $min_canopy,
                        minHeight: $min_height,
                        minWidth: $min_width,
                        minAreaSI: $min_area_si,
                        minCanopyCoverSI: $min_canopy_si,
                        minHeightSI: $min_height_si,
                        minWidthSI: $min_width_si
                    })
                    """
                    session.run(
                        query,
                        uri=str(criteria_node),
                        min_area=criteria_props.get('minArea'),
                        min_canopy=criteria_props.get('minCanopyCover'),
                        min_height=criteria_props.get('minHeight'),
                        min_width=criteria_props.get('minWidth'),
                        min_area_si=criteria_props.get('minAreaSI'),
                        min_canopy_si=criteria_props.get('minCanopyCoverSI'),
                        min_height_si=criteria_props.get('minHeightSI'),
                        min_width_si=criteria_props.get('minWidthSI')
                    )
                    self.stats['criteria'] += 1
                    
                    # Link to Definition
                    query = """
                    MATCH (d:Definition {uri: $def_uri})
                    MATCH (c:TechnicalCriteria {uri: $criteria_uri})
                    CREATE (d)-[:QUANTIFIED_BY]->(c)
                    """
                    session.run(query, def_uri=def_uri_str, criteria_uri=str(criteria_node))
                    self.stats['relationships'] += 1
        
        print(f"[OK] Imported {self.stats['criteria']} Technical Criteria")
    
    def import_relationships(self, rdf_graph):
        """
        Import Concept-Definition relationships.
        
        Args:
            rdf_graph: rdflib Graph containing RDF data
        """
        print("\n[*] Importing Relationships...")
        
        with self.driver.session() as session:
            # Link Concepts to Definitions
            for concept_uri, def_uri in rdf_graph.subject_objects(SKOS.definition):
                query = """
                MATCH (c:Concept {uri: $concept_uri})
                MATCH (d:Definition {uri: $def_uri})
                CREATE (c)-[:HAS_DEFINITION]->(d)
                """
                session.run(query, concept_uri=str(concept_uri), def_uri=str(def_uri))
                self.stats['relationships'] += 1

            # Link Concepts with AFFECTS relationship
            for source_uri, target_uri in rdf_graph.subject_objects(self.EX.affects):
                query = """
                MATCH (source:Concept {uri: $source_uri})
                MATCH (target:Concept {uri: $target_uri})
                CREATE (source)-[:AFFECTS]->(target)
                """
                session.run(query, source_uri=str(source_uri), target_uri=str(target_uri))
                self.stats['relationships'] += 1

            # Link Concepts with PART_OF relationship
            for source_uri, target_uri in rdf_graph.subject_objects(self.EX.partOf):
                query = """
                MATCH (source:Concept {uri: $source_uri})
                MATCH (target:Concept {uri: $target_uri})
                CREATE (source)-[:PART_OF]->(target)
                """
                session.run(query, source_uri=str(source_uri), target_uri=str(target_uri))
                self.stats['relationships'] += 1
            
            # Link Concepts with RELATED_TO relationship
            for source_uri, target_uri in rdf_graph.subject_objects(self.EX.relatedTo):
                query = """
                MATCH (source:Concept {uri: $source_uri})
                MATCH (target:Concept {uri: $target_uri})
                CREATE (source)-[:RELATED_TO]->(target)
                """
                session.run(query, source_uri=str(source_uri), target_uri=str(target_uri))
                self.stats['relationships'] += 1
            
            # Link Concepts with OPPOSITE_OF relationship
            for source_uri, target_uri in rdf_graph.subject_objects(self.EX.oppositeOf):
                query = """
                MATCH (source:Concept {uri: $source_uri})
                MATCH (target:Concept {uri: $target_uri})
                CREATE (source)-[:OPPOSITE_OF]->(target)
                """
                session.run(query, source_uri=str(source_uri), target_uri=str(target_uri))
                self.stats['relationships'] += 1
            
            # Link Concepts with MANAGES relationship
            for source_uri, target_uri in rdf_graph.subject_objects(self.EX.manages):
                query = """
                MATCH (source:Concept {uri: $source_uri})
                MATCH (target:Concept {uri: $target_uri})
                CREATE (source)-[:MANAGES]->(target)
                """
                session.run(query, source_uri=str(source_uri), target_uri=str(target_uri))
                self.stats['relationships'] += 1
            
            # Link Concepts with MEASURES relationship
            for source_uri, target_uri in rdf_graph.subject_objects(self.EX.measures):
                query = """
                MATCH (source:Concept {uri: $source_uri})
                MATCH (target:Concept {uri: $target_uri})
                CREATE (source)-[:MEASURES]->(target)
                """
                session.run(query, source_uri=str(source_uri), target_uri=str(target_uri))
                self.stats['relationships'] += 1
            
            # Link Concepts with DERIVED_FROM relationship
            for source_uri, target_uri in rdf_graph.subject_objects(self.EX.derivedFrom):
                query = """
                MATCH (source:Concept {uri: $source_uri})
                MATCH (target:Concept {uri: $target_uri})
                CREATE (source)-[:DERIVED_FROM]->(target)
                """
                session.run(query, source_uri=str(source_uri), target_uri=str(target_uri))
                self.stats['relationships'] += 1

            # Link Concepts with SYNONYM_OF relationship
            for source_uri, target_uri in rdf_graph.subject_objects(self.EX.synonymOf):
                query = """
                MATCH (source:Concept {uri: $source_uri})
                MATCH (target:Concept {uri: $target_uri})
                CREATE (source)-[:SYNONYM_OF]->(target)
                """
                session.run(query, source_uri=str(source_uri), target_uri=str(target_uri))
                self.stats['relationships'] += 1

            # Link Definitions to Countries
            for def_uri, country_uri in rdf_graph.subject_objects(self.EX.appliesTo):
                query = """
                MATCH (d:Definition {uri: $def_uri})
                MATCH (c:Country {uri: $country_uri})
                CREATE (d)-[:APPLIES_TO]->(c)
                """
                session.run(query, def_uri=str(def_uri), country_uri=str(country_uri))
                self.stats['relationships'] += 1
        
        print(f"[OK] Created {self.stats['relationships']} total relationships")
    
    def print_statistics(self):
        """Print import statistics."""
        print("\n" + "=" * 60)
        print("Import Statistics")
        print("=" * 60)
        print(f"Concepts:            {self.stats['concepts']}")
        print(f"Definitions:         {self.stats['definitions']}")
        print(f"Sources:             {self.stats['sources']}")
        print(f"Countries:           {self.stats['countries']}")
        print(f"Technical Criteria:  {self.stats['criteria']}")
        print(f"Relationships:       {self.stats['relationships']}")
        print("=" * 60)


def main():
    """Main execution function."""
    import sys
    
    # Configuration
    RDF_FILE = "data/forest_definitions.ttl"
    NEO4J_URI = "bolt://localhost:7687"
    NEO4J_USER = "neo4j"
    NEO4J_PASSWORD = "umontpellier"
    
    # Check for --clear-db flag
    clear_db = '--clear-db' in sys.argv
    
    print("=" * 60)
    print("RDF to Neo4j Importer")
    print("=" * 60)
    
    # Check if RDF file exists
    if not Path(RDF_FILE).exists():
        print(f"[ERROR] Error: {RDF_FILE} not found")
        print("Please run csv_to_rdf.py first to generate RDF file")
        return
    
    # Initialize importer
    importer = RDFToNeo4jImporter(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    
    # Connect to Neo4j
    if not importer.connect():
        return
    
    try:
        # Clear existing data (optional - comment out to preserve data)
        if clear_db:
            importer.clear_database()
        else:
            response = input("\n[?] Clear existing database? (yes/no): ").lower()
            if response == 'yes':
                importer.clear_database()
        
        # Create indexes
        importer.create_indexes()
        
        # Create constraints (prevent duplicates)
        if hasattr(importer, 'create_constraints'):
            importer.create_constraints()
        
        # Load RDF
        rdf_graph = importer.load_rdf(RDF_FILE)
        
        # Import data
        importer.import_concepts(rdf_graph)
        importer.import_sources(rdf_graph)
        importer.import_countries(rdf_graph)
        importer.import_definitions(rdf_graph)
        importer.import_criteria(rdf_graph)
        importer.import_relationships(rdf_graph)
        
        # Print statistics
        importer.print_statistics()
        
        print("\n Import complete!")
        print(f"\nNext steps:")
        print(f"  1. Open Neo4j Browser: http://localhost:7474")
        print(f"  2. Query your graph: MATCH (c:Concept)-[:HAS_DEFINITION]->(d:Definition) RETURN c, d LIMIT 25")
        print(f"  3. Explore relationships and criteria")
        
    finally:
        importer.close()


if __name__ == "__main__":
    main()
