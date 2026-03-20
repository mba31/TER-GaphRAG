#!/usr/bin/env python3
"""
Run full TER2026 pipeline in one command.

Steps:
1) extract_definitions.py
2) envo_auto_map.py (optional/automatic)
3) csv_to_rdf.py
4) rdf_to_neo4j.py (optional)
5) graphrag_query.py (smoke query)
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
TOOLS_DIR = PROJECT_ROOT / "tools"


def run_step(cmd: list[str], title: str) -> None:
    print("\n" + "=" * 60)
    print(f"[*] {title}")
    print("=" * 60)
    print("$ " + " ".join(cmd))

    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
    if result.returncode != 0:
        raise SystemExit(f"\n[ERROR] Step failed: {title} (exit code {result.returncode})")

    print(f"[OK] {title}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run TER2026 pipeline end-to-end")
    parser.add_argument(
        "--skip-neo4j",
        action="store_true",
        help="Skip RDF -> Neo4j import step",
    )
    parser.add_argument(
        "--clear-db",
        action="store_true",
        help="Pass --clear-db to rdf_to_neo4j.py",
    )
    parser.add_argument(
        "--skip-setup-check",
        action="store_true",
        help="Skip tools/check_setup.py before running",
    )
    parser.add_argument(
        "--skip-envo-auto-map",
        action="store_true",
        help="Skip automatic ENVO mapping generation",
    )
    parser.add_argument(
        "--skip-envo-subgraph",
        action="store_true",
        help="Skip ENVO hierarchy subgraph import into Neo4j",
    )
    parser.add_argument(
        "--envo-parent-depth",
        type=int,
        default=2,
        help="Parent depth for ENVO hierarchy import",
    )
    parser.add_argument(
        "--envo-child-depth",
        type=int,
        default=1,
        help="Child depth for ENVO hierarchy import",
    )
    parser.add_argument(
        "--envo-seed-mode",
        choices=["mappings", "auto", "hybrid"],
        default="hybrid",
        help="Seed strategy for ENVO subgraph import",
    )
    parser.add_argument(
        "--envo-write-mappings-csv",
        action="store_true",
        help="Persist auto/hybrid ENVO seeds back to csv/envo_mappings.csv",
    )
    parser.add_argument(
        "--neo4j-browser-url",
        default="http://localhost:7474",
        help="Neo4j Browser URL to display at the end",
    )
    parser.add_argument(
        "--skip-graphrag-query",
        action="store_true",
        help="Skip GraphRAG smoke query step",
    )
    parser.add_argument(
        "--graphrag-question",
        default="What is afforestation?",
        help="Question used for GraphRAG smoke query",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("TER2026 Pipeline Launcher")
    print("=" * 60)
    print(f"[*] Project root: {PROJECT_ROOT}")

    if not args.skip_setup_check:
        run_step(
            [sys.executable, str(TOOLS_DIR / "check_setup.py")],
            "Setup check",
        )

    run_step(
        [sys.executable, str(SCRIPTS_DIR / "extract_definitions.py")],
        "Extract definitions (DOCX -> CSV)",
    )

    if not args.skip_envo_auto_map:
        run_step(
            [sys.executable, str(SCRIPTS_DIR / "envo_auto_map.py")],
            "Auto-generate ENVO mappings",
        )
    else:
        print("\n[INFO] ENVO auto-mapping step skipped (--skip-envo-auto-map)")

    run_step(
        [sys.executable, str(SCRIPTS_DIR / "csv_to_rdf.py")],
        "Convert CSV to RDF (with ENVO mappings)",
    )

    if not args.skip_neo4j:
        neo4j_cmd = [sys.executable, str(SCRIPTS_DIR / "rdf_to_neo4j.py")]
        if args.clear_db:
            neo4j_cmd.append("--clear-db")

        run_step(
            neo4j_cmd,
            "Import RDF into Neo4j",
        )

        if not args.skip_envo_subgraph:
            run_step(
                [
                    sys.executable,
                    str(SCRIPTS_DIR / "import_envo_subgraph.py"),
                    "--seed-mode",
                    args.envo_seed_mode,
                    "--parent-depth",
                    str(args.envo_parent_depth),
                    "--child-depth",
                    str(args.envo_child_depth),
                    *( ["--write-mappings-csv"] if args.envo_write_mappings_csv else [] ),
                ],
                "Import scoped ENVO hierarchy subgraph",
            )
        else:
            print("\n[INFO] ENVO subgraph step skipped (--skip-envo-subgraph)")
    else:
        print("\n[INFO] Neo4j step skipped (--skip-neo4j)")

    if args.skip_graphrag_query:
        print("\n[INFO] GraphRAG query step skipped (--skip-graphrag-query)")
    else:
        run_step(
            [
                sys.executable,
                str(SCRIPTS_DIR / "graphrag_query.py"),
                "--question",
                args.graphrag_question,
            ],
            "Run GraphRAG smoke query",
        )

    print("\n" + "=" * 60)
    print("[OK] Pipeline finished successfully")
    if not args.skip_neo4j:
        print(f"[→] Open graph in Neo4j Browser: {args.neo4j_browser_url}")
        print("[→] Suggested query (overview): MATCH (c:Concept)-[:HAS_DEFINITION]->(d:Definition) RETURN c, d LIMIT 10")
        print("[→] Suggested query (ENVO): MATCH (c:Concept)-[r]->(e:ENVOTerm) WHERE type(r) ENDS WITH 'MATCH' RETURN c.name AS concept, type(r) AS match_type, e.id AS envo_id, e.uri AS envo_uri ORDER BY concept, match_type")
    print(f"[→] GraphRAG question used: {args.graphrag_question}")
    print("=" * 60)


if __name__ == "__main__":
    main()
