# Message Utils - parse_and_format_message Function

## Mô tả

Hàm `parse_and_format_message` được thiết kế để phân tích và format tin nhắn markdown, tách các file media ra thành các MessagePart riêng biệt trong khi vẫn giữ nguyên các markdown links trong text.

## Tính năng chính

### ✅ Media Files được tách riêng

- **Images**: `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.svg`, `.webp`
- **Videos**: `.mp4`, `.mov`, `.avi`, `.mkv`, `.flv`, `.webm`
- **Audio**: `.mp3`, `.wav`, `.flac`, `.aac`, `.ogg`, `.m4a`, `.wma`
- **Files**: `.pdf`, `.doc`, `.docx`, `.xls`, `.xlsx`, `.ppt`, `.pptx`, `.txt`, `.csv`, `.zip`, `.rar`, `.7z`

### ✅ Markdown Links được giữ nguyên

- `[text](url)` - Được giữ nguyên trong text parts
- Bare URLs không phải media files - Được giữ nguyên trong text

### ✅ Text Splitting thông minh

- Chia theo markdown separators: `---`, `***`, `___`, `===`, `###`
- Chia theo đoạn văn khi text quá dài
- Chia theo câu và từ khi cần thiết
- Giữ nguyên format và whitespace

## Cách sử dụng

```python
from app.utils.message_utils import parse_and_format_message

# Basic usage
message = """
# Báo cáo tuần này
![Screenshot](https://example.com/image.jpg)
Xem thêm tại [Documentation](https://docs.example.com)
Video demo: https://example.com/demo.mp4
"""

result = parse_and_format_message(message, char_limit=2000)

for part in result:
    print(f"Type: {part.type}, Content: {part.payload}")
```

## Output

Hàm trả về danh sách các `MessagePart` objects:

```python
class MessagePart:
    type: str      # "text", "image", "video", "audio", "file"
    payload: str   # Nội dung (text hoặc URL)
```

## Ví dụ kết quả

### Input:

```markdown
# Report

![Chart](https://example.com/chart.png)
See [documentation](https://docs.example.com)
Video: https://example.com/video.mp4
```

### Output:

```python
[
    MessagePart(type="text", payload="See [documentation](https://docs.example.com)\nVideo:"),
    MessagePart(type="image", payload="https://example.com/chart.png"),
    MessagePart(type="video", payload="https://example.com/video.mp4")
]
```

## Supported Patterns

### Media Files

```markdown
# Markdown syntax

![Alt text](https://example.com/image.jpg)

# Bare URLs

https://example.com/video.mp4
https://example.com/document.pdf
```

### Links (giữ nguyên trong text)

```markdown
[Link text](https://example.com)
https://example.com (không phải media file)
mailto:email@example.com
```

### Markdown Separators

```markdown
---

---

---

===

### Headers
```

## Test Cases

Chạy tests để kiểm tra tính năng:

```bash
# Chạy unit tests
python -m pytest tests/test_message_utils.py -v

# Chạy demo
python tests/demo_message_utils.py
```

## Lưu ý

1. **Media Priority**: Nếu một URL vừa là media file vừa có markdown syntax, nó sẽ được tách ra như media
2. **Text Preservation**: Markdown links `[text](url)` luôn được giữ nguyên trong text parts
3. **Character Limit**: Text parts sẽ được chia nhỏ nếu vượt quá `char_limit` (mặc định: 2000)
4. **Order Preservation**: Thứ tự của content trong message được giữ nguyên

## Dependencies

```python
import re
from typing import List
from app.utils.agent_utils import MessagePart
```
