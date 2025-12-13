"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { searchCommands, CATEGORY_LABELS, type Command } from "@/lib/commands";

// ============================================================================
// Types
// ============================================================================

interface CommandPaletteProps {
    isOpen: boolean;
    onClose: () => void;
    onExecuteCommand?: (command: Command) => void;
}

// ============================================================================
// Command Palette Component
// ============================================================================

export function CommandPalette({
    isOpen,
    onClose,
    onExecuteCommand,
}: CommandPaletteProps) {
    const router = useRouter();
    const [query, setQuery] = useState("");
    const [selectedIndex, setSelectedIndex] = useState(0);
    const inputRef = useRef<HTMLInputElement>(null);
    const listRef = useRef<HTMLDivElement>(null);

    const results = searchCommands(query);

    // Focus input when opened
    useEffect(() => {
        if (isOpen) {
            setQuery("");
            setSelectedIndex(0);
            setTimeout(() => inputRef.current?.focus(), 50);
        }
    }, [isOpen]);

    // Reset selection when results change
    useEffect(() => {
        setSelectedIndex(0);
    }, [query]);

    // Keyboard navigation
    const handleKeyDown = (e: React.KeyboardEvent) => {
        switch (e.key) {
            case "ArrowDown":
                e.preventDefault();
                setSelectedIndex((prev) => Math.min(prev + 1, results.length - 1));
                break;
            case "ArrowUp":
                e.preventDefault();
                setSelectedIndex((prev) => Math.max(prev - 1, 0));
                break;
            case "Enter":
                e.preventDefault();
                if (results[selectedIndex]) {
                    executeCommand(results[selectedIndex]);
                }
                break;
            case "Escape":
                e.preventDefault();
                onClose();
                break;
        }
    };

    // Execute command
    const executeCommand = (command: Command) => {
        onClose();

        if (onExecuteCommand) {
            onExecuteCommand(command);
            return;
        }

        // Default handling
        switch (command.actionType) {
            case "navigate":
                router.push(command.action);
                break;
            case "command":
                // For now, just navigate to chat with the command
                router.push(`/chat?cmd=${encodeURIComponent(command.action)}`);
                break;
            case "api":
                // TODO: Call API directly
                console.log("API command:", command.action);
                break;
        }
    };

    if (!isOpen) return null;

    return (
        <>
            {/* Backdrop */}
            <div
                className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50"
                onClick={onClose}
            />

            {/* Modal */}
            <div className="fixed inset-x-4 top-[20%] max-w-xl mx-auto z-50">
                <div className="bg-zinc-900 border border-zinc-700 rounded-xl shadow-2xl overflow-hidden">
                    {/* Search Input */}
                    <div className="flex items-center gap-3 p-4 border-b border-zinc-700">
                        <span className="text-zinc-400 text-lg">🔍</span>
                        <input
                            ref={inputRef}
                            type="text"
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            onKeyDown={handleKeyDown}
                            placeholder="Type a command or search..."
                            className="flex-1 bg-transparent border-none outline-none text-zinc-100 
                         placeholder:text-zinc-500 text-base"
                            autoComplete="off"
                            autoCorrect="off"
                            autoCapitalize="off"
                            spellCheck="false"
                        />
                        <kbd className="text-xs bg-zinc-700 px-2 py-1 rounded text-zinc-400">
                            ESC
                        </kbd>
                    </div>

                    {/* Results */}
                    <div
                        ref={listRef}
                        className="max-h-[50vh] overflow-y-auto"
                    >
                        {results.length === 0 ? (
                            <div className="p-6 text-center text-zinc-500">
                                <div className="text-3xl mb-2 opacity-30">🔎</div>
                                <div>No commands found</div>
                            </div>
                        ) : (
                            <div className="p-2">
                                {/* Group by category */}
                                {groupByCategory(results).map(([category, commands]) => (
                                    <div key={category} className="mb-3">
                                        <div className="px-3 py-1.5 text-xs font-medium text-zinc-500 uppercase tracking-wider">
                                            {CATEGORY_LABELS[category as Command["category"]]}
                                        </div>
                                        {commands.map((command, idx) => {
                                            const globalIndex = results.indexOf(command);
                                            const isSelected = globalIndex === selectedIndex;

                                            return (
                                                <button
                                                    key={command.id}
                                                    onClick={() => executeCommand(command)}
                                                    onMouseEnter={() => setSelectedIndex(globalIndex)}
                                                    className={`
                            w-full flex items-center gap-3 px-3 py-2.5 rounded-lg
                            transition-colors text-left
                            ${isSelected
                                                            ? "bg-violet-600/20 text-violet-100"
                                                            : "text-zinc-300 hover:bg-zinc-800/50"
                                                        }
                          `}
                                                >
                                                    <span className="text-lg">{command.icon}</span>
                                                    <div className="flex-1 min-w-0">
                                                        <div className="font-medium text-sm">{command.label}</div>
                                                        <div className="text-xs text-zinc-500 truncate">
                                                            {command.description}
                                                        </div>
                                                    </div>
                                                    {command.shortcut && (
                                                        <kbd className="text-xs bg-zinc-700 px-1.5 py-0.5 rounded text-zinc-400">
                                                            {command.shortcut}
                                                        </kbd>
                                                    )}
                                                    {isSelected && (
                                                        <span className="text-xs text-violet-400">↵</span>
                                                    )}
                                                </button>
                                            );
                                        })}
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>

                    {/* Footer */}
                    <div className="flex items-center justify-between px-4 py-2 border-t border-zinc-700 text-xs text-zinc-500">
                        <div className="flex items-center gap-4">
                            <span><kbd className="bg-zinc-800 px-1 rounded">↑↓</kbd> Navigate</span>
                            <span><kbd className="bg-zinc-800 px-1 rounded">↵</kbd> Select</span>
                            <span><kbd className="bg-zinc-800 px-1 rounded">ESC</kbd> Close</span>
                        </div>
                        <div className="text-zinc-600">
                            {results.length} command{results.length !== 1 ? "s" : ""}
                        </div>
                    </div>
                </div>
            </div>
        </>
    );
}

// ============================================================================
// Helper: Group commands by category
// ============================================================================

function groupByCategory(commands: Command[]): [string, Command[]][] {
    const groups: Record<string, Command[]> = {};

    for (const cmd of commands) {
        if (!groups[cmd.category]) {
            groups[cmd.category] = [];
        }
        groups[cmd.category].push(cmd);
    }

    return Object.entries(groups);
}

export default CommandPalette;
