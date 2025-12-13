"use client";

import { useState } from "react";
import { STATUS_COLORS } from "@/lib/design-tokens";

// ============================================================================
// Types
// ============================================================================

export interface ExecutionStep {
    id: string;
    name: string;
    description?: string;
    agent: string;
    status: "pending" | "running" | "success" | "warning" | "error" | "skipped";
    startTime?: Date;
    endTime?: Date;
    duration?: number;
    tokensUsed?: number;
    artifacts?: string[];
    issues?: string[];
    canRollback?: boolean;
}

interface ExecutionMonitorProps {
    steps?: ExecutionStep[];
    currentStepIndex?: number;
    isPaused?: boolean;
    onPause?: () => void;
    onResume?: () => void;
    onRollback?: (stepId: string) => void;
    className?: string;
}

// ============================================================================
// Step Status Icon
// ============================================================================

function StepStatusIcon({ status }: { status: ExecutionStep["status"] }) {
    switch (status) {
        case "pending":
            return <span className="text-zinc-500">○</span>;
        case "running":
            return <span className="text-blue-400 animate-pulse">●</span>;
        case "success":
            return <span className="text-emerald-400">✓</span>;
        case "warning":
            return <span className="text-yellow-400">⚠</span>;
        case "error":
            return <span className="text-red-400">✕</span>;
        case "skipped":
            return <span className="text-zinc-500">⊘</span>;
        default:
            return <span className="text-zinc-500">○</span>;
    }
}

// ============================================================================
// Execution Step Card
// ============================================================================

