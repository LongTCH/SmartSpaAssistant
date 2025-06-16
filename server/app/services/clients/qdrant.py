from app.configs import env_config
from app.utils import asyncio_utils
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, Modifier, SparseVectorParams, VectorParams


def create_qdrant_client() -> AsyncQdrantClient:
    """Factory function to create a new Qdrant client instance."""
    return AsyncQdrantClient(url=env_config.QDRANT_URL, prefer_grpc=True)


async def init_qdrant():
    client = create_qdrant_client()

    if not await client.collection_exists(env_config.QDRANT_SCRIPT_COLLECTION_NAME):
        await client.create_collection(
            collection_name=env_config.QDRANT_SCRIPT_COLLECTION_NAME,
            vectors_config={"jina": VectorParams(size=1024, distance=Distance.COSINE)},
            sparse_vectors_config={"bm25": SparseVectorParams(modifier=Modifier.IDF)},
        )

    if not await client.collection_exists(env_config.QDRANT_SHEET_COLLECTION_NAME):
        await client.create_collection(
            collection_name=env_config.QDRANT_SHEET_COLLECTION_NAME,
            vectors_config={},
            sparse_vectors_config={"bm25": SparseVectorParams(modifier=Modifier.IDF)},
        )


asyncio_utils.run_async(init_qdrant())
