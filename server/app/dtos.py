import json
from app.models import FileMetaData


class LocalData:
    def __init__(self, drive_folder_id: str):
        self.drive_folder_id = drive_folder_id


class ChunkWrapper:
    def __init__(self, file_id: str, content: str, start_line: int, end_line: int, blob_type: str):
        """Khởi tạo thông tin đoạn văn bản và số dòng bắt đầu, kết thúc."""
        self.file_id = file_id
        self.content = content
        self.start_line = start_line
        self.end_line = end_line
        self.blob_type = blob_type

    def get_content(self):
        """Trả về nội dung đoạn văn bản."""
        return self.content

    def get_metadata(self):
        """Trả về thông tin số dòng bắt đầu và kết thúc."""
        return {
            "source": "blob",
            "blobType": self.blob_type,
            "loc": {
                'lines': {
                    'from': self.start_line,
                    'to': self.end_line
                }
            },
            "file_id": self.file_id
        }


class ProcessedFileData:
    def __init__(self, data: str, metadata: FileMetaData):
        """Khởi tạo thông tin tệp đã được xử lý."""
        self.data = data
        self.metadata = metadata

    def get_text_for_embedding(self) -> str:
        if self.metadata.mime_type == 'application/pdf':
            return self.data
        elif self.metadata.mime_type == 'application/vnd.google-apps.document':
            return self.data
        elif self.metadata.mime_type == 'text/csv' or self.metadata.mime_type == 'application/vnd.google-apps.spreadsheet':
            # Chuyển object thành chuỗi JSON
            return json.dumps(self.data, ensure_ascii=False)


class ProcessedSheetData(ProcessedFileData):
    def __init__(self, id: str, data: str, metadata: FileMetaData):
        super().__init__(id, data, metadata)

    def __init__(self, file_data: ProcessedFileData):
        self.data = file_data.data
        self.metadata = file_data.metadata

    def get_sheet_schema(self) -> str:
        """Trả về schema của tệp."""
        return json.dumps(list(self.data[0].keys()), ensure_ascii=False)

    def get_list_for_embedding(self) -> list:
        # self.data is a list of dicts, convert to list string
        result = []
        for row in self.data:
            # Chuyển object thành chuỗi JSON
            json_str = json.dumps(row, ensure_ascii=False)
            # escaped_str = json_str.replace("'", "''")  # Escape dấu nháy đơn
            result.append(json_str)
        return result
