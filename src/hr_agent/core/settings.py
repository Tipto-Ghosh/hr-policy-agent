from __future__ import annotations
 
from functools import lru_cache
from pathlib import Path
 
import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
import torch


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_GUARDRAILS_CONFIG_PATH = REPO_ROOT / "configs" / "guardrails.yaml"
DEFAULT_CHUNKING_CONFIG_PATH = REPO_ROOT / "configs" / "chunking.yaml"
DEFAULT_MODELS_CONFIG_PATH = REPO_ROOT / "configs" / "models.yaml"
DEFAULT_QUERY_ANALYSIS_CONFIG_PATH = REPO_ROOT / "configs" / "query_analysis.yaml"
CHAT_HISTORY_CONFIG_PATH = REPO_ROOT / "configs" / "chat_history.yaml"


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
    embedding_model_kwargs: dict = Field(
        default_factory=lambda: {"device": "cpu" if not torch.cuda.is_available() else "cuda"}
    )
    embedding_model_encode_kwargs: dict = Field(
        default_factory=lambda: {"normalize_embeddings": True}
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
    
    # pii / presidio
    spacy_model_name: str = Field(
        default = "en_core_web_sm"
    )
    
    # paths
    data_raw_dir: Path = Path("data/raw")
    data_processed_dir: Path = Path("data/processed")
    memory_db_path: Path = Path("data/memory/agent_state_checkpoint.db")
    audit_db_path: Path = Path("data/audit/query_audit.db")
    
    # guardrails
    guardrails_config_path: Path = DEFAULT_GUARDRAILS_CONFIG_PATH
    # chunking
    chunking_config_path: Path = DEFAULT_CHUNKING_CONFIG_PATH
    # models
    models_config_path: Path = DEFAULT_MODELS_CONFIG_PATH
    # query analysis
    query_analysis_config_path: Path = DEFAULT_QUERY_ANALYSIS_CONFIG_PATH
    # chat history
    chat_history_config_path: Path = CHAT_HISTORY_CONFIG_PATH

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

# Chunking config
class LengthConfig(BaseModel):
    min_chars: int = 30
    max_chars: int = 2200
    orphan_body_threshold_chars: int = 15

class SplittingConfig(BaseModel):
    chunk_size: int = 2000
    chunk_overlap: int = 200

class HeaderRegexConfig(BaseModel):
    section: str
    subsection: str
    subsubsection: str
    subsubsubsection: str

class ChunkingConfig(BaseModel):
    length: LengthConfig = Field(default_factory=LengthConfig)
    splitting: SplittingConfig = Field(default_factory=SplittingConfig)
    header_regexes: HeaderRegexConfig

@lru_cache()
def get_chunking_config(path: Path | None = None) -> ChunkingConfig:
    """
    Load and cache the chunking configuration from the specified YAML file.
    """
    resolved_path = path or get_settings().chunking_config_path
    with open(resolved_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    
    return ChunkingConfig.model_validate(raw)

class ModelPricing(BaseModel):
    provider: str = ""
    input_cost_per_1k_usd: float = 0.0
    output_cost_per_1k_usd: float = 0.0

class ToolPricing(BaseModel):
    cost_per_call_usd: float = 0.0

class ModelsConfig(BaseModel):
    models: dict[str, ModelPricing] = Field(default_factory=dict)
    tools: dict[str, ToolPricing] = Field(default_factory=dict)
    
@lru_cache()
def get_models_config(path: Path | None = None) -> ModelsConfig:
    """
    Load and cache the models configuration from the specified YAML file.
    """
    resolved_path = path or get_settings().models_config_path
    with open(resolved_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    
    return ModelsConfig.model_validate(raw)


class QueryAnalysisConfig(BaseModel):
    max_turns: int = 4
    model_name: str = "openai/gpt-oss-20b"
    prompt: str = (
        "Given the conversation history and a follow-up question, rewrite "
        "the follow-up question as a standalone question that can be "
        "understood WITHOUT the conversation history. Resolve pronouns and "
        "implicit references (e.g. \"their\", \"it\", \"that policy\") using "
        "the history.\n\n"
        "Rules:\n"
        "- If the follow-up question is already standalone, return it UNCHANGED.\n"
        "- Do NOT answer the question.\n"
        "- Do NOT add information that isn't implied by the history.\n"
        "- Return ONLY the rewritten question, nothing else.\n\n"
        "Conversation history:\n{history}\n\n"
        "Follow-up question: {question}\n\n"
        "Standalone question:"
    )
    
    
@lru_cache()
def get_query_analysis_config(path: Path | None = None) -> QueryAnalysisConfig:
    """
    Load and cache the query analysis configuration from the specified YAML file.
    """
    resolved_path = path or get_settings().query_analysis_config_path
    with open(resolved_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    
    return QueryAnalysisConfig.model_validate(raw)

def get_chat_history_config(path: Path | None = None) -> dict:
    """
    Load and cache the chat history configuration from the specified YAML file.
    """
    resolved_path = path or get_settings().chat_history_config_path
    with open(resolved_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    
    return raw