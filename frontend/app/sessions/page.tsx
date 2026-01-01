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
  sentiment?: string; 
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
        const formatted: ChatMessage[] = messages.map((m: any) => ({
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
              color: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
              icon: <Smile className="w-3.5 h-3.5" />,
              label: "Positive"
          };
      }
      if (s.includes("negative") || s.includes("stress") || s.includes("anger") || s.includes("fear")) {
          return {
              color: "text-rose-400 bg-rose-500/10 border-rose-500/20",
              icon: <Frown className="w-3.5 h-3.5" />,
              label: s.charAt(0).toUpperCase() + s.slice(1)
          };
      }
      return {
          color: "text-slate-400 bg-slate-500/10 border-slate-500/20",
          icon: <Meh className="w-3.5 h-3.5" />,
          label: "Neutral"
      };
  };

  if (isAuthLoading) return <div className="min-h-screen bg-slate-950 flex items-center justify-center text-slate-500">Initializing...</div>;
  if (!user) return <div className="min-h-screen bg-slate-950 flex items-center justify-center text-slate-500">Please log in.</div>;

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
    <div className="flex h-screen w-full bg-slate-950 text-slate-100 font-sans overflow-hidden">
      
      {/* Sidebar */}
      <aside className="w-80 flex-shrink-0 border-r border-slate-800/50 bg-slate-900/30 flex flex-col">
        <div className="p-6 border-b border-slate-800/50">
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
                <BrainCircuit className="w-5 h-5 text-cyan-400" />
                Explorer
            </h2>
        </div>
        <div className="flex-1 overflow-y-auto p-4 space-y-2">
            <button
                onClick={() => setSelectedSessionId(null)}
                className={`w-full text-left px-4 py-3 rounded-xl transition-all border ${
                    selectedSessionId === null 
                    ? "bg-cyan-500/10 border-cyan-500/50 text-cyan-100" 
                    : "bg-slate-800/30 border-transparent text-slate-400 hover:bg-slate-800/50"
                }`}
            >
                <div className="flex items-center gap-3">
                    <LayoutDashboard className="w-5 h-5" />
                    <span className="font-medium">Overview</span>
                </div>
            </button>
            <div className="h-px bg-slate-800/50 my-2" />
            {showSessionsSkeleton && (
              <div className="space-y-3 px-1">
                {[...Array(4)].map((_, idx) => (
                  <div key={idx} className="h-14 rounded-xl bg-slate-800/40 animate-pulse" />
                ))}
              </div>
            )}
            {sessionsError && (
              <div className="px-3 py-2 text-sm text-rose-400 flex items-center gap-2">
                <AlertCircle className="w-4 h-4" />
                <span>{sessionsError}</span>
              </div>
            )}
            {!isLoadingSessions && !sessionsError && sessionList.length === 0 && (
              <div className="px-3 py-2 text-sm text-slate-500">No sessions yet.</div>
            )}
            {!showSessionsSkeleton && !sessionsError && sessionList.map((session) => (
              <button
                key={session.session_id}
                onClick={() => setSelectedSessionId(session.session_id)}
                className={`w-full text-left p-4 rounded-xl transition-all border group relative ${
                  selectedSessionId === session.session_id
                  ? "bg-blue-600/10 border-blue-500/50"
                  : "bg-slate-800/20 border-slate-800/50 hover:border-slate-700"
                }`}
              >
                <div className="flex justify-between items-start mb-1">
                  <span className="text-sm font-bold text-white capitalize">{session.scenario_id}</span>
                  <div className={`w-2 h-2 rounded-full ${
                    session.overall_sentiment === 'Positive' ? 'bg-emerald-500' :
                    session.overall_sentiment === 'Negative' ? 'bg-rose-500' : 'bg-slate-500'
                  }`} />
                </div>
                <div className="flex justify-between text-[10px] text-slate-500">
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

      {/* Main Content */}
      <main className="flex-1 relative overflow-hidden flex flex-col">
        <div className="flex-1 overflow-y-auto p-8 z-10">
            
            {!selectedSessionId && (
              <div className="space-y-8">
                {showDashboardSkeleton && (
                  <div className="space-y-6 animate-pulse">
                    <div className="h-8 w-64 bg-slate-800/60 rounded" />
                    <div className="h-4 w-80 bg-slate-800/40 rounded" />
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                      {[...Array(3)].map((_, idx) => (
                        <div key={idx} className="h-28 bg-slate-800/40 rounded-2xl" />
                      ))}
                    </div>
                    <div className="h-56 bg-slate-800/40 rounded-2xl" />
                  </div>
                )}

                {dashboardError && (
                  <div className="rounded-2xl border border-rose-500/30 bg-rose-500/10 p-6 text-rose-200 flex items-center gap-3">
                    <AlertCircle className="w-5 h-5" />
                    <span>{dashboardError}</span>
                  </div>
                )}

                {dashboardStats && !showDashboardSkeleton && !dashboardError && (
                  <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
                    <header>
                      <h1 className="text-3xl font-bold text-white">Performance Overview</h1>
                      <p className="text-slate-400">Aggregated insights from all simulations.</p>
                    </header>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                      <MetricCard title="Total Sessions" value={dashboardStats.overview.total_sessions} unit="" icon={Activity} color="cyan" />
                      <MetricCard title="Total Messages" value={dashboardStats.overview.total_messages} unit="" icon={MessageSquare} color="blue" />
                      <MetricCard title="Impact Score" value={dashboardStats.overview.avg_score} unit="/ 100" icon={Trophy} color="yellow" />
                    </div>
                    <div className="bg-slate-900/50 backdrop-blur-md border border-slate-800 rounded-2xl p-6">
                      <h3 className="text-lg font-semibold text-white mb-6">Sentiment Distribution</h3>
                      <div className="space-y-4">
                        {sentimentOrder.map((key) => {
                          const count = dashboardStats.sentiment[key];
                          const label = sentimentLabels[key];
                          const barColor =
                            key === "positive"
                              ? "bg-emerald-500"
                              : key === "negative"
                              ? "bg-rose-500"
                              : "bg-slate-500";
                          return (
                            <div key={key}>
                              <div className="flex justify-between text-sm mb-1 text-slate-300">
                                <span>{label}</span>
                                <span className="font-mono text-white">{count}</span>
                              </div>
                              <div className="w-full bg-slate-800 rounded-full h-2">
                                <div
                                  className={`h-2 rounded-full transition-all duration-1000 ${barColor}`}
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
                <div className="h-full flex flex-col animate-in fade-in zoom-in-95 duration-300">
                    <header className="mb-8 pb-4 border-b border-slate-800/50">
                        <h1 className="text-2xl font-bold text-white">Session #{selectedSessionId} History</h1>
                    </header>

                    {loadingChat ? (
                        <div className="flex-1 flex items-center justify-center text-slate-500">Loading transcript...</div>
                    ) : (
                        <div className="space-y-8 max-w-3xl mx-auto w-full pb-24">
                            {chatHistory.map((msg) => {
                                const sentiment = getSentimentStyles(msg.sentiment || "");
                                return (
                                    <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                                        <div className="max-w-[85%] relative">
                                            {/* Sentiment Badge - User Only */}
                                            {msg.role === 'user' && msg.sentiment && (
                                                <div className={`absolute -top-3.5 -right-2 px-2 py-0.5 rounded-full border shadow-lg flex items-center gap-1.5 z-20 font-bold text-[10px] tracking-tight backdrop-blur-md ${sentiment.color}`}>
                                                    {sentiment.icon}
                                                    <span>{sentiment.label}</span>
                                                </div>
                                            )}

                                            <div className={`p-4 rounded-2xl text-sm leading-relaxed ${
                                                msg.role === 'user' 
                                                ? "bg-blue-600 text-white rounded-tr-none shadow-[0_0_20px_rgba(37,99,235,0.2)]" 
                                                : "bg-slate-800 text-slate-200 rounded-tl-none border border-slate-700 shadow-xl"
                                            }`}>
                                                {msg.content}
                                            </div>
                                            
                                            <div className={`text-[10px] text-slate-500 mt-1.5 flex items-center gap-2 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                                                <span className="font-mono uppercase tracking-widest">{msg.role === 'user' ? 'Patient' : 'Avatar'}</span>
                                                {msg.role === 'user' && !msg.sentiment && <AlertCircle className="w-3 h-3 text-slate-700" title="No analysis available" />}
                                            </div>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    )}
                </div>
            )}
        </div>
      </main>
    </div>
  );
}
