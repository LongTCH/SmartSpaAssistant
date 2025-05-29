# SSL Certificate Validation

Thư mục này được sử dụng để lưu trữ các file xác thực SSL certificate.

## Cách sử dụng:

1. Khi apply cho SSL certificate từ các nhà cung cấp (Let's Encrypt, SSL.com, v.v.), họ sẽ yêu cầu bạn đặt một file xác thực vào thư mục này.

2. File xác thực thường có tên dạng: `xxxxx.txt` hoặc `xxxxx.html`

3. Đặt file đó vào thư mục này: `nginx/ssl-validation/.well-known/pki-validation/`

4. File sẽ có thể truy cập được qua: `http://yourdomain.com/.well-known/pki-validation/filename`

## Ví dụ:

Nếu bạn có file xác thực tên `verification123.txt`, đặt nó vào đây và truy cập qua:
`http://yourdomain.com/.well-known/pki-validation/verification123.txt`
