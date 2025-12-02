#!/bin/bash
set -e

# Wav2Lip Weights
WEIGHTS_DIR="/app/Wav2Lip/checkpoints"
S3FD_DIR="/app/Wav2Lip/face_detection/detection/sfd"

echo "🚀 Checking AI Models..."

if [ ! -f "$WEIGHTS_DIR/wav2lip_gan.pth" ]; then
    echo "⚠️ Wav2Lip GAN Model not found in $WEIGHTS_DIR. Please ensure it is included in the image or mounted."
    # Optional: Fallback download (commented out to rely on local build)
    # wget -O "$WEIGHTS_DIR/wav2lip_gan.pth" "https://huggingface.co/Nekochu/Wav2Lip/resolve/main/wav2lip_gan.pth"
else
    echo "✅ Wav2Lip GAN Model found."
fi

if [ ! -f "$S3FD_DIR/s3fd.pth" ]; then
     echo "⚠️ S3FD Model not found in $S3FD_DIR. Please ensure it is included in the image or mounted."
     # Optional: Fallback download
     # mkdir -p "$S3FD_DIR"
     # wget -O "$S3FD_DIR/s3fd.pth" "https://www.adrianbulat.com/downloads/python-fan/s3fd-619a316812.pth"
else
    echo "✅ S3FD Model found."
fi

# Start the application
exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload
