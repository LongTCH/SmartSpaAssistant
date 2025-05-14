import re

from app.configs.constants import WS_MESSAGES
from app.dtos import WsMessageDto
from app.models import Guest
from app.services.connection_manager import manager


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
    # Thêm một số ký tự đặc biệt vào văn bản để đánh dấu các định dạng
    # Thay thế **bold** thành <bold>bold</bold>
    text_after_bold = re.sub(r"\*\*(.*?)\*\*", r"<bold>\1</bold>", text)

    # Thay thế *italic* thành <italic>italic</italic>
    text_after_italic = re.sub(
        r"(?<!\*)\*(?!\*)(.*?)(?<!\*)\*(?!\*)", r"<italic>\1</italic>", text_after_bold
    )

    # Thay thế các dấu danh sách
    text_after_lists = re.sub(
        r"^\s*[\*\-]\s+", "• ", text_after_italic, flags=re.MULTILINE
    )

    # Sau khi đã xử lý xong các định dạng khác, chuyển đổi về định dạng Messenger
    # <bold>text</bold> -> *text*
    text_final_bold = re.sub(r"<bold>(.*?)</bold>", r"*\1*", text_after_lists)

    # <italic>text</italic> -> _text_
    text_final_italic = re.sub(r"<italic>(.*?)</italic>", r"_\1_", text_final_bold)

    # Xử lý các định dạng khác nếu cần
    final_text = re.sub(r"~~(.*?)~~", r"~\1~", text_final_italic)  # Gạch ngang

    return final_text


def messenger_to_markdown(text):
    """
    Chuyển đổi định dạng từ Messenger sang Markdown.
    """
    # Tương tự, sử dụng tags tạm thời để tránh xung đột

    # Thay thế *bold* thành <bold>bold</bold>
    text = re.sub(r"(?<!_)\*(?!_)(.*?)(?<!_)\*(?!_)", r"<bold>\1</bold>", text)

    # Thay thế _italic_ thành <italic>italic</italic>
    text = re.sub(r"_(.*?)_", r"<italic>\1</italic>", text)

    # Thay thế • thành dấu *
    text = re.sub(r"^\s*•\s+", "* ", text, flags=re.MULTILINE)

    # Chuyển đổi định dạng tạm về Markdown
    text = re.sub(r"<bold>(.*?)</bold>", r"**\1**", text)
    text = re.sub(r"<italic>(.*?)</italic>", r"*\1*", text)

    # Xử lý các định dạng khác
    text = re.sub(r"~(.*?)~", r"~~\1~~", text)  # Gạch ngang

    return text


