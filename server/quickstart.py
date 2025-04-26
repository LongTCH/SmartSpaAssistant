import re


def markdown_to_messenger(text):
    # In đậm: **bold** → *bold*
    text = re.sub(r"\*\*(.*?)\*\*", r"*\1*", text)
    # In nghiêng: *italic* → _italic_
    text = re.sub(r"\*(.*?)\*", r"_\1_", text)
    # Gạch ngang: ~~strikethrough~~ → ~strikethrough~
    text = re.sub(r"~~(.*?)~~", r"~\1~", text)
    # Mã nguồn: `code` → `code`
    text = re.sub(r"`(.*?)`", r"`\1`", text)
    # Khối mã: ```code``` → ```code```
    text = re.sub(r"```(.*?)```", r"``` \1 ```", text, flags=re.DOTALL)
    # Liên kết: [text](url) → [text](url)
    text = re.sub(r"\[(.*?)\]\((.*?)\)", r"[\1](\2)", text)
    return text


def messenger_to_markdown(text):
    # In đậm: *bold* → **bold**
    text = re.sub(r"\*(.*?)\*", r"**\1**", text)
    # In nghiêng: _italic_ → *italic*
    text = re.sub(r"_(.*?)_", r"*\1*", text)
    # Gạch ngang: ~strikethrough~ → ~~strikethrough~~
    text = re.sub(r"~(.*?)~", r"~~\1~~", text)
    # Mã nguồn: `code` → `code`
    text = re.sub(r"`(.*?)`", r"`\1`", text)
    # Khối mã: ```code``` → ```code```
    text = re.sub(r"```(.*?)```", r"``` \1 ```", text, flags=re.DOTALL)
    # Liên kết: [text](url) → [text](url)
    text = re.sub(r"\[(.*?)\]\((.*?)\)", r"[\1](\2)", text)
    return text


def parse_and_format_message(message):
    # Định nghĩa các mẫu regex cho các loại liên kết (hình ảnh, video, tệp)
    media_patterns = {
        "image": r"!\[.*?\]\((https?://\S+\.(?:jpg|jpeg|png|gif|bmp|svg|webp))\)|(https?://\S+\.(?:jpg|jpeg|png|gif|bmp|svg|webp))",
        "video": r"!\[.*?\]\((https?://\S+\.(?:mp4|mov|avi|mkv|flv))\)|(https?://\S+\.(?:mp4|mov|avi|mkv|flv))",
        "file": r"!\[.*?\]\((https?://\S+\.(?:pdf|doc|docx|xls|xlsx|ppt|pptx|txt|csv|zip))\)|(https?://\S+\.(?:pdf|doc|docx|xls|xlsx|ppt|pptx|txt|csv|zip))",
    }

    # Nếu không tìm thấy media, chỉ trả về văn bản
    if not any(re.search(pattern, message) for pattern in media_patterns.values()):
        return [{"text": message.strip()}]

    message = markdown_to_messenger(message)

    # Danh sách chứa các phần media với vị trí
    media_items = []

    # Tạo bản sao làm việc của tin nhắn để chỉnh sửa
    working_message = message

    # Tìm tất cả các media với vị trí của chúng
    for media_type, pattern in media_patterns.items():
        for match in re.finditer(pattern, message):
            full_match = match.group(0)
            # Xử lý cả hai trường hợp: URL trong markdown và URL trực tiếp
            if len(match.groups()) >= 1 and match.group(1):
                media_url = match.group(1)  # URL trong markdown ![...](URL)
            elif len(match.groups()) >= 2 and match.group(2):
                media_url = match.group(2)  # URL trực tiếp
            else:
                media_url = full_match  # Fallback đến toàn bộ match

            start_pos = match.start()
            end_pos = match.end()

            media_items.append(
                {
                    "type": media_type,
                    "url": media_url,
                    "start": start_pos,
                    "end": end_pos,
                    "full_match": full_match,
                }
            )

    # Sắp xếp các phần media theo vị trí (từ cuối đến đầu để tránh thay đổi vị trí)
    media_items.sort(key=lambda x: x["start"], reverse=True)

    # Thay thế tất cả các markdown media bằng placeholder trong bản sao làm việc
    for i, item in enumerate(media_items):
        placeholder = f"__MEDIA_PLACEHOLDER_{i}__"
        working_message = (
            working_message[: item["start"]]
            + placeholder
            + working_message[item["end"] :]
        )

    # Tách tin nhắn đã chỉnh sửa theo các placeholder
    parts = re.split(r"__MEDIA_PLACEHOLDER_\d+__", working_message)

    # Tạo kết quả với văn bản và media xen kẽ
    result = []
    media_items.sort(key=lambda x: x["start"])

    media_index = 0
    combined_parts = []

    for i, text in enumerate(parts):
        if text and text.strip():
            start_pos = 0
            if i > 0 and media_index < len(media_items):
                start_pos = media_items[i - 1]["end"]

            combined_parts.append(
                {"type": "text", "content": text.strip(), "pos": start_pos}
            )

    for item in media_items:
        combined_parts.append(
            {
                "type": "media",
                "media_type": item["type"],
                "url": item["url"],
                "pos": item["start"],
            }
        )

    combined_parts.sort(key=lambda x: x["pos"])

    for part in combined_parts:
        if part["type"] == "text":
            result.append({"text": part["content"]})
        else:
            result.append({"type": part["media_type"], "url": part["url"]})

    return result


