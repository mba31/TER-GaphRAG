#!/usr/bin/env python3
"""
Alternative Extraction: ML-based
================================
Demonstrates a lightweight supervised extraction flow using scikit-learn.

Input:  1_sample_data.csv
Output: extracted_definitions_ml.csv

Notes:
  - This is an educational variant (tiny dataset).
  - It trains a simple classifier to decide if a text likely contains
    a definition, then extracts cleaned content.
"""

import argparse
import csv
import importlib
from pathlib import Path
from typing import List


def clean_text(text: str) -> str:
    return " ".join(text.split())


def train_definition_classifier(texts: List[str], labels: List[int]):
    tfidf_module = importlib.import_module("sklearn.feature_extraction.text")
    linear_model_module = importlib.import_module("sklearn.linear_model")
    pipeline_module = importlib.import_module("sklearn.pipeline")

    TfidfVectorizer = getattr(tfidf_module, "TfidfVectorizer")
    LogisticRegression = getattr(linear_model_module, "LogisticRegression")
    Pipeline = getattr(pipeline_module, "Pipeline")

    model = Pipeline(
        steps=[
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1)),
            ("clf", LogisticRegression(max_iter=500)),
        ]
    )
    model.fit(texts, labels)
    return model


def main() -> None:
    parser = argparse.ArgumentParser(description="ML-based extraction for mini pipeline")
    parser.add_argument("--threshold", type=float, default=0.5, help="Probability threshold")
    args = parser.parse_args()

    input_file = Path("1_sample_data.csv")
    output_file = Path("extracted_definitions_ml.csv")

    if not input_file.exists():
        print(f"❌ Missing {input_file}")
        return

    try:
        importlib.import_module("sklearn")
    except Exception:
        print("❌ scikit-learn is required for this variant.")
        print("Install with: pip install scikit-learn")
        return

    # Tiny educational training set (definition vs non-definition text)
    train_texts = [
        "Forest is land spanning more than 0.5 hectares with trees.",
        "A forest means tree-covered ecosystems with ecological function.",
        "Forest refers to tree formations above specific canopy thresholds.",
        "Meeting agenda for next Tuesday and action items.",
        "Budget approval details and procurement policy changes.",
        "Weather forecast and transport schedule for the week.",
    ]
    train_labels = [1, 1, 1, 0, 0, 0]

    model = train_definition_classifier(train_texts, train_labels)

    rows = []
    with open(input_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    outputs = []

    print("📖 Running ML extraction...\n")

    for row in rows:
        text = row["definition_text"]
        probability = float(model.predict_proba([text])[0][1])
        is_definition = probability >= args.threshold

        if is_definition:
            definition = clean_text(text)
            method = "ML"
        else:
            definition = ""
            method = "ML_REJECTED"

        outputs.append(
            {
                "id": f"def_{row['country'].lower()}_{row['year']}_001",
                "concept": "forest",
                "source": row["source"],
                "year": row["year"],
                "country": row["country"],
                "definition": definition,
                "extraction_method": method,
                "ml_score": f"{probability:.4f}",
            }
        )

        status = "✓" if is_definition else "⚠"
        print(f"  {status} {row['country']} ({row['year']}) - score={probability:.3f}")

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
                "ml_score",
            ],
        )
        writer.writeheader()
        writer.writerows(outputs)

    print(f"\n✅ Done! Check {output_file}")


if __name__ == "__main__":
    main()
