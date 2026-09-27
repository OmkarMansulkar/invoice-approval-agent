"""
Centralized settings. Everything the app needs from the environment lives here,
so no other module reaches into os.environ directly.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM
    llm_provider: str = "mock"       # groq | openai | mock
    groq_api_key: str = ""
    openai_api_key: str = ""
    llm_model: str = "llama-3.1-8b-instant"
    mock_mode: bool = True

    # DB
    database_url: str = "sqlite:///./invoice_agent.db"

    # Auth
    api_key: str = "demo-secret-key"


settings = Settings()
