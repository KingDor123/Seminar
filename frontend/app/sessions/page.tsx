'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { 
  Zap, 
  MessageSquareWarning, 
  Smile, 
  Trophy, 
  LayoutDashboard,
  Activity,
  History
} from 'lucide-react';
import { MetricCard } from '../../components/dashboard/MetricCard';

// --- Interface Definition ---
interface DashboardStats {
  overview: {
    total_sessions: number;
    total_messages: number;
    avg_score: number;
  };
  sentiment: {
    Positive: number;
    Neutral: number;
    Negative: number;
  };
  recent_activity: Array<{
    id: number;
    scenario: string;
    date: string | null;
  }>;
}

// AI Service Base URL (Direct call as per instructions)
const AI_SERVICE_URL = "http://localhost:8000"; 

export default function SessionsPage() {
  const { user, isLoading: isAuthLoading } = useAuth();
  
  // State
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // --- Fetch Logic ---
  useEffect(() => {
    if (isAuthLoading || !user) return;

    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        // Direct fetch to AI Service
        const response = await fetch(`${AI_SERVICE_URL}/analytics/dashboard`);
        if (!response.ok) {
          throw new Error(`Failed to fetch analytics: ${response.statusText}`);
        }
        const data: DashboardStats = await response.json();
        setStats(data);
      } catch (err: any) {
        console.error("Dashboard Fetch Error:", err);
        setError(err.message || "An error occurred");
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, [user, isAuthLoading]);


  // --- Render ---

  if (isAuthLoading) return <div className="min-h-screen bg-slate-950 flex items-center justify-center text-slate-500">Initializing...</div>;
  if (!user) return <div className="min-h-screen bg-slate-950 flex items-center justify-center text-slate-500">Please log in to view analytics.</div>;

  return (
    <div className="flex h-screen w-full bg-slate-950 text-slate-100 font-sans overflow-y-auto overflow-x-hidden">
      
      {/* Background Gradients */}
      <div className="fixed top-0 left-0 w-full h-full pointer-events-none z-0">
          <div className="absolute top-[-10%] right-[-5%] w-[500px] h-[500px] bg-cyan-500/5 rounded-full blur-[128px]" />
          <div className="absolute bottom-[-10%] left-[20%] w-[400px] h-[400px] bg-blue-600/5 rounded-full blur-[128px]" />
      </div>

      <main className="flex-1 p-8 space-y-8 z-10 w-full max-w-7xl mx-auto">
        
        {/* Header */}
        <header className="flex justify-between items-end border-b border-slate-800/50 pb-6">
            <div>
                <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-3">
                    <LayoutDashboard className="h-8 w-8 text-cyan-400" />
                    Performance Dashboard
                </h1>
                <p className="text-slate-400 mt-2">
                    Real-time analytics from your AI training sessions.
                </p>
            </div>
        </header>

        {loading ? (
            <div className="flex h-64 items-center justify-center text-slate-500 animate-pulse">
                Loading Dashboard Data...
            </div>
        ) : error ? (
            <div className="p-4 bg-red-900/20 border border-red-800 rounded-lg text-red-200">
                Error: {error}
            </div>
        ) : stats ? (
            <>
                {/* 1. Overview Cards */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <MetricCard 
                        title="Total Sessions" 
                        value={stats.overview.total_sessions} 
                        unit="" 
                        icon={Activity} 
                        color="cyan"
                    />
                    <MetricCard 
                        title="Total Messages" 
                        value={stats.overview.total_messages} 
                        unit="" 
                        icon={MessageSquareWarning} 
                        color="blue"
                    />
                    <MetricCard 
                        title="Global Avg Score" 
                        value={stats.overview.avg_score} 
                        unit="/ 100" 
                        icon={Trophy} 
                        color="yellow"
                    />
                </div>

                {/* 2. Sentiment Breakdown */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    <div className="bg-slate-900/50 backdrop-blur-md rounded-2xl border border-slate-800 p-6">
                        <h3 className="text-lg font-semibold text-white mb-6 flex items-center gap-2">
                            <Smile className="h-5 w-5 text-purple-400" />
                            Sentiment Analysis
                        </h3>
                        <div className="space-y-4">
                            {/* Positive */}
                            <div>
                                <div className="flex justify-between text-sm mb-1">
                                    <span className="text-slate-300">Positive</span>
                                    <span className="text-green-400 font-mono">{stats.sentiment.Positive}</span>
                                </div>
                                <div className="w-full bg-slate-800 rounded-full h-2.5">
                                    <div 
                                        className="bg-green-500 h-2.5 rounded-full transition-all duration-1000" 
                                        style={{ width: `${(stats.sentiment.Positive / (stats.overview.total_messages || 1)) * 100}%` }}
                                    ></div>
                                </div>
                            </div>

                            {/* Neutral */}
                            <div>
                                <div className="flex justify-between text-sm mb-1">
                                    <span className="text-slate-300">Neutral</span>
                                    <span className="text-slate-400 font-mono">{stats.sentiment.Neutral}</span>
                                </div>
                                <div className="w-full bg-slate-800 rounded-full h-2.5">
                                    <div 
                                        className="bg-slate-500 h-2.5 rounded-full transition-all duration-1000" 
                                        style={{ width: `${(stats.sentiment.Neutral / (stats.overview.total_messages || 1)) * 100}%` }}
                                    ></div>
                                </div>
                            </div>

                            {/* Negative */}
                            <div>
                                <div className="flex justify-between text-sm mb-1">
                                    <span className="text-slate-300">Negative / Stress</span>
                                    <span className="text-red-400 font-mono">{stats.sentiment.Negative}</span>
                                </div>
                                <div className="w-full bg-slate-800 rounded-full h-2.5">
                                    <div 
                                        className="bg-red-500 h-2.5 rounded-full transition-all duration-1000" 
                                        style={{ width: `${(stats.sentiment.Negative / (stats.overview.total_messages || 1)) * 100}%` }}
                                    ></div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* 3. Recent Activity */}
                    <div className="bg-slate-900/50 backdrop-blur-md rounded-2xl border border-slate-800 p-6">
                        <h3 className="text-lg font-semibold text-white mb-6 flex items-center gap-2">
                            <History className="h-5 w-5 text-blue-400" />
                            Recent Sessions
                        </h3>
                        <div className="overflow-hidden">
                            <table className="min-w-full text-left text-sm whitespace-nowrap">
                                <thead className="uppercase tracking-wider border-b border-slate-700 bg-slate-800/30">
                                    <tr>
                                        <th scope="col" className="px-4 py-3 text-slate-400">ID</th>
                                        <th scope="col" className="px-4 py-3 text-slate-400">Scenario</th>
                                        <th scope="col" className="px-4 py-3 text-slate-400 text-right">Date</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-700">
                                    {stats.recent_activity.map((session) => (
                                        <tr key={session.id} className="hover:bg-slate-800/50 transition-colors">
                                            <td className="px-4 py-3 font-mono text-cyan-400">#{session.id}</td>
                                            <td className="px-4 py-3 text-white capitalize">{session.scenario}</td>
                                            <td className="px-4 py-3 text-slate-400 text-right">
                                                {session.date ? new Date(session.date).toLocaleDateString() : "N/A"}
                                            </td>
                                        </tr>
                                    ))}
                                    {stats.recent_activity.length === 0 && (
                                        <tr>
                                            <td colSpan={3} className="px-4 py-8 text-center text-slate-500">
                                                No recent activity found.
                                            </td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </>
        ) : null}

      </main>
    </div>
  );
}