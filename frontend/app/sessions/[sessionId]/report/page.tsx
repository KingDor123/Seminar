"use client";

import { useEffect, useState, useMemo } from 'react';
import { useParams } from 'next/navigation';
import dynamic from 'next/dynamic';
import { analyticsApi } from '../../../../lib/analyticsApi';
import AICoachSummary from './AICoachSummary';
import { processMetricsToChartData } from '../../../../utils/chartHelpers';
import { RawMetric } from './EmotionalArcChart';

const EmotionalArcChart = dynamic(
  () => import('./EmotionalArcChart'),
  { 
    ssr: false,
    loading: () => <div className="h-[500px] w-full bg-gray-100 dark:bg-gray-800 animate-pulse rounded-xl" />
  }
);

export default function SessionReportPage() {
  const params = useParams();
  const sessionId = params.sessionId ? parseInt(params.sessionId as string) : null;

  const [metrics, setMetrics] = useState<RawMetric[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Process data immediately when metrics change
  // This removes the need for the child component to "transform and callback"
  const chartData = useMemo(() => {
      return processMetricsToChartData(metrics);
  }, [metrics]);

  useEffect(() => {
    if (sessionId) {
      const fetchAndAnalyze = async () => {
        try {
          setLoading(true);
          let data = await analyticsApi.getMetricsForSession(sessionId);
          
          // Check if we have semantic metrics (e.g. sentiment)
          // If not, trigger generation (Optimized Option C)
          // We check for 'sentiment' which is produced by the Deep Analysis
          const hasSentiment = data.some((m: any) => m.metric_name === 'sentiment');
          
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
          const errorMessage = err instanceof Error ? err.message : "Failed to load metrics.";
          // @ts-expect-error - axios error structure
          const responseMessage = err?.response?.data?.message;
          setError(responseMessage || errorMessage);
        } finally {
          setLoading(false);
        }
      };
      fetchAndAnalyze();
    }
  }, [sessionId]);

  if (!sessionId) {
    return <div className="text-center py-8">Invalid Session ID provided.</div>;
  }

  if (loading || generating) {
    return (
        <div className="flex flex-col h-screen items-center justify-center bg-gray-50 dark:bg-gray-900 space-y-4">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
            <p className="text-lg text-gray-700 dark:text-gray-300">
                {generating ? "AI is analyzing your session conversation..." : "Loading session report..."}
            </p>
            {generating && <p className="text-sm text-gray-500">This may take a minute for long sessions.</p>}
        </div>
    );
  }

  if (error) {
    return <div className="text-center py-8 text-red-600">Error: {error}</div>;
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8 dark:bg-gray-900 text-gray-900 dark:text-white">
      <div className="max-w-4xl mx-auto space-y-8">
        <h2 className="text-3xl font-extrabold text-center">Session Report (ID: {sessionId})</h2>
        
        {/* AI Coach Summary Section */}
        {chartData.length > 0 && <AICoachSummary data={chartData} />}

        {/* Emotional Arc Chart - Now purely presentational */}
        {metrics.length > 0 && (
            <EmotionalArcChart data={chartData} />
        )}

        {metrics.length === 0 ? (
          <p className="text-center text-gray-600 dark:text-gray-400">No metrics available for this session yet.</p>
        ) : (
          <div className="bg-white shadow overflow-hidden sm:rounded-lg dark:bg-gray-800">
            <div className="px-4 py-5 sm:px-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900 dark:text-white">Detailed Metrics Log</h3>
            </div>
            <div className="border-t border-gray-200 dark:border-gray-700">
              <dl>
                {metrics.map((metric, index) => (
                  <div key={metric.id} className={`${index % 2 === 0 ? 'bg-gray-50 dark:bg-gray-700' : 'bg-white dark:bg-gray-800'} px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6`}>
                    <dt className="text-sm font-medium text-gray-500 dark:text-gray-300">{metric.metric_name}</dt>
                    <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2 dark:text-white">
                      {typeof metric.metric_value === 'number' ? metric.metric_value.toFixed(2) : metric.metric_value} 
                      {metric.metric_name === 'response_latency' && ' seconds'}
                      {metric.context && (
                          <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">Context: {metric.context}</p>
                      )}
                      <p className="text-xs text-gray-400 dark:text-gray-500">Recorded at: {new Date(metric.created_at).toLocaleString()}</p>
                    </dd>
                  </div>
                ))}
              </dl>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
