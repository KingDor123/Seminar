import logger from '../../utils/logger.js';
import fs from 'fs';

/**
 * Service for Speech-to-Text (STT) transcription.
 * 
 * CURRENT STATUS: Placeholder.
 * 
 * Reason: Local high-quality STT (like Whisper) requires binary dependencies (ffmpeg, python, etc.)
 * that are not present in the lightweight Node.js Alpine container used for the backend.
 * 
 * To Enable Real STT:
 * 1. Use an external API (e.g., OpenAI Whisper).
 * 2. Or, use a heavier Docker image for the backend that includes Python/FFmpeg and use 'whisper-node'.
 */
export class SttService {
    /**
     * Transcribes an audio file to text.
     * 
     * @param audioPath - Path to the audio file.
     * @returns The transcribed text.
     */
    async transcribe(audioPath: string): Promise<string> {
        // In a full Node.js refactor, local STT (Whisper) is hard to host directly.
        // Options:
        // 1. Use OpenAI API (requires key)
        // 2. Use a separate whisper-node wrapper (requires system dependencies)
        // 3. Keep the Python service (which we are deleting per request)
        
        logger.warn('STT Service: Local transcription is not fully implemented in Node.js backend yet.');
        
        // Example implementation for OpenAI API (commented out):
        /*
        const formData = new FormData();
        formData.append('file', fs.createReadStream(audioPath));
        const res = await axios.post('https://api.openai.com/v1/audio/transcriptions', formData, {
            headers: { 'Authorization': `Bearer ${process.env.OPENAI_API_KEY}` }
        });
        return res.data.text;
        */

        return "Transcription unavailable in backend-only mode";
    }
}

export const sttService = new SttService();