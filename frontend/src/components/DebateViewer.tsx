"use client";

import { useState, useEffect } from "react";
import { AGENT_COLORS } from "@/lib/design-tokens";

// ============================================================================
// Types
// ============================================================================

export interface DebateTurn {
    id: string;
    turnNumber: number;
    agent: "Gemini" | "Claude";
    position: "SUPPORT" | "OPPOSE" | "CONCEDE";
    argument: string;
    targetPoint?: string;
    concession?: string;
    evidence?: string[];
    timestamp: Date;
}

interface DebateViewerProps {
    topic?: string;
    turns?: DebateTurn[];
    consensusScore?: number;
    isLive?: boolean;
    className?: string;
}

// ============================================================================
// Position Badge
// ============================================================================

function PositionBadge({ position }: { position: DebateTurn["position"] }) {
    const styles = {
        SUPPORT: "bg-emerald-500/20 text-emerald-400 border-emerald-500/50",
        OPPOSE: "bg-red-500/20 text-red-400 border-red-500/50",
        CONCEDE: "bg-yellow-500/20 text-yellow-400 border-yellow-500/50",
    };

    const icons = {
        SUPPORT: "👍",
        OPPOSE: "👎",
        CONCEDE: "🤝",
    };

    return (
        <span className={`px-2 py-0.5 text-xs font-medium rounded-full border ${styles[position]}`}>
            {icons[position]} {position}
        </span>
    );
}

// ============================================================================
// Consensus Gauge
// ============================================================================

function ConsensusGauge({ score, isLive }: { score: number; isLive?: boolean }) {
    const getColor = (s: number) => {
        if (s >= 80) return "text-emerald-400";
        if (s >= 60) return "text-yellow-400";
        if (s >= 40) return "text-orange-400";
        return "text-red-400";
    };

    const getBarColor = (s: number) => {
        if (s >= 80) return "bg-emerald-500";
        if (s >= 60) return "bg-yellow-500";
        if (s >= 40) return "bg-orange-500";
        return "bg-red-500";
    };

    return (
        <div className="flex items-center gap-4">
            <div className="flex-1">
                <div className="flex items-center justify-between text-sm mb-1">
                    <span className="text-zinc-400">Consensus</span>
                    <span className={`font-bold ${getColor(score)}`}>
                        {score.toFixed(0)}%
                        {isLive && <span className="ml-2 text-xs animate-pulse">● LIVE</span>}
                    </span>
                </div>
                <div className="h-2 bg-zinc-800 rounded-full overflow-hidden">
                    <div
                        className={`h-full transition-all duration-500 ${getBarColor(score)}`}
                        style={{ width: `${score}%` }}
                    />
                </div>
            </div>
        </div>
    );
}

// ============================================================================
// Debate Turn Card
// ============================================================================

function DebateTurnCard({ turn }: { turn: DebateTurn }) {
    const colors = AGENT_COLORS[turn.agent.toLowerCase() as keyof typeof AGENT_COLORS];
    const isGemini = turn.agent === "Gemini";

    return (
        <div
            className={`
        p-4 rounded-lg border transition-all animate-fadeIn
        ${isGemini ? "bg-blue-500/5 border-blue-500/30" : "bg-orange-500/5 border-orange-500/30"}
      `}
        >
            {/* Header */}
            <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                    <div className={`w-6 h-6 rounded bg-gradient-to-br ${colors.gradient} flex items-center justify-center`}>
                        <span className="text-white text-xs font-bold">{turn.agent[0]}</span>
                    </div>
                    <span className="font-medium text-zinc-200">{turn.agent}</span>
                    <span className="text-xs text-zinc-500">Turn {turn.turnNumber}</span>
                </div>
                <PositionBadge position={turn.position} />
            </div>

            {/* Target Point */}
            {turn.targetPoint && (
                <div className="text-xs text-zinc-500 mb-2 flex items-center gap-1">
                    <span>🎯</span>
                    <span>Re: {turn.targetPoint}</span>
                </div>
            )}

            {/* Argument */}
            <p className="text-sm text-zinc-300 leading-relaxed">{turn.argument}</p>

            {/* Concession */}
            {turn.concession && (
                <div className="mt-2 p-2 bg-yellow-500/10 border border-yellow-500/30 rounded text-sm text-yellow-300">
                    <span className="font-medium">Concession:</span> {turn.concession}
                </div>
            )}

            {/* Evidence */}
            {turn.evidence && turn.evidence.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1">
                    {turn.evidence.map((ev, i) => (
                        <span key={i} className="px-2 py-0.5 bg-zinc-700/50 rounded text-xs text-zinc-400">
                            📎 {ev}
                        </span>
                    ))}
                </div>
            )}
        </div>
    );
}

