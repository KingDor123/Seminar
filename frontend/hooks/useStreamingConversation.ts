import { useState, useRef, useCallback } from 'react';
import { fetchEventSource } from '@microsoft/fetch-event-source';
import { SCENARIOS } from '../constants/appConstants';
import { useApi } from './useApi';

interface ChatMessage {
    role: "user" | "ai";
    content: string;
}

interface UseStreamingConversationProps {
    sessionId: number | null;
    selectedScenario: string;
    onNewMessage: (message: ChatMessage) => void;
    onThinkingStateChange: (isThinking: boolean) => void;
    onAudioData: (base64Audio: string) => void;
    onError: (error: string) => void;
}

export const useStreamingConversation = ({
    sessionId,
    selectedScenario,
    onNewMessage,
    onThinkingStateChange,
    onAudioData,
    onError,
}: UseStreamingConversationProps) => {
    const { getApiUrl } = useApi();
    const abortControllerRef = useRef<AbortController | null>(null);
    const [isProcessing, setIsProcessing] = useState(false);

    const sendMessage = useCallback(async (text: string | null, audioBlob: Blob | null) => {
        if (!sessionId) {
            onError("No active session.");
            return;
        }

        if (abortControllerRef.current) {
            abortControllerRef.current.abort();
        }
        abortControllerRef.current = new AbortController();

        setIsProcessing(true);
        onThinkingStateChange(true);

        const formData = new FormData();
        formData.append("session_id", sessionId.toString());
        
        if (text) formData.append("text", text);
        if (audioBlob) formData.append("audio", audioBlob, "input.wav");

        const scenario = SCENARIOS.find(s => s.id === selectedScenario);
        const systemPrompt = scenario?.prompt || "You are a helpful assistant.";
        formData.append("system_prompt", systemPrompt);

        // Determine API URL (Proxy to AI Service via Backend or Direct?)
        // Assuming we have a direct route or a proxy setup. 
        // For now, let's assume we hit the AI service directly or via a specific backend proxy.
        // Given the context, let's try to hit the backend proxy we're about to set up or 
        // the AI service if exposed. 
        // BUT, the plan mentioned "/api/interact". 
        // If we are on the client, we usually go through the Next.js rewrite or Backend.
        // Let's assume the Next.js middleware/proxy handles `/api/ai/interact` -> `ai_service:8000/interact`
        // OR we use the backend proxy.
        // Let's use the hook's base URL.
        const url = `${getApiUrl()}/api/interact`; 

        try {
            await fetchEventSource(url, {
                method: "POST",
                body: formData,
                signal: abortControllerRef.current.signal,
                openWhenHidden: true,
                async onopen(response) {
                    if (response.ok) {
                        return; // Everything is good
                    } else {
                        // Handle errors
                        if (response.status >= 400 && response.status < 500 && response.status !== 429) {
                             throw new Error(`Client Error: ${response.status}`);
                        }
                        throw new Error(`Server Error: ${response.status}`);
                    }
                },
                onmessage(msg) {
                    if (msg.event === "transcript") {
                        try {
                            const data = JSON.parse(msg.data);
                            onNewMessage({
                                role: data.role === "assistant" ? "ai" : "user",
                                content: data.text
                            });
                        } catch (e) {
                            console.error("Failed to parse transcript:", e);
                        }
                    } else if (msg.event === "audio") {
                        onAudioData(msg.data); // base64
                    } else if (msg.event === "status") {
                        if (msg.data === "thinking") {
                            onThinkingStateChange(true);
                        } else if (msg.data === "done") {
                            onThinkingStateChange(false);
                            setIsProcessing(false);
                        }
                    } else if (msg.event === "error") {
                        onError(msg.data);
                        onThinkingStateChange(false);
                        setIsProcessing(false);
                    }
                },
                onclose() {
                    setIsProcessing(false);
                    onThinkingStateChange(false);
                },
                onerror(err) {
                    console.error("SSE Error:", err);
                    onError("Connection error.");
                    setIsProcessing(false);
                    onThinkingStateChange(false);
                    throw err; // Rethrow to stop retries if needed
                }
            });
        } catch (err: any) {
            if (err.name !== 'AbortError') {
                onError(err.message || "Failed to send message.");
            }
            setIsProcessing(false);
            onThinkingStateChange(false);
        }
    }, [sessionId, selectedScenario, getApiUrl, onNewMessage, onThinkingStateChange, onAudioData, onError]);

    const cancel = useCallback(() => {
        if (abortControllerRef.current) {
            abortControllerRef.current.abort();
            abortControllerRef.current = null;
            setIsProcessing(false);
            onThinkingStateChange(false);
        }
    }, [onThinkingStateChange]);

    return { sendMessage, cancel, isProcessing };
};