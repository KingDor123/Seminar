
import { RawMetric, ChartDataPoint } from '../app/sessions/[sessionId]/report/EmotionalArcChart';

export const processMetricsToChartData = (metrics: RawMetric[]): ChartDataPoint[] => {
    if (!metrics || metrics.length === 0) return [];

    // 1. Group metrics by their approximate timestamp or "context"
    const turnsMap = new Map<string, Partial<ChartDataPoint> & { turnNum: number }>();
    let turnCounter = 0;

    // Sort by time
    const sortedMetrics = [...metrics].sort((a, b) =>
      new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
    );

    sortedMetrics.forEach((m) => {
      // Create a unique key for the "turn"
      const key = m.context || m.created_at;

      if (!turnsMap.has(key)) {
        turnCounter++;
        turnsMap.set(key, {
          turnNum: turnCounter,
          context: m.context 
            ? m.context.replace("Analyzed user text: ", "").replace("User responded after AI message:", "User Reply: ") 
            : "Unknown"
        });
      }

      const entry = turnsMap.get(key)!;
      const name = m.metric_name.toLowerCase().trim();
      let val = Number(m.metric_value);
      if (isNaN(val)) val = 0;

      if (name === 'sentiment') entry.sentiment = val;
      if (name === 'topic_adherence' || name === 'topic adherence') entry.topic_adherence = val;
      if (name === 'clarity') entry.clarity = val;
      if (name === 'response_latency' || name === 'latency') entry.latency = val;
    });

    return Array.from(turnsMap.values())
        .map(entry => ({
            turn: `Turn ${entry.turnNum || 0}`,
            context: entry.context || "",
            sentiment: entry.sentiment ?? 0,
            topic_adherence: entry.topic_adherence ?? 0,
            clarity: entry.clarity ?? 0,
            latency: entry.latency ?? 0
        }))
        .filter(d => 
            !isNaN(d.sentiment) && 
            !isNaN(d.topic_adherence) && 
            !isNaN(d.clarity)
        ) as ChartDataPoint[];
};
