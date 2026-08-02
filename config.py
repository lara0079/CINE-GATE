from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="CINE-GATE", validation_alias="CINE_GATE_APP_NAME")
    environment: str = Field(default="development", validation_alias="CINE_GATE_ENVIRONMENT")
    agent_mode: str = Field(default="local", validation_alias="CINE_GATE_AGENT_MODE")
    database_path: str = Field(default="data/cine_gate.db", validation_alias="CINE_GATE_DATABASE_PATH")
    google_cloud_project: str | None = Field(default=None, validation_alias="GOOGLE_CLOUD_PROJECT")
    google_cloud_location: str = Field(default="us-central1", validation_alias="GOOGLE_CLOUD_LOCATION")
    google_api_key: str | None = Field(default=None, validation_alias="GOOGLE_API_KEY")
    gemini_model: str = Field(default="gemini-3.5-flash", validation_alias="GEMINI_MODEL")
    agent_engine_resource_name: str | None = Field(
        default=None, validation_alias="CINE_GATE_AGENT_ENGINE_RESOURCE_NAME"
    )
    agent_workflow_version: str = Field(
        default="cine-gate-agentic-workflow-0.5", validation_alias="CINE_GATE_AGENT_WORKFLOW_VERSION"
    )

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
