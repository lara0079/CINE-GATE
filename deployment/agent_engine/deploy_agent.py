from __future__ import annotations

import os

import vertexai
from vertexai import agent_engines

from cine_gate_agent.agent import root_agent


def required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} is required")
    return value


def main() -> None:
    project = required("GOOGLE_CLOUD_PROJECT")
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    staging_bucket = required("GOOGLE_CLOUD_STAGING_BUCKET")

    client = vertexai.Client(project=project, location=location)
    adk_app = agent_engines.AdkApp(
        agent=root_agent,
        app_name="cine-gate-rights-discovery",
        enable_tracing=True,
    )
    remote_agent = client.agent_engines.create(
        agent=adk_app,
        config={
            "staging_bucket": staging_bucket,
            "requirements": ["google-cloud-aiplatform[adk,agent_engines]>=1.112.0"],
            "extra_packages": ["./cine_gate_agent"],
            "env_vars": {
                "GEMINI_MODEL": os.getenv("GEMINI_MODEL", "gemini-3.5-flash"),
                "GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY": "true",
            },
        },
    )
    print(remote_agent.resource_name)


if __name__ == "__main__":
    main()
