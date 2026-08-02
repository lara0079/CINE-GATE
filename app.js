const form = document.getElementById('review-form');
const result = document.getElementById('result');
const assetList = document.getElementById('asset-list');
const assetTemplate = document.getElementById('asset-template');
const appStatus = document.getElementById('app-status');
let assetCounter = 0;
let activeReviewId = null;
let activeRevisionSourceId = null;

const FAKE_SHA_A = 'a'.repeat(64);
const FAKE_SHA_B = 'b'.repeat(64);

const scenarios = {
  cleared: {
    project: 'Asteria', action: 'public_trailer',
    description: "Publish a public trailer containing the lead performer's consented digital likeness and a licensed original score.",
    territories: 'worldwide', channels: ['social'], commercial: false, modifications: false, synthetic: true,
    assets: [
      {type:'likeness', name:'Lead performer digital likeness', owner:'Lead performer', ai:true, minor:false, status:'granted', evidenceType:'consent_form', evidence:'consent://asteria/performer-001', sha:FAKE_SHA_A, channels:['social'], commercial:true, modification:true, synthetic:true, guardian:null, source:'Production consent register'},
      {type:'music', name:'Original trailer score', owner:'Asteria composer', ai:false, minor:false, status:'granted', evidenceType:'license', evidence:'license://asteria/music-014', sha:FAKE_SHA_B, channels:['social'], commercial:true, modification:true, synthetic:null, guardian:null, source:'Music rights register', attribution:true, attributionText:'Music composed by Asteria Studio'}
    ]
  },
  review: {
    project: 'Asteria Festival Cut', action: 'festival_submission',
    description: 'Submit a festival cut containing archive footage and a closing song for which the clearance request remains pending.',
    territories: 'Germany, France', channels: ['festival'], commercial: false, modifications: true, synthetic: false,
    assets: [
      {type:'footage', name:'Historic city archive clip', owner:'City archive', ai:false, minor:false, status:'granted', evidenceType:'license', evidence:'license://archive/882', channels:['festival'], commercial:false, modification:null, synthetic:null, guardian:null},
      {type:'music', name:'Festival cut closing song', owner:'Independent artist', ai:false, minor:false, status:'pending', evidenceType:'email_confirmation', evidence:'request://music/193', channels:['festival'], commercial:null, modification:null, synthetic:null, guardian:null}
    ]
  },
  blocked: {
    project: 'Asteria International Trailer', action: 'public_trailer',
    description: "Release an international trailer using the lead performer's digital likeness after the recorded consent has expired.",
    territories: 'worldwide', channels: ['social','advertising'], commercial: true, modifications: true, synthetic: true,
    assets: [
      {type:'likeness', name:'Lead performer digital likeness', owner:'Lead performer', ai:true, minor:false, status:'granted', evidenceType:'consent_form', evidence:'consent://expired/001', channels:['social','advertising'], commercial:true, modification:true, synthetic:true, guardian:null, until:'2025-01-01'}
    ]
  },
  synthetic: {
    project: 'Orion Teaser', action: 'social_media_publication',
    description: 'Publish a social teaser with cloned voice narration and licensed artwork.',
    territories: 'Greece', channels: ['social'], commercial: true, modifications: true, synthetic: true,
    assets: [
      {type:'voice', name:'Cloned narrator voice', owner:'Narrator', ai:true, minor:false, status:'granted', evidenceType:'release', evidence:'release://voice/014', channels:['social'], commercial:true, modification:true, synthetic:null, guardian:null},
      {type:'artwork', name:'Campaign key art', owner:'Visual artist', ai:false, minor:false, status:'granted', evidenceType:'license', evidence:'license://art/901', channels:['social'], commercial:true, modification:false, synthetic:null, guardian:null}
    ]
  }
};

function announce(message) {
  appStatus.textContent = '';
  window.setTimeout(() => { appStatus.textContent = message; }, 20);
}

function splitList(value) {
  return value.split(',').map(item => item.trim()).filter(Boolean);
}

function triState(value) {
  if (value === 'true') return true;
  if (value === 'false') return false;
  return null;
}

function setTri(select, value) {
  select.value = value === true ? 'true' : value === false ? 'false' : 'null';
}

