"""
Test case cụ thể cho vấn đề markdown links như [https://example.com](https://example.com)
"""

import os
import sys

from app.utils.message_utils import parse_and_format_message

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))


def test_markdown_links_with_same_url():
    """Test markdown links có text và URL giống nhau"""
    message = """
    Đây là một số links:
    - [https://example.com](https://example.com) - Website chính
    - [https://docs.example.com](https://docs.example.com) - Documentation  
    - [https://github.com/user/repo](https://github.com/user/repo) - Source code
    
    Và một bare URL: https://google.com
    """

    result = parse_and_format_message(message)

    # Chỉ có text parts, không có media parts
    text_parts = [part for part in result if part.type == "text"]
    media_parts = [
        part for part in result if part.type in ["image", "video", "audio", "file"]
    ]

    print(f"Text parts: {len(text_parts)}")
    print(f"Media parts: {len(media_parts)}")

    for i, part in enumerate(result):
        print(f"Part {i+1}: [{part.type}] {part.payload[:100]}...")

    assert (
        len(media_parts) == 0
    ), f"Không nên có media parts, nhưng có {len(media_parts)}"
    assert len(text_parts) > 0, "Phải có text parts"

    # Kiểm tra markdown links vẫn còn trong text
    full_text = " ".join([part.payload for part in text_parts])
    assert "[https://example.com](https://example.com)" in full_text
    assert "[https://docs.example.com](https://docs.example.com)" in full_text
    assert "[https://github.com/user/repo](https://github.com/user/repo)" in full_text
    assert "https://google.com" in full_text

    print("✅ Test markdown links with same URL passed")


def test_mixed_markdown_and_media():
    """Test markdown links trộn với media files"""
    message = """
    Links thông thường:
    - [https://example.com](https://example.com)
    - [Documentation](https://docs.example.com)
    
    Media files:
    - Image: https://example.com/photo.jpg
    - ![Chart](https://example.com/chart.png)
    - Video: https://example.com/video.mp4
    
    Thêm links:
    - [https://github.com](https://github.com)
    """

    result = parse_and_format_message(message)

    text_parts = [part for part in result if part.type == "text"]
    image_parts = [part for part in result if part.type == "image"]
    video_parts = [part for part in result if part.type == "video"]

    print(f"\nMixed content test:")
    print(f"Text parts: {len(text_parts)}")
    print(f"Image parts: {len(image_parts)}")
    print(f"Video parts: {len(video_parts)}")

    for i, part in enumerate(result):
        print(f"Part {i+1}: [{part.type}] {part.payload[:80]}...")

    # Phải có 2 image và 1 video
    assert len(image_parts) == 2, f"Expected 2 images, got {len(image_parts)}"
    assert len(video_parts) == 1, f"Expected 1 video, got {len(video_parts)}"

    # Kiểm tra URLs
    image_urls = [part.payload for part in image_parts]
    assert "https://example.com/photo.jpg" in image_urls
    assert "https://example.com/chart.png" in image_urls
    assert video_parts[0].payload == "https://example.com/video.mp4"

    # Kiểm tra markdown links vẫn trong text
    full_text = " ".join([part.payload for part in text_parts])
    assert "[https://example.com](https://example.com)" in full_text
    assert "[Documentation](https://docs.example.com)" in full_text
    assert "[https://github.com](https://github.com)" in full_text

    print("✅ Test mixed markdown and media passed")


def test_media_extension_in_markdown_link():
    """Test trường hợp URL trong markdown link có extension media nhưng không phải media file thực sự"""
    message = """
    Đây là các links đến trang có tên file giống media:
    - [Download photo.jpg](https://example.com/download/photo.jpg) - Link download
    - [View video.mp4](https://example.com/view/video.mp4) - Link xem video
    - [Get document.pdf](https://example.com/get/document.pdf) - Link tài liệu
    
    Còn đây là media files thực sự:
    https://cdn.example.com/actual-photo.jpg
    https://cdn.example.com/actual-video.mp4
    """

    result = parse_and_format_message(message)

    text_parts = [part for part in result if part.type == "text"]
    image_parts = [part for part in result if part.type == "image"]
    video_parts = [part for part in result if part.type == "video"]

    print(f"\nMedia extension in markdown test:")
    print(f"Text parts: {len(text_parts)}")
    print(f"Image parts: {len(image_parts)}")
    print(f"Video parts: {len(video_parts)}")

    for i, part in enumerate(result):
        print(f"Part {i+1}: [{part.type}] {part.payload[:80]}...")

    # Chỉ có 2 media files thực sự (bare URLs)
    assert len(image_parts) == 1, f"Expected 1 image, got {len(image_parts)}"
    assert len(video_parts) == 1, f"Expected 1 video, got {len(video_parts)}"

    # Kiểm tra URLs
    assert image_parts[0].payload == "https://cdn.example.com/actual-photo.jpg"
    assert video_parts[0].payload == "https://cdn.example.com/actual-video.mp4"

    # Kiểm tra markdown links vẫn trong text (không bị tách)
    full_text = " ".join([part.payload for part in text_parts])
    assert "[Download photo.jpg](https://example.com/download/photo.jpg)" in full_text
    assert "[View video.mp4](https://example.com/view/video.mp4)" in full_text
    assert "[Get document.pdf](https://example.com/get/document.pdf)" in full_text

    print("✅ Test media extension in markdown link passed")


def run_specific_tests():
    """Chạy các tests cụ thể cho vấn đề markdown links"""
    print("🔧 Testing specific markdown link issues...")
    print("=" * 60)

    try:
        test_markdown_links_with_same_url()
        test_mixed_markdown_and_media()
        test_media_extension_in_markdown_link()

        print("=" * 60)
        print("🎉 Tất cả tests cho markdown links đều PASSED!")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    run_specific_tests()
