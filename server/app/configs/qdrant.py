from app.configs import env_config
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

qdrant_client = QdrantClient(url=env_config.QDRANT_URL)
qdrant_collections = [
    env_config.QDRANT_KNOWLEDGE_COLLECTION_NAME,
    env_config.QDRANT_SCRIPT_COLLECTION_NAME,
]
for collection in qdrant_collections:
    if not qdrant_client.collection_exists(collection):
        # Định nghĩa cấu hình cho collection
        # Thay đổi size và distance nếu cần
        vectors_config = VectorParams(
            size=env_config.OLLAMA_EMBEDDINGS_DIMENSION, distance=Distance.COSINE
        )
        # Tạo collection mới
        qdrant_client.create_collection(
            collection_name=collection,
            vectors_config=vectors_config,
        )
        print(f"Collection '{collection}' đã được tạo thành công.")
