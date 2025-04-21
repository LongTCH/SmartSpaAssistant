from underthesea import pos_tag


async def extract_nouns_adjectives(text, size=2, overlap=1):
    # Phân tích câu thành các từ với POS tag và chunk tag
    tokens = pos_tag(text)

    # Lọc các từ có POS tag là 'N' (danh từ) hoặc 'A' (tính từ) hoặc 'M' (số lượng từ)
    filtered_tokens = [
        word for word, pos in tokens if any(tag in pos for tag in ["N", "A", "M"])
    ]

    filtered_tokens = " ".join(filtered_tokens)
    filtered_tokens = filtered_tokens.split()

    # Nếu số lượng từ nhỏ hơn kích thước cần thiết, trả về toàn bộ từ
    if len(filtered_tokens) < size:
        return " ".join(filtered_tokens)

    # Tạo các nhóm từ theo size và overlap
    result_parts = []
    for i in range(0, len(filtered_tokens) - size + 1):
        group = filtered_tokens[i : i + size]
        result_parts.append(" ".join(group))
        i += overlap

    # Join các nhóm từ bằng ' OR '
    return " OR ".join(result_parts)
