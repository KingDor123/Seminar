"use client";

import { useEffect, useState, useMemo } from 'react';
import { useParams } from 'next/navigation';
import dynamic from 'next/dynamic';
import { analyticsApi } from '../../../../lib/analyticsApi';
import { sessionService } from '../../../../services/sessionService';
import { TranscriptViewer } from '../../../../components/dashboard/TranscriptViewer';
import AICoachSummary from './AICoachSummary';
import { processMetricsToChartData } from '../../../../utils/chartHelpers';
import { RawMetric } from './EmotionalArcChart';
import type { ChatMessage } from '../../../../types/chat';
import { PageShell } from '../../../../components/layout/PageShell';
import { ensureHebrew, he } from '../../../../constants/he';

const EmotionalArcChart = dynamic(
  () => import('./EmotionalArcChart'),
  { 
    ssr: false,
    loading: () => <div className="h-[500px] w-full bg-muted/50 animate-pulse rounded-2xl" />
  }
);

export default function SessionReportPage() {
  const params = useParams();
  const sessionId = params.sessionId ? parseInt(params.sessionId as string) : null;

  const [metrics, setMetrics] = useState<RawMetric[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Process data immediately when metrics change
  // This removes the need for the child component to "transform and callback"
  const chartData = useMemo(() => {
      return processMetricsToChartData(metrics);
  }, [metrics]);

  const formatMetricValue = (metric: RawMetric) => {
    if (typeof metric.metric_value === "number") return metric.metric_value.toFixed(2);
    if (typeof metric.metric_value === "string") {
      const normalized = metric.metric_value.toLowerCase();
      if (normalized.includes("positive") || normalized.includes("joy")) return he.sentiments.positive;
      if (normalized.includes("negative") || normalized.includes("anger") || normalized.includes("fear")) return he.sentiments.negative;
      if (normalized.includes("neutral")) return he.sentiments.neutral;
      if (normalized.includes("sadness")) return he.sentiments.sadness;
      return ensureHebrew(metric.metric_value, he.report.unknownMetric);
    }
    return String(metric.metric_value);
  };

  useEffect(() => {
    if (sessionId) {
      const fetchAndAnalyze = async () => {
        try {
          setLoading(true);
          const [metricsData, sessionMessages] = await Promise.all([
            analyticsApi.getMetricsForSession(sessionId),
            sessionService.getSessionMessages(Number(sessionId))
          ]);
          let data = metricsData as RawMetric[];
          setMessages(sessionMessages);
          
          // Check if we have semantic metrics (e.g. sentiment)
          // If not, trigger generation (Optimized Option C)
          // We check for 'sentiment' which is produced by the Deep Analysis
          const hasSentiment = data.some((m) => m.metric_name === 'sentiment');
          
          if (!hasSentiment && data.length > 0) { // Only generate if we have SOME data (audio metrics) but missing deep metrics
              console.log("Missing semantic metrics. Triggering auto-generation...");
              setGenerating(true);
              try {
                  await analyticsApi.generateSessionReport(sessionId);
                  // Refetch after generation
                  data = await analyticsApi.getMetricsForSession(sessionId);
              } catch (genErr) {
                  console.error("Auto-generation failed:", genErr);
                  // We continue with partial data rather than crashing
              } finally {
                  setGenerating(false);
              }
          } else if (data.length === 0) {
              // If completely empty, try generating anyway (maybe audio failed but we have text?)
               console.log("No metrics found. Triggering auto-generation...");
               setGenerating(true);
               try {
                   await analyticsApi.generateSessionReport(sessionId);
                   data = await analyticsApi.getMetricsForSession(sessionId);
               } catch (genErr) {
                   console.error("Auto-generation failed:", genErr);
               } finally {
                   setGenerating(false);
               }
          }

          setMetrics(data);
        } catch (err: unknown) {
          console.error("Failed to fetch session metrics:", err);
          const errorMessage = err instanceof Error ? err.message : he.errors.loadMetricsFailed;
          // @ts-expect-error - axios error structure
          const responseMessage = err?.response?.data?.message;
          setError(ensureHebrew(responseMessage || errorMessage, he.errors.loadMetricsFailed));
        } finally {
          setLoading(false);
        }
      };
      fetchAndAnalyze();
    }
  }, [sessionId]);

  if (!sessionId) {
    return (
      <PageShell className="flex items-center justify-center">
        <div className="text-sm text-muted-foreground">{he.report.invalidId}</div>
      </PageShell>
    );
  }

  if (loading || generating) {
    return (
      <PageShell className="flex items-center justify-center">
        <div className="flex flex-col items-center space-y-3 text-muted-foreground">
          <div className="h-12 w-12 animate-spin rounded-full border-4 border-muted border-t-primary"></div>
          <p className="text-lg text-foreground">
            {generating ? he.report.analyzing : he.report.loading}
          </p>
          {generating && <p className="text-sm text-muted-foreground">{he.report.longSessionNote}</p>}
        </div>
      </PageShell>
    );
  }

  if (error) {
    return (
      <PageShell className="flex items-center justify-center">
        <div className="text-sm text-destructive">{he.report.errorPrefix}: {error}</div>
      </PageShell>
    );
  }

  return (
    <PageShell>
      <div className="container mx-auto max-w-4xl px-4 space-y-8">
        <h2 className="text-3xl font-heading font-bold text-center text-foreground">
          {he.report.title} ({he.report.idLabel}: {sessionId})
        </h2>
        
        {/* AI Coach Summary Section */}
        {chartData.length > 0 && <AICoachSummary data={chartData} />}

        {/* Emotional Arc Chart - Now purely presentational */}
        {metrics.length > 0 && (
            <EmotionalArcChart data={chartData} />
        )}

        {metrics.length === 0 ? (
          <p className="text-center text-muted-foreground">{he.report.noMetrics}</p>
        ) : (
          <div className="overflow-hidden rounded-2xl border border-border bg-card">
            <div className="px-6 py-5">
              <h3 className="text-lg font-heading font-semibold text-foreground">{he.report.detailedMetrics}</h3>
            </div>
            <div className="border-t border-border">
              <dl>
                {metrics.map((metric, index) => (
                  <div
                    key={metric.id}
                    className={`${index % 2 === 0 ? 'bg-muted/30' : 'bg-card'} px-6 py-5 sm:grid sm:grid-cols-3 sm:gap-4`}
                  >
                    <dt className="text-sm font-medium text-muted-foreground">
                      {(() => {
                        const normalized = metric.metric_name.toLowerCase();
                        if (normalized === "sentiment") return he.metrics.sentiment;
                        if (normalized === "topic_adherence" || normalized === "topic adherence") return he.metrics.topicAdherence;
                        if (normalized === "clarity") return he.metrics.clarity;
                        if (normalized === "response_latency" || normalized === "latency") return he.metrics.responseLatency;
                        return he.report.unknownMetric;
                      })()}
                    </dt>
                    <dd className="mt-1 text-sm text-foreground sm:mt-0 sm:col-span-2">
                      {formatMetricValue(metric)}
                      {metric.metric_name === 'response_latency' && ` ${he.report.secondsLabel}`}
                      {metric.context && (
                        <p className="text-xs text-muted-foreground mt-1">{he.report.contextLabel}: {metric.context}</p>
                      )}
                      <p className="text-xs text-muted-foreground">
                        {he.report.recordedAtLabel}: {new Date(metric.created_at).toLocaleString("he-IL")}
                      </p>
                    </dd>
                  </div>
                ))}
              </dl>
            </div>
          </div>
        )}

        <div className="overflow-hidden rounded-2xl border border-border bg-card">
          <div className="px-6 py-5">
            <h3 className="text-lg font-heading font-semibold text-foreground">{he.report.transcriptTitle}</h3>
          </div>
          <div className="border-t border-border">
            <TranscriptViewer text="" messages={messages} />
          </div>
        </div>
      </div>
    </PageShell>
  );
}
