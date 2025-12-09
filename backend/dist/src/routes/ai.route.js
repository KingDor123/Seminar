// backend/src/routes/ai.route.ts
import express from 'express';
import aiController from '../controllers/ai.controller.js';
const router = express.Router();
router.post('/tts', aiController.tts);
export default router;
