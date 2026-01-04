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
    <div className="flex h-full w-full flex-col overflow-hidden bg-card border-r border-border">
      <div className="p-4 border-b border-border">
        <h2 className="text-sm font-bold uppercase tracking-widest text-muted-foreground flex items-center gap-2">
          <Activity className="h-4 w-4 text-primary" />
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
                ? "bg-primary/10 border-primary/40 shadow-sm"
                : "bg-background border-transparent hover:bg-muted/60 hover:border-border"
            )}
          >
            <div className="flex justify-between items-start">
              <div>
                <h3 className={clsx(
                  "font-semibold text-sm",
                  selectedId === session.id ? "text-primary" : "text-foreground"
                )}>
                  {session.scenario}
                </h3>
                <div className="flex items-center gap-1.5 mt-1 text-xs text-muted-foreground">
                  <Calendar className="h-3 w-3" />
                  {format(new Date(session.date), 'MMM d, HH:mm')}
                </div>
              </div>
              {selectedId === session.id && (
                <ChevronRight className="h-4 w-4 text-primary animate-pulse" />
              )}
            </div>
            
            {/* Mini Score Indicator */}
            <div className="mt-3 flex items-center gap-2">
                <div className="h-1.5 w-full bg-muted rounded-full overflow-hidden">
                    <div 
                        className={clsx(
                            "h-full rounded-full transition-all",
                            session.stats.score > 80 ? "bg-stat-positive" : session.stats.score > 60 ? "bg-stat-accent" : "bg-destructive"
                        )}
                        style={{ width: `${session.stats.score}%` }}
                    />
                </div>
                <span className="text-[10px] font-mono text-muted-foreground">{session.stats.score}%</span>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
};
