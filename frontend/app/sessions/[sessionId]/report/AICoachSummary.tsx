"use client";

import { useMemo } from 'react';
import { ChartDataPoint } from './EmotionalArcChart';
import { he } from '../../../../constants/he';

interface AICoachSummaryProps {
  data: ChartDataPoint[];
}

export default function AICoachSummary({ data }: AICoachSummaryProps) {
  const summary = useMemo(() => {
    if (data.length === 0) return null;

    const strengths: string[] = [];
    const tips: string[] = [];

    // Calculate Averages
    const avgSentiment = data.reduce((acc, curr) => acc + (curr.sentiment || 0), 0) / data.length;
    const avgFocus = data.reduce((acc, curr) => acc + (curr.topic_adherence || 0), 0) / data.length;
    const avgClarity = data.reduce((acc, curr) => acc + (curr.clarity || 0), 0) / data.length;
    const avgLatency = data.reduce((acc, curr) => acc + (curr.latency || 0), 0) / data.length;

    // --- SENTIMENT ANALYSIS ---
    if (avgSentiment > 0.5) {
      strengths.push(he.coach.strengths.greatAttitude);
    } else if (avgSentiment < -0.2) {
      tips.push(he.coach.tips.toneCheck);
    }

    // --- FOCUS ANALYSIS ---
    const distractions = data.filter(d => d.topic_adherence < 0.5);
    if (distractions.length === 0 && avgFocus > 0.8) {
      strengths.push(he.coach.strengths.laserFocus);
    } else if (distractions.length > 0) {
      tips.push(he.coach.tips.distractions(distractions.length));
    }

    // --- CLARITY ANALYSIS ---
    if (avgClarity > 0.8) {
        strengths.push(he.coach.strengths.clearSpeaker);
    } else if (avgClarity < 0.5) {
        tips.push(he.coach.tips.clarity);
    }

    // --- LATENCY (PACING) ANALYSIS ---
    if (avgLatency > 1.0 && avgLatency < 4.0) {
        strengths.push(he.coach.strengths.goodPacing);
    } else if (avgLatency > 5.0) {
        tips.push(he.coach.tips.longPauses);
    } else if (avgLatency < 0.5) {
        tips.push(he.coach.tips.tooFast);
    }

    // Fallback if empty
    if (strengths.length === 0) strengths.push(he.coach.strengths.fallback);
    if (tips.length === 0) tips.push(he.coach.tips.fallback);

    return { strengths, tips, avgSentiment, avgFocus };
  }, [data]);

  if (!summary) return null;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
      {/* Strengths Card */}
      <div className="rounded-2xl border border-stat-positive/20 bg-stat-positive/5 p-6 shadow-sm">
        <h3 className="text-xl font-heading font-semibold text-foreground mb-4 flex items-center">
          <span className="mr-2">✅</span> {he.coach.strengthsTitle}
        </h3>
        <ul className="space-y-3">
          {summary.strengths.map((s, i) => (
            <li key={i} className="flex items-start text-foreground">
              <span className="mr-2">•</span> {s}
            </li>
          ))}
        </ul>
      </div>

      {/* Tips Card */}
      <div className="rounded-2xl border border-stat-accent/20 bg-stat-accent/5 p-6 shadow-sm">
        <h3 className="text-xl font-heading font-semibold text-foreground mb-4 flex items-center">
          <span className="mr-2">💡</span> {he.coach.tipsTitle}
        </h3>
        <ul className="space-y-3">
          {summary.tips.map((t, i) => (
            <li key={i} className="flex items-start text-foreground">
              <span className="mr-2">•</span> {t}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
