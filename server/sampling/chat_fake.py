"""
Prompt cho LLM n8n sinh chat
tạo cho tôi một cuộc hoại thoại giữa khách và nhân viên chăm sóc da của Mailisa spa để làm dữ liệu mẫu, cấu trúc ví dụ như sau:
```
[
  {
    "side": "client",
    "message": {
      "text": "Xin chào"
    }
  },
  {
    "side": "staff",
    "message": {
      "text": "Xin chào, bạn cần hỗ trợ gì"
    }
  }
]
```
Thông tin khác:
- TỔNG HỢP CÁC DỊCH VỤ CỦA MAILISA
1-Phun mày chạm hạt sương bay
2-Phun môi tán màu light touch
3-Phun mí mở tròng
4-Xóa sửa mày
5-Xóa sửa môi
6-Xóa sửa mí
7-Điều trị nám đinh
8-Điều trị nám mảng
9-Điều trị bớt sắc tố
10-Điều trị sẹo rỗ
11-Điều trị tàn nhang
12-Điều trị da mụn
13-Xóa nốt ruồi
14-Xóa mụn thịt
15-Nâng cung chân mày Perfect Form
16-Tạo hình mắt 2 mí Perfect Line
17-Khâu tạo hình mắt 2 mí
18-Phẫu thuật cắt da dư lấy bọng mỡ mi dưới
19-Phẫu thuật nâng mũi
20-Phẫu thuật thu gọn cánh mũi
21-Thu gọn môi dày
22-Độn cằm
=> Tổng cộng là 22 dịch vụ
- Nói về dịch vụ số ```{{ $now.toMillis() % 22 }}```
- MỘT SỐ THÔNG TIN KHÁC VỀ MAILISA
THÔNG TIN LIÊN HỆ: 
Số HOTLINE: 0932 699 299 - 0931 699 299
Trang website chính thức: https://mailisa.com/
Thời gian làm việc: 7:30 - 18:00 (Từ thứ 2 - CN)
Các cơ sở Mailisa:
Hà Nội: 
Số 6 Đường Nguyễn Khánh Toàn, Quan Hoa, Cầu Giấy, Hà Nội, Việt Nam
Nha Trang:
69/1 Tô Hiến Thành, Tân Lập, Nha Trang, Khánh Hòa
Đắk Lắk:
71 Ngô Quyền, Tân Lợi, Thành phố Buôn Ma Thuột, Đắk Lắk , Việt Nam
Đà Nẵng:
97-99 Đ Nguyễn Văn Linh, Phường Nam Dương, Hải Châu, Đà Nẵng , Việt Nam
Vinh:
132 Nguyễn Văn Cừ, Khối Bình Phúc, Thành phố Vinh, Nghệ An , Việt Nam
TP Hồ Chí Minh:
86-88-92 Huỳnh Văn Bánh, Phường 15, Quận Phú Nhuận, Tp. Hồ Chí Minh,
Bình Dương:
E3/16 Tổ 32, Kp. Bình Thuận 2, P. Thuận Giao, Tp. Thuận An, Tỉnh. Bình Dương
Cần Thơ:
67 Phan Đình Phùng, Tân An, Ninh Kiều, Cần Thơ , Việt Nam
Phú Quốc:
98 Đ. 30 Tháng 4, Khu phố 1, Phú Quốc, Kiên Giang, Việt Nam
-Khách có thể ở các tỉnh:
1-Hà Nội
2-Nha Trang
3-Đắk Lắk
4-Đà Nẵng
5-Vinh
6-TP Hồ Chí Minh
7-Bình Dương
8-Cần Thơ
9-Phú Quốc
Chọn khách ở tỉnh số ```{{ $now.toMillis() % 9 }}```
Chỉ trả về kết quả json
"""
