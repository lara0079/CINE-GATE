from pathlib import Path

from app.domain.insights import build_risk_profile, build_workflow_metrics
from app.domain.models import ProductionAction
from app.domain.policy import evaluate_clearance
from app.domain.readiness import build_release_readiness, build_rights_matrix


def test_capabilities_expose_bounded_agent_layers(client):
    response = client.get('/api/system/capabilities')
    assert response.status_code == 200
    body = response.json()
    assert body['version'] == '0.5.0'
    assert len(body['runtime_layers']) == 5
    assert any('cannot establish' in item for item in body['guardrails'])


def test_security_and_timing_headers(client):
    response = client.get('/health')
    assert response.headers['cross-origin-opener-policy'] == 'same-origin'
    assert response.headers['cross-origin-resource-policy'] == 'same-origin'
    assert response.headers['server-timing'].startswith('app;dur=')


def test_agent_run_contains_metrics_and_risk_profile(client, cleared_payload):
    response = client.post('/api/reviews', json=cleared_payload)
    assert response.status_code == 201
    analysis = response.json()['agent_analysis']
    assert analysis['workflow_version'] == 'cine-gate-agentic-workflow-0.5'
    assert analysis['run_id']
    assert analysis['total_duration_ms'] >= 1
    assert len(analysis['workflow_metrics']) == 6
    assert len(analysis['risk_profile']) == 5
    assert any(step['agent'] == 'scope-controller' for step in analysis['steps'])
    assert all('provider' in step and 'duration_ms' in step for step in analysis['steps'])


def test_risk_profile_is_transparent_not_decision_score(cleared_payload):
    action = ProductionAction.model_validate(cleared_payload)
    outcome, findings, _ = evaluate_clearance(action)
    matrix = build_rights_matrix(action, findings)
    readiness = build_release_readiness(action, findings, matrix)
    signals = build_risk_profile(action, findings, readiness)
    assert outcome.value == 'CLEARED'
    assert {signal.name for signal in signals} == {
        'Rights coverage', 'Evidence completeness', 'Scope alignment',
        'Temporal validity', 'Synthetic-media exposure'
    }
    assert all(0 <= signal.score <= 100 for signal in signals)


def test_workflow_metrics_report_observed_counts(cleared_payload):
    action = ProductionAction.model_validate(cleared_payload)
    _, findings, _ = evaluate_clearance(action)
    matrix = build_rights_matrix(action, findings)
    readiness = build_release_readiness(action, findings, matrix)
    metrics = build_workflow_metrics(action, findings, readiness, hint_count=2)
    values = {metric.name: metric.value for metric in metrics}
    assert values['Declared assets'] == 2
    assert values['Permission records'] == 2
    assert values['Agent discoveries'] == 2


def test_competition_files_and_ip_guard_exist():
    root = Path(__file__).parents[1]
    assert (root / 'AGENTS.md').exists()
    assert (root / '.bobignore').exists()
    agent_source = (root / 'deployment/agent_engine/cine_gate_agent/agent.py').read_text()
    assert 'ParallelAgent' in agent_source
    assert 'SequentialAgent' in agent_source
    assert 'state_final_boundary' in agent_source
    bobignore = (root / '.bobignore').read_text()
    assert '*BACKUP*' in bobignore
    assert '.env' in bobignore


def test_ui_contains_agent_observability():
    root = Path(__file__).parents[1]
    html = (root / 'app/static/index.html').read_text()
    js = (root / 'app/static/app.js').read_text()
    assert 'Agent system' in html
    assert 'Release risk profile' in js
    assert 'Agent run trace' in js
    assert 'workflowMetrics' in js
