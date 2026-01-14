import { Request, Response } from 'express';
import { ttsService } from '../services/ai/tts.service.js';
import { llmService } from '../services/ai/llm.service.js';
import { sentimentService } from '../services/ai/sentiment.service.js';
import { sttService } from '../services/ai/stt.service.js';
import { promptService } from '../services/ai/prompt.service.js';
import * as chatService from '../services/chat.service.js';
import logger from '../utils/logger.js';
import fs from 'fs';

/**
 * Controller for AI-related endpoints.
 * Handles Text-to-Speech, User Interactions (Chat), and Report Generation.
 */
class AiController {
  
  /**
   * Generates audio from text.
   * POST /api/tts
   */
  async tts(req: Request, res: Response) {
    const { text } = req.body;
    
    if (!text || typeof text !== 'string') {
        return res.status(400).json({ error: "Text is required" });
    }

    try {
      const audioContent = await ttsService.generateAudioBase64(text, 'he');
      res.json({ audioContent });
    } catch (error: any) {
      logger.error("TTS Generation Failed:", error);
      res.status(500).json({ error: "TTS Generation Failed", details: error.message });
    }
  }

  /**
   * Handles the main chat interaction flow.
   * 1. Transcribes audio (if provided) [Placeholder].
   * 2. Analyzes sentiment & Turn Analysis.
   * 3. Streams an LLM response back to the client via SSE.
   * 4. Saves the conversation to the database.
   * 
   * POST /api/interact
   */
  async interact(req: Request, res: Response) {
    let audioPath: string | null = null;
    try {
        // Multer puts the file in req.file and text fields in req.body
        const { session_id, scenario_id } = req.body;
        let text = req.body.text;

        // 1. STT if audio provided
        if (req.file) {
            audioPath = req.file.path;
            const transcribedText = await sttService.transcribe(audioPath);
            if (transcribedText) {
                text = transcribedText;
            }
        }

        if (!text) {
             return res.status(400).json({ error: "Input text or audio required" });
        }

        logger.info(`Interact: session=${session_id} text="${text}"`);

        // 2. Analyze Sentiment
        const sentimentResult = await sentimentService.analyzeSentiment(text);
        
        // 2b. Start Turn Analysis (Parallel)
        // We start this now but await it before saving the user message.
        const analysisPromise = promptService.analyzeTurn(text, sentimentResult.label);

        // 3. Prepare SSE
        res.setHeader('Content-Type', 'text/event-stream');
        res.setHeader('Cache-Control', 'no-cache');
        res.setHeader('Connection', 'keep-alive');

        // 4. Update Frontend with transcribed text & sentiment
        // The frontend useStreamingConversation expects "event: transcript" or just data
        // Matching the frontend hook logic:
        res.write(`event: transcript\ndata: ${JSON.stringify({ role: 'user', text: text, sentiment: sentimentResult.label })}\n\n`);

        // 5. Construct LLM Messages
        // Fetch history for context
        const history = await chatService.getSessionHistory(Number(session_id));
        const historyMessages = history.slice(-10).map(m => ({
            role: m.role,
            content: m.content
        }));
        
        const finalMessages = await promptService.buildChatMessages(
            scenario_id,
            sentimentResult.label,
            historyMessages,
            text
        );

        // 6. Stream Response
        let fullAiResponse = "";
        for await (const token of llmService.streamResponse(finalMessages)) {
            fullAiResponse += token;
            res.write(`event: transcript\ndata: ${JSON.stringify({ role: 'assistant', text: token, partial: true })}\n\n`);
        }

        // 7. Save to DB
        // Await the analysis now
        const turnAnalysis = await analysisPromise;

        await chatService.saveMessage(
            Number(session_id), 
            'user', 
            text, 
            sentimentResult.label,
            turnAnalysis
        );
        await chatService.saveMessage(Number(session_id), 'ai', fullAiResponse);

        // 8. Done
        res.write(`event: status\ndata: done\n\n`);
        res.end();

    } catch (error: any) {
        logger.error("Interact Error:", error);
        if (!res.headersSent) {
            res.status(500).json({ error: "Interaction Failed", details: error.message });
        } else {
            res.write(`event: error\ndata: ${error.message}\n\n`);
            res.end();
        }
    } finally {
        if (audioPath && fs.existsSync(audioPath)) {
            fs.unlinkSync(audioPath); // Clean up temp file
        }
    }
  }

  /**
   * Generates a behavioral report for a session.
   * Aggregates stats and uses the LLM to provide qualitative feedback.
   * 
   * POST /api/report/generate/:sessionId
   */
  async generateReport(req: Request, res: Response) {
    const sessionId = parseInt(req.params.sessionId);
    if (isNaN(sessionId)) {
        return res.status(400).json({ error: "Invalid Session ID" });
    }

    try {
      const history = await chatService.getSessionHistory(sessionId, true);
      
      let conversationText = "";
      history.forEach(m => conversationText += `${m.role.toUpperCase()}: ${m.content}\n`);

      const prompt = `
      Analyze this conversation.
      Role: Professional Behavioral Therapist.
      Conversation:
      ${conversationText}
      
      Provide a JSON summary with keys: summary, strengths (array), tips (array), score (0-100).
      Return JSON only.
      `;

      const llmRaw = await llmService.generateResponse([{ role: 'user', content: prompt }], 'json');
      const analysis = JSON.parse(llmRaw);

      res.json({
          sessionId,
          ...analysis,
          metrics: {
              average_sentiment: "analyzed", // Simplified
              social_impact_score: analysis.score || 0
          }
      });

    } catch (error: any) {
        logger.error("Report Generation Error:", error);
        res.status(500).json({ error: "Report Generation Failed" });
    }
  }
}

export default new AiController();
