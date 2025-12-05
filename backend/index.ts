import express from 'express';
import cors from "cors";
import dotenv from "dotenv";
import http from 'http';
import { WebSocketServer, WebSocket } from 'ws';
import router from './src/routes/user.route.js';
import aiRouter from './src/routes/ai.route.js';
import chatRouter from './src/routes/chat.route.js'; // Import chat router
import { REQUEST_TIMEOUT_MS, MAX_QUEUE_LENGTH, HEARTBEAT_INTERVAL_MS, AI_SERVICE_WS_BASE_URL } from './src/config/appConfig.js';

dotenv.config();

const app = express();

// Middlewares
app.use(cors());
app.use(express.json());

// Example route
app.get("/api/health", (req, res) => {
  res.json({ status: "ok", time: new Date().toISOString() });
});

app.use('/api', router); 
app.use('/api', aiRouter);
app.use('/api/chat', chatRouter); // Register chat routes (e.g. /api/chat/sessions)

import { attachWebSocketHandlers } from './src/websocket/ws.handler.js';
import { runMigrations } from './src/db/migrate.js';

// Create HTTP server combining Express
const server = http.createServer(app);

// Attach WebSocket handlers
attachWebSocketHandlers(server);

// Pick port from environment (Docker injects PORT)
const port = process.env.PORT || 5000;

if (process.env.NODE_ENV !== 'test') {
  // Run DB migrations before starting
  runMigrations().then(() => {
    server.listen(port, () => {
      console.log(`🚀 Backend server running inside Docker on port ${port}`);
      console.log(`🔌 WebSocket proxy listening on /api/chat and /api/avatar`);
    });
  });
}

export { app, server };
