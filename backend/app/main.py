"""
CivicFlow backend entrypoint.

Smart India Hackathon 2026 -- Problem Statement SIH26034
"Software System to check compliance of Packaged Commodities under Legal Metrology
Rules, 2011 by scanning products, images and labels."
"""
import logging

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.database.session import Base, engine
from app.models import models  # noqa: F401 -- ensures models are registered on Base before create_all

from app.api import auth, users, products, inspections, images, ocr, extraction, compliance, rules, reports, complaints, analytics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("civicflow")

app = FastAPI(
    title="CivicFlow API",
    description=(
        "AI-assisted packaged commodity compliance checking system for Smart India "
        "Hackathon 2026 (Problem Statement SIH26034). Provides an explainable pipeline: "
        "OCR -> structured extraction -> configurable rule engine -> compliance validation "
        "-> evidence -> human review -> PDF report -> inspection history."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables verified/created.")
    except SQLAlchemyError as exc:
        # We deliberately don't crash the whole app on a DB connectivity issue at
        # startup -- Swagger docs and health checks should still be reachable so the
        # error is visible instead of the process just failing silently in a container.
        logger.error("Database initialization failed: %s", exc)


@app.exception_handler(SQLAlchemyError)
def handle_db_errors(request: Request, exc: SQLAlchemyError):
    logger.error("Database error on %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "A database error occurred. Please try again or contact an administrator."},
    )


@app.get("/", tags=["Health"], summary="Health check")
def root():
    return {
        "service": settings.PROJECT_NAME,
        "problem_statement": settings.PROBLEM_STATEMENT_ID,
        "status": "ok",
        "docs": "/docs",
    }


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(products.router)
app.include_router(inspections.router)
app.include_router(images.router)
app.include_router(ocr.router)
app.include_router(extraction.router)
app.include_router(compliance.router)
app.include_router(rules.router)
app.include_router(reports.router)
app.include_router(complaints.router)
app.include_router(analytics.router)
