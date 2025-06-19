import re
from typing import List

from app.configs.constants import WS_MESSAGES
from app.dtos import WsMessageDto
from app.models import Guest
from app.services.connection_manager import manager
from app.utils.agent_utils import MessagePart


async def send_message_to_ws(guest: Guest):
    """
    Gửi tin nhắn đến WebSocket
    """
    message = WsMessageDto(
        message=WS_MESSAGES.INBOX,
        data=guest.to_dict(include=["interests", "info", "last_chat_message"]),
    )
    await manager.broadcast(message)


def get_attachment_type_name(attachment):
    """
    Lấy tên loại tệp đính kèm
    """
    if attachment["type"] == "image":
        return "Hình ảnh"
    elif attachment["type"] == "video":
        return "Video"
    elif attachment["type"] == "audio":
        return "Âm thanh"
    elif attachment["type"] == "file":
        return "Tệp tin"
    elif attachment["type"] == "location":
        return "Vị trí"
    elif attachment["type"] == "template":
        return "Mẫu"


def markdown_to_messenger(text):
    """
    Chuyển đổi định dạng Markdown sang định dạng Messenger.
    """
    # Xử lý headings trước để tránh conflict với bold
    # ### Heading 3 -> <heading>Heading 3</heading>
    # ## Heading 2 -> <heading>Heading 2</heading>
    # # Heading 1 -> <heading>Heading 1</heading>
    text_after_headings = re.sub(
        r"^#{1,6}\s+(.*?)$", r"<heading>\1</heading>", text, flags=re.MULTILINE
    )

    # Thay thế **bold** thành <bold>bold</bold>
    text_after_bold = re.sub(r"\*\*(.*?)\*\*", r"<bold>\1</bold>", text_after_headings)

    # Thay thế các dấu danh sách (giữ nguyên whitespace trước *)
    # Chỉ replace * hoặc - ở đầu dòng, không động đến whitespace trước
    text_after_lists = re.sub(
        r"^(\s*)[\*\-]\s+(\S.*?)$", r"\1• \2", text_after_bold, flags=re.MULTILINE
    )

    # Sau khi đã xử lý xong các định dạng khác, chuyển đổi về định dạng Messenger
    # <heading>text</heading> -> *text* (và merge với bold bên trong nếu có)
    def replace_heading(match):
        content = match.group(1)
        # Nếu content đã có <bold>, tạo ***bold text***
        if "<bold>" in content and "</bold>" in content:
            # Convert <bold>text</bold> thành *text* rồi wrap thêm *
            inner_bold = re.sub(r"<bold>(.*?)</bold>", r"*\1*", content)
            return f"*{inner_bold}*"
        return f"*{content}*"

    text_final_heading = re.sub(
        r"<heading>(.*?)</heading>", replace_heading, text_after_lists
    )

    # <bold>text</bold> -> *text*
    text_final_bold = re.sub(r"<bold>(.*?)</bold>", r"*\1*", text_final_heading)

    # Xử lý các định dạng khác
    final_text = re.sub(r"~~(.*?)~~", r"~\1~", text_final_bold)  # Gạch ngang

    return final_text

    return final_text


def messenger_to_markdown(text: str) -> str:
    """
    Chuyển đổi định dạng từ Messenger sang Markdown.
    - Bold: *text* -> **text** (tránh chuyển đổi phép nhân như 5 * 10)
    - Italic: _text_ -> *text*
    - List bullet: • -> *
    """

    def bold_replacer(match):
        """
        Hàm thay thế để chuyển đổi bold text một cách thông minh.
        Tránh chuyển đổi các biểu thức số học sử dụng dấu * cho phép nhân.
        """
        content = match.group(1)

        # Nếu nội dung có chữ cái, chắc chắn là text formatting -> chuyển đổi
        if any(c.isalpha() for c in content):
            return f"**{content}**"

        # Nếu chỉ có số, ký tự đặc biệt -> có thể là phép nhân -> giữ nguyên
        return match.group(0)

    # Chuyển đổi *text* thành **text** (bold)
    # Regex avoids matching * text * (with spaces) to prevent converting multiplication.
    # It looks for an asterisk, then a non-space/non-asterisk character,
    # then optionally more non-asterisk characters ending in a non-space/non-asterisk,
    # and finally a closing asterisk.
    # Using negative lookarounds to avoid converting **text**
    bold_pattern = r"(?<!\*)\*([^\s*](?:[^*]*[^\s*])?)\*(?!\*)"
    text = re.sub(bold_pattern, bold_replacer, text)

    # Chuyển đổi _text_ thành *text* (italic)
    # Using lookarounds to avoid converting __text__
    text = re.sub(r"(?<!_)_([^_]+)_(?!_)", r"*\1*", text)

    # Chuyển đổi bullet points • thành *
    text = re.sub(r"^(\s*)•\s+", r"\1* ", text, flags=re.MULTILINE)

    return text


