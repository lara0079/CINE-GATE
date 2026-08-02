from __future__ import annotations

import hashlib
import json
from time import perf_counter
from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.agents.gemini_adapter import GeminiNarrativeAdapter
from app.agents.rights_discovery import RightsDiscoveryAgent
from app.config import Settings
from app.domain.finding_catalog import FINDING_CATALOG
from app.domain.insights import build_risk_profile, build_workflow_metrics
from app.domain.models import (
    AgentStep,
    AuditEvent,
    ClearanceOutcome,
    ClearanceReview,
    DashboardSummary,
    EvidenceVerification,
    FindingGuide,
    ProductionAction,
    ReviewEvidenceBundle,
    ReviewLineage,
)
from app.domain.policy import POLICY_VERSION, evaluate_clearance
from app.domain.readiness import build_release_readiness, build_rights_matrix
from app.repositories.review_repository import ReviewNotFoundError, SQLiteReviewRepository
from app.services.reporting import (
    build_release_package,
    build_release_report,
    build_rights_matrix_csv,
)


class HumanApprovalNotAllowedError(ValueError):
    pass


class ReviewAlreadyFinalizedError(ValueError):
    pass


class DecisionNoteRequiredError(ValueError):
    pass


class RevisionConflictError(ValueError):
    pass


