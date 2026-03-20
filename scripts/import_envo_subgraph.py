#!/usr/bin/env python3
"""
Import a scoped ENVO subgraph into Neo4j.

What it does:
1) Builds ENVO seed terms (from mappings CSV, auto-discovery from local concepts, or both)
2) Expands hierarchy via OLS4 parents/children (configurable depth)
3) Upserts ENVOTerm nodes in Neo4j
4) Creates hierarchy edges (:ENVOTerm)-[:IS_A]->(:ENVOTerm)
5) Optionally links local Concept nodes to ENVOTerm nodes using mapping match types
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import deque
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from neo4j import GraphDatabase

# Import config
sys.path.insert(0, str(Path(__file__).parent.parent))
import config


MATCH_TYPE_TO_REL = {
    "exactMatch": "EXACT_MATCH",
    "closeMatch": "CLOSE_MATCH",
    "broadMatch": "BROAD_MATCH",
    "narrowMatch": "NARROW_MATCH",
}


def read_concepts(criteria_csv: Path) -> list[str]:
    """Read distinct concept labels from criteria CSV."""
    concepts = set()
    if not criteria_csv.exists():
        return []

    with open(criteria_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            label = (row.get("label") or "").strip()
            if label:
                concepts.add(label)

    return sorted(concepts)


def normalize_envo_id(raw_id: str) -> str | None:
    """Normalize flexible ENVO identifiers to ENVO_######## format."""
    if not raw_id:
        return None

    token = raw_id.strip()
    if not token:
        return None

    if token.startswith("http://") or token.startswith("https://"):
        if "ENVO_" not in token:
            return None
        return "ENVO_" + token.rsplit("ENVO_", 1)[-1]

    if token.lower().startswith("envo:"):
        token = token.split(":", 1)[1]

    if token.upper().startswith("ENVO_"):
        token = token.split("_", 1)[1]

    digits = "".join(ch for ch in token if ch.isdigit())
    if not digits:
        return None

    return f"ENVO_{digits.zfill(8)}"


def envo_uri_from_id(envo_id: str) -> str:
    return f"{config.ENVO_NAMESPACE_URI}{envo_id.replace('ENVO_', '')}"


def read_seed_mappings(mappings_csv: Path) -> list[dict[str, str]]:
    """Read local concept -> ENVO mappings from CSV."""
    rows: list[dict[str, str]] = []
    if not mappings_csv.exists():
        return rows

    with open(mappings_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            local_concept = (row.get("local_concept") or "").strip()
            raw_envo_id = (row.get("envo_id") or "").strip()
            match_type = (row.get("match_type") or "closeMatch").strip()

            norm_id = normalize_envo_id(raw_envo_id)
            if not local_concept or not norm_id:
                continue

            if match_type not in MATCH_TYPE_TO_REL:
                match_type = "closeMatch"

            rows.append(
                {
                    "local_concept": local_concept,
                    "envo_id": norm_id,
                    "envo_uri": envo_uri_from_id(norm_id),
                    "match_type": match_type,
                }
            )

    return rows


def write_seed_mappings(mappings_csv: Path, mappings: list[dict[str, str]]) -> None:
    """Write mappings in project-compatible schema."""
    mappings_csv.parent.mkdir(parents=True, exist_ok=True)
    rows = sorted(mappings, key=lambda r: r["local_concept"].lower())

    with open(mappings_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["local_concept", "envo_id", "match_type", "confidence", "source"],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "local_concept": row["local_concept"],
                    "envo_id": row["envo_id"],
                    "match_type": row["match_type"],
                    "confidence": "high" if row["match_type"] == "exactMatch" else "medium",
                    "source": row.get("source") or "auto-ols4",
                }
            )