def parse_and_format_message(message, char_limit=2000) -> List[MessagePart]:
    """
    Parses and formats a message for Messenger, splitting it into multiple parts if it exceeds the character limit.

    New logic order:
    1. Split by markdown separators first (---, ###, etc.)
    2. Extract media parts from each section
    3. Clean remaining text parts

    Args:
        message: The message in markdown format to parse
        char_limit: The maximum number of characters allowed per message (default: 2000 for Messenger)

    Returns:
        A list of MessagePart objects containing either text or media parts
    """
    if not message or not message.strip():
        return []

    # Bước 1: Chia theo markdown separators trước
    sections = _split_by_markdown_separators_first(message.strip())

    # Bước 2: Xử lý từng section - tách media và text
    result = []
    for section in sections:
        if not section.strip():
            continue

        # Tìm media trong section này
        section_parts = _process_section_for_media_and_text(section, char_limit)
        result.extend(section_parts)

    return result


def _find_all_media_matches(message):
    """Tìm tất cả media matches trong message"""
    media_patterns = {
        "image": r"(?:!\[.*?\]\((https?://\S+?\.(?:jpg|jpeg|png|gif|bmp|svg|webp))[^\)]*\))|(?:\[(https?://\S+?\.(?:jpg|jpeg|png|gif|bmp|svg|webp))\])|(https?://\S+?\.(?:jpg|jpeg|png|gif|bmp|svg|webp))",
        "video": r"(?:!\[.*?\]\((https?://\S+?\.(?:mp4|mov|avi|mkv|flv))[^\)]*\))|(?:\[(https?://\S+?\.(?:mp4|mov|avi|mkv|flv))\])|(https?://\S+?\.(?:mp4|mov|avi|mkv|flv))",
        "audio": r"(?:!\[.*?\]\((https?://\S+?\.(?:mp3|wav|flac|aac|ogg|m4a|wma))[^\)]*\))|(?:\[(https?://\S+?\.(?:mp3|wav|flac|aac|ogg|m4a|wma))\])|(https?://\S+?\.(?:mp3|wav|flac|aac|ogg|m4a|wma))",
        "file": r"(?:!\[.*?\]\((https?://\S+?\.(?:pdf|doc|docx|xls|xlsx|ppt|pptx|txt|csv|zip))[^\)]*\))|(?:\[(https?://\S+?\.(?:pdf|doc|docx|xls|xlsx|ppt|pptx|txt|csv|zip))\])|(https?://\S+?\.(?:pdf|doc|docx|xls|xlsx|ppt|pptx|txt|csv|zip))",
        "link": r"(?:!\[.*?\]\((https?://[^\)]+?)\))|(?:\[.*?\]\((https?://[^\)]+?)\))|(https?://[^\s\)]+)",
    }

    all_matches = []
    for media_type, pattern in media_patterns.items():
        for match in re.finditer(pattern, message):
            url = _extract_url_from_match(match)
            if url:
                all_matches.append(
                    {
                        "type": media_type,
                        "url": url,
                        "start": match.start(),
                        "end": match.end(),
                        "full_match": match.group(0),
                    }
                )

    return all_matches


def _extract_url_from_match(match):
    """Trích xuất URL từ regex match"""
    url = None
    for i in range(1, 4):  # Kiểm tra group 1, 2, 3
        try:
            if match.group(i):
                url = match.group(i)
                break
        except IndexError:
            continue

    if not url:
        url = match.group(0)

    # Làm sạch URL
    if "](" in url:
        url = url.split("](")[-1]
    if "(" in url and ")" in url:
        url = url.split("(")[-1].split(")")[0]

    return url


