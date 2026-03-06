"""
Configuration file for TER2026 Forest Definitions Project
==========================================================
Centralized configuration for all scripts.

Edit this file to change paths, database settings, etc.
"""

from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).parent

# ==================
# Data Directories
# ==================

# Source documents
DOCS_DIR = PROJECT_ROOT / "docs" / "sources"
DOCUMENT_PATH = DOCS_DIR / "forest_definitions.docx"

# Output directories
CSV_DIR = PROJECT_ROOT / "csv"
RDF_DIR = PROJECT_ROOT / "data"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"

# Output files
CRITERIA_CSV = CSV_DIR / "criteria.csv"
DEFINITION_CSV = CSV_DIR / "definition.csv"
RDF_OUTPUT = RDF_DIR / "forest_definitions.ttl"

# ==================
# Extraction Settings
# ==================

# Concepts to extract
CONCEPTS_TO_EXTRACT = [
    "forest",
    # Uncomment to extract more concepts:
    # "deforestation",
    # "afforestation",
    # "reforestation",
    # "tree",
    # "woodland"
]

# Countries to detect (can add more)
COUNTRIES = [
    "Brazil", "Canada", "India", "France", "China",
    "USA", "United States", "Australia", "Germany", "Japan",
    "Russia", "Indonesia", "Mexico", "Peru", "Colombia",
    "Argentina", "United Kingdom", "UK", "Italy", "Spain",
    "Poland", "Sweden", "Finland", "Norway", "Denmark",
    # Add more countries as needed
]

# Keywords that indicate official definitions
DEFINITION_KEYWORDS = [
    "means",
    "defined as",
    "refers to",
    "is defined as",
    "definition",
    "is understood as",
    "shall mean",
    "is considered",
    "is interpreted as"
]

# ==================
# RDF/Ontology Settings
# ==================

# Namespace URI
NAMESPACE_URI = "http://ter2026-project.org/forest#"

# Use SKOS vocabulary
USE_SKOS = True

# ==================
# Neo4j Settings
# ==================

# Neo4j connection
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "umontpellier"

# Database options
CLEAR_DATABASE_ON_IMPORT = False  # Set to True to clear existing data
CREATE_INDEXES = True
CREATE_CONSTRAINTS = True  # NEW: Create unique constraints on URIs to prevent duplicates

# ==================
# Logging Settings
# ==================

# Verbosity level (0=minimal, 1=normal, 2=verbose)
VERBOSITY = 1

# Log files
LOG_FILE = OUTPUTS_DIR / "extraction.log"
AUDIT_LOG = OUTPUTS_DIR / "extraction_audit.log"  # Tracks all paragraphs processed
ERROR_LOG = OUTPUTS_DIR / "extraction_errors.log"  # Tracks failures and skips
ENABLE_AUDIT_LOG = True  # Enable audit trail for data validation
ENABLE_ERROR_LOG = True  # Enable error tracking

# LLM fallback queue (hybrid extraction mode) - DISABLED to save resources
ENABLE_LLM_FALLBACK_QUEUE = False
# QUEUE_FOR_LLM_CSV = OUTPUTS_DIR / "queue_for_llm.csv"
# LLM_FALLBACK_RESULTS_CSV = OUTPUTS_DIR / "llm_fallback_results.csv"

# ==================
# Advanced Settings
# ==================

# Regular expression settings
REGEX_CASE_SENSITIVE = False

# Minimum confidence threshold for extraction (0-1)
MIN_CONFIDENCE = 0.7

# Maximum definitions per concept (0 = no limit)
MAX_DEFINITIONS_PER_CONCEPT = 0

# Year validation range
MIN_YEAR = 1800
MAX_YEAR = 2100


def validate_config():
    """Validate configuration and create necessary directories."""
    
    # Create directories if they don't exist
    for directory in [CSV_DIR, RDF_DIR, OUTPUTS_DIR, DOCS_DIR]:
        directory.mkdir(parents=True, exist_ok=True)
    
    # Check if document exists
    if not DOCUMENT_PATH.exists():
        print(f"[WARN] Warning: Document not found at {DOCUMENT_PATH}")
        print(f"   Please place your document there before running extraction.")
    
    return True


if __name__ == "__main__":
    print("TER2026 Configuration")
    print("=" * 60)
    print(f"Project Root:     {PROJECT_ROOT}")
    print(f"Document Path:    {DOCUMENT_PATH}")
    print(f"CSV Output:       {CSV_DIR}")
    print(f"RDF Output:       {RDF_DIR}")
    print(f"Neo4j URI:        {NEO4J_URI}")
    print(f"Concepts:         {', '.join(CONCEPTS_TO_EXTRACT)}")
    print(f"Countries:        {len(COUNTRIES)} configured")
    print("=" * 60)
    
    if validate_config():
        print("[OK] Configuration validated")
    else:
        print("[ERROR] Configuration errors found")