function selectedChecks(container) {
  return [...container.querySelectorAll('input[type="checkbox"]:checked')].map(item => item.value);
}

function setChecks(container, values) {
  const selected = new Set(values || []);
  container.querySelectorAll('input[type="checkbox"]').forEach(item => {
    item.checked = selected.has(item.value);
  });
}

function addAsset(data = {}) {
  assetCounter += 1;
  const fragment = assetTemplate.content.cloneNode(true);
  const card = fragment.querySelector('.asset-card');
  card.querySelector('.asset-number').textContent = assetCounter;
  card.querySelector('.asset-type').value = data.type || 'likeness';
  card.querySelector('.asset-name').value = data.name || '';
  card.querySelector('.asset-owner').value = data.owner || '';
  card.querySelector('.ai-generated').checked = Boolean(data.ai);
  card.querySelector('.subject-minor').checked = Boolean(data.minor);
  card.querySelector('.permission-status').value = data.status || 'granted';
  card.querySelector('.evidence-type').value = data.evidenceType === undefined ? 'consent_form' : (data.evidenceType || '');
  card.querySelector('.permission-territories').value = data.territories || document.getElementById('territories').value || 'worldwide';
  card.querySelector('.valid-from').value = data.from || '';
  card.querySelector('.valid-until').value = data.until || '';
  card.querySelector('.evidence-reference').value = data.evidence || '';
  card.querySelector('.evidence-sha').value = data.sha || '';
  setChecks(card.querySelector('.permission-channels'), data.channels || selectedChecks(document.getElementById('release-channels')));
  setTri(card.querySelector('.commercial-allowed'), data.commercial);
  setTri(card.querySelector('.modification-allowed'), data.modification);
  setTri(card.querySelector('.synthetic-allowed'), data.synthetic);
  setTri(card.querySelector('.guardian-authorization'), data.guardian);
  card.querySelector('.exclusivity').value = data.exclusivity || 'unknown';
  card.querySelector('.source-system').value = data.source || '';
  card.querySelector('.attribution-required').checked = Boolean(data.attribution);
  card.querySelector('.attribution-text').value = data.attributionText || '';
  card.querySelector('.remove-asset').addEventListener('click', () => {
    card.remove();
    renumberAssets();
  });
  assetList.appendChild(fragment);
}

function renumberAssets() {
  [...assetList.querySelectorAll('.asset-card')].forEach((card, index) => {
    card.querySelector('.asset-number').textContent = index + 1;
  });
  assetCounter = assetList.querySelectorAll('.asset-card').length;
}

function clearAssets() {
  assetList.innerHTML = '';
  assetCounter = 0;
}

function clearRevisionMode() {
  activeRevisionSourceId = null;
  document.getElementById('revision-banner').classList.add('hidden');
  document.getElementById('revision-banner-text').textContent = '';
  document.getElementById('form-title').textContent = 'Review production rights';
  document.getElementById('submit-review').textContent = 'Run agentic clearance review';
}

function loadScenario(name) {
  clearRevisionMode();
  const scenario = scenarios[name];
  document.getElementById('project_name').value = scenario.project;
  document.getElementById('action_type').value = scenario.action;
  document.getElementById('description').value = scenario.description;
  document.getElementById('territories').value = scenario.territories;
  document.getElementById('planned_date').value = '';
  setChecks(document.getElementById('release-channels'), scenario.channels);
  document.getElementById('commercial_use').checked = scenario.commercial;
  document.getElementById('modifications_planned').checked = scenario.modifications;
  document.getElementById('synthetic_media_use').checked = scenario.synthetic;
  clearAssets();
  scenario.assets.forEach(addAsset);
  result.classList.add('hidden');
  announce(`${name} scenario loaded`);
}

