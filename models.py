from __future__ import annotations

from datetime import date, datetime, timezone
from enum import StrEnum
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, model_validator


class ClearanceOutcome(StrEnum):
    CLEARED = "CLEARED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    BLOCKED = "BLOCKED"


class AssetType(StrEnum):
    LIKENESS = "likeness"
    VOICE = "voice"
    MUSIC = "music"
    FOOTAGE = "footage"
    SCRIPT = "script"
    ARTWORK = "artwork"
    LOCATION = "location"
    OTHER = "other"


class PermissionStatus(StrEnum):
    GRANTED = "granted"
    PENDING = "pending"
    DENIED = "denied"
    UNKNOWN = "unknown"
    REVOKED = "revoked"


class EvidenceType(StrEnum):
    CONTRACT = "contract"
    CONSENT_FORM = "consent_form"
    LICENSE = "license"
    RELEASE = "release"
    EMAIL_CONFIRMATION = "email_confirmation"
    INTERNAL_RECORD = "internal_record"
    OTHER = "other"


class ActionType(StrEnum):
    INTERNAL_REVIEW = "internal_review"
    FESTIVAL_SUBMISSION = "festival_submission"
    PUBLIC_TRAILER = "public_trailer"
    COMMERCIAL_RELEASE = "commercial_release"
    SOCIAL_MEDIA_PUBLICATION = "social_media_publication"
    ASSET_GENERATION = "asset_generation"


class DistributionChannel(StrEnum):
    INTERNAL = "internal"
    FESTIVAL = "festival"
    THEATRICAL = "theatrical"
    STREAMING = "streaming"
    BROADCAST = "broadcast"
    SOCIAL = "social"
    ADVERTISING = "advertising"
    OTHER = "other"


class ExclusivityType(StrEnum):
    EXCLUSIVE = "exclusive"
    NON_EXCLUSIVE = "non_exclusive"
    UNKNOWN = "unknown"


class ReleaseContext(BaseModel):
    distribution_channels: list[DistributionChannel] = Field(default_factory=list, max_length=20)
    commercial_use: bool = False
    modifications_planned: bool = False
    synthetic_media_use: bool = False


class AssetDeclaration(BaseModel):
    asset_id: str = Field(min_length=2, max_length=100)
    asset_type: AssetType
    asset_name: str = Field(min_length=2, max_length=200)
    owner_or_subject: str = Field(min_length=2, max_length=200)
    ai_generated: bool = False
    subject_is_minor: bool = False
    notes: str | None = Field(default=None, max_length=1000)


class PermissionRecord(BaseModel):
    permission_id: str = Field(min_length=2, max_length=100)
    asset_id: str = Field(min_length=2, max_length=100)
    status: PermissionStatus
    allowed_uses: list[ActionType] = Field(default_factory=list, max_length=20)
    allowed_channels: list[DistributionChannel] = Field(default_factory=list, max_length=20)
    territories: list[str] = Field(default_factory=lambda: ["worldwide"], max_length=50)
    valid_from: date | None = None
    valid_until: date | None = None
    evidence_type: EvidenceType | None = None
    evidence_reference: str | None = Field(default=None, max_length=500)
    evidence_sha256: str | None = Field(default=None, pattern=r"^[a-fA-F0-9]{64}$")
    commercial_use_allowed: bool | None = None
    modification_allowed: bool | None = None
    synthetic_use_allowed: bool | None = None
    guardian_authorization: bool | None = None
    attribution_required: bool = False
    attribution_text: str | None = Field(default=None, max_length=500)
    exclusivity: ExclusivityType = ExclusivityType.UNKNOWN
    source_system: str | None = Field(default=None, max_length=160)
    notes: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def validate_record(self) -> "PermissionRecord":
        if self.valid_from and self.valid_until and self.valid_until < self.valid_from:
            raise ValueError("valid_until cannot be earlier than valid_from")
        return self


class ProductionAction(BaseModel):
    project_name: str = Field(min_length=2, max_length=160)
    action_type: ActionType
    description: str = Field(min_length=10, max_length=5000)
    intended_territories: list[str] = Field(default_factory=lambda: ["worldwide"], max_length=50)
    planned_date: date | None = None
    release_context: ReleaseContext = Field(default_factory=ReleaseContext)
    assets: list[AssetDeclaration] = Field(default_factory=list, max_length=100)
    permissions: list[PermissionRecord] = Field(default_factory=list, max_length=200)

    @model_validator(mode="after")
    def validate_references(self) -> "ProductionAction":
        asset_ids = [asset.asset_id for asset in self.assets]
        if len(asset_ids) != len(set(asset_ids)):
            raise ValueError("asset_id values must be unique")
        permission_ids = [permission.permission_id for permission in self.permissions]
        if len(permission_ids) != len(set(permission_ids)):
            raise ValueError("permission_id values must be unique")
        unknown_assets = sorted({p.asset_id for p in self.permissions} - set(asset_ids))
        if unknown_assets:
            raise ValueError(f"permissions reference unknown assets: {', '.join(unknown_assets)}")
        return self


