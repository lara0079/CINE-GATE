from datetime import date, timedelta

from app.agents.rights_discovery import RightsDiscoveryAgent
from app.config import Settings
from app.domain.models import ClearanceOutcome, ProductionAction
from app.domain.policy import evaluate_clearance


def make_action(**changes) -> ProductionAction:
    payload = {
        "project_name": "Asteria",
        "action_type": "public_trailer",
        "description": "Publish a trailer containing an actor likeness and licensed music.",
        "intended_territories": ["Greece"],
        "planned_date": date.today(),
        "release_context": {
            "distribution_channels": ["social"],
            "commercial_use": False,
            "modifications_planned": False,
            "synthetic_media_use": True,
        },
        "assets": [
            {
                "asset_id": "a1",
                "asset_type": "likeness",
                "asset_name": "Actor likeness",
                "owner_or_subject": "Actor",
                "ai_generated": True,
            },
            {
                "asset_id": "a2",
                "asset_type": "music",
                "asset_name": "Score",
                "owner_or_subject": "Composer",
            },
        ],
        "permissions": [
            {
                "permission_id": "p1",
                "asset_id": "a1",
                "status": "granted",
                "allowed_uses": ["public_trailer"],
                "allowed_channels": ["social"],
                "territories": ["worldwide"],
                "evidence_type": "consent_form",
                "evidence_reference": "consent://p1",
                "evidence_sha256": "a" * 64,
                "synthetic_use_allowed": True,
            },
            {
                "permission_id": "p2",
                "asset_id": "a2",
                "status": "granted",
                "allowed_uses": ["public_trailer"],
                "allowed_channels": ["social"],
                "territories": ["Greece"],
                "evidence_type": "license",
                "evidence_reference": "license://p2",
                "evidence_sha256": "b" * 64,
            },
        ],
    }
    payload.update(changes)
    return ProductionAction.model_validate(payload)


def test_complete_record_clears():
    action = make_action()
    analysis = RightsDiscoveryAgent(Settings(CINE_GATE_AGENT_MODE="local")).analyse(action)
    outcome, findings, score = evaluate_clearance(action, analysis)
    assert outcome == ClearanceOutcome.CLEARED
    assert score == 100
    assert any(f.code == "RECORDED_PERMISSIONS_APPEAR_SUFFICIENT" for f in findings)


def test_missing_asset_permission_blocks():
    action = make_action(permissions=[make_action().permissions[0].model_dump()])
    outcome, findings, _ = evaluate_clearance(action)
    assert outcome == ClearanceOutcome.BLOCKED
    assert any(f.code == "ASSET_WITHOUT_PERMISSION_RECORD" and f.asset_id == "a2" for f in findings)


def test_expired_permission_blocks_on_planned_date():
    payload = make_action().model_dump(mode="json")
    payload["permissions"][0]["valid_until"] = (date.today() - timedelta(days=1)).isoformat()
    outcome, findings, _ = evaluate_clearance(ProductionAction.model_validate(payload))
    assert outcome == ClearanceOutcome.BLOCKED
    assert any(f.code == "PERMISSION_EXPIRED" for f in findings)


def test_territory_mismatch_blocks():
    payload = make_action().model_dump(mode="json")
    payload["permissions"][1]["territories"] = ["France"]
    outcome, findings, _ = evaluate_clearance(ProductionAction.model_validate(payload))
    assert outcome == ClearanceOutcome.BLOCKED
    assert any(f.code == "TERRITORY_OUTSIDE_PERMISSION_SCOPE" for f in findings)


def test_pending_record_requires_human_review():
    payload = make_action().model_dump(mode="json")
    payload["permissions"][1]["status"] = "pending"
    outcome, findings, _ = evaluate_clearance(ProductionAction.model_validate(payload))
    assert outcome == ClearanceOutcome.REVIEW_REQUIRED
    assert any(f.code == "PERMISSION_UNRESOLVED" for f in findings)


def test_ai_likeness_requires_explicit_evidence():
    payload = make_action().model_dump(mode="json")
    payload["permissions"][0]["evidence_reference"] = None
    payload["permissions"][0]["evidence_type"] = None
    outcome, findings, _ = evaluate_clearance(ProductionAction.model_validate(payload))
    assert outcome == ClearanceOutcome.BLOCKED
    assert any(f.code == "SYNTHETIC_PERSONA_EXPLICIT_EVIDENCE_REQUIRED" for f in findings)