def parse_and_format_message(message, char_limit=2000):
    """
    Parses and formats a message for Messenger, splitting it into multiple parts if it exceeds the character limit.

    Args:
        message: The message in markdown format to parse
        char_limit: The maximum number of characters allowed per message (default: 2000 for Messenger)

    Returns:
        A list of dictionaries containing either text or media parts
    """
    # Định nghĩa các mẫu regex cho các loại liên kết (hình ảnh, video, tệp)
    media_patterns = {
        "image": r"(?:!\[.*?\]\((https?://\S+?\.(?:jpg|jpeg|png|gif|bmp|svg|webp))[^\)]*\))|(?:\[(https?://\S+?\.(?:jpg|jpeg|png|gif|bmp|svg|webp))\])|(https?://\S+?\.(?:jpg|jpeg|png|gif|bmp|svg|webp))",
        "video": r"(?:!\[.*?\]\((https?://\S+?\.(?:mp4|mov|avi|mkv|flv))[^\)]*\))|(?:\[(https?://\S+?\.(?:mp4|mov|avi|mkv|flv))\])|(https?://\S+?\.(?:mp4|mov|avi|mkv|flv))",
        "file": r"(?:!\[.*?\]\((https?://\S+?\.(?:pdf|doc|docx|xls|xlsx|ppt|pptx|txt|csv|zip))[^\)]*\))|(?:\[(https?://\S+?\.(?:pdf|doc|docx|xls|xlsx|ppt|pptx|txt|csv|zip))\])|(https?://\S+?\.(?:pdf|doc|docx|xls|xlsx|ppt|pptx|txt|csv|zip))",
    }

    # Tìm tất cả các media matches và vị trí của chúng
    all_matches = []
    extracted_urls = []  # Lưu trữ tất cả các URL đã trích xuất để loại bỏ trùng lặp

    for media_type, pattern in media_patterns.items():
        for match in re.finditer(pattern, message):
            # Xác định URL từ các nhóm match
            url = None
            if match.group(1):  # Trường hợp ![...](URL)
                url = match.group(1)
            elif match.group(2):  # Trường hợp [URL]
                url = match.group(2)
            elif match.group(3):  # Trường hợp URL trực tiếp
                url = match.group(3)
            else:
                url = match.group(0)

            # Làm sạch URL nếu còn bất kỳ dấu markdown nào
            if "](" in url:
                url = url.split("](")[-1]
            if "(" in url and ")" in url:
                url = url.split("(")[-1].split(")")[0]

            all_matches.append(
                {
                    "type": media_type,
                    "url": url,
                    "start": match.start(),
                    "end": match.end(),
                    "full_match": match.group(0),
                }
            )
            extracted_urls.append(url)

    # Nếu không tìm thấy media, chỉ trả về văn bản (có thể được chia nhỏ)
    if not all_matches:
        text_content = message.strip()
        # Loại bỏ các dấu markdown liên quan đến URL trong phần văn bản
        # Thay thế [text](url) bằng url
        text_content = re.sub(r"\[(.*?)\]\((.*?)\)", r"\2", text_content)
        # Loại bỏ các link markdown còn sót lại mà không có text (ví dụ: [](url))
        text_content = re.sub(r"\[\]\((.*?)\)", r"\1", text_content)
        # Loại bỏ các URL đứng riêng trong ngoặc đơn nếu regex trên chưa bắt được
        text_content = re.sub(r"\((https?://[^)]+)\)", r"\1", text_content)

        # Chuyển đổi định dạng Markdown sang Messenger
        formatted_text = markdown_to_messenger(text_content)

        # Chia nhỏ nếu vượt quá giới hạn ký tự
        if len(formatted_text) <= char_limit:
            return [{"text": formatted_text}]
        else:
            return split_text_into_chunks(formatted_text, char_limit)

    # Sắp xếp các match theo vị trí
    all_matches.sort(key=lambda x: x["start"])

    # Loại bỏ các match trùng nhau hoặc chồng lấn
    filtered_matches = []
    for match in all_matches:
        # Kiểm tra xem URL đã tồn tại trong filtered_matches chưa
        if not any(match["url"] == existing["url"] for existing in filtered_matches):
            filtered_matches.append(match)

    # Chuyển đổi thành kết quả cuối cùng
    result = []
    current_pos = 0

    for match in filtered_matches:
        # Thêm text trước match
        if match["start"] > current_pos:
            text_before = message[current_pos : match["start"]].strip()
            if text_before:
                # Loại bỏ các dấu markdown liên quan đến URL trong phần văn bản
                # Thay thế [text](url) bằng url
                text_before = re.sub(r"\[(.*?)\]\((.*?)\)", r"\2", text_before)
                # Loại bỏ các link markdown còn sót lại mà không có text (ví dụ: [](url))
                text_before = re.sub(r"\[\]\((.*?)\)", r"\1", text_before)
                # Loại bỏ các URL đứng riêng trong ngoặc đơn nếu regex trên chưa bắt được
                text_before = re.sub(r"\((https?://[^)]+)\)", r"\1", text_before)

                # Chuyển đổi định dạng Markdown sang Messenger
                text_before = markdown_to_messenger(text_before)

                # Chia nhỏ nếu vượt quá giới hạn ký tự
                if len(text_before) <= char_limit:
                    result.append({"text": text_before})
                else:
                    result.extend(split_text_into_chunks(text_before, char_limit))

        # Thêm media
        result.append({"type": match["type"], "url": match["url"]})
        current_pos = match["end"]

    # Thêm text còn lại sau match cuối cùng
    if current_pos < len(message):
        text_after = message[current_pos:].strip()
        if text_after:
            # Xử lý nội dung còn lại
            # Loại bỏ các URL đã được trích xuất thành media riêng để tránh trùng lặp
            for url in extracted_urls:
                text_after = text_after.replace(url, "")

            # Sửa định dạng MD sạch sẽ trước khi chuyển đổi
            # Trích xuất lại các danh sách và định dạng sạch sẽ
            lines = text_after.split("\n")
            clean_lines = []

            for line in lines:
                # Xử lý danh sách với dấu *
                if line.strip().startswith("*   **"):  # Danh sách lồng có đánh dấu đậm
                    # Sửa lại: Giữ nguyên định dạng in đậm cho tiêu đề phụ (không chuyển sang in nghiêng)
                    line = line.replace("*   **", "• **")
                elif line.strip().startswith("*   "):  # Danh sách thông thường
                    line = line.replace("*   ", "• ")

                # Thêm dòng đã sửa vào danh sách
                clean_lines.append(line)

            # Ghép các dòng lại
            text_after = "\n".join(clean_lines)

            # Loại bỏ các dấu markdown liên quan đến URL trong phần văn bản
            text_after = re.sub(r"\[(.*?)\]\((.*?)\)", r"\2", text_after)
            text_after = re.sub(r"\[\]\((.*?)\)", r"\1", text_after)
            text_after = re.sub(r"\((https?://[^)]+)\)", r"\1", text_after)

            # Loại bỏ các dấu ngoặc rỗng
            # Loại bỏ dấu ngoặc đơn rỗng ()
            text_after = re.sub(r"\(\s*\)", "", text_after)
            # Loại bỏ dấu ngoặc vuông rỗng []
            text_after = re.sub(r"\[\s*\]", "", text_after)
            text_after = text_after.replace("()", "")

            # Chuyển đổi định dạng Markdown sang Messenger
            text_after = markdown_to_messenger(text_after)

            # Xử lý cuối cùng - làm sạch khoảng trắng thừa và định dạng lỗi
            # Sửa định dạng danh sách lồng nhau
            text_after = text_after.replace("* _", "• _")

            # Fix lỗi định dạng: chuyển lại các tiêu đề phụ từ in nghiêng sang in đậm
            # Tìm các mẫu như "• _Tẩy trang M32:_" và thay thế thành "• *Tẩy trang M32:*"
            text_after = re.sub(r"• _(.*?)(_\s)", r"• *\1*\2", text_after)
            text_after = re.sub(r"• _(.*?):_", r"• *\1:*", text_after)

            # Loại bỏ dòng trống thừa
            # Loại bỏ dòng trống thừa
            text_after = re.sub(r"\n\s+\n", "\n\n", text_after)
            # Giảm số dòng trống liên tiếp
            text_after = re.sub(r"\n{3,}", "\n\n", text_after)

            if (
                text_after.strip()
            ):  # Chỉ thêm vào kết quả nếu còn nội dung sau khi loại bỏ URL
                # Chia nhỏ nếu vượt quá giới hạn ký tự
                if len(text_after) <= char_limit:
                    result.append({"text": text_after})
                else:
                    result.extend(split_text_into_chunks(text_after, char_limit))

    return result


