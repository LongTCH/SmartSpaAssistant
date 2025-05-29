# SSA (Smart Sales Assistant) - Graduation Project

Dự án tốt nghiệp về hệ thống hỗ trợ bán hàng thông minh sử dụng AI và chatbot.

## Cấu trúc dự án

```
├── server/          # Backend FastAPI
├── web/            # Frontend Next.js
├── nginx/          # Nginx reverse proxy configuration
├── docker-compose.yml
├── .env.example
└── README.md
```

## Yêu cầu hệ thống

- Docker và Docker Compose
- Node.js 18+ (nếu chạy không dùng Docker)
- Python 3.11+ (nếu chạy không dùng Docker)
- PostgreSQL (đã được cấu hình trong Docker)
- Qdrant Vector Database (đã được cấu hình trong Docker)

## Cài đặt và chạy với Docker

### 1. Sao chép file cấu hình môi trường

```powershell
# Copy file .env.example thành .env và cấu hình các biến môi trường
Copy-Item .env.example .env
```

Chỉnh sửa file `.env` với thông tin cần thiết:

```env
# Database Configuration
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_strong_password_here
POSTGRES_DB=ssa_database
```

### 2. Copy và cấu hình file environment cho server

```powershell
cd server
Copy-Item .env.example .env
cd ..
```

Chỉnh sửa file `server/.env` với các API keys và cấu hình cần thiết.

### 3. Chạy với Docker Compose

```powershell
# Build và chạy tất cả các container
docker-compose up --build

# Hoặc chạy ở background
docker-compose up --build -d
```

### 4. Truy cập ứng dụng

Sau khi chạy Docker Compose, tất cả sẽ được truy cập qua cổng 80:

- **Ứng dụng chính**: http://localhost
- **Frontend (Web)**: http://localhost (được route qua Nginx)
- **Backend API**: http://localhost/api (được route qua Nginx đến server:8080)
- **API Documentation**: http://localhost/docs
- **PostgreSQL**: localhost:5432 (chỉ từ bên trong Docker network)
- **Qdrant**: http://localhost:6333

**Lưu ý**: Server và client không còn expose port trực tiếp ra ngoài. Tất cả traffic đều đi qua Nginx reverse proxy.

## Các services trong Docker Compose

### 1. Nginx Reverse Proxy (`nginx`)

- Image: `nginx:alpine`
- Port: `80` (HTTP), `443` (HTTPS - sẵn sàng cho SSL)
- Route các request:
  - `/api/*` → Backend server (port 8080)
  - `/docs`, `/redoc` → API documentation
  - `/static/*` → Static files từ server
  - `/ws` → WebSocket connections
  - `/` → Frontend client (port 3000)
- Cấu hình CORS, rate limiting và security headers

### 2. PostgreSQL Database (`postgres`)

- Image: `groonga/pgroonga:4.0.1-alpine-17`
- Port: `5432` (chỉ trong Docker network)
- Hỗ trợ full-text search với PGroonga

### 3. Qdrant Vector Database (`qdrant`)

- Image: `qdrant/qdrant`
- Ports: `6333` (HTTP), `6334` (gRPC)
- Dùng để lưu trữ và tìm kiếm vector embeddings

### 4. Server Backend (`server`)

- Build từ `./server/Dockerfile`
- Port: `8080` (chỉ trong Docker network)
- FastAPI application với Python 3.11
- Depends on: `postgres`, `qdrant`

### 5. Client Frontend (`client`)

- Build từ `./web/Dockerfile`
- Port: `3000` (chỉ trong Docker network)
- Next.js application với Node.js 18
- Depends on: `server`

## Commands hữu ích

### Xem logs của các services

```bash
# Xem logs của tất cả services
docker-compose logs

# Xem logs của một service cụ thể
docker-compose logs nginx
docker-compose logs server
docker-compose logs client
docker-compose logs postgres
docker-compose logs qdrant
```

### Restart services

```bash
# Restart tất cả services
docker-compose restart

# Restart một service cụ thể
docker-compose restart nginx
docker-compose restart server
```

### Stop và xóa containers

```bash
# Stop tất cả services
docker-compose down

# Stop và xóa volumes (sẽ mất dữ liệu database)
docker-compose down -v
```

### Chạy commands trong container

```bash
# Truy cập shell của server container
docker-compose exec server bash

# Chạy migration database
docker-compose exec server python -m alembic upgrade head

# Chạy tests
docker-compose exec server python -m pytest
```

## Development

### Chạy server locally (không dùng Docker)

```bash
cd server
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

### Chạy client locally (không dùng Docker)

```bash
cd web
npm install
npm run dev
```

## Environment Variables

### Server (.env trong thư mục server/)

- `SERVER_PORT`: Port cho server (mặc định: 8080)
- `DATABASE_URL`: Connection string cho PostgreSQL
- `QDRANT_URL`: URL cho Qdrant service
- `CLIENT_URLS`: Danh sách URLs được phép CORS
- Các API keys cho các dịch vụ AI (OpenAI, Cohere, etc.)

### Docker Compose (.env ở root)

- `POSTGRES_USER`: Username cho PostgreSQL
- `POSTGRES_PASSWORD`: Password cho PostgreSQL
- `POSTGRES_DB`: Tên database

## Troubleshooting

### Lỗi port đã được sử dụng

```bash
# Kiểm tra process đang sử dụng port 80
netstat -ano | findstr :80

# Kill process nếu cần (thường là IIS hoặc Apache)
Stop-Process -Id <process_id> -Force

# Hoặc stop IIS service nếu đang chạy
Stop-Service -Name W3SVC -Force
```

### Lỗi database connection

- Đảm bảo PostgreSQL container đã chạy và healthy
- Kiểm tra DATABASE_URL trong file .env của server
- Wait cho health check của postgres thành công

### Lỗi build Docker

```bash
# Clean Docker cache
docker system prune -a

# Rebuild từ đầu
docker-compose build --no-cache
```

## Monitoring và Health Checks

Tất cả các services đều có health checks được cấu hình:

- **postgres**: `pg_isready` check
- **server**: HTTP request đến `/health` endpoint
- **nginx**: HTTP request đến `/health` (được proxy đến server)
- **qdrant**: Container startup check

Sử dụng `docker-compose ps` để kiểm tra trạng thái health của các services.

## Kiến trúc Nginx Reverse Proxy

```
Internet → Nginx (Port 80) → {
    /api/* → Server (Port 8080)
    /docs  → Server (Port 8080)
    /static/* → Server (Port 8080)
    /ws → Server (Port 8080) [WebSocket]
    /* → Client (Port 3000)
}
```

### Lợi ích của việc sử dụng Nginx:

- **Single Domain**: Tất cả services đều chạy trên cùng domain (localhost)
- **CORS Management**: Nginx xử lý CORS thay vì cấu hình trong từng service
- **Rate Limiting**: Bảo vệ API khỏi spam/abuse
- **Static File Serving**: Nginx phục vụ static files hiệu quả hơn
- **Load Balancing**: Có thể scale multiple instances sau này
- **SSL Termination**: Dễ dàng thêm HTTPS
- **Security Headers**: Thêm các header bảo mật tự động

### Cấu hình Nginx tùy chỉnh:

Để thay đổi cấu hình Nginx, chỉnh sửa file `nginx/nginx.conf` và restart container:

```bash
docker-compose restart nginx
```