def test_ai_likeness_requires_explicit_synthetic_scope():
    payload = make_action().model_dump(mode="json")
    payload["permissions"][0]["synthetic_use_allowed"] = None
    outcome, findings, _ = evaluate_clearance(ProductionAction.model_validate(payload))
    assert outcome == ClearanceOutcome.BLOCKED
    assert any(f.code == "SYNTHETIC_USE_SCOPE_NOT_EXPLICIT" for f in findings)


def test_agent_flags_undeclared_voice_as_review():
    action = make_action(
        description="Publish a trailer with an actor likeness, music, and cloned voice narration."
    )
    analysis = RightsDiscoveryAgent(Settings(CINE_GATE_AGENT_MODE="local")).analyse(action)
    outcome, findings, _ = evaluate_clearance(action, analysis)
    assert outcome == ClearanceOutcome.REVIEW_REQUIRED
    assert any(f.code == "POSSIBLE_UNDECLARED_ASSET" and "voice" in f.message for f in findings)


def test_conflicting_grant_and_revocation_blocks():
    payload = make_action().model_dump(mode="json")
    payload["permissions"].append(
        {
            "permission_id": "p1-revoked",
            "asset_id": "a1",
            "status": "revoked",
            "allowed_uses": ["public_trailer"],
            "allowed_channels": ["social"],
            "territories": ["worldwide"],
            "evidence_type": "internal_record",
            "evidence_reference": "revocation://a1",
        }
    )
    outcome, findings, _ = evaluate_clearance(ProductionAction.model_validate(payload))
    assert outcome == ClearanceOutcome.BLOCKED
    assert any(f.code == "CONFLICTING_PERMISSION_RECORDS" for f in findings)


def test_channel_mismatch_blocks():
    payload = make_action().model_dump(mode="json")
    payload["release_context"]["distribution_channels"] = ["streaming"]
    outcome, findings, _ = evaluate_clearance(ProductionAction.model_validate(payload))
    assert outcome == ClearanceOutcome.BLOCKED
    assert any(f.code == "CHANNEL_OUTSIDE_PERMISSION_SCOPE" for f in findings)


def test_missing_channel_scope_requires_review():
    payload = make_action().model_dump(mode="json")
    payload["permissions"][1]["allowed_channels"] = []
    outcome, findings, _ = evaluate_clearance(ProductionAction.model_validate(payload))
    assert outcome == ClearanceOutcome.REVIEW_REQUIRED
    assert any(f.code == "CHANNEL_SCOPE_NOT_RECORDED" for f in findings)


def test_commercial_use_denial_blocks():
    payload = make_action().model_dump(mode="json")
    payload["release_context"]["commercial_use"] = True
    for permission in payload["permissions"]:
        permission["commercial_use_allowed"] = True
    payload["permissions"][1]["commercial_use_allowed"] = False
    outcome, findings, _ = evaluate_clearance(ProductionAction.model_validate(payload))
    assert outcome == ClearanceOutcome.BLOCKED
    assert any(f.code == "COMMERCIAL_USE_NOT_ALLOWED" for f in findings)


def test_modification_unknown_requires_review():
    payload = make_action().model_dump(mode="json")
    payload["release_context"]["modifications_planned"] = True
    for permission in payload["permissions"]:
        permission["modification_allowed"] = True
    payload["permissions"][1]["modification_allowed"] = None
    outcome, findings, _ = evaluate_clearance(ProductionAction.model_validate(payload))
    assert outcome == ClearanceOutcome.REVIEW_REQUIRED
    assert any(f.code == "MODIFICATION_SCOPE_UNKNOWN" for f in findings)


def test_minor_requires_guardian_authorization():
    payload = make_action().model_dump(mode="json")
    payload["assets"][0]["subject_is_minor"] = True
    payload["permissions"][0]["guardian_authorization"] = None
    outcome, findings, _ = evaluate_clearance(ProductionAction.model_validate(payload))
    assert outcome == ClearanceOutcome.BLOCKED
    assert any(f.code == "GUARDIAN_AUTHORIZATION_REQUIRED" for f in findings)


def test_attribution_text_gap_requires_review():
    payload = make_action().model_dump(mode="json")
    payload["permissions"][1]["attribution_required"] = True
    payload["permissions"][1]["attribution_text"] = None
    outcome, findings, _ = evaluate_clearance(ProductionAction.model_validate(payload))
    assert outcome == ClearanceOutcome.REVIEW_REQUIRED
    assert any(f.code == "ATTRIBUTION_TEXT_MISSING" for f in findings)
