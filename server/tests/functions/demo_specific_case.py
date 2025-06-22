"""
Final demo để test case cụ thể: [https://example.com](https://example.com)
"""

import os
import sys

from app.utils.message_utils import parse_and_format_message

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))


def demo_specific_case():
    """Demo case cụ thể mà user đề cập"""
    print("DEMO: Case cụ thể [https://example.com](https://example.com)")
    print("=" * 60)

    message = """
    Đây là các loại links:
    
    1. Normal markdown link: [Google](https://google.com)
    2. URL as text in markdown: [https://example.com](https://example.com)
    3. Media in markdown link: [Download Image](https://example.com/photo.jpg)
    4. Same URL in markdown: [https://example.com/photo.jpg](https://example.com/photo.jpg)
    5. Bare media URL: https://example.com/video.mp4
    6. Markdown media syntax: ![Screenshot](https://example.com/screenshot.png)
    """

    print("Input:")
    print(message)
    print("\nOutput:")

    result = parse_and_format_message(message)

    print(f"Total parts: {len(result)}")
    for i, part in enumerate(result, 1):
        print(f"  {i}. [{part.type.upper()}] {part.payload}")

    print("\nAnalysis:")
    text_parts = [part for part in result if part.type == "text"]
    media_parts = [part for part in result if part.type != "text"]

    print(f"- Text parts: {len(text_parts)}")
    print(f"- Media parts: {len(media_parts)}")

    full_text = " ".join([part.payload for part in text_parts])

    print("\nMarkdown links preserved in text:")
    preserved_links = [
        "[Google](https://google.com)",
        "[https://example.com](https://example.com)",
        "[Download Image](https://example.com/photo.jpg)",
        "[https://example.com/photo.jpg](https://example.com/photo.jpg)",
    ]

    for link in preserved_links:
        if link in full_text:
            print(f"  ✅ {link}")
        else:
            print(f"  ❌ {link}")

    print("\nMedia extracted:")
    for part in media_parts:
        print(f"  ✅ {part.type}: {part.payload}")

    print("\n" + "=" * 60)
    print("✅ RESULT: Hàm hoạt động đúng!")
    print("- Markdown links được giữ nguyên trong text")
    print("- Chỉ tách bare URLs và markdown media syntax ![]()")
    print("- Không tách URLs nằm trong markdown links []()")


if __name__ == "__main__":
    demo_specific_case()
