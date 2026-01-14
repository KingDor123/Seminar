import { PromptService } from '../prompt.service.js';
import * as scenariosModule from '../../../data/scenarios.js';
import { llmService } from '../llm.service.js';

// Mock dependencies
jest.mock('../../../data/scenarios.js');
jest.mock('../llm.service.js');
jest.mock('../../../repositories/prompt.repo.js', () => {
    return {
        PromptRepo: jest.fn().mockImplementation(() => {
            return {
                getSystemPromptByScenarioId: jest.fn()
            };
        })
    };
});
jest.mock('../../../config/databaseConfig.js', () => ({
    db: {}
}));

import { PromptRepo } from '../../../repositories/prompt.repo.js';

describe('PromptService', () => {
    let promptService: PromptService;
    let mockPromptRepo: any;

    beforeEach(() => {
        jest.clearAllMocks();
        promptService = new PromptService();
        // @ts-ignore
        mockPromptRepo = promptService['promptRepo']; 
        console.log('Mock Prompt Repo from service:', mockPromptRepo);
    });

    describe('buildChatMessages', () => {
        it('should use DB prompt when available', async () => {
            const mockDbPrompt = {
                content: 'DB Persona Prompt'
            };
            mockPromptRepo.getSystemPromptByScenarioId.mockResolvedValue(mockDbPrompt);

            const messages = await promptService.buildChatMessages(
                'bank',
                'neutral',
                [],
                'Hello'
            );

            expect(mockPromptRepo.getSystemPromptByScenarioId).toHaveBeenCalledWith('bank');
            expect(messages[0]).toEqual({ role: 'system', content: 'DB Persona Prompt' });
        });

        it('should fallback to static scenario file when DB prompt is missing', async () => {
            // DB returns null
            mockPromptRepo.getSystemPromptByScenarioId.mockResolvedValue(null);

            // Static file exists
            const mockScenario = {
                scenario_id: 'bank',
                persona_prompt: 'Static Persona Prompt',
                scenario_goal: 'Test Goal',
                difficulty: 1,
                evaluation_rubric: 'Test Rubric'
            };
            (scenariosModule.getScenarioById as jest.Mock).mockReturnValue(mockScenario);

            const messages = await promptService.buildChatMessages(
                'bank',
                'neutral',
                [],
                'Hello'
            );

            expect(messages[0]).toEqual({ role: 'system', content: 'Static Persona Prompt' });
        });

        it('should fallback to generic prompt when DB and static file are missing', async () => {
            mockPromptRepo.getSystemPromptByScenarioId.mockResolvedValue(null);
            (scenariosModule.getScenarioById as jest.Mock).mockReturnValue(null);

            const messages = await promptService.buildChatMessages(
                'invalid_id',
                'neutral',
                [],
                'Hello'
            );

            expect(messages[0].role).toBe('system');
            expect(messages[0].content).toContain('helpful and professional AI social skills trainer');
        });
    });

    describe('analyzeTurn', () => {
        it('should return parsed analysis when LLM returns valid JSON', async () => {
            const mockResponse = JSON.stringify({
                detected_intent: 'Greeting',
                social_impact: 'Positive',
                reasoning: 'User was polite',
                confidence: 0.9
            });

            (llmService.generateResponse as jest.Mock).mockResolvedValue(mockResponse);

            const result = await promptService.analyzeTurn('Hello', 'positive');

            expect(result).toEqual({
                sentiment: 'positive',
                confidence: 0.9,
                detected_intent: 'Greeting',
                social_impact: 'Positive',
                reasoning: 'User was polite'
            });
        });

        it('should return fallback values when LLM fails', async () => {
            (llmService.generateResponse as jest.Mock).mockRejectedValue(new Error('LLM Error'));

            const result = await promptService.analyzeTurn('Hello', 'positive');

            expect(result.detected_intent).toBe('Analysis failed');
        });
    });
});