class ReviewService:
    def __init__(self, settings: Settings, repository: SQLiteReviewRepository | None = None) -> None:
        self.settings = settings
        self.repository = repository or SQLiteReviewRepository(settings.database_path)
        self.discovery = RightsDiscoveryAgent(settings)
        self.narrative = GeminiNarrativeAdapter(settings)

    @staticmethod
    def _input_checksum(action: ProductionAction) -> str:
        canonical = json.dumps(
            action.model_dump(mode="json"),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(canonical).hexdigest()

    def _create_review(
        self,
        action: ProductionAction,
        *,
        case_id: UUID,
        revision_number: int,
        supersedes_review_id: UUID | None,
    ) -> ClearanceReview:
        run_started = perf_counter()
        analysis = self.discovery.analyse(action)

        policy_started = perf_counter()
        outcome, findings, score = evaluate_clearance(action, agent_analysis=analysis)
        policy_duration = max(1, int((perf_counter() - policy_started) * 1000))

        matrix_started = perf_counter()
        matrix = build_rights_matrix(action, findings)
        readiness = build_release_readiness(action, findings, matrix)
        matrix_duration = max(1, int((perf_counter() - matrix_started) * 1000))

        explanation = self.narrative.explain(action, outcome, findings)
        analysis.workflow_version = self.settings.agent_workflow_version
        analysis.model = self.settings.gemini_model if analysis.mode != "local" else "local-deterministic"
        analysis.fallback_used = analysis.fallback_used or explanation.mode == "google_fallback"
        analysis.workflow_metrics = build_workflow_metrics(
            action, findings, readiness, len(analysis.asset_hints)
        )
        analysis.risk_profile = build_risk_profile(action, findings, readiness)
        analysis.steps.extend(
            [
                AgentStep(
                    name="deterministic_clearance_policy",
                    status="completed",
                    detail=f"Policy {POLICY_VERSION} produced {outcome.value} with {len(findings)} finding(s).",
                    agent="scope-controller",
                    provider="cine-gate-policy",
                    duration_ms=policy_duration,
                    guardrail="The deterministic policy is the source of the recorded outcome.",
                ),
                AgentStep(
                    name="rights_matrix_assembly",
                    status="completed",
                    detail=f"Built asset-level status for {len(matrix)} declared asset(s).",
                    agent="evidence-mapper",
                    provider="cine-gate-policy",
                    duration_ms=matrix_duration,
                    guardrail="Matrix rows reflect supplied metadata; documents are not authenticated.",
                ),
                AgentStep(
                    name="clearance_explanation",
                    status="completed" if explanation.mode in {"google", "local"} else "fallback",
                    detail=f"Explanation mode: {explanation.mode}.",
                    agent="release-brief-agent",
                    provider=explanation.provider,
                    duration_ms=explanation.duration_ms,
                    guardrail="The explanation cannot change the recorded outcome or invent permission.",
                ),
                AgentStep(
                    name="human_review_boundary",
                    status="completed",
                    detail="A named human decision remains required before the workflow is finalized.",
                    agent="human-control-plane",
                    provider="cine-gate-workflow",
                    duration_ms=0,
                    guardrail="BLOCKED records cannot be approved and REVIEW_REQUIRED approvals need a reason.",
                ),
            ]
        )
        analysis.total_duration_ms = max(1, int((perf_counter() - run_started) * 1000))
        review = ClearanceReview(
            case_id=case_id,
            revision_number=revision_number,
            supersedes_review_id=supersedes_review_id,
            policy_version=POLICY_VERSION,
            input_sha256=self._input_checksum(action),
            action=action,
            outcome=outcome,
            findings=findings,
            rights_matrix=matrix,
            readiness=readiness,
            coverage_score=score,
            summary=explanation.summary,
            recommended_next_step=explanation.recommended_next_step,
            agent_analysis=analysis,
        )
        self.repository.save(review)
        self.repository.add_event(
            AuditEvent(
                review_id=review.review_id,
                event_type="REVIEW_CREATED",
                actor="system",
                details={
                    "case_id": str(case_id),
                    "revision_number": revision_number,
                    "supersedes_review_id": str(supersedes_review_id) if supersedes_review_id else None,
                    "project_name": action.project_name,
                    "action_type": action.action_type.value,
                    "asset_count": len(action.assets),
                    "permission_count": len(action.permissions),
                    "input_sha256": review.input_sha256,
                    "agent_run_id": str(review.agent_analysis.run_id),
                    "workflow_version": review.agent_analysis.workflow_version,
                },
            )
        )
        self.repository.add_event(
            AuditEvent(
                review_id=review.review_id,
                event_type="AGENT_DISCOVERY_COMPLETED",
                actor="rights-discovery-agent",
                details={
                    "mode": analysis.mode,
                    "model": analysis.model,
                    "hint_count": len(analysis.asset_hints),
                    "fallback_used": analysis.fallback_used,
                    "total_duration_ms": analysis.total_duration_ms,
                    "run_id": str(analysis.run_id),
                },
            )
        )
        self.repository.add_event(
            AuditEvent(
                review_id=review.review_id,
                event_type="POLICY_EVALUATED",
                actor="clearance-policy",
                details={
                    "policy_version": POLICY_VERSION,
                    "outcome": outcome.value,
                    "coverage_score": score,
                    "critical_findings": readiness.blocking_findings,
                    "warning_findings": readiness.warning_findings,
                    "asset_coverage_percent": readiness.asset_coverage_percent,
                    "evidence_completeness_percent": readiness.evidence_completeness_percent,
                },
            )
        )
        return review

    def create(self, action: ProductionAction) -> ClearanceReview:
        return self._create_review(
            action,
            case_id=uuid4(),
            revision_number=1,
            supersedes_review_id=None,
        )

    def create_revision(self, review_id: UUID, action: ProductionAction) -> ClearanceReview:
        parent = self.repository.get(review_id)
        latest = self.repository.latest_for_case(parent.case_id)
        if latest.review_id != parent.review_id:
            raise RevisionConflictError(
                "A newer revision already exists for this case. Open the latest revision before creating another."
            )
        revised = self._create_review(
            action,
            case_id=parent.case_id,
            revision_number=parent.revision_number + 1,
            supersedes_review_id=parent.review_id,
        )
        self.repository.add_event(
            AuditEvent(
                review_id=parent.review_id,
                event_type="REVISION_CREATED",
                actor="system",
                details={
                    "new_review_id": str(revised.review_id),
                    "new_revision_number": revised.revision_number,
                },
            )
        )
        self.repository.add_event(
            AuditEvent(
                review_id=revised.review_id,
                event_type="REVISION_DERIVED_FROM",
                actor="system",
                details={
                    "previous_review_id": str(parent.review_id),
                    "previous_revision_number": parent.revision_number,
                    "previous_outcome": parent.outcome.value,
                },
            )
        )
        return revised

    def get(self, review_id: UUID) -> ClearanceReview:
        return self.repository.get(review_id)

    def list(
        self,
        limit: int = 100,
        outcome: ClearanceOutcome | None = None,
        query: str | None = None,
    ) -> list[ClearanceReview]:
        return self.repository.list(limit=limit, outcome=outcome, query=query)

    def summary(self) -> DashboardSummary:
        return self.repository.summary()

    def database_check(self) -> str:
        return self.repository.quick_check()

    def events(self, review_id: UUID) -> list[AuditEvent]:
        self.repository.get(review_id)
        return self.repository.list_events(review_id)

    def lineage(self, review_id: UUID) -> ReviewLineage:
        review = self.repository.get(review_id)
        reviews = self.repository.list_case(review.case_id)
        latest = reviews[-1]
        return ReviewLineage(
            case_id=review.case_id,
            latest_review_id=latest.review_id,
            latest_revision_number=latest.revision_number,
            reviews=reviews,
        )

    def finding_catalog(self) -> list[FindingGuide]:
        return [
            FindingGuide(
                code=code,
                category=definition.category,
                title=definition.title,
                resolution=definition.resolution,
            )
            for code, definition in sorted(FINDING_CATALOG.items())
        ]

    @staticmethod
    def _checksum(review: ClearanceReview, events: list[AuditEvent]) -> str:
        canonical = json.dumps(
            {
                "review": review.model_dump(mode="json"),
                "audit_events": [event.model_dump(mode="json") for event in events],
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(canonical).hexdigest()

    def evidence_bundle(self, review_id: UUID) -> ReviewEvidenceBundle:
        review = self.repository.get(review_id)
        events = self.repository.list_events(review_id)
        return ReviewEvidenceBundle(
            review=review,
            audit_events=events,
            content_sha256=self._checksum(review, events),
        )

    def verify_evidence(self, review_id: UUID) -> EvidenceVerification:
        bundle = self.evidence_bundle(review_id)
        recalculated_input = self._input_checksum(bundle.review.action)
        return EvidenceVerification(
            review_id=review_id,
            input_sha256=recalculated_input,
            content_sha256=bundle.content_sha256,
            event_count=len(bundle.audit_events),
        )

    def release_report(self, review_id: UUID) -> str:
        bundle = self.evidence_bundle(review_id)
        return build_release_report(bundle.review, bundle)

    def rights_matrix_csv(self, review_id: UUID) -> str:
        review = self.repository.get(review_id)
        return build_rights_matrix_csv(review)

    def release_package(self, review_id: UUID) -> bytes:
        bundle = self.evidence_bundle(review_id)
        return build_release_package(bundle.review, bundle)

    def finalize(
        self,
        review_id: UUID,
        decision: str,
        reviewer: str,
        note: str | None,
    ) -> ClearanceReview:
        if decision not in {"approved", "rejected"}:
            raise ValueError("decision must be approved or rejected")
        review = self.repository.get(review_id)
        if review.human_decision != "pending":
            raise ReviewAlreadyFinalizedError("review already has a final human decision")
        if review.outcome == ClearanceOutcome.BLOCKED and decision == "approved":
            raise HumanApprovalNotAllowedError(
                "A BLOCKED review cannot be approved. Correct the records and create a new revision."
            )
        if (
            review.outcome == ClearanceOutcome.REVIEW_REQUIRED
            and decision == "approved"
            and (not note or len(note.strip()) < 10)
        ):
            raise DecisionNoteRequiredError(
                "Approving a REVIEW_REQUIRED record requires a resolution note of at least 10 characters."
            )
        if decision == "rejected" and (not note or len(note.strip()) < 5):
            raise DecisionNoteRequiredError(
                "Rejecting a record requires a reason of at least 5 characters."
            )
        updated = review.model_copy(
            update={
                "human_decision": decision,
                "human_reviewer": reviewer.strip(),
                "human_note": note.strip() if note else None,
                "finalized_at": datetime.now(timezone.utc),
            }
        )
        self.repository.save(updated)
        self.repository.add_event(
            AuditEvent(
                review_id=review_id,
                event_type="HUMAN_DECISION_RECORDED",
                actor=reviewer.strip(),
                details={"decision": decision, "note": note.strip() if note else ""},
            )
        )
        return updated


__all__ = [
    "DecisionNoteRequiredError",
    "HumanApprovalNotAllowedError",
    "RevisionConflictError",
    "ReviewAlreadyFinalizedError",
    "ReviewNotFoundError",
    "ReviewService",
]
