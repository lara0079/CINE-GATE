from __future__ import annotations

from collections import defaultdict
from datetime import date

from .finding_catalog import get_finding_definition
from .models import (
    ActionType,
    AgentAnalysis,
    AssetType,
    ClearanceFinding,
    ClearanceOutcome,
    PermissionStatus,
    ProductionAction,
)


POLICY_VERSION = "cine-gate-rights-policy-0.5"

PUBLIC_ACTIONS = {
    ActionType.FESTIVAL_SUBMISSION,
    ActionType.PUBLIC_TRAILER,
    ActionType.COMMERCIAL_RELEASE,
    ActionType.SOCIAL_MEDIA_PUBLICATION,
}

SENSITIVE_AI_ASSETS = {AssetType.LIKENESS, AssetType.VOICE}
MEDIA_ASSETS = {
    AssetType.LIKENESS,
    AssetType.VOICE,
    AssetType.MUSIC,
    AssetType.FOOTAGE,
    AssetType.ARTWORK,
}


def _normalise(value: str) -> str:
    return " ".join(value.strip().lower().split())


def _territories_cover(recorded: list[str], intended: list[str]) -> bool:
    recorded_set = {_normalise(value) for value in recorded}
    intended_set = {_normalise(value) for value in intended}
    if "worldwide" in recorded_set or "global" in recorded_set:
        return True
    if "worldwide" in intended_set or "global" in intended_set:
        return "worldwide" in recorded_set or "global" in recorded_set
    return intended_set.issubset(recorded_set)


def _add(
    findings: list[ClearanceFinding],
    code: str,
    severity: str,
    message: str,
    asset_id: str | None = None,
    permission_id: str | None = None,
) -> None:
    definition = get_finding_definition(code)
    findings.append(
        ClearanceFinding(
            code=code,
            severity=severity,  # type: ignore[arg-type]
            message=message,
            category=definition.category,
            title=definition.title,
            resolution=definition.resolution,
            asset_id=asset_id,
            permission_id=permission_id,
        )
    )


