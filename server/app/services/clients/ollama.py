import aiohttp
from app.configs import env_config

api_url = env_config.OLLAMA_API_URL
embeddings_model = env_config.OLLAMA_EMBEDDINGS_MODEL


async def get_ollama_embeddings(texts: str | list[str]) -> list[list[float]]:
    """Tạo embeddings cho văn bản bằng Ollama API."""
    payload = {
        "model": embeddings_model,
        "input": texts,
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(api_url, json=payload) as response:
            if response.status != 200:
                raise Exception(f"Error: {response.status}")
            json_response = await response.json()
            data = json_response["data"]
            return [item["embedding"] for item in data]
