FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends gcc g++ \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create directories and user
RUN addgroup --system appgroup && \
    adduser --system appuser --ingroup appgroup && \
    chown -R appuser:appgroup /app

USER appuser

EXPOSE 8080

CMD ["python", "-m", "app.main"]