def _clean_markdown_urls(text):
    """Làm sạch các markdown URL trong text và format markdown"""
    # Thay thế [text](url) bằng url
    text = re.sub(r"\[(.*?)\]\((.*?)\)", r"\2", text)
    # Loại bỏ các link markdown rỗng
    text = re.sub(r"\[\]\((.*?)\)", r"\1", text)
    text = re.sub(r"\((https?://[^)]+)\)", r"\1", text)

    # Xử lý markdown list formatting
    lines = text.split("\n")
    clean_lines = []

    for line in lines:
        if line.strip().startswith("*   **"):
            line = line.replace("*   **", "• **")
        elif line.strip().startswith("*   "):
            line = line.replace("*   ", "• ")
        clean_lines.append(line)

    return "\n".join(clean_lines)


def _filter_matches(all_matches):
    """Lọc và loại bỏ matches trùng lặp"""
    if not all_matches:
        return []

    # Sắp xếp theo vị trí
    all_matches.sort(key=lambda x: x["start"])

    # Định nghĩa các extension để kiểm tra
    MEDIA_EXTENSIONS = {
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".bmp",
        ".svg",
        ".webp",  # image
        ".mp4",
        ".mov",
        ".avi",
        ".mkv",
        ".flv",  # video
        ".mp3",
        ".wav",
        ".flac",
        ".aac",
        ".ogg",
        ".m4a",
        ".wma",  # audio
        ".pdf",
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".ppt",
        ".pptx",
        ".txt",
        ".csv",
        ".zip",  # file
    }

    filtered_matches = []
    seen_urls = set()

    for match in all_matches:
        url = match["url"]

        # Kiểm tra URL đã tồn tại chưa
        if url in seen_urls:
            continue

        # Nếu là link, kiểm tra xem có phải media/file URL không
        if match["type"] == "link":
            url_lower = url.lower()
            is_media_file = any(url_lower.endswith(ext) for ext in MEDIA_EXTENSIONS)
            if is_media_file:
                continue  # Bỏ qua link này vì nó sẽ được xử lý bởi media pattern khác

        filtered_matches.append(match)
        seen_urls.add(url)

    return filtered_matches


def _create_media_part(match):
    """Tạo MessagePart cho media"""
    media_type = match["type"]
    url = match["url"]

    # Ánh xạ trực tiếp type
    return MessagePart(type=media_type, payload=url)


def _clean_remaining_text(text, extracted_urls):
    """Làm sạch text còn lại sau khi loại bỏ media - bao gồm full cleaning"""
    # Loại bỏ URLs đã được trích xuất
    for url in extracted_urls:
        text = text.replace(url, "")

    # Làm sạch markdown URLs còn sót lại
    text = _clean_markdown_urls(text)

    # Loại bỏ dấu ngoặc rỗng do việc remove URL
    text = re.sub(r"\(\s*\)", "", text)
    text = re.sub(r"\[\s*\]", "", text)
    text = text.replace("()", "")

    # Chỉ chuẩn hóa dòng trống thừa (4+ newlines liên tiếp)
    text = re.sub(r"\n{4,}", "\n\n\n", text)

    # Loại bỏ spaces ở cuối dòng
    lines = text.split("\n")
    clean_lines = [line.rstrip() for line in lines]
    text = "\n".join(clean_lines)

    return text


