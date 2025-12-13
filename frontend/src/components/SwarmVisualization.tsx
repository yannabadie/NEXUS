"use client";

import { useState, useMemo } from "react";

// ============================================================================
// Swarm Mode Types
// ============================================================================

export type SwarmMode =
    | "PARALLEL"
    | "SEQUENTIAL"
    | "LEAD_SUPPORT"
    | "PING_PONG"
    | "SPECIALIST"
    | "RED_BLUE"
    | null;

interface SwarmVisualizationProps {
    mode: SwarmMode;
    agents?: string[];
    progress?: number;
    className?: string;
}

// ============================================================================
// Mode Descriptions & Icons
// ============================================================================

const MODE_CONFIG: Record<string, { icon: string; description: string; color: string }> = {
    PARALLEL: {
        icon: "⚡",
        description: "Agents work simultaneously, results merged",
        color: "from-blue-500 to-cyan-500",
    },
    SEQUENTIAL: {
        icon: "📋",
        description: "Chain of responsibility (A → B → C)",
        color: "from-green-500 to-emerald-500",
    },
    LEAD_SUPPORT: {
        icon: "👑",
        description: "Leader directs, supporters execute",
        color: "from-amber-500 to-orange-500",
    },
    PING_PONG: {
        icon: "🏓",
        description: "Rapid alternation until convergence",
        color: "from-violet-500 to-purple-500",
    },
    SPECIALIST: {
        icon: "🎯",
        description: "Single expert handles everything",
        color: "from-rose-500 to-pink-500",
    },
    RED_BLUE: {
        icon: "⚔️",
        description: "Adversarial: Propose vs Critique",
        color: "from-red-500 to-blue-500",
    },
};

// ============================================================================
// Swarm Visualization Component
// ============================================================================

export function SwarmVisualization({
    mode,
    agents = ["Gemini", "Claude"],
    progress = 0,
    className = ""
}: SwarmVisualizationProps) {
    const config = mode ? MODE_CONFIG[mode] : null;

    if (!mode) {
        return (
            <div className={`bg-zinc-800/30 border border-zinc-700/50 rounded-lg p-6 text-center ${className}`}>
                <div className="text-4xl mb-2 opacity-30">🔄</div>
                <div className="text-zinc-500 text-sm">No active Swarm</div>
                <div className="text-zinc-600 text-xs mt-1">Swarm activates for complex tasks</div>
            </div>
        );
    }

    return (
        <div className={`bg-zinc-800/50 border border-zinc-700 rounded-lg overflow-hidden ${className}`}>
            {/* Mode Header */}
            <div className={`bg-gradient-to-r ${config?.color} p-4`}>
                <div className="flex items-center gap-3">
                    <span className="text-3xl">{config?.icon}</span>
                    <div>
                        <div className="text-white font-bold text-lg">{mode}</div>
                        <div className="text-white/80 text-sm">{config?.description}</div>
                    </div>
                </div>
            </div>

            {/* Agent Participation */}
            <div className="p-4 space-y-4">
                {/* Agents Grid */}
                <div className="flex gap-2 flex-wrap">
                    {agents.map((agent, idx) => (
                        <div
                            key={agent}
                            className="flex items-center gap-2 bg-zinc-700/50 rounded-full px-3 py-1"
                        >
                            <div className={`w-2 h-2 rounded-full ${mode === "RED_BLUE"
                                    ? idx === 0 ? "bg-red-500" : "bg-blue-500"
                                    : mode === "LEAD_SUPPORT" && idx === 0
                                        ? "bg-amber-500"
                                        : "bg-emerald-500"
                                } animate-pulse`} />
                            <span className="text-zinc-300 text-sm">{agent}</span>
                        </div>
                    ))}
                </div>

                {/* Progress Bar */}
                {progress > 0 && (
                    <div>
                        <div className="flex justify-between text-xs text-zinc-500 mb-1">
                            <span>Progress</span>
                            <span>{progress}%</span>
                        </div>
                        <div className="h-2 bg-zinc-700 rounded-full overflow-hidden">
                            <div
                                className={`h-full bg-gradient-to-r ${config?.color} transition-all duration-500`}
                                style={{ width: `${progress}%` }}
                            />
                        </div>
                    </div>
                )}

                {/* Mode-specific visualization */}
                {mode === "PING_PONG" && (
                    <div className="flex items-center justify-center gap-2 py-2">
                        <div className="w-8 h-8 bg-blue-500/20 border border-blue-500 rounded-full flex items-center justify-center animate-ping-slow">
                            G
                        </div>
                        <div className="text-zinc-400">↔</div>
                        <div className="w-8 h-8 bg-orange-500/20 border border-orange-500 rounded-full flex items-center justify-center animate-ping-slow" style={{ animationDelay: "0.5s" }}>
                            C
                        </div>
                    </div>
                )}

                {mode === "SEQUENTIAL" && (
                    <div className="flex items-center justify-center gap-1 py-2">
                        {agents.map((agent, idx) => (
                            <div key={agent} className="flex items-center">
                                <div className="w-6 h-6 bg-green-500/20 border border-green-500 rounded text-xs flex items-center justify-center text-green-400">
                                    {agent[0]}
                                </div>
                                {idx < agents.length - 1 && (
                                    <span className="text-green-500 mx-1">→</span>
                                )}
                            </div>
                        ))}
                    </div>
                )}

                {mode === "RED_BLUE" && (
                    <div className="flex items-center justify-center gap-4 py-2">
                        <div className="text-center">
                            <div className="w-10 h-10 bg-red-500/20 border border-red-500 rounded-lg flex items-center justify-center text-red-400 mb-1">
                                ⚔️
                            </div>
                            <div className="text-xs text-red-400">Propose</div>
                        </div>
                        <div className="text-zinc-500 text-xl">vs</div>
                        <div className="text-center">
                            <div className="w-10 h-10 bg-blue-500/20 border border-blue-500 rounded-lg flex items-center justify-center text-blue-400 mb-1">
                                🛡️
                            </div>
                            <div className="text-xs text-blue-400">Critique</div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

export default SwarmVisualization;
