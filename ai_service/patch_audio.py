import sys
import re
import os

"""
Patch Audio Script
------------------
This script is a workaround for a compatibility issue between `librosa` and 
the `Wav2Lip` legacy code.

Problem: Wav2Lip calls `librosa.filters.mel` with positional arguments, 
but newer versions of librosa require keyword arguments.

Solution: This script uses regex to find the specific function call in 
`/app/Wav2Lip/audio.py` and injects the necessary keyword argument names.
"""

FILE_PATH = '/app/Wav2Lip/audio.py'

def patch_file():
    if not os.path.exists(FILE_PATH):
        print(f"⚠️  File not found: {FILE_PATH}. Skipping patch.")
        return

    try:
        with open(FILE_PATH, 'r') as f:
            content = f.read()
        
        # Pattern to match the specific problematic function call:
        # return librosa.filters.mel(hp.sample_rate, hp.n_fft, n_mels=hp.num_mels,
        pattern = r"(return\s+librosa\.filters\.mel\(\s*)hp\.sample_rate\s*,\s*hp\.n_fft\s*,\s*n_mels=hp\.num_mels\s*,"
        
        # Replacement string:
        # return librosa.filters.mel(sr=hp.sample_rate, n_fft=hp.n_fft, n_mels=hp.num_mels,
        replacement = r"\1sr=hp.sample_rate, n_fft=hp.n_fft, n_mels=hp.num_mels,"
        
        if re.search(pattern, content):
            new_content = re.sub(pattern, replacement, content)
            with open(FILE_PATH, 'w') as f:
                f.write(new_content)
            print(f"✅ Successfully patched {FILE_PATH} for librosa compatibility.")
        else:
            # Check if it was already patched
            if "sr=hp.sample_rate" in content:
                 print(f"ℹ️  {FILE_PATH} is already patched.")
            else:
                print(f"❌ Warning: Could not find exact text to patch in {FILE_PATH}. Code structure may have changed.")

    except Exception as e:
        print(f"❌ Error patching file: {e}")

if __name__ == "__main__":
    patch_file()