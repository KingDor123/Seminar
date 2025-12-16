'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '../../context/AuthContext';
import { sessionService } from '../../services/sessionService'; // Import the new sessionService
import Link from 'next/link';

interface Session {
  id: number;
  scenario_id: string;
  start_time: string; // ISO string
}

export default function SessionsPage() {
  const { user, isLoading } = useAuth();
  const router = useRouter();
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isLoading) return;
    
    if (!user) {
      // AuthContext handles redirect, but we can double check or just return
      return; 
    }

    const fetchSessions = async () => {
      try {
        setLoading(true);
        // Use the sessionService to fetch user sessions
        const response = await sessionService.getUserSessions(user.id); 
        setSessions(response);
      } catch (err: unknown) {
        console.error("Failed to fetch user sessions:", err);
        let errorMessage = "Failed to load sessions.";
        if (err && typeof err === 'object' && 'response' in err) {
             // eslint-disable-next-line @typescript-eslint/no-explicit-any
             errorMessage = (err as any).response?.data?.message || errorMessage;
        }
        setError(errorMessage);
      } finally {
        setLoading(false);
      }
    };

    fetchSessions();
  }, [user, isLoading, router]);

  if (isLoading) {
      return <div className="text-center py-8">Verifying session...</div>;
  }

  if (loading) {
    return <div className="text-center py-8">Loading sessions...</div>;
  }

  if (error) {
    return <div className="text-center py-8 text-red-600">Error: {error}</div>;
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8 dark:bg-gray-900 text-gray-900 dark:text-white">
      <div className="max-w-3xl mx-auto space-y-8">
        <h2 className="text-3xl font-extrabold text-center">Your Past Sessions</h2>

        {sessions.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-600 dark:text-gray-400 mb-6 text-lg">You have no recorded sessions yet.</p>
            <Link 
              href="/home" 
              className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
            >
              Start a New Session
            </Link>
          </div>
        ) : (
          <div className="bg-white shadow overflow-hidden sm:rounded-lg dark:bg-gray-800">
            <ul role="list" className="divide-y divide-gray-200 dark:divide-gray-700">
              {sessions.map((session) => (
                <li key={session.id} className="px-4 py-4 sm:px-6 hover:bg-gray-50 dark:hover:bg-gray-700 flex justify-between items-center">
                  <div>
                    <p className="text-lg font-medium text-blue-600 dark:text-blue-400">
                      Scenario: {session.scenario_id}
                    </p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      Started: {new Date(session.start_time).toLocaleString()}
                    </p>
                  </div>
                  <Link href={`/sessions/${session.id}/report`} className="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-200 font-medium">
                    View Report &rarr;
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
