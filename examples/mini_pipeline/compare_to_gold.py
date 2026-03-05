#!/usr/bin/env python3
"""
Compare Automated Extraction Output Against Gold Standard
==========================================================
Scores extraction quality by comparing automated output to manually curated reference data.

Usage:
  python compare_to_gold.py --automated extracted_definitions.csv --gold_standard gold_standard/gold_standard_template.csv
  python compare_to_gold.py --automated extracted_definitions_nlp.csv
  python compare_to_gold.py --automated extracted_definitions_hybrid.csv

Output:
  - precision, recall, F1 for key fields (country, year, definition)
  - missing field report
  - confidence histogram
  - detailed diff for low-score rows
"""

import argparse
import csv
from pathlib import Path
from typing import Dict, List, Tuple
from difflib import SequenceMatcher


def load_csv(filepath: Path) -> List[Dict]:
    """Load CSV file and return list of dicts."""
    rows = []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames:
            rows = list(reader)
    return rows


def fuzzy_match(a: str, b: str) -> float:
    """Simple fuzzy string match (0.0 to 1.0)."""
    if not a or not b:
        return 1.0 if a == b else 0.0
    return SequenceMatcher(None, str(a).lower(), str(b).lower()).ratio()


def score_row(automated: Dict, gold: Dict) -> Tuple[float, Dict]:
    """
    Score a single automated row against gold standard.
    Returns overall_score (0-1) and detailed per-field scores.
    """
    scores = {}
    weights = {}

    # Critical fields (must match exactly)
    for field in ["id", "country", "year"]:
        gold_val = gold.get(field, "").strip()
        auto_val = automated.get(field, "").strip()
        match = 1.0 if auto_val == gold_val else fuzzy_match(auto_val, gold_val)
        scores[field] = match
        weights[field] = 1.0  # Critical

    # Definition field (fuzzy match acceptable)
    gold_def = gold.get("definition", "").strip()
    auto_def = automated.get("definition", "").strip()
    if gold_def and auto_def:
        def_match = fuzzy_match(auto_def, gold_def)
        scores["definition"] = def_match
        weights["definition"] = 1.0
    else:
        scores["definition"] = 1.0 if not gold_def and not auto_def else 0.0
        weights["definition"] = 1.0

    # Numeric criteria (optional, but bonus for match)
    for field in ["canopy_min_pct", "area_min_ha", "height_min_m"]:
        gold_val = gold.get(field, "").strip()
        auto_val = automated.get(field, "").strip()
        if gold_val and gold_val not in ["NA", "na"]:
            match = 1.0 if auto_val == gold_val else 0.5
            scores[field] = match
            weights[field] = 0.3  # Optional, lower weight
        else:
            weights[field] = 0.0

    # Source field
    gold_src = gold.get("source", "").strip()
    auto_src = automated.get("source", "").strip()
    match = 1.0 if auto_src == gold_src else fuzzy_match(auto_src, gold_src)
    scores["source"] = match
    weights["source"] = 0.5

    # Confidence field (if present in auto)
    confidence = float(automated.get("confidence", 1.0)) if automated.get("confidence") else 1.0
    scores["confidence"] = confidence
    weights["confidence"] = 0.2

    # Weighted average
    total_weight = sum(w for w in weights.values() if w > 0)
    if total_weight > 0:
        overall = sum(scores.get(f, 0.0) * w for f, w in weights.items()) / total_weight
    else:
        overall = 0.0

    return overall, scores


