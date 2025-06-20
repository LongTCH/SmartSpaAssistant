"""
Test file for message_utils.py - focusing on parse_and_format_message function
"""

import os
import sys

from app.utils.message_utils import parse_and_format_message

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))


def test_text_only():
    """Test với chỉ có text, không có media hoặc links"""
    message = "Đây là một tin nhắn đơn giản chỉ có text. Không có media hoặc links."
    result = parse_and_format_message(message)

    assert len(result) == 1
    assert result[0].type == "text"
    assert result[0].payload == message
    print("✓ Test text only passed")


def test_markdown_links_preserved():
    """Test markdown links được giữ nguyên trong text"""
    message = """
    Đây là một số links hữu ích:
    - [Google](https://google.com) để tìm kiếm
    - [GitHub](https://github.com) để code
    - [StackOverflow](https://stackoverflow.com) để hỏi đáp
    
    Và một link thông thường: https://example.com
    """
    result = parse_and_format_message(message)

    # Chỉ có text parts, không có media parts
    text_parts = [part for part in result if part.type == "text"]
    media_parts = [
        part for part in result if part.type in ["image", "video", "audio", "file"]
    ]

    assert len(media_parts) == 0, "Không nên có media parts"
    assert len(text_parts) > 0, "Phải có text parts"

    # Kiểm tra markdown links vẫn còn trong text
    full_text = " ".join([part.payload for part in text_parts])
    assert "[Google](https://google.com)" in full_text
    assert "[GitHub](https://github.com)" in full_text
    assert "https://example.com" in full_text
    print("✓ Test markdown links preserved passed")


def test_image_extraction():
    """Test tách image ra khỏi text"""
    message = """
    Đây là một số hình ảnh:
    ![Alt text](https://example.com/image.jpg)
    
    Và một bare image URL: https://example.com/photo.png
    
    Cùng với text bình thường và [một link](https://example.com).
    """
    result = parse_and_format_message(message)

    text_parts = [part for part in result if part.type == "text"]
    image_parts = [part for part in result if part.type == "image"]

    assert len(image_parts) == 2, f"Expected 2 image parts, got {len(image_parts)}"
    assert "https://example.com/image.jpg" in [part.payload for part in image_parts]
    assert "https://example.com/photo.png" in [part.payload for part in image_parts]

    # Kiểm tra links vẫn còn trong text
    full_text = " ".join([part.payload for part in text_parts])
    assert "[một link](https://example.com)" in full_text
    print("✓ Test image extraction passed")


def test_multiple_media_types():
    """Test tách nhiều loại media khác nhau"""
    message = """
    Đây là collection media:
    
    Hình ảnh: ![Photo](https://example.com/image.jpg)
    Video: https://example.com/video.mp4
    Audio: https://example.com/song.mp3
    File: https://example.com/document.pdf
    
    Và một số links thông thường:
    - [Website](https://example.com)
    - [Documentation](https://docs.example.com)
    """
    result = parse_and_format_message(message)

    image_parts = [part for part in result if part.type == "image"]
    video_parts = [part for part in result if part.type == "video"]
    audio_parts = [part for part in result if part.type == "audio"]
    file_parts = [part for part in result if part.type == "file"]
    text_parts = [part for part in result if part.type == "text"]

    assert len(image_parts) == 1
    assert len(video_parts) == 1
    assert len(audio_parts) == 1
    assert len(file_parts) == 1

    # Kiểm tra URLs
    assert image_parts[0].payload == "https://example.com/image.jpg"
    assert video_parts[0].payload == "https://example.com/video.mp4"
    assert audio_parts[0].payload == "https://example.com/song.mp3"
    assert file_parts[0].payload == "https://example.com/document.pdf"

    # Kiểm tra links vẫn còn trong text
    full_text = " ".join([part.payload for part in text_parts])
    assert "[Website](https://example.com)" in full_text
    assert "[Documentation](https://docs.example.com)" in full_text
    print("✓ Test multiple media types passed")


