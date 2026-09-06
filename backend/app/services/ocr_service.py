"""
OCR service. Uses Tesseract (via pytesseract) when available.

If pytesseract or the tesseract binary is not installed on the machine running this
backend, the service transparently drops into DEMO MODE and returns clearly-labelled
sample text -- it never presents demo output as if it were real OCR. This keeps the
product demoable per the spec even when the OCR dependency isn't set up yet.
"""
from typing import Tuple, List, Dict

try:
    import pytesseract
    from PIL import Image
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

from app.core.config import settings

DEMO_TEXT = (
    "Sample Atta\n"
    "Net Quantity: 5 kg\n"
    "MRP: Rs. 320 (Inclusive of all taxes)\n"
    "Manufactured By: ABC Foods Pvt Ltd\n"
    "Address: Plot 12, Industrial Area, Coimbatore, Tamil Nadu\n"
    "Country of Origin: India\n"
    "Batch No: B2026-014\n"
    "Mfg Date: 03/2026\n"
    "Best Before: 12 months from mfg date\n"
    "Consumer Care: 1800-000-0000, care@abcfoods.example"
)


def _tesseract_available() -> bool:
    if not TESSERACT_AVAILABLE:
        return False
    try:
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False


def run_ocr(image_path: str) -> Dict:
    """
    Returns { raw_text, confidence, bounding_boxes, engine_used, is_demo_mode }.
    """
    engine_configured = settings.OCR_ENGINE.lower()

    if engine_configured != "demo" and _tesseract_available():
        try:
            image = Image.open(image_path)
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)

            words: List[str] = []
            boxes: List[dict] = []
            confidences: List[float] = []

            for i, text in enumerate(data.get("text", [])):
                text = text.strip()
                if not text:
                    continue
                conf_raw = data["conf"][i]
                try:
                    conf = float(conf_raw)
                except (TypeError, ValueError):
                    conf = -1.0
                words.append(text)
                if conf >= 0:
                    confidences.append(conf)
                boxes.append({
                    "text": text,
                    "left": data["left"][i],
                    "top": data["top"][i],
                    "width": data["width"][i],
                    "height": data["height"][i],
                    "conf": conf,
                })

            raw_text = " ".join(words)
            avg_conf = round(sum(confidences) / len(confidences), 2) if confidences else None

            # Never fabricate: if OCR genuinely found nothing, say so -- don't backfill demo text.
            return {
                "raw_text": raw_text,
                "confidence": avg_conf,
                "bounding_boxes": boxes,
                "engine_used": "tesseract",
                "is_demo_mode": False,
            }
        except Exception as exc:
            return {
                "raw_text": "",
                "confidence": None,
                "bounding_boxes": [],
                "engine_used": "tesseract",
                "is_demo_mode": False,
                "error": f"OCR failed: {exc}",
            }

    # ---- DEMO MODE ----
    return {
        "raw_text": DEMO_TEXT,
        "confidence": 92.0,
        "bounding_boxes": [],
        "engine_used": "demo",
        "is_demo_mode": True,
    }
