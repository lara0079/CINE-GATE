from __future__ import annotations

from pathlib import Path
from time import perf_counter
from typing import Literal
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.config import get_settings
from app.domain.models import (
    ActionType,
    AssetType,
    AuditEvent,
    ClearanceOutcome,
    ClearanceReview,
    DashboardSummary,
    DistributionChannel,
    EvidenceType,
    EvidenceVerification,
    FindingGuide,
    PermissionStatus,
    ProductionAction,
    ReviewEvidenceBundle,
    ReviewLineage,
    SystemOptions,
)
from app.services.review_service import (
    DecisionNoteRequiredError,
    HumanApprovalNotAllowedError,
    RevisionConflictError,
    ReviewAlreadyFinalizedError,
    ReviewNotFoundError,
    ReviewService,
)

APP_VERSION = "0.5.0"
MAX_REQUEST_BYTES = 1_000_000

settings = get_settings()
service = ReviewService(settings)
app = FastAPI(
    title=settings.app_name,
    version=APP_VERSION,
    description=(
        "Agentic film-production rights-clearance and human-review workflow. "
        "The deterministic policy records supplied metadata; Gemini is advisory only."
    ),
    contact={"name": "CINE-GATE project"},
    license_info={"name": "MIT"},
)

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class HumanDecisionRequest(BaseModel):
    decision: Literal["approved", "rejected"]
    reviewer: str = Field(min_length=2, max_length=120)
    note: str | None = Field(default=None, max_length=2000)


@app.middleware("http")
async def request_and_response_hardening(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > MAX_REQUEST_BYTES:
                return JSONResponse(status_code=413, content={"detail": "Request body is too large"})
        except ValueError:
            return JSONResponse(status_code=400, content={"detail": "Invalid Content-Length header"})

    request_id = request.headers.get("x-request-id") or str(uuid4())
    started = perf_counter()
    response = await call_next(request)
    duration_ms = max(0.1, (perf_counter() - started) * 1000)
    response.headers["X-Request-ID"] = request_id
    response.headers["Server-Timing"] = f"app;dur={duration_ms:.2f}"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), payment=(), usb=()"
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
    response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; style-src 'self'; script-src 'self'; img-src 'self' data:; "
        "connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
    )
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    if request.url.scheme == "https":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": APP_VERSION,
        "agent_mode": settings.agent_mode,
        "environment": settings.environment,
        "workflow_version": settings.agent_workflow_version,
        "agent_engine_configured": str(bool(settings.agent_engine_resource_name)).lower(),
    }


@app.get("/ready")
def readiness() -> dict[str, str]:
    try:
        service.summary()
        database_check = service.database_check()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database is not ready") from exc
    if database_check.lower() != "ok":
        raise HTTPException(status_code=503, detail="Database integrity check failed")
    return {
        "status": "ready",
        "database": "available",
        "database_check": database_check,
        "agent_mode": settings.agent_mode,
    }


@app.get("/api/system/capabilities")
def system_capabilities() -> dict[str, object]:
    return {
        "product": settings.app_name,
        "version": APP_VERSION,
        "workflow_version": settings.agent_workflow_version,
        "agent_mode": settings.agent_mode,
        "gemini_model": settings.gemini_model,
        "google_cloud_project_configured": bool(settings.google_cloud_project),
        "agent_engine_configured": bool(settings.agent_engine_resource_name),
        "runtime_layers": [
            {
                "name": "Rights Scout",
                "type": "advisory agent",
                "purpose": "Discovers possible rights-bearing material without inferring permission.",
            },
            {
                "name": "Scope Controller",
                "type": "deterministic control",
                "purpose": "Evaluates supplied permission metadata and produces the recorded outcome.",
            },
            {
                "name": "Evidence Mapper",
                "type": "deterministic control",
                "purpose": "Builds the asset-level rights matrix and release-readiness metrics.",
            },
            {
                "name": "Release Brief Agent",
                "type": "advisory agent",
                "purpose": "Explains findings and recommended corrective actions without changing the outcome.",
            },
            {
                "name": "Human Control Plane",
                "type": "named human decision",
                "purpose": "Records the final accountable decision or requires a corrected revision.",
            },
        ],
        "guardrails": [
            "AI cannot establish that permission exists.",
            "AI cannot authenticate contracts, signatures, licenses, or consent forms.",
            "The deterministic policy is the source of the recorded outcome.",
            "BLOCKED records cannot be human-approved.",
            "Every corrected record becomes a linked revision rather than overwriting history.",
        ],
        "competition_integrations": {
            "google_runtime": "configured" if settings.agent_mode == "google" else "local scaffold",
            "vertex_agent_engine": "configured" if settings.agent_engine_resource_name else "account-stage deployment required",
            "ibm_bob": "development evidence must be created through the entrant account",
        },
    }


