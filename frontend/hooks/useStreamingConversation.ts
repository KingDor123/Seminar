import { useState, useRef, useCallback, useEffect } from 'react';
import { useApi } from './useApi';

interface ChatMessage {
    role: "user" | "ai";
    content: string;
    partial?: boolean;
}

export interface StreamMetrics {
    filler_count?: number;
    word_count?: number;
    fluency_score?: number;
    sentiment?: number;
    sentiment_label?: "positive" | "neutral" | "negative";
    sentiment_confidence?: number;
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
    onNewMessage,
    onThinkingStateChange,
    onAudioData,
    onMetricsUpdate,
    onError,
}: UseStreamingConversationProps) => {
    const { getApiUrl } = useApi();
    const abortControllerRef = useRef<AbortController | null>(null);
    const [isProcessing, setIsProcessing] = useState(false);
    const lastOptimisticText = useRef<string | null>(null);

    const sendMessage = useCallback(async (
        text: string | null, 
        audioBlob: Blob | null
    ) => {
        if (!sessionId) {
            onError("No active session.");
            return;
        }
        if (!selectedScenario) {
            onError("No scenario selected.");
            return;
        }

        if (abortControllerRef.current) {
            abortControllerRef.current.abort();
        }
        abortControllerRef.current = new AbortController();

        // --- OPTIMISTIC UI UPDATE ---
        if (text) {
            lastOptimisticText.current = text;
            onNewMessage({
                role: "user",
                content: text,
                partial: false
            });
        }

        setIsProcessing(true);
        onThinkingStateChange(true);

        const formData = new FormData();
        formData.append("session_id", sessionId.toString());
        
        if (text) formData.append("text", text);
        if (audioBlob) formData.append("audio", audioBlob, "input.wav");
        formData.append("scenario_id", selectedScenario);

        const url = `${getApiUrl()}/api/interact`; 

        try {
            const response = await fetch(url, {
                method: "POST",
                body: formData,
                signal: abortControllerRef.current.signal,
            });

            if (!response.ok) {
                throw new Error(`Server Error: ${response.status}`);
            }

            if (!response.body) {
                throw new Error("Response body is empty");
            }

            const reader = response.body.getReader();
            // CRITICAL: Instantiate decoder OUTSIDE the loop for correct state handling
            const decoder = new TextDecoder("utf-8");
            
            let done = false;
            let currentEvent = "";
            let buffer = "";

            while (!done) {
                const { value, done: doneReading } = await reader.read();
                done = doneReading;
                
                // CRITICAL: Use { stream: true } to handle partial Hebrew characters across chunks
                const chunk = decoder.decode(value, { stream: !done });
                buffer += chunk;

                const lines = buffer.split("\n");
                // Keep the last partial line in the buffer
                buffer = lines.pop() || "";

                for (const line of lines) {
                    const trimmedLine = line.trim();
                    if (!trimmedLine) continue;

                    if (trimmedLine.startsWith("event: ")) {
                        currentEvent = trimmedLine.replace("event: ", "");
                    } else if (trimmedLine.startsWith("data: ")) {
                        const dataStr = trimmedLine.replace("data: ", "");
                        
                        if (currentEvent === "transcript") {
                            try {
                                const data = JSON.parse(dataStr);
                                
                                // De-duplication for optimistic update
                                if (data.role === "user" && data.text === lastOptimisticText.current) {
                                    continue;
                                }

                                if (data.text) {
                                    onNewMessage({
                                        role: data.role === "assistant" ? "ai" : "user",
                                        content: data.text,
                                        partial: true 
                                    });
                                }

                                if (data.metrics && onMetricsUpdate) {
                                    onMetricsUpdate(data.metrics);
                                }
                            } catch (e) {
                                console.error("Failed to parse transcript JSON", e);
                            }
                        } else if (currentEvent === "audio") {
                            onAudioData(dataStr); 
                        } else if (currentEvent === "status") {
                            if (dataStr === "thinking") {
                                onThinkingStateChange(true);
                            } else if (dataStr === "done") {
                                onThinkingStateChange(false);
                                setIsProcessing(false);
                                lastOptimisticText.current = null;
                            }
                        } else if (currentEvent === "error") {
                            onError(dataStr);
                            onThinkingStateChange(false);
                            setIsProcessing(false);
                        }
                    }
                }
            }
        } catch (err: any) {
            if (err.name !== 'AbortError') {
                onError(err.message || "Failed to send message.");
            }
            setIsProcessing(false);
            onThinkingStateChange(false);
        }
    }, [sessionId, selectedScenario, getApiUrl, onThinkingStateChange, onAudioData, onMetricsUpdate, onError, onNewMessage]);

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
