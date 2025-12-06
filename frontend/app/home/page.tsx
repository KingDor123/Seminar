"use client";

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import LobbyView from '../../components/LobbyView';
import { SCENARIOS } from '../../constants/appConstants';

export default function HomePage() {
  const router = useRouter();
  const [selectedScenario, setSelectedScenario] = useState(SCENARIOS[0].id);
  const [language, setLanguage] = useState<"en-US" | "he-IL">("he-IL");

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
