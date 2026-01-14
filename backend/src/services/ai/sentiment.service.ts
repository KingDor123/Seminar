import { llmService } from './llm.service.js';
import logger from '../../utils/logger.js';

export interface SentimentAnalysisResult {
    label: 'positive' | 'negative' | 'neutral';
    score: number;
}

/**
 * Service for analyzing the sentiment of text using an LLM.
 * Replaces the previous BERT-based implementation for simplicity in the Node.js backend.
 */
export class SentimentService {
    /**
     * Analyzes the sentiment of the provided text.
     * 
     * @param text - The text to analyze.
     * @returns A promise that resolves to a SentimentAnalysisResult (label and score).
     */
    async analyzeSentiment(text: string): Promise<SentimentAnalysisResult> {
        if (!text.trim()) {
            return { label: 'neutral', score: 0.5 };
        }

        try {
            // Prompt the LLM to act as a sentiment classifier
            const prompt = `
            Analyze the sentiment of the following Hebrew text. 
            Return a JSON object with "label" (positive, negative, or neutral) and "score" (0.0 to 1.0, where 1.0 is very positive and 0.0 is very negative).
            
            Text: "${text}"
            
            JSON Output:
            `;

            const response = await llmService.generateResponse([
                { role: 'user', content: prompt }
            ], 'json');

            const result = JSON.parse(response);
            
            // Normalize the output to ensure it matches our expected schema
            let label = result.label?.toLowerCase() || 'neutral';
            if (!['positive', 'negative', 'neutral'].includes(label)) {
                label = 'neutral';
            }

            return {
                label: label,
                score: typeof result.score === 'number' ? result.score : 0.5
            };

        } catch (error: any) {
            logger.error(`Error during sentiment analysis: ${error.message}`);
            // Fallback to neutral on error
            return { label: 'neutral', score: 0.5 };
        }
    }
}

export const sentimentService = new SentimentService();