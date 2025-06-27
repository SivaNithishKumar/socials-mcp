from functools import lru_cache
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Application configuration pulled from environment variables or .env file."""

    app_name: str = Field("Social MCP", env="APP_NAME")
    debug: bool = Field(False, env="DEBUG")
    api_v1_prefix: str = Field("/v1", env="API_V1_PREFIX")

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings() 