#!/bin/bash
set -e

# Wav2Lip Weights
WEIGHTS_DIR="/app/Wav2Lip/checkpoints"
MODEL_URL="https://huggingface.co/camenduru/Wav2Lip/resolve/main/wav2lip_gan.pth"
FACE_DETECTION_URL="https://www.adrianbulat.com/downloads/python-fan/s3fd-619a316812.pth"

mkdir -p "$WEIGHTS_DIR"
mkdir -p "/app/Wav2Lip/face_detection/detection/sfd/s3fd.pth" # Put face detection model here? No, usually in ~/.cache or specific dir

if [ ! -f "$WEIGHTS_DIR/wav2lip_gan.pth" ]; then
    echo "🚀 Downloading Wav2Lip GAN Model..."
    wget -O "$WEIGHTS_DIR/wav2lip_gan.pth" "$MODEL_URL"
fi

# Face Detection Model (S3FD)
# Usually Wav2Lip looks for it in face_detection/detection/sfd/s3fd.pth
S3FD_DIR="/app/Wav2Lip/face_detection/detection/sfd"
if [ ! -f "$S3FD_DIR/s3fd.pth" ]; then
    echo "🚀 Downloading Face Detection Model..."
    mkdir -p "$S3FD_DIR"
    wget -O "$S3FD_DIR/s3fd.pth" "$FACE_DETECTION_URL"
fi

echo "✅ AI Models Ready."

# PATCH: Fix Librosa > 0.10 breaking change in Wav2Lip/audio.py
echo "🔧 Patching Wav2Lip audio.py..."
python patch_audio.py

# Start the application
exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload