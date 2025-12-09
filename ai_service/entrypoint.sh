#!/bin/bash
set -e

# ==============================================================================
# AI Service Entrypoint
# Checks for required model files and starts the application.
# ==============================================================================

# Directories for Wav2Lip models (if used)
WEIGHTS_DIR="/app/Wav2Lip/checkpoints"
S3FD_DIR="/app/Wav2Lip/face_detection/detection/sfd"

echo "🚀 Starting SoftSkill AI Service..."
echo "🔍 Checking for AI Model dependencies..."

# --- Wav2Lip Model Checks ---
# These checks ensure that the visual dubbing models are present.
if [ ! -f "$WEIGHTS_DIR/wav2lip_gan.pth" ]; then
    echo "⚠️  Warning: Wav2Lip GAN Model not found in $WEIGHTS_DIR."
    echo "    Visual dubbing features may fail."
else
    echo "✅ Wav2Lip GAN Model found."
fi

if [ ! -f "$S3FD_DIR/s3fd.pth" ]; then
     echo "⚠️  Warning: S3FD (Face Detection) Model not found in $S3FD_DIR."
else
    echo "✅ S3FD Model found."
fi

# --- Patching ---
# Run the audio patch script to fix version incompatibility in librosa/Wav2Lip
if [ -f "patch_audio.py" ]; then
    echo "🔧 Applying audio library patches..."
    python patch_audio.py
fi

# --- Start Server ---
echo "🔥 Launching Uvicorn..."
exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload