import { subDays } from 'date-fns';
import { he } from '../constants/he';

export interface SessionStats {
  wpm: number;
  fillers: number;
  sentiment: number; // -1 to 1
  sentimentConfidence?: number; // 0 to 1
  fluencyScore?: number; // 0 to 10
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

const SCENARIOS = he.mock.scenarios;
const TRANSCRIPTS = he.mock.transcripts;
const RADAR_SUBJECTS = he.mock.radarSubjects;

export const getMockSessions = (): SessionData[] => {
  return Array.from({ length: 8 }).map((_, i) => {
    const wpm = Math.floor(Math.random() * (160 - 80) + 80);
    const fillers = Math.floor(Math.random() * 15);
    const sentiment = Math.random() * 2 - 1; // -1 to 1
    const sentimentConfidence = Math.random();
    const fluencyScore = Math.max(0, Math.min(10, 10 - (fillers / Math.max(1, wpm / 10))));
    const score = Math.floor(Math.random() * (98 - 60) + 60);
    
    return {
      id: 1000 + i,
      date: subDays(new Date(), i * 2).toISOString(),
      scenario: SCENARIOS[i % SCENARIOS.length],
      stats: {
        wpm,
        fillers,
        sentiment,
        sentimentConfidence,
        fluencyScore,
        score
      },
      transcript: TRANSCRIPTS[i % TRANSCRIPTS.length],
      chartData: [
        { subject: RADAR_SUBJECTS[0], A: fluencyScore * 10, fullMark: 100 },
        { subject: RADAR_SUBJECTS[1], A: 100 - (fillers * 5), fullMark: 100 },
        { subject: RADAR_SUBJECTS[2], A: (sentimentConfidence * 100), fullMark: 100 },
        { subject: RADAR_SUBJECTS[3], A: Math.random() * 100, fullMark: 100 },
        { subject: RADAR_SUBJECTS[4], A: Math.random() * 100, fullMark: 100 },
      ]
    };
  });
};
