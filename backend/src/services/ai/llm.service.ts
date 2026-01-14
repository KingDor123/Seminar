import axios from 'axios';
import logger from '../../utils/logger.js';

/**
 * Service for interacting with Large Language Models (LLMs) via Ollama.
 * Handles both single response generation and streaming responses.
 */
export class LlmService {
    private baseUrl: string;
    private model: string;

    constructor() {
        // Defaults to local Ollama instance
        this.baseUrl = process.env.OLLAMA_BASE_URL || 'http://ollama:11434';
        this.model = process.env.LLM_MODEL || 'aya:8b';
    }

    /**
     * Generates a single complete response from the LLM.
     * 
     * @param messages - Array of chat messages (role, content).
     * @param format - Output format ('text' or 'json').
     * @returns The content of the assistant's response.
     */
    async generateResponse(messages: { role: string; content: string }[], format: 'json' | 'text' = 'text'): Promise<string> {
        try {
            logger.info(`Generating response with model ${this.model}`);
            const response = await axios.post(`${this.baseUrl}/api/chat`, {
                model: this.model,
                messages: messages,
                stream: false,
                format: format === 'json' ? 'json' : undefined
            });

            return response.data.message.content;
        } catch (error: any) {
            logger.error(`Error generating response from LLM: ${error.message}`);
            throw error;
        }
    }

    /**
     * Streams the response from the LLM token by token.
     * Useful for real-time chat interfaces.
     * 
     * @param messages - Array of chat messages.
     * @yields Strings representing chunks of the response content.
     */
    async *streamResponse(messages: { role: string; content: string }[]): AsyncGenerator<string, void, unknown> {
        try {
            logger.info(`Streaming response with model ${this.model}`);
            const response = await axios.post(`${this.baseUrl}/api/chat`, {
                model: this.model,
                messages: messages,
                stream: true
            }, {
                responseType: 'stream'
            });

            // Process the stream
            for await (const chunk of response.data) {
                const lines = chunk.toString().split('\n').filter((line: string) => line.trim() !== '');
                for (const line of lines) {
                    try {
                        const json = JSON.parse(line);
                        if (json.message && json.message.content) {
                            yield json.message.content;
                        }
                        if (json.done) {
                            return;
                        }
                    } catch (e) {
                        // Ignore parse errors for partial chunks
                    }
                }
            }
        } catch (error: any) {
            logger.error(`Error streaming response from LLM: ${error.message}`);
            throw error;
        }
    }
}

export const llmService = new LlmService();