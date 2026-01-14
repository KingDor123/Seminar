import * as googleTTS from 'google-tts-api';
import logger from '../../utils/logger.js';

/**
 * Service for Text-to-Speech (TTS) generation.
 * Uses the 'google-tts-api' library to generate audio from text.
 */
export class TtsService {
    /**
     * Generates a base64 encoded audio string for the given text.
     * 
     * @param text - The text to convert to speech.
     * @param lang - The language code (default: 'he').
     * @returns A Promise resolving to the base64 string of the audio.
     */
    async generateAudioBase64(text: string, lang: string = 'he'): Promise<string> {
        if (!text.trim()) {
            throw new Error('Text is empty');
        }

        try {
            logger.info(`Generating TTS for: ${text.substring(0, 20)}...`);
            // getAudioBase64 returns the base64 string of the audio
            // Note: This library hits Google Translate's TTS API.
            // For production with high volume, consider a paid provider like Google Cloud TTS or AWS.
            const base64 = await googleTTS.getAudioBase64(text, {
                lang: lang,
                slow: false,
                host: 'https://translate.google.com',
                timeout: 10000,
            });
            
            return base64;
        } catch (error: any) {
            logger.error(`TTS Generation failed: ${error.message}`);
            throw error;
        }
    }
}

export const ttsService = new TtsService();