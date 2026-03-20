#!/usr/bin/env python3
"""
Automatically generate ENVO mappings for all extracted concepts.

Input:
- csv/criteria.csv (concept labels)
- csv/envo_mappings.csv (existing curated mappings, optional)

Output:
- csv/envo_mappings.csv (updated with auto-generated entries)
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

# Import config
sys.path.insert(0, str(Path(__file__).parent.parent))
import config


def read_concepts(criteria_csv: Path) -> list[str]:
    concepts = set()
    with open(criteria_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            label = (row.get("label") or "").strip()
            if label:
                concepts.add(label)
    return sorted(concepts)


def read_existing_mappings(mappings_csv: Path) -> dict[str, dict[str, str]]:
    existing: dict[str, dict[str, str]] = {}
    if not mappings_csv.exists():
        return existing

    with open(mappings_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            local_concept = (row.get("local_concept") or "").strip()
            envo_id = (row.get("envo_id") or "").strip()
            if local_concept and envo_id:
                existing[local_concept] = {
                    "local_concept": local_concept,
                    "envo_id": envo_id,
                    "match_type": (row.get("match_type") or "exactMatch").strip() or "exactMatch",
                    "confidence": (row.get("confidence") or "high").strip() or "high",
                    "source": (row.get("source") or "manual-curation").strip() or "manual-curation",
                }
    return existing


def normalize_envo_id(iri: str | None, obo_id: str | None) -> str:
    if obo_id and obo_id.startswith("ENVO:"):
        return obo_id.replace(":", "_")
    if iri and "ENVO_" in iri:
        return "ENVO_" + iri.rsplit("ENVO_", 1)[-1]
    return ""


def query_ols4(term: str, exact: bool) -> dict | None:
    params = {
        "q": term,
        "ontology": "envo",
        "type": "class",
        "exact": "true" if exact else "false",
        "rows": 5,
    }
    url = f"{config.ENVO_OLS4_SEARCH_URL}?{urlencode(params)}"

    req = Request(url, headers={"Accept": "application/json", "User-Agent": "TER2026-ENVO-AutoMapper/1.0"})
    with urlopen(req, timeout=15) as resp:
        payload = json.loads(resp.read().decode("utf-8"))

    docs = payload.get("response", {}).get("docs", [])
    if not docs:
        return None

    return docs[0]


def find_envo_mapping(term: str) -> dict[str, str] | None:
    # Try exact search first
    for exact in (True, False):
        try:
            doc = query_ols4(term, exact=exact)
        except Exception:
            return None

        if not doc:
            continue

        label = (doc.get("label") or "").strip()
        iri = (doc.get("iri") or "").strip()
        obo_id = (doc.get("obo_id") or "").strip()
        envo_id = normalize_envo_id(iri, obo_id)

        if not envo_id:
            continue

        is_exact = label.lower() == term.lower()
        return {
            "local_concept": term,
            "envo_id": envo_id,
            "match_type": "exactMatch" if is_exact else "closeMatch",
            "confidence": "high" if is_exact else "medium",
            "source": "auto-ols4",
        }

    return None


def write_mappings(mappings_csv: Path, rows: list[dict[str, str]]) -> None:
    mappings_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(mappings_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["local_concept", "envo_id", "match_type", "confidence", "source"],
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    criteria_csv = Path(config.CRITERIA_CSV)
    mappings_csv = Path(config.ENVO_MAPPINGS_CSV)

    if not criteria_csv.exists():
        print(f"[ERROR] Missing input CSV: {criteria_csv}")
        sys.exit(1)

    concepts = read_concepts(criteria_csv)
    existing = read_existing_mappings(mappings_csv)

    print("=" * 60)
    print("ENVO Auto Mapper")
    print("=" * 60)
    print(f"[*] Concepts detected: {len(concepts)}")
    print(f"[*] Existing curated mappings kept: {len(existing)}")

    output_rows: list[dict[str, str]] = []
    auto_added = 0
    unresolved = 0

    for concept in concepts:
        if concept in existing:
            output_rows.append(existing[concept])
            continue

        mapping = find_envo_mapping(concept)
        if mapping:
            output_rows.append(mapping)
            auto_added += 1
            print(f"   [OK] {concept} -> {mapping['envo_id']} ({mapping['match_type']})")
        else:
            unresolved += 1
            print(f"   [WARN] No ENVO match found for: {concept}")

    output_rows.sort(key=lambda r: r["local_concept"].lower())
    write_mappings(mappings_csv, output_rows)

    print("\n" + "=" * 60)
    print(f"[OK] Saved mappings: {mappings_csv}")
    print(f"[OK] Manual kept: {len(existing)}")
    print(f"[OK] Auto-added: {auto_added}")
    print(f"[INFO] Unresolved: {unresolved}")
    print("=" * 60)


if __name__ == "__main__":
    main()
