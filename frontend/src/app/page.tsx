"use client";

import { useEffect, useState } from "react";
import { useNexusWebSocket } from "@/hooks/useNexusWebSocket";
import {
  getSelfAwareness,
  getOrchestrationState,
  getBudgetStatus,
  type SelfAwareness,
  type OrchestrationState,
  type BudgetStatus
} from "@/lib/api";
import { SwarmVisualization, type SwarmMode } from "@/components/SwarmVisualization";
import { ChatPanel } from "@/components/ChatPanel";
import { AgentExchanges } from "@/components/AgentExchanges";
import { HiveMindTracker } from "@/components/HiveMindTracker";
import { AGENT_COLORS } from "@/lib/design-tokens";

// ============================================================================
// Status Panel Component
// ============================================================================

function StatusPanel({
  title,
  children,
  className = ""
}: {
  title: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={`bg-zinc-900/50 border border-zinc-800 rounded-xl p-4 ${className}`}>
      <h2 className="text-sm font-medium text-zinc-400 mb-3">{title}</h2>
      {children}
    </div>
  );
}

// ============================================================================
// Agent Card
// ============================================================================

function AgentCard({
  name,
  status,
  type
}: {
  name: string;
  status: "active" | "idle" | "spawned";
  type: "gemini" | "claude" | "spawned";
}) {
  const colors = AGENT_COLORS[type];

  const statusColors = {
    active: "bg-emerald-500",
    idle: "bg-zinc-500",
    spawned: "bg-violet-500",
  };

  return (
    <div className="bg-zinc-800/50 border border-zinc-700 rounded-lg p-3 flex items-center gap-3">
      <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${colors.gradient} flex items-center justify-center`}>
        <span className="text-white font-bold text-sm">{name[0].toUpperCase()}</span>
      </div>
      <div className="flex-1">
        <div className="font-medium text-zinc-200">{name}</div>
        <div className="text-xs text-zinc-400 capitalize">{type}</div>
      </div>
      <div className={`w-2 h-2 rounded-full ${statusColors[status]}`} />
    </div>
  );
}

// ============================================================================
// Helper: Extract phase number safely (API may return object or number)
// ============================================================================

function getPhaseNumber(phase: unknown): number | null {
  if (typeof phase === 'number') return phase;
  if (typeof phase === 'object' && phase !== null && 'iteration' in phase) {
    return (phase as { iteration?: number }).iteration || null;
  }
  return null;
}

// ============================================================================
// Main Dashboard Page
// ============================================================================

export default function Dashboard() {
  const { isConnected, lastMessage } = useNexusWebSocket();
  const [selfAwareness, setSelfAwareness] = useState<SelfAwareness | null>(null);
  const [orchestration, setOrchestration] = useState<OrchestrationState | null>(null);
  const [budget, setBudget] = useState<BudgetStatus | null>(null);
  const [loading, setLoading] = useState(true);

  // Fetch initial data
  useEffect(() => {
    async function fetchData() {
      const [selfRes, orchRes, budgetRes] = await Promise.all([
        getSelfAwareness(),
        getOrchestrationState(),
        getBudgetStatus(),
      ]);

      if (selfRes.data) setSelfAwareness(selfRes.data);
      if (orchRes.data) setOrchestration(orchRes.data);
      if (budgetRes.data) setBudget(budgetRes.data);
      setLoading(false);
    }

    fetchData();
    // Refresh every 5 seconds
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin w-8 h-8 border-2 border-violet-500 border-t-transparent rounded-full" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Connection Status Alert */}
      {!isConnected && (
        <div className="bg-amber-900/20 border border-amber-700 rounded-lg p-3 flex items-center gap-3">
          <span className="text-amber-500">⚠️</span>
          <span className="text-amber-200 text-sm">
            WebSocket disconnected. Trying to reconnect...
          </span>
        </div>
      )}

      {/* Top Row: FSM State + Budget */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatusPanel title="FSM State" className="md:col-span-2">
          <div className="flex items-center gap-4">
            <div className="text-3xl font-bold text-white">
              {orchestration?.fsm_state || "IDLE"}
            </div>
            {orchestration?.swarm_mode && (
              <div className="px-3 py-1 bg-violet-600/20 border border-violet-600 rounded-full text-sm text-violet-300">
                SWARM: {orchestration.swarm_mode.toUpperCase()}
              </div>
            )}
          </div>
        </StatusPanel>

        <StatusPanel title="Budget">
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-zinc-400">Spent</span>
              <span className="text-white font-mono">${budget?.spent?.toFixed(2) || "0.00"}</span>
            </div>
            <div className="h-2 bg-zinc-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-violet-500 to-fuchsia-500 transition-all"
                style={{ width: `${budget?.percentage || 0}%` }}
              />
            </div>
            <div className="text-xs text-zinc-500 text-right">
              {budget?.percentage?.toFixed(0) || 0}% of ${budget?.limit?.toFixed(0) || "0"}
            </div>
          </div>
        </StatusPanel>
      </div>

      {/* HiveMind Phase Tracker */}
      <StatusPanel title="HiveMind Pipeline">
        <HiveMindTracker currentPhase={getPhaseNumber(orchestration?.hive_mind_phase)} />
      </StatusPanel>

      {/* Middle Row: Swarm + Agents */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Swarm Visualization */}
        <StatusPanel title="Swarm Mode">
          <SwarmVisualization
            mode={(orchestration?.swarm_mode as SwarmMode) || null}
            agents={selfAwareness?.active_agents || ["Gemini", "Claude"]}
          />
        </StatusPanel>

        {/* Agents Grid */}
        <StatusPanel title="Active Agents">
          <div className="grid grid-cols-1 gap-3">
            <AgentCard name="Gemini" status="active" type="gemini" />
            <AgentCard name="Claude" status="active" type="claude" />
            {selfAwareness?.active_agents
              ?.filter((a) => !["gemini", "claude"].includes(a.toLowerCase()))
              .map((agent) => (
                <AgentCard key={agent} name={agent} status="spawned" type="spawned" />
              ))}
          </div>
        </StatusPanel>
      </div>

      {/* Chat Panel */}
      <ChatPanel className="min-h-[300px]" />

      {/* Agent Exchanges - Live Stream */}
      <AgentExchanges className="min-h-[300px]" />

      {/* Last Message Debug (collapsed by default) */}
      {lastMessage && (
        <details className="bg-zinc-900/50 border border-zinc-800 rounded-xl">
          <summary className="p-4 text-sm font-medium text-zinc-400 cursor-pointer hover:text-zinc-300">
            WebSocket Debug
          </summary>
          <pre className="text-xs text-zinc-400 overflow-auto max-h-32 bg-zinc-800 p-4 mx-4 mb-4 rounded">
            {JSON.stringify(lastMessage, null, 2)}
          </pre>
        </details>
      )}
    </div>
  );
}

