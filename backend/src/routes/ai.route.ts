// backend/src/routes/ai.route.ts
import express from 'express';
import multer from 'multer';
import aiController from '../controllers/ai.controller.js';

const router = express.Router();
const upload = multer({ dest: 'uploads/' }); // Temporary storage for audio files

router.post('/tts', aiController.tts);
router.post('/interact', upload.single('audio'), aiController.interact);
router.post('/report/generate/:sessionId', aiController.generateReport);

export default router;