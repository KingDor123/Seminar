import React from 'react';
import { format } from 'date-fns';
import { SessionData } from '../../utils/mockData';
import { Activity, Calendar, ChevronRight } from 'lucide-react';
import { clsx } from 'clsx';

interface SessionSidebarProps {
  sessions: SessionData[];
  selectedId: number | null;
  onSelect: (id: number) => void;
}

export const SessionSidebar: React.FC<SessionSidebarProps> = ({ sessions, selectedId, onSelect }) => {
  return (
    <div className="flex h-full w-full flex-col overflow-hidden bg-slate-900/50 border-r border-slate-800 backdrop-blur-xl">
      <div className="p-4 border-b border-slate-800">
        <h2 className="text-sm font-bold uppercase tracking-widest text-slate-400 flex items-center gap-2">
          <Activity className="h-4 w-4 text-cyan-400" />
          History Log
        </h2>
      </div>
      <div className="flex-1 overflow-y-auto p-2 space-y-2">
        {sessions.map((session) => (
          <button
            key={session.id}
            onClick={() => onSelect(session.id)}
            className={clsx(
              "w-full text-left rounded-xl p-3 transition-all border",
              selectedId === session.id
                ? "bg-cyan-500/10 border-cyan-500/50 shadow-[0_0_15px_rgba(6,182,212,0.15)]"
                : "bg-slate-800/40 border-transparent hover:bg-slate-800 hover:border-slate-700"
            )}
          >
            <div className="flex justify-between items-start">
              <div>
                <h3 className={clsx(
                  "font-semibold text-sm",
                  selectedId === session.id ? "text-cyan-300" : "text-slate-200"
                )}>
                  {session.scenario}
                </h3>
                <div className="flex items-center gap-1.5 mt-1 text-xs text-slate-500">
                  <Calendar className="h-3 w-3" />
                  {format(new Date(session.date), 'MMM d, HH:mm')}
                </div>
              </div>
              {selectedId === session.id && (
                <ChevronRight className="h-4 w-4 text-cyan-400 animate-pulse" />
              )}
            </div>
            
            {/* Mini Score Indicator */}
            <div className="mt-3 flex items-center gap-2">
                <div className="h-1.5 w-full bg-slate-700/50 rounded-full overflow-hidden">
                    <div 
                        className={clsx(
                            "h-full rounded-full transition-all",
                            session.stats.score > 80 ? "bg-emerald-400" : session.stats.score > 60 ? "bg-yellow-400" : "bg-red-400"
                        )}
                        style={{ width: `${session.stats.score}%` }}
                    />
                </div>
                <span className="text-[10px] font-mono text-slate-400">{session.stats.score}%</span>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
};
