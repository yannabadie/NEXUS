/**
 * NEXUS CEREBRO Dashboard Page
 * Main interface after login
 */
import { useEffect, useState } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';
import { useAuth } from '../context/AuthContext';
import { useEventStore } from '../stores/eventStore';
import { useInteractionStore, eventToInteraction } from '../stores/interactionStore';
import { api } from '../api/client';
import { Header } from '../components/Header';
import { EventStream } from '../components/EventStream';
import { InteractionModal } from '../components/InteractionModal';
import type { StateSnapshot, PendingInteraction } from '../types/api';

export function Dashboard() {
  const { user } = useAuth();
  const { status: wsStatus } = useWebSocket({
    onConnect: () => console.log('[Dashboard] WebSocket connected'),
    onDisconnect: () => console.log('[Dashboard] WebSocket disconnected'),
  });

  const events = useEventStore((s) => s.events);
  const addInteraction = useInteractionStore((s) => s.addInteraction);
  const pending = useInteractionStore((s) => s.pending);
  const fetchPending = useInteractionStore((s) => s.fetchPending);

  const [activeInteraction, setActiveInteraction] = useState<PendingInteraction | null>(null);
  const [snapshot, setSnapshot] = useState<StateSnapshot | null>(null);
  const [snapshotLoading, setSnapshotLoading] = useState(true);
  const [snapshotError, setSnapshotError] = useState<string | null>(null);

  // Load state snapshot on mount (F5 recovery)
  useEffect(() => {
    const loadSnapshot = async () => {
      setSnapshotLoading(true);
      setSnapshotError(null);
      try {
        const data = await api.get<StateSnapshot>('/api/state/snapshot');
        setSnapshot(data);

        // Load pending interactions from snapshot
        data.pending_interactions.forEach((i) => addInteraction(i));
      } catch (error) {
        console.error('[Dashboard] Failed to load snapshot:', error);
        setSnapshotError(error instanceof Error ? error.message : 'Failed to load state');
      } finally {
        setSnapshotLoading(false);
      }
    };

    loadSnapshot();
    fetchPending();
  }, [fetchPending, addInteraction]);

  // Watch for interaction events from WebSocket
  useEffect(() => {
    // Get the latest interaction events
    const interactionEvents = events.filter((e) =>
      e.event_type.startsWith('interaction.') &&
      e.event_type !== 'interaction.progress' &&
      e.event_type !== 'interaction.announce'
    );

    // Convert and add new interactions
    interactionEvents.forEach((event) => {
      const interaction = eventToInteraction(event);
      if (interaction && !pending.find((p) => p.request_id === interaction.request_id)) {
        addInteraction(interaction);
      }
    });
  }, [events, pending, addInteraction]);

  // Show first pending interaction automatically
  useEffect(() => {
    if (pending.length > 0 && !activeInteraction) {
      setActiveInteraction(pending[0]);
    }
  }, [pending, activeInteraction]);

  return (
    <div className="min-h-screen bg-nexus-darker flex flex-col">
      <Header wsStatus={wsStatus} />

      <main className="flex-1 max-w-7xl mx-auto px-4 py-6 w-full">
        {/* Status Bar */}
        <div className="flex flex-wrap items-center gap-4 mb-6 text-sm">
          {user && (
            <span className="text-gray-400">
              Tenant: <span className="text-white">{user.tenant_id}</span>
            </span>
          )}
          {snapshot?.phase && (
            <span className="text-gray-400">
              Phase: <span className="text-primary">{String(snapshot.phase.current_phase || 'IDLE')}</span>
            </span>
          )}
          {pending.length > 0 && (
            <span className="px-2 py-0.5 rounded bg-warning/20 text-warning">
              {pending.length} pending interaction{pending.length > 1 ? 's' : ''}
            </span>
          )}
        </div>

        {/* Snapshot Loading/Error */}
        {snapshotLoading && (
          <div className="bg-nexus-dark rounded-lg border border-gray-700 p-4 mb-6">
            <div className="flex items-center gap-2 text-gray-400">
              <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Loading state...
            </div>
          </div>
        )}

        {snapshotError && (
          <div className="bg-danger/20 border border-danger/50 rounded-lg p-4 mb-6">
            <p className="text-danger">{snapshotError}</p>
            <p className="text-sm text-gray-400 mt-1">
              The system will still receive live events via WebSocket.
            </p>
          </div>
        )}

        {/* Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Event Stream */}
          <EventStream />

          {/* Pending Interactions Panel */}
          <div className="bg-nexus-dark rounded-lg border border-gray-700 h-96 flex flex-col">
            <div className="px-4 py-3 border-b border-gray-700">
              <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                <span className="text-warning">?</span>
                Pending Interactions
              </h2>
            </div>

            <div className="flex-1 overflow-y-auto p-4">
              {pending.length === 0 ? (
                <div className="flex items-center justify-center h-full text-gray-500 italic">
                  No pending interactions
                </div>
              ) : (
                <div className="space-y-2">
                  {pending.map((interaction) => (
                    <button
                      key={interaction.request_id}
                      onClick={() => setActiveInteraction(interaction)}
                      className="w-full text-left p-4 rounded-lg bg-nexus-darker
                                 hover:bg-gray-700 transition-colors group"
                    >
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-warning font-medium text-sm">
                          [{interaction.interaction_type.toUpperCase()}]
                        </span>
                        <span className="text-xs text-gray-500">
                          {interaction.request_id}
                        </span>
                      </div>
                      <p className="text-gray-300 group-hover:text-white transition-colors">
                        {interaction.prompt.length > 80
                          ? interaction.prompt.slice(0, 80) + '...'
                          : interaction.prompt}
                      </p>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Phase Info (if available) */}
        {snapshot?.phase && !snapshotLoading && (
          <div className="mt-6 bg-nexus-dark rounded-lg border border-gray-700 p-4">
            <h3 className="text-sm font-medium text-gray-400 mb-2">Current State</h3>
            <pre className="text-sm text-gray-300 overflow-x-auto font-mono">
              {JSON.stringify(snapshot.phase, null, 2)}
            </pre>
          </div>
        )}
      </main>

      {/* Interaction Modal */}
      {activeInteraction && (
        <InteractionModal
          interaction={activeInteraction}
          onClose={() => setActiveInteraction(null)}
        />
      )}
    </div>
  );
}