class OLS4Client:
    """Small OLS4 client for ENVO term and hierarchy retrieval."""

    def __init__(self, api_base: str, timeout: int = 20):
        self.api_base = api_base.rstrip("/")
        self.timeout = timeout

    def _request_json(self, url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        if params:
            url = f"{url}?{urlencode(params)}"

        req = Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": "TER2026-ENVO-SubgraphImporter/1.0",
            },
        )
        with urlopen(req, timeout=self.timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))

    @staticmethod
    def _encoded_iri_candidates(iri: str) -> list[str]:
        # OLS endpoints often require double encoding of full IRI in path segments.
        single = quote(iri, safe="")
        double = quote(single, safe="")
        return [double, single]

    def get_term(self, iri: str) -> dict[str, Any] | None:
        for enc in self._encoded_iri_candidates(iri):
            url = f"{self.api_base}/ontologies/envo/terms/{enc}"
            try:
                payload = self._request_json(url)
                if payload:
                    return payload
            except Exception:
                continue
        return None

    def get_related_terms(self, iri: str, relation: str, page_size: int = 500) -> list[dict[str, Any]]:
        """Fetch parent/child terms with pagination."""
        terms: list[dict[str, Any]] = []
        for enc in self._encoded_iri_candidates(iri):
            base_url = f"{self.api_base}/ontologies/envo/terms/{enc}/{relation}"
            try:
                page = 0
                while True:
                    payload = self._request_json(base_url, params={"page": page, "size": page_size})
                    embedded = payload.get("_embedded", {})
                    page_terms = embedded.get("terms", [])
                    terms.extend(page_terms)

                    page_info = payload.get("page", {})
                    total_pages = int(page_info.get("totalPages", 1))
                    if page + 1 >= total_pages:
                        break
                    page += 1
                return terms
            except Exception:
                continue

        return []

    def search_envo(self, term: str, exact: bool, rows: int = 5) -> list[dict[str, Any]]:
        """Search ENVO classes via OLS4 /search endpoint."""
        url = f"{self.api_base}/search"
        payload = self._request_json(
            url,
            params={
                "q": term,
                "ontology": "envo",
                "type": "class",
                "exact": "true" if exact else "false",
                "rows": rows,
            },
        )
        return payload.get("response", {}).get("docs", [])

    def find_best_mapping(self, local_concept: str) -> dict[str, str] | None:
        """Map local concept label to best ENVO term via OLS4 search."""
        for exact in (True, False):
            try:
                docs = self.search_envo(local_concept, exact=exact)
            except Exception:
                return None

            if not docs:
                continue

            for doc in docs:
                iri = (doc.get("iri") or "").strip()
                obo_id = (doc.get("obo_id") or "").strip()
                label = (doc.get("label") or "").strip()

                if not iri:
                    continue

                envo_id = normalize_envo_id(obo_id or iri)
                if not envo_id:
                    continue

                is_exact = label.lower() == local_concept.lower()
                return {
                    "local_concept": local_concept,
                    "envo_id": envo_id,
                    "envo_uri": envo_uri_from_id(envo_id),
                    "match_type": "exactMatch" if is_exact else "closeMatch",
                    "source": "auto-ols4",
                }

        return None


def build_seed_mappings(
    seed_mode: str,
    mappings_csv: Path,
    criteria_csv: Path,
    client: OLS4Client,
    write_back: bool,
) -> tuple[list[dict[str, str]], dict[str, int]]:
    """Build seed mappings using selected strategy."""
    stats = {
        "existing": 0,
        "auto_added": 0,
        "unresolved": 0,
    }

    existing_rows = read_seed_mappings(mappings_csv)
    existing_by_concept = {r["local_concept"]: r for r in existing_rows}
    stats["existing"] = len(existing_rows)

    if seed_mode == "mappings":
        return existing_rows, stats

    concepts = read_concepts(criteria_csv)
    if not concepts:
        # In pure auto mode, no concepts means no seeds.
        if seed_mode == "auto":
            return [], stats
        return existing_rows, stats

    output_by_concept = dict(existing_by_concept) if seed_mode == "hybrid" else {}

    for concept in concepts:
        if concept in output_by_concept:
            continue

        mapping = client.find_best_mapping(concept)
        if mapping:
            output_by_concept[concept] = mapping
            stats["auto_added"] += 1
        else:
            stats["unresolved"] += 1

    mappings = sorted(output_by_concept.values(), key=lambda r: r["local_concept"].lower())

    if write_back and mappings:
        write_seed_mappings(mappings_csv, mappings)

    return mappings, stats


def parse_term(payload: dict[str, Any]) -> dict[str, str] | None:
    iri = (payload.get("iri") or "").strip()
    obo_id = (payload.get("obo_id") or "").strip()

    if not iri:
        return None

    # Keep scope to ENVO terms only.
    if "ENVO_" not in iri and not obo_id.startswith("ENVO:"):
        return None

    envo_id = normalize_envo_id(obo_id or iri)
    if not envo_id:
        return None

    label = (payload.get("label") or "").strip() or envo_id
    description = payload.get("description")
    definition = ""
    if isinstance(description, list) and description:
        definition = str(description[0]).strip()
    elif isinstance(description, str):
        definition = description.strip()

    return {
        "uri": iri,
        "id": envo_id,
        "label": label,
        "definition": definition,
    }


