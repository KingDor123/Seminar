FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN apt-get update && apt-get install -y libgl1 libglib2.0-0 git git-lfs ffmpeg wget ca-certificates && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir -r requirements.txt

# Clone LivePortrait (Pinned commit for stability if needed, but using main for now)
RUN git clone https://github.com/KwaiVGI/LivePortrait.git /app/LivePortrait

# Pre-download weights (This is a placeholder - in production you'd use a script)
# For this demo, we will let the python script download them or expect them mounted.

COPY avatar.png .
COPY entrypoint.sh .
COPY patch_audio.py .
RUN chmod +x entrypoint.sh

# Wav2Lip is now included in the context, so we don't need to clone or download it here.
# Dependencies are handled by requirements.txt

COPY . .
ENV PYTHONPATH="${PYTHONPATH}:/app/Wav2Lip"

CMD ["./entrypoint.sh"]

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
