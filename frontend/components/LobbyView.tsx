import React, { useEffect, useState } from 'react';
import { SCENARIOS } from '../constants/appConstants';
import { useChatSession } from '../hooks/useChatSession';

interface LobbyViewProps {
  selectedScenario: string;
  setSelectedScenario: (scenarioId: string) => void;
  language: "en-US" | "he-IL";
  toggleLanguage: () => void;
  onStartCall: () => void;
}

const LobbyView: React.FC<LobbyViewProps> = ({
  selectedScenario,
  setSelectedScenario,
  language,
  toggleLanguage,
  onStartCall,
}) => {
  const { getSessions } = useChatSession();
  const [sessions, setSessions] = useState<any[]>([]);

  useEffect(() => {
    getSessions().then(setSessions);
  }, [getSessions]);

  return (
    <div className="flex flex-col items-center justify-center h-full min-h-[600px] w-full max-w-4xl mx-auto p-4 space-y-8">
      
      <div className="flex flex-col items-center w-full max-w-2xl border rounded-lg shadow-lg bg-white dark:bg-gray-900 p-8 space-y-6">
        <h2 className="text-2xl font-bold text-gray-800 dark:text-gray-100">Ready to Practice?</h2>

        <div className="w-full max-w-md space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Choose Scenario</label>
            <select
              value={selectedScenario}
              onChange={(e) => setSelectedScenario(e.target.value)}
              className="w-full p-2 border rounded-md dark:bg-gray-800 dark:text-white"
            >
              {SCENARIOS.map(s => <option key={s.id} value={s.id}>{s.label}</option>)}
            </select>
          </div>

          <div>
             <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Language</label>
             <button
                onClick={toggleLanguage}
                className="w-full p-2 border rounded-md bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 transition flex justify-between items-center px-4"
            >
                <span>{language === "he-IL" ? "Hebrew (עברית)" : "English (US)"}</span>
                <span>{language === "he-IL" ? "🇮🇱" : "🇺🇸"}</span>
            </button>
          </div>
        </div>

        <button
          onClick={onStartCall}
          className="px-8 py-3 bg-green-600 text-white text-lg font-bold rounded-full shadow-lg hover:bg-green-700 transition transform hover:scale-105"
        >
          Start Video Call 📹
        </button>
      </div>

      {/* Recent Sessions List */}
      <div className="w-full max-w-2xl">
        <h3 className="text-xl font-semibold text-gray-200 mb-4">Recent Practice Sessions</h3>
        <div className="bg-gray-900 border border-gray-700 rounded-lg overflow-hidden max-h-60 overflow-y-auto">
          {sessions.length === 0 ? (
            <div className="p-4 text-gray-500 text-center">No history yet. Start practicing!</div>
          ) : (
            sessions.map((session: any) => (
              <div key={session.id} className="p-4 border-b border-gray-800 hover:bg-gray-800 transition flex justify-between items-center">
                <div>
                  <div className="font-medium text-gray-200">
                    {SCENARIOS.find(s => s.id === session.scenario_id)?.label || session.scenario_id}
                  </div>
                  <div className="text-sm text-gray-500">
                    {new Date(session.start_time).toLocaleString()}
                  </div>
                </div>
                <div className="text-gray-400 text-sm">ID: {session.id}</div>
              </div>
            ))
          )}
        </div>
      </div>

    </div>
  );
};

export default LobbyView;
