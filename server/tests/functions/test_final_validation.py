from app.utils.message_utils import parse_and_format_message


def test_real_world_message():
    """Test với message thực tế phức tạp"""
    message = """
    # Danh sách sản phẩm spa
    
    Xin chào! Dưới đây là danh sách các dịch vụ spa và liệu pháp thư giãn:
    
    ## Massage và Liệu pháp
    
    • **Massage toàn thân**: 500,000 VNĐ - [Xem thêm](https://spa.example.com/massage)
    • **Liệu pháp đá nóng**: 800,000 VNĐ 
    • **Massage chân**: 300,000 VNĐ
    
    ![Hình ảnh spa](https://example.com/spa-image.jpg)
    
    ---
    
    ## Chăm sóc da
    
    • **Facial cơ bản**: 400,000 VNĐ - [Đặt lịch](https://booking.spa.com/facial)
    • **Treatment chống lão hóa**: 1,200,000 VNĐ
    • **Mask collagen**: 600,000 VNĐ
    
    Video giới thiệu: https://example.com/intro-video.mp4
    
    ***
    
    ## Thông tin liên hệ
    
    📞 Hotline: [0123-456-789](tel:0123456789)
    📧 Email: [contact@spa.com](mailto:contact@spa.com)
    🌐 Website: [spa.example.com](https://spa.example.com)
    
    Âm thanh thư giãn: https://example.com/relaxing-sounds.mp3
    
    Brochure PDF: https://example.com/brochure.pdf
    """

    result = parse_and_format_message(message)

    # Đếm các loại parts
    text_parts = [part for part in result if part.type == "text"]
    image_parts = [part for part in result if part.type == "image"]
    video_parts = [part for part in result if part.type == "video"]
    audio_parts = [part for part in result if part.type == "audio"]
    file_parts = [part for part in result if part.type == "file"]

    # Kiểm tra media được tách đúng
    assert len(image_parts) == 1
    assert len(video_parts) == 1
    assert len(audio_parts) == 1
    assert len(file_parts) == 1

    # Kiểm tra URLs media
    assert image_parts[0].payload == "https://example.com/spa-image.jpg"
    assert video_parts[0].payload == "https://example.com/intro-video.mp4"
    assert audio_parts[0].payload == "https://example.com/relaxing-sounds.mp3"
    assert file_parts[0].payload == "https://example.com/brochure.pdf"

    # Kiểm tra links đã được chuyển thành URL thuần túy trong text
    full_text = " ".join([part.payload for part in text_parts])

    # Markdown links đã được chuyển thành URL thuần túy
    assert "https://spa.example.com/massage" in full_text
    assert "https://booking.spa.com/facial" in full_text
    assert "tel:0123456789" in full_text
    assert "mailto:contact@spa.com" in full_text
    assert "https://spa.example.com" in full_text
    # Các thông tin quan trọng vẫn còn
    assert "500,000 VNĐ" in full_text
    assert "Massage toàn thân" in full_text
    assert "Facial cơ bản" in full_text
    # Note: "0123-456-789" đã chuyển thành "tel:0123456789" (chỉ giữ URL)

    # Kiểm tra có chia theo separator (có --- và ***)
    assert len(text_parts) >= 3  # Ít nhất 3 sections

    print(f"Tổng số parts: {len(result)}")
    print(f"Text parts: {len(text_parts)}")
    print(f"Media parts: {len(image_parts + video_parts + audio_parts + file_parts)}")


def test_short_message_with_links():
    """Test message ngắn với links - không nên chia"""
    message = (
        "Xem thêm tại [website](https://example.com) và [facebook](https://fb.com/page)"
    )

    result = parse_and_format_message(message)

    # Message ngắn không có media -> chỉ 1 text part
    assert len(result) == 1
    assert result[0].type == "text"

    # Links đã được chuyển thành URL thuần túy
    assert "https://example.com" in result[0].payload
    assert "https://fb.com/page" in result[0].payload
    assert "[website]" not in result[0].payload  # Không còn markdown
    assert "[facebook]" not in result[0].payload


def test_short_message_with_media():
    """Test message ngắn có media - phải tách media"""
    message = "Xem hình: ![image](https://example.com/pic.jpg) và link [here](https://example.com)"

    result = parse_and_format_message(message)

    # Có media nên phải tách
    text_parts = [part for part in result if part.type == "text"]
    image_parts = [part for part in result if part.type == "image"]

    assert len(image_parts) == 1
    assert len(text_parts) == 1

    # Link trong text đã chuyển thành URL thuần túy
    assert "https://example.com" in text_parts[0].payload
    assert "[here]" not in text_parts[0].payload


if __name__ == "__main__":
    test_real_world_message()
    test_short_message_with_links()
    test_short_message_with_media()
    print("Tất cả tests đều pass! ✅")
