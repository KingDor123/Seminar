import { useState, useRef, useCallback, useEffect } from 'react';
import { fetchEventSource } from '@microsoft/fetch-event-source';
import { SCENARIOS } from '../constants/appConstants';
import { useApi } from './useApi';

interface ChatMessage {
    role: "user" | "ai";
    content: string;
    partial?: boolean;
}

export interface StreamMetrics {
    filler_count?: number;
    wpm?: number;
    sentiment?: number;
    latency?: number;
}

interface UseStreamingConversationProps {
    sessionId: number | null;
    selectedScenario: string;
    language?: "en-US" | "he-IL";
    onNewMessage: (message: ChatMessage) => void;
    onThinkingStateChange: (isThinking: boolean) => void;
    onAudioData: (base64Audio: string) => void;
    onMetricsUpdate?: (metrics: StreamMetrics) => void;
    onError: (error: string) => void;
}

export const useStreamingConversation = ({
    sessionId,
    selectedScenario,
    language,
    onNewMessage,
    onThinkingStateChange,
    onAudioData,
    onMetricsUpdate,
    onError,
}: UseStreamingConversationProps) => {
    const { getApiUrl } = useApi();
    const abortControllerRef = useRef<AbortController | null>(null);
    const [isProcessing, setIsProcessing] = useState(false);
    
    // --- Throttling Buffer ---
    const tokenBuffer = useRef<{ role: "ai" | "user"; text: string }[]>([]);
    const bufferInterval = useRef<NodeJS.Timeout | null>(null);

    // Flush buffer to state every 100ms to prevent "Render Hell"
    useEffect(() => {
        bufferInterval.current = setInterval(() => {
            if (tokenBuffer.current.length > 0) {
                // Process buffering: In a real chat app, you might want to debounce or 
                // accumulate text. Here we flush all pending tokens in sequence.
                // Optimally, we could merge consecutive AI tokens.
                
                const queue = [...tokenBuffer.current];
                tokenBuffer.current = [];

                queue.forEach(item => {
                    onNewMessage({
                        role: item.role,
                        content: item.text,
                        partial: true // Assume streaming content is partial until 'done'
                    });
                });
            }
        }, 100);

        return () => {
            if (bufferInterval.current) clearInterval(bufferInterval.current);
        };
    }, [onNewMessage]);

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
        if (language) formData.append("language", language);

        const scenario = SCENARIOS.find(s => s.id === selectedScenario);
        const systemPrompt = scenario?.prompt || "You are a helpful assistant.";
        formData.append("system_prompt", systemPrompt);

        const url = `${getApiUrl()}/api/interact`; 

        try {
            await fetchEventSource(url, {
                method: "POST",
                body: formData,
                signal: abortControllerRef.current.signal,
                openWhenHidden: true,
                async onopen(response) {
                    if (response.ok) {
                        return; 
                    } else {
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
                            
                            // Push to buffer instead of immediate state update
                            if (data.text) {
                                tokenBuffer.current.push({
                                    role: data.role === "assistant" ? "ai" : "user",
                                    text: data.text
                                });
                            }

                            // Capture Metrics if available
                            if (data.metrics && onMetricsUpdate) {
                                onMetricsUpdate(data.metrics);
                            }

                        } catch (e) {
                            console.error("Failed to parse transcript:", e);
                        }
                    } else if (msg.event === "audio") {
                        onAudioData(msg.data); 
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
                    // Do not retry on fatal errors
                    throw err; 
                }
            });
        } catch (err: any) {
            if (err.name !== 'AbortError') {
                onError(err.message || "Failed to send message.");
            }
            setIsProcessing(false);
            onThinkingStateChange(false);
        }
    }, [sessionId, selectedScenario, language, getApiUrl, onThinkingStateChange, onAudioData, onMetricsUpdate, onError]);

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
