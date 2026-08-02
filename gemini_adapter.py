from __future__ import annotations

import json
from dataclasses import dataclass
from time import perf_counter

from app.config import Settings
from app.domain.models import ClearanceFinding, ClearanceOutcome, ProductionAction


@dataclass(frozen=True)
class AgentNarrative:
    summary: str
    recommended_next_step: str
    mode: str
    duration_ms: int = 0
    provider: str = "local-deterministic"


class GeminiNarrativeAdapter:
    """Explain deterministic findings without changing the decision."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def explain(
        self,
        action: ProductionAction,
        outcome: ClearanceOutcome,
        findings: list[ClearanceFinding],
    ) -> AgentNarrative:
        started = perf_counter()
        if self.settings.agent_mode.lower() != "google":
            narrative = self._local_explanation(action, outcome, findings, "local")
            return AgentNarrative(
                summary=narrative.summary,
                recommended_next_step=narrative.recommended_next_step,
                mode=narrative.mode,
                duration_ms=max(1, int((perf_counter() - started) * 1000)),
                provider="local-deterministic",
            )

        try:
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
                "role": "film production rights-clearance explanation agent",
                "instruction": (
                    "Explain the supplied deterministic outcome and findings. Do not change the outcome, "
                    "invent permissions, authenticate evidence, or provide legal advice. Return JSON with "
                    "summary and recommended_next_step."
                ),
                "outcome": outcome.value,
                "action": action.model_dump(mode="json"),
                "findings": [finding.model_dump(mode="json") for finding in findings],
            }
            response = client.models.generate_content(
                model=self.settings.gemini_model,
                contents=json.dumps(prompt, ensure_ascii=False),
                config={"response_mime_type": "application/json", "temperature": 0.1},
            )
            payload = json.loads(response.text or "{}")
            summary = str(payload.get("summary") or "The supplied record requires review.")
            next_step = str(
                payload.get("recommended_next_step")
                or "Resolve the listed findings before the action proceeds."
            )
            return AgentNarrative(
                summary=summary,
                recommended_next_step=next_step,
                mode="google",
                duration_ms=max(1, int((perf_counter() - started) * 1000)),
                provider="google-gemini",
            )
        except Exception:
            narrative = self._local_explanation(action, outcome, findings, "google_fallback")
            return AgentNarrative(
                summary=narrative.summary,
                recommended_next_step=narrative.recommended_next_step,
                mode=narrative.mode,
                duration_ms=max(1, int((perf_counter() - started) * 1000)),
                provider="google-fallback",
            )

    @staticmethod
    def _local_explanation(
        action: ProductionAction,
        outcome: ClearanceOutcome,
        findings: list[ClearanceFinding],
        mode: str,
    ) -> AgentNarrative:
        critical = sum(finding.severity == "critical" for finding in findings)
        warnings = sum(finding.severity == "warning" for finding in findings)
        action_label = action.action_type.value.replace("_", " ")
        if outcome == ClearanceOutcome.BLOCKED:
            summary = f"The proposed {action_label} has {critical} blocking rights condition(s)."
            next_step = "Do not proceed. Correct the asset inventory or permission record, then run a new review."
        elif outcome == ClearanceOutcome.REVIEW_REQUIRED:
            summary = f"The proposed {action_label} has {warnings} unresolved clearance item(s)."
            next_step = "Send the record to a qualified production reviewer and resolve every warning before release."
        else:
            summary = "The supplied metadata contains no identified blocking or unresolved rights condition."
            next_step = "A designated production reviewer may confirm the record and proceed within the documented scope."
        return AgentNarrative(summary=summary, recommended_next_step=next_step, mode=mode)
