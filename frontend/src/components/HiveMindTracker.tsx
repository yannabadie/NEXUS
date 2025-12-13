"use client";

import { useState } from "react";
import { PHASE_COLORS } from "@/lib/design-tokens";

// ============================================================================
// Types
// ============================================================================

export interface PhaseData {
    id: number;
    name: string;
    key: keyof typeof PHASE_COLORS;
    status: 'pending' | 'active' | 'complete' | 'error' | 'skipped';
    startTime?: string;
    endTime?: string;
    duration?: number;
    agents?: { name: string; contribution: number }[];
    details?: string;
    issues?: string[];
}

interface HiveMindTrackerProps {
    currentPhase: number | null;
    phases?: Partial<PhaseData>[];
    className?: string;
}

// ============================================================================
// Default Phases
// ============================================================================

const DEFAULT_PHASES: PhaseData[] = [
    { id: 1, name: "Analysis", key: "analysis", status: "pending" },
    { id: 2, name: "Debate", key: "debate", status: "pending" },
    { id: 3, name: "Architecture", key: "architecture", status: "pending" },
    { id: 4, name: "Execution", key: "execution", status: "pending" },
    { id: 5, name: "Diagnosis", key: "diagnosis", status: "pending" },
    { id: 6, name: "Retry", key: "retry", status: "pending" },
    { id: 7, name: "Consolidation", key: "consolidation", status: "pending" },
];

// ============================================================================
// Phase Card Component
// ============================================================================

function PhaseCard({
    phase,
    isActive,
    isComplete,
    isExpanded,
    onToggle,
}: {
    phase: PhaseData;
    isActive: boolean;
    isComplete: boolean;
    isExpanded: boolean;
    onToggle: () => void;
}) {
    const colors = PHASE_COLORS[phase.key];

    return (
        <div
            className={`
        relative flex-1 cursor-pointer transition-all duration-300
        ${isExpanded ? "flex-[2]" : ""}
      `}
            onClick={onToggle}
        >
            {/* Main Card */}
            <div
                className={`
          p-3 rounded-lg text-center transition-all duration-300
          ${isActive
                        ? `${colors.bg} text-white scale-105 shadow-lg ring-2 ring-white/20`
                        : isComplete
                            ? "bg-zinc-700 text-zinc-300"
                            : phase.status === 'error'
                                ? "bg-red-900/30 text-red-400 border border-red-600"
                                : phase.status === 'skipped'
                                    ? "bg-zinc-800/50 text-zinc-500 opacity-50"
                                    : "bg-zinc-800 text-zinc-500"
                    }
        `}
            >
                {/* Phase Icon */}
                <div className="text-xl mb-1">{colors.icon}</div>

                {/* Phase Name */}
                <div className="text-xs font-medium hidden md:block">{phase.name}</div>

                {/* Status Indicator */}
                {isActive && (
                    <div className="absolute -bottom-1 left-1/2 -translate-x-1/2">
                        <div className="w-2 h-2 bg-white rounded-full animate-pulse" />
                    </div>
                )}

                {/* Complete Checkmark */}
                {isComplete && (
                    <div className="absolute -top-1 -right-1 w-4 h-4 bg-emerald-500 rounded-full flex items-center justify-center">
                        <span className="text-[8px]">✓</span>
                    </div>
                )}

                {/* Error Indicator */}
                {phase.status === 'error' && (
                    <div className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 rounded-full flex items-center justify-center">
                        <span className="text-[8px]">✕</span>
                    </div>
                )}
            </div>

            {/* Expanded Details */}
            {isExpanded && (
                <div className="mt-2 p-3 bg-zinc-800/80 rounded-lg border border-zinc-700 text-left">
                    {/* Timing */}
                    {phase.duration && (
                        <div className="flex items-center gap-2 text-xs text-zinc-400 mb-2">
                            <span>⏱</span>
                            <span>{(phase.duration / 1000).toFixed(1)}s</span>
                        </div>
                    )}

                    {/* Agent Contributions */}
                    {phase.agents && phase.agents.length > 0 && (
                        <div className="mb-2">
                            <div className="text-xs text-zinc-500 mb-1">Agents:</div>
                            <div className="flex gap-1">
                                {phase.agents.map((agent) => (
                                    <div
                                        key={agent.name}
                                        className="px-2 py-0.5 bg-zinc-700 rounded text-xs text-zinc-300"
                                        title={`${agent.contribution}% contribution`}
                                    >
                                        {agent.name}
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Details */}
                    {phase.details && (
                        <div className="text-xs text-zinc-400 line-clamp-2">
                            {phase.details}
                        </div>
                    )}

                    {/* Issues */}
                    {phase.issues && phase.issues.length > 0 && (
                        <div className="mt-2 space-y-1">
                            {phase.issues.map((issue, i) => (
                                <div key={i} className="flex items-start gap-1 text-xs text-red-400">
                                    <span>⚠</span>
                                    <span>{issue}</span>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

// ============================================================================
// HiveMind Tracker Component
// ============================================================================

export function HiveMindTracker({
    currentPhase,
    phases,
    className = "",
}: HiveMindTrackerProps) {
    const [expandedId, setExpandedId] = useState<number | null>(null);

    // Merge default phases with provided data
    const mergedPhases = DEFAULT_PHASES.map((defaultPhase) => {
        const provided = phases?.find((p) => p.id === defaultPhase.id);
        return { ...defaultPhase, ...provided };
    });

    return (
        <div className={`space-y-2 ${className}`}>
            {/* Phase Cards */}
            <div className="flex items-stretch gap-1">
                {mergedPhases.map((phase) => {
                    const isActive = phase.id === currentPhase;
                    const isComplete = currentPhase !== null && phase.id < currentPhase;
                    const isExpanded = expandedId === phase.id;

                    return (
                        <PhaseCard
                            key={phase.id}
                            phase={phase}
                            isActive={isActive}
                            isComplete={isComplete}
                            isExpanded={isExpanded}
                            onToggle={() => setExpandedId(isExpanded ? null : phase.id)}
                        />
                    );
                })}
            </div>

            {/* Progress Bar */}
            {currentPhase && (
                <div className="h-1 bg-zinc-800 rounded-full overflow-hidden">
                    <div
                        className="h-full bg-gradient-to-r from-violet-500 to-fuchsia-500 transition-all duration-500"
                        style={{ width: `${((currentPhase - 1) / 7) * 100}%` }}
                    />
                </div>
            )}

            {/* Legend (hidden on small screens) */}
            <div className="hidden lg:flex items-center justify-center gap-6 text-xs text-zinc-500">
                <div className="flex items-center gap-1">
                    <div className="w-2 h-2 bg-violet-500 rounded-full animate-pulse" />
                    <span>Active</span>
                </div>
                <div className="flex items-center gap-1">
                    <div className="w-2 h-2 bg-zinc-600 rounded-full" />
                    <span>Pending</span>
                </div>
                <div className="flex items-center gap-1">
                    <div className="w-2 h-2 bg-emerald-500 rounded-full" />
                    <span>Complete</span>
                </div>
                <div className="flex items-center gap-1">
                    <div className="w-2 h-2 bg-red-500 rounded-full" />
                    <span>Error</span>
                </div>
            </div>
        </div>
    );
}

export default HiveMindTracker;
