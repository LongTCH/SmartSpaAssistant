# Build stage
FROM python:3.13-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /build

# Install dependencies for compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ \
    libc6-dev \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies including PyInstaller
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir pyinstaller

# Copy source code
COPY app/ app/
# Compile Python to executable using PyInstaller
RUN pyinstaller app/main.py --onefile --recursive-copy-metadata pydantic_ai_slim

# Runtime stage
FROM debian:bookworm-slim

# Install SSL certificates in runtime stage
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create directories and user
RUN addgroup --system appgroup && \
    adduser --system appuser --ingroup appgroup && \
    mkdir -p /app

COPY --from=builder /build/dist/main /app/server

# Set ownership and permissions
RUN chown -R appuser:appgroup /app && \
    chmod +x /app/server

# Set working directory
WORKDIR /app

# Switch to non-root user
USER appuser

EXPOSE 8080

# Run the compiled executable
CMD ["/app/server"]