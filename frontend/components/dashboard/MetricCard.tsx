import React from 'react';
import { LucideIcon } from 'lucide-react';
import { cn } from '@/lib/utils';

interface MetricCardProps {
  title: string;
  value: string | number;
  unit?: string;
  icon: LucideIcon;
  variant?: 'positive' | 'neutral' | 'accent';
  delay?: number;
}

const variantStyles = {
  positive: 'border-stat-positive/20 bg-stat-positive/5',
  neutral: 'border-stat-neutral/20 bg-stat-neutral/5',
  accent: 'border-stat-accent/20 bg-stat-accent/5',
};

const iconStyles = {
  positive: 'bg-stat-positive/10 text-stat-positive',
  neutral: 'bg-stat-neutral/10 text-stat-neutral',
  accent: 'bg-stat-accent/10 text-stat-accent',
};

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  unit,
  icon: Icon,
  variant = 'neutral',
  delay = 0,
}) => {
  return (
    <div
      className={cn('rounded-2xl border-2 p-5 animate-fade-in', variantStyles[variant])}
      style={{ animationDelay: `${delay}ms` }}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-muted-foreground">{title}</p>
          <p className="mt-1 text-3xl font-heading font-bold text-foreground">
            {value}
            {unit && <span className="ml-1 text-sm font-medium text-muted-foreground">{unit}</span>}
          </p>
        </div>
        <div className={cn('rounded-xl p-2.5', iconStyles[variant])}>
          <Icon className="h-5 w-5" />
        </div>
      </div>
    </div>
  );
};