function ExecutionStepCard({
    step,
    isActive,
    onRollback,
}: {
    step: ExecutionStep;
    isActive: boolean;
    onRollback?: () => void;
}) {
    const [isExpanded, setIsExpanded] = useState(false);

    const statusStyles = {
        pending: "border-zinc-700 bg-zinc-800/30",
        running: "border-blue-500 bg-blue-500/10 ring-2 ring-blue-500/20",
        success: "border-emerald-500/50 bg-emerald-500/5",
        warning: "border-yellow-500/50 bg-yellow-500/5",
        error: "border-red-500/50 bg-red-500/5",
        skipped: "border-zinc-700 bg-zinc-800/20 opacity-50",
    };

    return (
        <div
            className={`
        relative border rounded-lg transition-all cursor-pointer
        ${statusStyles[step.status]}
        ${isActive ? "scale-[1.02]" : ""}
      `}
            onClick={() => setIsExpanded(!isExpanded)}
        >
            {/* Main Row */}
            <div className="p-3 flex items-center gap-3">
                {/* Status Icon */}
                <div className="text-lg">
                    <StepStatusIcon status={step.status} />
                </div>

                {/* Step Info */}
                <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                        <span className="font-medium text-zinc-200 truncate">{step.name}</span>
                        <span className="px-1.5 py-0.5 bg-zinc-700/50 rounded text-xs text-zinc-400">
                            {step.agent}
                        </span>
                    </div>
                    {step.description && (
                        <div className="text-xs text-zinc-500 truncate">{step.description}</div>
                    )}
                </div>

                {/* Duration */}
                {step.duration && (
                    <div className="text-xs text-zinc-500">
                        {(step.duration / 1000).toFixed(1)}s
                    </div>
                )}

                {/* Tokens */}
                {step.tokensUsed && (
                    <div className="text-xs text-zinc-500">
                        {(step.tokensUsed / 1000).toFixed(1)}K
                    </div>
                )}

                {/* Expand Arrow */}
                <span className={`text-zinc-500 transition-transform ${isExpanded ? "rotate-180" : ""}`}>
                    ▼
                </span>
            </div>

            {/* Expanded Content */}
            {isExpanded && (
                <div className="px-3 pb-3 border-t border-zinc-700/50 pt-3 space-y-2">
                    {/* Artifacts */}
                    {step.artifacts && step.artifacts.length > 0 && (
                        <div>
                            <div className="text-xs text-zinc-500 mb-1">Artifacts:</div>
                            <div className="flex flex-wrap gap-1">
                                {step.artifacts.map((art, i) => (
                                    <span
                                        key={i}
                                        className="px-2 py-0.5 bg-violet-500/20 text-violet-300 rounded text-xs"
                                    >
                                        📄 {art}
                                    </span>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Issues */}
                    {step.issues && step.issues.length > 0 && (
                        <div>
                            <div className="text-xs text-zinc-500 mb-1">Issues:</div>
                            {step.issues.map((issue, i) => (
                                <div key={i} className="text-xs text-red-400 flex items-start gap-1">
                                    <span>⚠</span>
                                    <span>{issue}</span>
                                </div>
                            ))}
                        </div>
                    )}

                    {/* Rollback Button */}
                    {step.canRollback && onRollback && (
                        <button
                            onClick={(e) => {
                                e.stopPropagation();
                                onRollback();
                            }}
                            className="px-3 py-1 bg-zinc-700 hover:bg-zinc-600 rounded text-xs text-zinc-300 transition-colors"
                        >
                            ⏪ Rollback to this step
                        </button>
                    )}
                </div>
            )}

            {/* Running Indicator */}
            {step.status === "running" && (
                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-zinc-800 overflow-hidden">
                    <div className="h-full bg-blue-500 animate-pulse w-1/2" />
                </div>
            )}
        </div>
    );
}

// ============================================================================
// Main Execution Monitor Component
// ============================================================================

export function ExecutionMonitor({
    steps = [],
    currentStepIndex = -1,
    isPaused = false,
    onPause,
    onResume,
    onRollback,
    className = "",
}: ExecutionMonitorProps) {
    const completedSteps = steps.filter((s) => s.status === "success").length;
    const failedSteps = steps.filter((s) => s.status === "error").length;
    const progress = steps.length > 0 ? (completedSteps / steps.length) * 100 : 0;

    return (
        <div className={`bg-zinc-900/50 border border-zinc-800 rounded-xl ${className}`}>
            {/* Header */}
            <div className="p-4 border-b border-zinc-800">
                <div className="flex items-center justify-between mb-3">
                    <div>
                        <h3 className="text-lg font-medium text-white flex items-center gap-2">
                            ⚡ Execution Monitor
                            {isPaused && (
                                <span className="px-2 py-0.5 bg-yellow-500/20 text-yellow-400 text-xs font-medium rounded-full">
                                    PAUSED
                                </span>
                            )}
                        </h3>
                        <p className="text-sm text-zinc-400">
                            {completedSteps}/{steps.length} steps complete
                            {failedSteps > 0 && <span className="text-red-400 ml-2">({failedSteps} failed)</span>}
                        </p>
                    </div>

                    {/* Control Buttons */}
                    <div className="flex items-center gap-2">
                        {isPaused ? (
                            <button
                                onClick={onResume}
                                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 rounded-lg text-sm font-medium text-white transition-colors flex items-center gap-2"
                            >
                                <span>▶</span>
                                <span>Resume</span>
                            </button>
                        ) : (
                            <button
                                onClick={onPause}
                                className="px-4 py-2 bg-yellow-600 hover:bg-yellow-700 rounded-lg text-sm font-medium text-white transition-colors flex items-center gap-2"
                            >
                                <span>⏸</span>
                                <span>Pause</span>
                            </button>
                        )}
                    </div>
                </div>

                {/* Progress Bar */}
                <div className="h-2 bg-zinc-800 rounded-full overflow-hidden">
                    <div
                        className={`h-full transition-all duration-500 ${failedSteps > 0 ? "bg-red-500" : "bg-gradient-to-r from-violet-500 to-fuchsia-500"
                            }`}
                        style={{ width: `${progress}%` }}
                    />
                </div>
            </div>

            {/* Steps List */}
            <div className="p-4">
                {steps.length === 0 ? (
                    <div className="text-center py-8 text-zinc-500">
                        <div className="text-3xl mb-2 opacity-30">⚡</div>
                        <div>No execution in progress</div>
                        <div className="text-xs mt-1">Steps will appear here during Phase 4</div>
                    </div>
                ) : (
                    <div className="space-y-2">
                        {steps.map((step, index) => (
                            <ExecutionStepCard
                                key={step.id}
                                step={step}
                                isActive={index === currentStepIndex}
                                onRollback={step.canRollback ? () => onRollback?.(step.id) : undefined}
                            />
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}

export default ExecutionMonitor;
