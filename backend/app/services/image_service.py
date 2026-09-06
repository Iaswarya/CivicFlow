"""
Image ingestion + basic quality analysis using OpenCV.

We never hard-reject an image outright for quality -- per spec, low quality produces a
warning that flows through to the inspector, not a blocked upload.
"""
import os
import uuid
from typing import Tuple, Optional

from app.core.config import settings

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

BLUR_THRESHOLD = 100.0       # Laplacian variance below this -> "possibly blurry"
MIN_DIMENSION = 400          # px, below this on either side -> "low resolution"


def save_upload(file_bytes: bytes, original_filename: str, inspection_id: str) -> str:
    """Persist an uploaded image to disk with a safe, unique filename. Returns the path."""
    ext = os.path.splitext(original_filename)[1].lower()
    if ext not in (".jpg", ".jpeg", ".png", ".webp"):
        ext = ".jpg"
    safe_name = f"{inspection_id}_{uuid.uuid4().hex}{ext}"
    dest_dir = os.path.join(settings.UPLOAD_DIR, inspection_id)
    os.makedirs(dest_dir, exist_ok=True)
    dest_path = os.path.join(dest_dir, safe_name)
    with open(dest_path, "wb") as f:
        f.write(file_bytes)
    return dest_path


def analyze_quality(image_path: str) -> dict:
    """
    Returns a dict: { width, height, is_blurry, is_low_resolution, sharpness_score, quality_warning }.
    Falls back to "unknown" values (no crash) if OpenCV isn't available in this environment --
    the upload still succeeds, just without automated quality scoring.
    """
    result = {
        "width": None,
        "height": None,
        "is_blurry": False,
        "is_low_resolution": False,
        "sharpness_score": None,
        "quality_warning": None,
    }

    if not CV2_AVAILABLE:
        result["quality_warning"] = "Image quality analysis unavailable (OpenCV not installed in this environment)."
        return result

    img = cv2.imread(image_path)
    if img is None:
        result["quality_warning"] = "Could not read image file for quality analysis."
        return result

    height, width = img.shape[:2]
    result["width"] = int(width)
    result["height"] = int(height)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    result["sharpness_score"] = round(float(laplacian_var), 2)

    warnings = []
    if laplacian_var < BLUR_THRESHOLD:
        result["is_blurry"] = True
        warnings.append("Image may be blurry -- some declarations might not be readable.")
    if width < MIN_DIMENSION or height < MIN_DIMENSION:
        result["is_low_resolution"] = True
        warnings.append("Image resolution is low -- consider re-capturing for a clearer scan.")

    if warnings:
        result["quality_warning"] = " ".join(warnings)

    return result
