"use client";

import { useState } from "react";
import { createAgent } from "@/lib/api";

// ============================================================================
// Types
// ============================================================================

interface SpawnAgentModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSuccess: () => void;
}

// ============================================================================
// Spawn Agent Modal Component
// ============================================================================

export function SpawnAgentModal({ isOpen, onClose, onSuccess }: SpawnAgentModalProps) {
    const [name, setName] = useState("");
    const [mission, setMission] = useState("");
    const [capabilities, setCapabilities] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    if (!isOpen) return null;

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);

        if (!name.trim() || !mission.trim()) {
            setError("Name and mission are required");
            return;
        }

        setIsLoading(true);
        try {
            const capList = capabilities
                .split(",")
                .map((c) => c.trim())
                .filter((c) => c.length > 0);

            const result = await createAgent({
                name: name.trim(),
                mission: mission.trim(),
                capabilities: capList.length > 0 ? capList : ["general"],
            });

            if (result.error) {
                setError(result.error);
            } else {
                // Reset form and close
                setName("");
                setMission("");
                setCapabilities("");
                onSuccess();
                onClose();
            }
        } catch {
            setError("Failed to spawn agent");
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <>
            {/* Backdrop */}
            <div
                className="fixed inset-0 bg-black/70 z-50 backdrop-blur-sm"
                onClick={onClose}
            />

            {/* Modal */}
            <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
                <div
                    className="bg-zinc-900 border border-zinc-700 rounded-xl w-full max-w-md shadow-2xl"
                    onClick={(e) => e.stopPropagation()}
                >
                    {/* Header */}
                    <div className="px-6 py-4 border-b border-zinc-800 flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <span className="text-xl">✨</span>
                            <h2 className="text-lg font-semibold text-white">Spawn New Agent</h2>
                        </div>
                        <button
                            onClick={onClose}
                            className="text-zinc-400 hover:text-white transition-colors"
                        >
                            ✕
                        </button>
                    </div>

                    {/* Form */}
                    <form onSubmit={handleSubmit} className="p-6 space-y-4">
                        {/* Name */}
                        <div>
                            <label className="block text-sm font-medium text-zinc-400 mb-1">
                                Agent Name
                            </label>
                            <input
                                type="text"
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                placeholder="UX-Expert, SecurityAuditor..."
                                className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg 
                                         text-white placeholder-zinc-500 focus:outline-none focus:border-violet-500"
                            />
                        </div>

                        {/* Mission */}
                        <div>
                            <label className="block text-sm font-medium text-zinc-400 mb-1">
                                Mission
                            </label>
                            <textarea
                                value={mission}
                                onChange={(e) => setMission(e.target.value)}
                                placeholder="Describe what this agent will do..."
                                rows={3}
                                className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg 
                                         text-white placeholder-zinc-500 focus:outline-none focus:border-violet-500 resize-none"
                            />
                        </div>

                        {/* Capabilities */}
                        <div>
                            <label className="block text-sm font-medium text-zinc-400 mb-1">
                                Capabilities (comma-separated)
                            </label>
                            <input
                                type="text"
                                value={capabilities}
                                onChange={(e) => setCapabilities(e.target.value)}
                                placeholder="ui_analysis, accessibility, testing..."
                                className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg 
                                         text-white placeholder-zinc-500 focus:outline-none focus:border-violet-500"
                            />
                        </div>

                        {/* Error */}
                        {error && (
                            <div className="px-3 py-2 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
                                {error}
                            </div>
                        )}

                        {/* Actions */}
                        <div className="flex justify-end gap-3 pt-2">
                            <button
                                type="button"
                                onClick={onClose}
                                className="px-4 py-2 text-zinc-400 hover:text-white transition-colors"
                            >
                                Cancel
                            </button>
                            <button
                                type="submit"
                                disabled={isLoading}
                                className="px-4 py-2 bg-violet-600 hover:bg-violet-500 disabled:bg-zinc-600 
                                         rounded-lg font-medium text-white transition-colors flex items-center gap-2"
                            >
                                {isLoading ? (
                                    <>
                                        <span className="animate-spin">⏳</span>
                                        <span>Spawning...</span>
                                    </>
                                ) : (
                                    <>
                                        <span>✨</span>
                                        <span>Spawn Agent</span>
                                    </>
                                )}
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </>
    );
}
