"""
Converts raw OCR text into structured product fields.

Uses regex/keyword heuristics (label text is fairly formulaic -- "Net Quantity:", "MRP:",
etc.). For every field we either return a value with a confidence + source snippet, or
None -- we never guess or hallucinate a value that isn't actually present in the text.
"""
import re
from typing import Optional, Dict, List

FIELD_PATTERNS = {
    "product_name": [r"(?:^|\n)\s*(?:Product\s*Name)\s*[:\-]\s*(.+)"],
    "net_quantity": [r"Net\s*(?:Qty|Quantity)\s*[:\-]\s*([0-9.,]+\s*(?:g|kg|ml|l|litre|litres|gm|gms))"],
    "mrp": [r"M\.?R\.?P\.?\s*[:\-]?\s*(?:Rs\.?|₹|INR)?\s*([0-9.,]+)"],
    "manufacturer": [r"Manufactured\s*By\s*[:\-]\s*(.+)", r"Manufacturer\s*[:\-]\s*(.+)"],
    "packer": [r"Packed\s*By\s*[:\-]\s*(.+)", r"Packer\s*[:\-]\s*(.+)"],
    "importer": [r"Imported\s*By\s*[:\-]\s*(.+)", r"Importer\s*[:\-]\s*(.+)"],
    "address": [r"Address\s*[:\-]\s*(.+)"],
    "country_of_origin": [r"Country\s*of\s*Origin\s*[:\-]\s*(.+)"],
    "batch_number": [r"Batch\s*(?:No\.?|Number)\s*[:\-]\s*([A-Za-z0-9\-\/]+)"],
    "manufacturing_date": [r"(?:Mfg\.?|Manufacturing)\s*Date\s*[:\-]\s*([0-9A-Za-z\/\-\s]+?)(?:\n|$)"],
    "expiry_date": [
        r"(?:Expiry|Exp\.?|Use\s*By)\s*Date\s*[:\-]\s*([0-9A-Za-z\/\-\s]+?)(?:\n|$)",
        r"Best\s*Before\s*[:\-]\s*(.+)",
    ],
    "consumer_care_details": [r"Consumer\s*Care\s*[:\-]\s*(.+)"],
    "brand": [r"Brand\s*[:\-]\s*(.+)"],
}

ALL_FIELDS = list(FIELD_PATTERNS.keys())


def extract_fields(raw_text: str) -> List[Dict]:
    """
    Returns a list of dicts, one per known field:
    { field_name, field_value, confidence, source_text, extraction_method }
    field_value is None when the field genuinely wasn't found in the OCR text.
    """
    results = []
    text = raw_text or ""

    for field_name, patterns in FIELD_PATTERNS.items():
        value: Optional[str] = None
        source_snippet: Optional[str] = None
        confidence: Optional[float] = None

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1).strip().strip(".,;")
                source_snippet = match.group(0).strip()
                # Heuristic confidence: exact keyword match with a captured value = high.
                confidence = 0.85 if value else 0.0
                break

        results.append({
            "field_name": field_name,
            "field_value": value,       # None/unknown if not found -- never fabricated
            "confidence": confidence,
            "source_text": source_snippet,
            "extraction_method": "regex" if value else None,
        })

    return results


def detect_category(extracted: Dict[str, Optional[str]], product_name_hint: Optional[str] = None) -> str:
    """
    Very lightweight keyword-based category detector. Meant to be corrected by an
    inspector -- this is a starting suggestion, not an authoritative classification.
    """
    haystack = " ".join(
        filter(None, [
            extracted.get("product_name"), product_name_hint, extracted.get("consumer_care_details"),
        ])
    ).lower()

    if any(k in haystack for k in ["atta", "rice", "oil", "flour", "spice", "masala", "snack", "biscuit"]):
        return "Food"
    if any(k in haystack for k in ["juice", "drink", "beverage", "water", "soda"]):
        return "Beverage"
    if any(k in haystack for k in ["soap", "shampoo", "cream", "lotion", "cosmetic", "toothpaste"]):
        return "Personal Care"
    if any(k in haystack for k in ["detergent", "cleaner", "disinfectant"]):
        return "Household Product"
    if haystack.strip():
        return "Packaged Commodity"
    return "Other"
