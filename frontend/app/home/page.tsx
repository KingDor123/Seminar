"use client";

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '../../context/AuthContext';
import LobbyView from '../../components/LobbyView';
import { SCENARIOS } from '../../constants/appConstants';
import { PageShell } from '../../components/layout/PageShell';
import { he } from '../../constants/he';

export default function HomePage() {
  const { user, isLoading } = useAuth();
  const router = useRouter();
  const [selectedScenario, setSelectedScenario] = useState(SCENARIOS[0].id);
  const [language, setLanguage] = useState<"en-US" | "he-IL">("he-IL");

  if (isLoading) {
    return (
      <PageShell className="flex items-center justify-center">
        <div className="flex flex-col items-center gap-3 text-muted-foreground">
          <div className="h-16 w-16 animate-spin rounded-full border-4 border-muted border-t-primary"></div>
          <span className="text-sm">{he.home.loadingWorkspace}</span>
        </div>
      </PageShell>
    );
  }

  if (!user) {
    return null; // AuthContext will handle redirect
  }

  const toggleLanguage = () => {
    setLanguage((prev) => (prev === "en-US" ? "he-IL" : "en-US"));
  };

  const handleStartCall = () => {
    router.push(`/meeting/${selectedScenario}?lang=${language}`);
  };

  return (
    <PageShell>
      <main className="container mx-auto max-w-5xl px-4">
        <LobbyView
          selectedScenario={selectedScenario}
          setSelectedScenario={setSelectedScenario}
          language={language}
          toggleLanguage={toggleLanguage}
          onStartCall={handleStartCall}
        />
      </main>
    </PageShell>
  );
}
