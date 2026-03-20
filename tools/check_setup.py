"""
Setup Checker - TER2026 Project
================================
Verifies that all dependencies and configurations are correct.

Run this before starting the extraction pipeline.
"""

import sys
from pathlib import Path

# Import project config
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def project_path(relative_path: str) -> Path:
    """Build absolute path from project root."""
    return PROJECT_ROOT / relative_path


def check_python_version():
    """Check if Python version is adequate."""
    print("[*] Checking Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"   [OK] Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"   [FAIL] Python {version.major}.{version.minor}.{version.micro} (requires 3.8+)")
        return False


def check_dependencies():
    """Check if required Python packages are installed."""
    print("\n[*] Checking dependencies...")
    
    required = {
        'docx': 'python-docx',
        'rdflib': 'rdflib',
        'neo4j': 'neo4j',
        'pandas': 'pandas'
    }
    
    missing = []
    installed = []
    
    for module, package in required.items():
        try:
            __import__(module)
            installed.append(package)
            print(f"   [OK] {package}")
        except ImportError:
            missing.append(package)
            print(f"   [FAIL] {package} (not installed)")
    
    if missing:
        print(f"\n   To install missing packages:")
        print(f"   pip install {' '.join(missing)}")
        return False
    
    return True


def check_file_structure():
    """Check if project directories exist."""
    print("\n[*] Checking file structure...")
    
    required_dirs = [
        'csv',
        'data',
        'docs/sources',
        'diagrams',
        'scripts',
        'outputs'
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        path = project_path(dir_path)
        if path.exists():
            print(f"   [OK] {dir_path}/")
        else:
            print(f"   [FAIL] {dir_path}/ (missing)")
            all_exist = False
    
    return all_exist


def check_source_document():
    """Check if source document exists."""
    print("\n[*] Checking source document...")
    
    doc_rel_path = "docs/sources/forest_definitions.docx"
    doc_path = project_path(doc_rel_path)
    
    if doc_path.exists():
        size_mb = doc_path.stat().st_size / (1024 * 1024)
        print(f"   [OK] Found: {doc_rel_path}")
        print(f"      Size: {size_mb:.2f} MB")
        return True
    else:
        print(f"   [WARN] Not found: {doc_rel_path}")
        print(f"      Place your document there before extraction")
        return False


def check_scripts():
    """Check if all scripts are present."""
    print("\n[*] Checking scripts...")
    
    scripts = [
        'scripts/extract_definitions.py',
        'scripts/csv_to_rdf.py',
        'scripts/rdf_to_neo4j.py'
    ]
    
    all_exist = True
    for script in scripts:
        path = project_path(script)
        if path.exists():
            print(f"   [OK] {script}")
        else:
            print(f"   [FAIL] {script} (missing)")
            all_exist = False
    
    return all_exist


def check_neo4j():
    """Check Neo4j connection (optional)."""
    print("\n[*] Checking Neo4j connection...")
    
    try:
        from neo4j import GraphDatabase
        
        try:
            driver = GraphDatabase.driver(
                "bolt://localhost:7687",
                auth=("neo4j", "umontpellier")
            )
            with driver.session() as session:
                result = session.run("RETURN 1")
                result.single()
            driver.close()
            print("   [OK] Neo4j is running and accessible")
            return True
        except Exception as e:
            print(f"   [WARN] Cannot connect to Neo4j: {e}")
            print("      (Optional - only needed for Step 3)")
            return None
    
    except ImportError:
        print("   [WARN] neo4j package not installed")
        print("      (Optional - install if using Neo4j)")
        return None


def check_existing_outputs():
    """Check if any outputs already exist."""
    print("\n[*] Checking existing outputs...")
    
    outputs = {
        'csv/criteria.csv': 'CSV definitions',
        'csv/definition.csv': 'CSV criteria',
        'data/forest_definitions.ttl': 'RDF graph'
    }
    
    found = []
    for path, description in outputs.items():
        if project_path(path).exists():
            print(f"   [INFO] Found: {description} ({path})")
            found.append(path)
    
    if not found:
        print("   No existing outputs - ready for fresh start")
    else:
        print(f"   [WARN] {len(found)} output(s) exist - will be overwritten")
    
    return True


def check_envo_setup():
    """Check ENVO integration setup (config + mapping file + optional RDF hints)."""
    print("\n[*] Checking ENVO integration...")

    ok = True

    # Config flag
    if getattr(config, "ENABLE_ENVO_MAPPINGS", False):
        print("   [OK] ENABLE_ENVO_MAPPINGS is enabled")
    else:
        print("   [WARN] ENABLE_ENVO_MAPPINGS is disabled")
        ok = False

    # Mapping file presence
    mappings_rel = str(config.ENVO_MAPPINGS_CSV.relative_to(PROJECT_ROOT))
    mappings_path = Path(config.ENVO_MAPPINGS_CSV)
    if mappings_path.exists():
        print(f"   [OK] Found ENVO mappings file: {mappings_rel}")
    else:
        print(f"   [WARN] Missing ENVO mappings file: {mappings_rel}")
        ok = False

    # Optional: quick RDF validation if output exists
    rdf_path = Path(config.RDF_OUTPUT)
    rdf_rel = str(rdf_path.relative_to(PROJECT_ROOT))
    if rdf_path.exists():
        try:
            with open(rdf_path, "r", encoding="utf-8") as f:
                head = "".join([next(f) for _ in range(80)])
            if "@prefix envo:" in head or "ENVO_" in head:
                print(f"   [OK] RDF appears ENVO-aware: {rdf_rel}")
            else:
                print(f"   [INFO] RDF exists but no ENVO prefix detected in header: {rdf_rel}")
        except (OSError, StopIteration):
            print(f"   [INFO] Could not inspect RDF header: {rdf_rel}")
    else:
        print(f"   [INFO] RDF not generated yet: {rdf_rel}")

    return ok


def print_summary(results):
    """Print summary of checks."""
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    all_passed = all(v is True for v in results.values() if v is not None)
    
    if all_passed:
        print("[OK] All checks passed! Ready to start.")
        print("\nNext steps:")
        print("  1. python scripts/extract_definitions.py")
        print("  2. python scripts/csv_to_rdf.py")
        print("  3. python scripts/rdf_to_neo4j.py (optional)")
    else:
        print("[WARN] Some checks failed. Please fix issues above.")
        
        if not results['dependencies']:
            print("\n==> Install dependencies:")
            print("   pip install -r requirements.txt")
        
        if not results['source_document']:
            print("\n==> Add source document:")
            print("   Place your DOCX file in docs/sources/")
    
    print("=" * 60)


def main():
    """Run all checks."""
    print("=" * 60)
    print("TER2026 Setup Checker")
    print("=" * 60)
    print(f"[*] Project root: {PROJECT_ROOT}")
    
    results = {
        'python_version': check_python_version(),
        'dependencies': check_dependencies(),
        'file_structure': check_file_structure(),
        'source_document': check_source_document(),
        'scripts': check_scripts(),
        'neo4j': check_neo4j(),
        'existing_outputs': check_existing_outputs(),
        'envo_setup': check_envo_setup()
    }
    
    print_summary(results)


if __name__ == "__main__":
    main()
