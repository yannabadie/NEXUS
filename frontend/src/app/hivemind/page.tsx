"use client";

import { useEffect, useState } from "react";
import { getOrchestrationState, type OrchestrationState } from "@/lib/api";
import { HiveMindTracker } from "@/components/HiveMindTracker";
import { AgentExchanges } from "@/components/AgentExchanges";
import { DebateViewer, type DebateTurn } from "@/components/DebateViewer";
import { ExecutionMonitor, type ExecutionStep } from "@/components/ExecutionMonitor";

// ============================================================================
// Demo Data for Preview
// ============================================================================

const DEMO_DEBATE_TURNS: DebateTurn[] = [
    {
        id: "1",
        turnNumber: 1,
        agent: "Gemini",
        position: "SUPPORT",
        argument: "I propose we use a modular approach with separate handlers for each file type.",
        timestamp: new Date(),
    },
    {
        id: "2",
        turnNumber: 2,
        agent: "Claude",
        position: "OPPOSE",
        argument: "A unified parser would be more maintainable and reduce code duplication.",
        targetPoint: "modular approach",
        timestamp: new Date(),
    },
    {
        id: "3",
        turnNumber: 3,
        agent: "Gemini",
        position: "CONCEDE",
        argument: "You raise a valid point about maintainability.",
        concession: "Unified parser can work if we still support extension points.",
        timestamp: new Date(),
    },
];

const DEMO_EXECUTION_STEPS: ExecutionStep[] = [
    { id: "1", name: "Analyze codebase", agent: "Gemini", status: "success", duration: 2300, tokensUsed: 1500 },
    { id: "2", name: "Generate architecture", agent: "Claude", status: "success", duration: 1800, tokensUsed: 2200 },
    { id: "3", name: "Write implementation", agent: "Gemini", status: "running", tokensUsed: 500 },
    { id: "4", name: "Review code", agent: "Claude", status: "pending" },
    { id: "5", name: "Run tests", agent: "Gemini", status: "pending" },
];

// ============================================================================
// Main HiveMind Page
// ============================================================================

export default function HiveMindPage() {
    const [orchestration, setOrchestration] = useState<OrchestrationState | null>(null);
    const [showDemo, setShowDemo] = useState(true);
    const [activeTab, setActiveTab] = useState<"overview" | "debate" | "execution">("overview");

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
                <div className="flex items-center gap-4">
                    <label className="flex items-center gap-2 text-sm text-zinc-400">
                        <input
                            type="checkbox"
                            checked={showDemo}
                            onChange={(e) => setShowDemo(e.target.checked)}
                            className="rounded"
                        />
                        Show demo data
                    </label>
                    <span className="px-3 py-1 bg-violet-600/20 border border-violet-600 rounded-full text-sm text-violet-300">
                        Phase {orchestration?.hive_mind_phase || "-"}
                    </span>
                </div>
            </div>

            {/* HiveMind Phase Tracker */}
            <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-6">
                <h2 className="text-sm font-medium text-zinc-400 mb-4">Pipeline Progress</h2>
                <HiveMindTracker currentPhase={orchestration?.hive_mind_phase || null} />
            </div>

            {/* Tab Navigation */}
            <div className="flex items-center gap-2 border-b border-zinc-800">
                {[
                    { id: "overview", label: "Overview", icon: "📋" },
                    { id: "debate", label: "Debate", icon: "⚔️" },
                    { id: "execution", label: "Execution", icon: "⚡" },
                ].map((tab) => (
                    <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id as typeof activeTab)}
                        className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${activeTab === tab.id
                                ? "border-violet-500 text-violet-300"
                                : "border-transparent text-zinc-400 hover:text-zinc-200"
                            }`}
                    >
                        {tab.icon} {tab.label}
                    </button>
                ))}
            </div>

            {/* Tab Content */}
            {activeTab === "overview" && (
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
            )}

            {activeTab === "debate" && (
                <DebateViewer
                    topic="Task Approach Strategy"
                    turns={showDemo ? DEMO_DEBATE_TURNS : []}
                    consensusScore={showDemo ? 65 : 0}
                    isLive={orchestration?.hive_mind_phase === 2}
                />
            )}

            {activeTab === "execution" && (
                <ExecutionMonitor
                    steps={showDemo ? DEMO_EXECUTION_STEPS : []}
                    currentStepIndex={showDemo ? 2 : -1}
                    isPaused={false}
                    onPause={() => console.log("Pause clicked")}
                    onResume={() => console.log("Resume clicked")}
                />
            )}

            {/* Live Agent Exchanges */}
            <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-6">
                <h2 className="text-sm font-medium text-zinc-400 mb-4">Live Agent Exchanges</h2>
                <AgentExchanges className="max-h-[400px]" />
            </div>
        </div>
    );
}