def _split_into_sentences(text):
    """
    Chia văn bản thành các câu, sử dụng các dấu kết thúc câu chính
    và tránh chia các từ viết tắt hoặc số thập phân

    Args:
        text: Văn bản cần chia thành các câu

    Returns:
        Danh sách các câu
    """
    # Danh sách các dấu kết thúc câu
    sentence_endings = [".", "!", "?", ":", ";"]

    # Các ngoại lệ không chia (từ viết tắt, số thập phân, vv)
    exceptions = [
        "TS.",
        "GS.",
        "PGS.",
        "ThS.",
        "BS.",
        "BSCK.",
        "KS.",
        "CN.",
        "Dr.",
        "Mr.",
        "Mrs.",
        "TP.",
        "T.P",
        "Q.",
        "P.",
        "Tr.",
        "St.",
        "Tp.",
        "tp.",
        "Khu p.",
        "khu p.",
    ]

    sentences = []
    current = ""
    i = 0

    while i < len(text):
        current += text[i]

        # Kiểm tra xem ký tự hiện tại có phải là dấu kết thúc câu không
        if text[i] in sentence_endings:
            # Kiểm tra xem đây có phải là một ngoại lệ không
            is_exception = False
            for ex in exceptions:
                if current.endswith(ex) and (i + 1 >= len(text) or text[i + 1] == " "):
                    is_exception = True
                    break

            # Kiểm tra xem đây có phải là số thập phân không
            if (
                i > 0
                and i < len(text) - 1
                and text[i] == "."
                and text[i - 1].isdigit()
                and text[i + 1].isdigit()
            ):
                is_exception = True

            # Nếu không phải ngoại lệ và sau dấu câu là khoảng trắng hoặc hết chuỗi, kết thúc câu
            if not is_exception and (
                i + 1 >= len(text) or text[i + 1] == " " or text[i + 1] == "\n"
            ):
                sentences.append(current)
                current = ""

        i += 1

    # Thêm phần còn lại (nếu có)
    if current:
        sentences.append(current)

    return sentences


def split_text_into_chunks_messagepart(text, char_limit=2000) -> List[MessagePart]:
    """
    Chia văn bản thành các MessagePart nhỏ hơn, theo thứ tự ưu tiên mới:
    1. Chia theo markdown separator trước (---, ***, ___, ===, ###)
    2. Tách media từ mỗi section
    3. Clean và split text parts

    Args:
        text: Văn bản cần chia
        char_limit: Giới hạn ký tự mỗi phần (mặc định: 2000 cho Messenger)

    Returns:
        Một danh sách các MessagePart, mỗi MessagePart chứa một phần văn bản
    """
    if len(text) <= char_limit:
        return [MessagePart(type="text", payload=text)]

    # Sử dụng logic mới từ parse_and_format_message
    return parse_and_format_message(text, char_limit)


def _split_by_markdown_separators_first(text):
    """Chia text theo markdown separators trước tiên"""
    markdown_separators = [
        r"^---+\s*$",  # Horizontal rule: ---
        r"^\*\*\*+\s*$",  # Horizontal rule: ***
        r"^___+\s*$",  # Horizontal rule: ___
        r"^===+\s*$",  # Alternative separator: ===
        r"^#{1,6}\s+.*$",  # Headers: # ## ### #### ##### ######
    ]

    # Combine all separator patterns
    separator_pattern = "|".join(f"({pattern})" for pattern in markdown_separators)

    lines = text.split("\n")
    sections = []
    current_section = []

    for line in lines:
        # Check if line matches any separator
        if re.match(separator_pattern, line.strip(), re.MULTILINE):
            # Add current section if it has content
            if current_section:
                sections.append("\n".join(current_section))
                current_section = []
        else:
            current_section.append(line)

    # Add final section
    if current_section:
        sections.append("\n".join(current_section))

    return sections


def _process_section_for_media_and_text(section, char_limit):
    """Xử lý một section - tách media và clean text"""
    # Tìm media trong section này
    all_matches = _find_all_media_matches(section)

    # Nếu không có media, chỉ xử lý text
    if not all_matches:
        return _process_text_section_only(section, char_limit)

    # Lọc và xử lý matches
    filtered_matches = _filter_matches(all_matches)

    # Xây dựng parts từ section này
    return _build_section_parts(section, filtered_matches, char_limit)


def _process_text_section_only(section, char_limit):
    """Xử lý section chỉ có text, không có media"""
    # Clean text trước
    cleaned_text = _clean_markdown_urls(section.strip())

    if len(cleaned_text) <= char_limit:
        return [MessagePart(type="text", payload=cleaned_text)]
    else:
        # Sử dụng logic split cũ cho text
        return _split_text_into_chunks_internal(cleaned_text, char_limit)


