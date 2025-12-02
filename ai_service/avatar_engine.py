import cv2
import numpy as np
import base64
import io
import logging
import os
import sys

# Add LivePortrait to path
sys.path.append("/app/LivePortrait")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AvatarEngine:
    def __init__(self):
        self.avatar_image = None
        # Create a default placeholder
        self.avatar_image = np.full((512, 512, 3), 100, dtype=np.uint8)
        
        self.base_height, self.base_width = self.avatar_image.shape[:2]
        self.use_live_portrait = False
        
        # Maps for remapping
        self.map_x = None
        self.map_y = None

        logger.info("Avatar Engine Initialized (Wav2Lip Mode).")

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

    def process_audio_frame(self, audio_amplitude: float) -> str:
        """
        Generates a frame using Grid Distortion to mimic mouth opening.
        """
        if self.avatar_image is None:
            return ""

        if self.use_live_portrait:
            pass

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
        strength = audio_amplitude * 20.0 
        
        if strength < 1.0:
            # Optimization: If silent, return original
             return self.encode_frame(self.avatar_image)

        # Create a copy of the base map to distort
        map_y_distorted = self.map_y.copy()
        
        # Calculate distance from mouth center
        # We use a simple mask to speed up numpy
        y_indices, x_indices = np.indices((h, w))
        
        # Vectorized Gaussian-like drop
        # dy = strength * exp(-distance^2 / radius^2)
        # We only care about the region around the mouth
        
        y_min = max(0, center_y - radius * 2)
        y_max = min(h, center_y + radius * 2)
        x_min = max(0, center_x - radius * 2)
        x_max = min(w, center_x + radius * 2)
        
        # Slice for speed
        slice_y = y_indices[y_min:y_max, x_min:x_max]
        slice_x = x_indices[y_min:y_max, x_min:x_max]
        
        dist_sq = (slice_x - center_x)**2 + (slice_y - center_y)**2
        
        # Gaussian falloff
        delta = strength * np.exp(-dist_sq / (radius**2))
        
        # Apply distortion: The pixels we want at (x, y) should come from (x, y - delta)
        # Wait, to move pixels DOWN, we need to pull from UP.
        # So map_y should be y - delta.
        
        map_y_distorted[y_min:y_max, x_min:x_max] -= delta

        # Remap
        frame = cv2.remap(self.avatar_image, self.map_x, map_y_distorted, cv2.INTER_LINEAR)

        return self.encode_frame(frame)

    def encode_frame(self, frame):
        _, buffer = cv2.imencode('.jpg', frame)
        return base64.b64encode(buffer).decode('utf-8')
