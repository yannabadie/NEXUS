"use client";

import { useEffect, useState } from "react";
import { getSelfAwareness, type SelfAwareness } from "@/lib/api";
import { AGENT_COLORS } from "@/lib/design-tokens";
import { AgentConstellation, type AgentNode, type AgentConnection } from "@/components/AgentConstellation";
import { AgentProfileCard, type AgentProfile } from "@/components/AgentProfileCard";

// ============================================================================
// Demo Data
// ============================================================================

const DEMO_AGENTS: AgentNode[] = [
    { id: "gemini", name: "Gemini", type: "gemini", status: "active", dylanScore: 0.85 },
    { id: "claude", name: "Claude", type: "claude", status: "active", dylanScore: 0.88 },
];

const DEMO_CONNECTIONS: AgentConnection[] = [
    { source: "gemini", target: "claude", type: "collaboration", strength: 0.9 },
];

// ============================================================================
// Main Agents Page
// ============================================================================

export default function AgentsPage() {
    const [selfAwareness, setSelfAwareness] = useState<SelfAwareness | null>(null);
    const [loading, setLoading] = useState(true);
    const [selectedAgentId, setSelectedAgentId] = useState<string | undefined>();
    const [viewMode, setViewMode] = useState<"grid" | "constellation">("constellation");

    useEffect(() => {
        async function fetchData() {
            const { data } = await getSelfAwareness();
            if (data) setSelfAwareness(data);
            setLoading(false);
        }

        fetchData();
        const interval = setInterval(fetchData, 5000);
        return () => clearInterval(interval);
    }, []);

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="animate-spin w-8 h-8 border-2 border-violet-500 border-t-transparent rounded-full" />
            </div>
        );
    }

    // Build agents list from API
    const spawnedAgents = selfAwareness?.active_agents?.filter(
        (a) => !["gemini", "claude"].includes(a.toLowerCase())
    ) || [];

    const allAgents: AgentNode[] = [
        ...DEMO_AGENTS,
        ...spawnedAgents.map((name) => ({
            id: name.toLowerCase(),
            name,
            type: "spawned" as const,
            status: "idle" as const,
        })),
    ];

    const allConnections: AgentConnection[] = [
        ...DEMO_CONNECTIONS,
        ...spawnedAgents.map((name) => ({
            source: "gemini",
            target: name.toLowerCase(),
            type: "spawned_by" as const,
            strength: 0.5,
        })),
    ];

    // Build profile for selected agent
    const selectedProfile: AgentProfile | undefined = selectedAgentId
        ? {
            id: selectedAgentId,
            name: allAgents.find((a) => a.id === selectedAgentId)?.name || selectedAgentId,
            type: allAgents.find((a) => a.id === selectedAgentId)?.type || "spawned",
            status: allAgents.find((a) => a.id === selectedAgentId)?.status || "idle",
            specializations: selectedAgentId === "gemini"
                ? ["Research", "Analysis", "Web Search"]
                : selectedAgentId === "claude"
                    ? ["Coding", "Creativity", "Security"]
                    : ["Specialized"],
            dylanScore: selectedAgentId === "gemini" ? 0.85 : selectedAgentId === "claude" ? 0.88 : 0.7,
            tasksCompleted: Math.floor(Math.random() * 50) + 10,
            tokensUsed: Math.floor(Math.random() * 100000) + 50000,
            successRate: 0.85 + Math.random() * 0.1,
        }
        : undefined;

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-white">🤖 Agent Registry</h1>
                    <p className="text-sm text-zinc-400">
                        Manage core and spawned agents
                    </p>
                </div>
                <div className="flex items-center gap-3">
                    {/* View Toggle */}
                    <div className="flex bg-zinc-800 rounded-lg p-1">
                        <button
                            onClick={() => setViewMode("constellation")}
                            className={`px-3 py-1 text-sm rounded transition-colors ${viewMode === "constellation"
                                    ? "bg-violet-600 text-white"
                                    : "text-zinc-400 hover:text-white"
                                }`}
                        >
                            🌐 Constellation
                        </button>
                        <button
                            onClick={() => setViewMode("grid")}
                            className={`px-3 py-1 text-sm rounded transition-colors ${viewMode === "grid"
                                    ? "bg-violet-600 text-white"
                                    : "text-zinc-400 hover:text-white"
                                }`}
                        >
                            📋 Grid
                        </button>
                    </div>

                    <button
                        className="px-4 py-2 bg-violet-600 hover:bg-violet-700 rounded-lg text-sm font-medium text-white transition-colors flex items-center gap-2"
                        onClick={() => alert("Spawn agent coming soon!")}
                    >
                        <span>✨</span>
                        <span>Spawn Agent</span>
                    </button>
                </div>
            </div>

            {/* Main Content */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Left: Visualization */}
                <div className="lg:col-span-2">
                    {viewMode === "constellation" ? (
                        <AgentConstellation
                            agents={allAgents}
                            connections={allConnections}
                            selectedAgentId={selectedAgentId}
                            onAgentSelect={setSelectedAgentId}
                        />
                    ) : (
                        <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-4">
                            <h3 className="text-sm font-medium text-zinc-400 mb-4">All Agents</h3>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                {allAgents.map((agent) => (
                                    <AgentProfileCard
                                        key={agent.id}
                                        agent={{
                                            id: agent.id,
                                            name: agent.name,
                                            type: agent.type,
                                            status: agent.status,
                                        }}
                                        variant="compact"
                                        onClick={() => setSelectedAgentId(agent.id)}
                                    />
                                ))}
                            </div>
                        </div>
                    )}
                </div>

                {/* Right: Selected Agent Details */}
                <div>
                    {selectedProfile ? (
                        <AgentProfileCard
                            agent={selectedProfile}
                            variant="detailed"
                        />
                    ) : (
                        <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-6 text-center">
                            <div className="text-3xl mb-2 opacity-30">🤖</div>
                            <div className="text-zinc-500">Select an agent to view details</div>
                        </div>
                    )}
                </div>
            </div>

            {/* Agent Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-4">
                    <div className="text-xs text-zinc-500 mb-1">Total Agents</div>
                    <div className="text-2xl font-bold text-white">
                        {allAgents.length}
                    </div>
                </div>
                <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-4">
                    <div className="text-xs text-zinc-500 mb-1">Active Now</div>
                    <div className="text-2xl font-bold text-emerald-400">
                        {allAgents.filter((a) => a.status === "active").length}
                    </div>
                </div>
                <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-4">
                    <div className="text-xs text-zinc-500 mb-1">Collaborations</div>
                    <div className="text-2xl font-bold text-violet-400">
                        {allConnections.length}
                    </div>
                </div>
            </div>
        </div>
    );
}
