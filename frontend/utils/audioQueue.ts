export class AudioQueue {
    private audioContext: AudioContext;
    private queue: AudioBuffer[] = [];
    private isPlaying: boolean = false;
    private startTime: number = 0;

    constructor() {
        // Initialize AudioContext lazily or immediately
        this.audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
    }

    public async addChunk(base64Data: string) {
        try {
            const binaryString = window.atob(base64Data);
            const len = binaryString.length;
            const bytes = new Uint8Array(len);
            for (let i = 0; i < len; i++) {
                bytes[i] = binaryString.charCodeAt(i);
            }
            
            // Decode audio data
            const audioBuffer = await this.audioContext.decodeAudioData(bytes.buffer);
            this.queue.push(audioBuffer);
            
            if (!this.isPlaying) {
                this.playNext();
            }
        } catch (e) {
            console.error("Error decoding audio chunk:", e);
        }
    }

    private playNext() {
        if (this.queue.length === 0) {
            this.isPlaying = false;
            return;
        }

        this.isPlaying = true;
        const buffer = this.queue.shift();
        if (!buffer) return;

        const source = this.audioContext.createBufferSource();
        source.buffer = buffer;
        source.connect(this.audioContext.destination);

        source.onended = () => {
            this.playNext();
        };

        source.start(0);
    }
    
    public resume() {
        if (this.audioContext.state === 'suspended') {
            this.audioContext.resume();
        }
    }
}
