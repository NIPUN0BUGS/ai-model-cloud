from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All secrets come from the environment. No defaults for secrets on purpose."""
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "production"
    database_url: str = ""
    redis_url: str = ""
    secret_key: str = Field(default="", min_length=0)
    api_key_pepper: str = Field(default="", min_length=0)
    default_ollama_url: str = "http://ollama:11434"
    cors_origins: str = ""
    session_ttl_hours: int = 168
    login_max_attempts: int = 5
    login_window_seconds: int = 900
    max_prompt_chars: int = 32000
    max_output_tokens: int = 4096
    request_timeout_seconds: int = 300
    max_concurrent_inference: int = 4
    bootstrap_admin_email: str = ""
    bootstrap_admin_password: str = ""
    smtp_host: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def smtp_enabled(self) -> bool:
        return bool(self.smtp_host)


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
