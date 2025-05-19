import uuid

from app.configs import env_config
from app.configs.database import with_session
from app.dtos import ScriptChunkDto
from app.models import Script
from app.repositories import script_repository
from app.services.clients import jina
from app.services.clients.qdrant import create_qdrant_client
from app.utils.rag_utils import markdown_splitter
from fastembed import SparseTextEmbedding
from qdrant_client.http.models import PointStruct
from qdrant_client.models import (
    FieldCondition,
    Filter,
    FilterSelector,
    MatchAny,
    MatchValue,
)

sparse_embedding_model = SparseTextEmbedding(model_name="Qdrant/bm25")


def get_description_for_embedding(script: Script):
    description = script.description
    for s in script.related_scripts:
        description += f"\n{s.description}"
    return description


async def get_script_chunks(script: Script) -> list[ScriptChunkDto]:
    chunk_descriptions = await markdown_splitter(script.description)
    chunk_solutions = await markdown_splitter(script.solution)
    return [
        ScriptChunkDto(script_id=script.id, script_name=script.name, chunk=chunk)
        for chunk in chunk_descriptions + chunk_solutions
    ]


async def get_points_struct_for_embedding(
    script_chunks: list[ScriptChunkDto],
) -> list[PointStruct]:
    texts = [script_chunk.chunk for script_chunk in script_chunks]
    dense_embeddings: list[list[float]] = await jina.get_embeddings(texts)
    points = []
    for script_chunk, dense_embedding in zip(script_chunks, dense_embeddings):
        point = PointStruct(
            id=str(uuid.uuid4()),
            vector=dense_embedding,
            payload={
                "content": script_chunk.chunk,
                "script_id": script_chunk.script_id,
                "script_name": script_chunk.script_name,
            },
        )
        points.append(point)
    return points


async def get_scripts_points(scripts: list[Script]) -> list[PointStruct]:
    points: list[PointStruct] = []
    chunks: list[ScriptChunkDto] = []
    for script in scripts:
        script_chunks = await get_script_chunks(script)
        chunks.extend(script_chunks)
    batch_embedding_size = 100
    for i in range(0, len(chunks), batch_embedding_size):
        batch_chunks = chunks[i : i + batch_embedding_size]
        points.extend(await get_points_struct_for_embedding(batch_chunks))
    return points


async def batch_upsert_points(points: list[PointStruct], batch_size: int = 100):
    qdrant_client = create_qdrant_client()
    for i in range(0, len(points), batch_size):
        batch = points[i : i + batch_size]
        await qdrant_client.upsert(
            collection_name=env_config.QDRANT_SCRIPT_COLLECTION_NAME,
            points=batch,
        )


async def get_scripts_points_no_chunk(scripts: list[Script]):
    points: list[PointStruct] = []
    chunks: list[ScriptChunkDto] = []
    batch_embedding_size = 100
    for script in scripts:
        script_chunks = [
            ScriptChunkDto(
                script_id=script.id,
                script_name=script.name,
                chunk=f"{script.description}",
            )
        ]
        chunks.extend(script_chunks)
    for i in range(0, len(chunks), batch_embedding_size):
        batch_chunks = chunks[i : i + batch_embedding_size]
        points.extend(await get_points_struct_for_embedding(batch_chunks))
    return points


async def get_script_points_all(scripts: list[Script]):
    points: list[PointStruct] = []
    chunks: list[ScriptChunkDto] = []
    batch_embedding_size = 100
    for script in scripts:
        script_chunks = [
            ScriptChunkDto(
                script_id=script.id,
                script_name=script.name,
                chunk=f"{script.description}",
            )
        ]
        chunks.extend(script_chunks)
    for i in range(0, len(chunks), batch_embedding_size):
        batch_chunks = chunks[i : i + batch_embedding_size]
        points.extend(await get_points_struct_for_embedding(batch_chunks))
    return points


async def insert_script(script_id: str) -> None:
    script = await with_session(
        lambda db: script_repository.get_script_by_id(db, script_id)
    )
    points = await get_script_points_all([script])
    await batch_upsert_points(points)


async def insert_scripts(script_ids: list[str]) -> None:
    points = []  # Danh sách lưu trữ các điểm cần chèn hoặc cập nhật
    scripts = await with_session(
        lambda db: script_repository.get_scripts_by_ids(db, script_ids)
    )
    points = await get_script_points_all(scripts)
    await batch_upsert_points(points)


async def delete_scripts(script_ids: list[str]) -> None:
    qdrant_client = create_qdrant_client()
    result = await qdrant_client.delete(
        collection_name=env_config.QDRANT_SCRIPT_COLLECTION_NAME,
        points_selector=FilterSelector(
            filter=Filter(
                must=[FieldCondition(key="script_id", match=MatchAny(any=script_ids))]
            )
        ),
    )


async def delete_script(script_id: str) -> None:
    qdrant_client = create_qdrant_client()
    await qdrant_client.delete(
        collection_name=env_config.QDRANT_SCRIPT_COLLECTION_NAME,
        points_selector=FilterSelector(
            filter=Filter(
                must=[
                    FieldCondition(key="script_id", match=MatchValue(value=script_id))
                ]
            )
        ),
    )


async def update_script(script_id) -> None:
    await delete_script(script_id)
    await insert_script(script_id)


async def search_script_chunks(query: str, limit: int = 5) -> list[ScriptChunkDto]:
    client = create_qdrant_client()
    dense_embeddings = await jina.get_embeddings(query)
    search_result = await client.query_points(
        collection_name=env_config.QDRANT_SCRIPT_COLLECTION_NAME,
        query=dense_embeddings[0],
        limit=limit,
    )
    search_result = search_result.points
    script_ids = [point.payload["script_id"] for point in search_result]
    scripts = await with_session(
        lambda session: script_repository.get_scripts_by_ids(session, script_ids)
    )
    final_scripts = {}
    i = 0
    while i < limit:
        script_top_i = scripts[i]
        final_scripts[script_top_i.id] = ScriptChunkDto(
            script_id=script_top_i.id,
            script_name=script_top_i.name,
            chunk=f"{script_top_i.solution}",
        )
        related_scripts = script_top_i.related_scripts
        for related_script in related_scripts:
            if related_script.id not in final_scripts:
                final_scripts[related_script.id] = ScriptChunkDto(
                    script_id=related_script.id,
                    script_name=related_script.name,
                    chunk=f"""
When customer ask:
{related_script.description}
Then you can use this solution:
{related_script.solution}
-------------------------------\n""",
                )
        i += 1
    return list(final_scripts.values())