def evaluate_clearance(
    action: ProductionAction,
    agent_analysis: AgentAnalysis | None = None,
    today: date | None = None,
) -> tuple[ClearanceOutcome, list[ClearanceFinding], int]:
    """Evaluate one narrow film-rights clearance record.

    This policy is intentionally limited to supplied film-rights metadata. It does not
    implement or disclose any private architecture, unpublished algorithm, or enterprise
    governance mechanism from another project.
    """
    current_date = today or date.today()
    evaluation_date = action.planned_date or current_date
    findings: list[ClearanceFinding] = []

    if not action.assets:
        _add(
            findings,
            "NO_ASSETS_DECLARED",
            "critical",
            "No rights-bearing assets were declared for the proposed action.",
        )

    permissions_by_asset: dict[str, list] = defaultdict(list)
    for permission in action.permissions:
        permissions_by_asset[permission.asset_id].append(permission)

    for asset in action.assets:
        records = permissions_by_asset.get(asset.asset_id, [])
        if not records:
            _add(
                findings,
                "ASSET_WITHOUT_PERMISSION_RECORD",
                "critical",
                f"No permission record is linked to '{asset.asset_name}'.",
                asset.asset_id,
            )
            continue

        statuses = {record.status for record in records}
        if PermissionStatus.DENIED in statuses or PermissionStatus.REVOKED in statuses:
            _add(
                findings,
                "PERMISSION_DENIED_OR_REVOKED",
                "critical",
                f"A permission for '{asset.asset_name}' is denied or revoked.",
                asset.asset_id,
            )

        if PermissionStatus.GRANTED in statuses and (
            PermissionStatus.DENIED in statuses or PermissionStatus.REVOKED in statuses
        ):
            _add(
                findings,
                "CONFLICTING_PERMISSION_RECORDS",
                "critical",
                f"Conflicting permission states exist for '{asset.asset_name}'.",
                asset.asset_id,
            )

        granted_records = [record for record in records if record.status == PermissionStatus.GRANTED]
        unresolved_records = [
            record
            for record in records
            if record.status in {PermissionStatus.PENDING, PermissionStatus.UNKNOWN}
        ]

        if not granted_records and unresolved_records:
            _add(
                findings,
                "PERMISSION_UNRESOLVED",
                "warning",
                f"Permission for '{asset.asset_name}' is still pending or unknown.",
                asset.asset_id,
            )

        usable_grants = []
        for permission in granted_records:
            valid = True
            if permission.valid_from and evaluation_date < permission.valid_from:
                _add(
                    findings,
                    "PERMISSION_NOT_YET_VALID",
                    "critical",
                    f"Permission '{permission.permission_id}' for '{asset.asset_name}' is not valid on "
                    f"{evaluation_date.isoformat()}.",
                    asset.asset_id,
                    permission.permission_id,
                )
                valid = False
            if permission.valid_until and evaluation_date > permission.valid_until:
                _add(
                    findings,
                    "PERMISSION_EXPIRED",
                    "critical",
                    f"Permission '{permission.permission_id}' for '{asset.asset_name}' expires before "
                    "the planned action date.",
                    asset.asset_id,
                    permission.permission_id,
                )
                valid = False
            if action.action_type not in permission.allowed_uses:
                _add(
                    findings,
                    "USE_OUTSIDE_PERMISSION_SCOPE",
                    "critical",
                    f"'{action.action_type.value}' is outside the recorded use scope for "
                    f"'{asset.asset_name}'.",
                    asset.asset_id,
                    permission.permission_id,
                )
                valid = False
            if not _territories_cover(permission.territories, action.intended_territories):
                _add(
                    findings,
                    "TERRITORY_OUTSIDE_PERMISSION_SCOPE",
                    "critical",
                    f"The recorded territories for '{asset.asset_name}' do not cover the intended "
                    "distribution territory.",
                    asset.asset_id,
                    permission.permission_id,
                )
                valid = False

            requested_channels = set(action.release_context.distribution_channels)
            allowed_channels = set(permission.allowed_channels)
            if requested_channels and allowed_channels and not requested_channels.issubset(allowed_channels):
                _add(
                    findings,
                    "CHANNEL_OUTSIDE_PERMISSION_SCOPE",
                    "critical",
                    f"The distribution channels recorded for '{asset.asset_name}' do not cover every "
                    "requested channel.",
                    asset.asset_id,
                    permission.permission_id,
                )
                valid = False
            elif requested_channels and not allowed_channels:
                _add(
                    findings,
                    "CHANNEL_SCOPE_NOT_RECORDED",
                    "warning",
                    f"No distribution-channel scope is recorded for '{asset.asset_name}'.",
                    asset.asset_id,
                    permission.permission_id,
                )

            if action.release_context.commercial_use:
                if permission.commercial_use_allowed is False:
                    _add(
                        findings,
                        "COMMERCIAL_USE_NOT_ALLOWED",
                        "critical",
                        f"Commercial use is expressly not allowed for '{asset.asset_name}'.",
                        asset.asset_id,
                        permission.permission_id,
                    )
                    valid = False
                elif permission.commercial_use_allowed is None:
                    _add(
                        findings,
                        "COMMERCIAL_USE_SCOPE_UNKNOWN",
                        "warning",
                        f"Commercial-use permission is not explicitly recorded for '{asset.asset_name}'.",
                        asset.asset_id,
                        permission.permission_id,
                    )

            if action.release_context.modifications_planned:
                if permission.modification_allowed is False:
                    _add(
                        findings,
                        "MODIFICATION_NOT_ALLOWED",
                        "critical",
                        f"Modification or adaptation is expressly not allowed for '{asset.asset_name}'.",
                        asset.asset_id,
                        permission.permission_id,
                    )
                    valid = False
                elif permission.modification_allowed is None:
                    _add(
                        findings,
                        "MODIFICATION_SCOPE_UNKNOWN",
                        "warning",
                        f"Modification or adaptation rights are not explicitly recorded for "
                        f"'{asset.asset_name}'.",
                        asset.asset_id,
                        permission.permission_id,
                    )

            synthetic_relevant = asset.ai_generated
            if synthetic_relevant:
                if permission.synthetic_use_allowed is False:
                    _add(
                        findings,
                        "SYNTHETIC_USE_NOT_ALLOWED",
                        "critical",
                        f"Synthetic or AI-mediated use is expressly not allowed for '{asset.asset_name}'.",
                        asset.asset_id,
                        permission.permission_id,
                    )
                    valid = False
                elif permission.synthetic_use_allowed is None:
                    severity = "critical" if asset.asset_type in SENSITIVE_AI_ASSETS else "warning"
                    _add(
                        findings,
                        "SYNTHETIC_USE_SCOPE_NOT_EXPLICIT",
                        severity,
                        f"Synthetic-use authorization is not explicitly recorded for "
                        f"'{asset.asset_name}'.",
                        asset.asset_id,
                        permission.permission_id,
                    )
                    if severity == "critical":
                        valid = False

            if asset.subject_is_minor:
                if permission.guardian_authorization is not True:
                    _add(
                        findings,
                        "GUARDIAN_AUTHORIZATION_REQUIRED",
                        "critical",
                        f"The declared minor subject for '{asset.asset_name}' requires explicit recorded "
                        "guardian authorization.",
                        asset.asset_id,
                        permission.permission_id,
                    )
                    valid = False

            if not permission.evidence_reference:
                _add(
                    findings,
                    "EVIDENCE_REFERENCE_MISSING",
                    "warning",
                    f"No evidence reference is recorded for '{asset.asset_name}'.",
                    asset.asset_id,
                    permission.permission_id,
                )
            if not permission.evidence_type:
                _add(
                    findings,
                    "EVIDENCE_TYPE_MISSING",
                    "warning",
                    f"The evidence type is not identified for '{asset.asset_name}'.",
                    asset.asset_id,
                    permission.permission_id,
                )
            if permission.attribution_required and not permission.attribution_text:
                _add(
                    findings,
                    "ATTRIBUTION_TEXT_MISSING",
                    "warning",
                    f"Attribution is required for '{asset.asset_name}', but no required wording is recorded.",
                    asset.asset_id,
                    permission.permission_id,
                )

            if asset.ai_generated and asset.asset_type in SENSITIVE_AI_ASSETS:
                if not permission.evidence_reference or permission.evidence_type is None:
                    _add(
                        findings,
                        "SYNTHETIC_PERSONA_EXPLICIT_EVIDENCE_REQUIRED",
                        "critical",
                        f"AI-generated {asset.asset_type.value} use for '{asset.asset_name}' requires "
                        "an explicit evidence reference and evidence type.",
                        asset.asset_id,
                        permission.permission_id,
                    )
                    valid = False

            if valid:
                usable_grants.append(permission)

        if not usable_grants and not any(
            finding.asset_id == asset.asset_id and finding.severity == "critical"
            for finding in findings
        ):
            _add(
                findings,
                "NO_USABLE_GRANT",
                "warning",
                f"No fully usable granted permission is recorded for '{asset.asset_name}'.",
                asset.asset_id,
            )

    if action.release_context.synthetic_media_use and not any(asset.ai_generated for asset in action.assets):
        _add(
            findings,
            "SYNTHETIC_CONTEXT_WITHOUT_DECLARED_SYNTHETIC_ASSET",
            "warning",
            "The release context declares synthetic-media use, but no asset is marked as AI-generated or synthetically modified.",
        )

    if action.action_type in PUBLIC_ACTIONS and action.assets:
        declared_types = {asset.asset_type for asset in action.assets}
        if not declared_types.intersection(MEDIA_ASSETS):
            _add(
                findings,
                "PUBLIC_RELEASE_MEDIA_REVIEW_CONFIRMATION",
                "warning",
                "The public action contains no declared performer, music, footage, voice, or artwork "
                "asset. Confirm that the asset inventory is complete.",
            )

    if agent_analysis:
        declared_types = {asset.asset_type for asset in action.assets}
        seen: set[AssetType] = set()
        for hint in agent_analysis.asset_hints:
            if hint.asset_type in declared_types or hint.asset_type in seen or hint.confidence < 0.55:
                continue
            seen.add(hint.asset_type)
            _add(
                findings,
                "POSSIBLE_UNDECLARED_ASSET",
                "warning",
                f"The advisory agent detected possible {hint.asset_type.value} material ('{hint.phrase}') "
                "that is not represented in the asset inventory.",
            )

    critical_count = sum(item.severity == "critical" for item in findings)
    warning_count = sum(item.severity == "warning" for item in findings)
    if critical_count:
        outcome = ClearanceOutcome.BLOCKED
    elif warning_count:
        outcome = ClearanceOutcome.REVIEW_REQUIRED
    else:
        outcome = ClearanceOutcome.CLEARED
        _add(
            findings,
            "RECORDED_PERMISSIONS_APPEAR_SUFFICIENT",
            "info",
            "The supplied metadata contains a usable permission record for every declared asset and "
            "no unresolved scope condition was identified.",
        )

    total_assets = max(1, len(action.assets))
    blocked_assets = {
        finding.asset_id
        for finding in findings
        if finding.asset_id and finding.severity == "critical"
    }
    review_assets = {
        finding.asset_id
        for finding in findings
        if finding.asset_id and finding.severity == "warning"
    }
    covered_assets = max(0, len(action.assets) - len(blocked_assets) - len(review_assets - blocked_assets))
    base_score = round((covered_assets / total_assets) * 100)
    record_warnings = sum(item.severity == "warning" for item in findings)
    global_critical = sum(item.severity == "critical" and not item.asset_id for item in findings)
    coverage_score = max(0, min(100, base_score - min(25, record_warnings * 3) - global_critical * 20))

    return outcome, findings, coverage_score
