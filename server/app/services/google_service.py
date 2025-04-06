import os
from app.dtos import FileMetaData, ProcessedFileData
import io
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload
import PyPDF2
import csv

# Scopes cho quyền truy cập Google Drive
SCOPES = ["https://www.googleapis.com/auth/drive"]
# Định nghĩa các mimeType được phép (google docs, spreadsheet)
allowed_mime_types = ["application/vnd.google-apps.document",
                      "application/vnd.google-apps.spreadsheet",]


def init_drive_service():
    """Khởi tạo dịch vụ Google Drive với cơ chế xử lý token hết hạn hoặc bị thu hồi."""
    creds = None
    # Kiểm tra xem tệp token.json đã tồn tại chưa
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    # Nếu không có thông tin xác thực hợp lệ, yêu cầu người dùng đăng nhập
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                # Thử làm mới token
                creds.refresh(Request())
            except Exception as e:
                print("Không thể làm mới token:", e)
                creds = None
        if not creds:
            # Nếu không thể làm mới, yêu cầu người dùng xác thực lại
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES)
            creds = flow.run_local_server(port=2345)

        # Lưu trữ token mới vào tệp token.json
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        # Xây dựng dịch vụ Google Drive
        service = build("drive", "v3", credentials=creds)
        return service
    except HttpError as err:
        print("Lỗi khi khởi tạo dịch vụ:", err)
        return None


def download_file(file_id, mime_type, service):
    """Download a file from Google Drive based on its MIME type."""
    processed_mime_type = mime_type
    if mime_type == 'application/vnd.google-apps.document':
        # Export Google Docs to plain text
        request = service.files().export_media(fileId=file_id, mimeType='text/plain')
        processed_mime_type = 'text/plain'
    elif mime_type == 'application/vnd.google-apps.spreadsheet':
        # Export Google Sheets to CSV
        request = service.files().export_media(fileId=file_id, mimeType='text/csv')
        processed_mime_type = 'text/csv'
    elif mime_type == 'application/pdf' or mime_type == 'text/csv' or mime_type.startswith('image/'):
        # Download PDFs, CSVs, and images directly
        request = service.files().get_media(fileId=file_id)
    else:
        raise ValueError(f"Unsupported MIME type: {mime_type}")

    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    fh.seek(0)
    return fh, processed_mime_type  # Return the file handle and MIME type


def extract_text_from_pdf(pdf_file_handle):
    """Extract text from a PDF file."""
    reader = PyPDF2.PdfReader(pdf_file_handle)
    text = ''
    for page in reader.pages:
        text += page.extract_text() or ''
    return text


def csv_to_json(fh):
    """Convert a CSV file-like object (BytesIO) to JSON array of objects."""
    # Giải mã bytes thành string rồi dùng csv.DictReader
    text_stream = io.TextIOWrapper(fh, encoding='utf-8-sig')
    reader = csv.DictReader(text_stream)
    rows = list(reader)
    return rows  # Đây là mảng JSON (list of dict)


def get_process_file_data_from_file_header(file_header, mime_type, file_metadata) -> ProcessedFileData:
    # Xử lý tệp dựa trên loại MIME
    if mime_type == 'application/pdf':
        file_data = ProcessedFileData(
            extract_text_from_pdf(file_header), file_metadata)
        # Xử lý thêm cho PDF
    elif mime_type == 'text/plain':
        file_data = ProcessedFileData(
            file_header.read().decode('utf-8-sig'), file_metadata)
    elif mime_type == 'text/csv':
        file_data = ProcessedFileData(csv_to_json(file_header), file_metadata)
    elif mime_type and mime_type.startswith('image/'):
        file_data = ProcessedFileData(file_header.read(), file_metadata)
        # Xử lý thêm cho hình ảnh
    else:
        raise ValueError(
            f"Loại MIME không được hỗ trợ hoặc không xác định: {mime_type}")

    return file_data


def get_process_file_data(file_metadata: FileMetaData, service) -> ProcessedFileData:
    # Download the file
    fh, mime_type = download_file(
        file_metadata.id, file_metadata.mime_type, service)

    return get_process_file_data_from_file_header(
        fh, mime_type, file_metadata)


def get_all_valid_files_recursive(folder_id, service) -> list[FileMetaData]:
    """Trả về danh sách tất cả các file trong một folder, bao gồm các nested folder."""

    if service is None:
        print("Không thể khởi tạo dịch vụ Google Drive.")
        return []
    files_list = []
    queue = [folder_id]

    while queue:
        current_folder = queue.pop(0)

        # Lấy danh sách các file trong folder hiện tại
        query_files = f"'{current_folder}' in parents and not mimeType='application/vnd.google-apps.folder' and trashed=false"
        results_files = service.files().list(q=query_files, spaces='drive',
                                             fields='files(id, name, version, mimeType)').execute()

        for file in results_files.get('files', []):
            if file["mimeType"] in allowed_mime_types:
                files_list.append(
                    FileMetaData(
                        id=file["id"],
                        name=file["name"],
                        mime_type=file["mimeType"],
                        version=int(file.get("version", 1))
                    )
                )

        # Lấy danh sách các folder con
        query_folders = f"'{current_folder}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
        results_folders = service.files().list(
            q=query_folders, spaces='drive', fields='files(id)').execute()

        for folder in results_folders.get('files', []):
            queue.append(folder["id"])

    return files_list
