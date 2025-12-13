"use client";

import { Sidebar } from "@/components/Sidebar";
import { CommandPalette } from "@/components/CommandPalette";
import { useCommandPalette } from "@/hooks/useCommandPalette";
import { useNexusWebSocket } from "@/hooks/useNexusWebSocket";

// ============================================================================
// Layout Shell (Client Component)
// ============================================================================

export function LayoutShell({ children }: { children: React.ReactNode }) {
    const { isOpen, open, close } = useCommandPalette();
    const { isConnected } = useNexusWebSocket();

    return (
        <div className="flex min-h-screen">
            {/* Sidebar */}
            <Sidebar onOpenCommandPalette={open} />

            {/* Main Content Area */}
            <div className="flex-1 flex flex-col min-w-0">
                {/* Header */}
                <header className="border-b border-zinc-800 bg-zinc-900/50 backdrop-blur-sm sticky top-0 z-40">
                    <div className="px-6 py-3 flex items-center justify-between">
                        <div className="flex items-center gap-4">
                            {/* Breadcrumb or page title would go here */}
                            <button
                                onClick={open}
                                className="hidden md:flex items-center gap-2 px-3 py-1.5 
                           bg-zinc-800/50 border border-zinc-700 rounded-lg
                           text-zinc-400 hover:text-zinc-200 text-sm transition-colors"
                            >
                                <span>🔍</span>
                                <span>Search...</span>
                                <kbd className="text-xs bg-zinc-700 px-1.5 py-0.5 rounded ml-2">⌘K</kbd>
                            </button>
                        </div>

                        {/* Connection Status */}
                        <div className="flex items-center gap-4">
                            <div className="flex items-center gap-2">
                                <div
                                    className={`w-2 h-2 rounded-full ${isConnected ? "bg-emerald-500 animate-pulse" : "bg-red-500"
                                        }`}
                                />
                                <span className="text-sm text-zinc-400">
                                    {isConnected ? "Connected" : "Disconnected"}
                                </span>
                            </div>
                        </div>
                    </div>
                </header>

                {/* Main Content */}
                <main className="flex-1 p-6 overflow-auto">
                    {children}
                </main>

                {/* Footer */}
                <footer className="border-t border-zinc-800 bg-zinc-900/30 py-3 px-6">
                    <div className="flex items-center justify-between text-xs text-zinc-500">
                        <span>NEXUS V10.2 • HiveMind + Swarm + Agent-as-Tool</span>
                        <span>Created by Yann Abadie</span>
                    </div>
                </footer>
            </div>

            {/* Command Palette Modal */}
            <CommandPalette isOpen={isOpen} onClose={close} />
        </div>
    );
}

export default LayoutShell;
