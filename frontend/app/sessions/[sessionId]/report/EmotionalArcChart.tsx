"use client";

import { useId } from 'react';
import {
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  Brush
} from 'recharts';

export interface RawMetric {
  id: number;
  session_id: number;
  metric_name: string;
  metric_value: number;
  context?: string;
  created_at: string;
}

export interface ChartDataPoint {
  turn: string;
  sentiment: number;
  topic_adherence: number;
  clarity: number;
  latency: number;
  context: string;
}

interface EmotionalArcChartProps {
  data: ChartDataPoint[];
}

export default function EmotionalArcChart({ data }: EmotionalArcChartProps) {
  // Generate a unique ID for SVG gradients to prevent hydration mismatch
  const rawId = useId();
  const safeId = rawId.replace(/:/g, "");
  const gradientId = `sentiment-gradient-${safeId}`;

  // DEBUG OVERLAY
  if (true) { 
      console.log("Chart Data:", data);
  }

  if (!data || data.length === 0) {
    return (
      <div className="h-[500px] flex flex-col items-center justify-center border-2 border-dashed border-gray-200 dark:border-gray-800 rounded-xl bg-gray-50/50 dark:bg-gray-900/50">
        <div className="text-4xl mb-4">📊</div>
        <p className="text-gray-500 dark:text-gray-400 font-medium">No session data available yet.</p>
        <p className="text-sm text-gray-400 dark:text-gray-500 mt-1">Start a conversation to see your emotional arc.</p>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-900 p-6 rounded-2xl shadow-xl border border-gray-100 dark:border-gray-800 transition-all hover:shadow-2xl">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-8 gap-4">
        <div>
          <h3 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
            Emotional Resonance Arc
          </h3>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Real-time analysis of sentiment, focus, and clarity throughout the session.
          </p>
        </div>
        
        {/* Custom Legend */}
        <div className="flex flex-wrap gap-4 text-xs font-medium bg-gray-50 dark:bg-gray-800 p-2 rounded-lg border border-gray-100 dark:border-gray-700">
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-gradient-to-r from-emerald-400 to-rose-500 shadow-sm"></span>
            <span className="text-gray-700 dark:text-gray-200">Sentiment (Area)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-cyan-500 shadow-sm"></span>
            <span className="text-gray-700 dark:text-gray-200">Focus</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-purple-500 shadow-sm"></span>
            <span className="text-gray-700 dark:text-gray-200">Clarity</span>
          </div>
        </div>
      </div>

      {/* Chart Container - Fixed Dimensions with Scroll */}
      <div className="w-full overflow-x-auto border border-gray-100 dark:border-gray-700 rounded-lg bg-gray-50/50 dark:bg-gray-900/50 p-2 flex justify-center">
          <ComposedChart
            width={1000}
            height={500}
            data={data}
            margin={{ top: 20, right: 30, left: 0, bottom: 20 }}
          >
            <defs>
              <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                <stop offset="50%" stopColor="#f59e0b" stopOpacity={0.1} />
                <stop offset="95%" stopColor="#ef4444" stopOpacity={0.3} />
              </linearGradient>
            </defs>

            <CartesianGrid strokeDasharray="3 3" opacity={0.08} vertical={false} />
            
            <XAxis 
              dataKey="turn" 
              axisLine={false}
              tickLine={false}
              tick={{ fill: '#9ca3af', fontSize: 11 }}
              dy={10}
              minTickGap={30}
            />
            
            <YAxis 
              domain={[-1.1, 1.1]}
              ticks={[-1, -0.5, 0, 0.5, 1]}
              axisLine={false}
              tickLine={false}
              tick={{ fill: '#9ca3af', fontSize: 11 }}
              tickFormatter={(val) => {
                  if (val === 1) return 'Positive (+1)';
                  if (val === -1) return 'Negative (-1)';
                  if (val === 0) return 'Neutral (0)';
                  return val.toFixed(1);
              }}
              width={80}
            />

            <Tooltip
              content={({ active, payload, label }) => {
                if (active && payload && payload.length) {
                  const ctx = payload[0].payload.context;
                  return (
                    <div className="bg-white/90 dark:bg-gray-900/90 backdrop-blur-md border border-gray-200 dark:border-gray-700 p-4 rounded-xl shadow-2xl max-w-xs">
                      <p className="font-bold text-gray-800 dark:text-gray-100 mb-2 border-b border-gray-200 dark:border-gray-800 pb-2">
                        {label}
                      </p>
                      <div className="space-y-2 mb-3">
                        {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
                        {payload.map((p: any) => (
                          <div key={p.name} className="flex justify-between items-center text-sm">
                            <span className="capitalize text-gray-500 dark:text-gray-400">{p.name === 'topic_adherence' ? 'Focus' : p.name}:</span>
                            <span className="font-mono font-bold" style={{ color: p.color }}>
                              {Number(p.value).toFixed(2)}
                            </span>
                          </div>
                        ))}
                      </div>
                      <p className="text-xs text-gray-500 dark:text-gray-400 italic line-clamp-3">
                        &quot;{ctx}&quot;
                      </p>
                    </div>
                  );
                }
                return null;
              }}
            />

            <ReferenceLine y={0} stroke="#9ca3af" strokeDasharray="3 3" opacity={0.5} />

            <Brush 
              dataKey="turn"
              height={30}
              stroke="#6366f1"
              fill="rgba(99, 102, 241, 0.1)"
              tickFormatter={() => ''}
            />

            {/* Sentiment Dots (Green/Red Gradient) */}
            <Line
              type="monotone"
              dataKey="sentiment"
              name="Sentiment"
              stroke="none" // No line
              dot={{ r: 8, strokeWidth: 2, fill: `url(#${gradientId})`, stroke: '#fff' }} 
              activeDot={{ r: 10, strokeWidth: 0, fill: '#10b981' }}
              animationDuration={1500}
            />

            {/* Focus Dots (Blue) */}
            <Line
              type="monotone"
              dataKey="topic_adherence"
              name="Focus"
              stroke="none" // No line
              dot={{ r: 6, fill: '#06b6d4' }}
              activeDot={{ r: 8, fill: '#06b6d4' }}
              animationDuration={1500}
              animationBegin={300}
            />

            {/* Clarity Dots (Purple) */}
            <Line
              type="monotone"
              dataKey="clarity"
              name="Clarity"
              stroke="none" // No line
              dot={{ r: 6, fill: '#a855f7' }}
              activeDot={{ r: 8, fill: '#a855f7' }}
              animationDuration={1500}
              animationBegin={600}
            />

          </ComposedChart>
      </div>
    </div>
  );
}