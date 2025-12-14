import { renderHook, act, waitFor } from '@testing-library/react';
import { useChatSession } from '../useChatSession';
import api from '../../lib/api';

// Mock the AuthContext
jest.mock('../../context/AuthContext', () => ({
  useAuth: () => ({
    user: { id: 123, name: 'Test User' },
  }),
}));

// Mock the API library
jest.mock('../../lib/api', () => ({
  post: jest.fn(),
  get: jest.fn(),
}));

describe('useChatSession Hook', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should start a session successfully', async () => {
    // Setup API mock response
    (api.post as jest.Mock).mockResolvedValueOnce({ data: { id: 999 } });

    const { result } = renderHook(() => useChatSession());

    let sessionId;
    await act(async () => {
      sessionId = await result.current.startSession('interview');
    });

    // Assertions
    expect(api.post).toHaveBeenCalledWith('/chat/sessions', {
      userId: 123,
      scenarioId: 'interview',
    });
    expect(sessionId).toBe(999);
    expect(result.current.sessionId).toBe(999);
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('should handle start session failure', async () => {
    // Setup API mock failure
    const errorMessage = 'Network Error';
    (api.post as jest.Mock).mockRejectedValueOnce({
       message: errorMessage,
       response: { data: { message: errorMessage } }
    });

    const { result } = renderHook(() => useChatSession());

    let sessionId;
    await act(async () => {
      sessionId = await result.current.startSession('interview');
    });

    expect(sessionId).toBeNull();
    expect(result.current.sessionId).toBeNull();
    expect(result.current.error).toBe(errorMessage);
    expect(result.current.loading).toBe(false);
  });

  it('should save a message', async () => {
    (api.post as jest.Mock).mockResolvedValueOnce({});

    const { result } = renderHook(() => useChatSession());

    await act(async () => {
      await result.current.saveMessage(999, 'user', 'Hello AI');
    });

    expect(api.post).toHaveBeenCalledWith('/chat/sessions/999/messages', {
      role: 'user',
      content: 'Hello AI',
    });
  });
});
