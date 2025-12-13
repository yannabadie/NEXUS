"use client";

import { useEffect, useState } from "react";
import { getSelfAwareness, type SelfAwareness } from "@/lib/api";
import { AGENT_COLORS } from "@/lib/design-tokens";

// ============================================================================
// Agent Card Component
// ============================================================================

function AgentProfileCard({
    name,
    type,
    status,
    specialization,
}: {
    name: string;
    type: "gemini" | "claude" | "spawned";
    status: "active" | "idle" | "offline";
    specialization?: string[];
}) {
    const colors = AGENT_COLORS[type];

    return (
        <div className="bg-zinc-800/50 border border-zinc-700 rounded-xl p-4 hover:border-zinc-600 transition-all">
            <div className="flex items-center gap-3 mb-3">
                <div className={`w-12 h-12 rounded-lg bg-gradient-to-br ${colors.gradient} flex items-center justify-center`}>
                    <span className="text-white font-bold text-lg">{name[0].toUpperCase()}</span>
                </div>
                <div className="flex-1">
                    <div className="font-medium text-white">{name}</div>
                    <div className="text-xs text-zinc-400 capitalize">{type} Agent</div>
                </div>
                <div className={`w-3 h-3 rounded-full ${status === 'active' ? 'bg-emerald-500 animate-pulse' :
                        status === 'idle' ? 'bg-yellow-500' : 'bg-zinc-500'
                    }`} />
            </div>

            {specialization && specialization.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-2">
                    {specialization.map((spec) => (
                        <span
                            key={spec}
                            className="px-2 py-0.5 bg-zinc-700/50 rounded text-xs text-zinc-400"
                        >
                            {spec}
                        </span>
                    ))}
                </div>
            )}
        </div>
    );
}

// ============================================================================
// Main Agents Page
// ============================================================================

export default function AgentsPage() {
    const [selfAwareness, setSelfAwareness] = useState<SelfAwareness | null>(null);
    const [loading, setLoading] = useState(true);

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

    // Extract spawned agents
    const spawnedAgents = selfAwareness?.active_agents?.filter(
        (a) => !["gemini", "claude"].includes(a.toLowerCase())
    ) || [];

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
                <button
                    className="px-4 py-2 bg-violet-600 hover:bg-violet-700 rounded-lg text-sm font-medium text-white transition-colors flex items-center gap-2"
                    onClick={() => alert("Spawn agent coming soon!")}
                >
                    <span>✨</span>
                    <span>Spawn Agent</span>
                </button>
            </div>

            {/* Core Agents */}
            <div>
                <h2 className="text-sm font-medium text-zinc-400 mb-3">Core Agents</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <AgentProfileCard
                        name="Gemini"
                        type="gemini"
                        status="active"
                        specialization={["Research", "Analysis", "Web Search"]}
                    />
                    <AgentProfileCard
                        name="Claude"
                        type="claude"
                        status="active"
                        specialization={["Coding", "Creativity", "Security"]}
                    />
                </div>
            </div>

            {/* Spawned Agents */}
            <div>
                <h2 className="text-sm font-medium text-zinc-400 mb-3">
                    Spawned Agents ({spawnedAgents.length})
                </h2>
                {spawnedAgents.length === 0 ? (
                    <div className="bg-zinc-800/30 border border-dashed border-zinc-700 rounded-xl p-8 text-center">
                        <div className="text-3xl mb-2 opacity-30">🤖</div>
                        <div className="text-zinc-500">No spawned agents yet</div>
                        <div className="text-xs text-zinc-600 mt-1">
                            Use /spawn &lt;role&gt; to create specialized agents
                        </div>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {spawnedAgents.map((agent) => (
                            <AgentProfileCard
                                key={agent}
                                name={agent}
                                type="spawned"
                                status="idle"
                            />
                        ))}
                    </div>
                )}
            </div>

            {/* Agent Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-4">
                    <div className="text-xs text-zinc-500 mb-1">Total Agents</div>
                    <div className="text-2xl font-bold text-white">
                        {2 + spawnedAgents.length}
                    </div>
                </div>
                <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-4">
                    <div className="text-xs text-zinc-500 mb-1">Active Now</div>
                    <div className="text-2xl font-bold text-emerald-400">2</div>
                </div>
                <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-4">
                    <div className="text-xs text-zinc-500 mb-1">Spawned</div>
                    <div className="text-2xl font-bold text-violet-400">
                        {spawnedAgents.length}
                    </div>
                </div>
            </div>
        </div>
    );
}
