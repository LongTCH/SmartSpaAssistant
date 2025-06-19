import uuid
from typing import Iterable

from app.configs import env_config
from app.configs.database import async_session
from app.dtos import SheetChunkDto
from app.models import Sheet
from app.repositories import sheet_repository
from app.services.clients import jina
from app.services.clients.qdrant import create_qdrant_client
from app.utils import rag_utils
from fastembed import SparseEmbedding, SparseTextEmbedding
from qdrant_client import models
from qdrant_client.http.models import (
    FieldCondition,
    Filter,
    FilterSelector,
    MatchAny,
    MatchValue,
    ScoredPoint,
)
from qdrant_client.models import PointStruct

sparse_embedding_model = SparseTextEmbedding(model_name="Qdrant/bm25")


async def get_points_struct_for_embedding(
    sheet_chunks: list[SheetChunkDto],
) -> list[PointStruct]:
    texts = [sheet_chunk.chunk for sheet_chunk in sheet_chunks]
    sparse_embeddings: Iterable[SparseEmbedding] = sparse_embedding_model.embed(texts)
    points = []
    for sheet_chunk, sparse_embedding in zip(sheet_chunks, sparse_embeddings):
        point = PointStruct(
            id=str(uuid.uuid4()),
            vector={
                "bm25": models.SparseVector(
                    values=sparse_embedding.values.tolist(),
                    indices=sparse_embedding.indices.tolist(),
                )
            },
            payload={
                "content": sheet_chunk.chunk,
                "sheet_id": sheet_chunk.sheet_id,
                "sheet_name": sheet_chunk.sheet_name,
                "id": sheet_chunk.id,
            },
        )
        points.append(point)
    return points


def get_sheet_row_content(row: dict, columns: list[str]) -> str:
    result = ""
    for col in columns:
        if col != "id":
            result += f"{row[col]} "
    return result.strip()


def get_sheet_row_content_all_column(row: dict) -> str:
    result = ""
    for key, value in row.items():
        result += f"{key}: {value} \n "
    # strips trailing whitespace
    return result.strip()


async def upsert_points(points: list[PointStruct]):
    client = create_qdrant_client()
    await client.upsert(
        collection_name=env_config.QDRANT_SHEET_COLLECTION_NAME,
        points=points,
    )


async def insert_sheet(sheet_id: str) -> None:
    async with async_session() as session:
        sheet: Sheet = await sheet_repository.get_sheet_by_id(session, sheet_id)
        table_name = sheet.table_name
        rows = await sheet_repository.get_all_rows_of_sheet(session, table_name)
        sheet_chunks = []
        for row in rows:
            texts = await rag_utils.markdown_splitter(
                get_sheet_row_content_all_column(row), 500, 10
            )
            for index, text in enumerate(texts):
                sheet_chunks.append(
                    SheetChunkDto(
                        sheet_id=sheet.id,
                        sheet_name=sheet.name,
                        chunk=text,
                        id=f"{row['id']}_{index}",  # Unique ID for each chunk
                    )
                )
        batch_size = 100
        for i in range(0, len(sheet_chunks), batch_size):
            points = await get_points_struct_for_embedding(
                sheet_chunks[i : i + batch_size]
            )
            await upsert_points(points)


async def delete_sheet(sheet_id: str) -> None:
    client = create_qdrant_client()
    await client.delete(
        collection_name=env_config.QDRANT_SHEET_COLLECTION_NAME,
        points_selector=FilterSelector(
            filter=Filter(
                must=[FieldCondition(key="sheet_id", match=MatchValue(value=sheet_id))]
            )
        ),
    )


async def delete_sheets(sheet_ids: list[str]) -> None:
    client = create_qdrant_client()
    await client.delete(
        collection_name=env_config.QDRANT_SHEET_COLLECTION_NAME,
        points_selector=FilterSelector(
            filter=Filter(
                must=[FieldCondition(key="sheet_id", match=MatchAny(any=sheet_ids))]
            )
        ),
    )


async def search_chunks_by_sheet_id(
    sheet_id: str, query: str, limit: int = 5
) -> list[SheetChunkDto]:
    search_result = await query_sheet_points(query, sheet_id, 100)
    item_ids = set()
    count = 0
    for point in search_result:
        id = point.payload["id"].split("_")[0]  # Get the first part of the ID
        if id not in item_ids:
            item_ids.add(id)
        count += 1
        if count >= limit:
            break
    async with async_session() as session:
        sheet: Sheet = await sheet_repository.get_sheet_by_id(session, sheet_id)
        if not sheet:
            return []
        # Convert string IDs to integers before passing to repository
        int_item_ids = [int(id) for id in item_ids]
        items = await sheet_repository.get_rows_with_ids(
            session, sheet.table_name, int_item_ids
        )
        return [
            SheetChunkDto(
                sheet_id=sheet_id,
                sheet_name=sheet.name,
                chunk=get_sheet_row_content_all_column(item),
                id=str(item["id"]),
            )
            for item in items
        ]


async def test_search_chunks_by_sheet_id(sheet_id: str, query: str, limit: int = 5):
    # search_result = await query_sheet_points(query, sheet_id, limit)
    # return [
    #     {
    #         "sheet_id": point.payload["sheet_id"],
    #         "sheet_name": point.payload["sheet_name"],
    #         "content": point.payload["content"],
    #         "id": point.payload["id"],
    #         "score": point.score,
    #     }
    #     for point in search_result
    # ]
    return await search_chunks_by_sheet_id(sheet_id, query, limit)


async def query_sheet_points(
    query: str, sheet_id: str, limit: int = 5
) -> list[ScoredPoint]:
    client = create_qdrant_client()
    sparse_embeddings: Iterable[SparseEmbedding] = sparse_embedding_model.query_embed(
        query
    )
    sparse_embedding = next(iter(sparse_embeddings))
    dense_embeddings = await jina.get_embeddings(query)
    search_result = await client.query_points(
        collection_name=env_config.QDRANT_SHEET_COLLECTION_NAME,
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
        query=models.FusionQuery(fusion=models.Fusion.RRF),
        query_filter=Filter(
            must=[FieldCondition(key="sheet_id", match=MatchValue(value=sheet_id))]
        ),
        limit=limit,
    )
    return search_result.points
