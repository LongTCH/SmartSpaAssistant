import json

import aiohttp
from app.configs import env_config
from pydantic import BaseModel


class ReRankResult(BaseModel):
    index: int
    relevance_score: float


jina_api_key = env_config.JINA_API_KEY


async def get_embeddings(texts: str | list[str]) -> list[list[float]]:
    """
    Get embeddings for a list of texts using Jina AI API

    Args:
        texts: List of text strings to embed

    Returns:
        JSON response from Jina AI containing embeddings
    """
    url = "https://api.jina.ai/v1/embeddings"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {jina_api_key}",
    }
    if isinstance(texts, str):
        texts = [texts]
    data = {
        "model": "jina-embeddings-v3",
        "truncate": True,
        "dimensions": 1024,
        "task": "text-matching",
        "input": texts,
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(
            url, headers=headers, data=json.dumps(data, ensure_ascii=False)
        ) as response:
            if response.status != 200:
                raise Exception(f"Error: {response.status}")
            json_response = await response.json()
            data = json_response["data"]
            return [item["embedding"] for item in data]


async def rerank(query: str, texts: list[str]) -> list[ReRankResult]:
    """
    Rerank text documents based on their relevance to a query using Jina AI API

    Args:
        query: The query string
        texts: List of text strings to rerank

    Returns:
        List of text strings reordered by relevance
    """
    url = "https://api.jina.ai/v1/rerank"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {jina_api_key}",
    }

    # Convert text strings to document dictionaries
    documents = [{"text": text} for text in texts]

    data = {
        "model": "jina-reranker-m0",
        "query": query,
        "documents": documents,
        "return_documents": False,
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(
            url, headers=headers, data=json.dumps(data, ensure_ascii=False)
        ) as response:
            if response.status != 200:
                raise Exception(f"Error: {response.status}")
            json_response = await response.json()
            results = json_response["results"]
            ranked_results = []
            for result in results:
                ranked_results.append(
                    ReRankResult(
                        index=result["index"], relevance_score=result["relevance_score"]
                    )
                )
            return ranked_results
