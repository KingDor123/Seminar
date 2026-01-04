'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { sessionService } from '../../services/sessionService';
import { 
  Activity, 
  MessageSquare, 
  Smile, 
  Frown, 
  Meh, 
  Calendar,
  LayoutDashboard,
  Trophy,
  BrainCircuit,
  AlertCircle
} from 'lucide-react';
import { MetricCard } from '../../components/dashboard/MetricCard';
import { PageShell } from '../../components/layout/PageShell';
import { cn } from '../../lib/utils';

// --- Interfaces ---

interface SessionListItem {
  session_id: number;
  created_at: string;
  scenario_id: string;
  message_count: number;
  overall_sentiment: string;
}

interface DashboardStats {
  overview: {
    total_sessions: number;
    total_messages: number;
    avg_score: number;
  };
  sentiment: {
    positive: number;
    neutral: number;
    negative: number;
  };
}

interface ChatMessage {
  id: number;
  role: "user" | "ai";
  content: string;
  sentiment?: string | null; 
}

interface ApiMessage {
  id: number;
  role: string;
  content: string;
  sentiment?: string | null;
}

const AI_SERVICE_URL = "http://localhost:8000"; 

export default function SessionsPage() {
  const { user, isLoading: isAuthLoading } = useAuth();
  
  const [sessionList, setSessionList] = useState<SessionListItem[]>([]);
  const [dashboardStats, setDashboardStats] = useState<DashboardStats | null>(null);
  const [selectedSessionId, setSelectedSessionId] = useState<number | null>(null);
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [loadingChat, setLoadingChat] = useState(false);
  const [isLoadingDashboard, setIsLoadingDashboard] = useState(true);
  const [isLoadingSessions, setIsLoadingSessions] = useState(true);
  const [dashboardError, setDashboardError] = useState<string | null>(null);
  const [sessionsError, setSessionsError] = useState<string | null>(null);

  // --- Fetch Initial Data ---
  useEffect(() => {
    if (!user) return;
    let isActive = true;
    const fetchData = async () => {
      try {
        setIsLoadingSessions(true);
        setIsLoadingDashboard(true);
        setSessionsError(null);
        setDashboardError(null);

        const [listRes, dashRes] = await Promise.allSettled([
          fetch(`${AI_SERVICE_URL}/analytics/sessions_list`),
          fetch(`${AI_SERVICE_URL}/analytics/dashboard`)
        ]);

        if (!isActive) return;

        if (listRes.status === "fulfilled" && listRes.value.ok) {
          const data = await listRes.value.json();
          setSessionList(Array.isArray(data) ? data : []);
        } else {
          setSessionList([]);
          setSessionsError("Could not load sessions.");
        }
        setIsLoadingSessions(false);

        if (dashRes.status === "fulfilled" && dashRes.value.ok) {
          const data = await dashRes.value.json();
          if (data && data.overview && data.sentiment) {
            setDashboardStats(data);
          } else {
            setDashboardStats(null);
            setDashboardError("Could not load stats.");
          }
        } else {
          setDashboardStats(null);
          setDashboardError("Could not load stats.");
        }
        setIsLoadingDashboard(false);
      } catch (e) {
        console.error("Init Fetch Error:", e);
        if (!isActive) return;
        setSessionsError("Could not load sessions.");
        setDashboardError("Could not load stats.");
        setSessionList([]);
        setDashboardStats(null);
        setIsLoadingSessions(false);
        setIsLoadingDashboard(false);
      }
    };
    fetchData();
    return () => {
      isActive = false;
    };
  }, [user]);

  // --- Fetch Session Detail ---
  useEffect(() => {
    if (!selectedSessionId) return;
    const fetchChat = async () => {
      setLoadingChat(true);
      try {
        const messages = await sessionService.getSessionMessages(selectedSessionId);
        const formatted: ChatMessage[] = messages.map((m: ApiMessage) => ({
            id: m.id,
            role: m.role === 'ai' ? 'ai' : 'user',
            content: m.content,
            sentiment: m.sentiment
        }));
        setChatHistory(formatted);
      } catch (e) {
        console.error("Chat Fetch Error:", e);
        setChatHistory([]);
      } finally {
        setLoadingChat(false);
      }
    };
    fetchChat();
  }, [selectedSessionId]);

  // --- UI Helpers ---
  const getSentimentStyles = (sentiment: string) => {
      const s = sentiment?.toLowerCase() || "neutral";
      if (s.includes("positive") || s.includes("joy")) {
          return {
              color: "text-stat-positive bg-stat-positive/10 border-stat-positive/20",
              icon: <Smile className="w-3.5 h-3.5" />,
              label: "Positive"
          };
      }
      if (s.includes("negative") || s.includes("stress") || s.includes("anger") || s.includes("fear")) {
          return {
              color: "text-destructive bg-destructive/10 border-destructive/20",
              icon: <Frown className="w-3.5 h-3.5" />,
              label: s.charAt(0).toUpperCase() + s.slice(1)
          };
      }
      return {
          color: "text-muted-foreground bg-muted border-border",
          icon: <Meh className="w-3.5 h-3.5" />,
          label: "Neutral"
      };
  };

  if (isAuthLoading) {
    return (
      <PageShell className="flex items-center justify-center">
        <div className="text-sm text-muted-foreground">Initializing...</div>
      </PageShell>
    );
  }
  if (!user) {
    return (
      <PageShell className="flex items-center justify-center">
        <div className="text-sm text-muted-foreground">Please log in.</div>
      </PageShell>
    );
  }

  const showSessionsSkeleton = isLoadingSessions && sessionList.length === 0 && !sessionsError;
  const showDashboardSkeleton = isLoadingDashboard && !dashboardStats && !dashboardError;
  const sentimentOrder: Array<keyof DashboardStats["sentiment"]> = ["positive", "neutral", "negative"];
  const sentimentLabels: Record<keyof DashboardStats["sentiment"], string> = {
    positive: "Positive",
    neutral: "Neutral",
    negative: "Negative"
  };
  const sentimentTotal = dashboardStats
    ? sentimentOrder.reduce((sum, item) => sum + dashboardStats.sentiment[item], 0) || 1
    : 1;

  return (
    <PageShell>
      <div className="container mx-auto max-w-6xl px-4">
        <div className="mb-6 animate-fade-in">
          <h1 className="text-3xl font-heading font-bold text-foreground">Your Journey</h1>
          <p className="text-muted-foreground">
            Track your progress and revisit your sessions.
          </p>
        </div>

        <div className="grid gap-6 lg:grid-cols-[280px,1fr]">
          <aside className="rounded-2xl border border-border bg-card p-4">
            <div className="mb-3 flex items-center gap-2 text-sm font-heading font-semibold text-foreground">
              <BrainCircuit className="h-4 w-4 text-primary" />
              Explorer
            </div>
            <button
              onClick={() => setSelectedSessionId(null)}
              className={cn(
                "w-full rounded-xl border px-4 py-3 text-left transition-all",
                selectedSessionId === null
                  ? "bg-primary/10 border-primary/40 text-primary"
                  : "bg-background border-border text-muted-foreground hover:bg-muted/60",
              )}
            >
              <div className="flex items-center gap-3">
                <LayoutDashboard className="h-5 w-5" />
                <span className="font-medium">Overview</span>
              </div>
            </button>

            <div className="mt-4 space-y-2">
              {showSessionsSkeleton && (
                <div className="space-y-3">
                  {[...Array(4)].map((_, idx) => (
                    <div key={idx} className="h-14 rounded-xl bg-muted/60 animate-pulse" />
                  ))}
                </div>
              )}
              {sessionsError && (
                <div className="rounded-xl border border-destructive/20 bg-destructive/10 px-3 py-2 text-sm text-destructive flex items-center gap-2">
                  <AlertCircle className="w-4 h-4" />
                  <span>{sessionsError}</span>
                </div>
              )}
              {!isLoadingSessions && !sessionsError && sessionList.length === 0 && (
                <div className="px-3 py-2 text-sm text-muted-foreground">No sessions yet.</div>
              )}
              {!showSessionsSkeleton && !sessionsError && sessionList.map((session) => (
                <button
                  key={session.session_id}
                  onClick={() => setSelectedSessionId(session.session_id)}
                  className={cn(
                    "w-full rounded-xl border px-4 py-3 text-left transition-all",
                    selectedSessionId === session.session_id
                      ? "bg-primary/10 border-primary/40"
                      : "bg-background border-border hover:bg-muted/60",
                  )}
                >
                  <div className="flex justify-between items-start mb-2">
                    <span className="text-sm font-semibold text-foreground capitalize">{session.scenario_id}</span>
                    <div className={cn(
                      "h-2 w-2 rounded-full",
                      session.overall_sentiment === 'Positive'
                        ? "bg-stat-positive"
                        : session.overall_sentiment === 'Negative'
                        ? "bg-destructive"
                        : "bg-muted-foreground",
                    )} />
                  </div>
                  <div className="flex justify-between text-[10px] text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <Calendar className="w-3 h-3" />
                      {new Date(session.created_at).toLocaleDateString()}
                    </span>
                    <span className="flex items-center gap-1">
                      <MessageSquare className="w-3 h-3" />
                      {session.message_count}
                    </span>
                  </div>
                </button>
              ))}
            </div>
          </aside>

          <main className="space-y-6">
            {!selectedSessionId && (
              <div className="space-y-6">
                {showDashboardSkeleton && (
                  <div className="space-y-4 animate-pulse">
                    <div className="h-6 w-56 rounded bg-muted/60" />
                    <div className="h-4 w-72 rounded bg-muted/40" />
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      {[...Array(3)].map((_, idx) => (
                        <div key={idx} className="h-28 rounded-2xl bg-muted/50" />
                      ))}
                    </div>
                    <div className="h-48 rounded-2xl bg-muted/50" />
                  </div>
                )}

                {dashboardError && (
                  <div className="rounded-2xl border border-destructive/20 bg-destructive/10 p-4 text-destructive flex items-center gap-3">
                    <AlertCircle className="w-5 h-5" />
                    <span>{dashboardError}</span>
                  </div>
                )}

                {dashboardStats && !showDashboardSkeleton && !dashboardError && (
                  <div className="space-y-6 animate-fade-in">
                    <header>
                      <h2 className="text-2xl font-heading font-semibold text-foreground">Performance Overview</h2>
                      <p className="text-sm text-muted-foreground">Aggregated insights from all simulations.</p>
                    </header>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <MetricCard
                        title="Total Sessions"
                        value={dashboardStats.overview.total_sessions}
                        unit=""
                        icon={Activity}
                        variant="positive"
                        delay={0}
                      />
                      <MetricCard
                        title="Total Messages"
                        value={dashboardStats.overview.total_messages}
                        unit=""
                        icon={MessageSquare}
                        variant="neutral"
                        delay={100}
                      />
                      <MetricCard
                        title="Impact Score"
                        value={dashboardStats.overview.avg_score}
                        unit="/ 100"
                        icon={Trophy}
                        variant="accent"
                        delay={200}
                      />
                    </div>
                    <div className="rounded-2xl border border-border bg-card p-6">
                      <h3 className="text-lg font-heading font-semibold text-foreground mb-4">Sentiment Distribution</h3>
                      <div className="space-y-4">
                        {sentimentOrder.map((key) => {
                          const count = dashboardStats.sentiment[key];
                          const label = sentimentLabels[key];
                          const barColor =
                            key === "positive"
                              ? "bg-stat-positive"
                              : key === "negative"
                              ? "bg-destructive"
                              : "bg-stat-neutral";
                          return (
                            <div key={key}>
                              <div className="flex justify-between text-sm mb-1 text-muted-foreground">
                                <span>{label}</span>
                                <span className="font-mono text-foreground">{count}</span>
                              </div>
                              <div className="w-full bg-muted rounded-full h-2">
                                <div
                                  className={cn("h-2 rounded-full transition-all duration-700", barColor)}
                                  style={{ width: `${(count / sentimentTotal) * 100}%` }}
                                />
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {selectedSessionId && (
              <div className="rounded-2xl border border-border bg-card p-6 animate-fade-in">
                <header className="mb-6 border-b border-border pb-4">
                  <h2 className="text-2xl font-heading font-semibold text-foreground">
                    Session #{selectedSessionId} History
                  </h2>
                </header>

                {loadingChat ? (
                  <div className="flex items-center justify-center text-muted-foreground">Loading transcript...</div>
                ) : (
                  <div className="space-y-6">
                    {chatHistory.map((msg) => {
                      const sentiment = getSentimentStyles(msg.sentiment || "");
                      return (
                        <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                          <div className="max-w-[80%] relative">
                            {msg.role === 'user' && msg.sentiment && (
                              <div className={`absolute -top-3.5 -right-2 px-2 py-0.5 rounded-full border shadow-sm flex items-center gap-1.5 z-20 font-semibold text-[10px] tracking-tight ${sentiment.color}`}>
                                {sentiment.icon}
                                <span>{sentiment.label}</span>
                              </div>
                            )}

                            <div
                              className={cn(
                                "rounded-2xl px-4 py-3 text-sm leading-relaxed",
                                msg.role === 'user'
                                  ? "bg-chat-user text-foreground rounded-br-md"
                                  : "bg-chat-bot border border-border rounded-bl-md text-foreground",
                              )}
                            >
                              {msg.content}
                            </div>

                            <div className={cn(
                              "mt-1.5 flex items-center gap-2 text-[10px] text-muted-foreground",
                              msg.role === 'user' ? 'justify-end' : 'justify-start',
                            )}>
                              <span className="font-mono uppercase tracking-widest">
                                {msg.role === 'user' ? 'Patient' : 'Avatar'}
                              </span>
                              {msg.role === 'user' && !msg.sentiment && (
                                <span title="No analysis available">
                                  <AlertCircle className="w-3 h-3 text-muted-foreground/60" />
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            )}
          </main>
        </div>
      </div>
    </PageShell>
  );
}
