# Base image: Python 3.11 Slim (Debian-based)
# Chosen for its small size while maintaining compatibility with most ML libraries.
FROM python:3.11-slim

# Set working directory inside the container
WORKDIR /app

# --- Environment Variables ---
# PYTHONDONTWRITEBYTECODE: Prevents Python from writing .pyc files to disc
# PYTHONUNBUFFERED: Ensures python output is sent straight to terminal (logs)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# --- Dependencies ---
COPY requirements.txt .

# Install system dependencies:
# - ffmpeg: Required by EdgeTTS and Faster-Whisper for audio processing.
# - git: Required if pip needs to install packages directly from git repositories.
RUN apt-get update && \
    apt-get install -y ffmpeg git && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# --- Application Code ---
COPY . .

# Expose the port FastAPI will run on
EXPOSE 8000

# Add /app to PYTHONPATH so python modules can be imported from root
ENV PYTHONPATH="${PYTHONPATH}:/app"

# --- Entrypoint ---
# We use a custom entrypoint script to perform model checks before starting the server.
# chmod is run to ensure the script is executable.
RUN chmod +x entrypoint.sh
CMD ["./entrypoint.sh"]