function buildPayload() {
  const actionType = document.getElementById('action_type').value;
  const assets = [];
  const permissions = [];
  [...assetList.querySelectorAll('.asset-card')].forEach((card, index) => {
    const assetId = `asset-${index + 1}`;
    assets.push({
      asset_id: assetId,
      asset_type: card.querySelector('.asset-type').value,
      asset_name: card.querySelector('.asset-name').value,
      owner_or_subject: card.querySelector('.asset-owner').value,
      ai_generated: card.querySelector('.ai-generated').checked,
      subject_is_minor: card.querySelector('.subject-minor').checked
    });
    permissions.push({
      permission_id: `permission-${index + 1}`,
      asset_id: assetId,
      status: card.querySelector('.permission-status').value,
      allowed_uses: [actionType],
      allowed_channels: selectedChecks(card.querySelector('.permission-channels')),
      territories: splitList(card.querySelector('.permission-territories').value || 'worldwide'),
      valid_from: card.querySelector('.valid-from').value || null,
      valid_until: card.querySelector('.valid-until').value || null,
      evidence_type: card.querySelector('.evidence-type').value || null,
      evidence_reference: card.querySelector('.evidence-reference').value || null,
      evidence_sha256: card.querySelector('.evidence-sha').value.trim() || null,
      commercial_use_allowed: triState(card.querySelector('.commercial-allowed').value),
      modification_allowed: triState(card.querySelector('.modification-allowed').value),
      synthetic_use_allowed: triState(card.querySelector('.synthetic-allowed').value),
      guardian_authorization: triState(card.querySelector('.guardian-authorization').value),
      attribution_required: card.querySelector('.attribution-required').checked,
      attribution_text: card.querySelector('.attribution-text').value || null,
      exclusivity: card.querySelector('.exclusivity').value,
      source_system: card.querySelector('.source-system').value || null
    });
  });
  return {
    project_name: document.getElementById('project_name').value,
    action_type: actionType,
    description: document.getElementById('description').value,
    planned_date: document.getElementById('planned_date').value || null,
    intended_territories: splitList(document.getElementById('territories').value || 'worldwide'),
    release_context: {
      distribution_channels: selectedChecks(document.getElementById('release-channels')),
      commercial_use: document.getElementById('commercial_use').checked,
      modifications_planned: document.getElementById('modifications_planned').checked,
      synthetic_media_use: document.getElementById('synthetic_media_use').checked
    },
    assets,
    permissions
  };
}

function loadActionIntoForm(action) {
  document.getElementById('project_name').value = action.project_name;
  document.getElementById('action_type').value = action.action_type;
  document.getElementById('description').value = action.description;
  document.getElementById('planned_date').value = action.planned_date || '';
  document.getElementById('territories').value = (action.intended_territories || []).join(', ');
  setChecks(document.getElementById('release-channels'), action.release_context.distribution_channels || []);
  document.getElementById('commercial_use').checked = Boolean(action.release_context.commercial_use);
  document.getElementById('modifications_planned').checked = Boolean(action.release_context.modifications_planned);
  document.getElementById('synthetic_media_use').checked = Boolean(action.release_context.synthetic_media_use);
  clearAssets();
  action.assets.forEach(asset => {
    const permission = action.permissions.find(item => item.asset_id === asset.asset_id) || {};
    addAsset({
      type: asset.asset_type,
      name: asset.asset_name,
      owner: asset.owner_or_subject,
      ai: asset.ai_generated,
      minor: asset.subject_is_minor,
      status: permission.status || 'unknown',
      evidenceType: permission.evidence_type,
      evidence: permission.evidence_reference,
      sha: permission.evidence_sha256,
      territories: (permission.territories || ['worldwide']).join(', '),
      channels: permission.allowed_channels || [],
      commercial: permission.commercial_use_allowed,
      modification: permission.modification_allowed,
      synthetic: permission.synthetic_use_allowed,
      guardian: permission.guardian_authorization,
      attribution: permission.attribution_required,
      attributionText: permission.attribution_text,
      exclusivity: permission.exclusivity,
      source: permission.source_system,
      from: permission.valid_from,
      until: permission.valid_until
    });
  });
}

function enterRevisionMode(review) {
  activeRevisionSourceId = review.review_id;
  loadActionIntoForm(review.action);
  const banner = document.getElementById('revision-banner');
  banner.classList.remove('hidden');
  document.getElementById('revision-banner-text').textContent = `Case ${review.case_id} · creating revision ${review.revision_number + 1} from review ${review.review_id}`;
  document.getElementById('form-title').textContent = 'Create a corrected review revision';
  document.getElementById('submit-review').textContent = 'Run corrected revision';
  result.classList.add('hidden');
  document.getElementById('review-form').scrollIntoView({behavior:'smooth', block:'start'});
  document.getElementById('project_name').focus();
  announce(`Revision mode started from revision ${review.revision_number}`);
}

