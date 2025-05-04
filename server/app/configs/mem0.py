from app.configs import env_config
from mem0 import Memory

config = {
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "collection_name": "agent_long_term_memory",
            "host": "localhost",
            "port": 6333,
            "embedding_model_dims": env_config.OLLAMA_EMBEDDINGS_DIMENSION,
        },
    },
    "embedder": {
        "provider": "ollama",
        "config": {
            "model": env_config.OLLAMA_EMBEDDINGS_MODEL,
            "ollama_base_url": "http://localhost:11434",
        },
    },
    "llm": {
        "provider": "gemini",
        "config": {
            "model": "gemini-2.0-flash",
            "temperature": 0.2,
            "max_tokens": 2000,
        },
    },
}

mem0_client = Memory.from_config(config)
