import asyncio
import uuid

import requests
from app.configs import env_config
from app.configs.cohere import cohere_client
from app.configs.qdrant import qdrant_client
from app.dtos import ChunkWrapper, FileMetaData, ProcessedFileData
from app.models import FileMetaData, Script
from app.repositories import script_repository
from app.services.integrations import google_service
from qdrant_client.http.models import PointStruct
from qdrant_client.models import (
    FieldCondition,
    Filter,
    FilterSelector,
    MatchAny,
    MatchValue,
)
from sentence_transformers import SentenceTransformer
from sqlalchemy.ext.asyncio import AsyncSession
from tqdm import tqdm


def delete_vectors_by_file_metadatas(file_metadatas: list[FileMetaData]) -> bool:
    file_ids = [file_metadata.id for file_metadata in file_metadatas]
    # Thực hiện xóa các điểm khớp với filter và nhận kết quả
    result = qdrant_client.delete(
        collection_name=env_config.QDRANT_KNOWLEDGE_COLLECTION_NAME,
        points_selector=FilterSelector(
            filter=Filter(
                must=[
                    FieldCondition(key="metadata.file_id", match=MatchAny(any=file_ids))
                ]
            )
        ),
    )

    # Kiểm tra trạng thái của kết quả
    if result.status == "completed":
        return True
    else:
        return False


def send_file_to_webhook(file_handle, mime_type, webhook_url, file_name):
    """Gửi tệp nhị phân đến webhook."""
    files = {"file": (file_name, file_handle, mime_type)}
    response = requests.post(webhook_url, files=files)
    return response


def get_file_downloaded_mime_type(file_metadata: FileMetaData) -> str:
    if file_metadata.mime_type == "application/vnd.google-apps.document":
        return "text/plain"
    elif file_metadata.mime_type == "application/vnd.google-apps.spreadsheet":
        return "text/csv"
    return file_metadata.mime_type


def insert_vectors_by_file_headers(
    file_headers, file_metadatas: list[FileMetaData]
) -> None:
    for i, file_metadata in tqdm(enumerate(file_metadatas), desc="Processing files"):
        # files.append(('files', (file_metadata.name, fh, mime_type)))
        response = send_file_to_webhook(
            file_handle=file_headers[i],
            mime_type=get_file_downloaded_mime_type(file_metadata),
            webhook_url=env_config.N8N_RAG_FILE_WEBHOOK_URL,
            file_name=file_metadata.id,
        )


def insert_vectors_by_files(file_metadatas: list[FileMetaData], drive_service) -> None:
    for file_metadata in file_metadatas:
        # Tải file từ Google Drive
        fh, mime_type = google_service.download_file(
            file_metadata.id, file_metadata.mime_type, drive_service
        )

        # files.append(('files', (file_metadata.name, fh, mime_type)))
        response = send_file_to_webhook(
            file_handle=fh,
            mime_type=mime_type,
            webhook_url=env_config.N8N_RAG_FILE_WEBHOOK_URL,
            file_name=file_metadata.id,
        )


async def insert_vectors_by_processed_file_data(
    file_datas: list[ProcessedFileData],
) -> None:
    points = []  # Danh sách lưu trữ các điểm cần chèn hoặc cập nhật
    chunk_wrappers: list[ChunkWrapper] = []

    # Chuyển tqdm sang một thread riêng để không chặn event loop
    def process_chunking():
        result = []
        for file_data in tqdm(file_datas, desc="Chunking"):
            text = file_data.get_text_for_embedding()
            result.extend(
                chunk_text_with_lines(
                    file_data.metadata.id, file_data.metadata.mime_type, text
                )
            )
        return result

    # Thực hiện chunking trong thread riêng
    chunk_wrappers = await asyncio.to_thread(process_chunking)

    # Sử dụng asyncio.gather để xử lý các embeddings song song
    embeddings_tasks = []
    for wrapper in chunk_wrappers:
        embeddings_tasks.append(get_ollama_embeddings(wrapper.get_content()))

    # Chờ tất cả các embedding tasks hoàn thành
    embeddings = await asyncio.gather(*embeddings_tasks)

    # Tạo các points từ embeddings đã có
    for i, wrapper in enumerate(chunk_wrappers):
        embedding = embeddings[i]
        if embedding:  # Đảm bảo embedding không phải là None
            point = PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload={
                    "content": wrapper.get_content(),
                    "metadata": wrapper.get_metadata(),
                },
            )
            points.append(point)
            # Batch upsert để tránh quá tải bộ nhớ
            if len(points) >= 10:
                qdrant_client.upsert(
                    collection_name=env_config.QDRANT_KNOWLEDGE_COLLECTION_NAME,
                    points=points,
                )
                points = []  # Đặt lại danh sách điểm sau khi chèn

    # Xử lý batch cuối cùng nếu còn lại
    if points:
        qdrant_client.upsert(
            collection_name=env_config.QDRANT_KNOWLEDGE_COLLECTION_NAME, points=points
        )


