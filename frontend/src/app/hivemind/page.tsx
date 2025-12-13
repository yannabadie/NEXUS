"use client";

import { useEffect, useState } from "react";
import { getOrchestrationState, type OrchestrationState } from "@/lib/api";
import { HiveMindTracker } from "@/components/HiveMindTracker";
import { AgentExchanges } from "@/components/AgentExchanges";

// ============================================================================
// Phase Details (placeholder - will be populated by WebSocket events)
// ============================================================================

interface PhaseDetail {
    id: number;
    name: string;
    status: 'pending' | 'active' | 'complete' | 'error';
    details?: string;
    duration?: number;
}

export default function HiveMindPage() {
    const [orchestration, setOrchestration] = useState<OrchestrationState | null>(null);
    const [phases] = useState<PhaseDetail[]>([]);

    useEffect(() => {
        async function fetchData() {
            const { data } = await getOrchestrationState();
            if (data) setOrchestration(data);
        }

        fetchData();
        const interval = setInterval(fetchData, 2000);
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-white">🐝 HiveMind Pipeline</h1>
                    <p className="text-sm text-zinc-400">
                        7-phase collaborative intelligence orchestration
                    </p>
                </div>
                <div className="flex items-center gap-2">
                    <span className="text-sm text-zinc-500">Current Phase:</span>
                    <span className="px-3 py-1 bg-violet-600/20 border border-violet-600 rounded-full text-sm text-violet-300">
                        Phase {orchestration?.hive_mind_phase || "-"}
                    </span>
                </div>
            </div>

            {/* HiveMind Phase Tracker */}
            <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-6">
                <h2 className="text-sm font-medium text-zinc-400 mb-4">Pipeline Progress</h2>
                <HiveMindTracker
                    currentPhase={orchestration?.hive_mind_phase || null}
                    phases={phases}
                />
            </div>

            {/* Phase Descriptions */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {[
                    { id: 1, name: "Analysis", icon: "🔍", desc: "Independent task analysis by each agent" },
                    { id: 2, name: "Debate", icon: "⚔️", desc: "Strategic debate to resolve disagreements" },
                    { id: 3, name: "Architecture", icon: "📐", desc: "Generate execution architecture" },
                    { id: 4, name: "Execution", icon: "⚡", desc: "Execute the agreed-upon plan" },
                    { id: 5, name: "Diagnosis", icon: "🔬", desc: "Analyze failures if execution fails" },
                    { id: 6, name: "Retry", icon: "🔄", desc: "Adaptive retry with lessons learned" },
                    { id: 7, name: "Consolidation", icon: "📦", desc: "Archive knowledge for future tasks" },
                ].map((phase) => (
                    <div
                        key={phase.id}
                        className={`bg-zinc-800/50 border rounded-lg p-4 transition-all ${orchestration?.hive_mind_phase === phase.id
                                ? "border-violet-500 bg-violet-600/10"
                                : "border-zinc-700"
                            }`}
                    >
                        <div className="flex items-center gap-2 mb-2">
                            <span className="text-xl">{phase.icon}</span>
                            <span className="font-medium text-white">Phase {phase.id}: {phase.name}</span>
                        </div>
                        <p className="text-sm text-zinc-400">{phase.desc}</p>
                    </div>
                ))}
            </div>

            {/* Live Agent Exchanges */}
            <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-6">
                <h2 className="text-sm font-medium text-zinc-400 mb-4">Live Agent Exchanges</h2>
                <AgentExchanges className="max-h-[400px]" />
            </div>
        </div>
    );
}
