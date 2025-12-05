import express from 'express';
import * as chatController from '../controllers/chat.controller.js';

const router = express.Router();

router.post('/sessions', chatController.startSession);
router.post('/sessions/:sessionId/messages', chatController.saveMessage);
router.get('/users/:userId/sessions', chatController.getUserSessions);
router.get('/sessions/:sessionId/messages', chatController.getSessionHistory);

export default router;
