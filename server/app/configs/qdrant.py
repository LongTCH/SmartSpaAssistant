from qdrant_client import QdrantClient
from app.configs import env_config
from qdrant_client.models import VectorParams, Distance

qdrant_client = QdrantClient(url=env_config.QDRANT_URL)
# Kiểm tra xem collection đã tồn tại chưa
if not qdrant_client.collection_exists(env_config.QDRANT_KNOWLEDGE_COLLECTION_NAME):
    # Định nghĩa cấu hình cho collection
    # Thay đổi size và distance nếu cần
    vectors_config = VectorParams(
        size=env_config.OLLAMA_EMBEDDINGS_DIMENSION, distance=Distance.COSINE)
    # Tạo collection mới
    qdrant_client.create_collection(
        collection_name=env_config.QDRANT_KNOWLEDGE_COLLECTION_NAME,
        vectors_config=vectors_config
    )
    print(
        f"Collection '{env_config.QDRANT_KNOWLEDGE_COLLECTION_NAME}' đã được tạo thành công.")
