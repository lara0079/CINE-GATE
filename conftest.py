from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

os.environ["CINE_GATE_AGENT_MODE"] = "local"
os.environ["CINE_GATE_DATABASE_PATH"] = ":memory:"

from app.config import Settings  # noqa: E402
from app.main import app  # noqa: E402
from app.repositories.review_repository import SQLiteReviewRepository  # noqa: E402
from app.services.review_service import ReviewService  # noqa: E402


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        CINE_GATE_AGENT_MODE="local",
        CINE_GATE_DATABASE_PATH=str(tmp_path / "cine_gate_test.db"),
    )


@pytest.fixture
def service(settings: Settings) -> ReviewService:
    return ReviewService(settings, SQLiteReviewRepository(settings.database_path))


@pytest.fixture
def cleared_payload() -> dict:
    return {
        "project_name": "Asteria",
        "action_type": "public_trailer",
        "description": "Publish a public trailer with the lead actor likeness and licensed music.",
        "intended_territories": ["worldwide"],
        "release_context": {
            "distribution_channels": ["social"],
            "commercial_use": False,
            "modifications_planned": False,
            "synthetic_media_use": True,
        },
        "assets": [
            {
                "asset_id": "actor-1",
                "asset_type": "likeness",
                "asset_name": "Lead actor likeness",
                "owner_or_subject": "Lead actor",
                "ai_generated": True,
            },
            {
                "asset_id": "music-1",
                "asset_type": "music",
                "asset_name": "Original score",
                "owner_or_subject": "Composer",
                "ai_generated": False,
            },
        ],
        "permissions": [
            {
                "permission_id": "p-actor",
                "asset_id": "actor-1",
                "status": "granted",
                "allowed_uses": ["public_trailer"],
                "allowed_channels": ["social"],
                "territories": ["worldwide"],
                "evidence_type": "consent_form",
                "evidence_reference": "consent://actor-1",
                "evidence_sha256": "a" * 64,
                "synthetic_use_allowed": True,
            },
            {
                "permission_id": "p-music",
                "asset_id": "music-1",
                "status": "granted",
                "allowed_uses": ["public_trailer"],
                "allowed_channels": ["social"],
                "territories": ["worldwide"],
                "evidence_type": "license",
                "evidence_reference": "license://music-1",
                "evidence_sha256": "b" * 64,
            },
        ],
    }
