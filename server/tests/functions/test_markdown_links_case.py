"""
Test case với markdown links trong message
"""

import os
import sys

from app.utils.message_utils import parse_and_format_message

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))


def test_markdown_links_case():
    """Test case với markdown links trong message"""
    message = """### Các sản phẩm trị mụn giá dưới 1 triệu tại Mailisa 🌟

1. **M01 – KEM LOẠI BỎ SẮC TỐ**
   - **Giá:** 750.000 Đ
   - **Mô tả:** Giúp loại bỏ thâm, sạm, nám trên bề mặt da, làm sáng da và cải thiện làn da vàng sậm màu.
   - **[Xem chi tiết và mua hàng](https://mailisa.com/kem-loai-bo-sac-to/)**

---

2. **M19 – SỮA RỬA MẶT SẠCH SÂU ACID AMINO**
   - **Giá:** 299.000 Đ
   - **Mô tả:** Làm sạch da sâu từ bên trong, cung cấp dưỡng chất và cân bằng độ ẩm, giúp da mềm mại và mịn màng.
   - **[Xem chi tiết và mua hàng](https://mailisa.com/san-pham/sua-rua-mat-sach-sau-acid-amino/)**

---

3. **M23 – KEM CHỐNG NẮNG CHE KHUYẾT ĐIỂM BB NANO**
   - **Giá:** 399.000 Đ
   - **Mô tả:** Cung cấp dưỡng chất và độ ẩm cho da, giúp da săn chắc và đều màu, bảo vệ da khỏi tác động của ánh nắng mặt trời.
   - **[Xem chi tiết và mua hàng](https://mailisa.com/san-pham/kem-chong-nang-che-khuyet-diem-bb-nano/)**

---

Nếu Chị cần thêm thông tin hoặc muốn đặt hàng, hãy cho em biết nhé! 💖"""

    print("Testing markdown links case...")
    print(f"Message length: {len(message)} characters")
    print("=" * 60)

    result = parse_and_format_message(message)

    print(f"Number of parts: {len(result)}")
    print("\nParts breakdown:")

    for i, part in enumerate(result, 1):
        print(f"\nPart {i}: [{part.type.upper()}] ({len(part.payload)} chars)")
        print("-" * 40)
        print(part.payload)
        print("-" * 40)

    # Kiểm tra xem có markdown links trong kết quả không
    full_text = " ".join([part.payload for part in result if part.type == "text"])

    if "[Xem chi tiết và mua hàng]" in full_text:
        print("\n⚠️  FOUND markdown links in text - cần xử lý")

        # Tìm các markdown links
        import re

        links = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", full_text)
        print(f"Found {len(links)} markdown links:")
        for i, (text, url) in enumerate(links, 1):
            print(f"  {i}. [{text}]({url})")
    else:
        print("\n✅ No markdown links found in text")


if __name__ == "__main__":
    test_markdown_links_case()
