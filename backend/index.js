import express from 'express';
import cors from "cors";
import dotenv from "dotenv";
import http from 'http';
import { WebSocketServer, WebSocket } from 'ws';
import router from './src/routes/user.route.js';

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

// Create HTTP server combining Express
const server = http.createServer(app);

// Setup WebSocket Server
const wss = new WebSocketServer({ server, path: '/api/chat' });

wss.on('connection', (clientWs) => {
  console.log('Client connected to WebSocket proxy');

  // Connect to the internal AI service
  const aiWs = new WebSocket('ws://ai_service:8000/ai/stream');
  const messageQueue = [];

  aiWs.on('open', () => {
    console.log('Connected to AI Service');
    // Flush queue
    while (messageQueue.length > 0) {
      const msg = messageQueue.shift();
      aiWs.send(msg);
    }
  });

  // Forward message from Client -> AI
  clientWs.on('message', (message) => {
    console.log('DEBUG: Received message from client:', message.toString());
    const msgString = message.toString();
    if (aiWs.readyState === WebSocket.OPEN) {
      aiWs.send(msgString);
    } else {
      console.log('Buffering message for AI...');
      messageQueue.push(msgString);
    }
  });

  // Forward message from AI -> Client
  aiWs.on('message', (message) => {
    if (clientWs.readyState === WebSocket.OPEN) {
      clientWs.send(message.toString());
    }
  });

  // Handle closures
  clientWs.on('close', () => {
    console.log('Client disconnected');
    aiWs.close();
  });

  aiWs.on('close', () => {
    console.log('AI Service disconnected');
    clientWs.close();
  });

  // Handle errors
  clientWs.on('error', (err) => console.error('Client WS Error:', err));
  aiWs.on('error', (err) => console.error('AI WS Error:', err));
});

// Pick port from environment (Docker injects PORT)
const port = process.env.PORT || 5000;

server.listen(port, () => {
  console.log(`🚀 Backend server running inside Docker on port ${port}`);
  console.log(`🔌 WebSocket proxy listening on /api/chat`);
});