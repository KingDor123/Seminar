import React from 'react';
import { ScrollText } from 'lucide-react';
import type { ChatMessage } from '../../types/chat';

interface TranscriptViewerProps {
  text: string;
  messages?: ChatMessage[];
}

const FILLERS = ['כאילו', 'כזה', 'אממ', 'אה', 'בעצם', 'סוג של', 'יעני'];
const FILLERS_REGEX = new RegExp(`(${FILLERS.map(f => f.replace(/\s+/g, '\\s+')).join('|')})`, 'gi');

export const TranscriptViewer: React.FC<TranscriptViewerProps> = ({ text, messages }) => {
  // Simple regex-based highlighter
  const renderHighlighted = (content: string) => {
    // Split by space but preserve punctuation is tricky. 
    // Let's use a simpler split for visual demo or Regex replace with spans.
    const parts = content.split(FILLERS_REGEX);
    
    return parts.map((part, i) => {
      const normalized = part.replace(/\s+/g, ' ').trim().toLowerCase();
      if (FILLERS.includes(normalized)) {
        return (
          <span key={i} className="bg-destructive/10 text-destructive px-1 rounded mx-0.5 border border-destructive/20">
            {part}
          </span>
        );
      }
      return part;
    });
  };

  const getSentimentEmoji = (sentiment?: string | null) => {
    if (!sentiment) return null;
    const normalized = sentiment.toLowerCase();
    if (normalized.includes('joy') || normalized.includes('positive')) return '🟢';
    if (normalized.includes('anger') || normalized.includes('negative')) return '🔴';
    if (normalized.includes('sadness')) return '🔵';
    if (normalized.includes('neutral')) return '⚪';
    return null;
  };

  return (
    <div className="flex flex-col h-full bg-card rounded-2xl border border-border overflow-hidden">
      <div className="p-4 border-b border-border bg-card flex items-center gap-2">
        <ScrollText className="h-4 w-4 text-primary" />
        <h3 className="text-sm font-bold uppercase tracking-widest text-muted-foreground">Transcript Analysis</h3>
      </div>
      <div className="p-6 font-mono text-sm leading-relaxed text-foreground overflow-y-auto custom-scrollbar">
        {messages && messages.length > 0 ? (
          <div className="space-y-4">
            {messages.map((message, index) => {
              const sentimentEmoji = getSentimentEmoji(message.sentiment);
              return (
                <div
                  key={index}
                  className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                    <div
                      className={`max-w-[85%] rounded-2xl px-3 py-2 ${
                        message.role === 'user'
                          ? 'bg-chat-user text-foreground'
                          : 'bg-chat-bot border border-border text-foreground'
                      }`}
                    >
                    <div className="flex items-start gap-2">
                      {sentimentEmoji && (
                        <span className="text-xs" title={message.sentiment || undefined}>
                          {sentimentEmoji}
                        </span>
                      )}
                      <span>{renderHighlighted(message.content)}</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          renderHighlighted(text)
        )}
      </div>
    </div>
  );
};