function showError(message, details = null) {
  result.classList.remove('hidden');
  result.innerHTML = `<div class="error-banner" role="alert"><strong>Review could not be completed</strong><p>${escapeHtml(message)}</p>${details ? `<pre>${escapeHtml(details)}</pre>` : ''}</div>`;
  result.focus();
  announce(message);
}

form.addEventListener('submit', async event => {
  event.preventDefault();
  const submitButton = document.getElementById('submit-review');
  submitButton.disabled = true;
  result.classList.remove('hidden');
  result.innerHTML = '<div class="loading-line" role="status"><span aria-hidden="true"></span>Running asset discovery, deterministic checks, and release-readiness analysis…</div>';
  result.focus();
  try {
    const endpoint = activeRevisionSourceId
      ? `/api/reviews/${activeRevisionSourceId}/revisions`
      : '/api/reviews';
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(buildPayload())
    });
    const data = await response.json();
    if (!response.ok) {
      const detail = Array.isArray(data.detail) ? data.detail.map(item => item.msg).join('; ') : data.detail;
      showError(detail || 'The service rejected the review payload.');
      return;
    }
    activeReviewId = data.review_id;
    clearRevisionMode();
    await renderReview(data);
    await refreshDashboard();
    announce(`Review completed with outcome ${data.outcome.replaceAll('_', ' ')}`);
  } catch (error) {
    showError('The service could not be reached.', error.message);
  } finally {
    submitButton.disabled = false;
  }
});


function workflowMetrics(metrics) {
  if (!metrics || !metrics.length) return '';
  return `<div class="workflow-metrics" aria-label="Measured workflow indicators">${metrics.map(metric => `
    <article><strong>${escapeHtml(metric.value)}${metric.unit === '%' ? '%' : ''}</strong><span>${escapeHtml(metric.name)}</span><small>${escapeHtml(metric.description)}</small></article>`).join('')}</div>`;
}

function riskProfile(signals) {
  if (!signals || !signals.length) return '';
  return `<div class="risk-profile">${signals.map(signal => `<div class="risk-row">
    <div><strong>${escapeHtml(signal.name)}</strong><span class="risk-level ${signal.level}">${escapeHtml(signal.level)}</span></div>
    <div class="risk-track" aria-label="${escapeHtml(signal.name)} risk ${signal.score} percent"><span style="width:${signal.score}%"></span></div>
    <small>${escapeHtml(signal.rationale)}</small>
  </div>`).join('')}</div>`;
}

function agentRunHeader(analysis) {
  return `<div class="agent-run-header">
    <div><span>Run ID</span><code>${escapeHtml(String(analysis.run_id).slice(0, 18))}…</code></div>
    <div><span>Workflow</span><strong>${escapeHtml(analysis.workflow_version)}</strong></div>
    <div><span>Model</span><strong>${escapeHtml(analysis.model)}</strong></div>
    <div><span>Latency</span><strong>${escapeHtml(analysis.total_duration_ms)} ms</strong></div>
    <div><span>Fallback</span><strong>${analysis.fallback_used ? 'Used' : 'No'}</strong></div>
  </div>`;
}

async function loadSystemMap() {
  const layers = document.getElementById('runtime-layers');
  const state = document.getElementById('integration-state');
  if (!layers || !state) return;
  try {
    const response = await fetch('/api/system/capabilities');
    const data = await response.json();
    state.innerHTML = `<strong>${escapeHtml(data.workflow_version)}</strong><span>Gemini: ${escapeHtml(data.gemini_model)}</span><span>Agent Engine: ${data.agent_engine_configured ? 'configured' : 'account-stage'}</span>`;
    layers.innerHTML = `<div class="agent-rail">${data.runtime_layers.map((layer, index) => `<article class="agent-node"><span>${String(index + 1).padStart(2,'0')}</span><div><small>${escapeHtml(layer.type)}</small><h3>${escapeHtml(layer.name)}</h3><p>${escapeHtml(layer.purpose)}</p></div></article>`).join('')}</div>
      <div class="guardrail-box"><p class="section-kicker">NON-NEGOTIABLE GUARDRAILS</p>${data.guardrails.map(item => `<p>✓ ${escapeHtml(item)}</p>`).join('')}</div>`;
  } catch (_) {
    state.textContent = 'System capabilities unavailable.';
  }
}

