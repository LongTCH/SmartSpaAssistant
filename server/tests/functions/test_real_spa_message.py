from app.utils.message_utils import parse_and_format_message


def test_real_spa_message():
    """Test với message thực tế từ spa - rất dài với nhiều links"""

    message = """Chào Quý khách Trương Long! 😊 Em đã có hình ảnh các sản phẩm làm trắng da đây rồi ạ! Quý khách xem nhé:

---

*   **BỘ B1 – HỖ TRỢ SÁNG DA:**
    [https://mailisa.com/wp-content/uploads/2024/02/BO-B1-SP-MOI.jpg](https://mailisa.com/wp-content/uploads/2024/02/BO-B1-SP-MOI.jpg)

*   **Bộ C02 CƠM ÁO GẠO TIỀN:**
    [https://mailisa.com/wp-content/uploads/2025/03/BO-C02.jpg](https://mailisa.com/wp-content/uploads/2025/03/BO-C02.jpg)

*   **M01 – KEM LOẠI BỎ SẮC TỐ:**
    [https://mailisa.com/wp-content/uploads/2024/02/M01-SP-MOI.jpg](https://mailisa.com/wp-content/uploads/2024/02/M01-SP-MOI.jpg)

*   **M03 – KEM XÓA THÂM LÀM SÁNG DA:**
    [https://mailisa.com/wp-content/uploads/2024/02/M03-SP-MOI.jpg](https://mailisa.com/wp-content/uploads/2024/02/M03-SP-MOI.jpg)

*   **M05 – KEM ỨC CHẾ SẠM NÁM LÀM SÁNG DA:**
    [https://mailisa.com/wp-content/uploads/2024/02/M05-2.jpg](https://mailisa.com/wp-content/uploads/2024/02/M05-2.jpg)

*   **M18 – KEM DƯỠNG ẨM SÂU BÊN TRONG:**
    [https://mailisa.com/wp-content/uploads/2024/02/M18-SP-MOI.jpg](https://mailisa.com/wp-content/uploads/2024/02/M18-SP-MOI.jpg)

*   **M20 – NƯỚC THẦN THÁNH:**
    [https://mailisa.com/wp-content/uploads/2024/02/9-1-1.jpg](https://mailisa.com/wp-content/uploads/2024/02/9-1-1.jpg)

*   **M47 – MẶT NẠ TRẺ HÓA TRẮNG SÁNG DA:**
    [https://mailisa.com/wp-content/uploads/2024/02/M47.jpg](https://mailisa.com/wp-content/uploads/2024/02/M47.jpg)

*   **M49 – KEM GIÚP LÀM TRẮNG SÁNG DA VÀ NGỪA LÃO HÓA:**
    [https://mailisa.com/wp-content/uploads/2024/10/M49.jpg](https://mailisa.com/wp-content/uploads/2024/10/M49.jpg)

*   **M50 – KEM NUÔI DƯỠNG DA TRẮNG SÁNG BAN NGÀY:**
    [https://mailisa.com/wp-content/uploads/2024/10/M50-e1731144908786.jpg](https://mailisa.com/wp-content/uploads/2024/10/M50-e1731144908786.jpg)

*   **M59 – MẶT NẠ DƯỠNG ẨM GIÚP LÀM TRẮNG SÁNG DA TAY:**
    [https://mailisa.com/wp-content/uploads/2024/10/M59.jpg](https://mailisa.com/wp-content/uploads/2024/10/M59.jpg)

*   **M60 – MẶT NẠ DƯỠNG ẨM GIÚP LÀM TRẮNG SÁNG DA CHÂN:**
    [https://mailisa.com/wp-content/uploads/2024/10/M60.jpg](https://mailisa.com/wp-content/uploads/2024/10/M60.jpg)

*   **M61 – MẶT NẠ TÁI TẠO TRẺ HÓA DA CHÂN:**
    [https://mailisa.com/wp-content/uploads/2024/10/M61.jpg](https://mailisa.com/wp-content/uploads/2024/10/M61.jpg)

*   **CB02 COMBO MẶT NẠ Ủ TÁI TẠO NUÔI DƯỠNG LÀM TRẮNG SÁNG DA CHÂN:**
    [https://mailisa.com/wp-content/uploads/2024/11/cb02.jpg](https://mailisa.com/wp-content/uploads/2024/11/cb02.jpg)

*   **M59.1 MIẾNG MẶT NẠ DƯỠNG ẨM GIÚP LÀM TRẮNG SÁNG DA TAY:**
    [https://mailisa.com/wp-content/uploads/2024/11/m59.1.jpg](https://mailisa.com/wp-content/uploads/2024/11/m59.1.jpg)

*   **M59.2 MIẾNG MẶT NẠ DƯỠNG ẨM GIÚP LÀM TRẮNG SÁNG DA TAY:**
    [https://mailisa.com/wp-content/uploads/2024/11/m59.2.jpg](https://mailisa.com/wp-content/uploads/2024/11/m59.2.jpg)

*   **M60.1 MIẾNG MẶT NẠ DƯỠNG ẨM GIÚP LÀM TRẮNG DA CHÂN:**
    [https://mailisa.com/wp-content/uploads/2024/11/m60.1.jpg](https://mailisa.com/wp-content/uploads/2024/11/m60.1.jpg)

*   **M60.2 MẶT NẠ DƯỠNG ẨM GIÚP LÀM TRẮNG DA CHÂN:**
    [https://mailisa.com/wp-content/uploads/2024/11/m60.2.jpg](https://mailisa.com/wp-content/uploads/2024/11/m60.2.jpg)

*   **M61.1 MIẾNG MẶT NẠ TÁI TẠO TRẺ HÓA DA CHÂN:**
    [https://mailisa.com/wp-content/uploads/2024/11/m61.1.jpg](https://mailisa.com/wp-content/uploads/2024/11/m61.1.jpg)

*   **M61.2 MIẾNG MẶT NẠ TÁI TẠO TRẺ HÓA DA CHÂN:**
    [https://mailisa.com/wp-content/uploads/2024/11/m61.2.jpg](https://mailisa.com/wp-content/uploads/2024/11/m61.2.jpg)

---

Quý khách Trương Long xem qua và cho em biết mình ưng ý sản phẩm nào nhé! Nếu cần thêm thông tin chi tiết về bất kỳ sản phẩm nào, Quý khách cứ hỏi em nha. 😊"""

    print("=== TEST MESSAGE THỰC TẾ TỪ SPA ===")
    print(f"Message length: {len(message)} characters")
    print(f"Number of image links: {message.count('.jpg')}")
    print()

    result = parse_and_format_message(message)

    print(f"Total parts generated: {len(result)}")
    print()

    # Phân tích kết quả
    text_parts = [part for part in result if part.type == "text"]
    image_parts = [part for part in result if part.type == "image"]

    print(f"Text parts: {len(text_parts)}")
    print(f"Image parts: {len(image_parts)}")
    print()

    # Hiển thị các parts
    for i, part in enumerate(result, 1):
        part_length = len(part.payload)
        if part.type == "text":
            preview = (
                part.payload[:100].replace("\n", " ") + "..."
                if len(part.payload) > 100
                else part.payload.replace("\n", " ")
            )
            print(f"Part {i}: [TEXT] ({part_length} chars) {preview}")
        else:
            print(f"Part {i}: [IMAGE] {part.payload}")

    print()
    print("=== PHÂN TÍCH KẾT QUẢ ===")

    # Kiểm tra tất cả images có được extract không
    all_image_urls = [
        "https://mailisa.com/wp-content/uploads/2024/02/BO-B1-SP-MOI.jpg",
        "https://mailisa.com/wp-content/uploads/2025/03/BO-C02.jpg",
        "https://mailisa.com/wp-content/uploads/2024/02/M01-SP-MOI.jpg",
        "https://mailisa.com/wp-content/uploads/2024/02/M03-SP-MOI.jpg",
        "https://mailisa.com/wp-content/uploads/2024/02/M05-2.jpg",
        "https://mailisa.com/wp-content/uploads/2024/02/M18-SP-MOI.jpg",
        "https://mailisa.com/wp-content/uploads/2024/02/9-1-1.jpg",
        "https://mailisa.com/wp-content/uploads/2024/02/M47.jpg",
        "https://mailisa.com/wp-content/uploads/2024/10/M49.jpg",
        "https://mailisa.com/wp-content/uploads/2024/10/M50-e1731144908786.jpg",
        "https://mailisa.com/wp-content/uploads/2024/10/M59.jpg",
        "https://mailisa.com/wp-content/uploads/2024/10/M60.jpg",
        "https://mailisa.com/wp-content/uploads/2024/10/M61.jpg",
        "https://mailisa.com/wp-content/uploads/2024/11/cb02.jpg",
        "https://mailisa.com/wp-content/uploads/2024/11/m59.1.jpg",
        "https://mailisa.com/wp-content/uploads/2024/11/m59.2.jpg",
        "https://mailisa.com/wp-content/uploads/2024/11/m60.1.jpg",
        "https://mailisa.com/wp-content/uploads/2024/11/m60.2.jpg",
        "https://mailisa.com/wp-content/uploads/2024/11/m61.1.jpg",
        "https://mailisa.com/wp-content/uploads/2024/11/m61.2.jpg",
    ]

    extracted_urls = [part.payload for part in image_parts]

    print(
        f"Expected {len(all_image_urls)} images, extracted {len(extracted_urls)} images"
    )

    # Kiểm tra images bị thiếu
    missing_images = []
    for url in all_image_urls:
        if url not in extracted_urls:
            missing_images.append(url)

    if missing_images:
        print(f"⚠️  Missing {len(missing_images)} images:")
        for img in missing_images:
            print(f"   - {img}")
    else:
        print("✅ All images extracted successfully!")

    # Kiểm tra text còn lại có chứa thông tin quan trọng không
    full_text = " ".join([part.payload for part in text_parts])

    important_keywords = [
        "Trương Long",
        "BỘ B1",
        "M01",
        "M03",
        "M05",
        "M18",
        "M20",
        "M47",
        "M49",
        "M50",
        "M59",
        "M60",
        "M61",
        "CB02",
        "M59.1",
        "M59.2",
        "M60.1",
        "M60.2",
        "M61.1",
        "M61.2",
        "KEM LOẠI BỎ",
        "TRẮNG SÁNG DA",
        "MẶT NẠ",
    ]

    missing_keywords = []
    for keyword in important_keywords:
        if keyword not in full_text:
            missing_keywords.append(keyword)

    if missing_keywords:
        print(f"⚠️  Missing keywords: {missing_keywords}")
    else:
        print("✅ All important keywords preserved!")

    # Kiểm tra xem có còn markdown links không
    if "[https://" in full_text:
        print("⚠️  Still contains markdown links (should be converted to plain URLs)")
    else:
        print("✅ All markdown links converted to plain URLs!")

    # Kiểm tra message có bị chia theo separator không (có ---)
    if len(text_parts) >= 2:
        print("✅ Message correctly split by separators!")
    else:
        print("⚠️  Message should be split by separators")


if __name__ == "__main__":
    test_real_spa_message()
