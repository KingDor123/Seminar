
import { ChatRepo } from '../../repositories/chat.repo';
import { fetchScenarioById } from '../scenario.service';

// Mock the ChatRepo class
jest.mock('../../repositories/chat.repo', () => {
    return {
        ChatRepo: jest.fn().mockImplementation(() => ({
            createSession: jest.fn(),
            addMessage: jest.fn(),
            addMessageWithAnalysis: jest.fn(),
            updateLatestUserSentiment: jest.fn(),
            getSessionsByUserId: jest.fn(),
            getMessagesBySessionId: jest.fn(),
            getMessagesBySessionIdWithAnalysis: jest.fn(),
        }))
    };
});

// Mock the database config to avoid connection attempts
jest.mock('../../config/databaseConfig', () => ({
    db: {}
}));

jest.mock('../scenario.service', () => ({
    fetchScenarioById: jest.fn(),
}));

describe('Chat Service', () => {
    let chatService: any;
    let mockChatRepo: any;

    beforeAll(async () => {
        // Dynamically import the service to ensure mocks are applied and we can capture the instance
        chatService = await import('../chat.service');
        // Capture the instance created by the service via the return value
        // @ts-ignore
        mockChatRepo = (ChatRepo as jest.Mock).mock.results[0].value;
    });

    beforeEach(() => {
        jest.clearAllMocks();
    });

    describe('startSession', () => {
        it('should create a session when valid data is provided', async () => {
            const userId = 1;
            const scenarioId = 'interview';
            const mockSession = { id: 100, user_id: userId, scenario_id: scenarioId };

            (fetchScenarioById as jest.Mock).mockReturnValue({ scenario_id: scenarioId });
            
            mockChatRepo.createSession.mockResolvedValue(mockSession);

            const result = await chatService.startSession(userId, scenarioId);

            expect(mockChatRepo.createSession).toHaveBeenCalledWith(userId, scenarioId);
            expect(result).toEqual(mockSession);
        });

        it('should throw error if userId is missing', async () => {
            await expect(chatService.startSession(0, 'scenario')).rejects.toThrow('User ID is required');
        });

        it('should throw error if scenarioId is missing', async () => {
            await expect(chatService.startSession(1, '')).rejects.toThrow('Valid Scenario ID is required');
        });

        it('should throw error if scenarioId is invalid', async () => {
            (fetchScenarioById as jest.Mock).mockReturnValue(null);
            await expect(chatService.startSession(1, 'unknown')).rejects.toThrow('Scenario not found');
        });
    });

    describe('saveMessage', () => {
        it('should save a message when valid data is provided', async () => {
            const sessionId = 100;
            const role = 'user';
            const content = 'Hello';
            const mockMessage = { id: 1, session_id: sessionId, role, content };

            mockChatRepo.addMessage.mockResolvedValue(mockMessage);

            const result = await chatService.saveMessage(sessionId, role, content);

            expect(mockChatRepo.addMessage).toHaveBeenCalledWith(sessionId, role, content, undefined);
            expect(result).toEqual(mockMessage);
        });

        it('should throw error if role is invalid', async () => {
            await expect(chatService.saveMessage(100, 'admin', 'content')).rejects.toThrow('Valid role (user/ai) is required');
        });

        it('should throw error if content is empty', async () => {
            await expect(chatService.saveMessage(100, 'user', '   ')).rejects.toThrow('Message content cannot be empty');
        });
    });
});
