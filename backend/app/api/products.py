"""
Product CRUD. Not every field is mandatory -- packaged commodities vary widely.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_roles
from app.database.session import get_db
from app.models import models as m
from app.schemas import schemas as s

router = APIRouter(prefix="/api/products", tags=["Products"])


@router.post("", response_model=s.ProductOut, status_code=status.HTTP_201_CREATED,
             summary="Create a product", description="Creates a product record (fields are optional; fill in what is known).")
def create_product(payload: s.ProductCreate, db: Session = Depends(get_db),
                    current_user: m.User = Depends(get_current_user)):
    product = m.Product(**payload.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.get("", response_model=List[s.ProductOut], summary="List products")
def list_products(category: Optional[str] = None, search: Optional[str] = None,
                   db: Session = Depends(get_db), current_user: m.User = Depends(get_current_user)):
    q = db.query(m.Product)
    if category:
        q = q.filter(m.Product.category == category)
    if search:
        like = f"%{search}%"
        q = q.filter(m.Product.product_name.ilike(like) | m.Product.brand.ilike(like))
    return q.order_by(m.Product.created_at.desc()).all()


@router.get("/{product_id}", response_model=s.ProductOut, summary="Get a product")
def get_product(product_id: str, db: Session = Depends(get_db), current_user: m.User = Depends(get_current_user)):
    product = db.query(m.Product).get(product_id)
    if not product:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found.")
    return product


@router.put("/{product_id}", response_model=s.ProductOut, summary="Update a product")
def update_product(product_id: str, payload: s.ProductUpdate, db: Session = Depends(get_db),
                    current_user: m.User = Depends(require_roles("ADMIN", "INSPECTOR"))):
    product = db.query(m.Product).get(product_id)
    if not product:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a product")
def delete_product(product_id: str, db: Session = Depends(get_db),
                    current_user: m.User = Depends(require_roles("ADMIN"))):
    product = db.query(m.Product).get(product_id)
    if not product:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found.")
    db.delete(product)
    db.commit()
