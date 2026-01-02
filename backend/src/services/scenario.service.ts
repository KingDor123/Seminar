import { getScenarioById, listScenarios } from '../data/scenarios.js';
import type { Scenario } from '../data/scenarios.js';

export const fetchScenarioById = (scenarioId: string): Scenario | null => {
    if (!scenarioId || typeof scenarioId !== 'string') {
        return null;
    }
    return getScenarioById(scenarioId.trim());
};

export const fetchAllScenarios = (): Scenario[] => {
    return listScenarios();
};
