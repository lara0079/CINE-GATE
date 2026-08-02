from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FindingDefinition:
    category: str
    title: str
    resolution: str


FINDING_CATALOG: dict[str, FindingDefinition] = {
    "NO_ASSETS_DECLARED": FindingDefinition(
        "inventory", "No assets declared", "Create a complete inventory of every rights-bearing asset used by the proposed action."
    ),
    "ASSET_WITHOUT_PERMISSION_RECORD": FindingDefinition(
        "permission", "Permission record missing", "Link a permission record to the asset or remove the asset from the proposed action."
    ),
    "PERMISSION_DENIED_OR_REVOKED": FindingDefinition(
        "permission", "Permission denied or revoked", "Do not use the asset unless a new, valid permission is obtained and separately recorded."
    ),
    "CONFLICTING_PERMISSION_RECORDS": FindingDefinition(
        "record_quality", "Conflicting permission states", "Reconcile the records and retain one authoritative, traceable status before review."
    ),
    "PERMISSION_UNRESOLVED": FindingDefinition(
        "permission", "Permission unresolved", "Obtain and record a final permission decision before release."
    ),
    "PERMISSION_NOT_YET_VALID": FindingDefinition(
        "time_scope", "Permission not yet valid", "Change the planned date or obtain permission that is valid on the intended date."
    ),
    "PERMISSION_EXPIRED": FindingDefinition(
        "time_scope", "Permission expired", "Renew or replace the permission before the planned action date."
    ),
    "USE_OUTSIDE_PERMISSION_SCOPE": FindingDefinition(
        "use_scope", "Use outside recorded scope", "Obtain permission covering the exact production action or change the proposed use."
    ),
    "TERRITORY_OUTSIDE_PERMISSION_SCOPE": FindingDefinition(
        "territory", "Territory outside recorded scope", "Restrict distribution to covered territories or obtain expanded territorial rights."
    ),
    "CHANNEL_OUTSIDE_PERMISSION_SCOPE": FindingDefinition(
        "channel", "Channel outside recorded scope", "Remove uncovered distribution channels or obtain permission for each requested channel."
    ),
    "CHANNEL_SCOPE_NOT_RECORDED": FindingDefinition(
        "channel", "Channel scope not recorded", "Record the permitted distribution channels in the source permission metadata."
    ),
    "COMMERCIAL_USE_NOT_ALLOWED": FindingDefinition(
        "commercial_scope", "Commercial use not allowed", "Remove commercial use or obtain explicit commercial-use permission."
    ),
    "COMMERCIAL_USE_SCOPE_UNKNOWN": FindingDefinition(
        "commercial_scope", "Commercial-use scope unknown", "Confirm and record whether commercial use is permitted."
    ),
    "MODIFICATION_NOT_ALLOWED": FindingDefinition(
        "modification_scope", "Modification not allowed", "Use the asset without modification or obtain adaptation rights."
    ),
    "MODIFICATION_SCOPE_UNKNOWN": FindingDefinition(
        "modification_scope", "Modification scope unknown", "Confirm and record whether editing, adaptation, or transformation is permitted."
    ),
    "SYNTHETIC_USE_NOT_ALLOWED": FindingDefinition(
        "synthetic_media", "Synthetic use not allowed", "Remove the synthetic use or obtain explicit permission for that use."
    ),
    "SYNTHETIC_USE_SCOPE_NOT_EXPLICIT": FindingDefinition(
        "synthetic_media", "Synthetic-use permission not explicit", "Record explicit permission for AI-generated or synthetically modified use."
    ),
    "GUARDIAN_AUTHORIZATION_REQUIRED": FindingDefinition(
        "minor_subject", "Guardian authorization required", "Record explicit authorization from the appropriate guardian before use."
    ),
    "EVIDENCE_REFERENCE_MISSING": FindingDefinition(
        "evidence", "Evidence reference missing", "Add a traceable reference to the supporting contract, consent, release, or license."
    ),
    "EVIDENCE_TYPE_MISSING": FindingDefinition(
        "evidence", "Evidence type missing", "Identify the type of supporting evidence in the permission record."
    ),
    "ATTRIBUTION_TEXT_MISSING": FindingDefinition(
        "attribution", "Required attribution text missing", "Record the exact credit wording before publication."
    ),
    "SYNTHETIC_PERSONA_EXPLICIT_EVIDENCE_REQUIRED": FindingDefinition(
        "synthetic_media", "Explicit synthetic-persona evidence required", "Attach a traceable consent or release reference covering the synthetic persona use."
    ),
    "NO_USABLE_GRANT": FindingDefinition(
        "permission", "No usable granted permission", "Resolve the permission scope and record at least one usable grant for the asset."
    ),
    "SYNTHETIC_CONTEXT_WITHOUT_DECLARED_SYNTHETIC_ASSET": FindingDefinition(
        "inventory", "Synthetic context without declared synthetic asset", "Confirm the inventory and mark every synthetically generated or modified asset."
    ),
    "PUBLIC_RELEASE_MEDIA_REVIEW_CONFIRMATION": FindingDefinition(
        "inventory", "Public-release inventory confirmation", "Confirm that performers, voices, music, footage, and artwork are fully represented."
    ),
    "POSSIBLE_UNDECLARED_ASSET": FindingDefinition(
        "agent_discovery", "Possible undeclared rights-bearing asset", "Review the advisory hint and add the asset if it is present in the production."
    ),
    "RECORDED_PERMISSIONS_APPEAR_SUFFICIENT": FindingDefinition(
        "clearance", "Recorded permissions appear sufficient", "Retain the evidence package and proceed only within the recorded scope."
    ),
}


def get_finding_definition(code: str) -> FindingDefinition:
    return FINDING_CATALOG.get(
        code,
        FindingDefinition(
            category="other",
            title=code.replace("_", " ").title(),
            resolution="Review the finding and document the corrective action taken.",
        ),
    )
