"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { TranscriptViewer } from "../../../components/dashboard/TranscriptViewer";
import { sessionService } from "../../../services/sessionService";
import type { ChatMessage } from "../../../types/chat";
import { PageShell } from "../../../components/layout/PageShell";
import { he } from "../../../constants/he";

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
        setError(he.errors.loadSessionTranscriptFailed);
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
    return (
      <PageShell className="flex items-center justify-center">
        <div className="text-sm text-muted-foreground">{he.sessionDetail.invalidId}</div>
      </PageShell>
    );
  }

  return (
    <PageShell>
      <div className="container mx-auto max-w-5xl px-4 space-y-8">
        <header className="space-y-2">
          <h1 className="text-3xl font-heading font-bold text-foreground">{he.sessionDetail.titlePrefix}{sessionId}</h1>
          <p className="text-muted-foreground">{he.sessionDetail.subtitle}</p>
        </header>

        <div className="rounded-2xl border border-border bg-card p-6">
          <h2 className="text-lg font-heading font-semibold text-foreground">{he.sessionDetail.playbackTitle}</h2>
          <p className="text-sm text-muted-foreground">
            {he.sessionDetail.playbackSubtitle}
          </p>
        </div>

        {loading && (
          <div className="rounded-2xl border border-border bg-card p-6 text-muted-foreground">
            {he.sessionDetail.loadingTranscript}
          </div>
        )}

        {error && (
          <div className="rounded-2xl border border-destructive/20 bg-destructive/10 p-6 text-destructive">
            {error}
          </div>
        )}

        {!loading && !error && (
          <div className="space-y-3">
            <h2 className="text-lg font-heading font-semibold text-foreground">{he.sessionDetail.transcriptTitle}</h2>
            <TranscriptViewer text="" messages={messages} />
          </div>
        )}
      </div>
    </PageShell>
  );
}
