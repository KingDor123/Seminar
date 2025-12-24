import { subDays } from 'date-fns';

export interface SessionStats {
  wpm: number;
  fillers: number;
  sentiment: number; // -1 to 1
  score: number; // 0 to 100
}

export interface RadarData {
  subject: string;
  A: number;
  fullMark: number;
}

export interface SessionData {
  id: number;
  date: string;
  scenario: string;
  stats: SessionStats;
  transcript: string;
  chartData: RadarData[];
}

const SCENARIOS = [
  "Job Interview",
  "First Date",
  "Grocery Store",
  "Team Meeting",
  "Conflict Resolution"
];

const TRANSCRIPTS = [
  "So, um, I think that, like, we should probably go with option A. It's just, you know, better.",
  "Hello! Uh, I am very excited to be here. I, like, really admire your company's work.",
  "Can I get, uh, two pounds of apples? And maybe, um, some of those oranges too.",
  "I feel that, like, my performance has been good. Uh, I hit all my targets.",
  "Look, I understand your point, but, um, I just don't agree. It feels, like, rushed."
];

export const getMockSessions = (): SessionData[] => {
  return Array.from({ length: 8 }).map((_, i) => {
    const wpm = Math.floor(Math.random() * (160 - 80) + 80);
    const fillers = Math.floor(Math.random() * 15);
    const sentiment = Math.random() * 2 - 1; // -1 to 1
    const score = Math.floor(Math.random() * (98 - 60) + 60);
    
    return {
      id: 1000 + i,
      date: subDays(new Date(), i * 2).toISOString(),
      scenario: SCENARIOS[i % SCENARIOS.length],
      stats: {
        wpm,
        fillers,
        sentiment,
        score
      },
      transcript: TRANSCRIPTS[i % TRANSCRIPTS.length],
      chartData: [
        { subject: 'Fluency', A: wpm, fullMark: 160 },
        { subject: 'Clarity', A: 100 - (fillers * 5), fullMark: 100 },
        { subject: 'Confidence', A: (sentiment + 1) * 50, fullMark: 100 },
        { subject: 'Empathy', A: Math.random() * 100, fullMark: 100 },
        { subject: 'Relevance', A: Math.random() * 100, fullMark: 100 },
      ]
    };
  });
};
