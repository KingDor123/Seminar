import React from 'react';
import { ScrollText } from 'lucide-react';

interface TranscriptViewerProps {
  text: string;
}

const FILLERS = ['כאילו', 'כזה', 'אממ', 'אה', 'בעצם', 'סוג של', 'יעני'];
const FILLERS_REGEX = new RegExp(`(${FILLERS.map(f => f.replace(/\s+/g, '\\s+')).join('|')})`, 'gi');

export const TranscriptViewer: React.FC<TranscriptViewerProps> = ({ text }) => {
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

  return (
    <div className="flex flex-col h-full bg-slate-900/50 backdrop-blur-md rounded-2xl border border-slate-800 overflow-hidden">
      <div className="p-4 border-b border-slate-800 bg-slate-900/80 flex items-center gap-2">
        <ScrollText className="h-4 w-4 text-cyan-400" />
        <h3 className="text-sm font-bold uppercase tracking-widest text-slate-400">Transcript Analysis</h3>
      </div>
      <div className="p-6 font-mono text-sm leading-relaxed text-slate-300 overflow-y-auto custom-scrollbar">
        {renderHighlighted(text)}
      </div>
    </div>
  );
};
