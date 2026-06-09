"""Application configuration via environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuration loaded from environment variables / .env file."""

    # Azure AI Services (Foundry resource — supports both CU and DI)
    ai_services_endpoint: str = ""
    ai_services_key: str = ""  # Optional — uses DefaultAzureCredential if empty

    # Azure Storage
    storage_account_url: str = ""

    # Optional admin token for analyzer create/update operations
    admin_api_key: str = ""

    # CU model names and deployment names (deployment names must match Azure resources)
    cu_completion_model: str = "gpt-5.2"
    cu_completion_deployment: str = "gpt-5.2"
    cu_embedding_model: str = "text-embedding-3-large"
    cu_embedding_deployment: str = "text-embedding-3-large"

    # Azure AI Search
    ais_endpoint: str = ""
    ais_key: str = ""  # Optional — uses DefaultAzureCredential if empty
    ais_index_name: str = "workshop-documents"

    # Runtime
    environment: str = "dev"
    log_level: str = "INFO"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
