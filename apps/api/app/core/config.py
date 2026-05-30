from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "local"
    app_secret_key: str = "dev-only-kuli-v2-secret-change-me"
    database_url: str = "sqlite:///./apps/api/data/kuli-v2.sqlite"
    redis_url: str = "redis://localhost:6379/0"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173"
    access_token_expire_minutes: int = 60 * 24
    object_storage_provider: str = "local"
    object_storage_endpoint: str = ""
    object_storage_bucket: str = "kuli-order-files"
    object_storage_region: str = "auto"
    object_storage_access_key_id: str = ""
    object_storage_secret_access_key: str = ""
    object_storage_public_base_url: str = ""
    object_storage_local_dir: str = "apps/api/data/uploads"
    object_storage_presign_expires_seconds: int = 3600
    llm_provider: str = "local-rules"
    llm_model: str = "local-rules"
    llm_api_key: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    openai_api_key: str = ""
    openai_model: str = "gpt-5.5"
    openai_base_url: str = "https://api.openai.com/v1"
    llm_timeout_seconds: int = 20
    embedding_model: str = "local-rules"
    vector_dimension: int = 1536
    knowledge_root: str = "apps/api/knowledge/docs"
    xiaoku_agent_enabled: bool = True
    xiaoku_require_citations: bool = True
    mail_provider: str = ""
    mail_from: str = ""
    mail_reply_to: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    email_verify_token_expire_minutes: int = 60
    password_reset_token_expire_minutes: int = 30
    notification_max_retries: int = 3

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def effective_llm_api_key(self) -> str:
        return self.llm_api_key or self.openai_api_key

    @property
    def effective_llm_model(self) -> str:
        if self.llm_model != "local-rules":
            return self.llm_model
        return self.openai_model if self.effective_llm_api_key else self.llm_model

    @property
    def effective_llm_provider(self) -> str:
        if self.llm_provider != "local-rules":
            return self.llm_provider
        return "openai-compatible" if self.effective_llm_api_key else self.llm_provider

    @property
    def effective_llm_base_url(self) -> str:
        return self.llm_base_url or self.openai_base_url


@lru_cache
def get_settings() -> Settings:
    return Settings()