def split_text_into_chunks(text, char_limit=2000):
    """
    Chia văn bản thành các phần nhỏ hơn, theo thứ tự ưu tiên:
    1. Chia theo đoạn văn (dấu xuống dòng đôi)
    2. Chia theo dòng (dấu xuống dòng đơn)
    3. Chia theo câu (dấu chấm, chấm hỏi, chấm than)
    4. Chia theo từ nếu buộc phải chia giữa câu

    Args:
        text: Văn bản cần chia
        char_limit: Giới hạn ký tự mỗi phần (mặc định: 2000 cho Messenger)

    Returns:
        Một danh sách các dictionary, mỗi dictionary chứa một phần văn bản
    """
    result = []
    if len(text) <= char_limit:
        return [{"text": text}]

    # Phân tích văn bản để tìm các điểm chia phù hợp
    paragraphs = text.split("\n\n")  # Chia theo đoạn văn
    current_chunk = ""

    for paragraph in paragraphs:
        # Nếu đoạn văn tự nó đã vượt quá giới hạn
        if len(paragraph) > char_limit:
            # Nếu chunk hiện tại không rỗng, lưu lại
            if current_chunk:
                result.append({"text": current_chunk.strip()})
                current_chunk = ""

            # Xử lý đoạn văn dài, ưu tiên chia theo dòng
            lines = paragraph.split("\n")
            line_chunk = ""

            for line in lines:
                # Kiểm tra xem dòng có phải là gạch đầu dòng không
                is_bullet = line.strip().startswith("•") or line.strip().startswith("-")

                # Nếu thêm dòng mới vào vẫn trong giới hạn
                if (
                    len(line_chunk) + len(line) + 1 <= char_limit
                ):  # +1 cho ký tự xuống dòng
                    if line_chunk:
                        line_chunk += "\n" + line
                    else:
                        line_chunk = line
                else:
                    # Nếu dòng không phải gạch đầu dòng hoặc chunk hiện tại rỗng
                    if not is_bullet or not line_chunk:
                        # Lưu chunk hiện tại và bắt đầu chunk mới
                        if line_chunk:
                            result.append({"text": line_chunk.strip()})

                        # Nếu dòng hiện tại vẫn vượt quá giới hạn, cần chia nhỏ hơn nữa
                        if len(line) > char_limit:
                            # Thử chia theo câu nếu dòng quá dài
                            sentences = split_into_sentences(line)
                            sentence_chunk = ""

                            for sentence in sentences:
                                # Nếu câu đơn lẻ cũng vượt quá giới hạn
                                if len(sentence) > char_limit:
                                    # Nếu có chunk câu hiện tại, lưu lại
                                    if sentence_chunk:
                                        result.append({"text": sentence_chunk.strip()})
                                        sentence_chunk = ""

                                    # Chia câu theo từ
                                    parts = []
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
                                            parts.append(part)
                                            part = word
                                    if part:
                                        parts.append(part)

                                    # Thêm các phần đã chia vào kết quả
                                    for part in parts:
                                        result.append({"text": part.strip()})

                                # Nếu câu vừa với giới hạn
                                elif len(sentence_chunk) + len(sentence) <= char_limit:
                                    sentence_chunk += sentence
                                else:
                                    # Lưu chunk câu hiện tại và bắt đầu chunk mới
                                    result.append({"text": sentence_chunk.strip()})
                                    sentence_chunk = sentence

                            # Lưu phần câu còn lại nếu có
                            if sentence_chunk:
                                result.append({"text": sentence_chunk.strip()})

                            line_chunk = ""
                        else:
                            line_chunk = line
                    else:
                        # Đối với gạch đầu dòng, giữ nguyên chunk hiện tại và thêm vào kết quả
                        result.append({"text": line_chunk.strip()})
                        line_chunk = line

            # Thêm phần còn lại của đoạn nếu có
            if line_chunk:
                result.append({"text": line_chunk.strip()})
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
                    result.append({"text": current_chunk.strip()})
                current_chunk = paragraph

    # Thêm chunk cuối cùng nếu có
    if current_chunk:
        result.append({"text": current_chunk.strip()})

    return result


def split_into_sentences(text):
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
