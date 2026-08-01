import pytest

from app.domain.models import ClearanceOutcome, ProductionAction
from app.repositories.review_repository import SQLiteReviewRepository
from app.services.review_service import (
    DecisionNoteRequiredError,
    HumanApprovalNotAllowedError,
    ReviewAlreadyFinalizedError,
    ReviewService,
)


def test_service_persists_and_exports(service: ReviewService, cleared_payload: dict):
    review = service.create(ProductionAction.model_validate(cleared_payload))
    loaded = service.get(review.review_id)
    assert loaded.review_id == review.review_id
    assert loaded.rights_matrix[0].status == "covered"
    assert loaded.readiness.evidence_completeness_percent == 100
    events = service.events(review.review_id)
    assert [event.event_type for event in events] == [
        "REVIEW_CREATED",
        "AGENT_DISCOVERY_COMPLETED",
        "POLICY_EVALUATED",
    ]
    bundle = service.evidence_bundle(review.review_id)
    assert bundle.review.review_id == review.review_id
    assert bundle.schema_version == "cine-gate-evidence-v4"
    assert len(bundle.content_sha256) == 64


def test_checksum_is_stable_until_record_changes(service: ReviewService, cleared_payload: dict):
    review = service.create(ProductionAction.model_validate(cleared_payload))
    first = service.verify_evidence(review.review_id).content_sha256
    second = service.verify_evidence(review.review_id).content_sha256
    assert first == second
    service.finalize(review.review_id, "approved", "Rights Officer", "Record checked")
    third = service.verify_evidence(review.review_id).content_sha256
    assert third != first


def test_release_report_contains_review(service: ReviewService, cleared_payload: dict):
    review = service.create(ProductionAction.model_validate(cleared_payload))
    html = service.release_report(review.review_id)
    assert "Rights matrix" in html
    assert str(review.review_id) in html
    assert "Asteria" in html


def test_repository_survives_new_service_instance(settings, cleared_payload):
    first = ReviewService(settings, SQLiteReviewRepository(settings.database_path))
    review = first.create(ProductionAction.model_validate(cleared_payload))
    second = ReviewService(settings, SQLiteReviewRepository(settings.database_path))
    assert second.get(review.review_id).review_id == review.review_id


def test_blocked_review_cannot_be_approved(service: ReviewService, cleared_payload: dict):
    cleared_payload["permissions"][0]["status"] = "denied"
    review = service.create(ProductionAction.model_validate(cleared_payload))
    with pytest.raises(HumanApprovalNotAllowedError):
        service.finalize(review.review_id, "approved", "Reviewer", "Cannot override")


def test_human_rejection_is_audited(service: ReviewService, cleared_payload: dict):
    review = service.create(ProductionAction.model_validate(cleared_payload))
    updated = service.finalize(review.review_id, "rejected", "Rights Officer", "Needs new release")
    assert updated.human_decision == "rejected"
    assert service.events(review.review_id)[-1].event_type == "HUMAN_DECISION_RECORDED"


def test_rejection_needs_reason(service: ReviewService, cleared_payload: dict):
    review = service.create(ProductionAction.model_validate(cleared_payload))
    with pytest.raises(DecisionNoteRequiredError):
        service.finalize(review.review_id, "rejected", "Rights Officer", "no")


def test_review_required_approval_needs_resolution_note(service: ReviewService, cleared_payload: dict):
    cleared_payload["permissions"][1]["status"] = "pending"
    review = service.create(ProductionAction.model_validate(cleared_payload))
    with pytest.raises(DecisionNoteRequiredError):
        service.finalize(review.review_id, "approved", "Rights Officer", "ok")
    approved = service.finalize(
        review.review_id,
        "approved",
        "Rights Officer",
        "Permission was obtained and independently checked before approval.",
    )
    assert approved.human_decision == "approved"


def test_review_cannot_be_finalized_twice(service: ReviewService, cleared_payload: dict):
    review = service.create(ProductionAction.model_validate(cleared_payload))
    service.finalize(review.review_id, "approved", "Rights Officer", "Record checked")
    with pytest.raises(ReviewAlreadyFinalizedError):
        service.finalize(review.review_id, "rejected", "Rights Officer", "Changed decision")


def test_repository_filters(service: ReviewService, cleared_payload: dict):
    service.create(ProductionAction.model_validate(cleared_payload))
    blocked = {**cleared_payload, "project_name": "Orion Blocked"}
    blocked["permissions"] = [dict(item) for item in cleared_payload["permissions"]]
    blocked["permissions"][0]["status"] = "denied"
    service.create(ProductionAction.model_validate(blocked))
    matches = service.list(outcome=ClearanceOutcome.BLOCKED, query="orion")
    assert len(matches) == 1
