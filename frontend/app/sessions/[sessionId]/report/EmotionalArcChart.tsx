"use client";

import { useMemo, useState, useEffect } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Legend,
  Brush,
  ReferenceArea,
  Label
} from 'recharts';

interface RawMetric {
  id: number;
  session_id: number;
  metric_name: string;
  metric_value: number;
  context: string; // e.g., "Analyzed user text: 'Hello'"
  created_at: string;
}

export interface ChartDataPoint {
  turn: number;
  sentiment: number;
  topic_adherence: number;
  clarity: number;
  latency: number;
  context: string;
}

interface EmotionalArcChartProps {
  metrics: RawMetric[];
  onDataTransformed?: (data: ChartDataPoint[]) => void;
}

export default function EmotionalArcChart({ metrics, onDataTransformed }: EmotionalArcChartProps) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const chartData = useMemo(() => {
    if (!metrics || metrics.length === 0) return [];
    
    console.log("Processing metrics for chart:", metrics.length);

    // 1. Group metrics by their approximate timestamp or "context" to bundle them into "turns"
    const turnsMap = new Map<string, Partial<ChartDataPoint>>();
    let turnCounter = 0;

    // Sort by time first to ensure order
    const sortedMetrics = [...metrics].sort((a, b) => 
      new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
    );

    sortedMetrics.forEach((m) => {
      // Create a unique key for the "turn" based on the user text context
      // Fallback to timestamp if context is missing
      const key = m.context || m.created_at;

      if (!turnsMap.has(key)) {
        turnCounter++;
        turnsMap.set(key, { 
          turn: turnCounter,
          context: m.context ? m.context.replace("Analyzed user text: ", "").replace("User responded after AI message:", "User Reply: ") : "Unknown"
        });
      }

      const entry = turnsMap.get(key)!;
      const name = m.metric_name.toLowerCase().trim();

      // Assign values based on metric name (Case insensitive check)
      if (name === 'sentiment') entry.sentiment = m.metric_value;
      if (name === 'topic_adherence' || name === 'topic adherence') entry.topic_adherence = m.metric_value;
      if (name === 'clarity') entry.clarity = m.metric_value;
      if (name === 'response_latency' || name === 'latency') entry.latency = m.metric_value;
    });

    const finalData = Array.from(turnsMap.values()).map(entry => ({
        turn: entry.turn || 0,
        context: entry.context || "",
        sentiment: entry.sentiment ?? 0,
        topic_adherence: entry.topic_adherence ?? 0,
        clarity: entry.clarity ?? 0,
        latency: entry.latency ?? 0
    })) as ChartDataPoint[];
    
    console.log("Generated chart data points:", finalData.length);
    return finalData;
  }, [metrics]);

  // Sync data to parent via Effect, not Memo (Avoids side-effects during render)
  useEffect(() => {
    if (onDataTransformed && chartData.length > 0) {
        onDataTransformed(chartData);
    }
  }, [chartData, onDataTransformed]);

  if (!mounted) return <div className="h-[500px] w-full bg-gray-100 dark:bg-gray-800 animate-pulse rounded-xl" />;

  if (chartData.length === 0) {
    return (
        <div className="h-64 flex items-center justify-center border-2 border-dashed border-gray-300 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-800/50">
            <p className="text-gray-500 dark:text-gray-400">Not enough data to generate chart. (Metrics: {metrics?.length || 0})</p>
        </div>
    );
  }

  const gradIdSuffix = Math.random().toString(36).substr(2, 5);
  const sentimentGradId = `sentimentGradient-${gradIdSuffix}`;
  const focusGradId = `focusGradient-${gradIdSuffix}`;

  return (
    <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-lg border border-gray-100 dark:border-gray-700 space-y-6">
      <div className="flex justify-between items-center border-b border-gray-100 dark:border-gray-700 pb-4">
        <div>
          <h3 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <span>📈</span> Emotional & Focus Arc
          </h3>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Visualizing the emotional journey and conversation quality.
          </p>
        </div>
        <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-gradient-to-r from-red-500 to-green-500"></span>
                <span className="text-xs font-medium text-gray-600 dark:text-gray-300">Sentiment</span>
            </div>
            <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-cyan-500"></span>
                <span className="text-xs font-medium text-gray-600 dark:text-gray-300">Focus</span>
            </div>
             <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-purple-500"></span>
                <span className="text-xs font-medium text-gray-600 dark:text-gray-300">Clarity</span>
            </div>
        </div>
      </div>
      
      <div className="flex justify-center overflow-x-auto w-full border border-gray-100 dark:border-gray-700 rounded-lg bg-gray-50/50 dark:bg-gray-900/50 p-4">
            <LineChart
              width={1000}
              height={500}
              data={chartData}
              margin={{ top: 20, right: 30, left: 20, bottom: 40 }}
            >
              <defs>
                <linearGradient id={sentimentGradId} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#22c55e" stopOpacity={1}/>
                  <stop offset="95%" stopColor="#ef4444" stopOpacity={1}/>
                </linearGradient>
                <linearGradient id={focusGradId} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="#06b6d4" stopOpacity={0}/>
                </linearGradient>
              </defs>

              <CartesianGrid strokeDasharray="3 3" opacity={0.1} vertical={false} stroke="#9ca3af" />
              
              <XAxis 
                  dataKey="turn" 
                  tick={{ fill: '#9ca3af', fontSize: 12 }}
                  axisLine={{ stroke: '#4b5563', opacity: 0.3 }}
                  tickLine={{ stroke: '#4b5563', opacity: 0.3 }}
                  height={60}
                  // Removed 'type="number"' and domain to let Recharts handle category auto-scaling which is safer for mixed data
              >
                 <Label 
                    value="Conversation Progression (Turn #)" 
                    offset={0} 
                    position="insideBottom" 
                    fill="#9ca3af" 
                    fontSize={12} 
                    dy={10} 
                 />
              </XAxis>
              
              <YAxis 
                  domain={[-1.2, 1.2]} 
                  ticks={[-1, -0.5, 0, 0.5, 1]}
                  tick={{ fill: '#9ca3af', fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                  width={80}
                  tickFormatter={(value) => {
                      if (value === 1) return 'High (+1)';
                      if (value === 0) return 'Neutral (0)';
                      if (value === -1) return 'Low (-1)';
                      return value;
                  }}
              >
                  <Label 
                    value="Score / Intensity" 
                    angle={-90} 
                    position="insideLeft" 
                    style={{ textAnchor: 'middle' }} 
                    fill="#6b7280" 
                    fontSize={13} 
                    fontWeight="bold"
                  />
              </YAxis>

              <Tooltip 
                  contentStyle={{ 
                      backgroundColor: 'rgba(17, 24, 39, 0.85)', 
                      backdropFilter: 'blur(8px)',
                      color: '#f3f4f6', 
                      borderRadius: '12px', 
                      border: '1px solid rgba(255,255,255,0.1)',
                      boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.5)' 
                  }}
                  itemStyle={{ fontSize: '0.85rem', padding: '2px 0' }}
                  labelStyle={{ fontWeight: 'bold', color: '#fbbf24', marginBottom: '8px', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '4px' }}
                  formatter={(value: number, name: string) => {
                      const formatted = value.toFixed(2);
                      if (name === 'sentiment') return [formatted, 'Sentiment'];
                      if (name === 'topic_adherence') return [formatted, 'Topic Focus'];
                      if (name === 'clarity') return [formatted, 'Clarity'];
                      return [formatted, name];
                  }}
                  labelFormatter={(label, payload) => {
                    if (payload && payload.length > 0) {
                        const context = payload[0].payload.context;
                        return `Turn ${label}: "${context.length > 60 ? context.substring(0, 60) + '...' : context}"`;
                    }
                    return `Turn ${label}`;
                  }}
              />
              
              <Legend verticalAlign="top" height={36} iconType="circle" />

              <ReferenceArea y1={0} y2={1.2} fill="#22c55e" fillOpacity={0.03} />
              <ReferenceArea y1={-1.2} y2={0} fill="#ef4444" fillOpacity={0.03} />
              <ReferenceLine y={0} stroke="#6b7280" strokeDasharray="3 3" opacity={0.5} />
              
              <Line
                type="monotone"
                dataKey="sentiment"
                stroke={`url(#${sentimentGradId})`}
                name="Sentiment"
                strokeWidth={3}
                dot={{ r: 4, strokeWidth: 2, fill: '#fff', stroke: '#888' }} 
                activeDot={{ r: 7, strokeWidth: 0, fill: '#fbbf24' }}
                animationDuration={1500}
                animationEasing="ease-in-out"
              />

              <Line
                type="monotone"
                dataKey="topic_adherence"
                stroke="#06b6d4" 
                name="Topic Focus"
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 6, fill: '#06b6d4' }}
                strokeDasharray="5 5" 
                animationDuration={1500}
                animationEasing="ease-in-out"
                animationBegin={300} 
              />

               <Line
                type="monotone"
                dataKey="clarity"
                stroke="#a855f7"
                name="Speech Clarity"
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 6, fill: '#a855f7' }}
                strokeDasharray="3 3"
                animationDuration={1500}
                animationEasing="ease-in-out"
                animationBegin={600} 
              />

              {/* Restored Brush for zooming */}
              <Brush 
                  dataKey="turn" 
                  height={30} 
                  stroke="#4b5563"
                  fill="rgba(31, 41, 55, 0.05)"
                  tickFormatter={() => ""}
                  travellerWidth={10}
              />

            </LineChart>
      </div>
      
      <p className="text-xs text-center text-gray-500 italic">
        Tip: Drag the slider at the bottom to zoom into specific parts of the conversation.
      </p>
    </div>
  );
}