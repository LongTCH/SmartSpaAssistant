"""
Test với dữ liệu cụ thể của user - test separator behavior
"""

import os
import sys

from app.utils.message_utils import parse_and_format_message

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))


def test_user_data():
    """Test với dữ liệu spa của user"""
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

    print("Testing với dữ liệu spa...")
    print(f"Message length: {len(message)} characters")
    print("=" * 60)

    result = parse_and_format_message(message)

    print(f"Number of parts: {len(result)}")
    print("\nParts breakdown:")

    for i, part in enumerate(result, 1):
        print(f"\nPart {i}: [{part.type.upper()}] ({len(part.payload)} chars)")
        print("-" * 40)
        print(part.payload[:200] + ("..." if len(part.payload) > 200 else ""))

    # Kiểm tra xem có bị mất thông tin không
    full_text = " ".join([part.payload for part in result if part.type == "text"])

    keywords = [
        "BỘ N3",
        "BỘ NM1",
        "M01",
        "M03",
        "M10",
        "2.100.000",
        "2.289.000",
        "750.000",
        "770.000",
        "450.000",
    ]

    print("\n" + "=" * 60)
    print("KEYWORD CHECK:")
    for keyword in keywords:
        if keyword in full_text:
            print(f"✅ {keyword}")
        else:
            print(f"❌ {keyword}")

    print("\n" + "=" * 60)
    print(
        f"✅ RESULT: Message được chia thành {len(result)} parts do có separator lines (---)"
    )


if __name__ == "__main__":
    test_user_data()