def _build_section_parts(section, filtered_matches, char_limit):
    """Xây dựng parts từ một section có media"""
    if not filtered_matches:
        return _process_text_section_only(section, char_limit)

    result = []
    current_pos = 0

    for match in filtered_matches:
        # Thêm text trước match
        if match["start"] > current_pos:
            text_before = section[current_pos : match["start"]].strip()
            if text_before:
                text_parts = _process_text_segment_cleaned(text_before, char_limit)
                result.extend(text_parts)

        # Thêm media part
        media_part = _create_media_part(match)
        result.append(media_part)
        current_pos = match["end"]

    # Thêm text còn lại
    if current_pos < len(section):
        text_after = section[current_pos:].strip()
        if text_after:
            # Clean remaining text
            cleaned_text = _clean_remaining_text(
                text_after, [match["url"] for match in filtered_matches]
            )

            if cleaned_text.strip():
                text_parts = _process_text_segment_cleaned(
                    cleaned_text.strip(), char_limit
                )
                result.extend(text_parts)

    return result


def _process_text_segment_cleaned(text, char_limit):
    """Xử lý text segment đã được cleaned"""
    # Text đã được clean, chỉ cần split nếu cần
    if len(text) <= char_limit:
        return [MessagePart(type="text", payload=text)]
    else:
        return _split_text_into_chunks_internal(text, char_limit)


def _split_text_into_chunks_internal(text, char_limit):
    """Split text internal - không bao gồm markdown separator logic"""
    result = []

    # Chia theo đoạn văn trước
    sections = _split_section_by_paragraphs(text, char_limit)

    for section in sections:
        if hasattr(section, "type"):  # Đã là MessagePart
            result.append(section)
        else:  # Vẫn là string
            result.append(MessagePart(type="text", payload=section))

    return result


def _split_section_by_paragraphs(text, char_limit):
    """
    Chia một section theo đoạn văn và các phương pháp khác

    Args:
        text: Section cần chia
        char_limit: Giới hạn ký tự

    Returns:
        Danh sách MessagePart
    """
    result = []  # Phân tích văn bản để tìm các điểm chia phù hợp
    paragraphs = text.split("\n\n")  # Chia theo đoạn văn
    current_chunk = ""

    for paragraph in paragraphs:
        # Nếu đoạn văn tự nó đã vượt quá giới hạn
        if len(paragraph) > char_limit:
            # Nếu chunk hiện tại không rỗng, lưu lại
            if current_chunk:
                result.append(MessagePart(type="text", payload=current_chunk.strip()))
                current_chunk = ""

            # Xử lý đoạn văn dài, ưu tiên chia theo dòng
            result.extend(_split_paragraph_by_lines(paragraph, char_limit))
        else:
            # Nếu thêm paragraph vào vẫn trong giới hạn
            if len(current_chunk) + len(paragraph) + 2 <= char_limit:  # +2 cho "\n\n"
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
            else:
                # Lưu chunk hiện tại và bắt đầu chunk mới
                if current_chunk:
                    result.append(
                        MessagePart(type="text", payload=current_chunk.strip())
                    )
                current_chunk = paragraph

    # Thêm chunk cuối cùng nếu có
    if current_chunk:
        result.append(MessagePart(type="text", payload=current_chunk.strip()))

    return result


def _split_paragraph_by_lines(paragraph, char_limit):
    """
    Chia đoạn văn theo dòng
    CHỊU TRÁCH NHIỆM: Chỉ chia text, KHÔNG clean

    Args:
        paragraph: Đoạn văn cần chia
        char_limit: Giới hạn ký tự

    Returns:
        Danh sách MessagePart
    """
    result = []
    lines = paragraph.split("\n")
    line_chunk = ""

    for line in lines:
        # Kiểm tra special cases
        is_bullet = line.strip().startswith(("•", "-", "*"))
        has_incomplete_link = _has_incomplete_markdown_link(line_chunk, line)

        # Tính toán kích thước khi thêm dòng mới
        potential_size = len(line_chunk) + len(line) + (1 if line_chunk else 0)

        # Quyết định có nên thêm vào chunk hiện tại
        should_add = (
            potential_size <= char_limit  # Vừa với giới hạn
            or has_incomplete_link  # Có markdown link chưa đóng
            or (
                is_bullet and line_chunk and len(line_chunk) < char_limit * 0.8
            )  # Bullet point logic
        )

        if should_add:
            if line_chunk:
                line_chunk += "\n" + line
            else:
                line_chunk = line
        else:
            # Lưu chunk hiện tại và bắt đầu chunk mới
            if line_chunk:
                result.append(MessagePart(type="text", payload=line_chunk.strip()))
                line_chunk = ""

            # Xử lý dòng quá dài
            if len(line) > char_limit:
                result.extend(_split_line_by_sentences(line, char_limit))
                line_chunk = ""
            else:
                line_chunk = line

    # Thêm chunk cuối cùng
    if line_chunk:
        result.append(MessagePart(type="text", payload=line_chunk.strip()))

    return result


