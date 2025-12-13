"use client";

import { useState } from "react";

// ============================================================================
// Types
// ============================================================================

export interface EvolutionNode {
    id: string;
    name: string;
    generation: number;
    parentId?: string;
    fitnessScore?: number;
    status: "active" | "promoted" | "archived" | "failed";
    mutations?: string[];
    createdAt: Date;
}

interface EvolutionTreeProps {
    nodes?: EvolutionNode[];
    selectedNodeId?: string;
    onNodeSelect?: (nodeId: string) => void;
    className?: string;
}

// ============================================================================
// Status Badge
// ============================================================================

function StatusBadge({ status }: { status: EvolutionNode["status"] }) {
    const styles = {
        active: "bg-emerald-500/20 text-emerald-400 border-emerald-500/50",
        promoted: "bg-violet-500/20 text-violet-400 border-violet-500/50",
        archived: "bg-zinc-500/20 text-zinc-400 border-zinc-500/50",
        failed: "bg-red-500/20 text-red-400 border-red-500/50",
    };

    const icons = {
        active: "🟢",
        promoted: "⭐",
        archived: "📦",
        failed: "❌",
    };

    return (
        <span className={`px-2 py-0.5 text-xs rounded-full border ${styles[status]}`}>
            {icons[status]} {status}
        </span>
    );
}

// ============================================================================
// Fitness Bar
// ============================================================================

function FitnessBar({ score }: { score: number }) {
    const percentage = score * 100;
    const color = percentage >= 80 ? "bg-emerald-500" : percentage >= 50 ? "bg-yellow-500" : "bg-red-500";

    return (
        <div className="flex items-center gap-2">
            <div className="flex-1 h-1.5 bg-zinc-800 rounded-full overflow-hidden">
                <div className={`h-full ${color}`} style={{ width: `${percentage}%` }} />
            </div>
            <span className="text-xs text-zinc-400">{percentage.toFixed(0)}%</span>
        </div>
    );
}

// ============================================================================
// Tree Node Component
// ============================================================================

function TreeNode({
    node,
    children,
    depth,
    isSelected,
    isExpanded,
    onToggle,
    onSelect,
}: {
    node: EvolutionNode;
    children: EvolutionNode[];
    depth: number;
    isSelected: boolean;
    isExpanded: boolean;
    onToggle: () => void;
    onSelect: () => void;
}) {
    const hasChildren = children.length > 0;

    return (
        <div style={{ marginLeft: depth * 24 }}>
            {/* Node Card */}
            <div
                className={`
          flex items-center gap-3 p-3 rounded-lg border transition-all cursor-pointer
          ${isSelected
                        ? "bg-violet-600/10 border-violet-500"
                        : "bg-zinc-800/50 border-zinc-700 hover:border-zinc-600"
                    }
        `}
                onClick={onSelect}
            >
                {/* Expand/Collapse */}
                {hasChildren && (
                    <button
                        onClick={(e) => {
                            e.stopPropagation();
                            onToggle();
                        }}
                        className="w-5 h-5 flex items-center justify-center text-zinc-500 hover:text-zinc-300"
                    >
                        {isExpanded ? "▼" : "▶"}
                    </button>
                )}
                {!hasChildren && <div className="w-5" />}

                {/* Generation Badge */}
                <div className="px-2 py-0.5 bg-zinc-700 rounded text-xs text-zinc-400">
                    Gen {node.generation}
                </div>

                {/* Name */}
                <div className="flex-1 min-w-0">
                    <div className="font-medium text-zinc-200 truncate">{node.name}</div>
                    {node.mutations && node.mutations.length > 0 && (
                        <div className="flex gap-1 mt-1">
                            {node.mutations.slice(0, 2).map((mut, i) => (
                                <span
                                    key={i}
                                    className="px-1.5 py-0.5 bg-violet-500/20 text-violet-300 rounded text-xs"
                                >
                                    🧬 {mut}
                                </span>
                            ))}
                            {node.mutations.length > 2 && (
                                <span className="text-xs text-zinc-500">+{node.mutations.length - 2}</span>
                            )}
                        </div>
                    )}
                </div>

                {/* Fitness Score */}
                {node.fitnessScore !== undefined && (
                    <div className="w-24">
                        <FitnessBar score={node.fitnessScore} />
                    </div>
                )}

                {/* Status */}
                <StatusBadge status={node.status} />
            </div>

            {/* Children */}
            {isExpanded && hasChildren && (
                <div className="mt-2 space-y-2 border-l-2 border-zinc-700 ml-2.5">
                    {children.map((child) => (
                        <TreeNodeWrapper
                            key={child.id}
                            node={child}
                            allNodes={[...children]}
                            depth={depth + 1}
                            selectedNodeId={isSelected ? node.id : undefined}
                            onNodeSelect={onSelect}
                        />
                    ))}
                </div>
            )}
        </div>
    );
}

