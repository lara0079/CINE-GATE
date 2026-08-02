from __future__ import annotations

import json
import re
from time import perf_counter

from app.config import Settings
from app.domain.models import AgentAnalysis, AgentStep, AssetHint, AssetType, ProductionAction


_KEYWORDS: dict[AssetType, tuple[str, ...]] = {
    AssetType.LIKENESS: (
        "likeness", "face", "actor", "performer", "digital double", "avatar", "deepfake"
    ),
    AssetType.VOICE: (
        "voice", "voice clone", "cloned voice", "narration", "dialogue", "dub", "dubbing"
    ),
    AssetType.MUSIC: ("music", "song", "score", "soundtrack", "composer", "recording"),
    AssetType.FOOTAGE: ("footage", "clip", "archive", "video", "film extract", "newsreel"),
    AssetType.SCRIPT: ("script", "screenplay", "dialogue text", "adaptation"),
    AssetType.ARTWORK: ("artwork", "poster", "illustration", "logo", "painting", "photograph"),
    AssetType.LOCATION: ("location", "property", "venue", "building interior", "private property"),
}


class RightsDiscoveryAgent:
    """Advisory asset discovery that cannot change rights or outcomes."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def analyse(self, action: ProductionAction) -> AgentAnalysis:
        started = perf_counter()
        if self.settings.agent_mode.lower() != "google":
            analysis = self._local(action, mode="local")
            analysis.total_duration_ms = max(1, int((perf_counter() - started) * 1000))
            analysis.model = "local-keyword-discovery"
            return analysis
        try:
            analysis = self._google(action)
            analysis.total_duration_ms = max(1, int((perf_counter() - started) * 1000))
            analysis.model = self.settings.gemini_model
            return analysis
        except Exception as exc:
            analysis = self._local(action, mode="google_fallback")
            analysis.total_duration_ms = max(1, int((perf_counter() - started) * 1000))
            analysis.model = self.settings.gemini_model
            analysis.fallback_used = True
            analysis.steps.append(
                AgentStep(
                    name="google_asset_discovery",
                    status="failed",
                    detail=(
                        "Google analysis failed; deterministic local discovery was used: "
                        f"{type(exc).__name__}"
                    ),
                    agent="rights-scout",
                    provider="google-gemini",
                    guardrail="Failure triggers a bounded local fallback; no permission is inferred.",
                )
            )
            return analysis

    def _google(self, action: ProductionAction) -> AgentAnalysis:
        from google import genai

        if self.settings.google_api_key:
            client = genai.Client(api_key=self.settings.google_api_key)
        else:
            if not self.settings.google_cloud_project:
                raise RuntimeError("GOOGLE_CLOUD_PROJECT is required for Vertex AI mode")
            client = genai.Client(
                vertexai=True,
                project=self.settings.google_cloud_project,
                location=self.settings.google_cloud_location,
            )

        prompt = {
            "role": "film production asset-discovery agent",
            "task": (
                "Identify rights-bearing asset types explicitly or strongly implied by the proposed action. "
                "Do not infer that permission exists, authenticate documents, or provide legal conclusions. "
                "Return only JSON with key asset_hints. Each item must contain asset_type, phrase, confidence, "
                "and rationale. Allowed asset_type values: "
                + ", ".join(asset.value for asset in AssetType)
            ),
            "action_type": action.action_type.value,
            "description": action.description,
            "release_context": action.release_context.model_dump(mode="json"),
            "declared_assets": [asset.model_dump(mode="json") for asset in action.assets],
        }
        response = client.models.generate_content(
            model=self.settings.gemini_model,
            contents=json.dumps(prompt, ensure_ascii=False),
            config={"response_mime_type": "application/json", "temperature": 0.1},
        )
        payload = json.loads(response.text or "{}")
        hints: list[AssetHint] = []
        for item in payload.get("asset_hints", []):
            try:
                hints.append(AssetHint.model_validate(item))
            except Exception:
                continue
        return AgentAnalysis(
            mode="google",
            asset_hints=hints[:12],
            steps=[
                AgentStep(
                    name="google_asset_discovery",
                    status="completed",
                    detail=f"Gemini returned {len(hints[:12])} advisory asset hint(s).",
                    agent="rights-scout",
                    provider="google-gemini",
                    guardrail="Discovery is advisory and cannot establish permission or change the outcome.",
                )
            ],
        )

    @staticmethod
    def _local(action: ProductionAction, mode: str) -> AgentAnalysis:
        text = action.description.lower()
        hints: list[AssetHint] = []
        for asset_type, keywords in _KEYWORDS.items():
            for keyword in keywords:
                match = re.search(rf"\b{re.escape(keyword)}\b", text)
                if match:
                    hints.append(
                        AssetHint(
                            asset_type=asset_type,
                            phrase=match.group(0),
                            confidence=0.78,
                            rationale=f"The action description contains the domain term '{match.group(0)}'.",
                        )
                    )
                    break
        return AgentAnalysis(
            mode=mode,  # type: ignore[arg-type]
            asset_hints=hints,
            steps=[
                AgentStep(
                    name="local_asset_discovery",
                    status="fallback" if mode == "google_fallback" else "completed",
                    detail=f"Keyword discovery returned {len(hints)} advisory asset hint(s).",
                    agent="rights-scout",
                    provider="local-deterministic",
                    guardrail="Discovery is advisory and cannot establish permission or change the outcome.",
                )
            ],
        )
