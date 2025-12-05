// backend/src/config/appConfig.ts
const AI_SERVICE_HOST: string = process.env.AI_SERVICE_HOST || 'ai_service';
const AI_SERVICE_PORT: string | number = process.env.AI_SERVICE_PORT || 8000;

export const AI_SERVICE_BASE_URL: string = `http://${AI_SERVICE_HOST}:${AI_SERVICE_PORT}/ai`;
export const AI_SERVICE_WS_BASE_URL: string = `ws://${AI_SERVICE_HOST}:${AI_SERVICE_PORT}/ai`;

export const REQUEST_TIMEOUT_MS: number = 300000;
export const MAX_QUEUE_LENGTH: number = 50;
export const HEARTBEAT_INTERVAL_MS: number = 30000;