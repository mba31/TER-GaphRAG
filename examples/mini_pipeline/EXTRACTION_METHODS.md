# Extraction Methods Comparison

## 4 Ways to Extract Data (Without Pure Regex)

### 1. **Regex** (What you started with)
```python
import re
year = re.search(r'\d{4}', text).group(0)
```
**Pros:** Fast, simple, works great for structured patterns
**Cons:** Brittle, fails on variations, hard to maintain
**Best for:** Formatted data (dates like YYYY, IDs, phone numbers)

---

### 2. **NLP / Entity Recognition** (2_extract_nlp.py)
```python
from dateutil import parser
year = parser.parse(text, fuzzy=True).year
```
**Pros:** Understands context, handles variations, "2015", "in 2015", "published 2015" all work
**Cons:** Slower, needs language libraries, overkill for simple cases
**Best for:** Natural language text, dates in sentences, understanding meaning
**Tools:** dateutil, spacy, NLTK, Stanford NER

---

### 3. **LLM-based Extraction** (extraction_fallback.py in main project)
```python
from openai import OpenAI
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Extract year from: " + text}]
)
```
**Pros:** Understands any format, handles ambiguity, very flexible
**Cons:** Expensive ($), slow, needs API
**Best for:** Complex extraction, when no clear pattern exists, quality > speed
**Tools:** OpenAI, Anthropic Claude, local Ollama

---

### 4. **ML Models** (Trained on labeled data)
```python
from spacy import load
nlp = load("en_core_web_sm")
doc = nlp(text)
for entity in doc.ents:
    if entity.label_ == "DATE":
        print(entity.text)
```
**Pros:** Fast, accurate after training, understands domain-specific language
**Cons:** Requires labeled training data, setup overhead
**Best for:** Production pipelines, high volume, consistency required
**Tools:** spacy, transformers (BERT, )

---

## The TER2026 Project Uses...

- **Phase 1 (Regex)**: `extract_definitions.py` uses regex for known patterns
  - Fast baseline
  - Gets ~3% of definitions (legitimate filter)
  
- **Phase 2 (LLM)**: `extraction_fallback.py` uses OpenAI/Ollama for hard cases
  - Processes the 9,240 queued paragraphs
  - Higher quality, slower
  
- **Phase 3 (Optional)**: `Docling` uses ML models to understand document layout
  - Works on PDF, scanned images, complex formatting
  - New capability

---

## Quick Comparison Table

| Method | Speed | Accuracy | Cost | Learning Curve | Best Use |
|--------|-------|----------|------|---|---|
| **Regex** | ⚡ Fast | ⭐⭐ | Free | Easy | Structured data (dates, IDs) |
| **NLP** | 🐢 Slow | ⭐⭐⭐ | Free | Medium | Natural language, context |
| **LLM** | 🐢 Slow | ⭐⭐⭐⭐ | $ | Easy (API) | Complex, ambiguous text |
| **ML Model** | ⚡ Fast | ⭐⭐⭐⭐ | Free* | Hard | Production, high volume |

*Free = once trained; requires labeled training data

---

## How to Choose?

```
Is the data well-formatted?
  ✅ YES → Use Regex (fast baseline)
  ❌ NO → Continue...

Is the pattern simple & consistent?
  ✅ YES → Use Regex + NLP for edge cases
  ❌ NO → Continue...

Do you have enough quality examples?
  ✅ YES → Train an ML model
  ❌ NO → Use LLM (costs money but works)

Need production speed & accuracy?
  ✅ YES → Combine: Regex (fast) + LLM (hard cases)
  ❌ NO → Just use LLM
```

---

## Your Project's Hybrid Approach

### ✅ Smart Design:

1. **Regex first** (fast baseline)
   - Catches ~1,859 definitions instantly
   - Low false positives

2. **Queue unresolved** 
   - Only remaining 9,240 to LLM

3. **LLM fallback** (flexible)
   - Handles anything regex missed
   - Only pays when needed

This is **production best practice** — speed + accuracy + cost-effective!

---

## Try It Yourself

```bash
# Compare both methods in mini_pipeline:
python 2_extract.py          # Regex approach
python 2_extract_nlp.py      # NLP approach

# Then compare the CSV files:
diff extracted_definitions.csv extracted_definitions_nlp.csv
```

Both produce same output here, but NLP handles weirder dates better!
