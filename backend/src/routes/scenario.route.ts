import express from 'express';
import * as scenarioController from '../controllers/scenario.controller.js';

const router = express.Router();

router.get('/scenarios', scenarioController.listScenarios);
router.get('/scenarios/:scenarioId', scenarioController.getScenarioById);

export default router;
