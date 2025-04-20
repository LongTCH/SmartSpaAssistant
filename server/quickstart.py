from underthesea import chunk


def extract_nouns_adjectives(text):
    # Phân tích câu thành các từ với POS tag và chunk tag
    tokens = chunk(text)

    # Lọc các từ có POS tag là 'N' (danh từ) hoặc 'A' (tính từ)
    filtered_tokens = [
        word
        for word, pos, chunk_tag in tokens
        if any(tag in pos for tag in ["N", "A", "M"])
    ]

    return filtered_tokens


sentence = "vững nguyên tắc các bước sử dụng như sau: Dạng tinh chất, serum nước xài bước 1. Dạng kem lỏng xài bước 2. Dạng kem cô đặc xài bước 3."
result = extract_nouns_adjectives(sentence)
print(result)
