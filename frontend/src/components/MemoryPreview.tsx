"use client";

import { useState } from "react";

// ============================================================================
// Types
// ============================================================================

export interface MemoryItem {
    id: string;
    content: string;
    source: "success" | "failure" | "pattern" | "learned";
    category?: string;
    createdAt: Date;
    relevance?: number;
    tokens?: number;
}

interface MemoryPreviewProps {
    memories?: MemoryItem[];
    maxItems?: number;
    className?: string;
}

// ============================================================================
// Source Badge
// ============================================================================

function SourceBadge({ source }: { source: MemoryItem["source"] }) {
    const styles = {
        success: "bg-emerald-500/20 text-emerald-400",
        failure: "bg-red-500/20 text-red-400",
        pattern: "bg-violet-500/20 text-violet-400",
        learned: "bg-blue-500/20 text-blue-400",
    };

    const icons = {
        success: "✅",
        failure: "❌",
        pattern: "🔄",
        learned: "📚",
    };

    return (
        <span className={`px-2 py-0.5 text-xs rounded ${styles[source]}`}>
            {icons[source]} {source}
        </span>
    );
}

// ============================================================================
// Memory Card
// ============================================================================

function MemoryCard({ memory }: { memory: MemoryItem }) {
    const [isExpanded, setIsExpanded] = useState(false);
    const isLong = memory.content.length > 150;

    return (
        <div className="bg-zinc-800/50 border border-zinc-700 rounded-lg p-3 hover:border-zinc-600 transition-colors">
            <div className="flex items-start justify-between gap-3 mb-2">
                <SourceBadge source={memory.source} />
                <span className="text-xs text-zinc-500">
                    {memory.createdAt.toLocaleDateString()}
                </span>
            </div>

            <p className="text-sm text-zinc-300">
                {isLong && !isExpanded
                    ? `${memory.content.slice(0, 150)}...`
                    : memory.content
                }
            </p>

            {isLong && (
                <button
                    onClick={() => setIsExpanded(!isExpanded)}
                    className="text-xs text-violet-400 hover:text-violet-300 mt-1"
                >
                    {isExpanded ? "Show less" : "Show more"}
                </button>
            )}

            <div className="flex items-center gap-3 mt-2 pt-2 border-t border-zinc-700/50">
                {memory.category && (
                    <span className="text-xs px-1.5 py-0.5 bg-zinc-700/50 rounded text-zinc-400">
                        {memory.category}
                    </span>
                )}
                {memory.relevance !== undefined && (
                    <span className="text-xs text-zinc-500">
                        Relevance: {(memory.relevance * 100).toFixed(0)}%
                    </span>
                )}
                {memory.tokens && (
                    <span className="text-xs text-zinc-500">
                        {memory.tokens} tokens
                    </span>
                )}
            </div>
        </div>
    );
}

// ============================================================================
// Demo Data
// ============================================================================

const DEMO_MEMORIES: MemoryItem[] = [
    {
        id: "1",
        content: "JSON parsing from Gemini requires ast.literal_eval fallback for Python dict format with single quotes.",
        source: "learned",
        category: "parsing",
        createdAt: new Date("2025-12-13"),
        relevance: 0.95,
        tokens: 45,
    },
    {
        id: "2",
        content: "Session UUID must propagate through all 7 HiveMind phases for proper event correlation in dashboard.",
        source: "success",
        category: "architecture",
        createdAt: new Date("2025-12-13"),
        relevance: 0.88,
        tokens: 38,
    },
    {
        id: "3",
        content: "Evolution brainstorming entered infinite loop when agents failed to parse each other's tool outputs.",
        source: "failure",
        category: "evolution",
        createdAt: new Date("2025-12-12"),
        relevance: 0.72,
        tokens: 52,
    },
    {
        id: "4",
        content: "PING_PONG swarm mode works best for iterative refinement tasks with rapid agent turn-taking.",
        source: "pattern",
        category: "swarm",
        createdAt: new Date("2025-12-11"),
        relevance: 0.65,
        tokens: 41,
    },
];

// ============================================================================
// Main Memory Preview Component
// ============================================================================

export function MemoryPreview({
    memories = DEMO_MEMORIES,
    maxItems = 10,
    className = "",
}: MemoryPreviewProps) {
    const [filter, setFilter] = useState<MemoryItem["source"] | "all">("all");
    const [search, setSearch] = useState("");

    const filteredMemories = memories
        .filter((m) => filter === "all" || m.source === filter)
        .filter((m) =>
            search === "" ||
            m.content.toLowerCase().includes(search.toLowerCase()) ||
            m.category?.toLowerCase().includes(search.toLowerCase())
        )
        .slice(0, maxItems);

    return (
        <div className={`bg-zinc-900/50 border border-zinc-800 rounded-xl ${className}`}>
            {/* Header */}
            <div className="p-4 border-b border-zinc-800">
                <h3 className="text-lg font-medium text-white flex items-center gap-2">
                    🧠 Project Memory
                </h3>
                <p className="text-sm text-zinc-400">
                    RAG knowledge base • {memories.length} memories
                </p>
            </div>

            {/* Filters */}
            <div className="p-4 border-b border-zinc-800 space-y-3">
                {/* Search */}
                <div className="relative">
                    <input
                        type="text"
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        placeholder="Search memories..."
                        className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg 
                     text-sm text-zinc-100 placeholder:text-zinc-500
                     focus:border-violet-500 focus:outline-none"
                    />
                    {search && (
                        <button
                            onClick={() => setSearch("")}
                            className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-zinc-300"
                        >
                            ✕
                        </button>
                    )}
                </div>

                {/* Source Filter */}
                <div className="flex gap-2 flex-wrap">
                    {(["all", "success", "failure", "pattern", "learned"] as const).map((src) => (
                        <button
                            key={src}
                            onClick={() => setFilter(src)}
                            className={`px-3 py-1 text-xs rounded-full transition-colors ${filter === src
                                    ? "bg-violet-600 text-white"
                                    : "bg-zinc-800 text-zinc-400 hover:text-zinc-200"
                                }`}
                        >
                            {src === "all" ? "All" : src.charAt(0).toUpperCase() + src.slice(1)}
                        </button>
                    ))}
                </div>
            </div>

            {/* Memories List */}
            <div className="p-4 space-y-3 max-h-[400px] overflow-y-auto">
                {filteredMemories.length === 0 ? (
                    <div className="text-center py-8 text-zinc-500">
                        <div className="text-3xl mb-2 opacity-30">🧠</div>
                        <div>No memories found</div>
                    </div>
                ) : (
                    filteredMemories.map((memory) => (
                        <MemoryCard key={memory.id} memory={memory} />
                    ))
                )}
            </div>

            {/* Stats Footer */}
            <div className="px-4 py-3 border-t border-zinc-800 flex items-center justify-between text-xs text-zinc-500">
                <span>
                    Showing {filteredMemories.length} of {memories.length}
                </span>
                <span>
                    {memories.reduce((sum, m) => sum + (m.tokens || 0), 0)} total tokens
                </span>
            </div>
        </div>
    );
}

export default MemoryPreview;
