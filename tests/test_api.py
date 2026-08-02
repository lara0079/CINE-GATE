def test_health_and_readiness(client):
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["version"] == "0.5.0"
    assert client.get("/ready").json()["status"] == "ready"


def test_security_headers_and_request_id(client):
    response = client.get("/health", headers={"X-Request-ID": "case-123"})
    assert response.headers["x-request-id"] == "case-123"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"


def test_options_endpoint(client):
    body = client.get("/api/options").json()
    assert "public_trailer" in body["action_types"]
    assert "streaming" in body["distribution_channels"]
    assert "likeness" in body["asset_types"]


def test_create_review_and_summary(client, cleared_payload):
    response = client.post("/api/reviews", json=cleared_payload)
    assert response.status_code == 201
    body = response.json()
    assert body["outcome"] == "CLEARED"
    assert body["coverage_score"] == 100
    assert body["readiness"]["asset_coverage_percent"] == 100
    assert len(body["rights_matrix"]) == 2
    summary = client.get("/api/reviews/summary").json()
    assert summary["total_reviews"] >= 1


def test_evidence_download_and_verification(client, cleared_payload):
    review = client.post("/api/reviews", json=cleared_payload).json()
    response = client.get(f"/api/reviews/{review['review_id']}/evidence/download")
    assert response.status_code == 200
    assert "attachment" in response.headers["content-disposition"]
    body = response.json()
    assert body["schema_version"] == "cine-gate-evidence-v4"
    assert len(body["content_sha256"]) == 64
    verification = client.get(
        f"/api/reviews/{review['review_id']}/evidence/verify"
    ).json()
    assert verification["content_sha256"] == body["content_sha256"]
    assert verification["event_count"] == 3


def test_release_report(client, cleared_payload):
    review = client.post("/api/reviews", json=cleared_payload).json()
    response = client.get(f"/api/reviews/{review['review_id']}/report")
    assert response.status_code == 200
    assert "CINE-GATE" in response.text
    assert "Rights matrix" in response.text
    assert review["review_id"] in response.text


def test_human_decision_endpoint(client, cleared_payload):
    review = client.post("/api/reviews", json=cleared_payload).json()
    response = client.post(
        f"/api/reviews/{review['review_id']}/human-decision",
        json={"decision": "approved", "reviewer": "Rights Officer", "note": "Record checked"},
    )
    assert response.status_code == 200
    assert response.json()["human_decision"] == "approved"


def test_review_filtering(client, cleared_payload):
    client.post("/api/reviews", json=cleared_payload)
    blocked = dict(cleared_payload)
    blocked["project_name"] = "Blocked Orion"
    blocked["permissions"] = [dict(item) for item in cleared_payload["permissions"]]
    blocked["permissions"][0]["status"] = "denied"
    client.post("/api/reviews", json=blocked)
    filtered = client.get("/api/reviews?outcome=BLOCKED&q=orion").json()
    assert len(filtered) == 1
    assert filtered[0]["action"]["project_name"] == "Blocked Orion"


def test_unknown_review_returns_404(client):
    review_id = "00000000-0000-0000-0000-000000000001"
    assert client.get(f"/api/reviews/{review_id}").status_code == 404
    assert client.get(f"/api/reviews/{review_id}/report").status_code == 404
