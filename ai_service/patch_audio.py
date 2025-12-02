import sys
import re

file_path = '/app/Wav2Lip/audio.py'

try:
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Pattern to match the specific problematic function call, including the trailing comma
    pattern = r"(return\s+librosa\.filters\.mel\(\s*)hp\.sample_rate\s*,\s*hp\.n_fft\s*,\s*n_mels=hp\.num_mels\s*,"
    
    # Replacement string, preserving the 'return ' part and adding keyword arguments
    replacement = r"\1sr=hp.sample_rate, n_fft=hp.n_fft, n_mels=hp.num_mels,"
    
    if re.search(pattern, content):
        new_content = re.sub(pattern, replacement, content)
        with open(file_path, 'w') as f:
            f.write(new_content)
        print(f"✅ Successfully patched {file_path} using Regex")
    else:
        print(f"❌ Warning: Could not find exact text to patch in {file_path}. The pattern may have changed.")
        # Print a snippet to help debug
        idx = content.find("librosa.filters.mel")
        if idx != -1:
            print(f"Found similar line (first 100 chars): {content[idx:idx+100]}")
        else:
            print("Could not find 'librosa.filters.mel' in the file.")

except Exception as e:
    print(f"❌ Error patching file: {e}")