def chunk_text_with_lines(file_id, mime_type, text, chunk_size=500, overlap=50):
    """
    Splits the input text into chunks of specified size with a given overlap,
    and accurately tracks the starting and ending line numbers for each chunk.

    Args:
        file_id (str): ID of the file.
        mime_type (str): MIME type of the file.
        text (str): The input text to be split.
        chunk_size (int): The maximum number of characters in each chunk.
        overlap (int): The number of characters to overlap between chunks.

    Returns:
        list of ChunkWrapper: A list of ChunkWrapper instances containing chunked text and metadata.
    """
    if not text:
        return []

    # Split text into lines to track line numbers
    lines = text.splitlines()

    # Create a map of character positions to line numbers
    char_to_line = {}
    pos = 0
    for i, line in enumerate(lines):
        for _ in range(len(line) + 1):  # +1 for the newline character
            char_to_line[pos] = i
            pos += 1

    # Create chunks
    chunks = []
    start_pos = 0

    # Make sure the overlap is smaller than the chunk size to prevent infinite loops
    overlap = min(overlap, chunk_size - 1)

    while start_pos < len(text):
        # Calculate end position with simple chunking
        end_pos = min(start_pos + chunk_size, len(text))

        # Extract the chunk text
        chunk_text = text[start_pos:end_pos]

        # Find the line numbers
        start_line = char_to_line.get(start_pos, len(lines) - 1)
        end_line = char_to_line.get(end_pos - 1, len(lines) - 1)

        # Create chunk wrapper
        chunk = ChunkWrapper(
            file_id=file_id,
            content=chunk_text,
            start_line=start_line + 1,  # Convert to 1-based index
            end_line=end_line + 1,  # Convert to 1-based index
            blob_type=mime_type,
        )
        chunks.append(chunk)

        # Move to next chunk position with overlap
        start_pos = end_pos - overlap

        # If we've reached the end or we're not making progress, break
        if start_pos >= len(text) or end_pos >= len(text):
            break

        # Safety check: if we're not advancing, force advancement
        if start_pos + chunk_size <= end_pos:
            start_pos = end_pos + 1
            if start_pos >= len(text):
                break

    return chunks


def get_detailed_instruct(query: str) -> str:
    return f"Instruct: Given a description about current conversation's situation, retrieve relevant scripts that matching with this description\nQuery: {query}"


async def get_ollama_embeddings(text):
    """Tạo embeddings cho văn bản bằng Ollama API."""

    # Đặt payload cho API request
    payload = {
        # Tên mô hình của Ollama (thay đổi theo mô hình bạn muốn sử dụng)
        "model": "jeffh/intfloat-multilingual-e5-large-instruct:f16",
        "input": get_detailed_instruct(text),
    }

    # Chuyển HTTP request sang một thread riêng để không chặn event loop
    def make_request():
        response = requests.post(env_config.OLLAMA_API_URL, json=payload)
        if response.status_code == 200:
            return response.json()["data"][0]["embedding"]
        else:
            print("Error:", response.text)
            return None

    # Sử dụng asyncio.to_thread để thực hiện request trong thread riêng
    return await asyncio.to_thread(make_request)


def get_description_for_embedding(scripts: list[Script] = []):
    description = ""
    for script in scripts:
        description += f"{script.description}\n"
    return description


async def get_point_struct_for_embedding(
    script_id, script_name, text: str
) -> PointStruct:
    embedding = await get_ollama_embeddings(text)
    point = PointStruct(
        id=str(uuid.uuid4()),
        vector=embedding,
        payload={
            "content": text,
            "metadata": {
                "script_id": script_id,
                "script_name": script_name,
            },
        },
    )
    return point