@app.get("/api/options", response_model=SystemOptions)
def options() -> SystemOptions:
    return SystemOptions(
        action_types=[item.value for item in ActionType],
        asset_types=[item.value for item in AssetType],
        distribution_channels=[item.value for item in DistributionChannel],
        permission_statuses=[item.value for item in PermissionStatus],
        evidence_types=[item.value for item in EvidenceType],
    )


@app.get("/api/findings/catalog", response_model=list[FindingGuide])
def finding_catalog() -> list[FindingGuide]:
    return service.finding_catalog()


@app.post("/api/reviews", response_model=ClearanceReview, status_code=201)
def create_review(action: ProductionAction) -> ClearanceReview:
    return service.create(action)


@app.get("/api/reviews", response_model=list[ClearanceReview])
def list_reviews(
    limit: int = Query(default=100, ge=1, le=500),
    outcome: ClearanceOutcome | None = Query(default=None),
    q: str | None = Query(default=None, max_length=100),
) -> list[ClearanceReview]:
    return service.list(limit=limit, outcome=outcome, query=q)


@app.get("/api/reviews/summary", response_model=DashboardSummary)
def review_summary() -> DashboardSummary:
    return service.summary()


@app.get("/api/reviews/{review_id}", response_model=ClearanceReview)
def get_review(review_id: UUID) -> ClearanceReview:
    try:
        return service.get(review_id)
    except ReviewNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Review not found") from exc


@app.post("/api/reviews/{review_id}/revisions", response_model=ClearanceReview, status_code=201)
def create_revision(review_id: UUID, action: ProductionAction) -> ClearanceReview:
    try:
        return service.create_revision(review_id, action)
    except ReviewNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Review not found") from exc
    except RevisionConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.get("/api/reviews/{review_id}/lineage", response_model=ReviewLineage)
def review_lineage(review_id: UUID) -> ReviewLineage:
    try:
        return service.lineage(review_id)
    except ReviewNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Review not found") from exc


@app.get("/api/reviews/{review_id}/events", response_model=list[AuditEvent])
def review_events(review_id: UUID) -> list[AuditEvent]:
    try:
        return service.events(review_id)
    except ReviewNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Review not found") from exc


@app.get("/api/reviews/{review_id}/evidence", response_model=ReviewEvidenceBundle)
def review_evidence(review_id: UUID) -> ReviewEvidenceBundle:
    try:
        return service.evidence_bundle(review_id)
    except ReviewNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Review not found") from exc


@app.get("/api/reviews/{review_id}/evidence/verify", response_model=EvidenceVerification)
def verify_review_evidence(review_id: UUID) -> EvidenceVerification:
    try:
        return service.verify_evidence(review_id)
    except ReviewNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Review not found") from exc


@app.get("/api/reviews/{review_id}/evidence/download", include_in_schema=False)
def download_review_evidence(review_id: UUID) -> JSONResponse:
    try:
        bundle = service.evidence_bundle(review_id)
    except ReviewNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Review not found") from exc
    return JSONResponse(
        content=bundle.model_dump(mode="json"),
        headers={
            "Content-Disposition": f'attachment; filename="cine-gate-{review_id}-evidence.json"'
        },
    )


@app.get("/api/reviews/{review_id}/rights-matrix.csv", include_in_schema=False)
def download_rights_matrix(review_id: UUID) -> Response:
    try:
        content = service.rights_matrix_csv(review_id)
    except ReviewNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Review not found") from exc
    return Response(
        content=content.encode("utf-8-sig"),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="cine-gate-{review_id}-rights-matrix.csv"'
        },
    )


@app.get("/api/reviews/{review_id}/release-package", include_in_schema=False)
def download_release_package(review_id: UUID) -> Response:
    try:
        content = service.release_package(review_id)
    except ReviewNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Review not found") from exc
    return Response(
        content=content,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="cine-gate-{review_id}-release-package.zip"'
        },
    )


@app.get("/api/reviews/{review_id}/report", response_class=HTMLResponse, include_in_schema=False)
def release_report(review_id: UUID) -> HTMLResponse:
    try:
        html = service.release_report(review_id)
    except ReviewNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Review not found") from exc
    return HTMLResponse(
        content=html,
        headers={
            "Content-Disposition": f'inline; filename="cine-gate-{review_id}-release-report.html"'
        },
    )


@app.post("/api/reviews/{review_id}/human-decision", response_model=ClearanceReview)
def human_decision(review_id: UUID, payload: HumanDecisionRequest) -> ClearanceReview:
    try:
        return service.finalize(
            review_id=review_id,
            decision=payload.decision,
            reviewer=payload.reviewer,
            note=payload.note,
        )
    except ReviewNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Review not found") from exc
    except HumanApprovalNotAllowedError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except (ReviewAlreadyFinalizedError, DecisionNoteRequiredError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
