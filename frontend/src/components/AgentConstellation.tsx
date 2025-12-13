"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { AGENT_COLORS } from "@/lib/design-tokens";

// ============================================================================
// Types
// ============================================================================

export interface AgentNode {
    id: string;
    name: string;
    type: "gemini" | "claude" | "spawned";
    status: "active" | "idle" | "offline";
    x?: number;
    y?: number;
    dylanScore?: number;
    specializations?: string[];
}

export interface AgentConnection {
    source: string;
    target: string;
    type: "collaboration" | "spawned_by" | "invoked";
    strength: number; // 0-1
}

interface AgentConstellationProps {
    agents?: AgentNode[];
    connections?: AgentConnection[];
    selectedAgentId?: string;
    onAgentSelect?: (agentId: string) => void;
    className?: string;
}

// ============================================================================
// Constants
// ============================================================================

const CANVAS_WIDTH = 600;
const CANVAS_HEIGHT = 400;
const NODE_RADIUS = 24;

// ============================================================================
// Position Calculation (Simple Force Layout)
// ============================================================================

function calculatePositions(agents: AgentNode[]): AgentNode[] {
    const centerX = CANVAS_WIDTH / 2;
    const centerY = CANVAS_HEIGHT / 2;
    const orbitRadius = 120;

    return agents.map((agent, index) => {
        if (agent.type === "gemini") {
            return { ...agent, x: centerX - 80, y: centerY };
        }
        if (agent.type === "claude") {
            return { ...agent, x: centerX + 80, y: centerY };
        }
        // Spawned agents orbit around
        const spawnedIndex = agents.filter((a, i) => a.type === "spawned" && i < index).length;
        const spawnedTotal = agents.filter((a) => a.type === "spawned").length;
        const angle = (spawnedIndex / Math.max(spawnedTotal, 1)) * Math.PI * 2 - Math.PI / 2;
        return {
            ...agent,
            x: centerX + Math.cos(angle) * orbitRadius,
            y: centerY + Math.sin(angle) * orbitRadius,
        };
    });
}

// ============================================================================
// Agent Node Component
// ============================================================================

function AgentNodeComponent({
    agent,
    isSelected,
    onClick,
}: {
    agent: AgentNode;
    isSelected: boolean;
    onClick: () => void;
}) {
    const colors = AGENT_COLORS[agent.type];
    const statusColors = {
        active: "#22C55E",
        idle: "#EAB308",
        offline: "#71717A",
    };

    return (
        <g
            transform={`translate(${agent.x}, ${agent.y})`}
            onClick={onClick}
            style={{ cursor: "pointer" }}
        >
            {/* Selection ring */}
            {isSelected && (
                <circle
                    r={NODE_RADIUS + 6}
                    fill="none"
                    stroke="#8B5CF6"
                    strokeWidth={2}
                    opacity={0.8}
                />
            )}

            {/* Outer glow for active */}
            {agent.status === "active" && (
                <circle
                    r={NODE_RADIUS + 3}
                    fill="none"
                    stroke={statusColors.active}
                    strokeWidth={2}
                    opacity={0.4}
                >
                    <animate
                        attributeName="opacity"
                        values="0.4;0.1;0.4"
                        dur="2s"
                        repeatCount="indefinite"
                    />
                </circle>
            )}

            {/* Main circle with gradient */}
            <defs>
                <linearGradient id={`grad-${agent.id}`} x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor={agent.type === "gemini" ? "#3B82F6" : agent.type === "claude" ? "#F97316" : "#8B5CF6"} />
                    <stop offset="100%" stopColor={agent.type === "gemini" ? "#06B6D4" : agent.type === "claude" ? "#F59E0B" : "#D946EF"} />
                </linearGradient>
            </defs>
            <circle
                r={NODE_RADIUS}
                fill={`url(#grad-${agent.id})`}
                stroke="#18181B"
                strokeWidth={3}
            />

            {/* Agent initial */}
            <text
                textAnchor="middle"
                dy="0.35em"
                fill="white"
                fontSize="14"
                fontWeight="bold"
            >
                {agent.name[0].toUpperCase()}
            </text>

            {/* Status indicator */}
            <circle
                cx={NODE_RADIUS - 4}
                cy={NODE_RADIUS - 4}
                r={5}
                fill={statusColors[agent.status]}
                stroke="#18181B"
                strokeWidth={2}
            />

            {/* Agent name below */}
            <text
                textAnchor="middle"
                y={NODE_RADIUS + 16}
                fill="#A1A1AA"
                fontSize="11"
            >
                {agent.name}
            </text>
        </g>
    );
}

