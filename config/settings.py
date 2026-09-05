from pydantic_settings import BaseSettings, SettingsConfigDict

langfuse_public_key: str | None = None
langfuse_secret_key: str | None = None
langfuse_host: str = "https://cloud.langfuse.com"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    groq_api_key: str
    gemini_api_key: str | None = None
    groq_model: str = "openai/gpt-oss-20b"
    flask_secret_key: str = "dev-secret-change-me"
    environment: str = "development"
    enable_reranker: bool = True


settings = Settings()