"""
Forest Definitions Extractor - Version 3
==========================================
Extracts forest definitions from DOCX documents and exports to CSV format.

Features:
- Detects countries and concept keywords
- Filters for official definitions using keywords
- Extracts technical criteria (area, canopy cover, height, width)
- Parses year from definitions
- Exports to structured CSV format
- Audit logging for data validation and error tracking

Author: TER2026 Project
Date: March 2026
"""

import re
import csv
import logging
import argparse
from datetime import datetime
from docx import Document
from pathlib import Path
from types import SimpleNamespace
import sys

# Add parent directory to path to import config
sys.path.insert(0, str(Path(__file__).parent.parent))
import config


class ForestDefinitionExtractor:
    """Extracts and structures forest definitions from documents."""
    
    def __init__(self, doc_path, use_docling=False):
        """
        Initialize extractor with document path.
        
        Args:
            doc_path: Path to the DOCX file containing definitions
        """
        self.doc_path = doc_path
        self.use_docling = use_docling
        self.doc = self._load_document(doc_path)
        
        # Initialize audit loggers
        self.setup_audit_logging()
        
        # Statistics tracking
        self.stats = {
            'paragraphs_processed': 0,
            'definitions_extracted': 0,
            'skipped_paragraphs': 0,
            'extraction_errors': 0
        }
        
        # Countries to detect (expandable)
        self.countries = [
            "Brazil", "Canada", "India", "France", "China", 
            "USA", "Australia", "Germany", "Japan", "Russia",
            "Indonesia", "Mexico", "Peru", "Colombia", "Argentina",
            "United Kingdom", "UK", "Italy", "Spain", "Poland",
            "Sweden", "Finland", "Norway", "Denmark", "Netherlands",
            "Belgium", "Austria", "Switzerland", "Portugal", "Greece",
            "Turkey", "South Africa", "Kenya", "Tanzania", "Uganda",
            "Ghana", "Nigeria", "Cameroon", "Congo", "Gabon",
            "Madagascar", "Mozambique", "Zimbabwe", "Zambia", "Malawi",
            "Thailand", "Vietnam", "Malaysia", "Philippines", "Myanmar",
            "Laos", "Cambodia", "Nepal", "Bangladesh", "Pakistan",
            "Afghanistan", "Iran", "Iraq", "Saudi Arabia", "Yemen",
            "Chile", "Uruguay", "Paraguay", "Bolivia", "Ecuador",
            "Venezuela", "Costa Rica", "Panama", "Guatemala", "Honduras",
            "Nicaragua", "El Salvador", "Belize", "Jamaica", "Cuba",
            "New Zealand", "Papua New Guinea", "Fiji", "Solomon Islands",
            "Belarus", "Ukraine", "Estonia", "Latvia", "Lithuania",
            "Czech Republic", "Slovakia", "Hungary", "Romania", "Bulgaria",
            "Croatia", "Serbia", "Bosnia", "Albania", "Macedonia",
            "Slovenia", "Montenegro", "Kosovo", "Moldova", "Georgia",
            "Armenia", "Azerbaijan", "Kazakhstan", "Uzbekistan", "Kyrgyzstan",
            "Tajikistan", "Turkmenistan", "Mongolia", "North Korea", "South Korea"
        ]
        
        # Concepts to extract
        self.concepts = [
            "forest", "deforestation", "afforestation", 
            "reforestation", "tree", "woodland", "land use", "land cover",
            "degradation", "forestation", "regeneration", "forestry",
            "stand", "grove", "thicket", "timber", "non-forest",
            "other wooded land", "woods", "stocking"
        ]
        
        # Keywords that indicate official definitions
        self.definition_keywords = [
            "means", "defined as", "refers to", "is defined as",
            "definition", "is understood as", "shall mean",
            "is considered", "is interpreted as"
        ]
        
        # Storage for extracted definitions
        self.definitions = []

        # Storage for unresolved paragraphs to be processed by LLM fallback
        self.llm_queue = []
        self._llm_queue_keys = set()

    def _load_document(self, doc_path):
        """Load document paragraphs from DOCX or via Docling."""
        if not self.use_docling:
            return Document(doc_path)

        try:
            from docling.document_converter import DocumentConverter
        except Exception as err:
            raise RuntimeError(
                "Docling is not installed. Install with: pip install docling"
            ) from err

        converter = DocumentConverter()
        result = converter.convert(str(doc_path))

        markdown_text = result.document.export_to_markdown()
        paragraphs = [
            SimpleNamespace(text=line.strip())
            for line in markdown_text.splitlines()
            if line.strip()
        ]

        return SimpleNamespace(paragraphs=paragraphs)
    
    def extract_year(self, text):
        """
        Extract year from definition text.
        
        Args:
            text: Definition text containing year
            
        Returns:
            Year as string or None
        """
        # Remove DOI fragments to avoid false positives like 1314 from 10.13140
        clean_text = re.sub(r'(?i)doi\s*:?\s*\S+', ' ', text)

        # Prefer years in common citation contexts
        year_patterns = [
            r'\((?:[^)]*?\b)?((?:18|19|20)\d{2})(?:\b[^)]*?)\)',
            r'\b(?:published|adopted|revised|rev\.?|source|edition|ed\.?|draft)\s*[:,-]?\s*((?:18|19|20)\d{2})\b',
            r'\b((?:18|19|20)\d{2})\b'
        ]

        for pattern in year_patterns:
            match = re.search(pattern, clean_text, re.IGNORECASE)
            if match:
                year = match.group(1)
                if 1800 <= int(year) <= 2100:
                    return year
        
        return None

    def setup_audit_logging(self):
        """Setup audit and error logging for extraction validation."""
        # Ensure logs directory exists
        config.OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
        
        # Audit logger (all processed paragraphs)
        self.audit_logger = logging.getLogger('audit')
        self.audit_logger.setLevel(logging.INFO)
        
        if config.ENABLE_AUDIT_LOG:
            audit_handler = logging.FileHandler(config.AUDIT_LOG)
            audit_handler.setFormatter(logging.Formatter(
                '%(asctime)s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            ))
            self.audit_logger.addHandler(audit_handler)
        
        # Error logger (skipped/failed paragraphs)
        self.error_logger = logging.getLogger('errors')
        self.error_logger.setLevel(logging.WARNING)
        
        if config.ENABLE_ERROR_LOG:
            error_handler = logging.FileHandler(config.ERROR_LOG)
            error_handler.setFormatter(logging.Formatter(
                '%(asctime)s | [%(levelname)s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            ))
            self.error_logger.addHandler(error_handler)
    
    def audit_paragraph(self, para_num, text, status, details=""):
        """Log paragraph processing to audit trail."""
        if self.audit_logger.handlers:
            msg = f"Para {para_num} | {status:12} | {len(text):5} chars"
            if details:
                msg += f" | {details}"
            self.audit_logger.info(msg)
    
    def audit_error(self, para_num, reason, excerpt=""):
        """Log extraction error/skip."""
        if self.error_logger.handlers:
            msg = f"Para {para_num} | SKIPPED | {reason}"
            if excerpt:
                excerpt_short = excerpt[:80].replace('\n', ' ')
                msg += f" | '{excerpt_short}...'"
            self.error_logger.warning(msg)

    def queue_paragraph_for_llm(self, para_num, concept, text, reason):
        """Queue unresolved paragraph for optional LLM fallback processing."""
        if not config.ENABLE_LLM_FALLBACK_QUEUE:
            return

        queue_key = (para_num, concept.lower(), reason)
        if queue_key in self._llm_queue_keys:
            return

        self._llm_queue_keys.add(queue_key)
        self.llm_queue.append({
            'queued_at': datetime.utcnow().isoformat(timespec='seconds') + 'Z',
            'paragraph_id': para_num,
            'concept': concept,
            'reason': reason,
            'text': text
        })

    def detect_country(self, text):
        """Detect country using explicit aliases and known country list."""
        country_aliases = {
            r'\bUnited States of America\b': 'USA',
            r'\bUnited States\b': 'USA',
            r'\bU\.?S\.?A\.?\b': 'USA',
            r'\bU\.?S\.?\b': 'USA',
            r'\bUnited Kingdom\b': 'UK',
            r'\bU\.?K\.?\b': 'UK',
            r'\bEU\b': 'European Union'
        }

        org_markers = [
            'fao', 'un-fao', 'unfao', 'unfccc', 'un-fccc', 'unep', 'un-ep',
            'ipcc', 'united nations', 'usda', 'forest information services',
            'world agroforestry', 'waf', 'organization', 'secretariat'
        ]

        def normalize_country_candidate(candidate):
            if not candidate:
                return None

            cleaned = re.sub(r'\b(?:18|19|20)\d{2}\b', '', candidate)
            cleaned = re.sub(r'[()\[\]]', ' ', cleaned)
            cleaned = re.sub(r'\s+', ' ', cleaned).strip(' ,;:-')

            if not cleaned:
                return None

            cleaned_lower = cleaned.lower()
            if any(marker in cleaned_lower for marker in org_markers):
                return None

            # Prefer first comma-delimited token (e.g. "Taiwan, ROC")
            primary = cleaned.split(',')[0].strip()
            primary_lower = primary.lower()
            if any(marker in primary_lower for marker in org_markers):
                return None

            # Match aliases first
            for pattern, alias_country in country_aliases.items():
                if re.search(pattern, primary, re.IGNORECASE):
                    return alias_country

            # Then match known country list
            for known_country in sorted(self.countries, key=len, reverse=True):
                if re.fullmatch(rf'{re.escape(known_country)}', primary, re.IGNORECASE):
                    return known_country

            return None

        for pattern, country in country_aliases.items():
            if re.search(pattern, text, re.IGNORECASE):
                return country

        # Match longer country names first to avoid partial hits
        for country in sorted(self.countries, key=len, reverse=True):
            if re.search(rf'\b{re.escape(country)}\b', text, re.IGNORECASE):
                return country

        # Try to detect from parentheses at start, e.g. (Taiwan, ROC 2001)
        match = re.match(r'\(([^)]+?)\s+(?:18|19|20)\d{2}\)', text)
        if match:
            return normalize_country_candidate(match.group(1))

        return None

    def detect_organization(self, text):
        """Detect organization or publisher from definition text."""
        def normalize_org_candidate(candidate):
            if not candidate:
                return None

            cleaned = candidate.strip().strip('"\'')
            cleaned = re.sub(r'&[a-z]+;?', ' ', cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r'\s+', ' ', cleaned).strip(' ,;:-')

            if not cleaned:
                return None

            cleaned_lower = cleaned.lower()

            # Reject obvious non-organization artifacts
            if re.search(r'https?://|www\.|@', cleaned_lower):
                return None
            if re.fullmatch(r'\d+', cleaned):
                return None
            if len(cleaned) <= 2:
                return None

            # Reject labels/titles that are not organizations
            non_org_prefixes = [
                'chapter', 'section', 'article', 'act on', 'state standard',
                'survey instructions', 'revised forestry code', 'latest draft',
                'earthtrends', 'anon'
            ]
            if any(cleaned_lower.startswith(prefix) for prefix in non_org_prefixes):
                return None

            # Reject country names used as organization
            if any(re.fullmatch(rf'{re.escape(country)}', cleaned, re.IGNORECASE)
                   for country in self.countries):
                return None

            return cleaned[:120]

        organization_patterns = [
            (r'\bUN-?FAO\b|\bFAO\b', 'UN-FAO'),
            (r'\bUN-?FCCC\b|\bUNFCCC\b|United Nations Framework Convention on Climate Change', 'UNFCCC'),
            (r'\bUN-?EP\b|\bUNEP\b|United Nations Environment Programme', 'UNEP'),
            (r'\bIPCC\b', 'IPCC'),
            (r'\bUnited Nations\b|\bUN\b', 'United Nations'),
            (r'\bUSDA\b|United States Department of Agriculture', 'USDA'),
            (r'\bEuropean Union\b|\bEU\b', 'European Union'),
            (r'\bWAF\b|World Agroforestry', 'World Agroforestry'),
            (r'\bForest Information Services\b', 'Forest Information Services')
        ]

        # Prefer parenthetical source tag at start, e.g. (UN-FCCC 2001), (Papua New Guinea), (UN)
        tag_match = re.match(r'^\(([^)]+)\)', text)
        if tag_match:
            tag = tag_match.group(1)
            tag_clean = re.sub(r'\b(?:18|19|20)\d{2}\b', '', tag)
            tag_clean = re.sub(r'\s+', ' ', tag_clean).strip(' ,;:-')
            if tag_clean:
                for pattern, name in organization_patterns:
                    if re.search(pattern, tag_clean, re.IGNORECASE):
                        return name

        for pattern, name in organization_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return name

        # Generic source capture: "Source: <organization>"
        match = re.search(r'(?i)\bsource\s*:\s*([^.;\n]+)', text)
        if match:
            candidate = match.group(1).strip()
            normalized = normalize_org_candidate(candidate)
            if normalized:
                return normalized

        # Generic "From: ..." capture when available
        from_match = re.search(r'(?i)\bfrom\s*:\s*([^.;\n]+)', text)
        if from_match:
            normalized = normalize_org_candidate(from_match.group(1).strip())
            if normalized:
                return normalized

        return None

    def parse_parenthetical_source_tag(self, text):
        """
        Parse leading parenthetical source tag and extract country + organization.

        Examples:
        - (USA-FED-EPA 2006) -> country=USA, organization=USA-FED-EPA
        - (UN-FCCC 2001) -> country=None, organization=UNFCCC
        - (Papua New Guinea) -> country=Papua New Guinea, organization=None
        """
        match = re.match(r'^\(([^)]+)\)', text)
        if not match:
            return None, None

        tag = match.group(1)
        tag_clean = re.sub(r'\b(?:18|19|20)\d{2}\b', '', tag)
        tag_clean = re.sub(r'\s+', ' ', tag_clean).strip(' ,;:-')
        if not tag_clean:
            return None, None

        # Organization detection first for known international bodies
        org_patterns = [
            (r'\bUN-?FAO\b|\bFAO\b', 'UN-FAO'),
            (r'\bUN-?FCCC\b|\bUNFCCC\b', 'UNFCCC'),
            (r'\bUN-?EP\b|\bUNEP\b', 'UNEP'),
            (r'\bIPCC\b', 'IPCC'),
            (r'\bUSDA\b', 'USDA'),
            (r'\bEU\b|\bEuropean Union\b', 'European Union'),
            (r'\bUN\b|\bUnited Nations\b', 'United Nations'),
            (r'\bWAF\b|World Agroforestry', 'World Agroforestry')
        ]

        detected_org = None
        for pattern, name in org_patterns:
            if re.search(pattern, tag_clean, re.IGNORECASE):
                detected_org = name
                break

        # Country aliases for tag prefixes
        tag_country_aliases = {
            'USA': 'USA',
            'US': 'USA',
            'UK': 'UK',
            'EU': 'European Union'
        }

        detected_country = None

        # Handle composite tags like USA-FED-...
        if '-' in tag_clean:
            first_token = tag_clean.split('-')[0].strip().upper()
            if first_token in tag_country_aliases:
                detected_country = tag_country_aliases[first_token]
                if not detected_org:
                    detected_org = tag_clean

        # Direct country name match in tag
        if not detected_country:
            for country in sorted(self.countries, key=len, reverse=True):
                if re.search(rf'\b{re.escape(country)}\b', tag_clean, re.IGNORECASE):
                    detected_country = country
                    break

        return detected_country, detected_org
    
    def detect_geographic_scope(self, text, organization):
        """
        Detect geographic scope (international, national, local/state).
        
        Args:
            text: Definition text
            organization: Organization name
            
        Returns:
            Geographic scope as string
        """
        text_lower = text.lower()
        org_lower = organization.lower() if organization and organization != 'Unknown' else ''
        
        # International indicators
        international_orgs = [
            'un', 'fao', 'unfccc', 'ipcc', 'cbd', 'unep', 'world bank', 
            'iucn', 'cifor', 'itto', 'un-redd', 'global', 'international'
        ]
        international_keywords = [
            'international', 'global', 'worldwide', 'kyoto protocol',
            'paris agreement', 'framework convention', 'montreal protocol'
        ]
        
        for org_key in international_orgs:
            if org_key in org_lower:
                return 'International'
        
        for keyword in international_keywords:
            if keyword in text_lower:
                return 'International'
        
        # Local/State indicators
        local_keywords = [
            'state', 'province', 'provincial', 'county', 'municipality',
            'local', 'regional', 'district', 'canton', 'prefecture'
        ]
        
        for keyword in local_keywords:
            if re.search(r'\b' + keyword + r'\b', text_lower):
                return 'Local/State'
        
        # Default to National if a country is mentioned but no international/local indicators
        return 'National'
    
    def extract_criteria(self, text):
        """
        Extract technical criteria from definition text.
        
        Args:
            text: Definition text containing criteria
            
        Returns:
            Dictionary with extracted criteria (including SI-normalized values)
        """
        criteria = {}
        text_lower = text.lower()
        
        # Min area (hectares, ha, acres)
        area_patterns = [
            r'(\d+\.?\d*)\s*(hectare|ha|acre)s?',
            r'area.*?(\d+\.?\d*)\s*(hectare|ha|acre)s?',
            r'spanning.*?(\d+\.?\d*)\s*(hectare|ha|acre)s?'
        ]
        for pattern in area_patterns:
            match = re.search(pattern, text_lower)
            if match:
                value = float(match.group(1))
                unit = match.group(2)
                criteria['min_area'] = value
                criteria['area_unit'] = unit
                # Normalize to hectares (SI unit for area)
                if 'acre' in unit:
                    criteria['min_area_si'] = value * 0.404686  # acres to hectares
                else:
                    criteria['min_area_si'] = value  # already in hectares
                break
        
        # Canopy/Crown cover (percentage)
        canopy_patterns = [
            r'(\d+\.?\d*)\s*%?\s*(?:tree\s+)?(?:canopy|crown)\s*cover',
            r'(?:canopy|crown)\s*cover.*?(\d+\.?\d*)\s*%',
            r'cover.*?(\d+\.?\d*)\s*(?:percent|%)'
        ]
        for pattern in canopy_patterns:
            match = re.search(pattern, text_lower)
            if match:
                value = float(match.group(1))
                criteria['min_canopy_cover'] = value
                criteria['canopy_unit'] = 'percent'
                # Already in percent (standard unit)
                criteria['min_canopy_cover_si'] = value
                break
        
        # Tree height (meters, metres, m, feet)
        height_patterns = [
            r'(\d+\.?\d*)\s*(meter|metre|m)s?\s*(?:height|tall|high)?',
            r'height.*?(\d+\.?\d*)\s*(meter|metre|m)s?',
            r'trees?\s*(?:higher|taller)\s*than\s*(\d+\.?\d*)\s*(meter|metre|m)s?',
            r'(\d+\.?\d*)\s*(feet|ft)\s*(?:height|tall|high)?'
        ]
        for pattern in height_patterns:
            match = re.search(pattern, text_lower)
            if match:
                value = float(match.group(1))
                unit = match.group(2) if len(match.groups()) > 1 else 'meter'
                # Normalize to meters (SI unit for height)
                if 'feet' in unit or 'ft' in unit:
                    criteria['min_height'] = value
                    criteria['height_unit'] = unit
                    criteria['min_height_si'] = value * 0.3048  # feet to meters
                else:
                    criteria['min_height'] = value
                    criteria['height_unit'] = unit
                    criteria['min_height_si'] = value  # already in meters
                break
        
        # Width (meters, metres)
        width_patterns = [
            r'width.*?(\d+\.?\d*)\s*(meter|metre|m)s?',
            r'(\d+\.?\d*)\s*(meter|metre|m)s?\s*wide'
        ]
        for pattern in width_patterns:
            match = re.search(pattern, text_lower)
            if match:
                value = float(match.group(1))
                unit = match.group(2)
                criteria['min_width'] = value
                criteria['width_unit'] = unit
                # Already in meters (SI unit)
                criteria['min_width_si'] = value
                break
        
        return criteria
    
    def determine_definition_type(self, text):
        """
        Determine the type of definition (Land Use, Land Cover, etc.).
        
        Args:
            text: Definition text
            
        Returns:
            Definition type as string
        """
        text_lower = text.lower()
        
        if 'land use' in text_lower:
            return 'Land Use'
        elif 'land cover' in text_lower:
            return 'Land Cover'
        elif 'administrative' in text_lower or 'legal' in text_lower:
            return 'Administrative'
        elif 'ecological' in text_lower:
            return 'Ecological'
        else:
            # Default based on criteria presence
            if 'canopy' in text_lower or 'crown' in text_lower:
                return 'Land Cover'
            return 'Land Use'
    
    def extract_definitions(self, concept="forest"):
        """
        Extract all definitions for a given concept.
        
        Args:
            concept: Concept to extract (default: "forest")
            
        Returns:
            List of extracted definitions
        """
        definitions = []
        
        print(f"[*] Extracting {concept} definitions...")
        print(f"[*] Processing {len(self.doc.paragraphs)} paragraphs...")
        
        for para_idx, para in enumerate(self.doc.paragraphs, 1):
            text = para.text.strip()
            
            self.stats['paragraphs_processed'] += 1
            
            if not text:
                self.audit_paragraph(para_idx, text, "SKIP", "Empty paragraph")
                self.stats['skipped_paragraphs'] += 1
                continue
            
            text_lower = text.lower()
            
            # Check if paragraph contains the concept
            if concept.lower() not in text_lower:
                self.audit_paragraph(para_idx, text, "SKIP", f"No '{concept}' keyword")
                self.stats['skipped_paragraphs'] += 1
                continue
            
            # Check if it contains definition keywords
            has_definition_keyword = any(
                keyword in text_lower 
                for keyword in self.definition_keywords
            )
            
            if not has_definition_keyword:
                self.audit_paragraph(para_idx, text, "SKIP", "No definition keywords")
                self.queue_paragraph_for_llm(para_idx, concept, text, "no_definition_keywords")
                self.stats['skipped_paragraphs'] += 1
                continue
            
            try:
                # Extract source metadata (parenthetical source tag has priority)
                tag_country, tag_organization = self.parse_parenthetical_source_tag(text)
                detected_country = tag_country or self.detect_country(text)
                detected_organization = tag_organization or self.detect_organization(text)

                # Extract metadata
                year = self.extract_year(text)
                criteria = self.extract_criteria(text)
                def_type = self.determine_definition_type(text)
                geographic_scope = self.detect_geographic_scope(text, detected_organization)

                definition = {
                    'concept': concept.capitalize(),
                    'country': detected_country or 'Unknown',
                    'organization': detected_organization or 'Unknown',
                    'year': year,
                    'definition_type': def_type,
                    'geographic_scope': geographic_scope,
                    'text': text,
                    'criteria': criteria
                }

                definitions.append(definition)
                self.stats['definitions_extracted'] += 1

                # Log successful extraction
                details = f"Country: {detected_country or 'Unknown'} | Org: {detected_organization or 'Unknown'}"
                self.audit_paragraph(para_idx, text, "EXTRACTED", details)
            except Exception as err:
                self.stats['extraction_errors'] += 1
                self.audit_error(para_idx, f"Extraction error: {err}", text)
                self.queue_paragraph_for_llm(para_idx, concept, text, "regex_extraction_error")
        
        print(f"[OK] Found {len(definitions)} {concept} definitions")
        print(f"[*] Extraction summary:")
        print(f"    - Paragraphs processed: {self.stats['paragraphs_processed']}")
        print(f"    - Definitions extracted: {self.stats['definitions_extracted']}")
        print(f"    - Paragraphs skipped: {self.stats['skipped_paragraphs']}")
        if config.ENABLE_LLM_FALLBACK_QUEUE:
            print(f"    - Queued for LLM fallback: {len(self.llm_queue)}")
        
        return definitions

    def export_llm_queue(self, queue_file=None):
        """Export unresolved paragraphs for second-pass LLM extraction."""
        if not config.ENABLE_LLM_FALLBACK_QUEUE:
            return

        queue_path = Path(queue_file) if queue_file else config.QUEUE_FOR_LLM_CSV
        queue_path.parent.mkdir(parents=True, exist_ok=True)

        with open(queue_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['queued_at', 'paragraph_id', 'concept', 'reason', 'text'])
            for item in self.llm_queue:
                writer.writerow([
                    item['queued_at'],
                    item['paragraph_id'],
                    item['concept'],
                    item['reason'],
                    item['text']
                ])

        print(f"[OK] Exported LLM queue to {queue_path} ({len(self.llm_queue)} rows)")
    
    def export_to_csv(self, definitions, output_dir="csv"):
        """
        Export definitions to CSV files (criteria.csv and definition.csv).
        
        Args:
            definitions: List of extracted definitions
            output_dir: Directory to save CSV files
        """
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Export to criteria.csv (main definitions)
        criteria_file = output_path / "criteria.csv"
        with open(criteria_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'concept_id', 'definition_id', 'label', 'alt_labels', 
                'definition_type', 'texte', 'organisation', 'country', 'year', 'geographic_scope'
            ])
            
            for idx, item in enumerate(definitions):
                concept_id = f"{item['concept'].lower()}_{idx:03d}"
                country_code = item['country'][:3].lower() if item['country'] != 'Unknown' else 'unk'
                year_code = item['year'] if item['year'] else 'unknown'
                definition_id = f"def_{country_code}_{year_code}_{idx}"
                
                writer.writerow([
                    concept_id,
                    definition_id,
                    item['concept'],
                    '',  # alt_labels (to be filled manually)
                    item['definition_type'],
                    item['text'],
                    item['organization'],
                    item['country'],
                    item['year'] or '',
                    item['geographic_scope']
                ])
        
        print(f"[OK] Exported to {criteria_file}")
        
        # Export to definition.csv (technical criteria)
        definition_file = output_path / "definition.csv"
        with open(definition_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['definition_id', 'criteria_name', 'value', 'unit', 'value_si'])
            
            for idx, item in enumerate(definitions):
                country_code = item['country'][:3].lower() if item['country'] != 'Unknown' else 'unk'
                year_code = item['year'] if item['year'] else 'unknown'
                definition_id = f"def_{country_code}_{year_code}_{idx}"
                
                # Write each criterion as a separate row
                for criterion_name, value in item['criteria'].items():
                    if '_unit' in criterion_name or '_si' in criterion_name:
                        continue  # Skip unit and SI entries (handled separately)
                    
                    # Get corresponding unit and SI value
                    unit_key = f"{criterion_name.replace('min_', '')}_unit"
                    unit = item['criteria'].get(unit_key, '')
                    si_key = f"{criterion_name}_si"
                    value_si = item['criteria'].get(si_key, '')
                    
                    writer.writerow([
                        definition_id,
                        criterion_name,
                        value,
                        unit,
                        value_si
                    ])
        
        print(f"[OK] Exported to {definition_file}")


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Extract forest definitions from source documents")
    parser.add_argument(
        "--doc-path",
        default="docs/sources/forest_definitions.docx",
        help="Path to input document",
    )
    parser.add_argument(
        "--use-docling",
        action="store_true",
        help="Use Docling for document parsing (supports PDF and more formats)",
    )
    args = parser.parse_args()
    
    # Configuration
    DOC_PATH = args.doc_path
    OUTPUT_DIR = "csv"
    CONCEPTS = [
        "forest", "deforestation", "afforestation", "reforestation", "tree",
        "woodland", "degradation", "forestation", "regeneration", "forestry",
        "stand", "grove", "thicket", "timber", "non-forest",
        "other wooded land", "woods", "stocking"
    ]
    
    print("=" * 60)
    print("Forest Definitions Extractor - Version 3")
    print("=" * 60)
    print()
    
    # Check if document exists
    if not Path(DOC_PATH).exists():
        print(f"[ERROR] Document not found at {DOC_PATH}")
        print(f"Please place your document in the docs/sources/ folder")
        print(f"Expected file: {DOC_PATH}")
        return
    
    # Initialize extractor
    extractor = ForestDefinitionExtractor(DOC_PATH, use_docling=args.use_docling)
    
    # Extract definitions for each concept
    all_definitions = []
    for concept in CONCEPTS:
        definitions = extractor.extract_definitions(concept)
        all_definitions.extend(definitions)
    
    # Export to CSV
    if all_definitions:
        print()
        print(f"[*] Total definitions extracted: {len(all_definitions)}")
        print()
        extractor.export_to_csv(all_definitions, OUTPUT_DIR)
        extractor.export_llm_queue()
        print()
        print("[OK] Extraction complete!")
        print(f"[*] Check {OUTPUT_DIR}/ for output files")
    else:
        print("[WARN] No definitions found. Check your document and configuration.")


if __name__ == "__main__":
    main()
