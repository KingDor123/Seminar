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
  const { user } = useAuth();
  const router = useRouter();
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!user) {
      router.push('/login'); // Redirect to login if not authenticated
      return;
    }

    const fetchSessions = async () => {
      try {
        setLoading(true);
        // Use the sessionService to fetch user sessions
        const response = await sessionService.getUserSessions(user.id); 
        setSessions(response);
      } catch (err: any) {
        console.error("Failed to fetch user sessions:", err);
        setError(err.response?.data?.message || "Failed to load sessions.");
      } finally {
        setLoading(false);
      }
    };

    fetchSessions();
  }, [user, router]);

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
          <p className="text-center text-gray-600 dark:text-gray-400">You have no recorded sessions yet.</p>
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
