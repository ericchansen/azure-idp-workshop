"""Application configuration via environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuration loaded from environment variables / .env file."""

    # Azure AI Services (Foundry resource — supports both CU and DI)
    ai_services_endpoint: str = ""
    ai_services_key: str = ""  # Optional — uses DefaultAzureCredential if empty

    # Azure Storage
    storage_account_url: str = ""

    # CU model deployment names (must match Bicep deployment resource names)
    cu_completion_deployment: str = "gpt-4.1"
    cu_embedding_deployment: str = "text-embedding-3-large"

    # Runtime
    environment: str = "dev"
    log_level: str = "INFO"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
