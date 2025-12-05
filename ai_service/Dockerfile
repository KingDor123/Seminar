FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
# Install system dependencies
# ffmpeg is required for audio processing (EdgeTTS, Faster-Whisper)
# git might be needed if we install from git
RUN apt-get update && apt-get install -y ffmpeg git && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# We use the new directory structure, so PYTHONPATH needs to include /app
ENV PYTHONPATH="${PYTHONPATH}:/app"

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
