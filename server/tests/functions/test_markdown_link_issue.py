"""
Test specific case for markdown links with URLs as text
"""

import os
import sys

from app.utils.message_utils import parse_and_format_message

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))


def test_markdown_link_with_url_as_text():
    """Test markdown links where the text is also a URL like [https://example.com](https://example.com)"""
    message = """
    Here are some links:
    - [https://example.com](https://example.com) - Website homepage
    - [https://docs.example.com](https://docs.example.com) - Documentation
    - [https://github.com/user/repo](https://github.com/user/repo) - Source code
    
    And some media files:
    - Image: https://example.com/photo.jpg
    - Video: https://example.com/video.mp4
    """

    result = parse_and_format_message(message)

    # Check that we have both text and media parts
    text_parts = [part for part in result if part.type == "text"]
    image_parts = [part for part in result if part.type == "image"]
    video_parts = [part for part in result if part.type == "video"]

    print(f"Total parts: {len(result)}")
    for i, part in enumerate(result, 1):
        print(f"  Part {i}: [{part.type}] {part.payload}")

    # Should have media parts
    assert len(image_parts) == 1, f"Expected 1 image part, got {len(image_parts)}"
    assert len(video_parts) == 1, f"Expected 1 video part, got {len(video_parts)}"

    # Check media URLs
    assert image_parts[0].payload == "https://example.com/photo.jpg"
    # Check that markdown links đã được chuyển thành URL thuần túy
    assert video_parts[0].payload == "https://example.com/video.mp4"
    full_text = " ".join([part.payload for part in text_parts])
    assert "https://example.com" in full_text
    assert "https://docs.example.com" in full_text
    assert "https://github.com/user/repo" in full_text

    # Không còn markdown syntax
    assert "[https://example.com]" not in full_text

    print("✅ Test markdown link with URL as text PASSED")


def test_mixed_markdown_and_bare_urls():
    """Test mix of markdown links and bare URLs"""
    message = """
    Various link formats:
    
    Markdown links:
    - [Google](https://google.com)
    - [https://example.com](https://example.com)
    - [Download PDF](https://example.com/document.pdf)
    
    Bare URLs (non-media):
    - https://website.com
    - https://api.example.com/endpoint
    
    Media files:
    - https://example.com/image.png
    - https://example.com/video.mp4
    """

    result = parse_and_format_message(message)

    text_parts = [part for part in result if part.type == "text"]
    image_parts = [part for part in result if part.type == "image"]
    video_parts = [part for part in result if part.type == "video"]

    print(f"\nTotal parts: {len(result)}")
    for i, part in enumerate(result, 1):
        # Should extract media files (bao gồm cả PDF trong markdown link)
        print(f"  Part {i}: [{part.type}] {part.payload}")
    assert len(image_parts) == 1
    assert len(video_parts) == 1

    # File parts should include PDF từ markdown link
    file_parts = [part for part in result if part.type == "file"]
    assert len(file_parts) == 1
    assert file_parts[0].payload == "https://example.com/document.pdf"

    # All markdown links đã được chuyển thành URL thuần túy
    full_text = " ".join([part.payload for part in text_parts])
    assert "https://google.com" in full_text
    assert "https://example.com" in full_text
    assert "https://example.com/document.pdf" in full_text  # PDF URL vẫn trong text

    # Bare non-media URLs should be preserved
    assert "https://website.com" in full_text
    assert "https://api.example.com/endpoint" in full_text

    # Không còn markdown syntax
    assert "[Google]" not in full_text

    print("✅ Test mixed markdown and bare URLs PASSED")


def test_edge_case_markdown_links():
    """Test edge cases with markdown links"""
    message = """
    Edge cases:
    
    1. Media file in markdown link: [Image](https://example.com/photo.jpg)
    2. Media file with same URL: [https://example.com/photo.jpg](https://example.com/photo.jpg)
    3. Regular link: [Website](https://example.com)
    4. Bare media URL: https://example.com/video.mp4
    5. URL with query params: [API](https://api.example.com?param=value)
    """

    result = parse_and_format_message(message)

    text_parts = [part for part in result if part.type == "text"]
    image_parts = [part for part in result if part.type == "image"]
    video_parts = [part for part in result if part.type == "video"]

    print(f"\nTotal parts: {len(result)}")
    for i, part in enumerate(result, 1):
        # Should extract media files bao gồm cả trong markdown links
        print(f"  Part {i}: [{part.type}] {part.payload}")
    assert (
        len(image_parts) == 2
    ), f"Expected 2 image parts (both from markdown links), got {len(image_parts)}"
    assert (
        len(video_parts) == 1
    ), f"Expected 1 video part (bare URL), got {len(video_parts)}"

    # Check that bare media URL is extracted
    assert video_parts[0].payload == "https://example.com/video.mp4"

    # Check image URLs from markdown links
    image_urls = [part.payload for part in image_parts]
    assert "https://example.com/photo.jpg" in image_urls

    # Check that ALL markdown links đã được chuyển thành URL thuần túy (even those with media URLs)
    full_text = " ".join([part.payload for part in text_parts])
    assert "https://example.com/photo.jpg" in full_text  # From markdown links
    assert "https://example.com" in full_text
    assert "https://api.example.com?param=value" in full_text

    # Không còn markdown syntax
    assert "[Image]" not in full_text
    assert "[Website]" not in full_text
    assert "[API]" not in full_text

    print("✅ Test edge case markdown links PASSED")


if __name__ == "__main__":
    print("Testing markdown links with URLs as text...")
    print("=" * 60)

    try:
        test_markdown_link_with_url_as_text()
        test_mixed_markdown_and_bare_urls()
        test_edge_case_markdown_links()

        print("=" * 60)
        print("🎉 All markdown link tests PASSED!")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
