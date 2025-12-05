// backend/src/websocket/ws.handler.js
import { WebSocketServer, WebSocket } from 'ws';
import {
  AI_SERVICE_WS_BASE_URL,
  MAX_QUEUE_LENGTH,
  HEARTBEAT_INTERVAL_MS
} from '../config/appConfig.js';

const wssChat = new WebSocketServer({ noServer: true });

const setupHeartbeatInterval = (clientWs, aiWs, messageQueue) => {
  const heartbeat = { clientAlive: true, aiAlive: true };

  const interval = setInterval(() => {
    if (clientWs.readyState === WebSocket.OPEN) {
      if (!heartbeat.clientAlive) {
        console.warn('Client heartbeat missed - closing sockets.');
        clientWs.terminate();
        aiWs.terminate();
        clearInterval(interval);
        if (messageQueue) messageQueue.length = 0;
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
        if (messageQueue) messageQueue.length = 0;
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

const cleanupWsConnections = (heartbeatInterval, clientWs, aiWs, messageQueue = null) => {
  clearInterval(heartbeatInterval);
  if (messageQueue) {
    messageQueue.length = 0;
  }

  if (aiWs.readyState === WebSocket.OPEN || aiWs.readyState === WebSocket.CONNECTING) {
    aiWs.close();
  }

  if (clientWs.readyState === WebSocket.OPEN || clientWs.readyState === WebSocket.CONNECTING) {
    clientWs.close();
  }
};

// --- Chat Proxy Logic ---
wssChat.on('connection', (clientWs) => {
  console.log('Client connected to Chat WebSocket');

  // Connect to the internal AI service
  const aiWs = new WebSocket(`${AI_SERVICE_WS_BASE_URL}/stream`);
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
    console.log(`[ChatWS] Received message from client: ${message.toString().substring(0, 50)}...`);
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

  // Handle closures
  clientWs.on('close', () => cleanupWsConnections(heartbeatInterval, clientWs, aiWs, messageQueue));
  aiWs.on('close', () => cleanupWsConnections(heartbeatInterval, clientWs, aiWs, messageQueue));

  clientWs.on('error', (err) => console.error('Client Chat WS Error:', err));
  aiWs.on('error', (err) => console.error('AI Chat WS Error:', err));
});

export const attachWebSocketHandlers = (server) => {
  server.on('upgrade', (request, socket, head) => {
    const pathname = new URL(request.url, `http://${request.headers.host}`).pathname;

    if (pathname === '/api/chat') {
      wssChat.handleUpgrade(request, socket, head, (ws) => {
        wssChat.emit('connection', ws, request);
      });
    } else {
      socket.destroy();
    }
  });
};