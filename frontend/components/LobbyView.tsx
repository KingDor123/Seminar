// frontend/components/LobbyView.tsx
import React, { useEffect } from 'react';
import { SCENARIOS } from '../constants/appConstants';
import { useChatSession } from '../hooks/useChatSession';
import { useAuth } from '../context/AuthContext';
import { Building2, ShoppingBasket, Briefcase, Heart, ArrowRight, AlertTriangle, Calendar, Sparkles } from 'lucide-react';
import { WelcomeHeader } from './home/WelcomeHeader';
import { ScenarioCard } from './home/ScenarioCard';
import { MetricCard } from './dashboard/MetricCard';
import { Button } from './ui/button';

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
  
  const scenarioMeta = {
    interview: { icon: Briefcase, variant: "support" as const },
    grocery: { icon: ShoppingBasket, variant: "social" as const },
    date: { icon: Heart, variant: "calm" as const },
    conflict: { icon: AlertTriangle, variant: "focus" as const },
    bank: { icon: Building2, variant: "support" as const },
  };

  const stats = [
    {
      title: "Total Sessions",
      value: sessions.length,
      icon: Calendar,
      variant: "positive" as const,
    },
    {
      title: "Status",
      value: sessions.length > 0 ? "Active" : "New",
      icon: Sparkles,
      variant: "accent" as const,
    },
  ];

  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  return (
    <div className="mx-auto w-full max-w-5xl px-4">
      <WelcomeHeader name={user?.full_name?.split(' ')[0]} />

      <div className="mb-8 grid gap-4 sm:grid-cols-2">
        {stats.map((stat, index) => (
          <MetricCard key={stat.title} {...stat} delay={index * 100} />
        ))}
      </div>

      <section className="mb-10">
        <div className="mb-4 flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
          <div>
            <h2 className="text-2xl font-heading font-semibold text-foreground">Start a New Practice</h2>
            <p className="text-sm text-muted-foreground">Choose a scenario that feels right for you.</p>
          </div>
          <Button
            type="button"
            variant="secondary"
            className="rounded-full px-4 py-2 text-sm"
            onClick={toggleLanguage}
          >
            <span>Language:</span>
            <span className="font-semibold">
              {language === "he-IL" ? "Hebrew" : "English"}
            </span>
          </Button>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          {SCENARIOS.map((scenario, index) => {
            const meta = scenarioMeta[scenario.id as keyof typeof scenarioMeta];
            return (
              <ScenarioCard
                key={scenario.id}
                title={scenario.label}
                description={scenario.description}
                icon={meta?.icon || Building2}
                variant={meta?.variant || "calm"}
                selected={selectedScenario === scenario.id}
                onSelect={() => setSelectedScenario(scenario.id)}
                delay={index * 100}
              />
            );
          })}
        </div>

        <div className="mt-6 flex justify-center">
          <Button
            type="button"
            className="h-14 rounded-full px-10 text-base font-semibold shadow-lg hover:shadow-xl"
            onClick={onStartCall}
          >
            Start Simulation
            <ArrowRight className="h-5 w-5" />
          </Button>
        </div>
      </section>

      <section className="pb-12">
        <h2 className="mb-4 text-xl font-heading font-semibold text-foreground">Recent Activity</h2>
        <div className="overflow-hidden rounded-2xl border border-border bg-card">
          {sessions.length === 0 ? (
            <div className="p-12 text-center text-muted-foreground">
              <div className="text-4xl font-heading font-semibold">No sessions yet</div>
              <p className="mt-2 text-sm">
                Complete your first simulation to see your history here.
              </p>
            </div>
          ) : (
            <table className="w-full text-left">
              <thead>
                <tr className="border-b border-border bg-muted/40 text-xs uppercase tracking-wider text-muted-foreground">
                  <th className="p-4">Scenario</th>
                  <th className="p-4">Date</th>
                  <th className="p-4">Duration</th>
                  <th className="p-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {sessions.map((session) => (
                  <tr key={session.id} className="transition hover:bg-muted/30">
                    <td className="p-4">
                      <div className="flex items-center gap-3">
                        <span className="text-sm font-medium text-foreground">
                          {SCENARIOS.find((s) => s.id === session.scenario_id)?.label || session.scenario_id}
                        </span>
                      </div>
                    </td>
                    <td className="p-4 text-sm text-muted-foreground">
                      {new Date(session.start_time).toLocaleDateString()}
                      <span className="ml-2 text-xs text-muted-foreground/80">
                        {new Date(session.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </td>
                    <td className="p-4 text-sm text-muted-foreground font-mono">--:--</td>
                    <td className="p-4 text-right">
                      <button className="text-sm font-medium text-primary hover:text-primary/80">
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
