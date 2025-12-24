'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { sessionService } from '../../services/sessionService';
import { SessionSidebar } from '../../components/dashboard/SessionSidebar';
import { MetricCard } from '../../components/dashboard/MetricCard';
import { AnalysisRadar } from '../../components/dashboard/RadarChart';
import { TranscriptViewer } from '../../components/dashboard/TranscriptViewer';
import { SessionData, RadarData } from '../../utils/mockData'; // Import types
import { 
  Zap, 
  MessageSquareWarning, 
  Smile, 
  Trophy, 
  LayoutDashboard
} from 'lucide-react';

export default function SessionsPage() {
  const { user, isLoading: isAuthLoading } = useAuth();
  
  // State
  const [sessions, setSessions] = useState<any[]>([]); // Raw sessions
  const [selectedId, setSelectedId] = useState<number | null>(null);
  
  // Detail State
  const [activeData, setActiveData] = useState<SessionData | null>(null);
  const [loadingDetails, setLoadingDetails] = useState(false);

  // 1. Fetch Session List
  useEffect(() => {
    if (!user) return;
    const fetchList = async () => {
      try {
        const list = await sessionService.getUserSessions(user.id);
        // Sort by newest
        list.sort((a, b) => new Date(b.start_time).getTime() - new Date(a.start_time).getTime());
        setSessions(list);
        if (list.length > 0 && !selectedId) setSelectedId(list[0].id);
      } catch (e) {
        console.error("List Fetch Error", e);
      }
    };
    fetchList();
  }, [user]);

  // 2. Fetch Details when Selection Changes
  useEffect(() => {
    if (!selectedId) return;
    
    const fetchDetails = async () => {
      setLoadingDetails(true);
      try {
        const [messages, metrics] = await Promise.all([
            sessionService.getSessionMessages(selectedId),
            sessionService.getSessionMetrics(selectedId)
        ]);

        // --- Data Adapter ---
        
        // A. Transcript
        const transcript = messages
            .map(m => `${m.role === 'ai' ? 'AI' : 'You'}: ${m.content}`)
            .join('\n\n');

        // B. Metrics Aggregation
        let totalWpm = 0, wpmCount = 0;
        let totalSentiment = 0, sentimentCount = 0;
        let totalFillers = 0;

        metrics.forEach(m => {
            if (m.metric_name === 'speech_rate_wpm') {
                totalWpm += Number(m.metric_value);
                wpmCount++;
            }
            if (m.metric_name === 'sentiment') {
                totalSentiment += Number(m.metric_value);
                sentimentCount++;
            }
            if (m.metric_name === 'filler_word_count') {
                totalFillers += Number(m.metric_value);
            }
        });

        const avgWpm = wpmCount > 0 ? Math.round(totalWpm / wpmCount) : 0;
        const avgSentiment = sentimentCount > 0 ? (totalSentiment / sentimentCount) : 0;
        
        // Score Calculation (Simple heuristic)
        // Base 60 + points for WPM (target 120) - penalty for fillers
        let score = 60;
        score += Math.min(20, (avgWpm / 120) * 20); // Up to 20 pts for speed
        score -= (totalFillers * 2); // -2 per filler
        score += ((avgSentiment + 1) * 10); // Sentiment bonus
        score = Math.max(0, Math.min(100, Math.round(score)));

        // C. Chart Data
        const chartData: RadarData[] = [
            { subject: 'Fluency', A: avgWpm, fullMark: 160 },
            { subject: 'Clarity', A: Math.max(0, 100 - (totalFillers * 5)), fullMark: 100 },
            { subject: 'Confidence', A: (avgSentiment + 1) * 50, fullMark: 100 },
            { subject: 'Empathy', A: 75, fullMark: 100 }, // Placeholder for now
            { subject: 'Relevance', A: 80, fullMark: 100 }, // Placeholder
        ];

        // Construct View Model
        const rawSession = sessions.find(s => s.id === selectedId);
        const viewData: SessionData = {
            id: selectedId,
            date: rawSession?.start_time || new Date().toISOString(),
            scenario: rawSession?.scenario_id || "Unknown",
            transcript: transcript || "(No conversation data)",
            stats: {
                wpm: avgWpm,
                fillers: totalFillers,
                sentiment: avgSentiment,
                score: score
            },
            chartData: chartData
        };

        setActiveData(viewData);

      } catch (e) {
        console.error("Detail Fetch Error", e);
      } finally {
        setLoadingDetails(false);
      }
    };

    fetchDetails();
  }, [selectedId, sessions]);


  // --- Render ---

  if (isAuthLoading) return <div className="min-h-screen bg-slate-950 flex items-center justify-center text-slate-500">Initializing...</div>;
  if (!user) return <div className="min-h-screen bg-slate-950 flex items-center justify-center text-slate-500">Please log in.</div>;

  // Transform raw sessions for sidebar
  const sidebarData: SessionData[] = sessions.map(s => ({
      id: s.id,
      date: s.start_time,
      scenario: s.scenario_id,
      // Mock stats for list view (since we only fetch details on select)
      stats: { wpm: 0, fillers: 0, sentiment: 0, score: 0 }, 
      transcript: "",
      chartData: []
  }));

  return (
    <div className="flex h-screen w-full bg-slate-950 text-slate-100 font-sans overflow-hidden selection:bg-cyan-500/30">
      
      {/* LEFT: Sidebar History */}
      <div className="w-80 flex-shrink-0 z-20 shadow-2xl">
        <SessionSidebar 
          sessions={sidebarData} 
          selectedId={selectedId} 
          onSelect={setSelectedId} 
        />
      </div>

      {/* RIGHT: Detail View */}
      <div className="flex-1 flex flex-col h-full relative overflow-y-auto overflow-x-hidden">
        
        {/* Background Gradients */}
        <div className="fixed top-0 left-0 w-full h-full pointer-events-none z-0">
            <div className="absolute top-[-10%] right-[-5%] w-[500px] h-[500px] bg-cyan-500/5 rounded-full blur-[128px]" />
            <div className="absolute bottom-[-10%] left-[20%] w-[400px] h-[400px] bg-blue-600/5 rounded-full blur-[128px]" />
        </div>

        {activeData && !loadingDetails ? (
            <>
                {/* Header */}
                <header className="flex-shrink-0 px-8 py-6 z-10 backdrop-blur-sm sticky top-0 border-b border-slate-800/50">
                <div className="flex justify-between items-end">
                    <div>
                    <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-3">
                        <LayoutDashboard className="h-6 w-6 text-cyan-400" />
                        {activeData.scenario}
                    </h1>
                    <p className="text-slate-400 text-sm mt-1 font-mono">
                        SESSION ID: #{activeData.id} • {new Date(activeData.date).toLocaleString()}
                    </p>
                    </div>
                    <div className="text-right">
                    <span className="text-xs font-bold uppercase tracking-widest text-slate-500 block mb-1">Overall Score</span>
                    <span className="text-4xl font-black text-transparent bg-clip-text bg-gradient-to-br from-cyan-300 to-blue-500">
                        {activeData.stats.score}
                    </span>
                    </div>
                </div>
                </header>

                {/* Content Scrollable Area */}
                <main className="flex-1 p-8 space-y-8 z-10">
                
                {/* Top Row: Metrics */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    <MetricCard 
                    title="Fluency" 
                    value={activeData.stats.wpm} 
                    unit="WPM" 
                    icon={Zap} 
                    color="cyan"
                    />
                    <MetricCard 
                    title="Clarity Issues" 
                    value={activeData.stats.fillers} 
                    unit="Detected" 
                    icon={MessageSquareWarning} 
                    color={activeData.stats.fillers > 5 ? 'red' : 'green'}
                    />
                    <MetricCard 
                    title="Confidence" 
                    value={(activeData.stats.sentiment * 100).toFixed(0)} 
                    unit="%" 
                    icon={Smile} 
                    color="blue"
                    />
                    <MetricCard 
                    title="Impact" 
                    value={activeData.stats.score} 
                    unit="/ 100" 
                    icon={Trophy} 
                    color="yellow"
                    />
                </div>

                {/* Middle Row: Radar + Transcript */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 h-[400px]">
                    {/* Chart */}
                    <div className="lg:col-span-1 bg-slate-900/50 backdrop-blur-md rounded-2xl border border-slate-800 p-4 flex flex-col items-center justify-center">
                    <h3 className="text-xs font-bold uppercase tracking-widest text-slate-500 mb-4 w-full text-left">Skill Matrix</h3>
                    <AnalysisRadar data={activeData.chartData} />
                    </div>

                    {/* Transcript */}
                    <div className="lg:col-span-2 h-full">
                    <TranscriptViewer text={activeData.transcript} />
                    </div>
                </div>

                </main>
            </>
        ) : (
            <div className="flex-1 flex items-center justify-center text-slate-500 z-10">
                {sessions.length === 0 ? "No sessions found." : "Loading Session Data..."}
            </div>
        )}
      </div>
    </div>
  );
}