def crawl_envo_subgraph(
    client: OLS4Client,
    seed_uris: list[str],
    parent_depth: int,
    child_depth: int,
) -> tuple[dict[str, dict[str, str]], set[tuple[str, str]]]:
    """
    Crawl ENVO hierarchy around seeds.

    Returns:
    - terms_by_uri: uri -> term metadata
    - is_a_edges: (child_uri, parent_uri)
    """
    terms_by_uri: dict[str, dict[str, str]] = {}
    is_a_edges: set[tuple[str, str]] = set()

    def add_term_from_payload(payload: dict[str, Any]) -> str | None:
        term = parse_term(payload)
        if not term:
            return None
        terms_by_uri[term["uri"]] = term
        return term["uri"]

    # Seed terms first
    for uri in seed_uris:
        payload = client.get_term(uri)
        if payload:
            add_term_from_payload(payload)

    # Parent expansion: child -> parent
    parent_seen_depth: dict[str, int] = {u: 0 for u in terms_by_uri.keys()}
    q_parents: deque[tuple[str, int]] = deque((u, 0) for u in list(terms_by_uri.keys()))

    while q_parents:
        current_uri, depth = q_parents.popleft()
        if depth >= parent_depth:
            continue

        parents = client.get_related_terms(current_uri, "parents")
        for p in parents:
            p_uri = add_term_from_payload(p)
            if not p_uri:
                continue

            is_a_edges.add((current_uri, p_uri))

            next_depth = depth + 1
            prev = parent_seen_depth.get(p_uri)
            if prev is None or next_depth < prev:
                parent_seen_depth[p_uri] = next_depth
                q_parents.append((p_uri, next_depth))

    # Child expansion: child -> parent (invert relation from current parent)
    child_seen_depth: dict[str, int] = {u: 0 for u in terms_by_uri.keys()}
    q_children: deque[tuple[str, int]] = deque((u, 0) for u in list(terms_by_uri.keys()))

    while q_children:
        current_uri, depth = q_children.popleft()
        if depth >= child_depth:
            continue

        children = client.get_related_terms(current_uri, "children")
        for c in children:
            c_uri = add_term_from_payload(c)
            if not c_uri:
                continue

            is_a_edges.add((c_uri, current_uri))

            next_depth = depth + 1
            prev = child_seen_depth.get(c_uri)
            if prev is None or next_depth < prev:
                child_seen_depth[c_uri] = next_depth
                q_children.append((c_uri, next_depth))

    return terms_by_uri, is_a_edges


