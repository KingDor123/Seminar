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
          <span key={i} className="bg-red-500/20 text-red-300 px-1 rounded mx-0.5 border border-red-500/30">
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
    <div className="flex flex-col h-full bg-slate-900/50 backdrop-blur-md rounded-2xl border border-slate-800 overflow-hidden">
      <div className="p-4 border-b border-slate-800 bg-slate-900/80 flex items-center gap-2">
        <ScrollText className="h-4 w-4 text-cyan-400" />
        <h3 className="text-sm font-bold uppercase tracking-widest text-slate-400">Transcript Analysis</h3>
      </div>
      <div className="p-6 font-mono text-sm leading-relaxed text-slate-300 overflow-y-auto custom-scrollbar">
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
                        ? 'bg-blue-600/20 text-slate-100'
                        : 'bg-slate-800/60 text-slate-200'
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
