import { Request, Response } from 'express';
import { fetchScenarioById, fetchAllScenarios } from '../services/scenario.service.js';

const INTERNAL_API_KEY = process.env.INTERNAL_API_KEY;

const isInternalRequest = (req: Request): boolean => {
    if (!INTERNAL_API_KEY) {
        return false;
    }
    return req.headers['x-internal-api-key'] === INTERNAL_API_KEY;
};

export const getScenarioById = (req: Request, res: Response) => {
    const scenarioId = req.params.scenarioId;
    const scenario = fetchScenarioById(scenarioId);
    if (!scenario) {
        res.status(404).json({ error: 'Scenario not found' });
        return;
    }

    if (!isInternalRequest(req)) {
        res.status(403).json({ error: 'Scenario access restricted' });
        return;
    }

    res.json(scenario);
};

export const listScenarios = (req: Request, res: Response) => {
    if (!isInternalRequest(req)) {
        res.status(403).json({ error: 'Scenario access restricted' });
        return;
    }
    res.json(fetchAllScenarios());
};
