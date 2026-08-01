import hashlib
import io
import json
import zipfile

import pytest

from app.domain.models import ProductionAction
from app.services.review_service import RevisionConflictError, ReviewService


def test_finding_catalog_endpoint(client):
    response = client.get("/api/findings/catalog")
    assert response.status_code == 200
    catalog = {item["code"]: item for item in response.json()}
    assert catalog["PERMISSION_EXPIRED"]["category"] == "time_scope"
    assert "Renew" in catalog["PERMISSION_EXPIRED"]["resolution"]


def test_findings_include_human_resolution(service: ReviewService, cleared_payload: dict):
    payload = json.loads(json.dumps(cleared_payload))
    payload["permissions"][0]["status"] = "denied"
    review = service.create(ProductionAction.model_validate(payload))
    finding = next(item for item in review.findings if item.code == "PERMISSION_DENIED_OR_REVOKED")
    assert finding.title == "Permission denied or revoked"
    assert finding.category == "permission"
    assert "new" in finding.resolution.lower()


def test_initial_review_has_case_revision_and_input_checksum(service: ReviewService, cleared_payload: dict):
    review = service.create(ProductionAction.model_validate(cleared_payload))
    assert review.revision_number == 1
    assert review.supersedes_review_id is None
    assert len(review.input_sha256) == 64
    assert str(review.case_id)


def test_create_revision_increments_and_preserves_case(service: ReviewService, cleared_payload: dict):
    first = service.create(ProductionAction.model_validate(cleared_payload))
    revised_payload = json.loads(json.dumps(cleared_payload))
    revised_payload["project_name"] = "Asteria Revised"
    second = service.create_revision(first.review_id, ProductionAction.model_validate(revised_payload))
    assert second.case_id == first.case_id
    assert second.revision_number == 2
    assert second.supersedes_review_id == first.review_id
    assert service.events(first.review_id)[-1].event_type == "REVISION_CREATED"
    assert service.events(second.review_id)[-1].event_type == "REVISION_DERIVED_FROM"


def test_revision_lineage_endpoint(client, cleared_payload):
    first = client.post("/api/reviews", json=cleared_payload).json()
    revised = json.loads(json.dumps(cleared_payload))
    revised["project_name"] = "Asteria Revision Two"
    second_response = client.post(f"/api/reviews/{first['review_id']}/revisions", json=revised)
    assert second_response.status_code == 201
    second = second_response.json()
    lineage = client.get(f"/api/reviews/{second['review_id']}/lineage").json()
    assert lineage["case_id"] == first["case_id"]
    assert lineage["latest_review_id"] == second["review_id"]
    assert [item["revision_number"] for item in lineage["reviews"]] == [1, 2]


def test_cannot_branch_from_superseded_revision(service: ReviewService, cleared_payload: dict):
    first = service.create(ProductionAction.model_validate(cleared_payload))
    action = ProductionAction.model_validate(cleared_payload)
    service.create_revision(first.review_id, action)
    with pytest.raises(RevisionConflictError):
        service.create_revision(first.review_id, action)


def test_release_package_contains_expected_files(service: ReviewService, cleared_payload: dict):
    review = service.create(ProductionAction.model_validate(cleared_payload))
    package = service.release_package(review.review_id)
    with zipfile.ZipFile(io.BytesIO(package)) as archive:
        names = set(archive.namelist())
        assert names == {
            "evidence.json",
            "release-report.html",
            "rights-matrix.csv",
            "README.txt",
            "manifest.json",
        }
        manifest = json.loads(archive.read("manifest.json"))
        assert manifest["review_id"] == str(review.review_id)
        assert manifest["revision_number"] == 1
        for name, metadata in manifest["files"].items():
            data = archive.read(name)
            assert hashlib.sha256(data).hexdigest() == metadata["sha256"]
            assert len(data) == metadata["bytes"]


def test_release_package_endpoint(client, cleared_payload):
    review = client.post("/api/reviews", json=cleared_payload).json()
    response = client.get(f"/api/reviews/{review['review_id']}/release-package")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"
    assert "attachment" in response.headers["content-disposition"]


def test_rights_matrix_csv_endpoint(client, cleared_payload):
    review = client.post("/api/reviews", json=cleared_payload).json()
    response = client.get(f"/api/reviews/{review['review_id']}/rights-matrix.csv")
    assert response.status_code == 200
    text = response.content.decode("utf-8-sig")
    assert "revision_number" in text
    assert "Lead actor likeness" in text


def test_verification_returns_input_and_content_checksums(client, cleared_payload):
    review = client.post("/api/reviews", json=cleared_payload).json()
    verification = client.get(f"/api/reviews/{review['review_id']}/evidence/verify").json()
    assert verification["input_sha256"] == review["input_sha256"]
    assert len(verification["content_sha256"]) == 64


def test_input_checksum_changes_when_action_changes(service: ReviewService, cleared_payload: dict):
    first = service.create(ProductionAction.model_validate(cleared_payload))
    changed = json.loads(json.dumps(cleared_payload))
    changed["description"] += " Additional approved end card."
    second = service.create(ProductionAction.model_validate(changed))
    assert first.input_sha256 != second.input_sha256


def test_summary_counts_cases_and_revisions(service: ReviewService, cleared_payload: dict):
    first = service.create(ProductionAction.model_validate(cleared_payload))
    service.create_revision(first.review_id, ProductionAction.model_validate(cleared_payload))
    summary = service.summary()
    assert summary.total_reviews == 2
    assert summary.total_cases == 1
    assert summary.revision_reviews == 1


def test_database_integrity_check(service: ReviewService):
    assert service.database_check().lower() == "ok"


def test_request_body_limit(client):
    oversized = "x" * 1_000_001
    response = client.post(
        "/api/reviews",
        content=oversized,
        headers={"Content-Type": "application/json", "Content-Length": str(len(oversized))},
    )
    assert response.status_code == 413


def test_report_contains_revision_and_input_checksum(service: ReviewService, cleared_payload: dict):
    review = service.create(ProductionAction.model_validate(cleared_payload))
    report = service.release_report(review.review_id)
    assert f"Revision: {review.revision_number}" in report
    assert review.input_sha256 in report
    assert str(review.case_id) in report


def test_csp_is_hardened(client):
    response = client.get("/health")
    csp = response.headers["content-security-policy"]
    assert "base-uri 'self'" in csp
    assert "form-action 'self'" in csp
