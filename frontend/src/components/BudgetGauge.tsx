"use client";

// ============================================================================
// Types
// ============================================================================

interface BudgetGaugeProps {
    spent: number;
    limit: number;
    className?: string;
    size?: "sm" | "md" | "lg";
    showBreakdown?: boolean;
    breakdown?: {
        gemini?: number;
        claude?: number;
        spawned?: number;
    };
}

// ============================================================================
// Circular Gauge SVG
// ============================================================================

function CircularGauge({
    percentage,
    size,
    warningLevel,
}: {
    percentage: number;
    size: number;
    warningLevel: "normal" | "warning" | "critical";
}) {
    const strokeWidth = size === 120 ? 8 : size === 80 ? 6 : 4;
    const radius = (size - strokeWidth) / 2;
    const circumference = 2 * Math.PI * radius;
    const offset = circumference - (percentage / 100) * circumference;

    const colors = {
        normal: { stroke: "#8B5CF6", bg: "rgba(139, 92, 246, 0.1)" },
        warning: { stroke: "#EAB308", bg: "rgba(234, 179, 8, 0.1)" },
        critical: { stroke: "#EF4444", bg: "rgba(239, 68, 68, 0.1)" },
    };

    const color = colors[warningLevel];

    return (
        <svg width={size} height={size} className="transform -rotate-90">
            {/* Background circle */}
            <circle
                cx={size / 2}
                cy={size / 2}
                r={radius}
                fill="none"
                stroke="#27272A"
                strokeWidth={strokeWidth}
            />
            {/* Progress circle */}
            <circle
                cx={size / 2}
                cy={size / 2}
                r={radius}
                fill="none"
                stroke={color.stroke}
                strokeWidth={strokeWidth}
                strokeLinecap="round"
                strokeDasharray={circumference}
                strokeDashoffset={offset}
                className="transition-all duration-500"
                style={{ filter: `drop-shadow(0 0 6px ${color.stroke}40)` }}
            />
        </svg>
    );
}

// ============================================================================
// Agent Breakdown Bar
// ============================================================================

function BreakdownBar({
    gemini = 0,
    claude = 0,
    spawned = 0,
    total,
}: {
    gemini?: number;
    claude?: number;
    spawned?: number;
    total: number;
}) {
    const geminiPct = (gemini / total) * 100;
    const claudePct = (claude / total) * 100;
    const spawnedPct = (spawned / total) * 100;

    return (
        <div className="space-y-2">
            <div className="h-3 bg-zinc-800 rounded-full overflow-hidden flex">
                {geminiPct > 0 && (
                    <div
                        className="h-full bg-blue-500 transition-all"
                        style={{ width: `${geminiPct}%` }}
                        title={`Gemini: $${gemini.toFixed(2)}`}
                    />
                )}
                {claudePct > 0 && (
                    <div
                        className="h-full bg-orange-500 transition-all"
                        style={{ width: `${claudePct}%` }}
                        title={`Claude: $${claude.toFixed(2)}`}
                    />
                )}
                {spawnedPct > 0 && (
                    <div
                        className="h-full bg-violet-500 transition-all"
                        style={{ width: `${spawnedPct}%` }}
                        title={`Spawned: $${spawned.toFixed(2)}`}
                    />
                )}
            </div>
            <div className="flex items-center justify-between text-xs text-zinc-500">
                <div className="flex items-center gap-3">
                    <span className="flex items-center gap-1">
                        <div className="w-2 h-2 rounded-full bg-blue-500" />
                        Gemini ${gemini.toFixed(2)}
                    </span>
                    <span className="flex items-center gap-1">
                        <div className="w-2 h-2 rounded-full bg-orange-500" />
                        Claude ${claude.toFixed(2)}
                    </span>
                    {spawned > 0 && (
                        <span className="flex items-center gap-1">
                            <div className="w-2 h-2 rounded-full bg-violet-500" />
                            Spawned ${spawned.toFixed(2)}
                        </span>
                    )}
                </div>
            </div>
        </div>
    );
}

// ============================================================================
// Main Budget Gauge Component
// ============================================================================

export function BudgetGauge({
    spent,
    limit,
    className = "",
    size = "md",
    showBreakdown = false,
    breakdown,
}: BudgetGaugeProps) {
    const percentage = Math.min((spent / limit) * 100, 100);
    const remaining = Math.max(limit - spent, 0);

    const warningLevel: "normal" | "warning" | "critical" =
        percentage >= 90 ? "critical" : percentage >= 75 ? "warning" : "normal";

    const gaugeSize = size === "lg" ? 120 : size === "md" ? 80 : 60;

    const warningColors = {
        normal: "text-violet-400",
        warning: "text-yellow-400",
        critical: "text-red-400",
    };

    return (
        <div className={`bg-zinc-900/50 border border-zinc-800 rounded-xl p-4 ${className}`}>
            <div className="flex items-center gap-4">
                {/* Circular Gauge */}
                <div className="relative">
                    <CircularGauge
                        percentage={percentage}
                        size={gaugeSize}
                        warningLevel={warningLevel}
                    />
                    <div className="absolute inset-0 flex items-center justify-center">
                        <span className={`text-sm font-bold ${warningColors[warningLevel]}`}>
                            {percentage.toFixed(0)}%
                        </span>
                    </div>
                </div>

                {/* Stats */}
                <div className="flex-1">
                    <div className="flex items-baseline gap-2 mb-1">
                        <span className="text-2xl font-bold text-white">${spent.toFixed(2)}</span>
                        <span className="text-zinc-500">/ ${limit.toFixed(0)}</span>
                    </div>
                    <div className="text-sm text-zinc-400">
                        ${remaining.toFixed(2)} remaining
                    </div>
                    {warningLevel !== "normal" && (
                        <div className={`text-xs mt-1 ${warningColors[warningLevel]}`}>
                            {warningLevel === "critical" ? "⚠️ Budget critical!" : "⚠️ Budget warning"}
                        </div>
                    )}
                </div>
            </div>

            {/* Breakdown */}
            {showBreakdown && breakdown && (
                <div className="mt-4 pt-4 border-t border-zinc-800">
                    <div className="text-xs text-zinc-500 mb-2">Usage by Agent</div>
                    <BreakdownBar
                        gemini={breakdown.gemini || 0}
                        claude={breakdown.claude || 0}
                        spawned={breakdown.spawned || 0}
                        total={spent || 1}
                    />
                </div>
            )}
        </div>
    );
}

export default BudgetGauge;
