"use client";

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '../../context/AuthContext';
import LobbyView from '../../components/LobbyView';
import { SCENARIOS } from '../../constants/appConstants';

export default function HomePage() {
  const { user, isLoading } = useAuth();
  const router = useRouter();
  const [selectedScenario, setSelectedScenario] = useState(SCENARIOS[0].id);
  const [language, setLanguage] = useState<"en-US" | "he-IL">("he-IL");

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-zinc-50 dark:bg-black">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!user) {
    return null; // AuthContext will handle redirect
  }

  const toggleLanguage = () => {
    setLanguage((prev) => (prev === "en-US" ? "he-IL" : "en-US"));
  };

  const handleStartCall = () => {
    router.push(`/meeting/${selectedScenario}`);
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-50 font-sans dark:bg-black">
      <main className="flex flex-col items-center w-full max-w-4xl p-4">
        <h1 className="text-3xl font-bold mb-8 text-gray-800 dark:text-gray-100">SoftSkill AI Coach</h1>
        <LobbyView
          selectedScenario={selectedScenario}
          setSelectedScenario={setSelectedScenario}
          language={language}
          toggleLanguage={toggleLanguage}
          onStartCall={handleStartCall}
        />
      </main>
    </div>
  );
}