// ============================================================================
// Connection Line Component
// ============================================================================

function ConnectionLine({
    source,
    target,
    connection,
}: {
    source: AgentNode;
    target: AgentNode;
    connection: AgentConnection;
}) {
    const colors = {
        collaboration: "#8B5CF6",
        spawned_by: "#22C55E",
        invoked: "#3B82F6",
    };

    return (
        <line
            x1={source.x}
            y1={source.y}
            x2={target.x}
            y2={target.y}
            stroke={colors[connection.type]}
            strokeWidth={1 + connection.strength * 2}
            strokeOpacity={0.3 + connection.strength * 0.4}
            strokeDasharray={connection.type === "invoked" ? "4,4" : undefined}
        />
    );
}

// ============================================================================
// Main Agent Constellation Component
// ============================================================================

export function AgentConstellation({
    agents = [],
    connections = [],
    selectedAgentId,
    onAgentSelect,
    className = "",
}: AgentConstellationProps) {
    const [positionedAgents, setPositionedAgents] = useState<AgentNode[]>([]);

    // Calculate positions when agents change
    useEffect(() => {
        if (agents.length > 0) {
            setPositionedAgents(calculatePositions(agents));
        }
    }, [agents]);

    // Demo data if none provided
    const displayAgents = positionedAgents.length > 0 ? positionedAgents : calculatePositions([
        { id: "gemini", name: "Gemini", type: "gemini", status: "active" },
        { id: "claude", name: "Claude", type: "claude", status: "active" },
    ]);

    const displayConnections = connections.length > 0 ? connections : [
        { source: "gemini", target: "claude", type: "collaboration" as const, strength: 0.8 },
    ];

    return (
        <div className={`bg-zinc-900/50 border border-zinc-800 rounded-xl overflow-hidden ${className}`}>
            {/* Header */}
            <div className="p-4 border-b border-zinc-800">
                <h3 className="text-lg font-medium text-white flex items-center gap-2">
                    🌐 Agent Constellation
                </h3>
                <p className="text-sm text-zinc-400">
                    Click an agent to view details
                </p>
            </div>

            {/* SVG Canvas */}
            <div className="p-4 flex justify-center">
                <svg
                    width={CANVAS_WIDTH}
                    height={CANVAS_HEIGHT}
                    viewBox={`0 0 ${CANVAS_WIDTH} ${CANVAS_HEIGHT}`}
                    className="bg-zinc-900/30 rounded-lg"
                >
                    {/* Background grid */}
                    <defs>
                        <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
                            <path
                                d="M 40 0 L 0 0 0 40"
                                fill="none"
                                stroke="#27272A"
                                strokeWidth="0.5"
                            />
                        </pattern>
                    </defs>
                    <rect width="100%" height="100%" fill="url(#grid)" />

                    {/* Connections */}
                    {displayConnections.map((conn, i) => {
                        const source = displayAgents.find((a) => a.id === conn.source);
                        const target = displayAgents.find((a) => a.id === conn.target);
                        if (!source || !target) return null;
                        return (
                            <ConnectionLine
                                key={i}
                                source={source}
                                target={target}
                                connection={conn}
                            />
                        );
                    })}

                    {/* Agent Nodes */}
                    {displayAgents.map((agent) => (
                        <AgentNodeComponent
                            key={agent.id}
                            agent={agent}
                            isSelected={agent.id === selectedAgentId}
                            onClick={() => onAgentSelect?.(agent.id)}
                        />
                    ))}

                    {/* Legend */}
                    <g transform="translate(20, 360)">
                        <text fill="#71717A" fontSize="10">
                            ● Active  ○ Idle  — Collaboration
                        </text>
                    </g>
                </svg>
            </div>

            {/* Stats Footer */}
            <div className="px-4 py-3 border-t border-zinc-800 flex items-center justify-between text-xs text-zinc-500">
                <span>{displayAgents.length} agents</span>
                <span>{displayConnections.length} connections</span>
            </div>
        </div>
    );
}

export default AgentConstellation;
