from __future__ import annotations

from collections import Counter

from app.domain.models import (
    ClearanceFinding,
    ProductionAction,
    ReleaseReadiness,
    RiskSignal,
    WorkflowMetric,
)


def _level(score: int) -> str:
    if score <= 25:
        return "low"
    if score <= 60:
        return "medium"
    return "high"


def _signal(name: str, score: int, rationale: str) -> RiskSignal:
    bounded = max(0, min(100, int(score)))
    return RiskSignal(name=name, score=bounded, level=_level(bounded), rationale=rationale)


def build_risk_profile(
    action: ProductionAction,
    findings: list[ClearanceFinding],
    readiness: ReleaseReadiness,
) -> list[RiskSignal]:
    codes = Counter(f.code for f in findings)
    categories = Counter(f.category for f in findings)

    scope_findings = sum(
        count
        for category, count in categories.items()
        if category in {"scope", "territory", "channel", "commercial", "modification", "attribution"}
    )
    temporal_findings = sum(
        count for code, count in codes.items() if any(term in code for term in ("EXPIRED", "NOT_YET", "DATE", "VALID"))
    )
    synthetic_findings = sum(
        count for code, count in codes.items() if any(term in code for term in ("SYNTHETIC", "VOICE", "LIKENESS"))
    )

    synthetic_base = 15 if action.release_context.synthetic_media_use else 0
    return [
        _signal(
            "Rights coverage",
            100 - readiness.asset_coverage_percent,
            f"{readiness.covered_assets} of {readiness.declared_assets} declared assets are covered by the supplied records.",
        ),
        _signal(
            "Evidence completeness",
            100 - readiness.evidence_completeness_percent,
            f"{readiness.evidence_references} evidence references and {readiness.evidence_fingerprints} fingerprints were supplied.",
        ),
        _signal(
            "Scope alignment",
            min(100, scope_findings * 25),
            f"{scope_findings} finding(s) concern use, channel, territory, commercial, modification, or attribution scope.",
        ),
        _signal(
            "Temporal validity",
            min(100, temporal_findings * 35),
            f"{temporal_findings} finding(s) concern validity dates or timing.",
        ),
        _signal(
            "Synthetic-media exposure",
            min(100, synthetic_base + synthetic_findings * 25),
            (
                "Synthetic-media use is declared; explicit likeness and voice scope must be checked."
                if action.release_context.synthetic_media_use
                else "Synthetic-media use is not declared for this action."
            ),
        ),
    ]


def build_workflow_metrics(
    action: ProductionAction,
    findings: list[ClearanceFinding],
    readiness: ReleaseReadiness,
    hint_count: int,
) -> list[WorkflowMetric]:
    exception_count = readiness.blocking_findings + readiness.warning_findings
    return [
        WorkflowMetric(
            name="Declared assets",
            value=len(action.assets),
            unit="assets",
            description="Rights-bearing assets supplied to the review.",
        ),
        WorkflowMetric(
            name="Permission records",
            value=len(action.permissions),
            unit="records",
            description="Permission metadata records mapped to declared assets.",
        ),
        WorkflowMetric(
            name="Agent discoveries",
            value=hint_count,
            unit="hints",
            description="Advisory rights-bearing categories found in the action description.",
        ),
        WorkflowMetric(
            name="Exceptions routed",
            value=exception_count,
            unit="findings",
            description="Blocking and warning findings routed into the review workflow.",
        ),
        WorkflowMetric(
            name="Release channels",
            value=len(action.release_context.distribution_channels),
            unit="channels",
            description="Distribution channels tested against supplied permission scope.",
        ),
        WorkflowMetric(
            name="Coverage",
            value=readiness.asset_coverage_percent,
            unit="%",
            description="Share of declared assets with a covered matrix status.",
        ),
    ]