text = "Dưới đây là thông tin chi tiết về Bộ C02 – “Cơm Áo Gạo Tiền” của Mailisa:\n\n1. Tên sản phẩm  \n   • Bộ C02 – Cơm Áo Gạo Tiền  \n\n2. Mã SKU  \n   • C02  \n\n3. Mô tả ngắn  \n   “Bộ C02 ‘Cơm Áo Gạo Tiền’ (gồm M19, M23, M32, M55) – không thể thiếu trong quy trình chăm sóc da hàng ngày, giúp nuôi dưỡng, bảo vệ và duy trì làn da khỏe đẹp, căng trắng, mịn màng.”\n\n4. Giá bán  \n   • Giá gốc: 1.400.000 Đ  \n   • Giá khuyến mãi: 1.138.000 Đ (giảm 18,71%)  \n\n5. Đơn vị  \n   • Đ  \n\n6. Hình ảnh sản phẩm  \n   https://mailisa.com/wp-content/uploads/2025/03/BO-C02.jpg  \n\n7. Thành phần & công dụng chính  \n   • M32 (Tẩy trang):  \n     – Loại bỏ lớp trang điểm, bụi bẩn, dầu nhờn dư thừa sâu dưới lỗ chân lông, nhẹ nhàng, không gây khô da.  \n   • M19 (Sữa rửa mặt sạch sâu Acid Amino):  \n     – Làm sạch da sâu, loại bỏ bụi bẩn và dầu nhờn tích tụ lâu ngày, cho da căng bóng, mịn màng.  \n   • M55 (Cát tẩy tế bào chết):  \n     – Hạt siêu mịn, làm sạch sâu, loại tế bào chết, thu nhỏ lỗ chân lông, ngừa mụn, giúp da mịn và tăng hiệu quả sản phẩm tiếp theo.  \n   • M23 (Kem chống nắng BB Nano Che Khuyết Điểm):  \n     – Bảo vệ da khỏi tia UV, ngăn ngừa lão hóa, cung cấp dưỡng chất nuôi dưỡng da khỏe mạnh, cân bằng tông màu, thay thế lớp nền trang điểm tự nhiên.\n\n8. Hướng dẫn sử dụng  \n   Buổi sáng:  \n     1. M32 – Tẩy trang siêu cấp X2 (nếu có trang điểm): lấy lượng vừa đủ, lau nhẹ theo hướng từ trong ra ngoài.  \n     2. M19 – Sữa rửa mặt Acid Amino: tạo bọt và mát-xa để làm sạch sâu, rửa lại nước sạch, lau khô.  \n     3. Thoa các sản phẩm dưỡng (nếu có).  \n     4. M23 – Kem chống nắng BB Nano: chấm 5 điểm trên mặt, tán đều và vỗ nhẹ, thoa lại sau 5 tiếng nếu hoạt động ngoài trời nhiều.\n\n   Buổi tối:  \n     1. M32 – Tẩy trang siêu cấp X2: lấy lượng vừa đủ, lau nhẹ để loại bỏ trang điểm và bụi bẩn.  \n     2. M19 – Sữa rửa mặt Acid Amino: tạo bọt, massage, rửa sạch, lau khô.  \n     3. Thoa các sản phẩm dưỡng (nếu có).  \n     4. M55 – Cát tẩy tế bào chết: (da dầu/mụn 2 lần/tuần; da khô/thường/nám 1 lần/tuần). Sau khi rửa mặt, lau khô, chấm kem đều 5 điểm, massage 2 phút, rửa sạch và lau khô.\n\n   Lưu ý đặc biệt:  \n   – Thứ tự sản phẩm: tinh chất/serum – kem lỏng – kem cô đặc.  \n   – Khi dùng nhiều sản phẩm, quy trình trên giữ nguyên.  \n\n9. Link đặt hàng  \n   https://mailisa.com/san-pham/bo-c02-doctor-magic/\n\nƯu đãi kèm theo (tự động áp dụng khi thanh toán):  \n• Giảm 20% cho khách hàng mới  \n• Tích điểm: 100.000 Đ = 1 điểm (10 điểm đổi voucher 50.000 Đ)\n\nBạn có muốn đặt hàng ngay hoặc cần thêm hỗ trợ gì không ạ? Nếu có, vui lòng cho mình biết:  \n– Họ tên  \n– Số điện thoại  \n– Địa chỉ nhận hàng  \n\nMình rất vui lòng hỗ trợ bạn!"
print(parse_and_format_message(text))
