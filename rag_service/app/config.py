"""
RAG Service Configuration
Author: Kanwarraj Singh

Central configuration for the RAG service.
All settings can be overridden via environment variables.
"""

import os
from pathlib import Path
from dataclasses import dataclass

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

@dataclass
class Config:
    """RAG Service Configuration"""
    
    # Service settings
    RAG_SERVICE_HOST: str = "127.0.0.1"
    RAG_SERVICE_PORT: int = 8000
    
    # LLM Server (llama-server)
    LLAMA_SERVER_URL: str = "http://127.0.0.1:7777"
    
    # Database paths
    LANCEDB_PATH: str = str(DATA_DIR / "lancedb")
    SQLITE_PATH: str = str(DATA_DIR / "documents.db")
    
    # Embedding model (runs locally on CPU)
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DEVICE: str = "cpu"  # "cpu", "cuda", or "mps" for Mac
    
    # Document processing
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    
    # Retrieval settings
    TOP_K_RESULTS: int = 5
    SIMILARITY_THRESHOLD: float = 0.3  # Minimum similarity score
    
    # Collection/Table name in LanceDB
    DEFAULT_COLLECTION: str = "documents"
    
    def __post_init__(self):
        """Load overrides from environment variables"""
        for field in self.__dataclass_fields__:
            env_value = os.getenv(field)
            if env_value is not None:
                field_type = type(getattr(self, field))
                if field_type == int:
                    setattr(self, field, int(env_value))
                elif field_type == float:
                    setattr(self, field, float(env_value))
                else:
                    setattr(self, field, env_value)


# Global config instance
config = Config()


# Ensure data directory exists
DATA_DIR.mkdir(parents=True, exist_ok=True)
