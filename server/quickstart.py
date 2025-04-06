import re


def parse_and_format_message(message):
    # Define regex patterns for different types of links (image, video, file)
    media_patterns = {
        # Match image files
        "image": r'!\[.*?\]\((https?://\S+\.(?:jpg|jpeg|png|gif|bmp|svg|webp))\)',
        # Match video files
        "video": r'!\[.*?\]\((https?://\S+\.(?:mp4|mov|avi|mkv|flv))\)',
        # Match file links
        "file": r'!\[.*?\]\((https?://\S+\.(?:pdf|doc|docx|xls|xlsx|ppt|pptx|txt|csv|zip))\)',
    }

    # If no media found, just return the text
    if not any(re.search(pattern, message) for pattern in media_patterns.values()):
        return [{"text": message.strip()}]
    
    # Replace bold text (**) with italic text (*)
    message = re.sub(r'\*\*(.*?)\*\*', r'*\1*', message)
    
    # Create a list to store media items with positions
    media_items = []
    
    # Create working copy of the message that we'll modify 
    working_message = message
    
    # Find all media occurrences with their positions
    for media_type, pattern in media_patterns.items():
        for match in re.finditer(pattern, message):
            full_match = match.group(0)  # The entire markdown syntax
            media_url = match.group(1)   # Just the URL part
            start_pos = match.start()
            end_pos = match.end()
            
            # Add to our media items list
            media_items.append({
                "type": media_type,
                "url": media_url,
                "start": start_pos,
                "end": end_pos,
                "full_match": full_match
            })
            
    # Sort media items by their position (from end to beginning to avoid position shifts)
    media_items.sort(key=lambda x: x["start"], reverse=True)
    
    # Replace all media markdown with placeholders in our working copy
    for i, item in enumerate(media_items):
        placeholder = f"__MEDIA_PLACEHOLDER_{i}__"
        working_message = working_message[:item["start"]] + placeholder + working_message[item["end"]:]
    
    # Split the modified message by placeholders
    parts = re.split(r'__MEDIA_PLACEHOLDER_\d+__', working_message)
    
    # Create the result with interleaved text and media
    result = []
    media_items.sort(key=lambda x: x["start"])  # Sort back to original order
    
    # Add text parts (filtered to remove empty ones) and media parts in correct order
    text_index = 0
    media_index = 0
    
    # Combine parts keeping track of original positions
    combined_parts = []
    
    # Add text parts first (removing empty ones)
    for i, text in enumerate(parts):
        if text and text.strip():
            # Find appropriate position
            start_pos = 0
            if i > 0 and media_index < len(media_items):
                start_pos = media_items[i-1]["end"]
            
            combined_parts.append({
                "type": "text",
                "content": text.strip(),
                "pos": start_pos
            })
    
    # Add media parts
    for item in media_items:
        combined_parts.append({
            "type": "media",
            "media_type": item["type"],
            "url": item["url"],
            "pos": item["start"]
        })
    
    # Sort all parts by their position
    combined_parts.sort(key=lambda x: x["pos"])
    
    # Convert to final output format
    for part in combined_parts:
        if part["type"] == "text":
            result.append({"text": part["content"]})
        else:
            result.append({"type": part["media_type"], "url": part["url"]})
            
    return result


# Example message with mixed media types and bold formatting
message = "Dưới đây là một số sản phẩm trị mụn trứng cá mà bạn có thể tham khảo:\n\n1. **M66 – KEM GIÚP LOẠI BỎ MỤN**\n   - Giúp loại bỏ các loại mụn, điều tiết lượng nhờn, giảm nhờn và thông thoáng lỗ chân lông.\n   - Giá gốc: 299.000 Đ, giá giảm: 249.000 Đ.\n   - [Mua sản phẩm](https://mailisa.com/m66-kem-giup-loai-bo-mun/)\n   ![M66](https://mailisa.com/wp-content/uploads/2024/10/M66-1.jpg)\n\n2. **M68 – Tinh Chất Giúp Làm Sạch Cho Da Mụn Nhờn**\n   - Tinh chất hạt tràm trà giúp giảm mụn trứng cá, kiểm soát dầu và thu nhỏ lỗ chân lông.\n   - Giá gốc: 320.000 Đ, giá giảm: 199.000 Đ.\n   - [Mua sản phẩm](https://mailisa.com/san-pham/m68-tinh-chat-giup-lam-sach-cho-da-mun-nhon/)\n   ![M68](https://mailisa.com/wp-content/uploads/2024/10/M68.jpg)\n\n3. **M70 – Kem Loại Bỏ Thâm Mụn**\n   - Ức chế vi khuẩn, kháng viêm và hỗ trợ gom cồi mụn.\n   - Giá gốc: 400.000 Đ, giá giảm: 300.000 Đ.\n   - [Mua sản phẩm](https://mailisa.com/san-pham/m70-kem-loai-bo-tham-mun/)\n   ![M70](https://mailisa.com/wp-content/uploads/2024/10/M70.jpg)\n\nNgoài ra, bạn có thể xem xét **Bộ B17 - Dành cho da mụn**, giúp hỗ trợ loại bỏ mụn triệt để và cung cấp dưỡng chất cho da.\n   - Giá gốc: 2.069.000 Đ, giá giảm: 1.517.000 Đ.\n   - [Mua sản phẩm](https://mailisa.com/san-pham/bo-b17-danh-cho-da-mun/)\n   ![B17](https://mailisa.com/wp-content/uploads/2025/03/BO-B17.jpg)\n\nHy vọng thông tin này sẽ giúp ích cho bạn! Nếu bạn cần thêm thông tin gì khác, đừng ngần ngại hỏi nhé!"

# Call function to parse and format the message
parsed_message = parse_and_format_message(message)

print(parsed_message)