def test_markdown_separators():
    """Test chia theo markdown separators"""
    message = """
    # Section 1
    Text in section 1 with [link](https://example.com)
    
    ---
    
    ## Section 2
    ![Image](https://example.com/image.jpg)
    More text here.
    
    ***
    
    ### Section 3
    https://example.com/video.mp4
    Final text.
    """
    result = parse_and_format_message(message)

    text_parts = [part for part in result if part.type == "text"]
    image_parts = [part for part in result if part.type == "image"]
    video_parts = [part for part in result if part.type == "video"]

    assert len(image_parts) == 1
    assert len(video_parts) == 1

    # Kiểm tra links vẫn trong text
    full_text = " ".join([part.payload for part in text_parts])
    assert "[link](https://example.com)" in full_text
    print("✓ Test markdown separators passed")


def test_long_text_splitting():
    """Test chia text dài"""
    # Tạo text dài hơn 2000 ký tự
    long_text = "Đây là một câu dài. " * 150  # ~3000 ký tự
    long_text += "\n\n![Image](https://example.com/image.jpg)\n\n"
    long_text += "Và thêm text nữa. " * 50

    result = parse_and_format_message(long_text, char_limit=1000)

    text_parts = [part for part in result if part.type == "text"]
    image_parts = [part for part in result if part.type == "image"]

    assert len(image_parts) == 1
    assert len(text_parts) > 1, "Text dài phải được chia thành nhiều parts"

    # Kiểm tra mỗi text part không vượt quá char_limit
    for part in text_parts:
        assert len(part.payload) <= 1000, f"Text part quá dài: {len(part.payload)}"

    print("✓ Test long text splitting passed")


def test_edge_cases():
    """Test các trường hợp edge cases"""

    # Empty message
    result = parse_and_format_message("")
    assert len(result) == 0

    # Only whitespace
    result = parse_and_format_message("   \n\n   ")
    assert len(result) == 0

    # Only media
    result = parse_and_format_message("https://example.com/image.jpg")
    assert len(result) == 1
    assert result[0].type == "image"

    # Media with query parameters
    result = parse_and_format_message("https://example.com/image.jpg?v=123&size=large")
    assert len(result) == 1
    assert result[0].type == "image"
    assert "?v=123&size=large" in result[0].payload

    print("✓ Test edge cases passed")


def test_mixed_content():
    """Test nội dung hỗn hợp phức tạp"""
    message = """
    # Báo cáo hàng tuần
    
    Chào mọi người! Đây là báo cáo của tuần này.
    
    ## Hình ảnh
    ![Screenshot](https://example.com/screenshot.png)
    
    ## Video demo
    https://example.com/demo.mp4
    
    ## Tài liệu tham khảo
    - [Tài liệu API](https://docs.example.com/api)
    - [Hướng dẫn](https://guide.example.com)
    - File PDF: https://example.com/manual.pdf
    
    ---
    
    ## Âm thanh
    https://example.com/recording.mp3
    
    Cảm ơn mọi người!
    
    Contact: [email](mailto:admin@example.com)
    """

    result = parse_and_format_message(message)

    # Đếm các loại parts
    text_parts = [part for part in result if part.type == "text"]
    image_parts = [part for part in result if part.type == "image"]
    video_parts = [part for part in result if part.type == "video"]
    audio_parts = [part for part in result if part.type == "audio"]
    file_parts = [part for part in result if part.type == "file"]

    assert len(image_parts) == 1
    assert len(video_parts) == 1
    assert len(audio_parts) == 1
    assert len(file_parts) == 1

    # Kiểm tra tất cả links vẫn trong text
    full_text = " ".join([part.payload for part in text_parts])
    assert "[Tài liệu API](https://docs.example.com/api)" in full_text
    assert "[Hướng dẫn](https://guide.example.com)" in full_text
    assert "[email](mailto:admin@example.com)" in full_text

    print("✓ Test mixed content passed")


def run_all_tests():
    """Chạy tất cả tests"""
    print("Bắt đầu chạy tests cho parse_and_format_message...")
    print("=" * 50)

    try:
        test_text_only()
        test_markdown_links_preserved()
        test_image_extraction()
        test_multiple_media_types()
        test_markdown_separators()
        test_long_text_splitting()
        test_edge_cases()
        test_mixed_content()

        print("=" * 50)
        print("🎉 Tất cả tests đều PASSED!")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