async def insert_script(db: AsyncSession, script_id: str) -> None:
    points = []
    script = await script_repository.get_script_by_id(db, script_id)
    attach_scripts = await script_repository.get_attached_to_scripts(db, script_id)
    description = get_description_for_embedding([script].extend(attach_scripts))
    point = await get_point_struct_for_embedding(script_id, script.name, description)
    points.append(point)

    related_scripts = script.related_scripts
    for s in related_scripts:
        attach_scripts = await script_repository.get_attached_to_scripts(db, s.id)
        if not attach_scripts:
            attach_scripts = []
        description = get_description_for_embedding([s].extend(attach_scripts))
        point = await get_point_struct_for_embedding(s.id, s.name, description)
        points.append(point)
    # Chèn hoặc cập nhật các điểm vào Qdrant
    qdrant_client.upsert(
        collection_name=env_config.QDRANT_SCRIPT_COLLECTION_NAME,
        points=points,
    )


async def insert_scripts(db: AsyncSession, script_ids: list[str]) -> None:
    # convert script_ids list to set
    script_ids_set = set(script_ids)
    for script_id in script_ids:
        related_scripts = await script_repository.get_related_scripts(db, script_id)
        related_script_ids = [s.id for s in related_scripts]
        script_ids_set.update(related_script_ids)

    script_ids = list(script_ids_set)
    points = []  # Danh sách lưu trữ các điểm cần chèn hoặc cập nhật
    for script_id in script_ids:
        script = await script_repository.get_script_by_id(db, script_id)
        attach_scripts = await script_repository.get_attached_to_scripts(db, script_id)
        if not attach_scripts:
            attach_scripts = []
        combined_scripts = [script] + attach_scripts
        description = get_description_for_embedding(combined_scripts)
        point = await get_point_struct_for_embedding(
            script_id, script.name, description
        )
        points.append(point)
    if points:
        qdrant_client.upsert(
            collection_name=env_config.QDRANT_SCRIPT_COLLECTION_NAME, points=points
        )


async def delete_scripts(script_ids: list[str]) -> None:
    # Thực hiện xóa các điểm khớp với filter và nhận kết quả
    result = qdrant_client.delete(
        collection_name=env_config.QDRANT_SCRIPT_COLLECTION_NAME,
        points_selector=FilterSelector(
            filter=Filter(
                must=[
                    FieldCondition(
                        key="metadata.script_id", match=MatchAny(any=script_ids)
                    )
                ]
            )
        ),
    )

    # Kiểm tra trạng thái của kết quả
    if result.status == "completed":
        return True
    else:
        return False


async def delete_script(script_id: str) -> None:
    # Thực hiện xóa các điểm khớp với filter và nhận kết quả
    result = qdrant_client.delete(
        collection_name=env_config.QDRANT_SCRIPT_COLLECTION_NAME,
        points_selector=FilterSelector(
            filter=Filter(
                must=[
                    FieldCondition(
                        key="metadata.script_id", match=MatchValue(value=script_id)
                    )
                ]
            )
        ),
    )

    # Kiểm tra trạng thái của kết quả
    if result.status == "completed":
        return True
    else:
        return False


async def update_script(db: AsyncSession, script_id) -> None:
    await delete_script(script_id)
    await insert_script(db, script_id)


async def get_hunggingface_embeddings(inputs):
    model = SentenceTransformer("vietnamese-embedding-local")
    return model.encode(inputs)


async def get_similar_scripts(db, input_text: str, limit: int = 5) -> list[dict]:
    """Truy vấn các vector từ Qdrant dựa trên văn bản đầu vào."""
    embedding = await get_ollama_embeddings(input_text)
    results = qdrant_client.search(
        collection_name=env_config.QDRANT_SCRIPT_COLLECTION_NAME,
        query_vector=embedding,
        limit=limit,
    )
    script_ids = [result.payload["metadata"]["script_id"] for result in results]
    scripts = await script_repository.get_scripts_by_ids(db, script_ids)
    map_id_to_script = {script.id: script for script in scripts}
    for script in scripts:
        for s in script.related_scripts:
            map_id_to_script[s.id] = s

    scripts = map_id_to_script.values()
    scripts_dict = [script.to_dict() for script in scripts]
    return scripts_dict
    if len(scripts_dict) == limit:
        return scripts_dict
    scripts_text = [script.description for script in scripts]
    response = cohere_client.rerank(
        model="rerank-v3.5", query=input_text, documents=scripts_text, top_n=limit
    )
    indexes = [result.index for result in response.results]
    similar_scripts = [scripts_dict[i] for i in indexes]
    return similar_scripts
