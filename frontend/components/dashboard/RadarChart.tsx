import React from 'react';
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip
} from 'recharts';
import { RadarData } from '../../utils/mockData';
import { he } from '../../constants/he';

interface RadarChartProps {
  data: RadarData[];
}

export const AnalysisRadar: React.FC<RadarChartProps> = ({ data }) => {
  return (
    <div className="h-[300px] w-full relative">
        <ResponsiveContainer width="100%" height="100%">
        <RadarChart cx="50%" cy="50%" outerRadius="80%" data={data}>
            <PolarGrid stroke="#334155" />
            <PolarAngleAxis 
                dataKey="subject" 
                tick={{ fill: '#94a3b8', fontSize: 10, fontWeight: 'bold' }} 
            />
            <PolarRadiusAxis angle={30} domain={[0, 150]} tick={false} axisLine={false} />
            <Radar
                name={he.chart.performanceLabel}
                dataKey="A"
                stroke="#06b6d4"
                strokeWidth={2}
                fill="#06b6d4"
                fillOpacity={0.3}
            />
            <Tooltip 
                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', borderRadius: '8px' }}
                itemStyle={{ color: '#22d3ee' }}
            />
        </RadarChart>
        </ResponsiveContainer>
    </div>
  );
};
