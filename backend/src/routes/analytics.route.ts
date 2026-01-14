import { Router } from 'express';
import * as analyticsController from '../controllers/analytics.controller.js';
import { authMiddleware, sessionOwnershipMiddleware } from '../middleware/auth.middleware.js'; // Import both middlewares

const router = Router();

// Apply authMiddleware to all analytics routes
router.use(authMiddleware);

// These routes require authentication and session ownership check
router.post('/sessions/:sessionId/metrics', sessionOwnershipMiddleware, analyticsController.saveMetric);
router.post('/sessions/:sessionId/report', sessionOwnershipMiddleware, analyticsController.saveReport);
router.get('/sessions/:sessionId/metrics', sessionOwnershipMiddleware, analyticsController.getMetrics);
router.get('/sessions/:sessionId/report', sessionOwnershipMiddleware, analyticsController.getReport);
router.get('/summary', analyticsController.getSessionsSummary);
router.get('/sessions_list', analyticsController.getSessionsSummary);
router.get('/dashboard', analyticsController.getDashboardStats);

export default router;
