"use client";

import { useMemo } from 'react';
import { ChartDataPoint } from './EmotionalArcChart';

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
      strengths.push("😊 Great Attitude: You maintained a positive and friendly tone.");
    } else if (avgSentiment < -0.2) {
      tips.push("😐 Tone Check: The conversation felt a bit negative. Try using more positive words.");
    }

    // --- FOCUS ANALYSIS ---
    const distractions = data.filter(d => d.topic_adherence < 0.5);
    if (distractions.length === 0 && avgFocus > 0.8) {
      strengths.push("🎯 Laser Focus: You stayed on topic perfectly throughout the session.");
    } else if (distractions.length > 0) {
      tips.push(`⚠️ Distractions: You drifted off-topic ${distractions.length} times. Try to stick to the scenario's goal.`);
    }

    // --- CLARITY ANALYSIS ---
    if (avgClarity > 0.8) {
        strengths.push("🗣️ Clear Speaker: Your responses were easy to understand.");
    } else if (avgClarity < 0.5) {
        tips.push("🤔 Clarity: Some responses were short or unclear. Don't be afraid to elaborate.");
    }

    // --- LATENCY (PACING) ANALYSIS ---
    if (avgLatency > 1.0 && avgLatency < 4.0) {
        strengths.push("⏱️ Good Pacing: You responded in a natural rhythm.");
    } else if (avgLatency > 5.0) {
        tips.push("🐢 Long Pauses: It took a while to respond. It's okay to use fillers like 'Let me think...'");
    } else if (avgLatency < 0.5) {
        tips.push("🐇 Too Fast: You responded very quickly. Make sure to listen fully before speaking.");
    }

    // Fallback if empty
    if (strengths.length === 0) strengths.push("👍 Good effort! Keep practicing to uncover more strengths.");
    if (tips.length === 0) tips.push("🌟 You're doing great! Try a harder scenario next time.");

    return { strengths, tips, avgSentiment, avgFocus };
  }, [data]);

  if (!summary) return null;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
      {/* Strengths Card */}
      <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-xl p-6 shadow-sm">
        <h3 className="text-xl font-bold text-green-800 dark:text-green-400 mb-4 flex items-center">
          <span className="mr-2">✅</span> What You Did Well
        </h3>
        <ul className="space-y-3">
          {summary.strengths.map((s, i) => (
            <li key={i} className="flex items-start text-green-900 dark:text-green-100">
              <span className="mr-2">•</span> {s}
            </li>
          ))}
        </ul>
      </div>

      {/* Tips Card */}
      <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-xl p-6 shadow-sm">
        <h3 className="text-xl font-bold text-yellow-800 dark:text-yellow-400 mb-4 flex items-center">
          <span className="mr-2">💡</span> Coaching Tips
        </h3>
        <ul className="space-y-3">
          {summary.tips.map((t, i) => (
            <li key={i} className="flex items-start text-yellow-900 dark:text-yellow-100">
              <span className="mr-2">•</span> {t}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
