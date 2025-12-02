import express from 'express';
import cors from "cors";
import dotenv from "dotenv";
import http from 'http';
import { WebSocketServer, WebSocket } from 'ws';
import router from './src/routes/user.route.js';

dotenv.config();

const app = express();

const REQUEST_TIMEOUT_MS = 10000;
const MAX_QUEUE_LENGTH = 50;
const HEARTBEAT_INTERVAL_MS = 30000;

// Middlewares
app.use(cors());
app.use(express.json());

// Example route
app.get("/api/health", (req, res) => {
  res.json({ status: "ok", time: new Date().toISOString() });
});

const validateMediaPayload = (body) => {
  if (!body || typeof body !== "object") {
    return "Request body must be a JSON object.";
  }

  if (typeof body.text !== "string" || body.text.trim().length === 0) {
    return "Field 'text' is required and must be a non-empty string.";
  }

  if (body.voice && typeof body.voice !== "string") {
    return "Field 'voice', when provided, must be a string.";
  }

  return null;
};

const proxyWithTimeout = async (url, payload, expectedContentType) => {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  try {
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: controller.signal,
    });

    if (!response.ok) {
      throw new Error(`${url} responded with status ${response.status}`);
    }

    const arrayBuffer = await response.arrayBuffer();
    const buffer = Buffer.from(arrayBuffer);

    return { buffer, contentType: expectedContentType };
  } finally {
    clearTimeout(timeout);
  }
};

// Proxy TTS endpoint
app.post("/api/tts", async (req, res) => {
  const validationError = validateMediaPayload(req.body);
  if (validationError) {
    return res.status(400).json({ error: validationError });
  }

  try {
    const { buffer, contentType } = await proxyWithTimeout(
      "http://ai_service:8000/ai/tts",
      req.body,
      "audio/mpeg",
    );

    res.set("Content-Type", contentType);
    res.send(buffer);
  } catch (error) {
    const status = error.name === "AbortError" ? 504 : 502;
    console.error("TTS Proxy Error:", error);
    res.status(status).json({ error: "TTS Generation Failed" });
  }
});

// Proxy Video Endpoint
app.post("/api/video", async (req, res) => {
  const validationError = validateMediaPayload(req.body);
  if (validationError) {
    return res.status(400).json({ error: validationError });
  }

  try {
    const { buffer, contentType } = await proxyWithTimeout(
      "http://ai_service:8000/ai/video",
      req.body,
      "video/mp4",
    );

    res.set("Content-Type", contentType);
    res.send(buffer);
  } catch (error) {
    const status = error.name === "AbortError" ? 504 : 502;
    console.error("Video Proxy Error:", error);
    res.status(status).json({ error: "Video Generation Failed" });
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

const setupHeartbeatInterval = (clientWs, aiWs, messageQueue) => {
  const heartbeat = { clientAlive: true, aiAlive: true };

  const interval = setInterval(() => {
    if (clientWs.readyState === WebSocket.OPEN) {
      if (!heartbeat.clientAlive) {
        console.warn('Client heartbeat missed - closing sockets.');
        clientWs.terminate();
        aiWs.terminate();
        clearInterval(interval);
        messageQueue.length = 0;
        return;
      }

      heartbeat.clientAlive = false;
      clientWs.ping();
    }

    if (aiWs.readyState === WebSocket.OPEN) {
      if (!heartbeat.aiAlive) {
        console.warn('AI heartbeat missed - closing sockets.');
        aiWs.terminate();
        clientWs.terminate();
        clearInterval(interval);
        messageQueue.length = 0;
        return;
      }

      heartbeat.aiAlive = false;
      aiWs.ping();
    }
  }, HEARTBEAT_INTERVAL_MS);

  clientWs.on('pong', () => {
    heartbeat.clientAlive = true;
  });

  aiWs.on('pong', () => {
    heartbeat.aiAlive = true;
  });

  return interval;
};

// --- Chat Proxy Logic ---
wssChat.on('connection', (clientWs) => {
  console.log('Client connected to Chat WebSocket');

  // Connect to the internal AI service
  const aiWs = new WebSocket('ws://ai_service:8000/ai/stream');
  const messageQueue = [];

  const heartbeatInterval = setupHeartbeatInterval(clientWs, aiWs, messageQueue);

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
      if (messageQueue.length >= MAX_QUEUE_LENGTH) {
        messageQueue.shift();
      }
      messageQueue.push(msgString);
    }
  });

  // Forward message from AI -> Client
  aiWs.on('message', (message) => {
    if (clientWs.readyState === WebSocket.OPEN) {
      clientWs.send(message.toString());
    }
  });

  const cleanup = () => {
    clearInterval(heartbeatInterval);
    messageQueue.length = 0;

    if (aiWs.readyState === WebSocket.OPEN || aiWs.readyState === WebSocket.CONNECTING) {
      aiWs.close();
    }

    if (clientWs.readyState === WebSocket.OPEN || clientWs.readyState === WebSocket.CONNECTING) {
      clientWs.close();
    }
  };

  // Handle closures
  clientWs.on('close', cleanup);

  aiWs.on('close', cleanup);

  clientWs.on('error', (err) => console.error('Client Chat WS Error:', err));
  aiWs.on('error', (err) => console.error('AI Chat WS Error:', err));
});

// --- Avatar Proxy Logic ---
wssAvatar.on('connection', (clientWs) => {
  console.log('Client connected to Avatar WebSocket');

  const aiWs = new WebSocket('ws://ai_service:8000/ai/avatar_stream');
  const heartbeatInterval = setupHeartbeatInterval(clientWs, aiWs, []);

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

  const cleanup = () => {
    clearInterval(heartbeatInterval);

    if (aiWs.readyState === WebSocket.OPEN || aiWs.readyState === WebSocket.CONNECTING) {
      aiWs.close();
    }

    if (clientWs.readyState === WebSocket.OPEN || clientWs.readyState === WebSocket.CONNECTING) {
      clientWs.close();
    }
  };

  clientWs.on('close', cleanup);
  aiWs.on('close', cleanup);

  clientWs.on('error', (err) => console.error('Client Avatar WS Error:', err));
  aiWs.on('error', (err) => console.error('AI Avatar WS Error:', err));
});

// Pick port from environment (Docker injects PORT)
const port = process.env.PORT || 5000;

if (process.env.NODE_ENV !== 'test') {
  server.listen(port, () => {
    console.log(`🚀 Backend server running inside Docker on port ${port}`);
    console.log(`🔌 WebSocket proxy listening on /api/chat`);
  });
}

export { app, server, wssChat, wssAvatar };
