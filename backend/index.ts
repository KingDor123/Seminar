import express from 'express';
import cors from "cors";
import dotenv from "dotenv";
import http from 'http';
import cookieParser from 'cookie-parser';
import router from './src/routes/user.route.js';
import authRouter from './src/routes/auth.route.js';
import aiRouter from './src/routes/ai.route.js';
import chatRouter from './src/routes/chat.route.js'; // Import chat router
import analyticsRouter from './src/routes/analytics.route.js';
import scenarioRouter from './src/routes/scenario.route.js';

dotenv.config();

const app = express();

// Middlewares
app.use(cors({
  origin: 'http://localhost:3000', // Allow frontend
  credentials: true // Allow cookies
}));
app.use(express.json());
app.use(cookieParser());

// Example route
app.get("/api/health", (req, res) => {
  res.json({ status: "ok", time: new Date().toISOString() });
});

app.use('/api', authRouter);
app.use('/api', router);
app.use('/api', aiRouter);
app.use('/api/chat', chatRouter); // Register chat routes (e.g. /api/chat/sessions)
app.use('/api/analytics', analyticsRouter);
app.use('/api', scenarioRouter);

// Create HTTP server combining Express
const server = http.createServer(app);

// WebSocket proxy removed (no active /ai/stream endpoint in ai_service).

// Pick port from environment (Docker injects PORT)
const port = process.env.PORT || process.env.BACKEND_PORT || 5001;

if (process.env.NODE_ENV !== 'test') {
  server.listen(port, () => {
    console.log(`🚀 Backend server running inside Docker on port ${port}`);
  });
}

export { app, server };