function readinessCards(readiness) {
  return `<div class="readiness-grid" aria-label="Release readiness">
    <article><strong>${readiness.asset_coverage_percent}%</strong><span>Asset coverage</span></article>
    <article><strong>${readiness.evidence_completeness_percent}%</strong><span>Evidence completeness</span></article>
    <article><strong>${readiness.blocking_findings}</strong><span>Blocking findings</span></article>
    <article><strong>${readiness.warning_findings}</strong><span>Warnings</span></article>
  </div>`;
}

function rightsMatrix(rows) {
  if (!rows.length) return '<p class="muted">No declared assets.</p>';
  return `<div class="table-wrap"><table class="matrix-table"><thead><tr><th>Asset</th><th>Type</th><th>Status</th><th>Matched grant</th><th>Required action</th></tr></thead><tbody>${rows.map(row => `
    <tr><td><strong>${escapeHtml(row.asset_name)}</strong><br><small>${escapeHtml(row.asset_id)}</small></td>
    <td>${escapeHtml(row.asset_type)}</td><td><span class="matrix-status ${row.status}">${escapeHtml(row.status.toUpperCase())}</span></td>
    <td>${escapeHtml(row.matched_permission_ids.join(', ') || 'None')}</td><td>${escapeHtml(row.required_action)}</td></tr>`).join('')}</tbody></table></div>`;
}

function findingCards(findings) {
  return findings.map(finding => `<details class="finding ${finding.severity}" ${finding.severity === 'critical' ? 'open' : ''}>
    <summary><span><strong>${escapeHtml(finding.title || finding.code)}</strong><small>${escapeHtml(finding.category || 'other')} · ${escapeHtml(finding.code)}</small></span><span class="severity-pill">${escapeHtml(finding.severity)}</span></summary>
    <p>${escapeHtml(finding.message)}</p>
    <div class="resolution"><strong>Resolution</strong><span>${escapeHtml(finding.resolution || 'Review and document the corrective action.')}</span></div>
  </details>`).join('');
}

function lineageHtml(lineage, currentReviewId) {
  if (!lineage || lineage.reviews.length < 2) return '';
  return `<div class="subpanel lineage-panel"><div class="subpanel-title"><h3>Case revision history</h3><span>${lineage.reviews.length} revisions</span></div>
    <div class="lineage-list">${lineage.reviews.map(item => `<button type="button" class="lineage-item ${item.review_id === currentReviewId ? 'current' : ''}" data-review-id="${item.review_id}">
      <span>Revision ${item.revision_number}</span><strong class="${item.outcome}">${escapeHtml(item.outcome.replaceAll('_',' '))}</strong><small>${new Date(item.created_at).toLocaleString()}</small>
    </button>`).join('')}</div></div>`;
}

async function loadLineage(reviewId) {
  const response = await fetch(`/api/reviews/${reviewId}/lineage`);
  if (!response.ok) return null;
  return response.json();
}