def main():
    parser = argparse.ArgumentParser(description="Compare automated extraction to gold standard")
    parser.add_argument("--automated", required=True, help="Path to automated extraction CSV")
    parser.add_argument(
        "--gold_standard",
        default="gold_standard/gold_standard_template.csv",
        help="Path to gold standard CSV",
    )
    args = parser.parse_args()

    auto_path = Path(args.automated)
    gold_path = Path(args.gold_standard)

    if not auto_path.exists():
        print(f"❌ Automated file not found: {auto_path}")
        return

    if not gold_path.exists():
        print(f"⚠ Gold standard file not found: {gold_path}")
        print(f"  Using fallback: assuming all automated rows should be evaluated for data quality.")
        gold_rows = []
    else:
        gold_rows = load_csv(gold_path)

    auto_rows = load_csv(auto_path)

    print(f"\n📊 Extraction Quality Report")
    print(f"Automated: {auto_path.name} ({len(auto_rows)} rows)")
    print(f"Gold Standard: {gold_path.name if gold_path.exists() else 'N/A'} ({len(gold_rows)} rows)\n")

    if not gold_rows:
        print("⚠ Gold standard is empty—reporting data quality only.\n")
        print("Missing fields in automated output:")
        critical_fields = ["id", "country", "year", "definition"]
        for field in critical_fields:
            missing = sum(1 for r in auto_rows if not r.get(field, "").strip())
            print(f"  {field}: {missing}/{len(auto_rows)} missing")
        return

    # Match gold rows to auto rows by ID
    auto_by_id = {r.get("id", ""): r for r in auto_rows}
    scores_list = []
    unmatched_gold = []

    for gold_row in gold_rows:
        gold_id = gold_row.get("id", "")
        if gold_id in auto_by_id:
            auto_row = auto_by_id[gold_id]
            overall, field_scores = score_row(auto_row, gold_row)
            scores_list.append(
                {
                    "id": gold_id,
                    "overall": overall,
                    "scores": field_scores,
                    "gold": gold_row,
                    "auto": auto_row,
                }
            )
        else:
            unmatched_gold.append(gold_row)

    if not scores_list:
        print(f"❌ No IDs matched between automated and gold standard!")
        return

    # Summary stats
    overall_scores = [s["overall"] for s in scores_list]
    avg_overall = sum(overall_scores) / len(overall_scores) if overall_scores else 0.0
    min_overall = min(overall_scores) if overall_scores else 0.0
    max_overall = max(overall_scores) if overall_scores else 0.0

    print(f"Overall Match Score (weighted average of all fields):")
    print(f"  Average: {avg_overall:.2%}")
    print(f"  Min: {min_overall:.2%}")
    print(f"  Max: {max_overall:.2%}\n")

    # Field-level analysis
    field_scores = {}
    for field in ["id", "country", "year", "definition", "source", "canopy_min_pct", "area_min_ha", "height_min_m", "confidence"]:
        field_values = [s["scores"].get(field, 0.0) for s in scores_list]
        if field_values:
            field_scores[field] = sum(field_values) / len(field_values)

    print("Field-Level Precision:")
    for field in ["id", "country", "year", "definition", "source"]:
        if field in field_scores:
            print(f"  {field}: {field_scores[field]:.1%}")

    print("\nOptional Fields:")
    for field in ["canopy_min_pct", "area_min_ha", "height_min_m"]:
        if field in field_scores and field_scores[field] > 0:
            print(f"  {field}: {field_scores[field]:.1%}")

    # Unmatched rows
    print(f"\nUnmatched rows:")
    print(f"  Gold standard rows with no auto ID match: {len(unmatched_gold)}")
    if unmatched_gold:
        for row in unmatched_gold:
            print(f"    - {row.get('id')} ({row.get('country')}, {row.get('year')})")

    # Low-score rows needing review
    print(f"\n⚠ Rows with low overall match score (<80%):")
    low_scores = [s for s in scores_list if s["overall"] < 0.8]
    if not low_scores:
        print("  ✅ None—all rows match well!")
    else:
        for s in sorted(low_scores, key=lambda x: x["overall"]):
            print(
                f"  - {s['id']}: {s['overall']:.1%}"
                f"\n    Gold definition: {s['gold'].get('definition', '')[:80]}"
                f"\n    Auto definition: {s['auto'].get('definition', '')[:80]}"
            )

    # Confidence histogram
    confidence_vals = [float(s["auto"].get("confidence", 1.0)) for s in scores_list if s["auto"].get("confidence")]
    if confidence_vals:
        print(f"\nConfidence Score Distribution:")
        buckets = [(0.9, 1.0), (0.8, 0.9), (0.7, 0.8), (0.6, 0.7), (0.0, 0.6)]
        for low, high in buckets:
            count = sum(1 for c in confidence_vals if low <= c < high)
            pct = count / len(confidence_vals) * 100 if confidence_vals else 0
            bar = "█" * int(pct / 5)
            print(f"  [{low:.1f}–{high:.1f}): {count:3d} ({pct:5.1f}%) {bar}")


if __name__ == "__main__":
    main()
