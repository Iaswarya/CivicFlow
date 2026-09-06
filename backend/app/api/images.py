"""
Image upload + quality analysis for an inspection.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_current_user
from app.database.session import get_db
from app.models import models as m
from app.schemas import schemas as s
from app.services import image_service

router = APIRouter(prefix="/api/inspections", tags=["Images"])


@router.post(
    "/{inspection_id}/images", response_model=s.ProductImageOut, status_code=status.HTTP_201_CREATED,
    summary="Upload a label image", description="Uploads a product/label image for an inspection and runs a basic OpenCV quality check.",
)
async def upload_image(
    inspection_id: str,
    file: UploadFile = File(...),
    image_type: Optional[str] = Form(default="front_label"),
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    inspection = db.query(m.Inspection).get(inspection_id)
    if not inspection:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Inspection not found.")

    if file.content_type not in settings.ALLOWED_IMAGE_TYPES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                             f"Unsupported file type '{file.content_type}'. Allowed: {settings.ALLOWED_IMAGE_TYPES}")

    contents = await file.read()
    size_mb = len(contents) / (1024 * 1024)
    if size_mb > settings.MAX_UPLOAD_SIZE_MB:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                             f"File too large ({size_mb:.1f} MB). Limit is {settings.MAX_UPLOAD_SIZE_MB} MB.")

    try:
        path = image_service.save_upload(contents, file.filename or "upload.jpg", inspection_id)
        quality = image_service.analyze_quality(path)
    except Exception as exc:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Failed to process image: {exc}")

    image = m.ProductImage(
        inspection_id=inspection_id,
        image_path=path,
        image_type=image_type,
        width=quality["width"],
        height=quality["height"],
        is_blurry=quality["is_blurry"],
        is_low_resolution=quality["is_low_resolution"],
        quality_warning=quality["quality_warning"],
        sharpness_score=quality["sharpness_score"],
    )
    db.add(image)
    db.commit()
    db.refresh(image)
    return image


@router.get("/{inspection_id}/images", response_model=List[s.ProductImageOut], summary="List images for an inspection")
def list_images(inspection_id: str, db: Session = Depends(get_db), current_user: m.User = Depends(get_current_user)):
    return db.query(m.ProductImage).filter(m.ProductImage.inspection_id == inspection_id).all()