def import_to_neo4j(
    neo4j_uri: str,
    neo4j_user: str,
    neo4j_password: str,
    terms_by_uri: dict[str, dict[str, str]],
    is_a_edges: set[tuple[str, str]],
    mappings: list[dict[str, str]],
    link_local_concepts: bool,
) -> dict[str, int]:
    stats = {
        "terms_upserted": 0,
        "is_a_links": 0,
        "concept_links": 0,
        "unmatched_concepts": 0,
    }

    driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
    try:
        with driver.session() as session:
            # Safety constraint
            session.run(
                "CREATE CONSTRAINT envo_uri_unique IF NOT EXISTS FOR (e:ENVOTerm) REQUIRE e.uri IS UNIQUE"
            )

            # Upsert terms
            term_query = """
            MERGE (e:ENVOTerm {uri: $uri})
            ON CREATE SET
                e.id = $id,
                e.name = coalesce($label, 'ENVO:' + $id),
                e.label = $label,
                e.definition = $definition,
                e.source = 'ols4-envo-subgraph'
            ON MATCH SET
                e.id = coalesce(e.id, $id),
                e.label = coalesce($label, e.label),
                e.name = coalesce(e.name, $label),
                e.definition = coalesce(e.definition, $definition)
            """
            for term in terms_by_uri.values():
                session.run(
                    term_query,
                    uri=term["uri"],
                    id=term["id"],
                    label=term["label"],
                    definition=term["definition"] or None,
                )
                stats["terms_upserted"] += 1

            # Hierarchy edges
            rel_query = """
            MATCH (child:ENVOTerm {uri: $child_uri})
            MATCH (parent:ENVOTerm {uri: $parent_uri})
            MERGE (child)-[:IS_A]->(parent)
            """
            for child_uri, parent_uri in is_a_edges:
                session.run(rel_query, child_uri=child_uri, parent_uri=parent_uri)
                stats["is_a_links"] += 1

            # Optional relinking from local concepts based on mapping CSV
            if link_local_concepts:
                for row in mappings:
                    rel_type = MATCH_TYPE_TO_REL[row["match_type"]]
                    query = f"""
                    MATCH (c:Concept)
                    WHERE c.name = $concept OR c.prefLabel = $concept
                    MATCH (e:ENVOTerm {{uri: $envo_uri}})
                    MERGE (c)-[:{rel_type}]->(e)
                    RETURN count(c) AS found
                    """
                    result = session.run(
                        query,
                        concept=row["local_concept"],
                        envo_uri=row["envo_uri"],
                    ).single()

                    found = int(result["found"]) if result and "found" in result else 0
                    if found > 0:
                        stats["concept_links"] += 1
                    else:
                        stats["unmatched_concepts"] += 1
    finally:
        driver.close()

    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Import scoped ENVO hierarchy into Neo4j")
    parser.add_argument(
        "--seed-mode",
        choices=["mappings", "auto", "hybrid"],
        default="hybrid",
        help="Seed strategy: mappings CSV only, auto from local concepts only, or hybrid",
    )
    parser.add_argument(
        "--mappings-csv",
        default=str(config.ENVO_MAPPINGS_CSV),
        help="Path to ENVO mappings CSV (seed terms)",
    )
    parser.add_argument(
        "--criteria-csv",
        default=str(getattr(config, "CRITERIA_CSV", Path("csv") / "criteria.csv")),
        help="Path to criteria.csv used for auto seed discovery",
    )
    parser.add_argument(
        "--write-mappings-csv",
        action="store_true",
        help="Persist auto/hybrid discovered seeds back to mappings CSV",
    )
    parser.add_argument(
        "--parent-depth",
        type=int,
        default=getattr(config, "ENVO_SUBGRAPH_PARENT_DEPTH", 2),
        help="How many parent levels to import upward from seeds",
    )
    parser.add_argument(
        "--child-depth",
        type=int,
        default=getattr(config, "ENVO_SUBGRAPH_CHILD_DEPTH", 1),
        help="How many child levels to import downward from seeds",
    )
    parser.add_argument(
        "--neo4j-uri",
        default=getattr(config, "NEO4J_URI", "bolt://localhost:7687"),
        help="Neo4j URI",
    )
    parser.add_argument(
        "--neo4j-user",
        default=getattr(config, "NEO4J_USER", "neo4j"),
        help="Neo4j user",
    )
    parser.add_argument(
        "--neo4j-password",
        default=getattr(config, "NEO4J_PASSWORD", "neo4j"),
        help="Neo4j password",
    )
    parser.add_argument(
        "--ols4-api-base",
        default=getattr(config, "ENVO_OLS4_API_BASE", "https://www.ebi.ac.uk/ols4/api"),
        help="OLS4 API base URL",
    )
    parser.add_argument(
        "--no-link-local-concepts",
        action="store_true",
        help="Do not create local Concept -> ENVOTerm mapping edges",
    )
    args = parser.parse_args()

    mappings_csv = Path(args.mappings_csv)
    criteria_csv = Path(args.criteria_csv)
    client = OLS4Client(args.ols4_api_base)

    mappings, seed_stats = build_seed_mappings(
        seed_mode=args.seed_mode,
        mappings_csv=mappings_csv,
        criteria_csv=criteria_csv,
        client=client,
        write_back=args.write_mappings_csv,
    )

    if not mappings:
        print("[ERROR] No valid ENVO seeds found")
        print(f"        seed-mode: {args.seed_mode}")
        print(f"        mappings-csv: {mappings_csv}")
        print(f"        criteria-csv: {criteria_csv}")
        sys.exit(1)

    seed_uris = sorted({m["envo_uri"] for m in mappings})

    print("=" * 60)
    print("ENVO Subgraph Importer")
    print("=" * 60)
    print(f"[*] Seed mode: {args.seed_mode}")
    print(f"[*] Existing mappings: {seed_stats['existing']}")
    print(f"[*] Auto-added mappings: {seed_stats['auto_added']}")
    print(f"[*] Unresolved concepts: {seed_stats['unresolved']}")
    if args.write_mappings_csv and args.seed_mode in {"auto", "hybrid"}:
        print(f"[*] Mappings written to: {mappings_csv}")
    print(f"[*] Seed mappings: {len(mappings)}")
    print(f"[*] Unique seed ENVO terms: {len(seed_uris)}")
    print(f"[*] Parent depth: {args.parent_depth}")
    print(f"[*] Child depth: {args.child_depth}")

    terms_by_uri, is_a_edges = crawl_envo_subgraph(
        client=client,
        seed_uris=seed_uris,
        parent_depth=max(0, args.parent_depth),
        child_depth=max(0, args.child_depth),
    )

    print(f"[OK] Terms collected: {len(terms_by_uri)}")
    print(f"[OK] IS_A edges collected: {len(is_a_edges)}")

    stats = import_to_neo4j(
        neo4j_uri=args.neo4j_uri,
        neo4j_user=args.neo4j_user,
        neo4j_password=args.neo4j_password,
        terms_by_uri=terms_by_uri,
        is_a_edges=is_a_edges,
        mappings=mappings,
        link_local_concepts=not args.no_link_local_concepts,
    )

    print("\n" + "=" * 60)
    print("Neo4j Import Summary")
    print("=" * 60)
    print(f"[OK] ENVOTerm upserts: {stats['terms_upserted']}")
    print(f"[OK] IS_A links: {stats['is_a_links']}")
    if not args.no_link_local_concepts:
        print(f"[OK] Concept->ENVO links upserted: {stats['concept_links']}")
        if stats["unmatched_concepts"]:
            print(f"[WARN] Unmatched local concepts: {stats['unmatched_concepts']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