async function renderReview(data) {
  const hints = data.agent_analysis.asset_hints || [];
  const steps = data.agent_analysis.steps || [];
  const finalDecision = data.human_decision !== 'pending';
  const lineage = await loadLineage(data.review_id);
  result.innerHTML = `
    <div class="result-header">
      <div><p class="section-kicker">CLEARANCE OUTCOME</p><div class="outcome ${data.outcome}">${data.outcome.replaceAll('_',' ')}</div></div>
      <div class="score-ring" title="Metadata coverage score" aria-label="Metadata coverage score ${data.coverage_score} percent">${data.coverage_score}%</div>
    </div>
    <div class="case-strip"><span>Case <code>${escapeHtml(data.case_id)}</code></span><span>Revision <strong>${data.revision_number}</strong></span><span>Input <code>${escapeHtml(data.input_sha256.slice(0, 16))}…</code></span></div>
    <p class="summary">${escapeHtml(data.summary)}</p>
    <p><strong>Recommended next step:</strong> ${escapeHtml(data.recommended_next_step)}</p>
    ${readinessCards(data.readiness)}
    ${agentRunHeader(data.agent_analysis)}
    ${workflowMetrics(data.agent_analysis.workflow_metrics)}
    <div class="subpanel risk-panel"><div class="subpanel-title"><h3>Release risk profile</h3><span>Transparent signals, not a legal score</span></div>${riskProfile(data.agent_analysis.risk_profile)}</div>
    <div class="subpanel matrix-panel"><div class="subpanel-title"><h3>Rights matrix</h3><span>${escapeHtml(data.policy_version)}</span></div>${rightsMatrix(data.rights_matrix)}</div>
    <div class="result-grid">
      <div class="subpanel"><h3>Policy findings</h3>${findingCards(data.findings)}</div>
      <div>
        <div class="subpanel"><h3>Agent discovery</h3>${hints.length ? hints.map(h => `<div class="hint"><strong>${escapeHtml(h.asset_type.toUpperCase())}</strong><p>${escapeHtml(h.phrase)}</p><span class="muted">${Math.round(h.confidence*100)}% · ${escapeHtml(h.rationale)}</span></div>`).join('') : '<p class="muted">No additional asset hints.</p>'}</div>
        <div class="subpanel trace-panel"><div class="subpanel-title"><h3>Agent run trace</h3><span>${escapeHtml(data.agent_analysis.boundary)}</span></div>${steps.map(s => `<div class="agent-step"><span class="step-dot ${s.status}" aria-hidden="true"></span><div><div class="step-title"><strong>${escapeHtml(s.agent || s.name.replaceAll('_',' '))}</strong><span>${escapeHtml(s.provider || 'local')} · ${escapeHtml(s.duration_ms || 0)} ms</span></div><div class="muted">${escapeHtml(s.detail)}</div>${s.guardrail ? `<small>${escapeHtml(s.guardrail)}</small>` : ''}</div></div>`).join('')}</div>
      </div>
    </div>
    <div class="subpanel action-list"><h3>Required actions</h3><ol>${data.readiness.required_actions.map(item => `<li>${escapeHtml(item)}</li>`).join('')}</ol></div>
    <div class="subpanel human-review">
      <div class="subpanel-title"><h3>Human decision and correction path</h3><span>${finalDecision ? 'Finalized' : 'Pending'}</span></div>
      ${finalDecision ? `<p><strong>${escapeHtml(data.human_decision.toUpperCase())}</strong> by ${escapeHtml(data.human_reviewer || 'Unknown reviewer')}</p><p>${escapeHtml(data.human_note || 'No note recorded.')}</p>` : `
      <div class="grid two"><label>Reviewer<input id="reviewer" value="Production Rights Officer" maxlength="120"></label><label>Decision note<input id="decision-note" maxlength="2000" placeholder="Explain the recorded decision"></label></div>
      <div class="decision-row">
        <button type="button" class="approve" id="approve-review" ${data.outcome === 'BLOCKED' ? 'disabled title="Blocked records cannot be approved"' : ''}>Approve record</button>
        <button type="button" class="reject" id="reject-review">Reject record</button>
      </div>`}
      <div class="decision-row correction-row">
        <button type="button" class="secondary-button" id="create-revision">Create corrected revision</button>
      </div>
      <div class="export-row" aria-label="Review exports">
        <a class="download-link" href="/api/reviews/${data.review_id}/release-package">Download release package ZIP</a>
        <a class="download-link" href="/api/reviews/${data.review_id}/evidence/download">Evidence JSON</a>
        <a class="download-link" href="/api/reviews/${data.review_id}/rights-matrix.csv">Rights matrix CSV</a>
        <a class="download-link" href="/api/reviews/${data.review_id}/report" target="_blank" rel="noopener">Printable report</a>
        <button type="button" class="text-link" id="verify-evidence">Verify checksums</button>
      </div>
      <div id="checksum-result" class="checksum-result hidden"></div>
    </div>
    ${lineageHtml(lineage, data.review_id)}
    <div class="subpanel timeline"><h3>Workflow timeline</h3><div id="timeline-events"><p class="muted">Loading events…</p></div></div>
    <p class="muted review-meta">Review ID: ${data.review_id} · Agent mode: ${escapeHtml(data.agent_analysis.mode)} · Created: ${new Date(data.created_at).toLocaleString()}</p>`;

  activeReviewId = data.review_id;
  if (!finalDecision) {
    document.getElementById('approve-review').addEventListener('click', () => submitDecision('approved'));
    document.getElementById('reject-review').addEventListener('click', () => submitDecision('rejected'));
  }
  document.getElementById('create-revision').addEventListener('click', () => enterRevisionMode(data));
  document.getElementById('verify-evidence').addEventListener('click', verifyEvidence);
  result.querySelectorAll('.lineage-item').forEach(button => button.addEventListener('click', async () => {
    await openReview(button.dataset.reviewId);
  }));
  await loadTimeline(data.review_id);
  result.classList.remove('hidden');
  result.focus();
}

