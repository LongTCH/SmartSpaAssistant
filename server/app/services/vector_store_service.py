from app.configs import env_config
from app.configs.qdrant import qdrant_client
from qdrant_client.models import Filter, FieldCondition, MatchAny, FilterSelector
import uuid
from qdrant_client.http.models import PointStruct
import requests
from app.dtos import FileMetaData, ChunkWrapper, ProcessedFileData
from app.services import google_service
from app.models import FileMetaData
from tqdm import tqdm


def delete_vectors_by_file_metadatas(file_metadatas: list[FileMetaData]) -> bool:
    file_ids = [file_metadata.id for file_metadata in file_metadatas]
    # Thực hiện xóa các điểm khớp với filter và nhận kết quả
    result = qdrant_client.delete(
        collection_name=env_config.QDRANT_KNOWLEDGE_COLLECTION_NAME,
        points_selector=FilterSelector(
            filter=Filter(
                must=[
                    FieldCondition(
                        key="metadata.file_id",
                        match=MatchAny(any=file_ids)
                    )
                ]
            )
        ),
    )

    # Kiểm tra trạng thái của kết quả
    if result.status == 'completed':
        return True
    else:
        return False


def send_file_to_webhook(file_handle, mime_type, webhook_url, file_name):
    """Gửi tệp nhị phân đến webhook."""
    files = {'file': (file_name, file_handle, mime_type)}
    response = requests.post(webhook_url, files=files)
    return response


def get_file_downloaded_mime_type(file_metadata: FileMetaData) -> str:
    if file_metadata.mime_type == "application/vnd.google-apps.document":
        return "text/plain"
    elif file_metadata.mime_type == "application/vnd.google-apps.spreadsheet":
        return "text/csv"
    return file_metadata.mime_type


def insert_vectors_by_file_headers(file_headers, file_metadatas: list[FileMetaData]) -> None:
    for i, file_metadata in tqdm(enumerate(file_metadatas), desc="Processing files"):
        # files.append(('files', (file_metadata.name, fh, mime_type)))
        response = send_file_to_webhook(
            file_handle=file_headers[i],
            mime_type=get_file_downloaded_mime_type(file_metadata),
            webhook_url=env_config.N8N_RAG_FILE_WEBHOOK_URL,
            file_name=file_metadata.id)


def insert_vectors_by_files(file_metadatas: list[FileMetaData], drive_service) -> None:
    files = []
    for file_metadata in file_metadatas:
        # Tải file từ Google Drive
        fh, mime_type = google_service.download_file(
            file_metadata.id, file_metadata.mime_type, drive_service)

        # files.append(('files', (file_metadata.name, fh, mime_type)))
        response = send_file_to_webhook(
            file_handle=fh,
            mime_type=mime_type,
            webhook_url=env_config.N8N_RAG_FILE_WEBHOOK_URL,
            file_name=file_metadata.id)

    # Gửi tệp đến webhook
    # response = requests.post(
    #     env_config.N8N_RAG_FILE_WEBHOOK_URL, files=files)
    # if response.status_code == 200:
    #     print("Tất cả các tệp đã được gửi thành công.")
    # else:
    #     print(f"Lỗi khi gửi tệp. Mã trạng thái: {response.status_code}")


