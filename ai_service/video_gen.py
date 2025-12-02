import os
import subprocess
import uuid
import logging
import cv2
import numpy as np
import sys

sys.path.append("/app/Wav2Lip")

logger = logging.getLogger(__name__)

class VideoGenerator:
    def __init__(self):
        self.base_dir = "/app/Wav2Lip"
        self.checkpoint_path = os.path.join(self.base_dir, "checkpoints", "wav2lip_gan.pth")
        self.avatar_path = "/app/avatar.png" # Absolute path
        
    def generate_lip_sync(self, audio_path: str) -> str:
        """
        Runs Wav2Lip inference to generate a lip-synced video.
        Returns the path to the generated video.
        """
        output_filename = f"/tmp/{uuid.uuid4()}.mp4"
        
        # Construct command
        # python inference.py --checkpoint_path <ckpt> --face <image> --audio <audio> --outfile <out>
        cmd = [
            "python",
            os.path.join(self.base_dir, "inference.py"),
            "--checkpoint_path", self.checkpoint_path,
            "--face", self.avatar_path,
            "--audio", audio_path,
            "--outfile", output_filename,
            "--resize_factor", "1",    # Keep resolution
            "--nosmooth",              # Sharper results
            "--static", "true"         # Since input is an image, treat as static video
        ]
        
        try:
            logger.info(f"Starting Video Generation: {cmd}")
            # Run the process
            subprocess.run(cmd, check=True, cwd=self.base_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            if os.path.exists(output_filename):
                logger.info(f"Video generated successfully: {output_filename}")
                return output_filename
            else:
                raise Exception("Output file was not created.")
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Wav2Lip Failed: {e.stderr.decode()}")
            raise Exception(f"Video Generation Failed: {e.stderr.decode()}")
        except Exception as e:
            logger.error(f"General Error: {e}")
            raise e

video_generator = VideoGenerator()
