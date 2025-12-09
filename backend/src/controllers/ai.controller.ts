import { Request, Response } from 'express';
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
}

export default new AiController();