// ============================================================================
// Tree Node Wrapper (manages expand state)
// ============================================================================

function TreeNodeWrapper({
    node,
    allNodes,
    depth,
    selectedNodeId,
    onNodeSelect,
}: {
    node: EvolutionNode;
    allNodes: EvolutionNode[];
    depth: number;
    selectedNodeId?: string;
    onNodeSelect: (nodeId: string) => void;
}) {
    const [isExpanded, setIsExpanded] = useState(depth < 2);
    const children = allNodes.filter((n) => n.parentId === node.id);

    return (
        <TreeNode
            node={node}
            children={children}
            depth={depth}
            isSelected={node.id === selectedNodeId}
            isExpanded={isExpanded}
            onToggle={() => setIsExpanded(!isExpanded)}
            onSelect={() => onNodeSelect(node.id)}
        />
    );
}

// ============================================================================
// Demo Data
// ============================================================================

const DEMO_NODES: EvolutionNode[] = [
    { id: "v1", name: "NEXUS V7.0", generation: 0, status: "archived", fitnessScore: 0.65, createdAt: new Date("2025-11-01") },
    { id: "v2", name: "NEXUS V8.0", generation: 1, parentId: "v1", status: "archived", fitnessScore: 0.78, mutations: ["HiveMind"], createdAt: new Date("2025-11-15") },
    { id: "v3", name: "NEXUS V9.0", generation: 2, parentId: "v2", status: "archived", fitnessScore: 0.85, mutations: ["Swarm Engine"], createdAt: new Date("2025-12-01") },
    { id: "v4", name: "NEXUS V10.2", generation: 3, parentId: "v3", status: "active", fitnessScore: 0.92, mutations: ["Agent Factory", "Dashboard"], createdAt: new Date("2025-12-13") },
];

// ============================================================================
// Main Evolution Tree Component
// ============================================================================

export function EvolutionTree({
    nodes = DEMO_NODES,
    selectedNodeId,
    onNodeSelect,
    className = "",
}: EvolutionTreeProps) {
    const [selected, setSelected] = useState<string | undefined>(selectedNodeId);
    const rootNodes = nodes.filter((n) => !n.parentId);

    const handleSelect = (nodeId: string) => {
        setSelected(nodeId);
        onNodeSelect?.(nodeId);
    };

    return (
        <div className={`bg-zinc-900/50 border border-zinc-800 rounded-xl ${className}`}>
            {/* Header */}
            <div className="p-4 border-b border-zinc-800">
                <h3 className="text-lg font-medium text-white flex items-center gap-2">
                    🧬 Evolution Lineage
                </h3>
                <p className="text-sm text-zinc-400">
                    {nodes.length} generations • Click to view details
                </p>
            </div>

            {/* Tree */}
            <div className="p-4 space-y-2">
                {rootNodes.length === 0 ? (
                    <div className="text-center py-8 text-zinc-500">
                        <div className="text-3xl mb-2 opacity-30">🧬</div>
                        <div>No evolution history</div>
                    </div>
                ) : (
                    rootNodes.map((root) => (
                        <TreeNodeWrapper
                            key={root.id}
                            node={root}
                            allNodes={nodes}
                            depth={0}
                            selectedNodeId={selected}
                            onNodeSelect={handleSelect}
                        />
                    ))
                )}
            </div>

            {/* Stats */}
            <div className="px-4 py-3 border-t border-zinc-800 flex items-center justify-between text-xs text-zinc-500">
                <span>
                    {nodes.filter((n) => n.status === "active").length} active •{" "}
                    {nodes.filter((n) => n.status === "promoted").length} promoted
                </span>
                <span>
                    Max Gen: {Math.max(...nodes.map((n) => n.generation))}
                </span>
            </div>
        </div>
    );
}

export default EvolutionTree;
