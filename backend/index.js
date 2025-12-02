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

// Proxy TTS endpoint
app.post("/api/tts", async (req, res) => {
  try {
    const response = await fetch("http://ai_service:8000/ai/tts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req.body),
    });

    if (!response.ok) throw new Error("TTS Failed");

    // Pipe audio buffer
    const arrayBuffer = await response.arrayBuffer();
    const buffer = Buffer.from(arrayBuffer);
    
    res.set("Content-Type", "audio/mpeg");
    res.send(buffer);
  } catch (error) {
    console.error("TTS Proxy Error:", error);
    res.status(500).json({ error: "TTS Generation Failed" });
  }
});

// Proxy Video Endpoint
app.post("/api/video", async (req, res) => {
  try {
    const response = await fetch("http://ai_service:8000/ai/video", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req.body),
    });

    if (!response.ok) throw new Error("Video Gen Failed");

    const arrayBuffer = await response.arrayBuffer();
    const buffer = Buffer.from(arrayBuffer);
    
    res.set("Content-Type", "video/mp4");
    res.send(buffer);
  } catch (error) {
    console.error("Video Proxy Error:", error);
    res.status(500).json({ error: "Video Generation Failed" });
  }
});

app.use('/api', router);

// Create HTTP server combining Express
const server = http.createServer(app);

// Setup WebSocket Servers
const wssChat = new WebSocketServer({ noServer: true });
const wssAvatar = new WebSocketServer({ noServer: true });

server.on('upgrade', (request, socket, head) => {
  const pathname = new URL(request.url, `http://${request.headers.host}`).pathname;

  if (pathname === '/api/chat') {
    wssChat.handleUpgrade(request, socket, head, (ws) => {
      wssChat.emit('connection', ws, request);
    });
  } else if (pathname === '/api/avatar') {
    wssAvatar.handleUpgrade(request, socket, head, (ws) => {
      wssAvatar.emit('connection', ws, request);
    });
  } else {
    socket.destroy();
  }
});

// --- Chat Proxy Logic ---
wssChat.on('connection', (clientWs) => {
  console.log('Client connected to Chat WebSocket');

  // Connect to the internal AI service
  const aiWs = new WebSocket('ws://ai_service:8000/ai/stream');
  const messageQueue = [];

  aiWs.on('open', () => {
    console.log('Connected to AI Service (Chat)');
    // Flush queue
    while (messageQueue.length > 0) {
      const msg = messageQueue.shift();
      aiWs.send(msg);
    }
  });

  // Forward message from Client -> AI
  clientWs.on('message', (message) => {
    const msgString = message.toString();
    if (aiWs.readyState === WebSocket.OPEN) {
      aiWs.send(msgString);
    } else {
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
    aiWs.close();
  });

  aiWs.on('close', () => {
    clientWs.close();
  });
  
  clientWs.on('error', (err) => console.error('Client Chat WS Error:', err));
  aiWs.on('error', (err) => console.error('AI Chat WS Error:', err));
});

// --- Avatar Proxy Logic ---
wssAvatar.on('connection', (clientWs) => {
  console.log('Client connected to Avatar WebSocket');

  const aiWs = new WebSocket('ws://ai_service:8000/ai/avatar_stream');

  aiWs.on('open', () => {
    console.log('Connected to AI Service (Avatar)');
  });

  clientWs.on('message', (message) => {
    // Client sends amplitude data -> AI Service
    if (aiWs.readyState === WebSocket.OPEN) {
      aiWs.send(message.toString());
    }
  });

  aiWs.on('message', (message) => {
    // AI Service sends Base64 Frame -> Client
    if (clientWs.readyState === WebSocket.OPEN) {
      clientWs.send(message.toString());
    }
  });

  clientWs.on('close', () => aiWs.close());
  aiWs.on('close', () => clientWs.close());
  
  clientWs.on('error', (err) => console.error('Client Avatar WS Error:', err));
  aiWs.on('error', (err) => console.error('AI Avatar WS Error:', err));
});

// Pick port from environment (Docker injects PORT)
const port = process.env.PORT || 5000;

server.listen(port, () => {
  console.log(`🚀 Backend server running inside Docker on port ${port}`);
  console.log(`🔌 WebSocket proxy listening on /api/chat`);
});