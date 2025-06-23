#!/usr/bin/env python3

import os
import sys

from utils.message_utils import parse_and_format_message

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "app"))


def test_mailisa_services_with_separators():
    """Test message with content wrapped in separators (--- lines)"""
    message = """---
Mailisa cung cấp đa dạng dịch vụ thẩm mỹ, bao gồm:

- **Phẫu thuật:** Nâng mũi, nhấn mí, cắt mí, nâng cung chân mày, thu gọn cánh mũi, cắt da dư bọng mỡ mi dưới, thu gọn môi dày.
- **Phun xăm:** Phun chân mày chạm hạt sương bay, phun môi tán màu Light Touch, phun mí mở tròng.
- **Làm đẹp da bằng công nghệ cao:** Điều trị da nám, mụn, sẹo rỗ, tàn nhang...
- **Tiêm thẩm mỹ:** Botox, Filler, Meso, Bap.

Nếu Anh/Chị cần tư vấn chi tiết hơn về dịch vụ nào, em rất sẵn lòng hỗ trợ nhé! 🌸😊

---"""

    result = parse_and_format_message(message)

    # Should return exactly 1 text part
    assert len(result) == 1, f"Expected 1 part, got {len(result)}"
    assert result[0].type == "text", f"Expected text type, got {result[0].type}"

    content = result[0].payload

    # Separators should be removed
    assert "---" not in content, "Separators should be removed from content"

    # Main content should be preserved
    assert "Mailisa cung cấp đa dạng dịch vụ thẩm mỹ" in content
    assert "**Phẫu thuật:**" in content
    assert "**Phun xăm:**" in content
    assert "**Làm đẹp da bằng công nghệ cao:**" in content
    assert "**Tiêm thẩm mỹ:**" in content
    assert "🌸😊" in content

    # Should not start or end with whitespace
    assert content.strip() == content

    print("✅ Mailisa services test passed!")


def test_multiple_separators():
    """Test message with multiple separator sections"""
    message = """---
Section 1 content here

---

Section 2 content here

---

Section 3 content here

---"""

    result = parse_and_format_message(message)

    # Should return 3 text parts
    assert len(result) == 3, f"Expected 3 parts, got {len(result)}"

    for part in result:
        assert part.type == "text"
        assert "---" not in part.payload

    print("✅ Multiple separators test passed!")


def test_empty_sections_with_separators():
    """Test message with empty sections between separators"""
    message = """---


---

Some content here

---


---"""

    result = parse_and_format_message(message)

    # Should return 1 text part (empty sections should be skipped)
    assert len(result) == 1, f"Expected 1 part, got {len(result)}"
    assert result[0].type == "text"
    assert result[0].payload.strip() == "Some content here"

    print("✅ Empty sections test passed!")


if __name__ == "__main__":
    test_mailisa_services_with_separators()
    test_multiple_separators()
    test_empty_sections_with_separators()
    print("All separator tests passed! ✅")