async function verifyEvidence() {
  const target = document.getElementById('checksum-result');
  const response = await fetch(`/api/reviews/${activeReviewId}/evidence/verify`);
  const data = await response.json();
  if (!response.ok) {
    announce('Checksum verification failed');
    return;
  }
  target.classList.remove('hidden');
  target.innerHTML = `<strong>Checksums recalculated</strong><span>Input metadata</span><code>${escapeHtml(data.input_sha256)}</code><span>Review and workflow record</span><code>${escapeHtml(data.content_sha256)}</code><span>${data.event_count} workflow event(s). These are integrity checksums, not digital signatures.</span>`;
  announce('Checksums verified');
}

async function submitDecision(decision) {
  const reviewer = document.getElementById('reviewer').value;
  const note = document.getElementById('decision-note').value;
  const response = await fetch(`/api/reviews/${activeReviewId}/human-decision`, {
    method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({decision, reviewer, note:note || null})
  });
  const data = await response.json();
  if (!response.ok) {
    announce(data.detail || 'Decision could not be recorded');
    showInlineMessage(data.detail || 'Decision could not be recorded', 'error');
    return;
  }
  await renderReview(data);
  await refreshDashboard();
  announce(`Human decision ${decision} recorded`);
}

function showInlineMessage(message, type = 'info') {
  const existing = result.querySelector('.inline-message');
  if (existing) existing.remove();
  const node = document.createElement('div');
  node.className = `inline-message ${type}`;
  node.setAttribute('role', type === 'error' ? 'alert' : 'status');
  node.textContent = message;
  result.prepend(node);
}

async function loadTimeline(reviewId) {
  const response = await fetch(`/api/reviews/${reviewId}/events`);
  const events = await response.json();
  const target = document.getElementById('timeline-events');
  if (!target) return;
  if (!response.ok) {
    target.innerHTML = '<p class="muted">Timeline unavailable.</p>';
    return;
  }
  target.innerHTML = events.map(event => `<div class="event"><time>${new Date(event.created_at).toLocaleString()}</time><div><strong>${escapeHtml(event.event_type.replaceAll('_',' '))}</strong><div class="muted">Actor: ${escapeHtml(event.actor)}</div></div></div>`).join('');
}

async function refreshDashboard() {
  try {
    const [healthResponse, readyResponse, summaryResponse] = await Promise.all([
      fetch('/health'), fetch('/ready'), fetch('/api/reviews/summary')
    ]);
    const health = await healthResponse.json();
    const ready = await readyResponse.json();
    const summary = await summaryResponse.json();
    document.getElementById('agent-mode').textContent = `Agent: ${health.agent_mode}`;
    document.getElementById('system-ready').textContent = `System: ${ready.status}`;
    document.getElementById('metric-total').textContent = summary.total_reviews;
    document.getElementById('metric-cases').textContent = summary.total_cases;
    document.getElementById('metric-revisions').textContent = summary.revision_reviews;
    document.getElementById('metric-cleared').textContent = summary.cleared;
    document.getElementById('metric-review').textContent = summary.review_required;
    document.getElementById('metric-blocked').textContent = summary.blocked;
  } catch (_) {
    document.getElementById('agent-mode').textContent = 'Agent: unavailable';
    document.getElementById('system-ready').textContent = 'System: unavailable';
  }
}

