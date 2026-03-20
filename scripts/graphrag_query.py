#!/usr/bin/env python3
"""
Simple GraphRAG query utility for TER2026.

What it does:
1) Retrieves relevant concepts and definitions from Neo4j
2) Expands context with source/country/criteria + ENVO links
3) Builds a ready-to-use grounded prompt for an LLM

Usage:
  python scripts/graphrag_query.py --question "What is afforestation?"
  python scripts/graphrag_query.py --question "forest definition in Brazil" --top-k 8
    python scripts/graphrag_query.py --question "What is woodland?" --envo-hop-depth 2
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from neo4j import GraphDatabase

# Import config
sys.path.insert(0, str(Path(__file__).parent.parent))
import config


STOPWORDS = {
    "what", "is", "are", "the", "a", "an", "of", "for", "in", "on", "to", "and", "or",
    "with", "from", "by", "about", "define", "definition", "definitions", "show", "give", "me",
    "how", "does", "do", "can", "could", "would", "should", "into", "using", "use",
}

# comment
@dataclass
class ContextItem:
    concept: str
    definition_uri: str
    definition_text: str
    source_org: str | None
    source_year: int | None
    country: str | None
    scope: str | None
    criteria: dict[str, Any]
    envo_matches: list[dict[str, str]]
    score: float = 0.0


def extract_terms(question: str) -> list[str]:
    tokens = re.findall(r"[A-Za-z][A-Za-z\-]{2,}", question.lower())
    terms = [t for t in tokens if t not in STOPWORDS]
    # Preserve order, remove duplicates
    seen = set()
    unique = []
    for t in terms:
        if t not in seen:
            seen.add(t)
            unique.append(t)
    return unique


def get_candidate_concepts(session, terms: list[str], explicit_concept: str | None, limit: int = 15) -> list[str]:
    if explicit_concept:
        query = """
        MATCH (c:Concept)
        WHERE toLower(c.name) = toLower($concept)
           OR toLower(c.prefLabel) = toLower($concept)
        RETURN DISTINCT c.name AS name
        LIMIT 1
        """
        recs = session.run(query, concept=explicit_concept).data()
        return [r["name"] for r in recs]

    if not terms:
        query = "MATCH (c:Concept) RETURN c.name AS name ORDER BY c.name LIMIT $limit"
        recs = session.run(query, limit=limit).data()
        return [r["name"] for r in recs]

    query = """
    MATCH (c:Concept)
    WHERE any(term IN $terms WHERE toLower(c.name) CONTAINS term OR toLower(c.prefLabel) CONTAINS term)
    RETURN DISTINCT c.name AS name
    ORDER BY c.name
    LIMIT $limit
    """
    recs = session.run(query, terms=terms, limit=limit).data()
    return [r["name"] for r in recs]


def expand_concepts_via_envo(
        session,
        seed_concepts: list[str],
        hop_depth: int,
        limit: int = 80,
) -> list[str]:
        """Expand concept candidates via ENVO hierarchy neighbors up to `hop_depth` hops."""
        if not seed_concepts or hop_depth <= 0:
                return seed_concepts

        # Neo4j path bounds cannot be parameterized directly in the *min..max pattern.
        max_hops = max(1, int(hop_depth))
        query = f"""
        MATCH (seed:Concept)
        WHERE seed.name IN $seed_concepts
        MATCH (seed)-[m1]->(e1:ENVOTerm)
            WHERE type(m1) ENDS WITH 'MATCH'
        MATCH (e1)-[:IS_A*0..{max_hops}]-(e2:ENVOTerm)
        MATCH (related:Concept)-[m2]->(e2)
            WHERE type(m2) ENDS WITH 'MATCH'
        RETURN DISTINCT related.name AS name
        ORDER BY name
        LIMIT $limit
        """

        recs = session.run(query, seed_concepts=seed_concepts, limit=limit).data()
        expanded = [r["name"] for r in recs if r.get("name")]

        # Preserve seed order first, then append ENVO-expanded concepts.
        ordered = []
        seen = set()
        for name in seed_concepts + expanded:
                if name not in seen:
                        seen.add(name)
                        ordered.append(name)
        return ordered


def fetch_context(session, concept_names: list[str], country_filter: str | None, max_rows: int = 200) -> list[ContextItem]:
    if not concept_names:
        return []

    query = """
    MATCH (c:Concept)-[:HAS_DEFINITION]->(d:Definition)-[:PROVIDED_BY]->(s:Source)
    WHERE c.name IN $concept_names
      AND ($country_filter IS NULL OR toLower(d.country) = toLower($country_filter))
    OPTIONAL MATCH (d)-[:APPLIES_TO]->(co:Country)
    OPTIONAL MATCH (d)-[:QUANTIFIED_BY]->(tc:TechnicalCriteria)
    OPTIONAL MATCH (c)-[m]->(e:ENVOTerm)
      WHERE type(m) ENDS WITH 'MATCH'
    RETURN c.name AS concept,
           d.uri AS d_uri,
           d.text AS d_text,
           s.organization AS s_org,
           s.year AS s_year,
           co.name AS ctry,
           d.country AS d_country,
           d.geographicScope AS scope,
           tc.minArea AS minArea,
           tc.minCanopyCover AS minCanopyCover,
           tc.minHeight AS minHeight,
           tc.minWidth AS minWidth,
           collect(DISTINCT {match_type: type(m), envo_id: e.id, envo_uri: e.uri}) AS envo
    LIMIT $max_rows
    """

    rows = session.run(
        query,
        concept_names=concept_names,
        country_filter=country_filter,
        max_rows=max_rows,
    ).data()

    items: list[ContextItem] = []
    for r in rows:
        text = (r.get("d_text") or "").strip()
        criteria = {
            "minArea": r.get("minArea"),
            "minCanopyCover": r.get("minCanopyCover"),
            "minHeight": r.get("minHeight"),
            "minWidth": r.get("minWidth"),
        }
        criteria = {k: v for k, v in criteria.items() if v is not None}

        envo = [e for e in (r.get("envo") or []) if e.get("envo_uri")]

        items.append(
            ContextItem(
                concept=r.get("concept") or "Unknown",
                definition_uri=r.get("d_uri") or "",
                definition_text=text,
                source_org=r.get("s_org"),
                source_year=r.get("s_year"),
                country=r.get("ctry") or r.get("d_country"),
                scope=r.get("scope"),
                criteria=criteria,
                envo_matches=envo,
            )
        )

    return items


def rank_items(items: list[ContextItem], terms: list[str], question: str) -> list[ContextItem]:
    q_lower = question.lower()
    for item in items:
        text = item.definition_text.lower()
        concept = item.concept.lower()

        term_hits = sum(1 for t in terms if t in text or t in concept)
        concept_boost = 1.0 if concept in q_lower else 0.0
        year_boost = 0.0
        if isinstance(item.source_year, int):
            year_boost = min(1.0, max(0.0, (item.source_year - 1950) / 100.0))
        envo_boost = 0.3 if item.envo_matches else 0.0

        item.score = term_hits + concept_boost + year_boost + envo_boost

    return sorted(items, key=lambda x: x.score, reverse=True)


def build_prompt_pack(question: str, top_items: list[ContextItem]) -> str:
    lines = []
    lines.append("You are a forestry domain assistant.")
    lines.append("Answer ONLY using the grounded context below.")
    lines.append("If evidence is insufficient, say so clearly.")
    lines.append("")
    lines.append(f"User question: {question}")
    lines.append("")
    lines.append("Grounded context:")

    for idx, item in enumerate(top_items, start=1):
        lines.append(f"[{idx}] Concept: {item.concept}")
        if item.source_org or item.source_year:
            lines.append(f"    Source: {item.source_org or 'Unknown'} ({item.source_year or 'Unknown'})")
        if item.country or item.scope:
            lines.append(f"    Geography: {item.country or 'Unknown'} | Scope: {item.scope or 'Unknown'}")
        if item.criteria:
            lines.append(f"    Criteria: {json.dumps(item.criteria, ensure_ascii=False)}")
        if item.envo_matches:
            lines.append(
                "    ENVO: " + ", ".join(
                    f"{m.get('match_type')}:{m.get('envo_id')}" for m in item.envo_matches if m.get("envo_id")
                )
            )
        snippet = (item.definition_text or "")
        if len(snippet) > 700:
            snippet = snippet[:700] + "..."
        lines.append(f"    Definition: {snippet}")
        lines.append(f"    Citation URI: {item.definition_uri}")
        lines.append("")

    lines.append("Output requirements:")
    lines.append("- concise answer")
    lines.append("- include 2-5 citation URIs")
    lines.append("- explicitly mention uncertainty if sources conflict")
    return "\n".join(lines)


def print_results(question: str, ranked: list[ContextItem], top_k: int, terms: list[str]) -> None:
    top_items = ranked[:top_k]

    print("=" * 60)
    print("GraphRAG Query Result")
    print("=" * 60)
    print(f"Question: {question}")
    print(f"Terms: {', '.join(terms) if terms else '(none)'}")
    print(f"Retrieved: {len(ranked)} candidate contexts")
    print(f"Top-K used: {len(top_items)}")
    print("=" * 60)

    if not top_items:
        print("[WARN] No context found.")
        return

    print("\nTop contexts:")
    for i, item in enumerate(top_items, start=1):
        print(f"\n[{i}] {item.concept} | score={item.score:.2f}")
        print(f"    URI: {item.definition_uri}")
        print(f"    Source: {item.source_org or 'Unknown'} ({item.source_year or 'Unknown'})")
        print(f"    Geo: {item.country or 'Unknown'} | Scope: {item.scope or 'Unknown'}")
        if item.envo_matches:
            matches = ", ".join(
                f"{m.get('match_type')}:{m.get('envo_id') or m.get('envo_uri')}" for m in item.envo_matches
            )
            print(f"    ENVO: {matches}")
        snippet = (item.definition_text or "")
        if len(snippet) > 220:
            snippet = snippet[:220] + "..."
        print(f"    Text: {snippet}")

    print("\n" + "=" * 60)
    print("Prompt pack for LLM")
    print("=" * 60)
    print(build_prompt_pack(question, top_items))


def main() -> None:
    parser = argparse.ArgumentParser(description="GraphRAG query helper for TER2026")
    parser.add_argument("--question", required=True, help="User question")
    parser.add_argument("--top-k", type=int, default=5, help="Top contexts to keep")
    parser.add_argument("--concept", default=None, help="Optional explicit concept name")
    parser.add_argument("--country", default=None, help="Optional country filter")
    parser.add_argument(
        "--envo-hop-depth",
        type=int,
        default=2,
        help="Expand concept retrieval through ENVO :IS_A graph up to N hops (0 disables)",
    )
    parser.add_argument("--json", action="store_true", help="Output compact JSON instead of text")

    args = parser.parse_args()

    terms = extract_terms(args.question)

    driver = GraphDatabase.driver(
        config.NEO4J_URI,
        auth=(config.NEO4J_USER, config.NEO4J_PASSWORD),
    )

    try:
        with driver.session() as session:
            seed_concepts = get_candidate_concepts(session, terms, args.concept)
            concepts = expand_concepts_via_envo(
                session,
                seed_concepts=seed_concepts,
                hop_depth=args.envo_hop_depth,
            )
            contexts = fetch_context(session, concepts, args.country)

        ranked = rank_items(contexts, terms, args.question)

        if args.json:
            payload = [
                {
                    "concept": i.concept,
                    "definition_uri": i.definition_uri,
                    "source_org": i.source_org,
                    "source_year": i.source_year,
                    "country": i.country,
                    "scope": i.scope,
                    "score": i.score,
                    "envo_matches": i.envo_matches,
                }
                for i in ranked[: args.top_k]
            ]
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return

        print_results(args.question, ranked, args.top_k, terms)

    finally:
        driver.close()


if __name__ == "__main__":
    main()
