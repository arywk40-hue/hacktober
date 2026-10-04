from pathlib import Path
from urllib.parse import urlparse

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", env_prefix="CITETUTOR_")
    ollama_url: str = "http://127.0.0.1:11434"
    generator_model: str = "gemma3:4b"
    verifier_model: str = "qwen2.5:3b"
    embedding_model: str = "nomic-embed-text"
    data_dir: Path = Path("data")
    model_context: int = Field(default=4096, ge=4096, le=32768)
    model_max_tokens: int = Field(default=1000, ge=256, le=4096)
    model_timeout: float = Field(default=240, gt=0)
    retrieval_top_k: int = Field(default=4, ge=1, le=8)
    max_upload_mb: int = Field(default=30, ge=1, le=100)
    sentry_dsn: SecretStr = SecretStr("")
    sentry_traces_sample_rate: float = Field(default=1.0, ge=0, le=1)

    @model_validator(mode="after")
    def local_only(self):
        url = urlparse(self.ollama_url)
        if (url.scheme != "http" or url.hostname not in {"localhost", "127.0.0.1", "::1"}
                or url.username or url.password or url.path not in {"", "/"}
                or url.query or url.fragment):
            raise ValueError("Ollama must run at an HTTP loopback address on this laptop")
        for tag in (self.generator_model, self.verifier_model, self.embedding_model):
            if not tag.strip() or "cloud" in tag.casefold():
                raise ValueError("Use installed local model weights, never cloud models")
        return self

    @property
    def database_url(self):
        return "sqlite:///" + str((self.data_dir / "citetutor.db").resolve())
