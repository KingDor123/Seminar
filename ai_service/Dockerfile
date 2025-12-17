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

# Set LD_LIBRARY_PATH for CTranslate2 to find cuDNN/cuBLAS
ENV LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib/python3.11/site-packages/nvidia/cudnn/lib:/usr/local/lib/python3.11/site-packages/nvidia/cublas/lib

# --- Application Code ---
COPY . .

# Expose the port FastAPI will run on
EXPOSE 8000

# Add /app to PYTHONPATH
ENV PYTHONPATH="${PYTHONPATH}:/app"

# --- Entrypoint ---
# Direct start with Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]