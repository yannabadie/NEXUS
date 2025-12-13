"use client";

import { AGENT_COLORS } from "@/lib/design-tokens";

// ============================================================================
// Types
// ============================================================================

export interface AgentProfile {
    id: string;
    name: string;
    type: "gemini" | "claude" | "spawned";
    status: "active" | "idle" | "offline";
    role?: string;
    specializations?: string[];
    dylanScore?: number;
    tasksCompleted?: number;
    tokensUsed?: number;
    successRate?: number;
    birthDate?: Date;
    parentAgent?: string;
}

interface AgentProfileCardProps {
    agent: AgentProfile;
    variant?: "compact" | "detailed";
    className?: string;
    onClick?: () => void;
}

// ============================================================================
// Status Indicator
// ============================================================================

function StatusIndicator({ status }: { status: AgentProfile["status"] }) {
    const styles = {
        active: "bg-emerald-500 animate-pulse",
        idle: "bg-yellow-500",
        offline: "bg-zinc-500",
    };

    return (
        <div className="flex items-center gap-1.5">
            <div className={`w-2 h-2 rounded-full ${styles[status]}`} />
            <span className="text-xs text-zinc-400 capitalize">{status}</span>
        </div>
    );
}

// ============================================================================
// DyLAN Score Bar
// ============================================================================

function DyLANScoreBar({ score }: { score: number }) {
    const percentage = score * 100;

    const getColor = (s: number) => {
        if (s >= 80) return "from-emerald-500 to-emerald-400";
        if (s >= 60) return "from-yellow-500 to-yellow-400";
        return "from-orange-500 to-orange-400";
    };

    return (
        <div className="space-y-1">
            <div className="flex items-center justify-between text-xs">
                <span className="text-zinc-500">DyLAN Score</span>
                <span className="text-zinc-300 font-medium">{(score * 100).toFixed(0)}%</span>
            </div>
            <div className="h-1.5 bg-zinc-800 rounded-full overflow-hidden">
                <div
                    className={`h-full bg-gradient-to-r ${getColor(percentage)} transition-all`}
                    style={{ width: `${percentage}%` }}
                />
            </div>
        </div>
    );
}

// ============================================================================
// Stat Item
// ============================================================================

function StatItem({ label, value, icon }: { label: string; value: string | number; icon: string }) {
    return (
        <div className="text-center">
            <div className="text-xs text-zinc-500 mb-0.5">{icon} {label}</div>
            <div className="text-sm font-medium text-zinc-200">{value}</div>
        </div>
    );
}

// ============================================================================
// Main Agent Profile Card Component
// ============================================================================

export function AgentProfileCard({
    agent,
    variant = "compact",
    className = "",
    onClick,
}: AgentProfileCardProps) {
    const colors = AGENT_COLORS[agent.type];

    if (variant === "compact") {
        return (
            <div
                className={`
          bg-zinc-800/50 border border-zinc-700 rounded-lg p-3 
          flex items-center gap-3 hover:border-zinc-600 transition-all cursor-pointer
          ${className}
        `}
                onClick={onClick}
            >
                {/* Avatar */}
                <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${colors.gradient} flex items-center justify-center flex-shrink-0`}>
                    <span className="text-white font-bold text-sm">{agent.name[0].toUpperCase()}</span>
                </div>

                {/* Info */}
                <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                        <span className="font-medium text-zinc-200">{agent.name}</span>
                        {agent.role && (
                            <span className="px-1.5 py-0.5 bg-zinc-700/50 rounded text-xs text-zinc-400">
                                {agent.role}
                            </span>
                        )}
                    </div>
                    <div className="text-xs text-zinc-400 capitalize">{agent.type}</div>
                </div>

                {/* Status */}
                <StatusIndicator status={agent.status} />
            </div>
        );
    }

    // Detailed variant
    return (
        <div
            className={`
        bg-zinc-800/50 border border-zinc-700 rounded-xl overflow-hidden
        hover:border-zinc-600 transition-all
        ${className}
      `}
        >
            {/* Header */}
            <div className={`h-16 bg-gradient-to-br ${colors.gradient} relative`}>
                <div className="absolute -bottom-6 left-4">
                    <div className="w-12 h-12 rounded-xl bg-zinc-900 border-4 border-zinc-800 flex items-center justify-center">
                        <span className="text-xl font-bold text-white">{agent.name[0].toUpperCase()}</span>
                    </div>
                </div>
            </div>

            {/* Content */}
            <div className="pt-8 p-4">
                {/* Name & Status */}
                <div className="flex items-center justify-between mb-3">
                    <div>
                        <h3 className="font-medium text-lg text-white">{agent.name}</h3>
                        <div className="text-sm text-zinc-400 capitalize">{agent.type} Agent</div>
                    </div>
                    <StatusIndicator status={agent.status} />
                </div>

                {/* Role */}
                {agent.role && (
                    <div className="mb-3">
                        <span className="px-2 py-1 bg-violet-500/20 text-violet-300 rounded text-sm">
                            {agent.role}
                        </span>
                    </div>
                )}

                {/* Specializations */}
                {agent.specializations && agent.specializations.length > 0 && (
                    <div className="flex flex-wrap gap-1 mb-4">
                        {agent.specializations.map((spec) => (
                            <span
                                key={spec}
                                className="px-2 py-0.5 bg-zinc-700/50 rounded text-xs text-zinc-400"
                            >
                                {spec}
                            </span>
                        ))}
                    </div>
                )}

                {/* DyLAN Score */}
                {agent.dylanScore !== undefined && (
                    <div className="mb-4">
                        <DyLANScoreBar score={agent.dylanScore} />
                    </div>
                )}

                {/* Stats */}
                <div className="grid grid-cols-3 gap-2 pt-3 border-t border-zinc-700">
                    <StatItem
                        label="Tasks"
                        value={agent.tasksCompleted || 0}
                        icon="✓"
                    />
                    <StatItem
                        label="Tokens"
                        value={agent.tokensUsed ? `${(agent.tokensUsed / 1000).toFixed(0)}K` : "0"}
                        icon="🔤"
                    />
                    <StatItem
                        label="Success"
                        value={agent.successRate ? `${(agent.successRate * 100).toFixed(0)}%` : "-"}
                        icon="📈"
                    />
                </div>

                {/* Parent Agent (for spawned) */}
                {agent.parentAgent && (
                    <div className="mt-3 pt-3 border-t border-zinc-700 text-xs text-zinc-500">
                        Spawned by: <span className="text-zinc-400">{agent.parentAgent}</span>
                    </div>
                )}
            </div>
        </div>
    );
}

export default AgentProfileCard;
