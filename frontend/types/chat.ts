// frontend/types/chat.ts

export interface ChatMessage {
  role: "user" | "ai";
  content: string;
}

export interface Viseme {
  time?: number; // Some formats use time
  start: number;
  end: number;
  value: string;
}