async function openReview(reviewId) {
  const response = await fetch(`/api/reviews/${reviewId}`);
  const review = await response.json();
  if (!response.ok) {
    announce('Review could not be opened');
    return;
  }
  activateTab('new-review');
  await renderReview(review);
  result.scrollIntoView({behavior:'smooth', block:'start'});
}

async function refreshHistory() {
  const outcome = document.getElementById('history-outcome').value;
  const query = document.getElementById('history-query').value.trim();
  const params = new URLSearchParams({limit:'50'});
  if (outcome) params.set('outcome', outcome);
  if (query) params.set('q', query);
  const response = await fetch(`/api/reviews?${params}`);
  const reviews = await response.json();
  const list = document.getElementById('history-list');
  if (!response.ok) {
    list.innerHTML = '<p class="muted">Review history is unavailable.</p>';
    return;
  }
  if (!reviews.length) {
    list.innerHTML = '<p class="muted">No matching reviews.</p>';
    return;
  }
  list.innerHTML = reviews.map(review => `<article class="history-card">
    <div><h3>${escapeHtml(review.action.project_name)}</h3><p class="muted">${escapeHtml(review.action.action_type.replaceAll('_',' '))}</p><small>Case ${escapeHtml(review.case_id.slice(0, 8))} · Rev ${review.revision_number}</small></div>
    <strong class="${review.outcome}">${escapeHtml(review.outcome.replaceAll('_',' '))}</strong>
    <span>${review.coverage_score}%</span><span>${escapeHtml(review.human_decision)}</span>
    <button class="secondary-button open-review" data-id="${review.review_id}">Open</button></article>`).join('');
  list.querySelectorAll('.open-review').forEach(button => button.addEventListener('click', () => openReview(button.dataset.id)));
}

function escapeHtml(value) {
  return String(value).replace(/[&<>'"]/g, character => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[character]));
}

function activateTab(tabId, focusTab = false) {
  document.querySelectorAll('.tab').forEach(tab => {
    const active = tab.dataset.tab === tabId;
    tab.classList.toggle('active', active);
    tab.setAttribute('aria-selected', String(active));
    tab.tabIndex = active ? 0 : -1;
    if (active && focusTab) tab.focus();
  });
  document.querySelectorAll('.tab-panel').forEach(panel => {
    const active = panel.id === tabId;
    panel.classList.toggle('active', active);
    panel.hidden = !active;
  });
  if (tabId === 'history') refreshHistory();
  if (tabId === 'system-map') loadSystemMap();
}

document.getElementById('add-asset').addEventListener('click', () => addAsset());
document.getElementById('cancel-revision').addEventListener('click', clearRevisionMode);
document.getElementById('refresh-history').addEventListener('click', refreshHistory);
document.getElementById('history-outcome').addEventListener('change', refreshHistory);
document.getElementById('history-query').addEventListener('input', () => {
  clearTimeout(window.historySearchTimer);
  window.historySearchTimer = setTimeout(refreshHistory, 250);
});
document.querySelectorAll('[data-scenario]').forEach(button => button.addEventListener('click', () => loadScenario(button.dataset.scenario)));
document.querySelectorAll('.tab').forEach(button => button.addEventListener('click', () => activateTab(button.dataset.tab)));

document.querySelector('.tabs').addEventListener('keydown', event => {
  if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
  const tabs = [...document.querySelectorAll('.tab')];
  const current = tabs.indexOf(document.activeElement);
  let next = current;
  if (event.key === 'ArrowRight') next = (current + 1) % tabs.length;
  if (event.key === 'ArrowLeft') next = (current - 1 + tabs.length) % tabs.length;
  if (event.key === 'Home') next = 0;
  if (event.key === 'End') next = tabs.length - 1;
  event.preventDefault();
  activateTab(tabs[next].dataset.tab, true);
});

loadScenario('cleared');
refreshDashboard();
