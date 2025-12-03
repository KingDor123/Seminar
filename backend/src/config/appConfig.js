// backend/src/config/appConfig.js
const AI_SERVICE_HOST = process.env.AI_SERVICE_HOST || 'ai_service';
const AI_SERVICE_PORT = process.env.AI_SERVICE_PORT || 8000;

export const AI_SERVICE_BASE_URL = `http://${AI_SERVICE_HOST}:${AI_SERVICE_PORT}/ai`;
export const AI_SERVICE_WS_BASE_URL = `ws://${AI_SERVICE_HOST}:${AI_SERVICE_PORT}/ai`;

export const REQUEST_TIMEOUT_MS = 300000;
export const MAX_QUEUE_LENGTH = 50;
export const HEARTBEAT_INTERVAL_MS = 30000;