class AssetHint(BaseModel):
    asset_type: AssetType
    phrase: str = Field(min_length=1, max_length=300)
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str = Field(min_length=1, max_length=500)


class AgentStep(BaseModel):
    name: str
    status: Literal["completed", "fallback", "failed"]
    detail: str
    agent: str = "clearance-orchestrator"
    provider: str = "local"
    duration_ms: int = Field(default=0, ge=0)
    guardrail: str | None = None


class WorkflowMetric(BaseModel):
    name: str
    value: int | float | str
    unit: str | None = None
    description: str


class RiskSignal(BaseModel):
    name: str
    score: int = Field(ge=0, le=100)
    level: Literal["low", "medium", "high"]
    rationale: str


class AgentAnalysis(BaseModel):
    mode: Literal["local", "google", "google_fallback"]
    run_id: UUID = Field(default_factory=uuid4)
    workflow_version: str = "cine-gate-agentic-workflow-0.5"
    model: str = "local-deterministic"
    total_duration_ms: int = Field(default=0, ge=0)
    fallback_used: bool = False
    boundary: str = (
        "AI agents may discover and explain possible rights issues, but the recorded outcome is "
        "produced by deterministic checks and remains subject to named human review."
    )
    asset_hints: list[AssetHint] = Field(default_factory=list)
    steps: list[AgentStep] = Field(default_factory=list)
    workflow_metrics: list[WorkflowMetric] = Field(default_factory=list)
    risk_profile: list[RiskSignal] = Field(default_factory=list)


class ClearanceFinding(BaseModel):
    code: str
    severity: Literal["info", "warning", "critical"]
    message: str
    category: str = "other"
    title: str = "Review finding"
    resolution: str = "Review and document the corrective action."
    asset_id: str | None = None
    permission_id: str | None = None


class FindingGuide(BaseModel):
    code: str
    category: str
    title: str
    resolution: str


class AssetClearanceRow(BaseModel):
    asset_id: str
    asset_name: str
    asset_type: AssetType
    status: Literal["covered", "review", "blocked"]
    matched_permission_ids: list[str] = Field(default_factory=list)
    critical_count: int = 0
    warning_count: int = 0
    required_action: str


class ReleaseReadiness(BaseModel):
    declared_assets: int
    covered_assets: int
    evidence_references: int
    evidence_fingerprints: int
    blocking_findings: int
    warning_findings: int
    asset_coverage_percent: int = Field(ge=0, le=100)
    evidence_completeness_percent: int = Field(ge=0, le=100)
    required_actions: list[str] = Field(default_factory=list)


class ClearanceReview(BaseModel):
    review_id: UUID = Field(default_factory=uuid4)
    case_id: UUID = Field(default_factory=uuid4)
    revision_number: int = Field(default=1, ge=1)
    supersedes_review_id: UUID | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    policy_version: str = "cine-gate-rights-policy-0.5"
    input_sha256: str = Field(default="0" * 64, pattern=r"^[a-f0-9]{64}$")
    action: ProductionAction
    outcome: ClearanceOutcome
    findings: list[ClearanceFinding]
    rights_matrix: list[AssetClearanceRow] = Field(default_factory=list)
    readiness: ReleaseReadiness
    coverage_score: int = Field(ge=0, le=100)
    summary: str
    recommended_next_step: str
    agent_analysis: AgentAnalysis
    human_decision: Literal["pending", "approved", "rejected"] = "pending"
    human_reviewer: str | None = None
    human_note: str | None = None
    finalized_at: datetime | None = None


class AuditEvent(BaseModel):
    event_id: UUID = Field(default_factory=uuid4)
    review_id: UUID
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    event_type: str
    actor: str
    details: dict[str, object] = Field(default_factory=dict)


class ReviewEvidenceBundle(BaseModel):
    schema_version: str = "cine-gate-evidence-v4"
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    review: ClearanceReview
    audit_events: list[AuditEvent]
    content_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    disclaimer: str = (
        "CINE-GATE records supplied metadata and workflow decisions. It does not authenticate documents, "
        "issue legal advice, or replace qualified rights-clearance review. SHA-256 values are content "
        "checksums, not digital signatures or proof of legal validity."
    )


class EvidenceVerification(BaseModel):
    review_id: UUID
    input_sha256: str
    content_sha256: str
    event_count: int
    verified_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    meaning: str = "Checksums recalculated from the stored input, review, and audit events."


class ReviewLineage(BaseModel):
    case_id: UUID
    latest_review_id: UUID
    latest_revision_number: int
    reviews: list[ClearanceReview]


class DashboardSummary(BaseModel):
    total_reviews: int
    total_cases: int = 0
    revision_reviews: int = 0
    cleared: int
    review_required: int
    blocked: int
    human_approved: int
    human_rejected: int


class SystemOptions(BaseModel):
    action_types: list[str]
    asset_types: list[str]
    distribution_channels: list[str]
    permission_statuses: list[str]
    evidence_types: list[str]
