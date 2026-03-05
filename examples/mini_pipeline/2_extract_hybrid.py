#!/usr/bin/env python3
"""
Alternative Extraction: Hybrid (Regex -> NLP -> LLM fallback)
===============================================================
Demonstrates a tiered extraction strategy used in production systems.

Input:  1_sample_data.csv
Output: extracted_definitions_hybrid.csv
"""

import argparse
import csv
import json
import re
from pathlib import Path

from dateutil import parser as date_parser


def clean_text(text: str) -> str:
    return " ".join(text.split())


def extract_year_regex(text: str) -> str:
    match = re.search(r"\b(19|20)\d{2}\b", text)
    return match.group(0) if match else "unknown"


def extract_year_nlp(text: str) -> str:
    try:
        return str(date_parser.parse(text, fuzzy=True).year)
    except Exception:
        return "unknown"


def call_ollama_year(model: str, text: str) -> str:
    import requests

    prompt = (
        "Extract only a 4-digit year from this text. "
        "If no year is present, return 'unknown'.\n\n"
        f"Text: {text}"
    )

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": model, "prompt": prompt, "stream": False, "options": {"temperature": 0}},
        timeout=90,
    )
    response.raise_for_status()
    content = response.json().get("response", "").strip()

    if re.fullmatch(r"\d{4}", content):
        return content

    data = None
    try:
        data = json.loads(content)
    except Exception:
        pass

    if isinstance(data, dict):
        candidate = str(data.get("year", "")).strip()
        if re.fullmatch(r"\d{4}", candidate):
            return candidate

    fallback = re.search(r"\b(19|20)\d{2}\b", content)
    return fallback.group(0) if fallback else "unknown"


def main() -> None:
    parser = argparse.ArgumentParser(description="Hybrid extraction for mini pipeline")
    parser.add_argument("--model", default="llama3.1:8b", help="Ollama model for fallback")
    args = parser.parse_args()

    input_file = Path("1_sample_data.csv")
    output_file = Path("extracted_definitions_hybrid.csv")

    if not input_file.exists():
        print(f"❌ Missing {input_file}")
        return

    rows = []
    with open(input_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows.extend(reader)

    outputs = []

    print("📖 Running hybrid extraction...\n")
    print("Order: Regex -> NLP -> LLM fallback\n")

    for row in rows:
        raw_year = row.get("year", "")

        year = extract_year_regex(raw_year)
        method = "REGEX"

        if year == "unknown":
            year = extract_year_nlp(raw_year)
            method = "NLP"

        if year == "unknown":
            try:
                year = call_ollama_year(args.model, raw_year)
                method = "LLM"
            except Exception:
                method = "LLM_FAILED"

        outputs.append(
            {
                "id": f"def_{row['country'].lower()}_{year}_001",
                "concept": "forest",
                "source": row["source"],
                "year": year,
                "country": row["country"],
                "definition": clean_text(row["definition_text"]),
                "extraction_method": f"HYBRID_{method}",
            }
        )

        print(f"  ✓ {row['country']} ({year}) - via {method}")

    with open(output_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "id",
                "concept",
                "source",
                "year",
                "country",
                "definition",
                "extraction_method",
            ],
        )
        writer.writeheader()
        writer.writerows(outputs)

    print(f"\n✅ Done! Check {output_file}")


if __name__ == "__main__":
    main()
