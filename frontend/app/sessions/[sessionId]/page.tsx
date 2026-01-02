"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { TranscriptViewer } from "../../../../components/dashboard/TranscriptViewer";
import { sessionService } from "../../../../services/sessionService";
import type { ChatMessage } from "../../../../types/chat";

export default function SessionDetailPage() {
  const params = useParams();
  const sessionId = params.sessionId ? Number(params.sessionId) : null;

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!sessionId) return;
    let isActive = true;

    const loadMessages = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await sessionService.getSessionMessages(sessionId);
        if (!isActive) return;
        setMessages(data);
      } catch (err) {
        console.error("Failed to load session messages:", err);
        if (!isActive) return;
        setError("Unable to load session transcript.");
      } finally {
        if (isActive) setLoading(false);
      }
    };

    loadMessages();
    return () => {
      isActive = false;
    };
  }, [sessionId]);

  if (!sessionId) {
    return <div className="text-center py-8 text-slate-500">Invalid Session ID provided.</div>;
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <div className="max-w-5xl mx-auto px-6 py-10 space-y-8">
        <header className="space-y-2">
          <h1 className="text-3xl font-bold">Session #{sessionId}</h1>
          <p className="text-slate-400">Review the full transcript with sentiment markers.</p>
        </header>

        <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6">
          <h2 className="text-lg font-semibold text-white">Session Playback</h2>
          <p className="text-sm text-slate-400">
            Transcript and analysis are available below.
          </p>
        </div>

        {loading && (
          <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6 text-slate-400">
            Loading transcript...
          </div>
        )}

        {error && (
          <div className="rounded-2xl border border-rose-500/40 bg-rose-500/10 p-6 text-rose-200">
            {error}
          </div>
        )}

        {!loading && !error && (
          <div className="space-y-3">
            <h2 className="text-lg font-semibold text-white">Transcript</h2>
            <TranscriptViewer text="" messages={messages} />
          </div>
        )}
      </div>
    </div>
  );
}
