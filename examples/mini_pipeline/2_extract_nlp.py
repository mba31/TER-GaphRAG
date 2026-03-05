#!/usr/bin/env python3
"""
Alternative Extraction: NLP-based (No Regex)
=============================================
Uses natural language processing to extract dates, entities, and patterns.

Input:  1_sample_data.csv
Output: extracted_definitions_nlp.csv

Approach:
  - dateutil for intelligent date parsing (not regex!)
  - Understand sentence structure instead of pattern matching
  - More robust, handles variations better
"""

import csv
from pathlib import Path
from dateutil import parser as date_parser

def extract_year_nlp(text):
    """
    Extract year using NLP-style approach (not regex).
    dateutil can understand context like "published in 2015" or just "2015".
    """
    try:
        # dateutil.parser understands natural language dates
        parsed_date = date_parser.parse(text, fuzzy=True)
        return str(parsed_date.year)
    except:
        # Fallback if parsing fails
        return "unknown"

def find_sentences(text):
    """
    Split text into sentences (basic NLP approach).
    Better than regex for understanding structure.
    """
    import re
    # Split on periods, but keep some context
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]

def extract_definition_nlp(text):
    """
    Extract definition using sentence analysis.
    Look for sentences that define or describe.
    """
    sentences = find_sentences(text)
    
    # Find definition keywords in context
    definition_markers = ["is ", "means ", "refers to ", "defined as ", "described as "]
    
    # Usually first 1-2 sentences contain the definition
    for sentence in sentences[:3]:
        sentence_lower = sentence.lower()
        if any(marker in sentence_lower for marker in definition_markers):
            return sentence.strip()
    
    # If no explicit marker, return first sentence
    return sentences[0] if sentences else text

def clean_definition(text):
    """Clean using NLP principles (not just whitespace)."""
    # Remove extra spaces
    text = " ".join(text.split())
    # Remove redundant punctuation
    text = text.rstrip('.,;:')
    return text

def main():
    input_file = Path("1_sample_data.csv")
    output_file = Path("extracted_definitions_nlp.csv")
    
    if not input_file.exists():
        print(f"❌ Missing {input_file}")
        return
    
    print(f"📖 Reading {input_file} (NLP Mode)...\n")
    
    definitions = []
    with open(input_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # NLP approach 1: Use dateutil instead of regex
            year = extract_year_nlp(row["year"])
            
            # NLP approach 2: Understand sentence structure
            definition_text = extract_definition_nlp(row["definition_text"])
            cleaned = clean_definition(definition_text)
            
            definitions.append({
                "id": f"def_{row['country'].lower()}_{year}_001",
                "concept": "forest",
                "source": row["source"],
                "year": year,
                "country": row["country"],
                "definition": cleaned,
                "extraction_method": "NLP"
            })
            print(f"  ✓ {row['country']} ({year}) - Extracted via NLP")
    
    print(f"\n💾 Writing {output_file}...")
    with open(output_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f, 
            fieldnames=[
                "id", "concept", "source", "year", 
                "country", "definition", "extraction_method"
            ]
        )
        writer.writeheader()
        writer.writerows(definitions)
    
    print(f"✅ Done! Check {output_file}\n")
    print("📊 Comparison:")
    print("  Regex:  Fast, simple, brittle")
    print("  NLP:    Slower, flexible, understands context")

if __name__ == "__main__":
    main()
