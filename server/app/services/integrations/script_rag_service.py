import uuid
from typing import Iterable

from app.configs import env_config
from app.configs.database import async_session, with_session
from app.dtos import ScriptChunkDto
from app.models import Script
from app.repositories import script_repository
from app.services.clients import jina
from app.services.clients.qdrant import create_qdrant_client
from app.utils.rag_utils import markdown_splitter
from fastembed import SparseEmbedding, SparseTextEmbedding
from qdrant_client import models
from qdrant_client.http.models import PointStruct, ScoredPoint
from qdrant_client.models import (
    FieldCondition,
    Filter,
    FilterSelector,
    MatchAny,
    MatchValue,
    SparseVector,
)

sparse_embedding_model = SparseTextEmbedding(model_name="Qdrant/bm25")


def get_description_for_embedding(script: Script):
    description = script.description
    for s in script.related_scripts:
        description += f"\n{s.description}"
    return description


async def get_points_struct_for_embedding(
    script_chunks: list[ScriptChunkDto],
) -> list[PointStruct]:
    texts = [script_chunk.chunk for script_chunk in script_chunks]
    dense_embeddings: list[list[float]] = await jina.get_embeddings(texts)
    sparse_embeddings: list[SparseEmbedding] = list(sparse_embedding_model.embed(texts))
    points = []
    for script_chunk, dense_embedding, sparse_embedding in zip(
        script_chunks, dense_embeddings, sparse_embeddings
    ):
        point = PointStruct(
            id=str(uuid.uuid4()),
            vector={
                "jina": dense_embedding,
                "bm25": SparseVector(
                    indices=sparse_embedding.indices.tolist(),
                    values=sparse_embedding.values.tolist(),
                ),
            },
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
        chunk_descriptions = await markdown_splitter(script.description)
        chunk_solutions = await markdown_splitter(script.solution)
        script_chunks = [
            ScriptChunkDto(script_id=script.id, script_name=script.name, chunk=chunk)
            for chunk in chunk_descriptions + chunk_solutions
        ]
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


async def get_scripts_points_special_chunk(scripts: list[Script]):
    points: list[PointStruct] = []
    chunks: list[ScriptChunkDto] = []
    batch_embedding_size = 100
    for script in scripts:
        if script.status != "published":
            continue
        # split script description by newlines and strip each part
        questions = [q.strip() for q in script.description.split("\n") if q.strip()]
        for question in questions:
            if not question:
                continue
            script_chunks = [
                ScriptChunkDto(
                    script_id=script.id,
                    script_name=script.name,
                    chunk=question,
                )
            ]
            chunks.extend(script_chunks)
        # solution_chunks = [
        #     ScriptChunkDto(
        #         script_id=script.id,
        #         script_name=script.name,
        #         chunk=script.solution,
        #     )
        # ]
        # chunks.extend(solution_chunks)
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
                chunk=f"<question>{script.description}</question><answer>{script.solution}</answer>",
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
    points = await get_scripts_points_special_chunk([script])
    await batch_upsert_points(points)


async def insert_scripts(script_ids: list[str]) -> None:
    points = []  # Danh sách lưu trữ các điểm cần chèn hoặc cập nhật
    scripts = await with_session(
        lambda db: script_repository.get_scripts_by_ids(db, script_ids)
    )
    points = await get_scripts_points_special_chunk(scripts)
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


async def search_script_chunks(query: str, limit: int = 5) -> list[Script]:
    async with async_session() as session:
        count_db_scripts = await script_repository.count_scripts(session)
        if count_db_scripts < limit:
            return await script_repository.get_all_scripts(session)
        search_result = await query_script_points(query, limit)

        # Tạo dict để lưu script_id và điểm cao nhất
        script_scores = {}
        for point in search_result:
            script_id = point.payload["script_id"]
            score = point.score
            if script_id not in script_scores or score > script_scores[script_id]:
                script_scores[script_id] = score

        # Sắp xếp theo điểm cao nhất và lấy chỉ script_id
        script_ids = [
            script_id
            for script_id, _ in sorted(
                script_scores.items(), key=lambda x: x[1], reverse=True
            )
        ]
        scripts = await with_session(
            lambda session: script_repository.get_scripts_by_ids(session, script_ids)
        )
        final_scripts = {}
        # count = 0
        for script in scripts:
            if script.id not in final_scripts:
                final_scripts[script.id] = script
                # count += 1
                # if count >= limit:
                #     break
            related_scripts = script.related_scripts
            for related_script in related_scripts:
                if related_script.id not in final_scripts:
                    final_scripts[related_script.id] = related_script
                    # count += 1
                    # if count >= limit:
                    #     break
        return list(final_scripts.values())


async def test_search_script_chunks(query: str, limit: int = 5):
    async with async_session() as session:
        search_result = await query_script_points(query, limit)
        return [
            {
                "content": point.payload["content"],
                "similarity_score": point.score,
                "script_name": point.payload["script_name"],
            }
            for point in search_result
        ]


async def query_script_points(query: str, limit: int = 5) -> list[ScoredPoint]:
    client = create_qdrant_client()
    sparse_embeddings: Iterable[SparseEmbedding] = sparse_embedding_model.query_embed(
        query
    )
    sparse_embedding = next(iter(sparse_embeddings))
    dense_embeddings = await jina.get_embeddings(query)
    search_result = await client.query_points(
        collection_name=env_config.QDRANT_SCRIPT_COLLECTION_NAME,
        query=models.FusionQuery(fusion=models.Fusion.DBSF),
        prefetch=[
            models.Prefetch(
                query=dense_embeddings[0],
                using="jina",
            ),
            models.Prefetch(
                query=models.SparseVector(
                    indices=sparse_embedding.indices.tolist(),
                    values=sparse_embedding.values.tolist(),
                ),
                using="bm25",
            ),
        ],
        score_threshold=0.5,
        limit=limit,
    )
    return search_result.points
