// frontend/components/LobbyView.tsx
import React, { useEffect, useState } from 'react';
import { SCENARIOS } from '../constants/appConstants';
import { useChatSession } from '../hooks/useChatSession';
import { useAuth } from '../context/AuthContext';

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
  const { loadSessions, sessions } = useChatSession();
  const { user } = useAuth();
  
  // Icons mapping for scenarios
  const scenarioIcons: Record<string, string> = {
      'bank': '🏦',
      'grocery': '🛒',
      'interview': '💼',
      'cafe': '☕',
      'date': '❤️'
  };

  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  return (
    <div className="w-full max-w-6xl mx-auto space-y-12">
      
      {/* 1. Header Section */}
      <header className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
              <h1 className="text-4xl font-extrabold text-gray-900 dark:text-white tracking-tight">
                  Welcome back, {user?.full_name?.split(' ')[0] || 'Friend'}! 👋
              </h1>
              <p className="text-lg text-gray-600 dark:text-gray-400 mt-2">
                  Ready to practice your social interactions today?
              </p>
          </div>
          
          <div className="flex items-center gap-4">
              <div className="bg-white dark:bg-gray-800 p-4 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 text-center min-w-[120px]">
                  <div className="text-3xl font-bold text-blue-600 dark:text-blue-400">{sessions.length}</div>
                  <div className="text-xs text-gray-500 font-medium uppercase tracking-wide">Sessions</div>
              </div>
              <div className="bg-white dark:bg-gray-800 p-4 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 text-center min-w-[120px]">
                  <div className="text-3xl font-bold text-green-600 dark:text-green-400">
                    {sessions.length > 0 ? 'Active' : 'New'}
                  </div>
                  <div className="text-xs text-gray-500 font-medium uppercase tracking-wide">Status</div>
              </div>
          </div>
      </header>

      {/* 2. Main Action Area: Choose Scenario */}
      <section>
          <div className="flex justify-between items-end mb-6">
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Start a New Practice</h2>
              
              <button
                onClick={toggleLanguage}
                className="flex items-center gap-2 px-4 py-2 bg-gray-100 dark:bg-gray-800 rounded-lg text-sm font-medium hover:bg-gray-200 dark:hover:bg-gray-700 transition"
              >
                <span>Language:</span>
                <span className="font-bold">{language === "he-IL" ? "Hebrew 🇮🇱" : "English 🇺🇸"}</span>
              </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {SCENARIOS.map((scenario) => {
                  const isSelected = selectedScenario === scenario.id;
                  return (
                      <div 
                          key={scenario.id}
                          onClick={() => setSelectedScenario(scenario.id)}
                          className={`cursor-pointer group relative p-6 rounded-2xl border-2 transition-all duration-200 ${
                              isSelected 
                                ? 'border-blue-500 bg-blue-50/50 dark:bg-blue-900/20 shadow-lg scale-[1.02]' 
                                : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 hover:border-blue-300 dark:hover:border-blue-700 hover:shadow-md'
                          }`}
                      >
                          <div className="flex justify-between items-start mb-4">
                              <span className="text-4xl">{scenarioIcons[scenario.id] || '🎯'}</span>
                              <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center ${
                                  isSelected ? 'border-blue-500 bg-blue-500' : 'border-gray-300 dark:border-gray-600'
                              }`}>
                                  {isSelected && <div className="w-2.5 h-2.5 bg-white rounded-full" />}
                              </div>
                          </div>
                          
                          <h3 className={`text-xl font-bold mb-2 ${isSelected ? 'text-blue-700 dark:text-blue-300' : 'text-gray-900 dark:text-white'}`}>
                              {scenario.label}
                          </h3>
                          <p className="text-sm text-gray-500 dark:text-gray-400 leading-relaxed">
                              {scenario.description}
                          </p>
                      </div>
                  );
              })}
          </div>

          <div className="mt-8 flex justify-center">
              <button
                  onClick={onStartCall}
                  className="group relative inline-flex items-center gap-3 px-12 py-5 bg-gradient-to-r from-blue-600 to-indigo-600 text-white text-xl font-bold rounded-full shadow-xl hover:shadow-2xl hover:scale-105 transition-all duration-200 focus:outline-none focus:ring-4 focus:ring-blue-500/30"
              >
                  <span>Start Simulation</span>
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 group-hover:translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                  </svg>
              </button>
          </div>
      </section>

      {/* 3. Recent History */}
      <section className="pb-12">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">Recent Activity</h2>
          
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
              {sessions.length === 0 ? (
                  <div className="p-12 text-center text-gray-500 dark:text-gray-400">
                      <div className="text-6xl mb-4">📝</div>
                      <p className="text-lg">No sessions yet.</p>
                      <p className="text-sm">Complete your first simulation to see your history here!</p>
                  </div>
              ) : (
                  <table className="w-full text-left border-collapse">
                      <thead>
                          <tr className="bg-gray-50 dark:bg-gray-900/50 border-b border-gray-200 dark:border-gray-700 text-xs uppercase tracking-wider text-gray-500 font-semibold">
                              <th className="p-4">Scenario</th>
                              <th className="p-4">Date</th>
                              <th className="p-4">Duration</th>
                              <th className="p-4 text-right">Action</th>
                          </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                          {sessions.map((session) => (
                              <tr key={session.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50 transition">
                                  <td className="p-4">
                                      <div className="flex items-center gap-3">
                                          <span className="text-2xl">{scenarioIcons[session.scenario_id] || '🎯'}</span>
                                          <span className="font-medium text-gray-900 dark:text-white">
                                              {SCENARIOS.find(s => s.id === session.scenario_id)?.label || session.scenario_id}
                                          </span>
                                      </div>
                                  </td>
                                  <td className="p-4 text-gray-600 dark:text-gray-300">
                                      {new Date(session.start_time).toLocaleDateString()}
                                      <span className="text-xs text-gray-400 ml-2">
                                          {new Date(session.start_time).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                                      </span>
                                  </td>
                                  <td className="p-4 text-gray-500 font-mono text-sm">
                                      {/* Placeholder for duration calculation */}
                                      --:--
                                  </td>
                                  <td className="p-4 text-right">
                                      <button className="text-blue-600 hover:text-blue-800 text-sm font-medium">
                                          View Details
                                      </button>
                                  </td>
                              </tr>
                          ))}
                      </tbody>
                  </table>
              )}
          </div>
      </section>

    </div>
  );
};

export default LobbyView;