from __future__ import annotations

from collections import defaultdict

from .models import (
    AssetClearanceRow,
    ClearanceFinding,
    PermissionStatus,
    ProductionAction,
    ReleaseReadiness,
)


def build_rights_matrix(
    action: ProductionAction,
    findings: list[ClearanceFinding],
) -> list[AssetClearanceRow]:
    findings_by_asset: dict[str, list[ClearanceFinding]] = defaultdict(list)
    for finding in findings:
        if finding.asset_id:
            findings_by_asset[finding.asset_id].append(finding)

    rows: list[AssetClearanceRow] = []
    for asset in action.assets:
        asset_findings = findings_by_asset.get(asset.asset_id, [])
        critical = sum(item.severity == "critical" for item in asset_findings)
        warnings = sum(item.severity == "warning" for item in asset_findings)
        matched = [
            permission.permission_id
            for permission in action.permissions
            if permission.asset_id == asset.asset_id and permission.status == PermissionStatus.GRANTED
        ]
        if critical:
            status = "blocked"
            required_action = "Resolve every blocking permission or scope condition and run a new review."
        elif warnings:
            status = "review"
            required_action = "A qualified reviewer must resolve or document the outstanding item."
        else:
            status = "covered"
            required_action = "Maintain the recorded scope and retain the referenced evidence."
        rows.append(
            AssetClearanceRow(
                asset_id=asset.asset_id,
                asset_name=asset.asset_name,
                asset_type=asset.asset_type,
                status=status,
                matched_permission_ids=matched,
                critical_count=critical,
                warning_count=warnings,
                required_action=required_action,
            )
        )
    return rows


def build_release_readiness(
    action: ProductionAction,
    findings: list[ClearanceFinding],
    matrix: list[AssetClearanceRow],
) -> ReleaseReadiness:
    total_assets = len(action.assets)
    covered_assets = sum(row.status == "covered" for row in matrix)
    evidence_references = sum(bool(item.evidence_reference) for item in action.permissions)
    evidence_fingerprints = sum(bool(item.evidence_sha256) for item in action.permissions)
    total_permissions = len(action.permissions)
    blocking = sum(item.severity == "critical" for item in findings)
    warnings = sum(item.severity == "warning" for item in findings)

    coverage = round((covered_assets / total_assets) * 100) if total_assets else 0
    if total_permissions:
        # A reference is essential; a fingerprint is an optional but valuable integrity field.
        evidence_points = evidence_references + (evidence_fingerprints * 0.25)
        evidence_percent = min(100, round((evidence_points / (total_permissions * 1.25)) * 100))
    else:
        evidence_percent = 0

    required_actions: list[str] = []
    if blocking:
        required_actions.append("Correct blocking scope, status, date, territory, or authorization conditions.")
    if warnings:
        required_actions.append("Resolve all warning-level evidence or workflow gaps with a qualified reviewer.")
    if evidence_references < total_permissions:
        required_actions.append("Add a traceable evidence reference to every permission record.")
    if evidence_fingerprints < total_permissions:
        required_actions.append("Add SHA-256 document fingerprints where source files are available.")
    if not required_actions:
        required_actions.append("Retain the evidence packet and proceed only within the recorded scope.")

    return ReleaseReadiness(
        declared_assets=total_assets,
        covered_assets=covered_assets,
        evidence_references=evidence_references,
        evidence_fingerprints=evidence_fingerprints,
        blocking_findings=blocking,
        warning_findings=warnings,
        asset_coverage_percent=coverage,
        evidence_completeness_percent=evidence_percent,
        required_actions=required_actions,
    )
