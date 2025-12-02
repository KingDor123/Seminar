import cv2
import numpy as np
import base64
import io
import logging
import os
import sys
import soundfile as sf
import librosa # Import librosa for audio feature extraction

# Add LivePortrait to path
sys.path.append("/app/LivePortrait")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SAMPLE_RATE = 16000 # Standard sample rate for speech

class AvatarEngine:
    def __init__(self):
        self.avatar_image = None
        # Create a default placeholder
        self.avatar_image = np.full((512, 512, 3), 100, dtype=np.uint8)
        
        self.base_height, self.base_width = self.avatar_image.shape[:2]
        self.use_live_portrait = False
        self.sample_rate = SAMPLE_RATE # Store sample rate

        # Maps for remapping
        self.map_x = None
        self.map_y = None

        logger.info("Avatar Engine Initialized.")

    def _init_maps(self):
        """Initialize the grid for distortion."""
        h, w = self.base_height, self.base_width
        # Create a grid of coordinates
        self.map_x, self.map_y = np.meshgrid(np.arange(w), np.arange(h))
        self.map_x = self.map_x.astype(np.float32)
        self.map_y = self.map_y.astype(np.float32)

    def load_avatar(self, image_path: str):
        """Loads a real avatar image from disk."""
        try:
            img = cv2.imread(image_path)
            if img is not None:
                self.avatar_image = img
                self.base_height, self.base_width = self.avatar_image.shape[:2]
                self._init_maps()
                logger.info(f"Loaded avatar from {image_path}")
            else:
                logger.error(f"Failed to load avatar from {image_path}")
        except Exception as e:
            logger.error(f"Error loading avatar: {e}")

    def _generate_frame_with_grid_distortion(self, amplitude: float) -> str:
        """
        Generates a frame using Grid Distortion to mimic mouth opening based on amplitude.
        """
        if self.avatar_image is None:
            return ""

        if self.use_live_portrait:
            pass # LivePortrait logic would go here

        # --- GRID DISTORTION SIMULATION ---
        # This mimics a jaw drop by stretching pixels in the mouth region downwards.
        
        if self.map_x is None:
            self._init_maps()

        h, w = self.base_height, self.base_width
        
        # Mouth Center (Approximate for a portrait)
        # Usually centered horizontally, and at ~70% height
        center_x = w // 2
        center_y = int(h * 0.65)
        
        # Radius of the mouth influence
        radius = int(min(h, w) * 0.15)
        
        # Strength of opening (0 to 15 pixels down)
        # Introduce a piecewise function for strength based on amplitude for more nuanced control
        if amplitude < 0.1:  # Neutral/closed mouth
            strength = 0.0
        elif amplitude < 0.3: # Slightly open
            strength = amplitude * 5.0  # Scale up slightly
        elif amplitude < 0.6: # Moderately open
            strength = 1.5 + (amplitude - 0.3) * 10.0 # Start from a base and scale more aggressively
        else: # Widely open
            strength = 4.5 + (amplitude - 0.6) * 15.0 # Even wider, capping at a reasonable max
        
        # Cap strength to prevent extreme distortion
        strength = min(strength, 15.0) # Maximum jaw drop of 15 pixels

        # Create a copy of the base map to distort
        map_y_distorted = self.map_y.copy()
        
        # Calculate distance from mouth center
        y_indices, x_indices = np.indices((h, w))
        
        y_min = max(0, center_y - radius * 2)
        y_max = min(h, center_y + radius * 2)
        x_min = max(0, center_x - radius * 2)
        x_max = min(w, center_x + radius * 2)
        
        slice_y = y_indices[y_min:y_max, x_min:x_max]
        slice_x = x_indices[y_min:y_max, x_min:x_max]
        
        dist_sq = (slice_x - center_x)**2 + (slice_y - center_y)**2
        
        # Gaussian falloff
        delta = strength * np.exp(-dist_sq / (radius**2))
        
        map_y_distorted[y_min:y_max, x_min:x_max] -= delta

        # Remap
        frame = cv2.remap(self.avatar_image, self.map_x, map_y_distorted, cv2.INTER_LINEAR)

        return self.encode_frame(frame)

    def process_audio_chunk_for_lip_sync(self, audio_chunk: bytes) -> str:
        """
        Processes an audio chunk to extract features and generate a lip-synced avatar frame.
        """
        if not audio_chunk:
            return self.encode_frame(self.avatar_image) # Return static image if no audio

        try:
            # Convert bytes to a file-like object
            audio_buffer = io.BytesIO(audio_chunk)
            
            # Read audio data using soundfile
            # sf.read returns (data, samplerate)
            audio_data, _ = sf.read(audio_buffer, dtype='float32') # Use float32 for librosa compatibility

            if audio_data.size == 0:
                return self.encode_frame(self.avatar_image)

            # Ensure audio data is mono for librosa
            if audio_data.ndim > 1:
                audio_data = librosa.to_mono(audio_data)

            # Calculate RMS as a simple amplitude measure
            # librosa.feature.rms returns a 2D array, take the mean
            rms = librosa.feature.rms(y=audio_data, frame_length=len(audio_data), hop_length=len(audio_data) + 1).mean()
            amplitude = float(np.clip(rms * 10, 0, 1)) # Scale RMS to get a 0-1 amplitude for distortion

            logger.debug(f"Processed audio chunk, amplitude: {amplitude:.2f}")

            # Use the existing grid distortion for now
            return self._generate_frame_with_grid_distortion(amplitude)

        except Exception as e:
            logger.error(f"Error processing audio chunk: {e}", exc_info=True)
            return self.encode_frame(self.avatar_image) # Return static image on error

    def encode_frame(self, frame):
        _, buffer = cv2.imencode('.jpg', frame)
        return base64.b64encode(buffer).decode('utf-8')

