import json
import uuid
from typing import Iterable

from app.configs import env_config
from app.configs.database import async_session
from app.dtos import SheetChunkDto
from app.models import Sheet
from app.repositories import sheet_repository
from app.services.clients import jina
from app.services.clients.qdrant import create_qdrant_client
from fastembed import SparseEmbedding, SparseTextEmbedding
from qdrant_client import models
from qdrant_client.http.models import (
    FieldCondition,
    Filter,
    FilterSelector,
    MatchAny,
    MatchValue,
)
from qdrant_client.models import PointStruct
from tqdm import tqdm

sparse_embedding_model = SparseTextEmbedding(model_name="Qdrant/bm25")


async def get_points_struct_for_embedding(
    sheet_chunks: list[SheetChunkDto],
) -> list[PointStruct]:
    texts = [sheet_chunk.chunk for sheet_chunk in sheet_chunks]
    dense_embeddings: list[list[float]] = await jina.get_embeddings(texts)
    sparse_embeddings: Iterable[SparseEmbedding] = sparse_embedding_model.embed(texts)
    points = []
    for sheet_chunk, dense_embedding, sparse_embedding in zip(
        sheet_chunks, dense_embeddings, sparse_embeddings
    ):
        point = PointStruct(
            id=str(uuid.uuid4()),
            vector={
                "jina": dense_embedding,
                "bm25": models.SparseVector(
                    values=sparse_embedding.values.tolist(),
                    indices=sparse_embedding.indices.tolist(),
                ),
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
        result += f"{value} "
    # strips trailing whitespace
    return result.strip()


async def get_chunks(
    sheet_name: str, table_name: str, columns: list[str]
) -> list[Sheet]:
    async with async_session() as session:
        rows = await sheet_repository.get_all_rows_with_sheet_and_columns(
            session, table_name, columns
        )
        return [
            SheetChunkDto(
                sheet_id=str(uuid.uuid4()),
                sheet_name=sheet_name,
                chunk=get_sheet_row_content(row, columns),
            )
            for row in rows
        ]


# Using the imported create_qdrant_client function from app.services.clients.qdrant


async def upsert_points(points: list[PointStruct]):
    client = create_qdrant_client()
    await client.upsert(
        collection_name=env_config.QDRANT_SHEET_COLLECTION_NAME,
        points=points,
    )


async def insert_sheet_only_text_column(sheet_id: str) -> None:
    async with async_session() as session:
        sheet: Sheet = await sheet_repository.get_sheet_by_id(session, sheet_id)
        table_name = sheet.table_name
        column_config = sheet.column_config
        text_data_columns = [
            column["column_name"]
            for column in column_config
            if column["column_type"] in ["String", "Text"]
        ]
        if len(text_data_columns) == 0:
            return None
        text_data_columns.append("id")
        sheet_chunks = await get_chunks(sheet.name, table_name, text_data_columns)
        batch_size = 100
        for i in tqdm(
            range(0, len(sheet_chunks), batch_size),
            desc=f"Processing sheet '{sheet.name}'",
            total=(len(sheet_chunks) + batch_size - 1) // batch_size,
        ):
            points = await get_points_struct_for_embedding(
                sheet_chunks[i : i + batch_size]
            )
            await upsert_points(points)


async def insert_sheet(sheet_id: str) -> None:
    async with async_session() as session:
        sheet: Sheet = await sheet_repository.get_sheet_by_id(session, sheet_id)
        table_name = sheet.table_name
        rows = await sheet_repository.get_all_rows_with_sheet_and_columns(
            session, table_name, ["id", "data_fts"]
        )
        sheet_chunks = [
            SheetChunkDto(
                id=row["id"],
                sheet_id=sheet.id,
                sheet_name=sheet.name,
                chunk=get_sheet_row_content_all_column(json.loads(row["data_fts"])),
            )
            for row in rows
        ]
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
    client = create_qdrant_client()
    dense_embeddings = await jina.get_embeddings(query)
    sparse_embeddings: Iterable[SparseEmbedding] = sparse_embedding_model.query_embed(
        query
    )
    sparse_embedding = next(iter(sparse_embeddings))
    search_result = await client.query_points(
        collection_name=env_config.QDRANT_SHEET_COLLECTION_NAME,
        query=models.FusionQuery(fusion=models.Fusion.DBSF),
        prefetch=[
            models.Prefetch(
                query=models.SparseVector(
                    indices=sparse_embedding.indices.tolist(),
                    values=sparse_embedding.values.tolist(),
                ),
                using="bm25",
            ),
            models.Prefetch(query=dense_embeddings[0], using="jina"),
        ],
        query_filter=Filter(
            must=[FieldCondition(key="sheet_id", match=MatchValue(value=sheet_id))]
        ),
        limit=limit,
    )
    search_result = search_result.points
    return [
        SheetChunkDto(
            sheet_id=point.payload["sheet_id"],
            sheet_name=point.payload["sheet_name"],
            chunk=point.payload["content"],
            id=point.payload["id"],
        )
        for point in search_result
    ]