def _has_incomplete_markdown_link(current_chunk, new_line):
    """
    Kiểm tra markdown link bị chia cắt
    """
    if not current_chunk or not new_line:
        return False

    # Pattern 1: [text]( ở cuối chunk, URL ở dòng mới
    if re.search(r"\[.*?\]\(\s*$", current_chunk.strip()):
        if re.match(r"^\s*https?://", new_line.strip()):
            return True

    # Pattern 2: URL bị chia giữa 2 dòng
    if re.search(r"\[.*?\]\(https?://[^\s\)]*$", current_chunk.strip()):
        if re.match(r"^[^\s\(]*\)", new_line.strip()):
            return True

    # Pattern 3: Link chưa đóng hoàn toàn
    open_brackets = current_chunk.count("[") - current_chunk.count("]")
    open_parens = current_chunk.count("](") - current_chunk.count(")")
    if open_brackets > 0 or open_parens > 0:
        return True

    return False


def _split_line_by_sentences(line, char_limit):
    """
    Chia dòng theo câu và từ

    Args:
        line: Dòng cần chia
        char_limit: Giới hạn ký tự

    Returns:
        Danh sách MessagePart
    """
    result = []

    # Thử chia theo câu nếu dòng quá dài
    sentences = _split_into_sentences(line)
    sentence_chunk = ""

    for sentence in sentences:
        # Nếu câu đơn lẻ cũng vượt quá giới hạn
        if len(sentence) > char_limit:
            # Nếu có chunk câu hiện tại, lưu lại
            if sentence_chunk:
                result.append(
                    MessagePart(
                        type="text",
                        payload=sentence_chunk.strip(),
                    )
                )
                sentence_chunk = ""

            # Chia câu theo từ
            result.extend(_split_sentence_by_words(sentence, char_limit))
        # Nếu câu vừa với giới hạn
        elif len(sentence_chunk) + len(sentence) <= char_limit:
            sentence_chunk += sentence
        else:
            # Lưu chunk câu hiện tại và bắt đầu chunk mới
            result.append(MessagePart(type="text", payload=sentence_chunk.strip()))
            sentence_chunk = sentence

    # Lưu phần câu còn lại nếu có
    if sentence_chunk:
        result.append(MessagePart(type="text", payload=sentence_chunk.strip()))

    return result


def _split_sentence_by_words(sentence, char_limit):
    """
    Chia câu theo từ

    Args:
        sentence: Câu cần chia
        char_limit: Giới hạn ký tự

    Returns:
        Danh sách MessagePart
    """
    result = []
    words = sentence.split()
    part = ""

    for word in words:
        # +1 cho khoảng trắng
        if len(part) + len(word) + 1 <= char_limit:
            if part:
                part += " " + word
            else:
                part = word
        else:
            result.append(MessagePart(type="text", payload=part))
            part = word

    if part:
        result.append(MessagePart(type="text", payload=part))

    return result


def markdown_remove(text):
    """
    Loại bỏ các định dạng markdown trong văn bản.

    Args:
        text: Văn bản cần loại bỏ định dạng markdown

    Returns:
        Văn bản đã loại bỏ định dạng markdown
    """
    # Loại bỏ các định dạng in đậm, in nghiêng, gạch ngang
    # text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)  # In đậm
    # text = re.sub(r"\*(.*?)\*", r"\1", text)  # In nghiêng
    # text = re.sub(r"~~(.*?)~~", r"\1", text)  # Gạch ngang

    return text.strip()