def insert_vectors_by_processed_file_data(file_datas: list[ProcessedFileData]) -> None:
    points = []  # Danh sách lưu trữ các điểm cần chèn hoặc cập nhật
    chunk_wrappers: list[ChunkWrapper] = []
    for file_data in tqdm(file_datas, desc="Chunking"):
        text = file_data.get_text_for_embedding()
        # response = send_to_webhook(
        #     file_data, file_version.id, env_config.N8N_RAG_FILE_WEBHOOK_URL)
        # print(
        #     f"Đã gửi tệp {file_version.id} đến webhook với mã phản hồi: {response.status_code}")
        # Chia văn bản thành các đoạn nhỏ
        chunk_wrappers.extend(chunk_text_with_lines(
            file_data.metadata.id, file_data.metadata.mime_type, text))

    for wrapper in tqdm(chunk_wrappers, desc="Tạo embeddings"):
        # Tạo embeddings cho từng đoạn
        embedding = generate_embeddings_ollama(wrapper.get_content())

        # Tạo điểm và thêm vào danh sách
        point = PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding,
            payload={"content": wrapper.get_content(),
                     "metadata": wrapper.get_metadata()},
        )
        points.append(point)
        if len(points) >= 10:
            qdrant_client.upsert(
                collection_name=env_config.QDRANT_KNOWLEDGE_COLLECTION_NAME,
                points=points
            )
            points = []  # Đặt lại danh sách điểm sau khi chèn
    if points:
        qdrant_client.upsert(
            collection_name=env_config.QDRANT_KNOWLEDGE_COLLECTION_NAME,
            points=points
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
            end_line=end_line + 1,      # Convert to 1-based index
            blob_type=mime_type
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
            end_line=end_line + 1,      # Convert to 1-based index
            blob_type=mime_type
        )
        chunks.append(chunk)

        # Move to next chunk position with overlap
        start_pos = end_pos - overlap
        if start_pos >= len(text):
            break

    return chunks

# def chunk_text_with_lines(file_id, mime_type, text, chunk_size=500, overlap=50) -> list[ChunkWrapper]:
#     """
#     Chia văn bản thành các đoạn nhỏ sử dụng phương pháp Recursive Character Text Splitter.
#     Phương pháp này sẽ cố gắng chia văn bản theo các ranh giới tự nhiên như đoạn, câu, hay từ.

#     Args:
#         file_id (str): ID của tệp.
#         mime_type (str): Loại MIME của tệp.
#         text (str): Văn bản đầu vào.
#         chunk_size (int): Kích thước tối đa của mỗi đoạn (tính theo số ký tự).
#         overlap (int): Số ký tự chồng lấp giữa các đoạn.

#     Returns:
#         list[ChunkWrapper]: Danh sách các đoạn văn bản được bọc trong ChunkWrapper.
#     """
#     # Xử lý trường hợp đầu vào rỗng
#     if not text or not text.strip():
#         return []

#     # Đảm bảo các tham số hợp lệ
#     chunk_size = max(100, chunk_size)  # Đảm bảo chunk_size tối thiểu là 100
#     overlap = min(overlap, chunk_size // 2)  # Đảm bảo overlap không quá lớn

#     # Định nghĩa các ký tự phân tách theo thứ tự ưu tiên
#     separators = ["\n\n", "\n", ". ", ", ", " ", ""]

#     def _split_text_recursive(text, separators, chunk_size):
#         """Chia văn bản đệ quy theo các ký tự phân tách."""
#         # Nếu văn bản đủ nhỏ, trả về nguyên văn
#         if len(text) <= chunk_size:
#             return [text]

#         # Thử từng ký tự phân tách theo thứ tự ưu tiên
#         for separator in separators:
#             if separator == "":  # Nếu không có ký tự phân tách nào khả dụng
#                 return [text[:chunk_size], text[chunk_size:]]

#             # Phân tách văn bản bằng ký tự hiện tại
#             splits = text.split(separator)

#             # Nếu không phân tách được, thử ký tự tiếp theo
#             if len(splits) == 1:
#                 continue

#             # Kết quả sẽ chứa các chunk đã tạo
#             result = []
#             current_chunk = ""

#             # Duyệt qua các phần đã được phân tách
#             for split in splits:
#                 candidate = current_chunk + \
#                     (separator if current_chunk else "") + split

#                 # Nếu thêm phần tiếp theo sẽ vượt quá kích thước, lưu chunk hiện tại và bắt đầu chunk mới
#                 if len(candidate) > chunk_size and current_chunk:
#                     result.append(current_chunk)
#                     current_chunk = split
#                 else:
#                     current_chunk = candidate

