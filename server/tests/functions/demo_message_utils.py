"""
Demo script để test hàm parse_and_format_message với các trường hợp thực tế
"""

import os
import sys

from app.utils.message_utils import parse_and_format_message

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))


def print_separator(title):
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)


def print_result(result):
    print(f"Số parts: {len(result)}")
    for i, part in enumerate(result, 1):
        print(
            f"  Part {i}: [{part.type}] {part.payload[:100]}{'...' if len(part.payload) > 100 else ''}"
        )


def demo_case_1():
    """Case 1: Text với markdown links và media files"""
    print_separator("CASE 1: Text + Markdown Links + Media Files")

    message = """
    # Báo cáo dự án tuần này
    
    Chào cả team! Đây là update của tuần này:
    
    ## Screenshots UI mới
    ![New UI](https://example.com/ui-screenshot.png)
    
    ## Video demo
    Các bạn xem demo tại: https://example.com/demo-video.mp4
    
    ## Tài liệu tham khảo
    - [API Documentation](https://docs.example.com/api)
    - [Design Guidelines](https://design.example.com)
    - [Project Wiki](https://wiki.example.com/project)
    
    ## Files đính kèm
    - Spec file: https://example.com/project-spec.pdf
    - Database schema: https://example.com/schema.sql
    
    ## Next steps
    Ngày mai sẽ có meeting lúc 9h. Link meeting: [Zoom](https://zoom.us/meeting/123)
    
    Thanks!
    """

    print("Input message:")
    print(message)
    print("\nResult:")
    result = parse_and_format_message(message)
    print_result(result)


def demo_case_2():
    """Case 2: Chỉ có markdown links, không có media"""
    print_separator("CASE 2: Chỉ có Markdown Links")

    message = """
    Đây là một số resources hữu ích cho việc học:
    
    - [MDN Web Docs](https://developer.mozilla.org) - Documentation tốt nhất
    - [W3Schools](https://w3schools.com) - Tutorials đơn giản
    - [GitHub](https://github.com) - Source code repository
    - [Stack Overflow](https://stackoverflow.com) - Q&A community
    
    Website của công ty: https://ourcompany.com
    Contact email: contact@ourcompany.com
    """

    print("Input message:")
    print(message)
    print("\nResult:")
    result = parse_and_format_message(message)
    print_result(result)


def demo_case_3():
    """Case 3: Chỉ có media files"""
    print_separator("CASE 3: Chỉ có Media Files")

    message = """
    https://example.com/photo1.jpg
    https://example.com/photo2.png
    ![Chart](https://example.com/chart.svg)
    
    https://example.com/presentation.pdf
    https://example.com/meeting-recording.mp3
    https://example.com/tutorial.mp4
    """

    print("Input message:")
    print(message)
    print("\nResult:")
    result = parse_and_format_message(message)
    print_result(result)


def demo_case_4():
    """Case 4: Text dài bị chia nhỏ"""
    print_separator("CASE 4: Text dài bị chia nhỏ")

    # Tạo một tin nhắn dài
    long_text = (
        """
    Đây là một báo cáo rất dài về dự án. """
        * 30
    )

    long_text += (
        """
    
    ![Progress Chart](https://example.com/progress.png)
    
    """
        + "Thêm nhiều nội dung chi tiết về tiến độ dự án. " * 50
    )

    long_text += """
    
    Tham khảo thêm tại: [Documentation](https://docs.example.com)
    
    Video tutorial: https://example.com/tutorial.mp4
    """

    print(f"Input message length: {len(long_text)} characters")
    print("Input message (first 200 chars):")
    print(long_text[:200] + "...")
    print("\nResult:")
    result = parse_and_format_message(long_text, char_limit=500)
    print_result(result)


def demo_case_5():
    """Case 5: Mixed content với markdown separators"""
    print_separator("CASE 5: Mixed Content với Markdown Separators")

    message = """
    # Section 1: Images
    ![Image 1](https://example.com/img1.jpg)
    Check out [our gallery](https://gallery.example.com)
    
    ---
    
    ## Section 2: Videos
    Training video: https://example.com/training.mp4
    More videos at [YouTube channel](https://youtube.com/channel/123)
    
    ***
    
    ### Section 3: Documents
    - Manual: https://example.com/manual.pdf
    - [Quick start guide](https://guide.example.com)
    - [FAQ](https://faq.example.com)
    
    ===
    
    #### Section 4: Audio
    Podcast: https://example.com/podcast.mp3
    """

    print("Input message:")
    print(message)
    print("\nResult:")
    result = parse_and_format_message(message)
    print_result(result)


def run_all_demos():
    """Chạy tất cả demos"""
    print("🚀 DEMO: parse_and_format_message Function")
    print(
        "Mục đích: Tách media files (image, video, audio, file) ra riêng, giữ nguyên markdown links trong text"
    )

    demo_case_1()
    demo_case_2()
    demo_case_3()
    demo_case_4()
    demo_case_5()

    print_separator("SUMMARY")
    print(
        "✅ Media files (jpg, png, mp4, mp3, pdf, etc.) được tách ra thành các MessagePart riêng"
    )
    print("✅ Markdown links [text](url) được giữ nguyên trong text")
    print("✅ Text dài được chia nhỏ theo char_limit")
    print("✅ Markdown separators (---, ***, ===, ###) được sử dụng để chia sections")
    print("✅ Hỗ trợ cả markdown media syntax ![alt](url) và bare URLs")


if __name__ == "__main__":
    run_all_demos()
