FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    netcat-openbsd \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY wait-for-qdrant.sh /app/wait-for-qdrant.sh
RUN chmod +x /app/wait-for-qdrant.sh

EXPOSE 3000

ENTRYPOINT ["/app/wait-for-qdrant.sh", "qdrant", "6333"]
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "3000"]