// ============================================================================
// Main Debate Viewer Component
// ============================================================================

export function DebateViewer({
    topic = "Task Approach Strategy",
    turns = [],
    consensusScore = 0,
    isLive = false,
    className = "",
}: DebateViewerProps) {
    // Separate turns by agent
    const geminiTurns = turns.filter((t) => t.agent === "Gemini");
    const claudeTurns = turns.filter((t) => t.agent === "Claude");

    return (
        <div className={`bg-zinc-900/50 border border-zinc-800 rounded-xl ${className}`}>
            {/* Header */}
            <div className="p-4 border-b border-zinc-800">
                <div className="flex items-center justify-between mb-3">
                    <div>
                        <h3 className="text-lg font-medium text-white flex items-center gap-2">
                            ⚔️ Strategic Debate
                            {isLive && (
                                <span className="px-2 py-0.5 bg-red-500/20 text-red-400 text-xs font-medium rounded-full animate-pulse">
                                    LIVE
                                </span>
                            )}
                        </h3>
                        <p className="text-sm text-zinc-400">{topic}</p>
                    </div>
                    <div className="text-sm text-zinc-500">
                        {turns.length} turn{turns.length !== 1 ? "s" : ""}
                    </div>
                </div>
                <ConsensusGauge score={consensusScore} isLive={isLive} />
            </div>

            {/* Two-Column Debate */}
            <div className="p-4">
                {turns.length === 0 ? (
                    <div className="text-center py-8 text-zinc-500">
                        <div className="text-3xl mb-2 opacity-30">⚔️</div>
                        <div>No debate in progress</div>
                        <div className="text-xs mt-1">Debate will appear here when Phase 2 starts</div>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                        {/* Gemini Column */}
                        <div>
                            <div className="flex items-center gap-2 mb-3">
                                <div className="w-4 h-4 rounded bg-gradient-to-br from-blue-500 to-cyan-500" />
                                <span className="text-sm font-medium text-zinc-300">Gemini</span>
                                <span className="text-xs text-zinc-500">({geminiTurns.length} turns)</span>
                            </div>
                            <div className="space-y-3">
                                {geminiTurns.map((turn) => (
                                    <DebateTurnCard key={turn.id} turn={turn} />
                                ))}
                            </div>
                        </div>

                        {/* Claude Column */}
                        <div>
                            <div className="flex items-center gap-2 mb-3">
                                <div className="w-4 h-4 rounded bg-gradient-to-br from-orange-500 to-amber-500" />
                                <span className="text-sm font-medium text-zinc-300">Claude</span>
                                <span className="text-xs text-zinc-500">({claudeTurns.length} turns)</span>
                            </div>
                            <div className="space-y-3">
                                {claudeTurns.map((turn) => (
                                    <DebateTurnCard key={turn.id} turn={turn} />
                                ))}
                            </div>
                        </div>
                    </div>
                )}
            </div>

            {/* Footer Stats */}
            {turns.length > 0 && (
                <div className="px-4 py-3 border-t border-zinc-800 flex items-center justify-between text-xs text-zinc-500">
                    <div className="flex items-center gap-4">
                        <span>👍 {turns.filter((t) => t.position === "SUPPORT").length} support</span>
                        <span>👎 {turns.filter((t) => t.position === "OPPOSE").length} oppose</span>
                        <span>🤝 {turns.filter((t) => t.position === "CONCEDE").length} concede</span>
                    </div>
                    {consensusScore >= 80 && (
                        <span className="text-emerald-400">✓ Consensus reached</span>
                    )}
                </div>
            )}
        </div>
    );
}

export default DebateViewer;
