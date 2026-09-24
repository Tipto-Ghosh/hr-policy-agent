from __future__ import annotations
 
from functools import lru_cache
from pathlib import Path
 
import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_GUARDRAILS_CONFIG_PATH = REPO_ROOT / "configs" / "guardrails.yaml"


class Settings(BaseSettings):
    """Environment-drived settings for the HR Agent application."""
    
    model_config = SettingsConfigDict(
        env_file = ".env",
        env_file_encoding = "utf-8",
        extra = "ignore"
    )
    
    # ingestion/parsing
    llama_parser_api_key: str = Field(
        default="",
        alias="LLAMA_PARSER_API_KEY",
    )
    
    # vector store
    pinecone_api_key: str = Field(
        default="",
        alias="PINECONE_API_KEY",
    )
    pinecone_index_name: str = Field(
        default = "hr-policy-agent"
    )
    pinecone_namespace: str = Field(
        default = "hr-policy-agent-namespace"
    )
    
    # embedding model
    embedding_model_name: str = Field(
        default = "sentence-transformers/all-MiniLM-L6-v2"
    )
    
    # llm
    groq_api_key: str = Field(
        default = "",
        alias = "GROQ_API_KEY"
    )
    groq_model_name: str = Field(
        default = "openai/gpt-oss-20b"
    )
    
    # web search
    tavily_api_key: str = Field(
        default = "",
        alias = "TAVILY_API_KEY"   
    )
    
    # paths
    data_raw_dir: Path = Path("data/raw")
    data_processed_dir: Path = Path("data/processed")
    memory_db_path: Path = Path("data/memory/agent_state_checkpoint.db")
    audit_db_path: Path = Path("data/audit/query_audit.db")
    
    # guardrails
    guardrails_config_path: Path = DEFAULT_GUARDRAILS_CONFIG_PATH


@lru_cache()
def get_settings() -> Settings:
    """Get the application settings."""
    return Settings()


class InjectionConfig(BaseModel):
    threshold: float = 0.5
    heuristic_markers: list[str] = Field(default_factory=list)
 
class SensitiveCaseConfig(BaseModel):
    markers: list[str] = Field(default_factory=list)

class RetryConfig(BaseModel):
    max_retries: int = 1

class PiiConfig(BaseModel):
    regex_patterns: dict[str, str] = Field(default_factory=dict)
    presidio_entities: list[str] = Field(default_factory=list)
    presidio_language: str = "en"
    presidio_score_threshold: float = 0.5

class OutputGuardConfig(BaseModel):
    citation_markers: list[str] = Field(default_factory=list)
    disclaimer: str = ""
    refusal_template: str = ""
 
 
class GuardrailsConfig(BaseModel):
    injection: InjectionConfig = InjectionConfig()
    sensitive_case: SensitiveCaseConfig = SensitiveCaseConfig()
    retry: RetryConfig = RetryConfig()
    pii: PiiConfig = PiiConfig()
    output_guard: OutputGuardConfig = OutputGuardConfig()
    

@lru_cache()
def get_guardrails_config(path: Path | None = None) -> GuardrailsConfig:
    """
    Load and cache the guardrails configuration from the specified YAML file.
    """
    resolved_path = path or get_settings().guardrails_config_path
    with open(resolved_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    
    return GuardrailsConfig.model_validate(raw)