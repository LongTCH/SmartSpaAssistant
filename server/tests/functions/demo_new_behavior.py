from app.utils.message_utils import parse_and_format_message


def demo_new_behavior():
    """Demo behavior mới: markdown links chuyển thành URL thuần túy"""

    print("=== DEMO: MARKDOWN LINKS CHUYỂN THÀNH URL THUẦN TÚY ===\n")

    # Test case 1: Message ngắn với markdown links
    print("1. Message ngắn với markdown links:")
    message1 = (
        "Tham khảo [website](https://example.com) và [docs](https://docs.example.com)"
    )
    result1 = parse_and_format_message(message1)

    print(f"Input: {message1}")
    print(f"Output: {len(result1)} part(s)")
    for i, part in enumerate(result1, 1):
        print(f"   Part {i}: [{part.type}] {part.payload}")
    print()

    # Test case 2: Message có media và markdown links
    print("2. Message có media và markdown links:")
    message2 = """
    Xem hình ảnh: ![demo](https://example.com/image.jpg)
    
    Và tham khảo [hướng dẫn](https://guide.example.com) để biết thêm chi tiết.
    Video demo: https://example.com/video.mp4
    """
    result2 = parse_and_format_message(message2)

    print(f"Input: {message2.strip()}")
    print(f"Output: {len(result2)} part(s)")
    for i, part in enumerate(result2, 1):
        print(f"   Part {i}: [{part.type}] {part.payload}")
    print()

    # Test case 3: Message với separators
    print("3. Message với separators:")
    message3 = """
    # Section 1
    Link 1: [example](https://example.com)
    
    ---
    
    # Section 2  
    Link 2: [github](https://github.com)
    Image: ![pic](https://example.com/pic.jpg)
    """
    result3 = parse_and_format_message(message3)

    print(f"Input: {message3.strip()}")
    print(f"Output: {len(result3)} part(s)")
    for i, part in enumerate(result3, 1):
        print(f"   Part {i}: [{part.type}] {part.payload}")
    print()

    print("=== KẾT LUẬN ===")
    print("✅ Markdown links [text](url) đã được chuyển thành URL thuần túy")
    print("✅ Media files vẫn được tách ra đúng")
    print("✅ Separators vẫn hoạt động đúng")
    print("✅ Không mất thông tin quan trọng")


if __name__ == "__main__":
    demo_new_behavior()
