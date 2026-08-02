from __future__ import annotations

import json
import os
import re
from typing import Any

from google.adk.agents import Agent, ParallelAgent, SequentialAgent


RIGHTS_TERMS = {
    "likeness": ("likeness", "face", "actor", "performer", "digital double", "avatar", "deepfake"),
    "voice": ("voice", "voice clone", "cloned voice", "narration", "dialogue", "dubbing"),
    "music": ("music", "song", "score", "soundtrack", "composer", "recording"),
    "footage": ("footage", "clip", "archive", "video", "film extract", "newsreel"),
    "script": ("script", "screenplay", "dialogue text", "adaptation"),
    "artwork": ("artwork", "poster", "illustration", "logo", "painting", "photograph"),
    "location": ("location", "property", "venue", "building interior", "private property"),
}

REQUIRED_METADATA = {
    "likeness": ["subject", "permitted use", "channel", "territory", "validity", "synthetic-use scope", "consent evidence"],
    "voice": ["speaker", "permitted use", "channel", "territory", "validity", "synthetic-use scope", "voice consent evidence"],
    "music": ["rights holder", "media/use scope", "channel", "territory", "term", "commercial scope", "license evidence"],
    "footage": ["source", "rights holder", "use scope", "territory", "license evidence"],
    "script": ["writer/rightsholder", "adaptation scope", "distribution scope", "agreement evidence"],
    "artwork": ["creator/rightsholder", "reproduction scope", "territory", "license evidence"],
    "location": ["property/controller", "filming or publication scope", "date", "release evidence"],
}


def identify_rights_categories(description: str) -> dict[str, Any]:
    """Return possible rights-bearing categories without determining permission."""
    text = description.lower()
    matches: list[dict[str, str]] = []
    for category, terms in RIGHTS_TERMS.items():
        found = next((term for term in terms if re.search(rf"\b{re.escape(term)}\b", text)), None)
        if found:
            matches.append({"category": category, "matched_phrase": found})
    return {
        "possible_rights_categories": matches,
        "boundary": "A category match is not proof of ownership, consent, or permission.",
    }


def list_required_metadata(asset_type: str) -> dict[str, Any]:
    """Return minimum metadata expected for a rights-bearing asset category."""
    category = asset_type.strip().lower()
    return {
        "asset_type": category,
        "expected_metadata": REQUIRED_METADATA.get(
            category,
            ["owner or subject", "permitted use", "territory", "validity", "evidence reference"],
        ),
        "boundary": "Metadata presence does not authenticate a document or establish legal clearance.",
    }


def inspect_declared_inventory(action_json: str) -> dict[str, Any]:
    """Summarize declared assets and permission records from a CINE-GATE action payload."""
    try:
        payload = json.loads(action_json)
    except json.JSONDecodeError:
        return {"error": "action_json is not valid JSON"}
    assets = payload.get("assets") or []
    permissions = payload.get("permissions") or []
    permission_assets = {str(item.get("asset_id")) for item in permissions if item.get("asset_id")}
    missing = [item.get("asset_id") for item in assets if item.get("asset_id") not in permission_assets]
    return {
        "declared_asset_count": len(assets),
        "permission_record_count": len(permissions),
        "asset_types": sorted({str(item.get("asset_type")) for item in assets if item.get("asset_type")}),
        "assets_without_permission_record": missing,
        "boundary": "This inventory check does not validate the contents or authenticity of evidence.",
    }


def state_final_boundary() -> dict[str, str]:
    """Return the non-negotiable CINE-GATE decision boundary."""
    return {
        "advisory_agents": "May discover categories, identify metadata gaps, and explain recorded findings.",
        "deterministic_gate": "Produces the recorded CLEARED, REVIEW_REQUIRED, or BLOCKED outcome.",
        "human_control": "A named reviewer records the final workflow decision.",
        "prohibited": "Agents may not invent permission, authenticate documents, grant legal clearance, or override a BLOCKED record.",
    }


MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")

rights_scout = Agent(
    model=MODEL,
    name="rights_scout",
    description="Discovers possible rights-bearing assets in a proposed media action.",
    instruction=(
        "Analyze the proposed media action. Use identify_rights_categories. Return concise JSON under "
        "rights_discovery with possible categories, matched phrases, uncertainty, and the stated boundary. "
        "Never infer that permission exists and never provide legal advice."
    ),
    tools=[identify_rights_categories],
    output_key="rights_discovery",
)

evidence_gap_scout = Agent(
    model=MODEL,
    name="evidence_gap_scout",
    description="Maps declared assets to expected permission metadata.",
    instruction=(
        "Inspect the supplied action JSON with inspect_declared_inventory. For each declared asset category, "
        "use list_required_metadata. Return concise JSON under evidence_gap_analysis. Do not authenticate "
        "evidence, interpret contracts, or determine final clearance."
    ),
    tools=[inspect_declared_inventory, list_required_metadata],
    output_key="evidence_gap_analysis",
)

parallel_discovery = ParallelAgent(
    name="parallel_rights_discovery",
    description="Runs rights discovery and evidence-gap analysis concurrently.",
    sub_agents=[rights_scout, evidence_gap_scout],
)

release_brief_agent = Agent(
    model=MODEL,
    name="release_brief_agent",
    description="Synthesizes an advisory production-rights brief for human review.",
    instruction=(
        "Synthesize the outputs in {rights_discovery} and {evidence_gap_analysis}. Call state_final_boundary. "
        "Return an English advisory brief with: detected categories, missing metadata questions, uncertainty, "
        "and the decision boundary. Do not issue CLEARED, REVIEW_REQUIRED, or BLOCKED; the FastAPI service's "
        "deterministic policy is the source of those outcomes."
    ),
    tools=[state_final_boundary],
    output_key="release_brief",
)

root_agent = SequentialAgent(
    name="cine_gate_agentic_workflow",
    description="A bounded multi-agent workflow for film-production rights discovery and review preparation.",
    sub_agents=[parallel_discovery, release_brief_agent],
)
