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
import { he } from '../../../../constants/he';

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

  if (!data || data.length === 0) {
    return (
      <div className="h-[500px] flex flex-col items-center justify-center border-2 border-dashed border-border rounded-2xl bg-muted/30">
        <div className="text-lg font-heading font-semibold text-foreground">{he.chart.noDataTitle}</div>
        <p className="text-sm text-muted-foreground mt-1">
          {he.chart.noDataSubtitle}
        </p>
      </div>
    );
  }

  return (
    <div className="bg-card p-6 rounded-2xl shadow-sm border border-border transition-all hover:shadow-lg">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-8 gap-4">
        <div>
          <h3 className="text-2xl font-heading font-semibold text-foreground flex items-center gap-2">
            {he.chart.emotionalArcTitle}
          </h3>
          <p className="text-sm text-muted-foreground mt-1">
            {he.chart.emotionalArcSubtitle}
          </p>
        </div>
        
        {/* Custom Legend */}
        <div className="flex flex-wrap gap-4 text-xs font-medium bg-muted/40 p-2 rounded-lg border border-border">
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-stat-positive shadow-sm"></span>
            <span className="text-muted-foreground">{he.chart.legend.sentiment}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-primary shadow-sm"></span>
            <span className="text-muted-foreground">{he.chart.legend.focus}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-accent-foreground shadow-sm"></span>
            <span className="text-muted-foreground">{he.chart.legend.clarity}</span>
          </div>
        </div>
      </div>

      {/* Chart Container - Fixed Dimensions with Scroll */}
      <div className="w-full overflow-x-auto border border-border rounded-lg bg-muted/30 p-2 flex justify-center">
          <ComposedChart
            width={1000}
            height={500}
            data={data}
            margin={{ top: 20, right: 30, left: 0, bottom: 20 }}
          >
            <defs>
              <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="hsl(var(--stat-positive))" stopOpacity={0.3} />
                <stop offset="50%" stopColor="hsl(var(--stat-neutral))" stopOpacity={0.1} />
                <stop offset="95%" stopColor="hsl(var(--destructive))" stopOpacity={0.3} />
              </linearGradient>
            </defs>

            <CartesianGrid strokeDasharray="3 3" opacity={0.08} vertical={false} />
            
            <XAxis 
              dataKey="turn" 
              axisLine={false}
              tickLine={false}
              tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 11 }}
              dy={10}
              minTickGap={30}
            />
            
            <YAxis 
              domain={[-1.1, 1.1]}
              ticks={[-1, -0.5, 0, 0.5, 1]}
              axisLine={false}
              tickLine={false}
              tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 11 }}
              tickFormatter={(val) => {
                  if (val === 1) return `${he.chart.yAxis.positive} (+1)`;
                  if (val === -1) return `${he.chart.yAxis.negative} (-1)`;
                  if (val === 0) return `${he.chart.yAxis.neutral} (0)`;
                  return val.toFixed(1);
              }}
              width={80}
            />

            <Tooltip
              content={({ active, payload, label }) => {
                if (active && payload && payload.length) {
                  const ctx = payload[0].payload.context;
                  return (
                    <div className="bg-card/90 backdrop-blur-md border border-border p-4 rounded-xl shadow-lg max-w-xs">
                      <p className="font-bold text-foreground mb-2 border-b border-border pb-2">
                        {label}
                      </p>
                      <div className="space-y-2 mb-3">
                        {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
                        {payload.map((p: any) => (
                          <div key={p.name} className="flex justify-between items-center text-sm">
                            <span className="text-muted-foreground">{p.name}:</span>
                            <span className="font-mono font-bold" style={{ color: p.color }}>
                              {Number(p.value).toFixed(2)}
                            </span>
                          </div>
                        ))}
                      </div>
                      <p className="text-xs text-muted-foreground italic line-clamp-3">
                        &quot;{ctx}&quot;
                      </p>
                    </div>
                  );
                }
                return null;
              }}
            />

            <ReferenceLine y={0} stroke="hsl(var(--border))" strokeDasharray="3 3" opacity={0.6} />

            <Brush 
              dataKey="turn"
              height={30}
              stroke="hsl(var(--primary))"
              fill="hsl(var(--primary) / 0.12)"
              tickFormatter={() => ''}
            />

            {/* Sentiment Dots (Green/Red Gradient) */}
            <Line
              type="monotone"
              dataKey="sentiment"
              name={he.chart.legend.sentiment}
              stroke="none" // No line
              dot={{ r: 8, strokeWidth: 2, fill: `url(#${gradientId})`, stroke: '#fff' }} 
              activeDot={{ r: 10, strokeWidth: 0, fill: 'hsl(var(--stat-positive))' }}
              animationDuration={1500}
            />

            {/* Focus Dots (Blue) */}
            <Line
              type="monotone"
              dataKey="topic_adherence"
              name={he.chart.legend.focus}
              stroke="none" // No line
              dot={{ r: 6, fill: 'hsl(var(--primary))' }}
              activeDot={{ r: 8, fill: 'hsl(var(--primary))' }}
              animationDuration={1500}
              animationBegin={300}
            />

            {/* Clarity Dots (Purple) */}
            <Line
              type="monotone"
              dataKey="clarity"
              name={he.chart.legend.clarity}
              stroke="none" // No line
              dot={{ r: 6, fill: 'hsl(var(--accent-foreground))' }}
              activeDot={{ r: 8, fill: 'hsl(var(--accent-foreground))' }}
              animationDuration={1500}
              animationBegin={600}
            />

          </ComposedChart>
      </div>
    </div>
  );
}
