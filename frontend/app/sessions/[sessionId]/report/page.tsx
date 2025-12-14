'use client';

import { useEffect, useState } from 'react';

import { useParams } from 'next/navigation';

import { analyticsApi } from '../../../../lib/analyticsApi';

import EmotionalArcChart, { ChartDataPoint } from './EmotionalArcChart';

import AICoachSummary from './AICoachSummary';

// Defined locally to avoid importing from backend during build
interface SessionMetric {
  id: number;
  session_id: number;
  metric_name: string;
  metric_value: number;
  context?: string;
  created_at: string; 
}

export default function SessionReportPage() {

  const params = useParams();

  const sessionId = params.sessionId ? parseInt(params.sessionId as string) : null;



  const [metrics, setMetrics] = useState<SessionMetric[]>([]);

  const [chartData, setChartData] = useState<ChartDataPoint[]>([]); // State to hold transformed data for AI Coach

  const [loading, setLoading] = useState(true);

  const [error, setError] = useState<string | null>(null);



  useEffect(() => {

    if (sessionId) {

      const fetchMetrics = async () => {

        try {

          setLoading(true);

          const data = await analyticsApi.getMetricsForSession(sessionId);

          setMetrics(data);

        } catch (err: any) {

          console.error("Failed to fetch session metrics:", err);

          setError(err.response?.data?.message || "Failed to load metrics.");

        } finally {

          setLoading(false);

        }

      };

      fetchMetrics();

    }

  }, [sessionId]);



  if (!sessionId) {

    return <div className="text-center py-8">Invalid Session ID provided.</div>;

  }



  if (loading) {

    return <div className="text-center py-8">Loading session report...</div>;

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



        {metrics.length > 0 && (

            <EmotionalArcChart 

                metrics={metrics as any} // Cast to any or matching type if needed, but structure matches

                onDataTransformed={setChartData} // Receive processed data

            />

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
