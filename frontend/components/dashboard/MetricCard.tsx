import React from 'react';
import { clsx } from 'clsx';
import { LucideIcon } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string | number;
  unit?: string;
  icon: LucideIcon;
  trend?: 'up' | 'down' | 'neutral';
  color?: 'blue' | 'green' | 'red' | 'yellow' | 'cyan';
}

export const MetricCard: React.FC<MetricCardProps> = ({ 
  title, 
  value, 
  unit, 
  icon: Icon,
  color = 'cyan' 
}) => {
  const colorStyles = {
    blue: 'text-blue-400 border-blue-500/30 bg-blue-500/10',
    green: 'text-green-400 border-green-500/30 bg-green-500/10',
    red: 'text-red-400 border-red-500/30 bg-red-500/10',
    yellow: 'text-yellow-400 border-yellow-500/30 bg-yellow-500/10',
    cyan: 'text-cyan-400 border-cyan-500/30 bg-cyan-500/10',
  };

  return (
    <div className={clsx(
      "relative overflow-hidden rounded-2xl border p-4 backdrop-blur-md transition-all hover:scale-[1.02]",
      colorStyles[color]
    )}>
      <div className="flex items-center justify-between">
        <span className="text-xs font-bold uppercase tracking-wider opacity-80">{title}</span>
        <Icon className="h-4 w-4 opacity-70" />
      </div>
      <div className="mt-3 flex items-baseline gap-1">
        <span className="text-3xl font-bold tracking-tight">{value}</span>
        {unit && <span className="text-sm font-medium opacity-60">{unit}</span>}
      </div>
      <div className="absolute -bottom-4 -right-4 h-16 w-16 rounded-full bg-current opacity-[0.08] blur-xl" />
    </div>
  );
};
