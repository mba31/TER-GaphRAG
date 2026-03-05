#!/usr/bin/env python3
"""
Alternative Extraction: LLM-based
=================================
Uses an LLM to extract structured fields from each definition row.

Input:  1_sample_data.csv
Output: extracted_definitions_llm.csv

Providers:
  - ollama (default): local model via http://localhost:11434
  - openai: API key from OPENAI_API_KEY env var
"""

import argparse
import csv
import json
import os
from pathlib import Path
from typing import Dict, Optional


def clean_text(text: str) -> str:
    return " ".join(text.split())


def extract_json_block(text: str) -> Optional[Dict]:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:].strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                return None
        return None


def call_ollama(model: str, prompt: str) -> str:
    import requests

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.0},
        },
        timeout=120,
    )
    response.raise_for_status()
    data = response.json()
    return data.get("response", "")


def call_openai(model: str, prompt: str) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model=model,
        temperature=0,
        messages=[
            {"role": "system", "content": "You extract structured fields and return strict JSON only."},
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content or ""


def build_prompt(row: Dict[str, str]) -> str:
    return (
        "Extract forest definition fields as strict JSON with keys: "
        "country, year, concept, definition, confidence (0-1).\n\n"
        f"SOURCE: {row['source']}\n"
        f"YEAR_FIELD: {row['year']}\n"
        f"COUNTRY_FIELD: {row['country']}\n"
        f"DEFINITION_TEXT: {row['definition_text']}\n\n"
        "Rules:\n"
        "- Keep concept as 'forest'.\n"
        "- year must be a 4-digit string when possible, else 'unknown'.\n"
        "- definition should be cleaned and concise.\n"
        "- Return JSON only, no markdown."
    )


def parse_llm_result(row: Dict[str, str], payload: Dict) -> Dict[str, str]:
    year = str(payload.get("year") or row.get("year") or "unknown")
    country = str(payload.get("country") or row.get("country") or "unknown")
    concept = str(payload.get("concept") or "forest")
    definition = clean_text(str(payload.get("definition") or row.get("definition_text") or ""))
    confidence = str(payload.get("confidence") or 0.0)

    return {
        "id": f"def_{country.lower()}_{year}_001",
        "concept": concept,
        "source": row.get("source", ""),
        "year": year,
        "country": country,
        "definition": definition,
        "extraction_method": "LLM",
        "confidence": confidence,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="LLM-based extraction for mini pipeline")
    parser.add_argument("--provider", choices=["ollama", "openai"], default="ollama")
    parser.add_argument("--model", default="llama3.1:8b", help="Ollama or OpenAI model name")
    parser.add_argument("--limit", type=int, default=0, help="Process only first N rows (0 = all)")
    args = parser.parse_args()

    input_file = Path("1_sample_data.csv")
    output_file = Path("extracted_definitions_llm.csv")

    if not input_file.exists():
        print(f"❌ Missing {input_file}")
        return

    print(f"📖 Reading {input_file} (LLM Mode: {args.provider}/{args.model})...\n")

    rows = []
    with open(input_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    if args.limit > 0:
        rows = rows[: args.limit]

    outputs = []

    for index, row in enumerate(rows, start=1):
        prompt = build_prompt(row)

        try:
            if args.provider == "ollama":
                raw = call_ollama(args.model, prompt)
            else:
                if not os.getenv("OPENAI_API_KEY"):
                    raise RuntimeError("OPENAI_API_KEY is not set")
                raw = call_openai(args.model, prompt)

            payload = extract_json_block(raw)
            if not payload:
                raise RuntimeError("Model response is not valid JSON")

            parsed = parse_llm_result(row, payload)
            outputs.append(parsed)
            print(f"  ✓ [{index}] {parsed['country']} ({parsed['year']}) - confidence={parsed['confidence']}")
        except Exception as exc:
            fallback = {
                "id": f"def_{row['country'].lower()}_{row['year']}_001",
                "concept": "forest",
                "source": row["source"],
                "year": row["year"],
                "country": row["country"],
                "definition": clean_text(row["definition_text"]),
                "extraction_method": "LLM_FAILED_FALLBACK",
                "confidence": "0.0",
            }
            outputs.append(fallback)
            print(f"  ⚠ [{index}] Fallback used for {row['country']}: {exc}")

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
                "confidence",
            ],
        )
        writer.writeheader()
        writer.writerows(outputs)

    print(f"\n✅ Done! Check {output_file}")


if __name__ == "__main__":
    main()
