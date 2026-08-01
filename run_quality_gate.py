from __future__ import annotations

import copy
import json
import os
import tempfile
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

os.environ.setdefault("CINE_GATE_AGENT_MODE", "local")

from app.config import Settings
from app.domain.models import ProductionAction
from app.repositories.review_repository import SQLiteReviewRepository
from app.services.review_service import ReviewService


def base_payload() -> dict:
    return {
        "project_name": "Asteria",
        "action_type": "public_trailer",
        "description": "Publish a public trailer with actor likeness, cloned voice, and licensed music.",
        "intended_territories": ["worldwide"],
        "release_context": {
            "distribution_channels": ["social"],
            "commercial_use": False,
            "modifications_planned": False,
            "synthetic_media_use": True,
        },
        "assets": [
            {"asset_id": "actor", "asset_type": "likeness", "asset_name": "Lead likeness", "owner_or_subject": "Lead performer", "ai_generated": True},
            {"asset_id": "voice", "asset_type": "voice", "asset_name": "Synthetic narration", "owner_or_subject": "Lead performer", "ai_generated": True},
            {"asset_id": "music", "asset_type": "music", "asset_name": "Original score", "owner_or_subject": "Composer"},
        ],
        "permissions": [
            {"permission_id": "p-actor", "asset_id": "actor", "status": "granted", "allowed_uses": ["public_trailer"], "allowed_channels": ["social"], "territories": ["worldwide"], "evidence_type": "consent_form", "evidence_reference": "consent://actor", "evidence_sha256": "a" * 64, "synthetic_use_allowed": True},
            {"permission_id": "p-voice", "asset_id": "voice", "status": "granted", "allowed_uses": ["public_trailer"], "allowed_channels": ["social"], "territories": ["worldwide"], "evidence_type": "consent_form", "evidence_reference": "consent://voice", "evidence_sha256": "b" * 64, "synthetic_use_allowed": True},
            {"permission_id": "p-music", "asset_id": "music", "status": "granted", "allowed_uses": ["public_trailer"], "allowed_channels": ["social"], "territories": ["worldwide"], "evidence_type": "license", "evidence_reference": "license://music", "evidence_sha256": "c" * 64},
        ],
    }


def cases() -> list[tuple[str, str, dict]]:
    base = base_payload()
    result: list[tuple[str, str, dict]] = [("complete synthetic trailer", "CLEARED", base)]

    missing = copy.deepcopy(base)
    missing["permissions"] = missing["permissions"][:-1]
    result.append(("missing music permission", "BLOCKED", missing))

    pending = copy.deepcopy(base)
    pending["permissions"][2]["status"] = "pending"
    result.append(("pending score license", "REVIEW_REQUIRED", pending))

    synthetic_gap = copy.deepcopy(base)
    synthetic_gap["permissions"][1]["synthetic_use_allowed"] = None
    result.append(("voice-clone scope absent", "BLOCKED", synthetic_gap))

    channel = copy.deepcopy(base)
    channel["release_context"]["distribution_channels"] = ["streaming"]
    result.append(("streaming outside scope", "BLOCKED", channel))

    evidence = copy.deepcopy(base)
    evidence["permissions"][2]["evidence_sha256"] = None
    result.append(("license fingerprint absent but reference present", "CLEARED", evidence))

    undeclared = copy.deepcopy(base)
    undeclared["description"] += " It also contains archival footage."
    result.append(("undeclared archival footage", "REVIEW_REQUIRED", undeclared))

    commercial = copy.deepcopy(base)
    commercial["release_context"]["commercial_use"] = True
    for record in commercial["permissions"]:
        record["commercial_use_allowed"] = True
    commercial["permissions"][2]["commercial_use_allowed"] = False
    result.append(("commercial score restriction", "BLOCKED", commercial))
    return result


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        settings = Settings(CINE_GATE_AGENT_MODE="local", CINE_GATE_DATABASE_PATH=str(Path(tmp) / "quality.db"))
        service = ReviewService(settings, SQLiteReviewRepository(settings.database_path))
        rows = []
        failures = 0
        for name, expected, payload in cases():
            review = service.create(ProductionAction.model_validate(payload))
            passed = review.outcome.value == expected
            failures += int(not passed)
            rows.append({"case": name, "expected": expected, "actual": review.outcome.value, "passed": passed})
        print(json.dumps({"quality_gate": "passed" if failures == 0 else "failed", "cases": rows}, indent=2))
        return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
