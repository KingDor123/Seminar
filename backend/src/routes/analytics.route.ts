import { Router } from 'express';
import * as analyticsController from '../controllers/analytics.controller.js';

const router = Router();

router.post('/sessions/:sessionId/metrics', analyticsController.saveMetric);
router.post('/sessions/:sessionId/report', analyticsController.saveReport);
router.get('/sessions/:sessionId/metrics', analyticsController.getMetrics);
router.get('/sessions/:sessionId/report', analyticsController.getReport);

export default router;
