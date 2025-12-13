"use client";

import { useState, useEffect, useRef } from "react";

// ============================================================================
// Types
// ============================================================================

interface AgentExchange {
    id: string;
    timestamp: Date;
    agent: "Gemini" | "Claude" | string;
    content: string;
    actionType: "TALK" | "TOOL_USE";
    tool?: string;
}

interface AgentExchangesProps {
    className?: string;
    maxExchanges?: number;
}

// ============================================================================
// Helper Functions
// ============================================================================

function formatContent(content: string): React.ReactNode {
    if (!content) return <span className="text-zinc-500 italic">(empty response)</span>;

    // Try to parse as JSON or Python dict
    const trimmed = content.trim();
    if (trimmed.startsWith('{') || trimmed.startsWith('[')) {
        let parsed: Record<string, unknown> | null = null;

        // Try standard JSON first
        try {
            parsed = JSON.parse(trimmed);
        } catch {
            // Try Python dict format (single quotes → double quotes)
            try {
                // Replace single quotes with double quotes (simple approach)
                const fixed = trimmed
                    .replace(/'/g, '"')
                    .replace(/True/g, 'true')
                    .replace(/False/g, 'false')
                    .replace(/None/g, 'null');
                parsed = JSON.parse(fixed);
            } catch {
                // Not parseable, display as-is
            }
        }

        if (parsed && typeof parsed === 'object') {
            const formatted: string[] = [];

            // Analysis phase fields
            if (parsed.task_understanding) formatted.push(`📋 ${parsed.task_understanding}`);
            if (parsed.proposed_approach) formatted.push(`🎯 ${parsed.proposed_approach}`);
            if (parsed.complexity_assessment) formatted.push(`📊 Complexity: ${parsed.complexity_assessment}`);

            // Debate phase fields
            if (parsed.argument) formatted.push(`💬 ${parsed.argument}`);
            if (parsed.position) formatted.push(`🔷 Position: ${parsed.position}`);
            if (parsed.concession) formatted.push(`🤝 Concession: ${parsed.concession}`);
            if (parsed.target_point) formatted.push(`🎯 Target: ${parsed.target_point}`);

            // Failure/Diagnosis fields
            if (parsed.failure_type) formatted.push(`⚠️ Failure: ${parsed.failure_type}`);
            if (parsed.root_cause) formatted.push(`🔍 Root cause: ${parsed.root_cause}`);
            if (parsed.contributing_factors) {
                const factors = Array.isArray(parsed.contributing_factors)
                    ? parsed.contributing_factors.join(', ')
                    : parsed.contributing_factors;
                formatted.push(`📝 Factors: ${factors}`);
            }

            // Consensus fields
            if (parsed.consensus_reached !== undefined) {
                formatted.push(`${parsed.consensus_reached ? '✅' : '❌'} Consensus: ${parsed.consensus_reached}`);
            }
            if (parsed.consensus_score) formatted.push(`📈 Score: ${parsed.consensus_score}`);

            if (formatted.length > 0) {
                return <>{formatted.join('\n')}</>;
            }
            // Fallback: pretty print JSON with truncation
            const jsonStr = JSON.stringify(parsed, null, 2);
            return jsonStr.length > 500 ? jsonStr.slice(0, 500) + '...' : jsonStr;
        }
    }

    return content;
}

// ============================================================================
// Agent Exchanges Component
// ============================================================================

export function AgentExchanges({
    className = "",
    maxExchanges = 50
}: AgentExchangesProps) {
    const [exchanges, setExchanges] = useState<AgentExchange[]>([]);
    const [isLive, setIsLive] = useState(true);
    const scrollRef = useRef<HTMLDivElement>(null);

    // WebSocket connection for live events
    useEffect(() => {
        if (!isLive) return;

        const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws/logs";
        let ws: WebSocket | null = null;

        const connect = () => {
            ws = new WebSocket(WS_URL);

            ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);

                    // Filter for AGENT_RESPONSE events
                    if (data.type === "AGENT_RESPONSE") {
                        const exchange: AgentExchange = {
                            id: `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
                            timestamp: new Date(data.timestamp || Date.now()),
                            agent: data.data?.agent || "Unknown",
                            content: data.data?.content || "",
                            actionType: data.data?.action_type || "TALK",
                            tool: data.data?.tool,
                        };

                        setExchanges((prev) => {
                            const updated = [...prev, exchange];
                            // Keep only last N exchanges
                            return updated.slice(-maxExchanges);
                        });
                    }
                } catch (e) {
                    // Ignore non-JSON messages
                }
            };

            ws.onerror = () => {
                setTimeout(connect, 3000);  // Reconnect after 3s
            };
        };

        connect();

        return () => {
            ws?.close();
        };
    }, [isLive, maxExchanges]);

    // Auto-scroll to bottom
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [exchanges]);

    const agentColors: Record<string, string> = {
        Gemini: "bg-blue-500",
        Claude: "bg-orange-500",
    };

    return (
        <div className={`bg-zinc-900/50 border border-zinc-800 rounded-xl overflow-hidden ${className}`}>
            {/* Header */}
            <div className="px-4 py-3 border-b border-zinc-800 flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <span className="text-lg">🔄</span>
                    <span className="font-medium text-zinc-200">Agent Exchanges</span>
                    <span className="text-xs text-zinc-500">({exchanges.length})</span>
                </div>
                <button
                    onClick={() => setIsLive(!isLive)}
                    className={`flex items-center gap-2 text-xs px-2 py-1 rounded ${isLive
                        ? "bg-emerald-500/20 text-emerald-400"
                        : "bg-zinc-700 text-zinc-400"
                        }`}
                >
                    <div className={`w-2 h-2 rounded-full ${isLive ? "bg-emerald-500 animate-pulse" : "bg-zinc-500"}`} />
                    {isLive ? "LIVE" : "PAUSED"}
                </button>
            </div>

            {/* Exchanges List */}
            <div
                ref={scrollRef}
                className="overflow-y-auto max-h-[400px] p-3 space-y-2"
            >
                {exchanges.length === 0 && (
                    <div className="text-center text-zinc-500 py-8">
                        <div className="text-3xl mb-2 opacity-30">💬</div>
                        <div className="text-sm">No exchanges yet</div>
                        <div className="text-xs mt-1">Run a task in nexus7.py to see live agent activity</div>
                    </div>
                )}

                {exchanges.map((exchange) => (
                    <div
                        key={exchange.id}
                        className="flex gap-3 p-2 bg-zinc-800/50 rounded-lg animate-fadeIn"
                    >
                        {/* Agent Avatar */}
                        <div className={`w-8 h-8 rounded-full ${agentColors[exchange.agent] || "bg-violet-500"} flex items-center justify-center flex-shrink-0`}>
                            <span className="text-white text-xs font-bold">
                                {exchange.agent[0].toUpperCase()}
                            </span>
                        </div>

                        {/* Content */}
                        <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                                <span className="font-medium text-zinc-200 text-sm">{exchange.agent}</span>
                                {exchange.actionType === "TOOL_USE" && exchange.tool && (
                                    <span className="px-2 py-0.5 bg-violet-600/20 border border-violet-600 text-violet-300 text-xs rounded">
                                        🔧 {exchange.tool}
                                    </span>
                                )}
                                <span className="text-xs text-zinc-500 ml-auto">
                                    {exchange.timestamp.toLocaleTimeString()}
                                </span>
                            </div>
                            {/* Content with improved formatting */}
                            <div className="text-zinc-300 text-sm whitespace-pre-wrap break-words">
                                {formatContent(exchange.content)}
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            {/* Footer */}
            {exchanges.length > 0 && (
                <div className="px-4 py-2 border-t border-zinc-800 flex justify-between text-xs text-zinc-500">
                    <span>Showing last {exchanges.length} exchanges</span>
                    <button
                        onClick={() => setExchanges([])}
                        className="text-zinc-400 hover:text-zinc-200"
                    >
                        Clear
                    </button>
                </div>
            )}
        </div>
    );
}

export default AgentExchanges;
