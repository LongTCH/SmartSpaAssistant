from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models import FileMetaData, SheetRow
from app.services import vector_store_service, google_service
from app.stores import store
from app.dtos import FileMetaData, ProcessedFileData, ProcessedSheetData
from app.repositories import file_metadata_repository, sheet_row_repository
from tqdm import tqdm
from io import BytesIO


async def update_knowledge(db: AsyncSession) -> bool:
    service = google_service.init_drive_service()

    files_in_drive = google_service.get_all_valid_files_recursive(
        store.LOCAL_DATA.drive_folder_id, service)
    # Get all documents from database
    db_files_result = await db.execute(
        select(FileMetaData)
    )
    db_files = db_files_result.scalars().all()

    mapping = {file.id: {"version": file.version, "delete": True}
               for file in db_files}

    files_for_deletion: list[FileMetaData] = []
    files_for_embedding: list[FileMetaData] = []
    for file in files_in_drive:
        if file.id in mapping:
            if mapping[file.id]["version"] != file.version:
                files_for_embedding.append(FileMetaData(
                    id=file.id, name=file.name, version=file.version, mime_type=file.mime_type))
            else:
                mapping[file.id]["delete"] = False
        else:
            files_for_deletion.append(FileMetaData(
                id=file.id, version=file.version, mime_type=file.mime_type))
            files_for_embedding.append(FileMetaData(
                id=file.id, name=file.name, version=file.version, mime_type=file.mime_type))

    for file in db_files:
        if mapping[file.id]["delete"]:
            files_for_deletion.append(FileMetaData(
                id=file.id, version=file.version, mime_type=file.mime_type))

    try:
        # Delete files from database
        file_ids_for_deletion = [file.id for file in files_for_deletion]
        await file_metadata_repository.delete_files(db, file_ids_for_deletion)
        # Insert or update files in database
        sheet_rows: list[SheetRow] = []
        drive_service = google_service.init_drive_service()
        processed_file_datas: list[ProcessedFileData] = []
        file_backups = []
        for file_metadata in tqdm(files_for_embedding, desc="Downloading files"):
            # Tải file từ Google Drive
            fh, mime_type = google_service.download_file(
                file_metadata.id,
                file_metadata.mime_type,
                drive_service)
            
            file_backups.append(fh.getvalue())
            file_data = None
            if file_metadata.mime_type == "application/vnd.google-apps.spreadsheet":
                file_data = google_service.get_process_file_data_from_file_header(
                    fh, mime_type, file_metadata)
                sheet_file = ProcessedSheetData(file_data)
                file_metadata.schema = sheet_file.get_sheet_schema()

                for row in sheet_file.data:
                    sheet_row = SheetRow(
                        file_id=sheet_file.metadata.id, data=row)
                    sheet_rows.append(sheet_row)
            else:
                file_data = google_service.get_process_file_data(
                    file_metadata, drive_service)
            processed_file_datas.append(file_data)

        file_metadata_repository.insert_or_update_documents(
            db, files_for_embedding)
        # Delete vectors from Qdrant
        if not vector_store_service.delete_vectors_by_file_metadatas(
                files_for_deletion):
            raise Exception("Failed to delete vectors from Qdrant")

        sheet_row_repository.insert_or_update(db, sheet_rows)
        # vector_store_service.insert_vectors_by_processed_file_data(
        #     processed_file_datas)
        file_headers = []
        for file_backup in file_backups:
            file_headers.append(BytesIO(file_backup).read())
        # Insert vectors into Qdrant
        vector_store_service.insert_vectors_by_file_headers(
            file_headers, files_for_embedding)
        await db.commit()
        print("Update knowledge successfully")
        return True
    except Exception as e:
        print(f"Error occurred: {e}")
        await db.rollback()  # Rollback transaction on error
        return False
