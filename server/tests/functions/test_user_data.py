"""
Test hàm parse_and_format_message với dữ liệu cụ thể từ user
"""

import os
import sys

from app.utils.message_utils import parse_and_format_message

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))


def test_user_data():
    """Test với dữ liệu cụ thể từ user"""
    message = """Chào Chị! 🌟

Mailisa Spa hiện có một số sản phẩm trị nám rất hiệu quả. Dưới đây là danh sách các sản phẩm cùng thông tin chi tiết:

---

### 1. **BỘ N3 – HỖ TRỢ LOẠI BỎ NÁM, TÀN NHANG, ĐỒI MỒI**
- **Mô tả:** Bộ sản phẩm hỗ trợ làm đẹp da nám, giúp nghiền nát sắc tố, làm sáng da và khỏe da.
- **Giá gốc:** 2.550.000 VNĐ
- **Giá khuyến mãi:** 2.100.000 VNĐ

---

### 2. **BỘ NM1 – DÀNH CHO DA NÁM MỤN**
- **Mô tả:** Giúp loại bỏ nám, tàn nhang, giảm thâm mụn, cân bằng dầu nhờn và làm sáng da.
- **Giá gốc:** 2.800.000 VNĐ
- **Giá khuyến mãi:** 2.289.000 VNĐ

---

### 3. **M01 – KEM LOẠI BỎ SẮC TỐ**
- **Mô tả:** Giúp loại bỏ thâm, sạm, nám trên bề mặt da, làm sáng da và cải thiện làn da vàng sậm màu.
- **Giá gốc:** 910.000 VNĐ
- **Giá khuyến mãi:** 750.000 VNĐ

---

### 4. **M03 – KEM XÓA THÂM LÀM SÁNG DA**
- **Mô tả:** Loại bỏ sắc tố đen sạm, cung cấp nước và dưỡng chất, làm sáng tông màu da.
- **Giá gốc:** 940.000 VNĐ
- **Giá khuyến mãi:** 770.000 VNĐ

---

### 5. **M10 – KEM KHỐNG CHẾ SẮC TỐ**
- **Mô tả:** Giúp khống chế sắc tố Melanin, cung cấp dưỡng chất cho da sáng và cải thiện hiệu quả.
- **Giá gốc:** 550.000 VNĐ
- **Giá khuyến mãi:** 450.000 VNĐ

---

Nếu Chị cần thêm thông tin chi tiết về bất kỳ sản phẩm nào hoặc muốn đặt hàng, hãy cho em biết nhé! Em luôn sẵn sàng hỗ trợ! 💖"""

    print("=" * 80)
    print("TEST DỮ LIỆU USER")
    print("=" * 80)

    print(f"Input length: {len(message)} characters")
    print("\nInput message:")
    print(message)

    print("\n" + "=" * 80)
    print("RUNNING parse_and_format_message...")
    print("=" * 80)

    try:
        result = parse_and_format_message(message, char_limit=2000)

        print(f"\nResult: {len(result)} parts")
        print("-" * 40)

        for i, part in enumerate(result, 1):
            print(f"Part {i}: [{part.type.upper()}] ({len(part.payload)} chars)")
            print(
                f"Content: {part.payload[:100]}{'...' if len(part.payload) > 100 else ''}"
            )
            print("-" * 40)

        # Kiểm tra có vấn đề gì không
        text_parts = [part for part in result if part.type == "text"]
        media_parts = [
            part for part in result if part.type in ["image", "video", "audio", "file"]
        ]

        print(f"\nSummary:")
        print(f"- Text parts: {len(text_parts)}")
        print(f"- Media parts: {len(media_parts)}")

        # Kiểm tra độ dài
        for i, part in enumerate(text_parts, 1):
            if len(part.payload) > 2000:
                print(f"⚠️  Text part {i} vượt quá 2000 chars: {len(part.payload)}")

        # Kiểm tra nội dung bị mất
        full_text = " ".join([part.payload for part in text_parts])

        # Kiểm tra một số từ khóa quan trọng
        keywords = ["Mailisa Spa", "BỘ N3", "BỘ NM1", "M01", "M03", "M10", "🌟", "💖"]
        missing_keywords = []

        for keyword in keywords:
            if keyword not in full_text:
                missing_keywords.append(keyword)

        if missing_keywords:
            print(f"⚠️  Missing keywords: {missing_keywords}")
        else:
            print("✅ All keywords preserved")

        print("\n" + "=" * 80)
        print("TEST COMPLETED")
        print("=" * 80)

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_user_data()