#             # Thêm chunk cuối cùng nếu còn
#             if current_chunk:
#                 result.append(current_chunk)

#             # Nếu một trong các chunk vẫn còn quá lớn, tiếp tục phân tách đệ quy
#             final_result = []
#             for chunk in result:
#                 if len(chunk) > chunk_size:
#                     # Dùng ký tự phân tách tiếp theo trong danh sách
#                     next_separator_index = separators.index(separator) + 1
#                     if next_separator_index < len(separators):
#                         final_result.extend(_split_text_recursive(
#                             chunk, separators[next_separator_index:], chunk_size))
#                     else:
#                         # Nếu đã dùng hết các ký tự phân tách, chia theo kích thước
#                         final_result.extend([chunk[i:i+chunk_size]
#                                             for i in range(0, len(chunk), chunk_size)])
#                 else:
#                     final_result.append(chunk)

#             return final_result

#         # Nếu không thành công với bất kỳ separator nào
#         return [text[:chunk_size], text[chunk_size:]]

#     # Chia văn bản thành các đoạn không chồng lấp
#     chunks_text = _split_text_recursive(text, separators, chunk_size)

#     # Tạo các chunk cuối cùng với phần chồng lấp
#     chunks = []
#     current_position = 0

#     # Tạo một mảng lưu trữ vị trí của tất cả các ký tự xuống dòng
#     newline_positions = [i for i, char in enumerate(text) if char == '\n']
#     newline_positions = [-1] + newline_positions + \
#         [len(text)]  # Thêm -1 ở đầu và độ dài văn bản ở cuối

#     for chunk_text in chunks_text:
#         # Xác định vị trí chính xác bắt đầu của đoạn văn trong văn bản gốc
#         start_index = text.find(chunk_text, current_position)
#         if start_index == -1:
#             # Thử tìm từ đầu nếu không tìm thấy từ vị trí hiện tại
#             start_index = text.find(chunk_text)
#             if start_index == -1:
#                 continue  # Bỏ qua nếu không tìm thấy

#         end_index = start_index + len(chunk_text)

#         # Thêm phần chồng lấp
#         overlap_start = max(0, start_index - overlap)
#         chunk_with_overlap = text[overlap_start:end_index]

#         # Tìm số dòng bắt đầu bằng cách đếm số ký tự xuống dòng trước vị trí bắt đầu
#         start_line = next(i for i, pos in enumerate(
#             newline_positions) if pos >= overlap_start)

#         # Tìm số dòng kết thúc bằng cách đếm số ký tự xuống dòng trước vị trí kết thúc
#         end_line = next(i for i, pos in enumerate(
#             newline_positions) if pos >= end_index)

#         # Điều chỉnh để số dòng bắt đầu từ 1 thay vì 0
#         start_line = start_line
#         end_line = end_line if end_line == len(
#             newline_positions) - 1 else end_line

#         # Đếm số dòng thực trong đoạn để xác nhận
#         newlines_in_chunk = chunk_with_overlap.count('\n')

#         chunks.append(ChunkWrapper(
#             file_id=file_id,
#             content=chunk_with_overlap,
#             start_line=start_line,
#             end_line=end_line,
#             blob_type=mime_type
#         ))

#         current_position = end_index

#     return chunks


def generate_embeddings_ollama(text):
    """Tạo embeddings cho văn bản bằng Ollama API."""

    # Đặt payload cho API request
    payload = {
        # Tên mô hình của Ollama (thay đổi theo mô hình bạn muốn sử dụng)
        "model": env_config.OLLAMA_EMBEDDINGS_MODEL,
        "input": text
    }

    # Gửi request tới Ollama API để nhận embeddings
    response = requests.post(env_config.OLLAMA_API_URL, json=payload)

    # Kiểm tra phản hồi từ Ollama API
    if response.status_code == 200:
        return response.json()['data'][0]['embedding']
    else:
        print("Error:", response.text)
        return None
