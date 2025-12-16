class PCMProcessor extends AudioWorkletProcessor {
  process(inputs) {
    // inputs[0] is the input channel (microphone)
    const input = inputs[0];
    if (input && input.length > 0) {
      // input[0] is the Float32Array of audio data (Mono)
      const float32Data = input[0];
      
      // Send the data back to the main thread (React)
      // We slice it to create a copy, ensuring thread safety
      if (float32Data.length > 0) {
          this.port.postMessage(float32Data);
      }
    }
    return true; // Keep processor alive
  }
}

registerProcessor('pcm-processor', PCMProcessor);