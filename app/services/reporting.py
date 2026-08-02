from __future__ import annotations

import csv
import hashlib
import io
import json
import zipfile
from datetime import datetime, timezone
from html import escape

from app.domain.models import ClearanceReview, ReviewEvidenceBundle


def _label(value: str) -> str:
    return value.replace("_", " ").title()


def build_rights_matrix_csv(review: ClearanceReview) -> str:
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(
        [
            "case_id",
            "review_id",
            "revision_number",
            "asset_id",
            "asset_name",
            "asset_type",
            "status",
            "matched_permission_ids",
            "critical_findings",
            "warning_findings",
            "required_action",
        ]
    )
    for row in review.rights_matrix:
        writer.writerow(
            [
                str(review.case_id),
                str(review.review_id),
                review.revision_number,
                row.asset_id,
                row.asset_name,
                row.asset_type.value,
                row.status,
                "; ".join(row.matched_permission_ids),
                row.critical_count,
                row.warning_count,
                row.required_action,
            ]
        )
    return output.getvalue()


def build_release_report(review: ClearanceReview, bundle: ReviewEvidenceBundle) -> str:
    finding_rows = "".join(
        f"<tr><td>{escape(item.severity.upper())}</td><td>{escape(item.category)}</td>"
        f"<td><strong>{escape(item.title)}</strong><br><small>{escape(item.code)}</small></td>"
        f"<td>{escape(item.message)}<br><small><strong>Resolution:</strong> {escape(item.resolution)}</small></td></tr>"
        for item in review.findings
    )
    matrix_rows = "".join(
        f"<tr><td>{escape(row.asset_name)}</td><td>{escape(_label(row.asset_type.value))}</td>"
        f"<td class='{escape(row.status)}'>{escape(row.status.upper())}</td>"
        f"<td>{escape(', '.join(row.matched_permission_ids) or 'None')}</td>"
        f"<td>{escape(row.required_action)}</td></tr>"
        for row in review.rights_matrix
    )
    event_rows = "".join(
        f"<tr><td>{escape(event.created_at.isoformat())}</td><td>{escape(_label(event.event_type))}</td>"
        f"<td>{escape(event.actor)}</td></tr>"
        for event in bundle.audit_events
    )
    channels = ", ".join(
        channel.value for channel in review.action.release_context.distribution_channels
    ) or "Not recorded"
    human = (
        f"{review.human_decision.upper()} by {escape(review.human_reviewer or 'Unassigned')}"
        if review.human_decision != "pending"
        else "PENDING"
    )
    previous = str(review.supersedes_review_id) if review.supersedes_review_id else "None"
    return f"""<!doctype html>
<html lang='en'>
<head>
<meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>CINE-GATE release report</title>
<style>
body{{font-family:Arial,sans-serif;color:#15202b;margin:40px;line-height:1.45}}
h1{{font-size:34px;margin:0}}h2{{margin-top:30px;border-bottom:2px solid #183b4e;padding-bottom:6px}}
.meta{{color:#52636f}}.hero{{border:1px solid #9bb0bb;padding:22px;border-radius:12px;background:#f4f8fa}}
.outcome{{font-size:25px;font-weight:800}}table{{width:100%;border-collapse:collapse;margin:14px 0}}
th,td{{border:1px solid #b9c7ce;padding:9px;text-align:left;vertical-align:top}}th{{background:#e9f0f3}}
.covered{{color:#116b41;font-weight:700}}.review{{color:#8a5a00;font-weight:700}}.blocked{{color:#a12626;font-weight:700}}
.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}}.metric{{border:1px solid #b9c7ce;padding:12px;border-radius:8px}}
small{{color:#52636f}}code{{word-break:break-all}}@media print{{body{{margin:18mm}}.hero{{break-inside:avoid}}}}
</style></head>
<body>
<section class='hero'>
<small>CINE-GATE · RIGHTS-CLEARANCE RELEASE REPORT</small>
<h1>{escape(review.action.project_name)}</h1>
<p class='outcome'>{escape(review.outcome.value.replace('_', ' '))}</p>
<p>{escape(review.summary)}</p>
<p class='meta'>Case ID: {review.case_id}<br>Review ID: {review.review_id}<br>Revision: {review.revision_number}<br>
Supersedes: {escape(previous)}<br>Created: {review.created_at.isoformat()}<br>
Policy: {escape(review.policy_version)}<br>Input checksum: <code>{review.input_sha256}</code><br>
Evidence checksum: <code>{bundle.content_sha256}</code></p>
</section>
<h2>Proposed action</h2>
<p><strong>Action:</strong> {escape(_label(review.action.action_type.value))}<br>
<strong>Description:</strong> {escape(review.action.description)}<br>
<strong>Territories:</strong> {escape(', '.join(review.action.intended_territories))}<br>
<strong>Channels:</strong> {escape(channels)}<br>
<strong>Commercial use:</strong> {review.action.release_context.commercial_use}<br>
<strong>Modifications planned:</strong> {review.action.release_context.modifications_planned}<br>
<strong>Synthetic-media use:</strong> {review.action.release_context.synthetic_media_use}</p>
<h2>Release readiness</h2>
<div class='grid'>
<div class='metric'><strong>{review.readiness.asset_coverage_percent}%</strong><br><small>Asset coverage</small></div>
<div class='metric'><strong>{review.readiness.evidence_completeness_percent}%</strong><br><small>Evidence completeness</small></div>
<div class='metric'><strong>{review.readiness.blocking_findings}</strong><br><small>Blocking findings</small></div>
<div class='metric'><strong>{review.readiness.warning_findings}</strong><br><small>Warnings</small></div>
</div>
<h2>Rights matrix</h2>
<table><thead><tr><th>Asset</th><th>Type</th><th>Status</th><th>Matched grants</th><th>Required action</th></tr></thead>
<tbody>{matrix_rows}</tbody></table>
<h2>Policy findings</h2>
<table><thead><tr><th>Severity</th><th>Category</th><th>Finding</th><th>Explanation and resolution</th></tr></thead><tbody>{finding_rows}</tbody></table>
<h2>Human decision</h2><p><strong>{human}</strong><br>{escape(review.human_note or 'No decision note recorded.')}</p>
<h2>Workflow events</h2>
<table><thead><tr><th>Time</th><th>Event</th><th>Actor</th></tr></thead><tbody>{event_rows}</tbody></table>
<h2>Limitations</h2><p>{escape(bundle.disclaimer)}</p>
</body></html>"""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_release_package(review: ClearanceReview, bundle: ReviewEvidenceBundle) -> bytes:
    evidence_bytes = json.dumps(
        bundle.model_dump(mode="json"),
        ensure_ascii=False,
        sort_keys=True,
        indent=2,
    ).encode("utf-8")
    report_bytes = build_release_report(review, bundle).encode("utf-8")
    csv_bytes = build_rights_matrix_csv(review).encode("utf-8-sig")
    readme_bytes = (
        "CINE-GATE RELEASE PACKAGE\n\n"
        f"Project: {review.action.project_name}\n"
        f"Case ID: {review.case_id}\n"
        f"Review ID: {review.review_id}\n"
        f"Revision: {review.revision_number}\n"
        f"Outcome: {review.outcome.value}\n\n"
        "This package records supplied metadata and workflow decisions. It does not authenticate source "
        "documents, establish ownership, or provide legal advice. Checksums are integrity aids, not digital signatures.\n"
    ).encode("utf-8")
    files = {
        "evidence.json": evidence_bytes,
        "release-report.html": report_bytes,
        "rights-matrix.csv": csv_bytes,
        "README.txt": readme_bytes,
    }
    manifest = {
        "schema_version": "cine-gate-release-package-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "case_id": str(review.case_id),
        "review_id": str(review.review_id),
        "revision_number": review.revision_number,
        "input_sha256": review.input_sha256,
        "evidence_content_sha256": bundle.content_sha256,
        "files": {
            name: {"sha256": _sha256(data), "bytes": len(data)}
            for name, data in sorted(files.items())
        },
    }
    files["manifest.json"] = json.dumps(
        manifest, ensure_ascii=False, sort_keys=True, indent=2
    ).encode("utf-8")

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in files.items():
            archive.writestr(name, data)
    return buffer.getvalue()
