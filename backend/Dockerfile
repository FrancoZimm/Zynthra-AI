FROM python:3.11-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create runtime directories
RUN mkdir -p /app/documents /app/index /app/chat_logs

# Expose port
EXPOSE 8001

# Run
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001"]
