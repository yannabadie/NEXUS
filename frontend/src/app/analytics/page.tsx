"use client";

import { useEffect, useState } from "react";
import { getBudgetStatus, type BudgetStatus } from "@/lib/api";

// ============================================================================
// Stat Card
// ============================================================================

function StatCard({
    label,
    value,
    subValue,
    icon,
    trend,
}: {
    label: string;
    value: string;
    subValue?: string;
    icon: string;
    trend?: "up" | "down" | "neutral";
}) {
    return (
        <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-4">
            <div className="flex items-start justify-between">
                <div>
                    <div className="text-xs text-zinc-500 mb-1">{label}</div>
                    <div className="text-2xl font-bold text-white">{value}</div>
                    {subValue && (
                        <div className="text-xs text-zinc-400 mt-1">{subValue}</div>
                    )}
                </div>
                <div className="text-2xl opacity-50">{icon}</div>
            </div>
            {trend && (
                <div className={`text-xs mt-2 ${trend === "up" ? "text-emerald-400" :
                        trend === "down" ? "text-red-400" : "text-zinc-500"
                    }`}>
                    {trend === "up" ? "↑" : trend === "down" ? "↓" : "→"} vs yesterday
                </div>
            )}
        </div>
    );
}

// ============================================================================
// Main Analytics Page
// ============================================================================

export default function AnalyticsPage() {
    const [budget, setBudget] = useState<BudgetStatus | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function fetchData() {
            const { data } = await getBudgetStatus();
            if (data) setBudget(data);
            setLoading(false);
        }

        fetchData();
        const interval = setInterval(fetchData, 10000);
        return () => clearInterval(interval);
    }, []);

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="animate-spin w-8 h-8 border-2 border-violet-500 border-t-transparent rounded-full" />
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-white">📈 Analytics</h1>
                    <p className="text-sm text-zinc-400">
                        Token usage, costs, and performance metrics
                    </p>
                </div>
                <button
                    className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg text-sm font-medium text-zinc-300 transition-colors"
                    onClick={() => alert("Export coming soon!")}
                >
                    Export CSV
                </button>
            </div>

            {/* Budget Overview */}
            <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-6">
                <h2 className="text-sm font-medium text-zinc-400 mb-4">Daily Budget</h2>
                <div className="flex items-end gap-4 mb-4">
                    <div className="text-4xl font-bold text-white">
                        ${budget?.spent?.toFixed(2) || "0.00"}
                    </div>
                    <div className="text-zinc-400 pb-1">
                        / ${budget?.limit?.toFixed(0) || "50"} limit
                    </div>
                </div>
                <div className="h-3 bg-zinc-800 rounded-full overflow-hidden">
                    <div
                        className={`h-full transition-all ${(budget?.percentage || 0) > 90 ? "bg-red-500" :
                                (budget?.percentage || 0) > 75 ? "bg-yellow-500" :
                                    "bg-gradient-to-r from-violet-500 to-fuchsia-500"
                            }`}
                        style={{ width: `${budget?.percentage || 0}%` }}
                    />
                </div>
                <div className="flex justify-between text-xs text-zinc-500 mt-2">
                    <span>{budget?.percentage?.toFixed(0) || 0}% used</span>
                    <span>${((budget?.limit || 50) - (budget?.spent || 0)).toFixed(2)} remaining</span>
                </div>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <StatCard
                    label="Total Tokens Today"
                    value="125.4K"
                    subValue="Input + Output"
                    icon="🔤"
                    trend="up"
                />
                <StatCard
                    label="API Calls"
                    value="47"
                    subValue="Gemini + Claude"
                    icon="📡"
                    trend="neutral"
                />
                <StatCard
                    label="Avg. Latency"
                    value="2.3s"
                    subValue="Per request"
                    icon="⚡"
                    trend="down"
                />
                <StatCard
                    label="Success Rate"
                    value="94%"
                    subValue="Last 24h"
                    icon="✅"
                    trend="up"
                />
            </div>

            {/* Usage Breakdown */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* By Agent */}
                <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-6">
                    <h2 className="text-sm font-medium text-zinc-400 mb-4">Usage by Agent</h2>
                    <div className="space-y-4">
                        {[
                            { name: "Gemini", tokens: 75200, cost: 4.51, color: "from-blue-500 to-cyan-500" },
                            { name: "Claude", tokens: 50200, cost: 7.53, color: "from-orange-500 to-amber-500" },
                        ].map((agent) => (
                            <div key={agent.name}>
                                <div className="flex justify-between text-sm mb-1">
                                    <span className="text-zinc-300">{agent.name}</span>
                                    <span className="text-zinc-400">{(agent.tokens / 1000).toFixed(1)}K tokens • ${agent.cost.toFixed(2)}</span>
                                </div>
                                <div className="h-2 bg-zinc-800 rounded-full overflow-hidden">
                                    <div
                                        className={`h-full bg-gradient-to-r ${agent.color}`}
                                        style={{ width: `${(agent.tokens / 125400) * 100}%` }}
                                    />
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* By Phase */}
                <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-6">
                    <h2 className="text-sm font-medium text-zinc-400 mb-4">Usage by HiveMind Phase</h2>
                    <div className="space-y-3">
                        {[
                            { name: "Analysis", pct: 25, icon: "🔍" },
                            { name: "Debate", pct: 35, icon: "⚔️" },
                            { name: "Architecture", pct: 15, icon: "📐" },
                            { name: "Execution", pct: 20, icon: "⚡" },
                            { name: "Consolidation", pct: 5, icon: "📦" },
                        ].map((phase) => (
                            <div key={phase.name} className="flex items-center gap-3">
                                <span className="text-lg w-6">{phase.icon}</span>
                                <span className="text-sm text-zinc-300 w-28">{phase.name}</span>
                                <div className="flex-1 h-2 bg-zinc-800 rounded-full overflow-hidden">
                                    <div
                                        className="h-full bg-violet-500"
                                        style={{ width: `${phase.pct}%` }}
                                    />
                                </div>
                                <span className="text-xs text-zinc-500 w-10 text-right">{phase.pct}%</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Coming Soon Notice */}
            <div className="bg-zinc-800/30 border border-dashed border-zinc-700 rounded-xl p-6 text-center">
                <div className="text-2xl mb-2 opacity-30">📊</div>
                <div className="text-zinc-400">More analytics features coming soon</div>
                <div className="text-xs text-zinc-600 mt-1">
                    Time-series charts, comparison reports, anomaly detection
                </div>
            </div>
        </div>
    );
}
