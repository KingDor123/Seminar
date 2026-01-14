import { getScenarioById } from '../../data/scenarios.js';
import { llmService } from './llm.service.js';
import logger from '../../utils/logger.js';
import { TurnAnalysisInput } from '../../repositories/chat.repo.js';
import { PromptRepo } from '../../repositories/prompt.repo.js';
import { db } from '../../config/databaseConfig.js';

export class PromptService {
    private promptRepo: PromptRepo;

    constructor() {
        this.promptRepo = new PromptRepo(db);
    }
    
    /**
     * Builds the chat message array for the LLM, including:
     * - System prompt (scenario persona + instructions)
     * - Conversation history
     * - Current user message
     */
    async buildChatMessages(
        scenarioId: string, 
        sentiment: string, 
        history: { role: string; content: string }[], 
        userText: string
    ): Promise<{ role: string; content: string }[]> {
        
        let systemContent = "You are a helpful and professional AI social skills trainer.";
        
        try {
            // 1. Try fetching from DB
            const dbPrompt = await this.promptRepo.getSystemPromptByScenarioId(scenarioId);
            if (dbPrompt) {
                systemContent = dbPrompt.content;
            } else {
                // 2. Fallback to static file
                const scenario = getScenarioById(scenarioId);
                if (scenario) {
                    systemContent = scenario.persona_prompt;
                } else {
                    logger.warn(`Scenario ID "${scenarioId}" not found in DB or static files. Using generic prompt.`);
                }
            }
        } catch (error) {
            logger.error(`Error fetching prompt for scenario ${scenarioId}:`, error);
            // Fallback to static if DB fails
            const scenario = getScenarioById(scenarioId);
            if (scenario) {
                systemContent = scenario.persona_prompt;
            }
        }

        const systemMessages = [
            { role: "system", content: systemContent },
            { role: "system", content: `Current user sentiment: ${sentiment}.` }
        ];

        // Ensure roles are mapped correctly for Ollama/OpenAI format
        const formattedHistory = history.map(msg => ({
            role: msg.role === 'ai' ? 'assistant' : msg.role,
            content: msg.content
        }));

        return [
            ...systemMessages,
            ...formattedHistory,
            { role: "user", content: userText }
        ];
    }

    /**
     * Analyzes a single turn of conversation to extract structured data.
     * Designed to run in parallel with the main response generation.
     */
    async analyzeTurn(
        userText: string,
        sentiment: string,
        context: string = ""
    ): Promise<TurnAnalysisInput> {
        if (!userText.trim()) {
            throw new Error("User text is empty");
        }

        const prompt = `
        Analyze the following user message in a social skills training context.
        
        User Message: "${userText}"
        Sentiment: ${sentiment}
        Context: ${context}

        Provide a JSON response with the following fields:
        1. detected_intent: What is the user trying to achieve? (String)
        2. social_impact: How does this message likely land with the listener? (String)
        3. reasoning: Brief explanation of the analysis. (String)
        4. confidence: A score from 0.0 to 1.0 indicating confidence in this analysis. (Number)
        
        Return strictly valid JSON.
        `;

        try {
            const rawResponse = await llmService.generateResponse([{ role: 'user', content: prompt }], 'json');
            const json = JSON.parse(rawResponse);

            // Validate and fallback if fields are missing
            return {
                sentiment: (['positive', 'negative', 'neutral'].includes(sentiment) ? sentiment : 'neutral') as 'positive' | 'negative' | 'neutral',
                confidence: typeof json.confidence === 'number' ? json.confidence : 0.5,
                detected_intent: json.detected_intent || "Unknown intent",
                social_impact: json.social_impact || "Neutral impact",
                reasoning: json.reasoning || "No reasoning provided"
            };
        } catch (error: any) {
            logger.error(`Turn Analysis Failed: ${error.message}`);
            // Return safe fallback
            return {
                sentiment: 'neutral',
                confidence: 0,
                detected_intent: "Analysis failed",
                social_impact: "Unknown",
                reasoning: "Error during processing"
            };
        }
    }
}

export const promptService = new PromptService();
