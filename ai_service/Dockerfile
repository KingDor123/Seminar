# Base image: Python 3.11 Slim (Debian-based)
FROM python:3.11-slim

# Set working directory inside the container
WORKDIR /app

# --- Environment Variables ---
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# --- Dependencies ---
COPY requirements.txt .

# Install system dependencies (ffmpeg is still useful for audio format conversion safety)
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# --- Application Code ---
COPY . .

# Expose the port FastAPI will run on
EXPOSE 8000

# Add /app to PYTHONPATH
ENV PYTHONPATH="${PYTHONPATH}:/app"

# --- Entrypoint ---
# Direct start with Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]