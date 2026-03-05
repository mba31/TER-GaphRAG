#!/usr/bin/env python3
"""
Mini Extraction Script
======================
Reads sample CSV, extracts countries and years, outputs cleaned CSV.

Input:  1_sample_data.csv
Output: extracted_definitions.csv
"""

import csv
import re
from pathlib import Path

def extract_number(text, pattern=r'\d{4}'):
    """Extract 4-digit year from text."""
    match = re.search(pattern, text)
    return match.group(0) if match else "unknown"

def clean_text(text):
    """Remove extra whitespace."""
    return " ".join(text.split())

def main():
    input_file = Path("1_sample_data.csv")
    output_file = Path("extracted_definitions.csv")
    
    if not input_file.exists():
        print(f"❌ Missing {input_file}")
        return
    
    print(f"📖 Reading {input_file}...")
    
    definitions = []
    with open(input_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            year = extract_number(row["year"])
            cleaned_text = clean_text(row["definition_text"])
            
            definitions.append({
                "id": f"def_{row['country'].lower()}_{year}_001",
                "concept": "forest",
                "source": row["source"],
                "year": year,
                "country": row["country"],
                "definition": cleaned_text
            })
            print(f"  ✓ {row['country']} ({year}) - {row['source']}")
    
    print(f"\n💾 Writing {output_file}...")
    with open(output_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f, 
            fieldnames=["id", "concept", "source", "year", "country", "definition"]
        )
        writer.writeheader()
        writer.writerows(definitions)
    
    print(f"✅ Done! Check {output_file}")

if __name__ == "__main__":
    main()
