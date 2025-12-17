import { Request, Response } from 'express';
import http from 'http';
import { URL } from 'url';
import { AI_SERVICE_BASE_URL, REQUEST_TIMEOUT_MS } from '../config/appConfig.js';

interface AudioPayload {
    text: string;
    voice?: string;
}

const validateMediaPayload = (body: any): string | null => {
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

const proxyWithTimeout = async (url: string, payload: AudioPayload) => {
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
      let errorDetail = "";
      try {
        const errBody = await response.json();
        errorDetail = errBody.detail || JSON.stringify(errBody);
      } catch (e) {
        errorDetail = await response.text();
      }
      throw new Error(`${url} responded with status ${response.status}: ${errorDetail}`);
    }

    return await response.json();
  } finally {
    clearTimeout(timeout);
  }
};

class AiController {
  async tts(req: Request, res: Response) {
    const validationError = validateMediaPayload(req.body);
    if (validationError) {
      return res.status(400).json({ error: validationError });
    }

    try {
      const data = await proxyWithTimeout(
        `${AI_SERVICE_BASE_URL}/tts`,
        req.body
      );

      res.json(data);
    } catch (error: any) {
      const status = error.name === "AbortError" ? 504 : 502;
      console.error("TTS Proxy Error:", error);
      res.status(status).json({ error: "TTS Generation Failed", details: error.message });
    }
  }

  async interact(req: Request, res: Response) {
    try {
        const targetUrl = new URL(`${AI_SERVICE_BASE_URL}/interact`);
        
        const options = {
            hostname: targetUrl.hostname,
            port: targetUrl.port,
            path: targetUrl.pathname,
            method: 'POST',
            headers: req.headers, // Forward headers (Content-Type, Content-Length, etc.)
        };

        // Remove host header to avoid confusion
        delete options.headers['host'];

        const proxyReq = http.request(options, (proxyRes) => {
            // Forward status and headers
            res.writeHead(proxyRes.statusCode || 500, proxyRes.headers);
            
            // Pipe response stream (SSE)
            proxyRes.pipe(res);
        });

        proxyReq.on('error', (err) => {
            console.error("Interact Proxy Error:", err);
            if (!res.headersSent) {
                res.status(502).json({ error: "AI Service Unavailable", details: err.message });
            }
        });

        // Set timeout
        proxyReq.setTimeout(REQUEST_TIMEOUT_MS || 60000, () => {
            proxyReq.destroy();
            if (!res.headersSent) {
                 res.status(504).json({ error: "Gateway Timeout" });
            }
        });

        // Pipe incoming request (Multipart) to proxy request
        req.pipe(proxyReq);

    } catch (error: any) {
        console.error("Interact Error:", error);
        res.status(500).json({ error: "Internal Proxy Error" });
    }
  }
}

export default new AiController();